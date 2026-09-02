# VibeZoo Bridge — Integrated 도구 그룹
# review_project + find_bugs + suggest_refactor + generate_docs
# 점진적 스트리밍 지원 (streaming=True)

import inspect
import json
import os
import re
import subprocess
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
from bridge.i18n import t
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

# ── 내부 도구 호출 ──────────────────────────────────

_tool_registry = {}


def _run_tool(name: str, timeout: float = 30.0, **kwargs):
    """내부적으로 기존 MCP 도구 함수를 호출하여 결과를 문자열로 반환."""
    fn = _tool_registry.get(name)
    if not fn:
        return (f"**{t('Tool not found: `{0}`', name)}**", False)

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


# ── ESLint / tsc 헬퍼 ───────────────────────────────


def _run_eslint(root: Path) -> Optional[list]:
    """ESLint 실행 (--format json), 결과 반환.
    실패 시 None 반환 (조용한 폴백).
    """
    try:
        if not (root / "package.json").exists():
            return None
        result = subprocess.run(
            ["npx", "eslint", ".", "--format", "json", "--quiet"],
            cwd=str(root), capture_output=True, text=True, timeout=30
        )
        if result.stdout.strip():
            return json.loads(result.stdout)
    except Exception:
        pass
    return None


def _run_tsc(root: Path) -> Optional[str]:
    """tsc --noEmit 실행, 출력 반환.
    실패 시 None 반환 (조용한 폴백).
    """
    try:
        if not (root / "package.json").exists():
            return None
        result = subprocess.run(
            ["npx", "tsc", "--noEmit"],
            cwd=str(root), capture_output=True, text=True, timeout=60
        )
        combined = (result.stdout or "") + "\n" + (result.stderr or "")
        if combined.strip():
            return combined
    except Exception:
        pass
    return None


def _run_native_linter(root: Path) -> dict:
    """프로젝트 루트의 빌드 파일을 감지하여 모든 매칭되는 네이티브 린터를 순차 실행.

    감지 순서 (모두 실행, 결과 누적):
    1. Cargo.toml → cargo clippy --frozen
    2. go.mod → go vet -mod=readonly
    3. CMakeLists.txt / Makefile → cppcheck
    4. package.json → eslint + tsc (기존)

    Returns:
        {
            "language": str,           # primary language detected
            "tool": str,               # primary tool name
            "success": bool,
            "results": list[dict],     # C2 fix: 모든 린터 결과 누적
            "raw_output": str (truncated),
        }
    """
    diagnostics = {
        "language": "unknown",
        "tool": "none",
        "success": False,
        "results": [],     # C2: return 제거, 모든 결과 누적
        "raw_output": "",
    }

    # ── 1. Rust: cargo clippy (C4: --frozen 추가, M4: timeout 120s) ──
    if (root / "Cargo.toml").exists():
        diagnostics["language"] = "rust"
        diagnostics["tool"] = "cargo-clippy"
        try:
            res = subprocess.run(
                ["cargo", "clippy", "--message-format=json", "--all-targets", "--frozen"],
                cwd=str(root), capture_output=True, text=True, timeout=120
            )
            diagnostics["raw_output"] = _truncate(res.stdout + res.stderr, 3000)
            warnings_list = []
            errors_list = []
            for line in res.stdout.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if data.get("reason") == "compiler-message":
                    msg = data.get("message", {})
                    spans = msg.get("spans", [])
                    item = {
                        "file": spans[0].get("file_name", "unknown") if spans else "unknown",
                        "line": spans[0].get("line_start", 0) if spans else 0,
                        "column": spans[0].get("column_start", 0) if spans else 0,
                        "message": msg.get("message", ""),
                        "rule": (msg.get("code") or {}).get("code", "clippy"),
                        "level": msg.get("level", "warning"),
                    }
                    if msg.get("level") == "error":
                        errors_list.append(item)
                    else:
                        warnings_list.append(item)
            diagnostics["results"].append({
                "tool": "cargo-clippy",
                "success": True,
                "errors": errors_list,
                "warnings": warnings_list,
            })
        except FileNotFoundError:
            diagnostics["results"].append({
                "tool": "cargo-clippy", "success": False,
                "error": t("cargo not found in PATH. Install Rust: https://rustup.rs"),
            })
        except subprocess.TimeoutExpired:
            diagnostics["results"].append({
                "tool": "cargo-clippy", "success": False,
                "error": t("cargo clippy timed out (120s)"),
            })
        except Exception as e:
            diagnostics["results"].append({
                "tool": "cargo-clippy", "success": False,
                "error": f"cargo clippy error: {e}",
            })
        # C2 fix: return 제거 → 다음 린터 계속 실행

    # ── 2. Go: go vet (C4: -mod=readonly 추가, M4: timeout 60s) ──
    if (root / "go.mod").exists():
        if diagnostics["language"] == "unknown":
            diagnostics["language"] = "go"
            diagnostics["tool"] = "go-vet"
        try:
            res = subprocess.run(
                ["go", "vet", "-mod=readonly", "./..."],
                cwd=str(root), capture_output=True, text=True, timeout=60
            )
            diagnostics["raw_output"] = _truncate(
                diagnostics["raw_output"] + "\n" + _truncate(res.stderr, 2000), 3000)
            warnings_list = []
            for line in res.stderr.splitlines():
                m = re.match(r'^([^:]+):(\d+):(?:\d+:)?\s*(.*)$', line.strip())
                if m:
                    warnings_list.append({
                        "file": m.group(1),
                        "line": int(m.group(2)),
                        "message": m.group(3).strip(),
                        "rule": "go_vet",
                        "level": "warning",
                    })
            diagnostics["results"].append({
                "tool": "go-vet",
                "success": True,
                "warnings": warnings_list,
            })
        except FileNotFoundError:
            diagnostics["results"].append({
                "tool": "go-vet", "success": False,
                "error": t("go not found in PATH. Install Go: https://go.dev/dl"),
            })
        except subprocess.TimeoutExpired:
            diagnostics["results"].append({
                "tool": "go-vet", "success": False,
                "error": t("go vet timed out (60s)"),
            })
        except Exception as e:
            diagnostics["results"].append({
                "tool": "go-vet", "success": False,
                "error": f"go vet error: {e}",
            })
        # C2 fix: return 제거

    # ── 3. C++: cppcheck (M3: xml.etree.ElementTree 사용, M4: timeout 120s) ──
    if (root / "CMakeLists.txt").exists() or any(root.glob("Makefile*")):
        if diagnostics["language"] == "unknown":
            diagnostics["language"] = "c/c++"
            diagnostics["tool"] = "cppcheck"
        try:
            res = subprocess.run(
                ["cppcheck", "--enable=all", "--xml", "."],
                cwd=str(root), capture_output=True, text=True, timeout=120
            )
            diagnostics["raw_output"] = _truncate(
                diagnostics["raw_output"] + "\n" + _truncate(res.stdout + res.stderr, 2000), 3000)
            # M3: xml.etree.ElementTree 로 속성 순서 무관 파싱
            import xml.etree.ElementTree as ET
            try:
                root_elem = ET.fromstring(res.stderr + res.stdout)
                warnings_list = []
                for error_elem in root_elem.findall(".//error"):
                    item = {
                        "file": error_elem.get("file", "unknown"),
                        "line": int(error_elem.get("line", 0)),
                        "message": error_elem.get("msg", ""),
                        "rule": f"cppcheck:{error_elem.get('id', '')}",
                        "level": error_elem.get("severity", "warning"),
                    }
                    warnings_list.append(item)
                diagnostics["results"].append({
                    "tool": "cppcheck",
                    "success": True,
                    "warnings": warnings_list,
                })
            except ET.ParseError:
                diagnostics["results"].append({
                    "tool": "cppcheck", "success": False,
                    "error": t("Failed to parse cppcheck XML output"),
                })
        except FileNotFoundError:
            diagnostics["results"].append({
                "tool": "cppcheck", "success": False,
                "error": t("cppcheck not found in PATH. Install: `winget install cppcheck` or `apt install cppcheck`"),
            })
        except subprocess.TimeoutExpired:
            diagnostics["results"].append({
                "tool": "cppcheck", "success": False,
                "error": t("cppcheck timed out (120s)"),
            })
        except Exception as e:
            diagnostics["results"].append({
                "tool": "cppcheck", "success": False,
                "error": f"cppcheck error: {e}",
            })
        # C2 fix: return 제거

    # ── 4. TS/JS: eslint + tsc (기존) ──
    if (root / "package.json").exists():
        if diagnostics["language"] == "unknown":
            diagnostics["language"] = "typescript/javascript"
            diagnostics["tool"] = "eslint+tsc"
        diagnostics["results"].append({
            "tool": "eslint+tsc",
            "success": True,
            "note": "ESLint/tsc results integrated separately",
        })

    diagnostics["success"] = any(r.get("success", False) for r in diagnostics["results"])
    return diagnostics


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

    def _get_search_codebase():
        from bridge.tools.scout import _search_codebase_impl as fn
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
        from bridge.tools.scout import _summarize_architecture_impl as fn
        _tool_registry["summarize_architecture"] = fn
        return fn

    def _get_draw_on_whiteboard():
        from bridge.tools.whiteboard import draw_on_whiteboard as fn
        _tool_registry["draw_on_whiteboard"] = fn
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
                sections.append(f"- {t('No source files found to review.')}\n")

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

    @mcp.tool
    def find_bugs(target_path: Optional[str] = None, mode: str = "summary", max_tokens: int = 500) -> str:
        """extract_patterns + search_codebase(console.log|debugger|any) + Crow recall 통합.
        프로젝트에서 잠재적 버그를 찾아 마크다운으로 반환합니다.
        ESLint/tsc 결과를 LLM 분석용 데이터 구조로 변환하여 포함합니다.

        Args:
            target_path: 분석 대상 디렉토리 경로 (생략 시 현재 작업 디렉토리 사용)
            mode: "summary" (기본) — 핵심 발견만 1000자 이내
                  "full" — 전체 상세 보고서
            max_tokens: LLM 컨텍스트 제한 (기본: 500). 0이면 전체.
        """
        if target_path is None:
            target_path = os.getcwd()
        err = _validate_string(target_path, "target_path")
        if err:
            return _markdown_header("Bug Finder Error", "❌") + f"**{err}**\n" + _markdown_footer()

        sections = []
        sections.append(_markdown_header("Bug Finder Report"))
        sections.append(f"> Target: `{target_path}`  \n> Mode: `{mode}`  \n> Max tokens: `{max_tokens if max_tokens > 0 else 'unlimited'}`\n")

        from bridge.tool_context import make_find_bugs_context

        # 캐시 워밍 + 통계
        from bridge.file_cache import FileCache
        cache = FileCache()
        cache_stats = cache.stats()

        suspicious_queries = [
            "console.log", "debugger", ".only(", "fit(", "fdescribe",
            "TODO", "FIXME", "HACK", "XXX", "any", "as any",
            "@ts-ignore", "@ts-nocheck", "eslint-disable"
        ]
        found_suspicious = 0
        suspicious_results = []

        if mode == "summary":
            # ── Summary 모드: 핵심 발견만 ──
            fn = _get_search_codebase()
            for query in suspicious_queries:
                result, ok = _run_tool("search_codebase", query=query, max_results=5)
                if ok:
                    line_count = len([l for l in result.split("\n") if l.strip().startswith("- `")])
                    if line_count > 0:
                        suspicious_results.append({"pattern": query, "count": line_count})
                        found_suspicious += 1
            sections.append("## ⚠️ Suspicious Patterns\n\n")
            if suspicious_results:
                for sr in suspicious_results:
                    sections.append(f"- `{sr['pattern']}`: {sr['count']} occurrence(s)\n")
            else:
                sections.append(f"- {t('No suspicious patterns found.')}\n")

            # ── Native Linter 실행 (모든 매칭 린터 순차 실행, C2 반영) ──
            root = Path(get_project_root(target_path))
            native_diag = _run_native_linter(root)

            if native_diag.get("results"):
                sections.append(f"\n## 🔬 Native Linter Results\n\n")
                for result in native_diag["results"]:
                    tool = result.get("tool", "unknown")
                    if result.get("success"):
                        total_warnings = len(result.get("warnings", []))
                        total_errors = len(result.get("errors", []))
                        if total_errors > 0 or total_warnings > 0:
                            sections.append(f"### {tool} — ⚠️ {total_errors} errors, {total_warnings} warnings\n")
                            for w in result.get("errors", [])[:3]:
                                sections.append(f"- ❌ `{w['file']}:{w['line']}` — [{w.get('rule','')}] {w.get('message','')[:100]}\n")
                            for w in result.get("warnings", [])[:3]:
                                sections.append(f"- ⚠️ `{w['file']}:{w['line']}` — [{w.get('rule','')}] {w.get('message','')[:100]}\n")
                        else:
                            sections.append(f"### {tool} — ✅ No issues\n")
                    else:
                        sections.append(f"### {tool} — ❌ {result.get('error', 'Unknown error')}\n")
            else:
                sections.append(f"\n## 🔬 Native Linter\n\n- {t('No supported linter environment detected.')}\n")

            # ESLint/tsc (native linter 미감지 시에만 fallback)
            if native_diag["language"] in ("unknown", "typescript/javascript"):
                eslint_data = _run_eslint(root)
                tsc_output = _run_tsc(root)

                if eslint_data:
                    total_issues = sum(len(f.get("messages", [])) for f in eslint_data if isinstance(f, dict))
                    files_with_issues = len([f for f in eslint_data if isinstance(f, dict) and f.get('messages')])
                    if total_issues > 0:
                        sections.append(f"\n## 🔬 ESLint\n\n")
                        sections.append(f"- **Issues**: {total_issues} in {files_with_issues} file(s)\n")

                if tsc_output:
                    ts_errors = len(re.findall(r'error TS\d+', tsc_output))
                    ts_warnings = len(re.findall(r'warning TS\d+', tsc_output))
                    if ts_errors > 0 or ts_warnings > 0:
                        sections.append(f"\n## 🔷 tsc\n\n")
                        sections.append(f"- **Errors**: {ts_errors}, **Warnings**: {ts_warnings}\n")

            sections.append("\n## 🧠 Crow Memory\n\n")
            crow_results = try_crow_recall(query="bug pattern error in project", register="bug", limit=5)
            if crow_results:
                for item in crow_results[:2]:
                    content = item.get("content", item.get("value", str(item)))
                    sections.append(f"- {_truncate(content, 200)}\n")
            else:
                sections.append(f"- {t('No relevant bug patterns found.')}\n")

            # 캐시 통계
            sections.append(f"\n<details>\n<summary>📊 Cache Statistics</summary>\n\n")
            sections.append(f"- L1 size: {cache_stats.get('l1_size', 0)}/{cache_stats.get('l1_max', 50)}\n")
            sections.append(f"- File list cache: {cache_stats.get('file_list_cache_size', 0)} entries\n")
            sections.append(f"</details>\n\n")

        else:
            # ── Full 모드: 기존 상세 보고서 ──
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
                sections.append(f"- {t('No suspicious patterns found.')}\n")

            # 3. Crow recall
            sections.append("## 🧠 Crow Memory Recall\n")
            crow_results = try_crow_recall(query="bug pattern error in project", register="bug", limit=10)
            if crow_results:
                sections.append("### Previous bug patterns from Crow memory:\n")
                for item in crow_results:
                    content = item.get("content", item.get("value", str(item)))
                    sections.append(f"- {_truncate(content, 300)}\n")
            else:
                sections.append(f"- {t('No relevant bug patterns found in Crow memory.')}\n")

            # 4. ESLint/tsc 실행 (조용한 폴백)
            root = Path(get_project_root(target_path))
            eslint_data = _run_eslint(root)
            tsc_output = _run_tsc(root)

            if eslint_data:
                sections.append("\n## 🔬 ESLint Analysis (LLM-ready data)\n\n")
                sections.append("<!-- LLM_TASK\n")
                sections.append("도구: find_bugs\n")
                sections.append("버전: 1.0\n")
                sections.append("설명: ESLint 결과 + 코드 패턴 + Crow Memory 통합 분석\n")
                sections.append("LLM 지시사항: 각 발견을 심각도(P0/P1/P2)로 분류하고, 위치/원인/수정 제안 포함\n")
                sections.append("-->\n\n")
                total_issues = sum(len(f.get("messages", [])) for f in eslint_data if isinstance(f, dict))
                sections.append(f"- **Total ESLint issues**: {total_issues}\n")
                sections.append(f"- **Files with issues**: {len([f for f in eslint_data if isinstance(f, dict) and f.get('messages')])}\n\n")
                # 상위 10개 이슈
                all_msgs = []
                for f in eslint_data:
                    if isinstance(f, dict):
                        for msg in f.get("messages", []):
                            all_msgs.append({
                                "file": f.get("filePath", ""),
                                "line": msg.get("line", 0),
                                "rule": msg.get("ruleId", "unknown"),
                                "severity": msg.get("severity", 0),
                                "message": msg.get("message", ""),
                            })
                for msg in all_msgs[:10]:
                    sections.append(f"- `{os.path.relpath(msg['file'], root)}:{msg['line']}` — [{msg['rule']}] {msg['message'][:120]}\n")

            if tsc_output:
                sections.append("\n## 🔷 TypeScript Compiler Output\n\n")
                sections.append("```\n")
                sections.append(_truncate(tsc_output, 2000))
                sections.append("\n```\n")
                # 에러 카운트
                ts_errors = len(re.findall(r'error TS\d+', tsc_output))
                ts_warnings = len(re.findall(r'warning TS\d+', tsc_output))
                sections.append(f"\n- **tsc errors**: {ts_errors}\n")
                sections.append(f"- **tsc warnings**: {ts_warnings}\n")

            # 캐시 통계
            sections.append(f"\n<details>\n<summary>📊 Cache Statistics</summary>\n\n")
            sections.append(f"- L1 size: {cache_stats.get('l1_size', 0)}/{cache_stats.get('l1_max', 50)}\n")
            sections.append(f"- File list cache: {cache_stats.get('file_list_cache_size', 0)} entries\n")
            sections.append(f"</details>\n\n")

        bug_summary = {
            "action": "find_bugs",
            "target": target_path,
            "mode": mode,
            "max_tokens": max_tokens,
            "suspicious_count": found_suspicious,
            "crow_recall_count": len(try_crow_recall(query="bug pattern error in project", register="bug", limit=1)) if mode == "full" else 0,
            "timestamp": time.time(),
        }
        try_crow_ingest(json.dumps(bug_summary), register="bug")

        result = "\n\n---\n\n".join(sections)
        result += _markdown_footer()
        return truncate_to_tokens(result, max_tokens)

    @mcp.tool
    def suggest_refactor(target_path: Optional[str] = None, mode: str = "summary", max_tokens: int = 500) -> str:
        """map_dependencies + extract_patterns + analyze_call_graph 통합.
        프로젝트의 리팩터링 제안을 마크다운으로 반환합니다.

        Args:
            target_path: 분석 대상 디렉토리 경로 (생략 시 현재 작업 디렉토리 사용)
            mode: "summary" (기본) — 핵심 제안 3~5개만 (각 50자 내외) + 등급
                  "full" — 전체 상세 보고서 (기존 동작)
            max_tokens: LLM 컨텍스트 제한 (기본: 500). 0이면 전체.
        """
        if target_path is None:
            target_path = os.getcwd()
        err = _validate_string(target_path, "target_path")
        if err:
            return _markdown_header("Refactoring Error", "❌") + f"**{err}**\n" + _markdown_footer()

        sections = []
        sections.append(_markdown_header("Refactoring Suggestions"))
        sections.append(f"> Target: `{target_path}`  \n> Mode: `{mode}`  \n> Max tokens: `{max_tokens if max_tokens > 0 else 'unlimited'}`\n")

        if mode == "summary":
            # ── Summary 모드: 핵심 제안 3~5개만 (각 50자 내외) + 등급 ──
            root = Path(get_project_root(target_path))

            # map_dependencies 간략 정보
            deps, ok = _run_tool("map_dependencies", target_path=target_path)
            has_cycles = "✅ No circular dependencies" not in deps if ok else False
            hub_count = len(re.findall(r'`(.+?)`:\s*\*{0,2}(\d+)\*{0,2}\s*imports?', deps)) if ok else 0

            # extract_patterns 간략 정보
            patterns, ok = _run_tool("extract_patterns", target_path=target_path, min_occurrences=3)
            pattern_count = len(re.findall(r'###\s+\d+\.', patterns)) if ok else 0

            # File stats
            total_files = 0
            for p in _iter_project_files_cached(root, extensions=SOURCE_EXTS, exclude_dirs=DEFAULT_EXCLUDE_DIRS, include_names=CONFIG_FILES):
                total_files += 1

            sections.append("## Refactoring Suggestions (Summary)\n\n")
            grade = "A"
            suggestions = []

            if has_cycles:
                suggestions.append("순환 의존성 감지 — 분해 전략 필요")
                grade = "C"
            if hub_count > 5:
                suggestions.append(f"허브 모듈 {hub_count}개 — 과도한 의존성 분산 필요")
                if grade == "A":
                    grade = "B"
            if pattern_count > 3:
                suggestions.append(f"중복 패턴 {pattern_count}개 — 공통 추출 권장")
                if grade == "A":
                    grade = "B"
            if total_files > 50:
                suggestions.append(f"대규모 프로젝트 ({total_files} 파일) — 모듈화 고려")
            else:
                suggestions.append("프로젝트 규모 양호 — 현재 구조 유지 가능")

            sections.append(f"- **Grade**: `{grade}`\n")
            sections.append(f"- **Source files**: {total_files}\n")
            sections.append(f"- **Circular deps**: {'⚠️ Yes' if has_cycles else '✅ No'}\n")
            sections.append(f"- **Hub modules**: {hub_count}\n")
            sections.append(f"- **Duplicated patterns**: {pattern_count}\n\n")
            sections.append("### Key Suggestions\n")
            for s in suggestions[:5]:
                sections.append(f"- {s}\n")

            # Cache stats
            from bridge.file_cache import FileCache
            cache = FileCache()
            cache_stats = cache.stats()
            sections.append(f"\n<details>\n<summary>📊 Cache Statistics</summary>\n\n")
            sections.append(f"- L1 size: {cache_stats.get('l1_size', 0)}/{cache_stats.get('l1_max', 50)}\n")
            sections.append(f"- File list cache: {cache_stats.get('file_list_cache_size', 0)} entries\n")
            sections.append(f"</details>\n\n")

        else:
            # ── Full 모드: 기존 상세 보고서 ──
            # 1. map_dependencies
            sections.append("## 🔗 Dependency Map\n")
            deps, ok = _run_tool("map_dependencies", target_path=target_path)
            if ok:
                sections.append(deps)
            else:
                sections.append(f"⚠️ Partial failure: {deps}")

            # 2. extract_patterns
            sections.append("## 📊 Pattern Duplication\n")
            patterns, ok = _run_tool("extract_patterns", target_path=target_path, min_occurrences=5)
            if ok:
                sections.append(patterns)
            else:
                sections.append(f"⚠️ Partial failure: {patterns}")

            # 3. analyze_call_graph
            sections.append("## 📞 Call Graph\n")
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
                "mode": mode,
                "max_tokens": max_tokens,
                "style_rules_found": len(style_rules) if mode == "full" else 0,
                "timestamp": time.time(),
            }),
            register="style"
        )

        result = "\n\n---\n\n".join(sections)
        result += _markdown_footer()
        return truncate_to_tokens(result, max_tokens)

    @mcp.tool
    def generate_docs(target_path: Optional[str] = None, output_format: str = "markdown",
                      mode: str = "summary", max_tokens: int = 500) -> str:
        """reverse_engineer + summarize_architecture + draw_on_whiteboard(architecture diagram) 통합.
        프로젝트 문서를 자동 생성하고 아키텍처 다이어그램을 화이트보드에 그립니다.
        format='mermaid' 시 ERD 다이어그램을 함께 생성합니다.

        Args:
            target_path: 분석 대상 디렉토리 경로 (생략 시 현재 작업 디렉토리 사용)
            output_format: 출력 형식 (markdown, openapi, mermaid). 기본: markdown
            mode: "summary" (기본) — 핵심 요약만
                  "full" — 전체 상세 보고서 (기존 동작)
            max_tokens: LLM 컨텍스트 제한 (기본: 500). 0이면 전체.
        """
        if target_path is None:
            target_path = os.getcwd()
        err = _validate_string(target_path, "target_path")
        if err:
            return _markdown_header("Document Generation Error", "❌") + f"**{err}**\n" + _markdown_footer()

        allowed_formats = {"markdown", "openapi", "mermaid"}
        if output_format not in allowed_formats:
            return (_markdown_header("Document Generation Error", "❌")
                    + f"**{t('Invalid format: `{0}`. Allowed: {1}', output_format, ', '.join(allowed_formats))}**\n"
                    + _markdown_footer())

        sections = []
        sections.append(_markdown_header("Auto-Generated Documentation"))
        sections.append(f"> Target: `{target_path}`  \n> Format: `{output_format}`  \n> Mode: `{mode}`\n")

        from bridge.file_cache import FileCache
        cache = FileCache()

        if mode == "summary":
            # ── Summary 모드: 핵심 요약만 ──
            root = Path(get_project_root(target_path))
            techs = {
                "package.json": "Node.js/TypeScript",
                "go.mod": "Go",
                "Cargo.toml": "Rust",
                "pyproject.toml": "Python",
                "requirements.txt": "Python (pip)",
                "pom.xml": "Java/Maven",
                "Gemfile": "Ruby",
            }
            found_techs = [tech for file, tech in techs.items() if (root / file).exists()]

            total_files = 0
            for p in _iter_project_files_cached(root, extensions=SOURCE_EXTS, exclude_dirs=DEFAULT_EXCLUDE_DIRS, include_names=CONFIG_FILES):
                total_files += 1

            output = f"- **Project**: `{root.name}`\n"
            output += f"- **Tech Stack**: {', '.join(found_techs) if found_techs else 'Auto-detect'}\n"
            output += f"- **Source files**: {total_files}\n"
            output += f"- **Format**: {output_format}\n\n"

            # 캐시 통계
            cache_stats = cache.stats()
            output += f"<details>\n<summary>📊 Cache Statistics</summary>\n\n"
            output += f"- L1 size: {cache_stats.get('l1_size', 0)}/{cache_stats.get('l1_max', 50)}\n"
            output += f"- File list cache: {cache_stats.get('file_list_cache_size', 0)} entries\n"
            output += f"</details>\n\n"

            sections.append(output)
        else:
            # ── Full 모드: 기존 상세 보고서 ──
            # 1. summarize_architecture
            sections.append("## 🏗️ Architecture Summary\n")
            fn = _get_summarize_architecture()
            arch, ok = _run_tool("summarize_architecture", target_path=target_path, mode="full")
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
                    sections.append(f"- {t('No directory structure to visualize.')}\n")

            except Exception as e:
                sections.append(f"- Could not draw diagram: `{e}`\n")

            # 캐시 통계
            cache_stats = cache.stats()
            sections.append(f"\n<details>\n<summary>📊 Cache Statistics</summary>\n\n")
            sections.append(f"- L1 size: {cache_stats.get('l1_size', 0)}/{cache_stats.get('l1_max', 50)}\n")
            sections.append(f"- File list cache: {cache_stats.get('file_list_cache_size', 0)} entries\n")
            sections.append(f"</details>\n\n")

        try_crow_ingest(f"generate_docs completed for {target_path} (format={output_format}, mode={mode})", register="arch")

        result = "\n\n---\n\n".join(sections)
        result += _markdown_footer()
        return truncate_to_tokens(result, max_tokens)
