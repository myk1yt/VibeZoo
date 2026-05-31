# VibeZoo Bridge — 검색 엔진
# ripgrep → git grep → walk 3단계 폴백 검색

import os
import re
import subprocess
import time
from pathlib import Path
from typing import Optional, List, Set

from bridge.config import DEFAULT_EXCLUDE_DIRS, SOURCE_EXTS


class SearchEngine:
    """
    외부 검색 엔진 연동 — 우선순위:
    1. ripgrep (rg) — Rust 기반, 가장 빠름
    2. git grep — Git 저장소에서만 동작
    3. _fallback_to_walk() — 기존 os.walk + line 매칭 (regex 폴백)
    """

    def __init__(self, root: Path):
        self._root = root
        self._rg_available: Optional[bool] = None
        self._git_available: Optional[bool] = None

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
        """
        if self.ripgrep_available():
            return self._search_ripgrep(query, file_patterns, max_results, context_lines)
        elif self._is_git_repo() and self.git_grep_available():
            return self._search_git_grep(query, file_patterns, max_results)
        else:
            return self._fallback_to_walk(query, file_patterns, max_results)

    def search_fast(self, query: str, max_results: int = 10) -> List[dict]:
        """점진적 검색 — 먼저 10개 결과를 빠르게 반환"""
        return self.search(query, max_results=max_results, context_lines=0)

    # ── ripgrep ──────────────────────────────────────

    def _search_ripgrep(self, query: str, file_patterns: Optional[str],
                        max_results: int, context_lines: int) -> List[dict]:
        """ripgrep 호출 + 결과 파싱"""
        cmd = ["rg", "--no-heading", "--line-number", "--color", "never",
               "--max-count", str(max_results)]
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
                return self._fallback_to_walk(query, file_patterns, max_results)

            return self._parse_ripgrep_output(result.stdout, max_results)
        except Exception:
            return self._fallback_to_walk(query, file_patterns, max_results)

    def _parse_ripgrep_output(self, output: str, max_results: int) -> List[dict]:
        """ripgrep 출력 파싱"""
        results = []
        current = {}
        context_before = []
        context_after = []
        collecting_after = False

        for line in output.split("\n"):
            if not line.strip():
                continue

            # 매칭 라인 파싱: filename:line:column:content
            m = re.match(r'^([^:]+):(\d+):(\d+):(.+)$', line)
            if m:
                if current:
                    current["context_after"] = context_after
                    results.append(current)
                current = {
                    "file": m.group(1),
                    "line": int(m.group(2)),
                    "column": int(m.group(3)),
                    "content": m.group(4).strip()[:200],
                    "context_before": list(context_before),
                    "context_after": [],
                    "score": 1.0,
                }
                context_before = []
                context_after = []
                collecting_after = False
                if len(results) >= max_results:
                    break
            elif current:
                # 컨텍스트 라인
                if not collecting_after:
                    context_before.append(line.strip()[:200])
                    if len(context_before) > 3:
                        context_before = context_before[-3:]
                else:
                    context_after.append(line.strip()[:200])

        if current:
            current["context_after"] = context_after
            results.append(current)

        return results[:max_results]

    # ── git grep ─────────────────────────────────────

    def _search_git_grep(self, query: str, file_patterns: Optional[str],
                         max_results: int) -> List[dict]:
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
                return self._fallback_to_walk(query, file_patterns, max_results)

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
            return self._fallback_to_walk(query, file_patterns, max_results)

    # ── Fallback (os.walk) ───────────────────────────

    def _fallback_to_walk(self, query: str, file_patterns: Optional[str],
                          max_results: int) -> List[dict]:
        """os.walk 기반 폴백 검색 (기존 동작 유지)"""
        results = []
        query_lower = query.lower()

        # 파일 패턴 결정
        if file_patterns:
            patterns = [p.strip() for p in file_patterns.split(",") if p.strip()]
            ext_set = set()
            for pat in patterns:
                ext = os.path.splitext(pat)[1]
                if ext:
                    ext_set.add(ext)
            if not ext_set:
                ext_set = SOURCE_EXTS
        else:
            ext_set = SOURCE_EXTS

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
                    if ext not in ext_set:
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
                            if any(fname.endswith(p.strip().lstrip("*.")) for p in [pat]):
                                matched = True
                                break
                        if not matched:
                            continue

                    for i, line in enumerate(lines, 1):
                        if query_lower not in line.lower():
                            continue

                        ctx_before = lines[max(0, i - 4):i - 1] if i > 1 else []
                        ctx_after = lines[i:min(len(lines), i + 3)] if i < len(lines) else []

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
