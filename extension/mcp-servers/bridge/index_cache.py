"""VibeZoo Bridge — Disk-based Vector & Code Index Cache.

Persists embedding vectors and file hash manifests to `.zoo-code/index-cache/`
for one-shot rebuild and zero re-indexing overhead across restarts.
Gracefully degrades to in-memory mode if numpy is unavailable.
"""

import hashlib
import json
import logging
import os
import shutil
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union

try:
    from bridge.config import DEFAULT_EXCLUDE_DIRS, SOURCE_EXTS
except ImportError:
    DEFAULT_EXCLUDE_DIRS = {
        ".git", "node_modules", ".zoo-code", "dist", "build",
        ".next", "coverage", "target", "vendor", "__pycache__",
        ".venv", "env", ".env", ".vibezoo-uploads",
    }
    SOURCE_EXTS = {
        ".ts", ".tsx", ".js", ".jsx", ".py", ".go", ".rs",
        ".cpp", ".hpp", ".cc", ".h", ".c", ".sh", ".bash", ".ps1",
        ".yaml", ".yml", ".json",
    }

try:
    from bridge.i18n import t
except ImportError:
    def t(msg: str, *args) -> str:  # type: ignore
        if args:
            return msg.format(*args)
        return msg

logger = logging.getLogger(__name__)

# Try importing numpy with graceful degrade flag
try:
    import numpy as np
    _NUMPY_AVAILABLE = True
except ImportError:
    np = None  # type: ignore
    _NUMPY_AVAILABLE = False

_numpy_warned = False
MAX_INDEX_FILES = 5000


def compute_file_hash(path: Union[str, Path], algo: str = "sha256") -> str:
    """Compute cryptographic hash of a file reading in 64KB chunks.
    
    Returns empty string if file does not exist or is unreadable.
    """
    try:
        p = Path(path)
        if not p.is_file():
            return ""
        h = hashlib.new(algo)
        with open(p, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        logger.debug(f"INDEX_CACHE/hash/001: failed to hash {path}: {e}")
        return ""


class CodeIndexCache:
    """Disk-backed index cache storing embedding vectors and file hash manifests."""

    def __init__(
        self,
        workspace_root: Optional[Union[str, Path]] = None,
        max_files: int = MAX_INDEX_FILES,
    ):
        global _numpy_warned
        raw_root = workspace_root or os.environ.get("VIBEZOO_WORKSPACE_ROOT") or Path.cwd()
        self.workspace_root = Path(raw_root).resolve()
        self.cache_dir = self.workspace_root / ".zoo-code" / "index-cache"
        self.meta_path = self.cache_dir / "meta.json"
        self.manifest_path = self.meta_path  # alias for backwards compatibility
        self.vectors_path = self.cache_dir / "vectors.npz"
        self.max_files = max_files
        self._lock = threading.RLock()

        # In-memory fallback / cache
        self._mem_vectors: Optional[Any] = None
        self._mem_file_paths: Optional[List[str]] = None
        self._meta_cache: Optional[Dict[str, Any]] = None

        if not _NUMPY_AVAILABLE and not _numpy_warned:
            logger.warning(
                t(
                    "INDEX_CACHE/numpy/001: numpy is not installed; CodeIndexCache "
                    "operating in memory-only mode without disk .npz persistence."
                )
            )
            _numpy_warned = True

    def _ensure_cache_dir(self) -> None:
        """Create cache directory if it does not exist."""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error(f"INDEX_CACHE/mkdir/001: failed to create cache dir {self.cache_dir}: {e}")

    def load_manifest(self) -> Dict[str, Any]:
        """Read meta.json from disk or memory cache. Returns empty dict on failure."""
        with self._lock:
            if not self.meta_path.exists():
                # Check if legacy manifest.json exists
                legacy = self.cache_dir / "manifest.json"
                if legacy.exists():
                    try:
                        data = json.loads(legacy.read_text(encoding="utf-8"))
                        self._meta_cache = data
                        return data
                    except Exception:
                        pass
                return {}

            try:
                data = json.loads(self.meta_path.read_text(encoding="utf-8"))
                self._meta_cache = data
                return data
            except Exception as e:
                logger.warning(f"INDEX_CACHE/manifest/001: failed to read meta.json: {e}")
                return {}

    def is_stale(self, files: Optional[Sequence[Union[str, Path]]] = None) -> bool:
        """Check if cached index is stale compared to disk files.
        
        Returns True if cache does not exist, is corrupted, or any file hash differs.
        """
        manifest = self.load_manifest()
        if not manifest or "files" not in manifest:
            return True

        cached_files: Dict[str, Any] = manifest.get("files", {})

        # If numpy is available, check if vectors.npz exists and is readable
        if _NUMPY_AVAILABLE and not self.vectors_path.exists():
            return True

        # Determine target file list
        if files is not None:
            rel_targets = []
            for f in files:
                p = Path(f)
                if p.is_absolute():
                    try:
                        rel = p.relative_to(self.workspace_root).as_posix()
                    except ValueError:
                        rel = p.as_posix()
                else:
                    rel = p.as_posix()
                rel_targets.append(rel)

            # If target list has different count or missing files
            if set(rel_targets) != set(cached_files.keys()):
                return True

            for rel in rel_targets:
                full_path = self.workspace_root / rel
                curr_hash = compute_file_hash(full_path)
                if not curr_hash:
                    return True
                rec = cached_files.get(rel)
                if not rec or rec.get("hash") != curr_hash:
                    return True
        else:
            if not cached_files:
                return True
            for rel, rec in cached_files.items():
                full_path = self.workspace_root / rel
                curr_hash = compute_file_hash(full_path)
                if not curr_hash:
                    return True
                if rec.get("hash") != curr_hash:
                    return True

        return False

    def is_file_stale(self, file_path: Union[str, Path], current_hash: Optional[str] = None) -> bool:
        """Check if an individual file is stale compared to manifest."""
        manifest = self.load_manifest()
        cached_files = manifest.get("files", {})

        p = Path(file_path)
        if p.is_absolute():
            try:
                rel = p.relative_to(self.workspace_root).as_posix()
            except ValueError:
                rel = p.as_posix()
        else:
            rel = p.as_posix()

        rec = cached_files.get(rel)
        if not rec:
            return True

        h = current_hash or compute_file_hash(self.workspace_root / rel)
        return rec.get("hash") != h

    def save(
        self,
        vectors: Any,
        file_paths: Sequence[Union[str, Path]],
        model_name: str = "nomic-embed-text",
        dim: Optional[int] = None,
    ) -> bool:
        """Save embedding vectors and file hash manifest to disk (and memory).
        
        Handles LRU / file limit truncation if len(file_paths) > max_files.
        """
        if len(vectors) != len(file_paths):
            logger.error(
                f"INDEX_CACHE/save/001: vectors length ({len(vectors)}) does not match "
                f"file_paths length ({len(file_paths)})"
            )
            return False

        with self._lock:
            self._ensure_cache_dir()

            # Normalize file paths to relative POSIX strings
            rel_paths: List[str] = []
            file_records: Dict[str, Dict[str, Any]] = {}
            indexed_vectors = []

            for idx, raw_p in enumerate(file_paths):
                p = Path(raw_p)
                if p.is_absolute():
                    try:
                        rel = p.relative_to(self.workspace_root).as_posix()
                    except ValueError:
                        rel = p.as_posix()
                else:
                    rel = p.as_posix()

                full_path = self.workspace_root / rel
                f_hash = compute_file_hash(full_path)
                try:
                    mtime = full_path.stat().st_mtime if full_path.exists() else time.time()
                    size = full_path.stat().st_size if full_path.exists() else 0
                except OSError:
                    mtime = time.time()
                    size = 0

                rel_paths.append(rel)
                file_records[rel] = {
                    "hash": f_hash,
                    "mtime": mtime,
                    "size": size,
                    "index": idx,
                }
                indexed_vectors.append(vectors[idx])

            # Apply file count limit if exceeded (keep most recent mtimes)
            if len(rel_paths) > self.max_files:
                sorted_rel = sorted(
                    rel_paths,
                    key=lambda r: file_records[r].get("mtime", 0),
                    reverse=True,
                )[:self.max_files]
                rel_set = set(sorted_rel)

                new_rel_paths = []
                new_records = {}
                new_vectors = []
                new_idx = 0
                for r in rel_paths:
                    if r in rel_set:
                        new_rel_paths.append(r)
                        rec = dict(file_records[r])
                        rec["index"] = new_idx
                        new_records[r] = rec
                        new_vectors.append(vectors[file_records[r]["index"]])
                        new_idx += 1
                rel_paths = new_rel_paths
                file_records = new_records
                indexed_vectors = new_vectors

            # Determine embedding dimension
            computed_dim = dim
            if computed_dim is None and len(indexed_vectors) > 0:
                first_vec = indexed_vectors[0]
                if hasattr(first_vec, "shape") and len(first_vec.shape) > 0:
                    computed_dim = int(first_vec.shape[0])
                elif isinstance(first_vec, (list, tuple)):
                    computed_dim = len(first_vec)

            manifest_data = {
                "version": "1.0",
                "model_name": model_name,
                "dim": computed_dim,
                "created_at": time.time(),
                "updated_at": time.time(),
                "count": len(rel_paths),
                "file_paths": rel_paths,
                "files": file_records,
            }

            # 1. Write meta.json atomically
            try:
                temp_meta = self.cache_dir / f"meta_{os.getpid()}_{time.time_ns()}.tmp"
                temp_meta.write_text(
                    json.dumps(manifest_data, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
                if temp_meta.exists():
                    if self.meta_path.exists():
                        self.meta_path.unlink()
                    temp_meta.rename(self.meta_path)
            except Exception as e:
                logger.error(f"INDEX_CACHE/save/002: failed to write meta.json: {e}")
                return False

            # 2. Save vectors to disk via np.savez_compressed if numpy available
            if _NUMPY_AVAILABLE:
                try:
                    vec_array = np.array(indexed_vectors, dtype=np.float32)
                    temp_npz = self.cache_dir / f"vectors_{os.getpid()}_{time.time_ns()}.tmp.npz"
                    np.savez_compressed(
                        temp_npz,
                        vectors=vec_array,
                        file_paths=np.array(rel_paths, dtype=object),
                    )
                    if temp_npz.exists():
                        if self.vectors_path.exists():
                            self.vectors_path.unlink()
                        temp_npz.rename(self.vectors_path)
                except Exception as e:
                    logger.error(f"INDEX_CACHE/save/003: failed to save vectors.npz: {e}")
                    return False

            # Update in-memory state
            self._mem_vectors = indexed_vectors
            self._mem_file_paths = rel_paths
            self._meta_cache = manifest_data
            return True

    def load(self) -> Optional[Tuple[Any, List[str]]]:
        """Load cached vectors and file paths.
        
        Returns None if cache is stale, missing, or corrupted.
        Automatically cleans up corrupted cache files on integrity failure.
        """
        with self._lock:
            manifest = self.load_manifest()
            if not manifest or "files" not in manifest or "file_paths" not in manifest:
                return None

            if self.is_stale():
                return None

            expected_paths = manifest.get("file_paths", [])

            if _NUMPY_AVAILABLE:
                if not self.vectors_path.exists():
                    return None
                try:
                    with np.load(self.vectors_path, allow_pickle=True) as data:
                        if "vectors" not in data or "file_paths" not in data:
                            raise ValueError("vectors.npz missing required keys")
                        vectors = data["vectors"]
                        file_paths = list(data["file_paths"])
                        if len(vectors) != len(file_paths) or len(file_paths) != len(expected_paths):
                            raise ValueError("vector count mismatch with manifest")
                        return vectors, file_paths
                except Exception as e:
                    logger.warning(
                        f"INDEX_CACHE/corrupted/001: vectors.npz corrupted ({e}), "
                        "cleaning up cache for rebuild."
                    )
                    self.clear()
                    return None
            else:
                if self._mem_vectors is not None and self._mem_file_paths is not None:
                    return self._mem_vectors, self._mem_file_paths
                return None

    def clear(self) -> None:
        """Remove all disk cache files and reset memory buffers."""
        with self._lock:
            self._mem_vectors = None
            self._mem_file_paths = None
            self._meta_cache = None

            for target in [self.meta_path, self.vectors_path, self.cache_dir / "manifest.json"]:
                try:
                    if target.exists():
                        target.unlink()
                except OSError as e:
                    logger.debug(f"INDEX_CACHE/clear/001: failed to unlink {target}: {e}")

            # Also remove any leftover tmp files
            if self.cache_dir.exists():
                for tmp_file in self.cache_dir.glob("*.tmp*"):
                    try:
                        tmp_file.unlink()
                    except OSError:
                        pass

    def get_embedding(self, file_path: Union[str, Path]) -> Optional[List[float]]:
        """Retrieve single file embedding vector if present in cache."""
        loaded = self.load()
        if not loaded:
            return None
        vectors, file_paths = loaded
        p = Path(file_path)
        if p.is_absolute():
            try:
                rel = p.relative_to(self.workspace_root).as_posix()
            except ValueError:
                rel = p.as_posix()
        else:
            rel = p.as_posix()

        if rel in file_paths:
            idx = file_paths.index(rel)
            vec = vectors[idx]
            if hasattr(vec, "tolist"):
                return vec.tolist()
            return list(vec)
        return None

    def store_embedding(
        self,
        file_path: Union[str, Path],
        vec: List[float],
        model_name: str = "nomic-embed-text",
        dim: Optional[int] = None,
    ) -> None:
        """Store or update embedding for a single file."""
        loaded = self.load()
        p = Path(file_path)
        if p.is_absolute():
            try:
                rel = p.relative_to(self.workspace_root).as_posix()
            except ValueError:
                rel = p.as_posix()
        else:
            rel = p.as_posix()

        if loaded:
            vectors, file_paths = loaded
            vec_list = [v.tolist() if hasattr(v, "tolist") else list(v) for v in vectors]
            path_list = list(file_paths)
            if rel in path_list:
                idx = path_list.index(rel)
                vec_list[idx] = vec
            else:
                path_list.append(rel)
                vec_list.append(vec)
            self.save(vec_list, path_list, model_name=model_name, dim=dim)
        else:
            self.save([vec], [rel], model_name=model_name, dim=dim)

    def invalidate(self, file_path: Optional[Union[str, Path]] = None) -> None:
        """Invalidate single file or entire cache."""
        if file_path is None:
            self.clear()
            return

        loaded = self.load()
        if not loaded:
            return

        p = Path(file_path)
        if p.is_absolute():
            try:
                rel = p.relative_to(self.workspace_root).as_posix()
            except ValueError:
                rel = p.as_posix()
        else:
            rel = p.as_posix()

        vectors, file_paths = loaded
        if rel in file_paths:
            idx = file_paths.index(rel)
            vec_list = [v.tolist() if hasattr(v, "tolist") else list(v) for v in vectors]
            path_list = list(file_paths)
            del vec_list[idx]
            del path_list[idx]
            self.save(vec_list, path_list)

    def rebuild(
        self,
        root: Optional[Union[str, Path]] = None,
        embed_fn: Optional[Callable[[List[str]], Optional[List[List[float]]]]] = None,
        model_name: str = "nomic-embed-text",
    ) -> int:
        """Rebuild index cache for workspace root. Returns processed file count."""
        target_root = Path(root or self.workspace_root).resolve()
        candidate_files: List[Path] = []

        for dirpath, dirnames, filenames in os.walk(target_root):
            # Prune excluded directories
            dirnames[:] = [d for d in dirnames if d not in DEFAULT_EXCLUDE_DIRS and not d.startswith(".")]
            for filename in filenames:
                _, ext = os.path.splitext(filename)
                if ext.lower() in SOURCE_EXTS:
                    candidate_files.append(Path(dirpath) / filename)

        if not candidate_files:
            self.clear()
            return 0

        # Read contents (capped at 2000 chars per file)
        contents = []
        valid_paths = []
        for f in candidate_files:
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")[:2000]
                contents.append(text)
                valid_paths.append(f)
            except Exception:
                continue

        if not valid_paths:
            return 0

        if embed_fn is not None:
            vectors = embed_fn(contents)
            if vectors is not None and len(vectors) == len(valid_paths):
                self.save(vectors, valid_paths, model_name=model_name)

        return len(valid_paths)


# Alias
IndexCache = CodeIndexCache

# ── Module-level singleton ─────────────────────────────────────────

_index_cache_instance: Optional[CodeIndexCache] = None


def get_index_cache(workspace_root: Optional[Union[str, Path]] = None) -> CodeIndexCache:
    """Get or create singleton CodeIndexCache for workspace."""
    global _index_cache_instance
    if _index_cache_instance is None:
        _index_cache_instance = CodeIndexCache(workspace_root=workspace_root)
    return _index_cache_instance


def _get_index_cache(workspace_root: Optional[Union[str, Path]] = None) -> CodeIndexCache:
    """Plan alias for get_index_cache."""
    return get_index_cache(workspace_root=workspace_root)
