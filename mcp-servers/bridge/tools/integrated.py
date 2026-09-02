# VibeZoo Bridge — Integrated 도구 그룹
# review_project — 집계형 도구 제거 뒤 남은 통합 도구 (매뉴얼 조합 지침은 plan §4 참조)
# 점진적 스트리밍 지원 (streaming=True)

import inspect
import json
import os
import re
import time
from collections import defaultdict
from pathlib import Path
import sys
# Pylance: ensure the extension root is in package search path
_EXT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _EXT_ROOT not in sys.path:
    sys.path.insert(0, _EXT_ROOT)
from typing import Optional

from bridge.config import (
    VERSION, DEFAULT_EXCLUDE_DIRS, SOURCE_EXTS, CONFIG_FILES,
)
from bridge.utils import (
    _markdown_header, _markdown_footer,
    _validate_string,
    _read_file_content, _truncate, _normalize_path,
    _iter_project_files, _iter_project_files_cached,
    get_project_root,
    truncate_to_tokens,
)
from bridge.crow_client import try_crow_ingest, try_crow_recall
from bridge.search_engine import SearchEngine
from bridge.ast_engine import AstEngine
from bridge.file_cache import FileCache
from bridge.tools._base import BaseTool
from bridge.i18n import t

# ── 내부 도구 호출 ──────────────────────────────────

_tool_registry = {}


def _run_tool(name: str, timeout: float = 30.0, **kwargs):
    """내부적으로 기존 MCP 도구 함수를 호출하여 결과를 문자열로 반환."""
    fn = _tool_registry.get(name)
    if not fn:
        return (f"**Tool not found:** `{name}`", False)

    sig = inspect.signature(fn)
    filtered = {k: v for k, v in kwargs.items() if k in sig.parameters}

    try:
        result = fn(**filtered)
        return (str(result), True)
    except Exception as e:
        error_msg = (
            f"**Error in `{name}`:**\n"
            f"- Exception: `{type(e).__name__}: {e}`\n"
            f"- Parameters: {json.dumps(filtered, default=str, ensure_ascii=False)[:500]}\n"
        )
        return (error_msg, False)


def register(mcp):
    """Integrated 도구 등록"""
    # 도구 레퍼런스 저장
    global _tool_registry
    _tool_registry = {
        "search_codebase": None,
        "review_code": None,
        "extract_patterns": None,
        "map_dependencies": None,
        "analyze_call_graph": None,
        "reverse_engineer": None,
        "summarize_architecture": None,
        "draw_on_whiteboard": None,
    }

    # ── FileCache 워밍 (첫 번째 도구 호출 시 미리 스캔) ──
    try:
        from bridge.file_cache import FileCache
        from bridge.config import DEFAULT_EXCLUDE_DIRS, SOURCE_EXTS
        from pathlib import Path
        cache = FileCache()
        root = Path(os.getcwd())
        cache.warm(root=root, extensions=SOURCE_EXTS, exclude_dirs=DEFAULT_EXCLUDE_DIRS)
    except Exception:
        pass  # 워밍 실패는 치명적이지 않음

    # ── integrated 도구들은 지연 임포트로 내부 함수 참조 ──

    def _get_review_code():
        from bridge.tools.reviewer import review_code as fn
        _tool_registry["review_code"] = fn
        return fn

    def _get_check_quality():
        from bridge.tools.reviewer import check_quality as fn
        _tool_registry["check_quality"] = fn
        return fn

    def _get_extract_patterns():
        from bridge.tools.deep_analyzer import extract_patterns as fn
        _tool_registry["extract_patterns"] = fn
        return fn

    # ── 도구 등록 ──

    @mcp.tool
    def review_project(target_path: Optional[str] = None, streaming: bool = True,
                       mode: str = "summary", max_tokens: int = 500) -> str:
        """search_codebase + review_code + check_quality + extract_patterns 통합.
        프로젝트 전체를 종합 리뷰하여 하나의 마크다운 보고서로 반환합니다.
        streaming=True 시 각 단계별 진행 청크를 포함하여 LLM이 빠르게 첫 결과를 볼 수 있습니다.

        Args:
            target_path: 분석 대상 디렉토리 경로 (생략 시 현재 작업 디렉토리 사용)
            streaming: True면 각 단계별 진행 청크 포함 (기본: True)
            mode: "summary" (기본) — 핵심 요약만 (파일 수, 주요 발견, 등급) 1000자 이내
                  "full" — 전체 상세 보고서 (기존 동작)
            max_tokens: LLM 컨텍스트 제한 (기본: 500). 0이면 전체.
        """
        if target_path is None:
            target_path = os.getcwd()
        err = _validate_string(target_path, "target_path")
        if err:
            return _markdown_header("Review Project Error", "❌") + f"**{err}**\n" + _markdown_footer()

        sections = []
        sections.append(_markdown_header("Project Review Report"))
        sections.append(f"> Target: `{target_path}`  \n> Mode: `{mode}`  \n> Max tokens: `{max_tokens if max_tokens > 0 else 'unlimited'}`\n")

        if mode == "summary":
            # ── Summary 모드: 핵심 요약만 (1000자 이내) ──
            root = Path(get_project_root(target_path))
            total_files = 0
            todo_count = 0
            func_count = 0
            class_count = 0
            for p in _iter_project_files_cached(root, extensions=SOURCE_EXTS, exclude_dirs=DEFAULT_EXCLUDE_DIRS, include_names=CONFIG_FILES):
                total_files += 1
                content = _read_file_content(p)
                if content:
                    todo_count += len(re.findall(r'(TODO|FIXME|HACK|XXX)', content))
                    func_count += len(re.findall(r'(?:function|async function|def\s+)', content))
                    class_count += len(re.findall(r'\bclass\s+\w+', content))

            from bridge.tools.reviewer import _review_project_core
            quality_result = _review_project_core(target_path, mode="quality")
            grade_match = re.search(r'Grade\s*:\s*`([^`]+)`', quality_result)
            grade = grade_match.group(1) if grade_match else "N/A"
            score_match = re.search(r'Score\s*:\s*([\d.]+)/100', quality_result)
            score = score_match.group(1) if score_match else "N/A"

            sections.append("## Summary\n\n")
            sections.append(f"- **Source files**: {total_files}\n")
            sections.append(f"- **Functions**: {func_count}\n")
            sections.append(f"- **Classes**: {class_count}\n")
            sections.append(f"- **TODO/FIXME markers**: {todo_count}\n")
            sections.append(f"- **Quality grade**: `{grade}` (score: {score}/100)\n\n")

            # 캐시 통계 포함
            from bridge.file_cache import FileCache
            cache = FileCache()
            cache_stats = cache.stats()
            sections.append(f"<details>\n<summary>📊 Cache Statistics</summary>\n\n")
            sections.append(f"- L1 size: {cache_stats.get('l1_size', 0)}/{cache_stats.get('l1_max', 50)}\n")
            sections.append(f"- L2 path: {cache_stats.get('l2_path', 'N/A')}\n")
            sections.append(f"</details>\n\n")
        else:
            # ── Full 모드: 기존 상세 보고서 ──
            # ── Stage 1/4: search_codebase (25%) ──
            if streaming:
                sections.append(BaseTool.progress_chunk("1/4", 25, "🔍 Searching codebase for TODO/FIXME/HACK/BUG patterns..."))
            sections.append("## 🔍 Code Search\n")
            search_terms = ["TODO", "FIXME", "HACK", "BUG"]
            for term in search_terms:
                term_result, ok = _run_tool("search_codebase", query=term, max_results=10)
                if ok:
                    if "No results found" not in term_result and "Found 0" not in term_result:
                        sections.append(term_result)
                else:
                    sections.append(f"⚠️ Partial failure: {term_result}")

            # ── Stage 2/4: review_code (50%) ──
            if streaming:
                sections.append(BaseTool.progress_chunk("2/4", 50, "📝 Reviewing source files (top 5)..."))
            sections.append("## 📝 Code Review\n")
            root = Path(get_project_root(target_path))
            reviewed = 0
            total_files = 0
            for p in _iter_project_files_cached(root, extensions=SOURCE_EXTS, exclude_dirs=DEFAULT_EXCLUDE_DIRS, include_names=CONFIG_FILES):
                total_files += 1
            for p in _iter_project_files_cached(root, extensions=SOURCE_EXTS, exclude_dirs=DEFAULT_EXCLUDE_DIRS, include_names=CONFIG_FILES):
                if reviewed >= 5:
                    sections.append(f"\n> ... and more files (reviewed top 5 of {total_files} total)\n")
                    break
                fn = _get_review_code()
                review, ok = _run_tool("review_code", file_path=str(p))
                if ok:
                    sections.append(review)
                else:
                    sections.append(f"⚠️ Partial failure: {review}")
                reviewed += 1

            if reviewed == 0:
                sections.append("- No source files found to review.\n")

            # ── Stage 3/4: check_quality (75%) ──
            if streaming:
                sections.append(BaseTool.progress_chunk("3/4", 75, "📊 Analyzing project quality metrics..."))
            sections.append("## ✅ Quality Check\n")
            fn = _get_check_quality()
            quality, ok = _run_tool("check_quality", target_path=target_path)
            if ok:
                sections.append(quality)
            else:
                sections.append(f"⚠️ Partial failure: {quality}")

            # ── Stage 4/4: extract_patterns (100%) ──
            if streaming:
                sections.append(BaseTool.progress_chunk("4/4", 100, "🔬 Extracting recurring code patterns..."))
            sections.append("## 📊 Pattern Analysis\n")
            fn = _get_extract_patterns()
            patterns, ok = _run_tool("extract_patterns", target_path=target_path, min_occurrences=3)
            if ok:
                sections.append(patterns)
            else:
                sections.append(f"⚠️ Partial failure: {patterns}")

        # Crow ingest
        try_crow_ingest(
            json.dumps({
                "action": "review_project",
                "target": target_path,
                "mode": mode,
                "max_tokens": max_tokens,
                "streaming": streaming,
                "timestamp": time.time(),
            }),
            register="style"
        )

        result = "\n\n---\n\n".join(sections)
        result += _markdown_footer()

        if streaming and mode == "full":
            stats = {"files_reviewed": reviewed, "total_files": total_files}
            result = BaseTool.final_result(result, stats)

        return truncate_to_tokens(result, max_tokens)
