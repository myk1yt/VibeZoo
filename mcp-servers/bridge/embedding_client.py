"""Optional embedding client for semantic search — feature-detected, graceful fallback."""
import json
import logging
import os
import urllib.request
import urllib.error
from typing import Optional

logger = logging.getLogger(__name__)


class EmbeddingClient:
    """HTTP embedding client with runtime shape probing (Ollama → OpenAI fallback)."""

    def __init__(self):
        self._base_url = os.environ.get("VIBEZOO_EMBED_URL", "http://localhost:8089")
        self._model = os.environ.get("VIBEZOO_EMBED_MODEL", "nomic-embed-text")
        self._api_style: Optional[str] = None  # "ollama" or "openai", cached after first probe
        self._available: Optional[bool] = None  # cached after first probe

    def is_available(self) -> bool:
        """Probe the embedding server (2s timeout). Caches result."""
        if self._available is not None:
            return self._available
        # Try Ollama-style first
        try:
            req = urllib.request.Request(
                f"{self._base_url}/api/embeddings",
                data=json.dumps({"model": self._model, "input": "test"}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    self._api_style = "ollama"
                    self._available = True
                    return True
        except (urllib.error.URLError, OSError, json.JSONDecodeError):
            pass
        # Try OpenAI-style
        try:
            req = urllib.request.Request(
                f"{self._base_url}/v1/embeddings",
                data=json.dumps({"model": self._model, "input": ["test"]}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    self._api_style = "openai"
                    self._available = True
                    return True
        except (urllib.error.URLError, OSError, json.JSONDecodeError):
            pass
        self._available = False
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
            with urllib.request.urlopen(req, timeout=5) as resp:
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
        with urllib.request.urlopen(req, timeout=5) as resp:
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
