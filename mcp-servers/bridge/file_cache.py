# VibeZoo Bridge — 3계층 파일 시스템 캐시
# L1(메모리 LRU) + L2(디스크 카탈로그) + L3(mtime 무효화)

import json
import os
import time
import threading
from collections import OrderedDict
from pathlib import Path
from typing import Optional, Set, List

from bridge.config import CACHE_DIR, MAX_CACHE_SIZE


class CacheEntry:
    """캐시 엔트리 — 파일 내용 + AST 결과 + mtime"""

    def __init__(self, content: str, mtime: float):
        self.content = content
        self.mtime = mtime
        self.ast = None
        self.created_at = time.time()


class FileCache:
    """
    3계층 파일 시스템 캐시
    L1: 메모리 LRU (파일 내용 + AST 결과, max 50 files)
    L2: 디스크 카탈로그 (~/.vibezoo-cache/catalog.json)
    L3: mtime 기반 자동 무효화
    """

    def __init__(self, max_l1_size: int = MAX_CACHE_SIZE, ttl: int = 30):
        self._l1: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max_l1 = max_l1_size
        self._l2_path = Path(CACHE_DIR) / "catalog.json"
        self._ttl = ttl
        self._lock = threading.Lock()
        self._file_list_cache: dict = {}
        self._file_list_cache_ttl: int = 5

        # L2 디렉토리 생성
        self._l2_path.parent.mkdir(parents=True, exist_ok=True)

    # ── L1 메모리 캐시 ──────────────────────────────

    def _l1_get(self, key: str) -> Optional[CacheEntry]:
        """L1 캐시 조회 (LRU 업데이트)"""
        entry = self._l1.get(key)
        if entry is None:
            return None
        # 접근 시 LRU 순서 업데이트
        self._l1.move_to_end(key)
        return entry

    def _l1_put(self, key: str, entry: CacheEntry):
        """L1 캐시 저장 (LRU eviction)"""
        if key in self._l1:
            self._l1.move_to_end(key)
        else:
            if len(self._l1) >= self._max_l1:
                self._l1.popitem(last=False)
        self._l1[key] = entry

    def _l1_invalidate(self, key: str = None):
        """L1 캐시 무효화"""
        if key and key in self._l1:
            del self._l1[key]
        elif key is None:
            self._l1.clear()

    # ── L2 디스크 카탈로그 ──────────────────────────

    def _l2_read(self) -> dict:
        """L2 카탈로그 읽기"""
        try:
            if self._l2_path.exists():
                return json.loads(self._l2_path.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {}

    def _l2_write(self, catalog: dict):
        """L2 카탈로그 쓰기"""
        try:
            self._l2_path.write_text(
                json.dumps(catalog, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
        except Exception:
            pass

    def _l2_update(self, file_path: str, mtime: float):
        """L2에 파일 메타데이터 업데이트"""
        catalog = self._l2_read()
        catalog[file_path] = {"mtime": mtime, "updated": time.time()}
        # 오래된 항목 정리 (1000개 제한)
        if len(catalog) > 1000:
            sorted_items = sorted(catalog.items(), key=lambda x: x[1].get("updated", 0))
            for k, _ in sorted_items[:len(sorted_items) - 1000]:
                del catalog[k]
        self._l2_write(catalog)

    # ── 공개 API ────────────────────────────────────

    def get_files(self, root: Path, extensions: Set[str],
                  exclude_dirs: Set[str]) -> List[Path]:
        """파일 목록 조회 (캐시 우선, mtime 변경 시 재스캔)"""
        cache_key = (str(root), tuple(sorted(extensions)),
                     tuple(sorted(exclude_dirs)))

        now = time.time()
        cached = self._file_list_cache.get(cache_key)
        if cached and (now - cached["time"]) < self._file_list_cache_ttl:
            return cached["results"]

        # 실제 스캔
        results = []
        root_str = str(root)
        try:
            for dirpath, dirnames, filenames in os.walk(root_str):
                rel_dir = os.path.relpath(dirpath, root_str)
                if rel_dir != ".":
                    parts = rel_dir.replace("\\", "/").split("/")
                    if any(part in exclude_dirs for part in parts):
                        dirnames.clear()
                        continue
                dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
                for fname in filenames:
                    ext = os.path.splitext(fname)[1]
                    if ext in extensions:
                        results.append(Path(dirpath) / fname)
        except (PermissionError, OSError):
            pass

        self._file_list_cache[cache_key] = {"results": results, "time": now}
        return results

    def get_content(self, file_path: Path) -> Optional[str]:
        """파일 내용 조회 (L1 캐시 우선)"""
        key = str(file_path)

        with self._lock:
            # L1 조회
            entry = self._l1_get(key)
            if entry is not None:
                # mtime 검증
                try:
                    current_mtime = file_path.stat().st_mtime
                    if current_mtime == entry.mtime:
                        return entry.content
                except OSError:
                    pass
                # mtime 변경됨 → L1 제거
                self._l1_invalidate(key)

        # 실제 파일 읽기
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            mtime = file_path.stat().st_mtime

            with self._lock:
                self._l1_put(key, CacheEntry(content, mtime))
                self._l2_update(key, mtime)

            return content
        except (OSError, PermissionError):
            return None

    def get_ast(self, file_path: Path, ast_func=None) -> Optional[object]:
        """파일 AST 조회 (L1 캐시, mtime 검증)"""
        key = f"{file_path}:ast"

        with self._lock:
            entry = self._l1_get(key)
            if entry is not None:
                try:
                    current_mtime = file_path.stat().st_mtime
                    if current_mtime == entry.mtime and entry.ast is not None:
                        return entry.ast
                except OSError:
                    pass

        # AST 생성
        if ast_func is None:
            return None

        try:
            content = self.get_content(file_path)
            if content is None:
                return None
            ast_result = ast_func(content, file_path.suffix)
            mtime = file_path.stat().st_mtime

            with self._lock:
                entry = CacheEntry(content, mtime)
                entry.ast = ast_result
                self._l1_put(key, entry)

            return ast_result
        except Exception:
            return None

    def invalidate(self, file_path: Path = None):
        """특정 파일(또는 전체) 캐시 무효화"""
        with self._lock:
            if file_path is not None:
                key = str(file_path)
                self._l1_invalidate(key)
                self._l1_invalidate(f"{key}:ast")
                # L2에서도 제거
                catalog = self._l2_read()
                if key in catalog:
                    del catalog[key]
                    self._l2_write(catalog)
            else:
                self._l1_invalidate()
                self._l2_write({})
                self._file_list_cache.clear()

    def stats(self) -> dict:
        """캐시 히트율, 크기 등 통계"""
        with self._lock:
            return {
                "l1_size": len(self._l1),
                "l1_max": self._max_l1,
                "l2_path": str(self._l2_path),
                "file_list_cache_size": len(self._file_list_cache),
            }
