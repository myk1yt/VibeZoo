"""Optional embedding client for semantic search — feature-detected, graceful fallback."""
import json
import logging
import os
import time
import urllib.request
import urllib.error
from typing import Optional

try:
    from bridge.i18n import t
except ImportError:
    def t(msg: str, *args) -> str:  # type: ignore
        if args:
            return msg.format(*args)
        return msg

logger = logging.getLogger(__name__)

# Constants for availability caching and backoff
DEFAULT_AVAILABILITY_TTL: float = 60.0  # Seconds to cache successful probe
INITIAL_BACKOFF: float = 1.0            # Initial backoff on failure (seconds)
MAX_BACKOFF: float = 30.0               # Maximum backoff interval (seconds)
BACKOFF_FACTOR: float = 2.0             # Multiplier for exponential backoff
PROBE_TIMEOUT: float = 2.0              # HTTP timeout for health check probe (seconds)
EMBED_TIMEOUT: float = 5.0              # HTTP timeout for embedding batch request (seconds)


class EmbeddingClient:
    """HTTP embedding client with runtime shape probing (Ollama → OpenAI fallback).
    
    Includes TTL-based positive caching, exponential backoff for failed probes,
    and availability reset capabilities.
    """

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None,
                 ttl: float = DEFAULT_AVAILABILITY_TTL):
        self._base_url = base_url or os.environ.get("VIBEZOO_EMBED_URL", "http://localhost:8089")
        self._model = model or os.environ.get("VIBEZOO_EMBED_MODEL", "nomic-embed-text")
        self._ttl: float = ttl
        self._api_style: Optional[str] = None  # "ollama" or "openai", cached after first probe
        self._available: Optional[bool] = None  # cached probe state
        self._last_probe_time: float = 0.0
        self._current_backoff: float = INITIAL_BACKOFF
        self._consecutive_failures: int = 0

    @property
    def base_url(self) -> str:
        """Base URL of the embedding server."""
        return self._base_url

    @property
    def model_name(self) -> str:
        """Name of the embedding model configured."""
        return self._model

    @property
    def api_style(self) -> Optional[str]:
        """Detected API style ('ollama' or 'openai')."""
        return self._api_style

    def is_available(self, force: bool = False) -> bool:
        """Probe the embedding server with TTL caching and exponential backoff.
        
        - If already verified available: cached for self._ttl seconds (default 60s).
        - If probe failed: subsequent checks return False immediately until backoff expires (1s -> 2s -> 4s -> ... max 30s).
        - If force is True: bypasses cache and forces an immediate network probe.
        """
        now = time.monotonic()
        if not force and self._available is not None and self._last_probe_time > 0.0:
            if self._available:
                if (now - self._last_probe_time) < self._ttl:
                    return True
            else:
                if (now - self._last_probe_time) < self._current_backoff:
                    return False

        if not force and self._available is not None and self._last_probe_time == 0.0:
            # Preserved for manual mock/override in tests
            return self._available

        return self._probe(now)

    def reset_availability(self) -> None:
        """Reset availability cache and backoff timers to force a re-probe on next check."""
        self._available = None
        self._last_probe_time = 0.0
        self._consecutive_failures = 0
        self._current_backoff = INITIAL_BACKOFF
        self._api_style = None

    def _probe(self, now: float) -> bool:
        was_available = self._available

        # Try Ollama-style first
        try:
            req = urllib.request.Request(
                f"{self._base_url}/api/embeddings",
                data=json.dumps({"model": self._model, "input": "test"}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=PROBE_TIMEOUT) as resp:
                if resp.status == 200:
                    self._api_style = "ollama"
                    self._available = True
                    self._consecutive_failures = 0
                    self._current_backoff = INITIAL_BACKOFF
                    self._last_probe_time = time.monotonic()
                    if was_available is False:
                        logger.info(t("Embedding server recovered ({0}) at {1}", self._api_style, self._base_url))
                    return True
        except (urllib.error.URLError, OSError, json.JSONDecodeError, TimeoutError):
            pass

        # Try OpenAI-style
        try:
            req = urllib.request.Request(
                f"{self._base_url}/v1/embeddings",
                data=json.dumps({"model": self._model, "input": ["test"]}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=PROBE_TIMEOUT) as resp:
                if resp.status == 200:
                    self._api_style = "openai"
                    self._available = True
                    self._consecutive_failures = 0
                    self._current_backoff = INITIAL_BACKOFF
                    self._last_probe_time = time.monotonic()
                    if was_available is False:
                        logger.info(t("Embedding server recovered ({0}) at {1}", self._api_style, self._base_url))
                    return True
        except (urllib.error.URLError, OSError, json.JSONDecodeError, TimeoutError):
            pass

        self._available = False
        self._api_style = None
        self._last_probe_time = time.monotonic()
        self._consecutive_failures += 1
        if self._consecutive_failures == 1:
            self._current_backoff = INITIAL_BACKOFF
        else:
            self._current_backoff = min(self._current_backoff * BACKOFF_FACTOR, MAX_BACKOFF)

        if was_available is True or was_available is None:
            logger.warning(
                t("Embedding server unavailable at {0}. Probes will retry with exponential backoff (next in {1}s).",
                  self._base_url, int(self._current_backoff))
            )
        return False

    def embed(self, texts: list[str]) -> Optional[list[list[float]]]:
        """Embed a batch of texts. Returns None on any error."""
        if not texts or not self.is_available():
            return None
        try:
            if self._api_style == "ollama":
                return self._embed_ollama(texts)
            else:
                return self._embed_openai(texts)
        except Exception as e:
            logger.debug(f"Embedding failed: {e}")
            return None

    def _embed_ollama(self, texts: list[str]) -> list[list[float]]:
        results = []
        for text in texts:  # Ollama typically handles one at a time
            req = urllib.request.Request(
                f"{self._base_url}/api/embeddings",
                data=json.dumps({"model": self._model, "input": text}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=EMBED_TIMEOUT) as resp:
                data = json.loads(resp.read())
                results.append(data["embedding"])
        return results

    def _embed_openai(self, texts: list[str]) -> list[list[float]]:
        req = urllib.request.Request(
            f"{self._base_url}/v1/embeddings",
            data=json.dumps({"model": self._model, "input": texts}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=EMBED_TIMEOUT) as resp:
            data = json.loads(resp.read())
            return [item["embedding"] for item in data["data"]]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def rank_by_embedding(query_vec: list[float], candidates: list[dict], embed_fn) -> list[dict]:
    """Rerank candidates by embedding similarity to query."""
    contents = [c.get("content", "")[:2000] for c in candidates]  # cap per-item
    vecs = embed_fn(contents)
    if vecs is None:
        return candidates  # fallback: return as-is
    for i, c in enumerate(candidates):
        c["semantic_score"] = round(cosine_similarity(query_vec, vecs[i]), 4)
    candidates.sort(key=lambda x: x.get("semantic_score", 0), reverse=True)
    return candidates


# ── Module-level singleton and helper functions ─────────────

_client_instance: Optional[EmbeddingClient] = None


def get_embedding_client() -> EmbeddingClient:
    """Get or create the module-level singleton EmbeddingClient."""
    global _client_instance
    if _client_instance is None:
        _client_instance = EmbeddingClient()
    return _client_instance


def _get_embed_client() -> EmbeddingClient:
    """Alias for get_embedding_client to match plan naming."""
    return get_embedding_client()


def reset_availability() -> None:
    """Reset the module-level singleton's availability cache."""
    global _client_instance
    if _client_instance is not None:
        _client_instance.reset_availability()
