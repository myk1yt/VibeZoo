# VibeZoo Bridge — Reviewer 도구 그룹
# review_code + check_quality (→ _review_project_core 위임)

import json
import os
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Optional

from bridge.config import (
    VERSION, DEFAULT_EXCLUDE_DIRS, SOURCE_EXTS, TS_JS_EXTS,
)
from bridge.utils import (
    _markdown_header, _markdown_footer,
    _validate_string, _validate_file_path,
    _read_file_content, _truncate, _normalize_path,
    _iter_project_files, _iter_project_files_cached,
    _npx_cmd, get_project_root,
)
from bridge.crow_client import try_crow_ingest, try_crow_recall
from bridge.ast_engine import AstEngine

# ── 싱글톤 ──────────────────────────────────────────

_ast_engine = None


def _get_ast_engine() -> AstEngine:
    global _ast_engine
    if _ast_engine is None:
        _ast_engine = AstEngine()
    return _ast_engine


# ── AST 기반 복잡도/중첩 계산 ────────────────────────


def _compute_cyclomatic_complexity(content: str, ext: str) -> int:
    """Cyclomatic complexity: 분기문(if/for/while/switch/catch) 카운팅"""
    if ext in TS_JS_EXTS:
        branches = (
            len(re.findall(r'\bif\s*\(', content))
            + len(re.findall(r'\bfor\s*\(', content))
            + len(re.findall(r'\bwhile\s*\(', content))
            + len(re.findall(r'\bswitch\s*\(', content))
            + len(re.findall(r'\bcatch\s*\(', content))
            + len(re.findall(r'\bcase\s+', content))
        )
    elif ext == '.py':
        branches = (
            len(re.findall(r'\bif\s+', content))
            + len(re.findall(r'\bfor\s+', content))
            + len(re.findall(r'\bwhile\s+', content))
            + len(re.findall(r'\bexcept\s+', content))
            + len(re.findall(r'\belif\s+', content))
        )
    else:
        branches = (
            len(re.findall(r'\bif\s*\(', content))
            + len(re.findall(r'\bfor\s*\(', content))
            + len(re.findall(r'\bwhile\s*\(', content))
        )
    return branches + 1  # 기본 경로 + 분기


def _compute_nesting_depth(content: str, ext: str, max_check: int = 100) -> int:
    """들여쓰기 기반 중첩 깊이 계산 (최대 max_check 줄만 검사)"""
    lines = content.split("\n")[:max_check]
    max_depth = 0
    for line in lines:
        stripped = line.rstrip()
        if not stripped or stripped.startswith(('\n', '\r')):
            continue
        # 탭/공백 들여쓰기 계산
        indent = len(line) - len(line.lstrip())
        depth = indent // 4 if indent > 0 else 0  # 공백 4 = 1단계
        if depth > max_depth:
            max_depth = depth
    return max_depth


# ── _review_project_core — review_project 내부 구현 ──


def _review_project_core(target_path: str, mode: str = "quality") -> str:
    """review_project의 내부 구현 — mode="quality"로 품질 검사만 수행

    Args:
        target_path: 분석 대상 경로
        mode: "quality" (품질 검사) | "full" (전체 리뷰)

    Returns:
        마크다운 보고서
    """
    root = Path(get_project_root(target_path))
    output = _markdown_header("Code Quality Check")

    source_files = list(_iter_project_files_cached(root, extensions=SOURCE_EXTS, exclude_dirs=DEFAULT_EXCLUDE_DIRS))
    total_files = len(source_files)
    total_lines = 0
    long_lines = 0
    todo_count = 0
    empty_catch_count = 0
    console_log_count = 0
    debugger_count = 0
    any_type_count = 0
    ts_ignore_count = 0
    empty_except_count = 0
    func_count_total = 0
    class_count_total = 0

    # Cyclomatic complexity 집계
    complexity_scores = []
    # 파일별 품질 등급 (A~F)
    file_grades: dict[str, str] = {}
    # 코드 중복도 (n-gram 기반 간단 탐지)
    code_duplication_scores: list[str] = []

    for p in source_files:
        content = _read_file_content(p)
        if content is None:
            continue
        lines = content.split("\n")
        ext = p.suffix.lower()
        rel = _normalize_path(str(p))
        total_lines += len(lines)
        long_lines += sum(1 for l in lines if len(l) > 120)
        todo_count += len(re.findall(r'(TODO|FIXME|HACK|XXX)', content))
        empty_catch_count += len(re.findall(r'catch\s*\([^)]*\)\s*\{\s*\}', content))
        console_log_count += len(re.findall(r'console\.(log|warn|error|debug)', content))
        debugger_count += len(re.findall(r'\bdebugger\b', content))
        any_type_count += len(re.findall(r':\s*any\b', content))
        ts_ignore_count += len(re.findall(r'@ts-ignore|@ts-nocheck', content))
        empty_except_count += len(re.findall(r'except\s*:', content))
        func_count_total += len(re.findall(r'(?:function|async function|def\s+)', content))
        class_count_total += len(re.findall(r'\bclass\s+\w+', content))

        # Cyclomatic complexity (파일당)
        comp = _compute_cyclomatic_complexity(content, ext)
        complexity_scores.append(comp)

        # 파일별 품질 등급
        file_issues = 0
        if len(re.findall(r'(TODO|FIXME|HACK|XXX)', content)) > 0:
            file_issues += 1
        if comp > 20:
            file_issues += 1
        if len(lines) > 500:
            file_issues += 1
        if sum(1 for l in lines if len(l) > 120) > 5:
            file_issues += 1

        if file_issues == 0:
            file_grades[rel] = "A"
        elif file_issues == 1:
            file_grades[rel] = "B"
        elif file_issues == 2:
            file_grades[rel] = "C"
        elif file_issues == 3:
            file_grades[rel] = "D"
        else:
            file_grades[rel] = "F"

    output += "## Quality Metrics\n\n"
    output += f"- Source files: {total_files}\n"
    output += f"- Total lines: {total_lines}\n"
    output += f"- Functions: {func_count_total}\n"
    output += f"- Classes: {class_count_total}\n\n"

    issues_found = 0
    severity_scores = []

    if long_lines > 0:
        ratio = long_lines / max(total_lines, 1) * 100
        w = "⚠️" if ratio > 1 else "📏"
        output += f"- {w} Lines >120 chars: {long_lines} ({ratio:.1f}%)\n"
        severity_scores.append(("long_lines", ratio))
        issues_found += 1
    if todo_count > 0:
        ratio = todo_count / max(total_files, 1)
        w = "⚠️" if ratio > 0.5 else "📝"
        output += f"- {w} TODO/FIXME markers: {todo_count}\n"
        severity_scores.append(("todos", ratio))
        issues_found += 1
    if console_log_count > 0:
        output += f"- ⚠️ console.* calls: {console_log_count}\n"
        severity_scores.append(("console_log", console_log_count))
        issues_found += 1
    if debugger_count > 0:
        output += f"- ❌ debugger statements: {debugger_count}\n"
        severity_scores.append(("debugger", debugger_count))
        issues_found += 1
    if any_type_count > 0:
        output += f"- ⚠️ `any` type usage: {any_type_count}\n"
        severity_scores.append(("any_type", any_type_count))
        issues_found += 1
    if ts_ignore_count > 0:
        output += f"- ⚠️ @ts-ignore/@ts-nocheck: {ts_ignore_count}\n"
        severity_scores.append(("ts_ignore", ts_ignore_count))
        issues_found += 1
    if empty_catch_count > 0:
        output += f"- ❌ Empty catch blocks: {empty_catch_count}\n"
        severity_scores.append(("empty_catch", empty_catch_count))
        issues_found += 1
    if empty_except_count > 0:
        output += f"- ⚠️ Bare except:: {empty_except_count}\n"
        severity_scores.append(("bare_except", empty_except_count))
        issues_found += 1

    # Cyclomatic complexity (평균)
    if complexity_scores:
        avg_complexity = sum(complexity_scores) / len(complexity_scores)
        w = "⚠️" if avg_complexity > 15 else "📊"
        output += f"- {w} Avg. Cyclomatic Complexity: {avg_complexity:.1f}\n"
        if avg_complexity > 30:
            severity_scores.append(("complexity", avg_complexity))
            issues_found += 1

    # 품질 등급 산정 (A-F)
    score = 100.0
    for name, val in severity_scores:
        if name == "long_lines":
            score -= val * 5
        elif name == "todos":
            score -= val * 2
        elif name == "console_log":
            score -= val * 2
        elif name == "debugger":
            score -= val * 10
        elif name == "any_type":
            score -= val * 1.5
        elif name == "ts_ignore":
            score -= val * 3
        elif name == "empty_catch":
            score -= val * 8
        elif name == "bare_except":
            score -= val * 5
        elif name == "complexity":
            score -= val * 0.5
    score = max(0, min(100, score))

    if score >= 90:
        grade = "A"
        grade_desc = "Excellent"
    elif score >= 80:
        grade = "B"
        grade_desc = "Good"
    elif score >= 70:
        grade = "C"
        grade_desc = "Fair"
    elif score >= 60:
        grade = "D"
        grade_desc = "Poor"
    elif score >= 40:
        grade = "E"
        grade_desc = "Bad"
    else:
        grade = "F"
        grade_desc = "Critical"
    if issues_found == 0:
        grade = "A+"
        grade_desc = "Perfect"

    output += f"\n## Quality Grade\n\n"
    output += f"- **Grade**: `{grade}` ({grade_desc})\n"
    output += f"- **Score**: {score:.1f}/100\n"
    output += f"- **Issues found**: {issues_found}\n\n"

    # 파일별 품질 등급 (상위/하위 5개)
    if file_grades:
        sorted_grades = sorted(file_grades.items(), key=lambda x: x[1])
        output += "## File-by-File Quality Grades\n\n"
        output += "### Top 5 Best\n\n"
        for fname, fgrade in sorted_grades[:5]:
            output += f"- `{fname}` → **{fgrade}**\n"
        output += "\n### Bottom 5 Worst\n\n"
        for fname, fgrade in sorted_grades[-5:]:
            output += f"- `{fname}` → **{fgrade}**\n"
        output += "\n"

    # ESLint
    if (root / "package.json").exists():
        try:
            result = subprocess.run([_npx_cmd(), "eslint", ".", "--ext", ".ts,.tsx,.js,.jsx", "--format", "compact", "--quiet"],
                                   cwd=str(root), capture_output=True, text=True, timeout=30)
            if result.stdout:
                output += f"## ESLint\n\n```\n{_truncate(result.stdout, 2000)}\n```\n"
            else:
                output += "## ESLint\n\n✅ No issues found.\n"
        except FileNotFoundError:
            output += "## ESLint\n\n⚠️ ESLint not installed.\n"
        except subprocess.TimeoutExpired:
            output += "## ESLint\n\n⚠️ ESLint timed out (30s).\n"
        except Exception as e:
            output += f"## ESLint\n\n❌ Error: {e}\n"

    try_crow_ingest(f"Quality check on {root.name}: grade={grade} score={score:.1f}", register="style")
    output += _markdown_footer()
    return output


def register(mcp):
    """Reviewer 도구 등록"""

    @mcp.tool
    def review_code(file_path: str, severity: str = "all") -> str:
        """지정된 파일의 코드 리뷰를 수행합니다.
        tree-sitter AST로 함수/클래스 구조와 실제 코드 품질 이슈를 탐지합니다.

        Args:
            file_path: 리뷰할 파일 경로
            severity: 심각도 필터 ("all", "error", "warning", "info"). 기본: "all"
        """
        err = _validate_file_path(file_path)
        if err:
            return _markdown_header("Code Review Error", "❌") + f"**{err}**\n" + _markdown_footer()

        p = Path(file_path)
        if not p.exists():
            p = Path(os.getcwd()) / file_path
        if not p.exists() or not p.is_file():
            return _markdown_header("Code Review Error", "❌") + f"**File not found: {file_path}**\n" + _markdown_footer()

        content = _read_file_content(p)
        if content is None:
            return _markdown_header("Code Review Error", "❌") + f"**Cannot read file: {file_path}**\n" + _markdown_footer()

        lines = content.split("\n")
        ext = p.suffix.lower()
        rel = _normalize_path(str(p))

        output = _markdown_header(f"Review: `{rel}`")
        output += f"{len(lines)} lines, {len(content)} bytes, `{ext}`\n\n"

        issues = []
        stats = {"functions": 0, "classes": 0, "interfaces": 0, "max_depth": 0}

        ast_engine = _get_ast_engine()
        ast_engine._init_legacy_tree_sitter()

        # AST 분석 (TS/JS)
        if ext in TS_JS_EXTS:
            ast = ast_engine.parse(content, ext)
            functions = ast.get("functions", [])
            classes = ast.get("classes", [])
            interfaces = ast.get("interfaces", [])
            stats["functions"] = len(functions)
            stats["classes"] = len(classes)
            stats["interfaces"] = len(interfaces)

            # AST 기반 이슈 탐지
            any_count = len(re.findall(r':\s*any\b', content))
            if any_count > 0:
                issues.append(("⚠️", f"`any` type used {any_count} time(s) — consider using specific types"))

            ts_ignore = len(re.findall(r'@ts-ignore', content))
            ts_nocheck = len(re.findall(r'@ts-nocheck', content))
            if ts_ignore > 0:
                issues.append(("⚠️", f"`@ts-ignore` found {ts_ignore} time(s)"))
            if ts_nocheck > 0:
                issues.append(("⚠️", f"`@ts-nocheck` found — entire file skips type checking"))

            eslint_disable = len(re.findall(r'eslint-disable', content))
            if eslint_disable > 0:
                issues.append(("📝", f"`eslint-disable` found {eslint_disable} time(s)"))

            console_logs = len(re.findall(r'console\.(log|warn|error|debug)', content))
            if console_logs > 0:
                issues.append(("⚠️", f"`console.*` found {console_logs} time(s) — remove before production"))

            if 'debugger' in content:
                issues.append(("⚠️", "`debugger` statement found"))

            empty_catches = len(re.findall(r'catch\s*\([^)]*\)\s*\{\s*\}', content))
            if empty_catches > 0:
                issues.append(("❌", f"Empty catch block(s): {empty_catches} — silently swallows errors"))

            todos = len(re.findall(r'(TODO|FIXME|HACK|XXX)', content))
            if todos > 0:
                issues.append(("📝", f"TODO/FIXME/HACK: {todos} marker(s)"))

            # ── Cyclomatic complexity ──
            comp = _compute_cyclomatic_complexity(content, ext)
            if comp > 15:
                issues.append(("⚠️", f"Cyclomatic complexity: {comp} — consider simplifying"))

            # ── 함수 길이 검사 (50줄 초과) ──
            if functions:
                long_funcs = []
                for fn in functions:
                    fn_start = fn.get('line', 0)
                    fn_end = fn.get('end_line', fn_start)
                    fn_lines = fn_end - fn_start
                    if fn_lines > 50:
                        long_funcs.append((fn.get('name', 'anonymous'), fn_lines, fn_start))
                for name, fn_lines, ln in long_funcs[:5]:
                    issues.append(("📏", f"Long function `{name}()`: {fn_lines} lines (line {ln}) — consider splitting"))

            # ── 파라미터 개수 검사 (5개 초과) ──
            if functions:
                for fn in functions:
                    params = fn.get('params', [])
                    if len(params) > 5:
                        issues.append(("⚠️", f"Function `{fn.get('name', 'anonymous')}()` has {len(params)} parameters (line {fn.get('line', 0)}) — consider using an options object"))

            # ── 중첩 깊이 검사 (4단계 초과) ──
            max_depth = _compute_nesting_depth(content, ext)
            stats["max_depth"] = max_depth
            if max_depth > 4:
                issues.append(("⚠️", f"Maximum nesting depth: {max_depth} levels — consider early returns or extracting logic"))

        elif ext == ".py":
            # ── Python AST 분석 ──
            ast = ast_engine.parse(content, ext)
            functions = ast.get("functions", [])
            classes = ast.get("classes", [])
            stats["functions"] = len(functions)
            stats["classes"] = len(classes)

            # Python AST 기반 이슈
            if functions:
                long_funcs = []
                for fn in functions:
                    fn_start = fn.get('line', 0)
                    fn_end = fn.get('end_line', fn_start)
                    fn_lines = fn_end - fn_start
                    if fn_lines > 50:
                        long_funcs.append((fn.get('name', 'anonymous'), fn_lines, fn_start))
                for name, fn_lines, ln in long_funcs[:5]:
                    issues.append(("📏", f"Long function `{name}()`: {fn_lines} lines (line {ln}) — consider splitting"))

                # 파라미터 개수 검사
                for fn in functions:
                    fn_name = fn.get('name', '')
                    if fn_name:
                        # AST에 params가 없으므로 regex로 추정
                        fn_text = content.split("\n")[fn.get('line', 0):fn.get('line', 0)+1][0] if fn.get('line', 0) > 0 else ""
                        param_count = fn_text.count(",") + 1 if "(" in fn_text else 0
                        if param_count > 6:  # self 포함
                            issues.append(("⚠️", f"Function `{fn_name}()` has ~{param_count} parameters (line {fn.get('line', 0)}) — consider reducing"))

            if classes:
                long_classes = []
                for cls in classes:
                    cls_start = cls.get('line', 0)
                    cls_end = cls.get('end_line', cls_start)
                    cls_lines = cls_end - cls_start
                    if cls_lines > 200:
                        long_classes.append((cls.get('name', 'anonymous'), cls_lines, cls_start))
                for name, cls_lines, ln in long_classes[:3]:
                    issues.append(("📏", f"Large class `{name}`: {cls_lines} lines (line {ln}) — consider splitting"))

            # Python 특화 검사
            console_logs = len(re.findall(r'\bprint\(', content))
            if console_logs > 0:
                issues.append(("⚠️", f"`print()` found {console_logs} time(s) — use logging instead"))
            todos = len(re.findall(r'(TODO|FIXME|HACK|XXX)', content))
            if todos > 0:
                issues.append(("📝", f"TODO/FIXME/HACK: {todos} marker(s)"))
            empty_excepts = len(re.findall(r'except\s*:', content))
            if empty_excepts > 0:
                issues.append(("⚠️", f"Bare `except:` found {empty_excepts} time(s) — specify exception type"))

            # Import 구조 분석
            py_imports = re.findall(r'^(?:from\s+(\S+)\s+)?import\s+(\S+)', content, re.MULTILINE)
            if len(py_imports) > 20:
                issues.append(("📝", f"Large number of imports ({len(py_imports)}) — consider lazy imports"))

            # ── Cyclomatic complexity (Python) ──
            comp = _compute_cyclomatic_complexity(content, ext)
            if comp > 15:
                issues.append(("⚠️", f"Cyclomatic complexity: {comp} — consider simplifying"))

            # ── 중첩 깊이 검사 (Python) ──
            max_depth = _compute_nesting_depth(content, ext)
            stats["max_depth"] = max_depth
            if max_depth > 4:
                issues.append(("⚠️", f"Maximum nesting depth: {max_depth} levels — consider early returns or extracting logic"))

        elif ext == ".go":
            # ── Go AST 분석 ──
            ast = ast_engine.parse(content, ext)
            functions = ast.get("functions", [])
            classes = ast.get("classes", [])  # Go structs
            stats["functions"] = len(functions)
            stats["classes"] = len(classes)

            # Go AST 기반 이슈
            if functions:
                long_funcs = []
                for fn in functions:
                    fn_start = fn.get('line', 0)
                    fn_end = fn.get('end_line', fn_start)
                    fn_lines = fn_end - fn_start
                    if fn_lines > 50:
                        long_funcs.append((fn.get('name', 'anonymous'), fn_lines, fn_start))
                for name, fn_lines, ln in long_funcs[:5]:
                    issues.append(("📏", f"Long function `{name}()`: {fn_lines} lines (line {ln}) — consider splitting"))

            if classes:
                for cls in classes:
                    cls_start = cls.get('line', 0)
                    cls_end = cls.get('end_line', cls_start)
                    cls_lines = cls_end - cls_start
                    if cls_lines > 100:
                        issues.append(("📏", f"Large struct `{cls.get('name', 'anonymous')}`: {cls_lines} lines (line {cls_start}) — consider splitting"))

            # Go 특화 검사
            todos = len(re.findall(r'(TODO|FIXME|HACK|XXX)', content))
            if todos > 0:
                issues.append(("📝", f"TODO/FIXME/HACK: {todos} marker(s)"))

            go_fmt_errors = 0
            for line in lines:
                if len(line) > 120:
                    go_fmt_errors += 1
            if go_fmt_errors > 0:
                issues.append(("📏", f"{go_fmt_errors} line(s) exceed 120 chars — run `gofmt`"))

            # Error handling 검사
            err_ignores = len(re.findall(r'if\s+err\s*!=\s*nil\s*\{\s*\n?\s*_\s*=\s*err', content))
            if err_ignores > 0:
                issues.append(("⚠️", f"`err` assigned to `_` {err_ignores} time(s) — handle errors properly"))

            # ── Cyclomatic complexity (Go) ──
            comp = _compute_cyclomatic_complexity(content, ext)
            if comp > 15:
                issues.append(("⚠️", f"Cyclomatic complexity: {comp} — consider simplifying"))

            # ── 중첩 깊이 검사 (Go) ──
            max_depth = _compute_nesting_depth(content, ext)
            stats["max_depth"] = max_depth
            if max_depth > 4:
                issues.append(("⚠️", f"Maximum nesting depth: {max_depth} levels — consider early returns or extracting logic"))

        else:
            # ── 기타 언어 (regex 폴백) ──
            if ext == ".rs":
                # Rust 특화 검사
                unsafe_blocks = len(re.findall(r'\bunsafe\s*\{', content))
                if unsafe_blocks > 0:
                    issues.append(("⚠️", f"`unsafe` block(s) found: {unsafe_blocks} — review for safety"))
                unwrap_calls = len(re.findall(r'\.unwrap\(\)', content))
                if unwrap_calls > 0:
                    issues.append(("⚠️", f"`.unwrap()` found {unwrap_calls} time(s) — use proper error handling"))
                todos = len(re.findall(r'(TODO|FIXME|HACK)', content))
                if todos > 0:
                    issues.append(("📝", f"TODO/FIXME/HACK: {todos} marker(s)"))
            else:
                todos = len(re.findall(r'(TODO|FIXME|HACK)', content))
                if todos > 0:
                    issues.append(("📝", f"TODO/FIXME/HACK: {todos} marker(s)"))

            # ── 중첩 깊이 검사 (기타 언어) ──
            max_depth = _compute_nesting_depth(content, ext)
            stats["max_depth"] = max_depth
            if max_depth > 4:
                issues.append(("⚠️", f"Maximum nesting depth: {max_depth} levels — consider early returns or extracting logic"))

        # 기본 검사 (모든 언어)
        long_lines = sum(1 for l in lines if len(l) > 120)
        if long_lines > 0:
            issues.append(("📏", f"{long_lines} line(s) exceed 120 chars"))

        # 심각도 필터
        severity_map = {"❌": "error", "⚠️": "warning", "📝": "info", "📏": "info"}
        if severity != "all":
            filtered_issues = []
            for level, msg in issues:
                sev = severity_map.get(level, "info")
                if sev == severity or (severity == "warning" and sev in ("error", "warning")):
                    filtered_issues.append((level, msg))
            issues = filtered_issues

        # 출력
        output += "## Structure\n"
        if stats["functions"] > 0:
            output += f"- Functions/Methods: {stats['functions']}\n"
        if stats["classes"] > 0:
            output += f"- Classes: {stats['classes']}\n"
        if stats["interfaces"] > 0:
            output += f"- Interfaces/Types: {stats['interfaces']}\n"
        if stats["max_depth"] > 0:
            output += f"- Max nesting depth: {stats['max_depth']}\n"

        output += "\n## Issues\n"
        if issues:
            for level, msg in issues:
                output += f"- {level} {msg}\n"
            output += f"\n**{len(issues)} issue(s) found.**\n"
        else:
            output += "✅ No issues found.\n"

        try_crow_ingest(f"Reviewed {p.name}: {len(issues)} issues, {stats['functions']} functions", register="style")
        output += _markdown_footer()
        return output

    @mcp.tool
    def check_quality(target_path: Optional[str] = None) -> str:
        """💀 (Deprecated) 프로젝트의 코드 품질을 검사합니다.

        💀 `review_project(mode="quality")` 사용 권장.
        이 도구는 내부적으로 `review_project(mode="quality")`으로 위임됩니다.

        Args:
            target_path: 검사 대상 경로
        """
        # _review_project_core로 완전 위임 (시그니처 100% 호환)
        return _review_project_core(target_path or ".", mode="quality")
