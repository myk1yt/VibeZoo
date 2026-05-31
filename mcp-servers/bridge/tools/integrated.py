# VibeZoo Bridge — Integrated 도구 그룹
# review_project + find_bugs + suggest_refactor + generate_docs
# 점진적 스트리밍 지원 (streaming=True)

import inspect
import json
import os
import re
import time
from collections import defaultdict
from pathlib import Path
from typing import Optional

from bridge.config import (
    VERSION, DEFAULT_EXCLUDE_DIRS, SOURCE_EXTS,
)
from bridge.utils import (
    _markdown_header, _markdown_footer,
    _validate_string,
    _read_file_content, _truncate, _normalize_path,
    _iter_project_files, _iter_project_files_cached,
    get_project_root,
)
from bridge.crow_client import try_crow_ingest, try_crow_recall
from bridge.search_engine import SearchEngine
from bridge.ast_engine import AstEngine
from bridge.file_cache import FileCache
from bridge.tools._base import BaseTool

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
        "check_quality": None,
        "extract_patterns": None,
        "map_dependencies": None,
        "analyze_call_graph": None,
        "reverse_engineer": None,
        "summarize_architecture": None,
        "draw_on_whiteboard": None,
        "generate_tests": None,
        "analyze_coverage": None,
        "explain_code": None,
        "analyze_changes": None,
        "review_pr": None,
        "refactor_across_files": None,
        "learn_project": None,
        "recall_project": None,
        "learn_preference": None,
        "get_preferences": None,
    }

    # register가 호출될 때 다른 모듈의 도구를 참조할 수 있도록 지연 바인딩
    def _lazy_tool(name):
        if _tool_registry.get(name) is None:
            # 다른 모듈의 등록된 함수 찾기
            for mod_name, mod_fn in _tool_registry.items():
                if mod_name == name:
                    break
        return _tool_registry.get(name)

    # ── integrated 도구들은 지연 임포트로 내부 함수 참조 ──

    def _get_search_codebase():
        from bridge.tools.scout import search_codebase as fn
        _tool_registry["search_codebase"] = fn
        return fn

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

    def _get_map_dependencies():
        from bridge.tools.deep_analyzer import map_dependencies as fn
        _tool_registry["map_dependencies"] = fn
        return fn

    def _get_analyze_call_graph():
        from bridge.tools.deep_analyzer import analyze_call_graph as fn
        _tool_registry["analyze_call_graph"] = fn
        return fn

    def _get_reverse_engineer():
        from bridge.tools.deep_analyzer import reverse_engineer as fn
        _tool_registry["reverse_engineer"] = fn
        return fn

    def _get_summarize_architecture():
        from bridge.tools.scout import summarize_architecture as fn
        _tool_registry["summarize_architecture"] = fn
        return fn

    def _get_draw_on_whiteboard():
        from bridge.tools.whiteboard import draw_on_whiteboard as fn
        _tool_registry["draw_on_whiteboard"] = fn
        return fn

    def _get_analyze_changes():
        from bridge.tools.analysis import analyze_changes as fn
        _tool_registry["analyze_changes"] = fn
        return fn

    # ── 도구 등록 ──

    @mcp.tool
    def review_project(target_path: str, streaming: bool = True) -> str:
        """search_codebase + review_code + check_quality + extract_patterns 통합.
        프로젝트 전체를 종합 리뷰하여 하나의 마크다운 보고서로 반환합니다.
        streaming=True 시 각 단계별 진행 청크를 포함하여 LLM이 빠르게 첫 결과를 볼 수 있습니다.

        Args:
            target_path: 분석 대상 디렉토리 경로
            streaming: True면 각 단계별 진행 청크 포함 (기본: True)
        """
        err = _validate_string(target_path, "target_path")
        if err:
            return _markdown_header("Review Project Error", "❌") + f"**{err}**\n" + _markdown_footer()

        sections = []
        sections.append(_markdown_header("Project Review Report"))
        sections.append(f"> Target: `{target_path}`\n")

        # ── Stage 1/4: search_codebase (25%) ──
        if streaming:
            sections.append(BaseTool.progress_chunk("1/4", 25, "🔍 Searching codebase for TODO/FIXME/HACK/BUG patterns..."))
        sections.append("## 🔍 Code Search\n")
        search_terms = ["TODO", "FIXME", "HACK", "BUG"]
        for term in search_terms:
            fn = _get_search_codebase()
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
        for p in _iter_project_files_cached(root, extensions=SOURCE_EXTS, exclude_dirs=DEFAULT_EXCLUDE_DIRS):
            total_files += 1
        for p in _iter_project_files_cached(root, extensions=SOURCE_EXTS, exclude_dirs=DEFAULT_EXCLUDE_DIRS):
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
                "files_reviewed": reviewed,
                "total_files": total_files,
                "streaming": streaming,
                "timestamp": time.time(),
            }),
            register="style"
        )

        result = "\n\n---\n\n".join(sections)
        result += _markdown_footer()

        if streaming:
            stats = {"files_reviewed": reviewed, "total_files": total_files}
            result = BaseTool.final_result(result, stats)

        return result

    @mcp.tool
    def find_bugs(target_path: str) -> str:
        """extract_patterns + search_codebase(console.log|debugger|any) + Crow recall 통합.
        프로젝트에서 잠재적 버그를 찾아 마크다운으로 반환합니다.

        Args:
            target_path: 분석 대상 디렉토리 경로
        """
        err = _validate_string(target_path, "target_path")
        if err:
            return _markdown_header("Bug Finder Error", "❌") + f"**{err}**\n" + _markdown_footer()

        sections = []
        sections.append(_markdown_header("Bug Finder Report"))
        sections.append(f"> Target: `{target_path}`\n")

        # 1. extract_patterns
        sections.append("## 📊 Pattern Analysis\n")
        fn = _get_extract_patterns()
        patterns, ok = _run_tool("extract_patterns", target_path=target_path, min_occurrences=1)
        if ok:
            sections.append(patterns)
        else:
            sections.append(f"⚠️ Partial failure: {patterns}")

        # 2. search_codebase
        sections.append("## ⚠️ Suspicious Patterns\n")
        suspicious_queries = [
            "console.log", "debugger", ".only(", "fit(", "fdescribe",
            "TODO", "FIXME", "HACK", "XXX", "any", "as any",
            "@ts-ignore", "@ts-nocheck", "eslint-disable"
        ]
        found_suspicious = 0
        fn = _get_search_codebase()
        for query in suspicious_queries:
            result, ok = _run_tool("search_codebase", query=query, max_results=10)
            if ok:
                if "No results found" not in result and "Found 0" not in result:
                    sections.append(result)
                    found_suspicious += 1
            else:
                sections.append(f"⚠️ Partial failure: {result}")
                found_suspicious += 1

        if found_suspicious == 0:
            sections.append("- No suspicious patterns found.\n")

        # 3. Crow recall
        sections.append("## 🧠 Crow Memory Recall\n")
        crow_results = try_crow_recall(query="bug pattern error in project", register="bug", limit=10)
        if crow_results:
            sections.append("### Previous bug patterns from Crow memory:\n")
            for item in crow_results:
                content = item.get("content", item.get("value", str(item)))
                sections.append(f"- {_truncate(content, 300)}\n")
        else:
            sections.append("- No relevant bug patterns found in Crow memory.\n")

        bug_summary = {
            "action": "find_bugs",
            "target": target_path,
            "suspicious_count": found_suspicious,
            "crow_recall_count": len(crow_results),
            "timestamp": time.time(),
        }
        try_crow_ingest(json.dumps(bug_summary), register="bug")

        result = "\n\n---\n\n".join(sections)
        result += _markdown_footer()
        return result

    @mcp.tool
    def suggest_refactor(target_path: str) -> str:
        """map_dependencies + extract_patterns + analyze_call_graph 통합.
        프로젝트의 리팩터링 제안을 마크다운으로 반환합니다.

        Args:
            target_path: 분석 대상 디렉토리 경로
        """
        err = _validate_string(target_path, "target_path")
        if err:
            return _markdown_header("Refactoring Error", "❌") + f"**{err}**\n" + _markdown_footer()

        sections = []
        sections.append(_markdown_header("Refactoring Suggestions"))
        sections.append(f"> Target: `{target_path}`\n")

        # 1. map_dependencies
        sections.append("## 🔗 Dependency Map\n")
        fn = _get_map_dependencies()
        deps, ok = _run_tool("map_dependencies", target_path=target_path)
        if ok:
            sections.append(deps)
        else:
            sections.append(f"⚠️ Partial failure: {deps}")

        # 2. extract_patterns
        sections.append("## 📊 Pattern Duplication\n")
        fn = _get_extract_patterns()
        patterns, ok = _run_tool("extract_patterns", target_path=target_path, min_occurrences=5)
        if ok:
            sections.append(patterns)
        else:
            sections.append(f"⚠️ Partial failure: {patterns}")

        # 3. analyze_call_graph
        sections.append("## 📞 Call Graph\n")
        fn = _get_analyze_call_graph()
        callgraph, ok = _run_tool("analyze_call_graph", file_path=target_path, depth=3)
        if ok:
            sections.append(callgraph)
        else:
            sections.append(f"⚠️ Partial failure: {callgraph}")

        # 4. Crow recall
        style_rules = try_crow_recall(query="coding style rules patterns", register="style", limit=5)
        if style_rules:
            sections.append("\n\n## 🎨 Crow Style Rules\n")
            sections.append("### Previous coding style rules from Crow memory:\n")
            for item in style_rules:
                content = item.get("content", item.get("value", str(item)))
                sections.append(f"- {_truncate(content, 300)}\n")
            sections.append("\n")

        try_crow_ingest(
            json.dumps({
                "action": "suggest_refactor",
                "target": target_path,
                "style_rules_found": len(style_rules),
                "timestamp": time.time(),
            }),
            register="style"
        )

        result = "\n\n---\n\n".join(sections)
        result += _markdown_footer()
        return result

    @mcp.tool
    def generate_docs(target_path: str, output_format: str = "markdown") -> str:
        """reverse_engineer + summarize_architecture + draw_on_whiteboard(architecture diagram) 통합.
        프로젝트 문서를 자동 생성하고 아키텍처 다이어그램을 화이트보드에 그립니다.
        format='mermaid' 시 ERD 다이어그램을 함께 생성합니다.

        Args:
            target_path: 분석 대상 디렉토리 경로
            output_format: 출력 형식 (markdown, openapi, mermaid). 기본: markdown
        """
        err = _validate_string(target_path, "target_path")
        if err:
            return _markdown_header("Document Generation Error", "❌") + f"**{err}**\n" + _markdown_footer()

        allowed_formats = {"markdown", "openapi", "mermaid"}
        if output_format not in allowed_formats:
            return (_markdown_header("Document Generation Error", "❌")
                    + f"**Invalid format: `{output_format}`. Allowed: {', '.join(allowed_formats)}**\n"
                    + _markdown_footer())

        sections = []
        sections.append(_markdown_header("Auto-Generated Documentation"))
        sections.append(f"> Target: `{target_path}`  \n> Format: `{output_format}`\n")

        # 1. summarize_architecture
        sections.append("## 🏗️ Architecture Summary\n")
        fn = _get_summarize_architecture()
        arch, ok = _run_tool("summarize_architecture", target_path=target_path)
        if ok:
            sections.append(arch)
        else:
            sections.append(f"⚠️ Partial failure: {arch}")

        # 2. reverse_engineer
        sections.append("## 🔄 Reverse Engineering\n")
        fn = _get_reverse_engineer()
        rev, ok = _run_tool("reverse_engineer", target_path=target_path, output_format=output_format)
        if ok:
            sections.append(rev)
        else:
            sections.append(f"⚠️ Partial failure: {rev}")

        # 3. draw_on_whiteboard
        sections.append("## 🎨 Architecture Diagram (Whiteboard)\n")
        try:
            root = Path(get_project_root(target_path))
            commands = []
            entries = []

            def collect(p, depth=0):
                if depth > 2:
                    return
                try:
                    for child in sorted(p.iterdir()):
                        if child.name.startswith(".") or child.name in DEFAULT_EXCLUDE_DIRS:
                            continue
                        entries.append((child, depth))
                        if child.is_dir():
                            collect(child, depth + 1)
                except (PermissionError, OSError):
                    pass
            collect(root)

            y = 50
            x_offset = 80
            colors = ["#4ec9ff", "#6acb6a", "#d4a0ff", "#ffd700"]
            for i, (entry, depth) in enumerate(entries[:15]):
                indent = depth * 25
                color = colors[depth % len(colors)]
                icon = "📁" if entry.is_dir() else "📄"
                commands.append({
                    "type": "rect",
                    "props": {
                        "left": x_offset + indent, "top": y + i * 42,
                        "width": 200 - indent, "height": 34,
                        "fill": "transparent", "stroke": color, "rx": 4
                    }
                })
                commands.append({
                    "type": "text",
                    "props": {
                        "left": x_offset + indent + 8, "top": y + i * 42 + 8,
                        "text": f"{icon} {entry.name}",
                        "fontSize": 12, "fill": "#ffffff"
                    }
                })

            if commands:
                fn = _get_draw_on_whiteboard()
                draw_result, ok = _run_tool("draw_on_whiteboard", commands=json.dumps(commands))
                if ok:
                    sections.append(f"- {draw_result}")
                else:
                    sections.append(f"⚠️ Partial failure (whiteboard): {draw_result}")
            else:
                sections.append("- No directory structure to visualize.\n")

        except Exception as e:
            sections.append(f"- Could not draw diagram: `{e}`\n")

        try_crow_ingest(f"generate_docs completed for {target_path} (format={output_format})", register="arch")

        result = "\n\n---\n\n".join(sections)
        result += _markdown_footer()
        return result
