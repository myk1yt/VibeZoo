"""
VibeZoo Bridge — Editor 도구 그룹
apply_patch: AI-safe apply_diff 대체 도구 (path 생략 가능, fuzzy 매칭, 자동 백업)
Pillar 1: AST-Guided Smart Ellipsis & Transactional Patching
"""

import difflib
import os
import re
import shutil
import sys
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


# ── Ellipsis Detection ───────────────────────────────────


def _detect_ellipsis(search_block: str) -> Optional[dict]:
    """SEARCH 블록에서 ellipsis 패턴 감지 및 header/footer 분리.

    감지 패턴:
      - Python:   r'^\\s*#\\s*\\.{2,}.*$'       (# ... existing code ...)
      - JS/TS/C:  r'^\\s*//\\s*\\.{2,}.*$'      (// ... rest ...)
      - Block:    r'/\\*\\s*\\.{2,}.*\\*/\\s*$'    (/* ... */)

    Returns:
        {"header": str, "footer": str, "style": str,
         "header_lines": int, "footer_lines": int} 또는 None
    """
    lines = search_block.split('\n')
    ellipsis_indices = []

    for i, line in enumerate(lines):
        stripped = line.strip()
        # Python comment ellipsis: # ...
        if re.match(r'^#\s*\.{2,}.*$', stripped):
            ellipsis_indices.append(i)
        # Line comment ellipsis: // ...
        elif re.match(r'^//\s*\.{2,}.*$', stripped):
            ellipsis_indices.append(i)
        # Block comment ellipsis: /* ... */
        elif re.match(r'^/\*\s*\.{2,}\s*\*/\s*$', stripped):
            ellipsis_indices.append(i)

    if not ellipsis_indices:
        return None

    # header: lines before first ellipsis
    first_ell = ellipsis_indices[0]
    last_ell = ellipsis_indices[-1]

    header_lines = lines[:first_ell]
    footer_lines = lines[last_ell + 1:]

    header = '\n'.join(header_lines)
    footer = '\n'.join(footer_lines)

    # Ellipsis at start or end → header or footer empty → not meaningful
    if not header.strip() or not footer.strip():
        return None

    # Detect style
    ellipsis_line = lines[first_ell].strip()
    if re.match(r'^#\s*\.{2,}', ellipsis_line):
        style = 'python_comment'
    elif re.match(r'^//\s*\.{2,}', ellipsis_line):
        style = 'line_comment'
    else:
        style = 'block_comment'

    return {
        "header": header,
        "footer": footer,
        "style": style,
        "header_lines": len(header_lines),
        "footer_lines": len(footer_lines),
    }


def _resolve_ellipsis_text(file_content: str, file_path: str, ellipsis_info: dict) -> Optional[str]:
    """파일 내용에서 header/footer 사이의 실제 코드를 찾아 ellipsis를 대체.

    1차 텍스트 기반 해결:
      - header를 _find_best_location()(cutoff=0.70)으로 파일에서 매칭
      - footer를 header_end 이후에서만 검색
      - 중간 텍스트 추출 → header + middle + footer 재구성
      - 재구성된 텍스트가 파일에 exact match되는지 최종 검증
    """
    header_text = ellipsis_info["header"]
    footer_text = ellipsis_info["footer"]

    # 1. Find header location
    header_loc = _find_best_location(file_content, header_text, cutoff=0.70)
    if not header_loc:
        return None

    header_start, header_end = header_loc

    # 2. Find footer location — search only after header_end
    after_header = file_content[header_end:]
    footer_loc = _find_best_location(after_header, footer_text, cutoff=0.70)
    if not footer_loc:
        return None
    footer_start_in_after = footer_loc[0]

    footer_start = header_end + footer_start_in_after
    footer_end = footer_start + len(footer_text)

    # 3. Extract middle text (the gap)
    middle = file_content[header_end:footer_start]

    # 4. Reconstruct: header + middle + footer
    resolved = header_text + middle + footer_text

    # 5. Verify exact match in file_content
    if resolved not in file_content:
        # Try normalizing whitespace
        normalized = '\n'.join(resolved.split('\n'))
        if normalized in file_content:
            return normalized
        return None

    return resolved


def _resolve_ellipsis_ast(file_path: str, file_content: str, ellipsis_info: dict) -> Optional[str]:
    """AST 기반 검증: header/footer가 동일 부모 scope에 있는지 확인.

    2차 AST 기반 검증 (try/except 전체 감싸기):
      - AstEngine().parse(file_content, ext)로 AST 파싱
      - header/footer 노드 찾기
      - 두 노드가 동일 부모 scope에 있는지 검증
      - 실패 시 return None (caller가 text 결과 사용)
      - tree-sitter 미설치 시도 return None
    """
    try:
        from bridge.ast_engine import AstEngine

        ext = Path(file_path).suffix
        engine = AstEngine()
        ast = engine.parse(file_content, ext)

        if not ast or (not ast.get("functions") and not ast.get("classes")):
            return None  # tree-sitter not available → text fallback

        header_lines = ellipsis_info.get("header_lines", 0)
        footer_lines = ellipsis_info.get("footer_lines", 0)

        if header_lines <= 0 or footer_lines <= 0:
            return None

        # Calculate line numbers for header end and footer start
        header_end_line = header_lines  # 1-based line where header ends
        footer_start_line = max(1, len(file_content.split('\n')) - footer_lines + 1)

        # Find which function/class contains header end
        header_scope = _find_scope_for_line(ast, header_end_line)
        footer_scope = _find_scope_for_line(ast, footer_start_line)

        if not header_scope or not footer_scope:
            return None

        # Both must be in the same scope
        if header_scope != footer_scope:
            return None

        # Same scope → text-based result is valid
        # Reconstruct with actual gap from file content
        lines = file_content.split('\n')
        if header_end_line <= len(lines) and footer_start_line <= len(lines):
            gap_lines = lines[header_end_line:footer_start_line - 1]
            middle = '\n'.join(gap_lines)
            resolved = ellipsis_info["header"] + '\n' + middle + '\n' + ellipsis_info["footer"]
            if resolved in file_content:
                return resolved

        return None
    except Exception:
        return None  # Caller will use text fallback


def _find_scope_for_line(ast: dict, line_number: int) -> Optional[str]:
    """AST 결과에서 특정 라인이 속한 함수/클래스 스코프 찾기."""
    # Check functions
    for func in ast.get("functions", []):
        func_line = func.get("line", 0)
        func_end = func.get("end_line", 0)
        if func_line <= line_number <= func_end:
            return f"function:{func.get('name', 'unknown')}"

    # Check classes
    for cls in ast.get("classes", []):
        cls_line = cls.get("line", 0)
        cls_end = cls.get("end_line", 0)
        if cls_line <= line_number <= cls_end:
            return f"class:{cls.get('name', 'unknown')}"

    # Check interfaces (TS/JS)
    for iface in ast.get("interfaces", []):
        iface_line = iface.get("line", 0)
        iface_end = iface.get("end_line", 0)
        if iface_line <= line_number <= iface_end:
            return f"interface:{iface.get('name', 'unknown')}"

    return None


def _preprocess_blocks(blocks: list[dict], file_path: Path, file_content: str) -> list[dict]:
    """모든 블록 순회하며 ellipsis 감지 → 해결.

    v2.0 변경:
      - D2: _resolve_file() 제거, 직접 read_text() 사용
      - D5: encoding="utf-8", errors="replace" 명시
    """
    for block in blocks:
        ellipsis = _detect_ellipsis(block["search"])
        if not ellipsis:
            block["_had_ellipsis"] = False
            continue

        # 1차: 텍스트 기반 해결
        resolved = _resolve_ellipsis_text(file_content, str(file_path), ellipsis)

        # 2차: AST 기반 검증 (선택적, 실패 시 text 결과 유지)
        if resolved:
            ast_resolved = _resolve_ellipsis_ast(str(file_path), file_content, ellipsis)
            if ast_resolved:
                resolved = ast_resolved

        if resolved:
            block["_original_search"] = block["search"]
            block["search"] = resolved
            block["_had_ellipsis"] = True
        else:
            block["_ellipsis_failed"] = True
            block["_had_ellipsis"] = False

    return blocks


# ── Path Validation ──────────────────────────────────────


def _resolve_and_validate_path(path_str: str) -> Optional[Path]:
    """경로 검증: normpath()로 정규화, 프로젝트 루트 벗어나면 None.

    v2.0 D4: path traversal 방지.
    """
    if not path_str:
        return None

    normalized = os.path.normpath(path_str)
    p = Path(normalized)

    if not p.is_absolute():
        root = Path(get_project_root(""))
        p = (root / p).resolve()

    # Path traversal 검증: 프로젝트 루트 바깥이면 거부
    project_root = Path(get_project_root("")).resolve()
    try:
        p.resolve().relative_to(project_root)
    except ValueError:
        return None  # 프로젝트 루트 바깥 경로

    if p.exists() and p.is_file():
        return p

    return None


# ── Similarity Computation ──────────────────────────────


def _compute_best_similarity(text: str, search_block: str) -> float:
    """텍스트 내에서 SEARCH 블록과 가장 유사한 위치의 유사도 계산 (진단용)."""
    matcher = difflib.SequenceMatcher(None, text, search_block, autojunk=False)
    best = matcher.ratio()

    # Sliding window approach for better accuracy
    search_len = len(search_block)
    if search_len < 10:
        return best

    step = max(1, search_len // 10)
    for start in range(0, max(1, len(text) - search_len), step):
        window = text[start:start + search_len]
        if len(window) < 10:
            continue
        ratio = difflib.SequenceMatcher(None, window, search_block, autojunk=False).ratio()
        if ratio > best:
            best = ratio

    return best


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


# ── Transactional Patching ──────────────────────────────


def _format_success_report(blocks: list[dict], results: list, file_path: Path, bak: Optional[Path]) -> str:
    """성공 보고서 포맷."""
    bak_info = f" (백업: `{_normalize_path(str(bak))}`)" if bak else " (백업 실패)"
    output = _markdown_header("Apply Patch", "✅")

    for i, (_, ok, reason, detail) in enumerate(results):
        if ok:
            output += f"- ✅ 블록 {i+1}: 적용됨"
            if detail.get("had_ellipsis"):
                output += " (ellipsis 해결됨)"
            output += f" @ line {detail.get('line', '?')}\n"

    output += f"\n**{sum(1 for r in results if r[1])}/{len(blocks)}** 블록 적용됨 -> `{_normalize_path(str(file_path))}`{bak_info}\n"
    return output + _markdown_footer()


def _format_failure_report(blocks: list[dict], results: list, file_path: Path, content: str) -> str:
    """실패한 블록에 대한 상세 보고서 생성.

    각 블록의 상세 진단: 검색 미리보기, 최고 유사도, 원본 SEARCH 텍스트
    """
    output = _markdown_header("Apply Patch", "❌")

    success_count = sum(1 for r in results if r[1])
    fail_index = -1
    for i, (_, ok, _, _) in enumerate(results):
        if not ok:
            fail_index = i
            break

    output += f"**{success_count}/{len(blocks)}** 블록 적용 성공 "
    if fail_index >= 0:
        output += f"(블록 {fail_index+1} 실패로 롤백됨)\n\n"
    else:
        output += "\n\n"
    output += "⚠️ 파일은 수정되지 않았습니다 (원자적 롤백).\n\n"

    for i, (_, ok, reason, detail) in enumerate(results):
        if ok:
            output += f"- ✅ 블록 {i+1}: 적용됨"
            if detail.get("had_ellipsis"):
                output += " (ellipsis 해결됨)"
            output += f" @ line {detail.get('line', '?')}\n"
        else:
            output += f"- ❌ 블록 {i+1}: 실패 - {reason}\n"
            if reason == "ellipsis_resolution_failed":
                original = detail.get("original_search_preview", "?")
                output += f"  원본 검색어: `{original}`\n"
            elif reason == "not_found":
                output += f"  검색 미리보기: `{detail.get('search_preview', '?')}`\n"
                output += f"  최고 유사도: {detail.get('similarity', 0):.1%}\n"

    # Diff suggestion for failed block
    if fail_index >= 0 and fail_index < len(blocks) and content:
        failed_block = blocks[fail_index]
        failed_search = failed_block.get("_original_search", failed_block["search"])
        output += "\n### 💡 제안: 파일 현재 상태 기준 SEARCH 블록\n"
        output += f"실패한 블록의 SEARCH 텍스트와 가장 유사한 실제 코드를 찾지 못했습니다.\n"
        output += f"원본 SEARCH (처음 80자): `{failed_search[:80].replace(chr(10), '\\\\n')}`\n"

    return output + _markdown_footer()


def _apply_patch_transactional(
    path: Optional[str] = None,
    diff: str = "",
    target_path: Optional[str] = None,
) -> str:
    """apply_patch 트랜잭셔널 구현.

    Phase 1: Dry-Run — 모든 블록을 가상 버퍼에 순차 적용
    Phase 2: Commit — 모두 성공 시에만 디스크 쓰기 + 백업
    Phase 2 (Rollback) — 하나라도 실패 시 virtual 폐기, 상세 실패 보고서 반환
    """
    # ── Phase 0: 파싱 및 파일 결정 ──
    blocks = _parse_diff(diff)
    if not blocks:
        return _markdown_header("Apply Patch Error", "❌") + "**`diff`에서 SEARCH/REPLACE 블록을 찾을 수 없습니다.**\n\n올바른 형식:\n```\n<<<<<<< SEARCH\n찾을 내용\n-------\n교체할 내용\n>>>>>>> REPLACE\n```\n" + _markdown_footer()

    # 파일 결정
    file_path: Optional[Path] = None
    if path:
        # D4: 경로 검증
        resolved = _resolve_and_validate_path(path)
        if resolved:
            file_path = resolved
        else:
            p = Path(path)
            if not p.is_absolute():
                root = Path(get_project_root(target_path))
                p = root / p
            if p.exists() and p.is_file():
                # 추가 검증: 프로젝트 루트 내 확인
                project_root = Path(get_project_root(target_path)).resolve()
                try:
                    p.resolve().relative_to(project_root)
                    file_path = p
                except ValueError:
                    return _markdown_header("Apply Patch Error", "❌") + f"**경로가 프로젝트 루트를 벗어났습니다:** `{path}`\n" + _markdown_footer()
            else:
                return _markdown_header("Apply Patch Error", "❌") + f"**파일을 찾을 수 없습니다:** `{path}`\n" + _markdown_footer()

    if file_path is None:
        search_sample = blocks[0]["search"][:100]
        candidates = _find_file_by_content(search_sample, target_path or os.getcwd())
        if not candidates:
            return _markdown_header("Apply Patch Error", "❌") + "**`path`가 지정되지 않았고, `diff` 내용과 일치하는 파일도 찾을 수 없습니다.**\n\n`path`에 파일 경로를 명시적으로 지정해주세요.\n" + _markdown_footer()
        file_path = candidates[0]

    # ── 파일 읽기 (D5: 명시적 인코딩) ──
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return _markdown_header("Apply Patch Error", "❌") + f"**파일 읽기 실패:** `{file_path}`\n```\n{e}\n```\n" + _markdown_footer()

    # ── Ellipsis 전처리 ──
    blocks = _preprocess_blocks(blocks, file_path, content)

    # ── Phase 1: Dry-Run (가상 버퍼) ──
    virtual = content
    results = []  # [(block_index, success, reason, detail_dict), ...]

    for i, block in enumerate(blocks):
        search_text = block["search"].strip()
        replace_text = block["replace"].strip()

        # Already failed ellipsis resolution → skip
        if block.get("_ellipsis_failed"):
            results.append((i, False, "ellipsis_resolution_failed", {
                "error": "SEARCH 블록의 생략 기호(ellipsis)를 해결할 수 없습니다",
                "original_search_preview": block.get("_original_search", search_text)[:100],
            }))
            break

        # Exact match
        if search_text in virtual:
            virtual = virtual.replace(search_text, replace_text, 1)
            line_no = virtual[:virtual.find(replace_text)].count('\n') + 1
            results.append((i, True, "applied", {
                "line": line_no,
                "had_ellipsis": block.get("_had_ellipsis", False),
            }))
            continue

        # Fuzzy match
        loc = _find_best_location(virtual, search_text)
        if loc:
            virtual = virtual[:loc[0]] + replace_text + virtual[loc[1]:]
            line_no = virtual[:loc[0]].count('\n') + 1
            results.append((i, True, "applied", {
                "line": line_no,
                "had_ellipsis": block.get("_had_ellipsis", False),
            }))
            continue

        # Failure — record details and break
        search_preview = search_text[:80].replace('\n', '\\n')
        results.append((i, False, "not_found", {
            "search_preview": search_preview,
            "similarity": _compute_best_similarity(content, search_text),
        }))
        break

    # ── Phase 2: Commit or Rollback ──
    all_success = all(r[1] for r in results)

    if all_success:
        bak = _backup_file(file_path)
        try:
            file_path.write_text(virtual, encoding="utf-8")
        except Exception as e:
            return _markdown_header("Apply Patch Error", "❌") + f"**파일 쓰기 실패:** `{file_path}`\n```\n{e}```\n" + _markdown_footer()
        return _format_success_report(blocks, results, file_path, bak)
    else:
        # virtual 버퍼 폐기 (아무것도 쓰지 않음) — 원자적 롤백
        return _format_failure_report(blocks, results, file_path, content)


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
        return _apply_patch_transactional(path, diff, target_path)
