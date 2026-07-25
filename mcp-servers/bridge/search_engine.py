# VibeZoo Bridge — 검색 엔진
# ripgrep → git grep → walk 3단계 폴백 검색

import os
import re
import subprocess
import sys
import threading
import time
from collections import OrderedDict
from pathlib import Path

# Pylance: ensure the extension root is in package search path
_EXT_ROOT = str(Path(__file__).resolve().parent.parent)
if _EXT_ROOT not in sys.path:
    sys.path.insert(0, _EXT_ROOT)

from typing import Optional, List, Set, Tuple, Any

from bridge.config import DEFAULT_EXCLUDE_DIRS, SOURCE_EXTS


class SearchEngine:
    """
    외부 검색 엔진 연동 — 우선순위:
    1. ripgrep (rg) — Rust 기반, 가장 빠름
    2. git grep — Git 저장소에서만 동작
    3. _fallback_to_walk() — 기존 os.walk + line 매칭 (regex 폴백)

    ST-07: Query-result memo layer — caches search results for 20 seconds
    with mtime-bucket invalidation to avoid re-scanning on repeated queries.
    """

    # ST-07: Search result memo — module-level LRU cache shared across instances
    _SEARCH_MEMO_TTL: int = 20  # seconds
    _SEARCH_MEMO_MAX: int = 64  # max entries
    _search_memo: OrderedDict = OrderedDict()
    _search_memo_lock = threading.Lock()

    def __init__(self, root: Path):
        self._root = root
        self._rg_available: Optional[bool] = None
        self._git_available: Optional[bool] = None

    # ── ST-07: Search Result Memo ──────────────────────

    @classmethod
    def _memo_key(cls, root: Path, query: str, file_patterns: Optional[str],
                  mode: str, context_lines: int) -> Tuple[Any, ...]:
        """Build a cache key including root mtime bucket (10-second granularity)."""
        try:
            root_mtime = os.path.getmtime(str(root))
            root_mtime_bucket = int(root_mtime // 10)
        except OSError:
            root_mtime_bucket = 0
        patterns_tuple = tuple(file_patterns.split(",")) if file_patterns else ()
        return (str(root), query, patterns_tuple, mode, context_lines, root_mtime_bucket)

    @classmethod
    def _memo_get(cls, key: Tuple[Any, ...]) -> Optional[List[dict]]:
        """Check memo for a cached result. Returns None on miss."""
        with cls._search_memo_lock:
            entry = cls._search_memo.get(key)
            if entry is None:
                return None
            cached_results, cached_time = entry
            if (time.time() - cached_time) > cls._SEARCH_MEMO_TTL:
                # Expired
                del cls._search_memo[key]
                return None
            # LRU update
            cls._search_memo.move_to_end(key)
            # Return a deep copy so callers can't mutate the cached list
            return [dict(r) for r in cached_results]

    @classmethod
    def _memo_put(cls, key: Tuple[Any, ...], results: List[dict]):
        """Store search results in the memo."""
        with cls._search_memo_lock:
            if key in cls._search_memo:
                cls._search_memo.move_to_end(key)
            else:
                if len(cls._search_memo) >= cls._SEARCH_MEMO_MAX:
                    cls._search_memo.popitem(last=False)
            # Store copies to prevent mutation of cached data
            cls._search_memo[key] = ([dict(r) for r in results], time.time())

    @classmethod
    def clear_memo(cls):
        """Clear all cached search results (for testing)."""
        with cls._search_memo_lock:
            cls._search_memo.clear()

    def ripgrep_available(self) -> bool:
        """ripgrep 설치 여부 확인"""
        if self._rg_available is None:
            try:
                subprocess.run(["rg", "--version"], capture_output=True, timeout=2)
                self._rg_available = True
            except Exception:
                self._rg_available = False
        return self._rg_available

    def _is_git_repo(self) -> bool:
        """현재 디렉토리가 Git 저장소인지 확인"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=str(self._root),
                capture_output=True, timeout=2
            )
            return result.returncode == 0
        except Exception:
            return False

    def git_grep_available(self) -> bool:
        """git grep 사용 가능 여부"""
        if self._git_available is None:
            try:
                subprocess.run(["git", "grep", "--version"], capture_output=True, timeout=2)
                self._git_available = True
            except Exception:
                self._git_available = False
        return self._git_available

    def search(self, query: str, file_patterns: Optional[str] = None,
               max_results: int = 10, mode: str = "auto",
               context_lines: int = 3) -> List[dict]:
        """
        통합 검색 — ripgrep 우선, git grep 차선, walk 폴백.
        각 결과: {file, line, column, content, context_before, context_after, score}

        ST-07: Checks query-result memo before running the actual search.
        On cache hit (fresh + same mtime bucket), returns cached results.
        On miss, runs search and stores results in memo.
        """
        # ST-07: Check memo first
        memo_key = self._memo_key(self._root, query, file_patterns, mode, context_lines)
        cached = self._memo_get(memo_key)
        if cached is not None:
            return cached[:max_results]

        if self.ripgrep_available():
            results = self._search_ripgrep(query, file_patterns, max_results, context_lines, mode)
        elif self._is_git_repo() and self.git_grep_available():
            results = self._search_git_grep(query, file_patterns, max_results, context_lines, mode)
        else:
            results = self._fallback_to_walk(query, file_patterns, max_results, context_lines, mode)

        # ST-07: Store in memo
        self._memo_put(memo_key, results)
        return results

    def search_fast(self, query: str, max_results: int = 50) -> List[dict]:
        """점진적 검색 — 먼저 50개 결과를 빠르게 반환"""
        return self.search(query, max_results=max_results, context_lines=0)

    # ── ripgrep ──────────────────────────────────────

    def _search_ripgrep(self, query: str, file_patterns: Optional[str],
                        max_results: int, context_lines: int,
                        mode: str = "auto") -> List[dict]:
        """ripgrep 호출 + 결과 파싱"""
        cmd = ["rg", "--no-heading", "--line-number", "--column", "--color", "never",
               "--max-count", str(max_results)]
        if mode == "exact":
            cmd.append("-s")  # case-sensitive
        if context_lines > 0:
            cmd.extend(["-C", str(context_lines)])
        if file_patterns:
            for pat in file_patterns.split(","):
                pat = pat.strip()
                if pat:
                    cmd.extend(["-g", pat])
        # 기본 제외 디렉토리
        for d in sorted(DEFAULT_EXCLUDE_DIRS):
            cmd.extend(["-g", f"!{d}/**"])
        cmd.append(query)

        try:
            result = subprocess.run(
                cmd, cwd=str(self._root),
                capture_output=True, text=True, timeout=10
            )
            if result.returncode not in (0, 1):  # 1 = no matches
                return self._fallback_to_walk(query, file_patterns, max_results, context_lines, mode)

            return self._parse_ripgrep_output(result.stdout, max_results)
        except Exception:
            return self._fallback_to_walk(query, file_patterns, max_results, context_lines, mode)

    def _parse_ripgrep_output(self, output: str, max_results: int) -> List[dict]:
        """ripgrep 출력 파싱"""
        results = []
        current = None
        context_before = []
        context_after = []
        collecting_after = True

        for line in output.split("\n"):
            if not line.strip():
                continue

            # 매칭 라인 파싱: filename:line:column:content
            # Format: filename:line:column:content (with --column flag)
            # Fallback: filename:line:content (without column)
            m = re.match(r'^([^:]+):(\d+):(\d+):(.+)$', line)
            if not m:
                m = re.match(r'^([^:]+):(\d+):(.+)$', line)
            if m:
                if current:
                    current["context_after"] = context_after
                    results.append(current)
                if m.lastindex == 4:
                    # filename:line:column:content
                    current = {
                        "file": m.group(1),
                        "line": int(m.group(2)),
                        "column": int(m.group(3)),
                        "content": m.group(4).strip()[:200],
                    }
                else:
                    # filename:line:content (no column)
                    current = {
                        "file": m.group(1),
                        "line": int(m.group(2)),
                        "column": 1,
                        "content": m.group(3).strip()[:200],
                    }
                current["context_before"] = list(context_before)
                current["context_after"] = []
                current["score"] = 1.0
                context_before = []
                context_after = []
                collecting_after = True
                if len(results) >= max_results:
                    break
            elif current:
                # 컨텍스트 라인 (current match 존재)
                if collecting_after:
                    context_after.append(line.strip()[:200])
                else:
                    context_before.append(line.strip()[:200])
                    if len(context_before) > 3:
                        context_before = context_before[-3:]
            else:
                # 첫 매칭 전 컨텍스트 라인 → context_before 축적
                context_before.append(line.strip()[:200])
                if len(context_before) > 3:
                    context_before = context_before[-3:]

        if current:
            current["context_after"] = context_after
            results.append(current)

        return results[:max_results]

    # ── git grep ─────────────────────────────────────

    def _search_git_grep(self, query: str, file_patterns: Optional[str],
                         max_results: int, context_lines: int = 3,
                         mode: str = "auto") -> List[dict]:
        """git grep 호출"""
        cmd = ["git", "grep", "-n", "--no-color",
               "--max-count", str(max_results)]
        if file_patterns:
            for pat in file_patterns.split(","):
                pat = pat.strip()
                if pat:
                    cmd.extend(["--", f"*{pat}" if not pat.startswith("*") else pat])
        cmd.append(query)

        try:
            result = subprocess.run(
                cmd, cwd=str(self._root),
                capture_output=True, text=True, timeout=10
            )
            if result.returncode not in (0, 1):
                return self._fallback_to_walk(query, file_patterns, max_results, context_lines, mode)

            results = []
            for line in result.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                m = re.match(r'^([^:]+):(\d+):(.+)$', line)
                if m:
                    results.append({
                        "file": m.group(1),
                        "line": int(m.group(2)),
                        "column": 1,
                        "content": m.group(3).strip()[:200],
                        "context_before": [],
                        "context_after": [],
                        "score": 0.9,
                    })
            return results[:max_results]
        except Exception:
            return self._fallback_to_walk(query, file_patterns, max_results, context_lines, mode)

    # ── Fallback (os.walk) ───────────────────────────

    def _fallback_to_walk(self, query: str, file_patterns: Optional[str],
                          max_results: int, context_lines: int = 3,
                          mode: str = "auto") -> List[dict]:
        """os.walk 기반 폴백 검색"""
        results = []
        query_lower = query.lower() if mode != "exact" else query

        # 파일 패턴 결정 — 확장자 미지정 시 None (모든 파일 허용)
        if file_patterns:
            patterns = [p.strip() for p in file_patterns.split(",") if p.strip()]
            ext_set = set()
            for pat in patterns:
                ext = os.path.splitext(pat)[1]
                if ext:
                    ext_set.add(ext)
            if not ext_set:
                ext_set = None  # 확장자 제한 없음
        else:
            ext_set = None  # 확장자 제한 없음

        try:
            for dirpath, dirnames, filenames in os.walk(str(self._root)):
                rel_dir = os.path.relpath(dirpath, str(self._root))
                if rel_dir != ".":
                    parts = rel_dir.replace("\\", "/").split("/")
                    if any(part in DEFAULT_EXCLUDE_DIRS for part in parts):
                        dirnames.clear()
                        continue
                dirnames[:] = [d for d in dirnames if d not in DEFAULT_EXCLUDE_DIRS]

                for fname in filenames:
                    ext = os.path.splitext(fname)[1]
                    if ext_set is not None and ext not in ext_set:
                        continue
                    fpath = Path(dirpath) / fname
                    try:
                        content = fpath.read_text(encoding="utf-8", errors="ignore")
                    except Exception:
                        continue

                    lines = content.split("\n")

                    # 파일 패턴 매칭 (globbing)
                    if file_patterns:
                        matched = False
                        for pat in patterns:
                            clean = pat.strip().lstrip("*.")
                            if fname.endswith(clean):
                                matched = True
                                break
                        if not matched:
                            continue

                    if mode == "exact":
                        # 대소문자 구분 매칭
                        for i, line in enumerate(lines, 1):
                            if query not in line:
                                continue

                            ctx_before = lines[max(0, i - 1 - context_lines):i - 1] if i > 1 else []
                            ctx_after = lines[i:min(len(lines), i + context_lines)] if i < len(lines) else []

                            results.append({
                                "file": os.path.relpath(str(fpath), str(self._root)),
                                "line": i,
                                "column": line.find(query) + 1,
                                "content": line.strip()[:200],
                                "context_before": ctx_before,
                                "context_after": ctx_after,
                                "score": 0.5,
                            })

                            if len(results) >= max_results:
                                return results

                        if len(results) >= max_results:
                            break
                    else:
                        for i, line in enumerate(lines, 1):
                            if query_lower not in line.lower():
                                continue

                            ctx_before = lines[max(0, i - 1 - context_lines):i - 1] if i > 1 else []
                            ctx_after = lines[i:min(len(lines), i + context_lines)] if i < len(lines) else []

                            results.append({
                                "file": os.path.relpath(str(fpath), str(self._root)),
                                "line": i,
                                "column": line.lower().find(query_lower) + 1,
                                "content": line.strip()[:200],
                                "context_before": ctx_before,
                                "context_after": ctx_after,
                                "score": 0.5,
                            })

                            if len(results) >= max_results:
                                return results

                        if len(results) >= max_results:
                            break
        except (PermissionError, OSError):
            pass

        return results[:max_results]
