"""
VibeZoo Bridge — Editor 도구 그룹
apply_patch: AI-safe apply_diff 대체 도구 (path 생략 가능, fuzzy 매칭, 자동 백업)
"""

import difflib
import json
import os
import re
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from bridge.config import VERSION
from bridge.utils import (
    _iter_project_files_cached,
    _markdown_footer,
    _markdown_header,
    _normalize_path,
    get_project_root,
)
# Pylance path fix
_EXT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _EXT_ROOT not in sys.path:
    sys.path.insert(0, _EXT_ROOT)


BACKUP_DIR = Path.home() / ".vibezoo-backup"


def _parse_diff(diff: str) -> list[dict]:
    """diff 파싱: SEARCH/REPLACE 블록 추출

    상호 운용성: `=======` (apply_diff) 및 `-------` (apply_patch) 모두 지원.
    `:start_line:` 메타데이터는 무시하고 건너뛰는 라인을 생략함.
    """
    blocks = []
    # 줄바꿈 정규화: \r\n, \r, \n, literal \\n 모두 처리
    diff = diff.replace("\\n", "\n").replace("\r\n", "\n").replace("\r", "\n")
    lines = diff.split("\n")
    search_lines = []
    replace_lines = []
    current = None  # 'search' | 'replace' | 'meta' (선택적)
    for line in lines:
        raw = line
        stripped = line.strip()
        if stripped == "<<<<<<< SEARCH":
            current = "search"
            search_lines = []
            replace_lines = []
            continue
        # 양쪽 구분자 모두 지원: ======= (apply_diff) + ------- (apply_patch)
        if stripped in ("-------", "======="):
            if current == "meta":
                # :start_line: 다음의 ------- → search 모드로 전환
                current = "search"
                continue
            current = "replace"
            continue
        if stripped == ">>>>>>> REPLACE":
            if search_lines and replace_lines:
                blocks.append({
                    "search": "\n".join(search_lines).strip(),
                    "replace": "\n".join(replace_lines).strip(),
                })
            search_lines = []
            replace_lines = []
            current = None
            continue
        # :start_line: 메타데이터 처리 (선택적 무시)
        if stripped.startswith(":start_line:"):
            if current == "search":
                current = "meta"  # 다음 ------- 까지 메타 모드
            continue
        if current == "search":
            search_lines.append(raw)
        elif current == "replace":
            replace_lines.append(raw)
        # current == "meta" or None → 라인 무시
    # 미완료 블록 처리
    if search_lines and replace_lines:
        blocks.append({
            "search": "\n".join(search_lines).strip(),
            "replace": "\n".join(replace_lines).strip(),
        })
    return blocks
def _find_file_by_content(content_sample: str, target_path: str, max_candidates: int = 5) -> list[Path]:
    """내용 샘플과 일치하는 파일 검색"""
    root = Path(get_project_root(target_path))
    if not root.is_dir():
        return []
    candidates = []
    for p in _iter_project_files_cached(root):
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
            if content_sample in text:
                candidates.append(p)
        except Exception:
            continue
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[:max_candidates]


def _find_best_location(text: str, search_block: str, cutoff: float = 0.85) -> Optional[tuple[int, int]]:
    """Fuzzy 매칭으로 SEARCH 블록 위치 찾기"""
    matcher = difflib.SequenceMatcher(None, text, search_block, autojunk=False)
    ratio = matcher.ratio()
    if ratio >= 1.0:
        idx = text.find(search_block)
        return (idx, idx + len(search_block))
    if ratio >= cutoff:
        for m in re.finditer(re.escape(search_block[:20]), text):
            start = max(0, m.start() - 50)
            end = min(len(text), m.end() + 50)
            window = text[start:end]
            if search_block in window or difflib.SequenceMatcher(None, window, search_block).ratio() >= cutoff:
                actual_start = text.find(window[:50], start)
                if actual_start >= 0:
                    return (actual_start, actual_start + len(window))
    return None


def _backup_file(path: Path) -> Optional[Path]:
    """파일 백업 생성"""
    date_str = datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.now().strftime("%H-%M-%S")
    bak_dir = BACKUP_DIR / date_str
    bak_dir.mkdir(parents=True, exist_ok=True)
    bak_name = f"{time_str}_{path.name}_{path.stat().st_size}_{path.stat().st_mtime_ns % 1000000:06d}.bak"
    bak_path = bak_dir / bak_name
    try:
        shutil.copy2(path, bak_path)
        return bak_path
    except Exception:
        return None


def _apply_patch_impl(
    path: Optional[str] = None,
    diff: str = "",
    target_path: Optional[str] = None,
) -> str:
    """apply_patch 실제 구현"""
    # 1. diff 파싱
    blocks = _parse_diff(diff)
    if not blocks:
        return _markdown_header("Apply Patch Error", "❌") + "**`diff`에서 SEARCH/REPLACE 블록을 찾을 수 없습니다.**\n\n올바른 형식:\n```\n<<<<<<< SEARCH\n찾을 내용\n-------\n교체할 내용\n>>>>>>> REPLACE\n```\n" + _markdown_footer()

    # 2. 파일 결정
    file_path: Optional[Path] = None
    if path:
        p = Path(path)
        if not p.is_absolute():
            root = Path(get_project_root(target_path))
            p = root / p
        if p.exists() and p.is_file():
            file_path = p
        else:
            return _markdown_header("Apply Patch Error", "❌") + f"**파일을 찾을 수 없습니다:** `{path}`\n" + _markdown_footer()

    # 3. path가 없으면 내용으로 파일 찾기
    if file_path is None:
        search_sample = blocks[0]["search"][:100]
        candidates = _find_file_by_content(search_sample, target_path or os.getcwd())
        if not candidates:
            return _markdown_header("Apply Patch Error", "❌") + "**`path`가 지정되지 않았고, `diff` 내용과 일치하는 파일도 찾을 수 없습니다.**\n\n`path`에 파일 경로를 명시적으로 지정해주세요.\n" + _markdown_footer()
        if len(candidates) == 1:
            file_path = candidates[0]
        else:
            # 여러 후보 — 첫 번째 자동 선택
            file_path = candidates[0]

    # 4. 파일 읽기
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        return _markdown_header("Apply Patch Error", "❌") + f"**파일 읽기 실패:** `{file_path}`\n```\n{e}\n```\n" + _markdown_footer()

    # 5. 백업
    bak = _backup_file(file_path)
    bak_info = f" (백업: `{bak}`)" if bak else " (백업 실패)"

    # 6. 각 블록 적용
    modified = content
    applied = 0
    errors = []
    for i, block in enumerate(blocks):
        search_text = block["search"].strip()
        replace_text = block["replace"].strip()

        # 정확 매칭 시도
        if search_text in modified:
            modified = modified.replace(search_text, replace_text, 1)
            applied += 1
            continue

        # Fuzzy 매칭 시도
        loc = _find_best_location(modified, search_text)
        if loc:
            modified = modified[:loc[0]] + replace_text + modified[loc[1]:]
            applied += 1
            continue

        errors.append(f"  블록 {i+1}: SEARCH 내용을 찾을 수 없습니다 (유사도 85% 이상 필요)")

    # 7. 결과 출력
    if errors:
        output = _markdown_header("Apply Patch", "⚠️") + f"**{applied}/{len(blocks)}** 블록 적용됨{bak_info}\n\n"
        for e in errors:
            output += f"- {e}\n"
        output += "\n**수동으로 적용하거나 `path`와 `diff`를 확인해주세요.**\n"
        return output + _markdown_footer()

    # 8. 파일 쓰기
    try:
        file_path.write_text(modified, encoding="utf-8")
    except Exception as e:
        return _markdown_header("Apply Patch Error", "❌") + f"**파일 쓰기 실패:** `{file_path}`\n```\n{e}```\n" + _markdown_footer()

    return _markdown_header("Apply Patch", "✅") + f"**{applied}/{len(blocks)}** 블록 적용됨 → `{_normalize_path(str(file_path))}`{bak_info}\n" + _markdown_footer()


# ── MCP 도구 등록 ──────────────────────────

def register(mcp):
    @mcp.tool
    def apply_patch(
        path: Optional[str] = None,
        diff: str = "",
        target_path: Optional[str] = None,
    ) -> str:
        """diff(SEARCH/REPLACE)를 파일에 적용합니다. path가 없으면 diff 내용으로 자동 감지합니다.
        
        Args:
            path: 대상 파일 경로 (생략 가능, diff 내용으로 자동 감지)
            diff: SEARCH/REPLACE 블록 (<<<<<<< SEARCH ... ------- ... >>>>>>> REPLACE 형식)
            target_path: 프로젝트 루트 (상대경로 기준, 기본: 현재 워크스페이스)
        """
        return _apply_patch_impl(path, diff, target_path)
