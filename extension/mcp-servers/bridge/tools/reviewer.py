# VibeZoo Bridge — Reviewer 도구 그룹
# review_code (→ _review_project_core 위임)
# check_quality 함수는 내부용으로 유지 (더 이상 MCP 도구 아님)

import json
import os
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
import sys
# Pylance: ensure the extension root is in package search path
_EXT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _EXT_ROOT not in sys.path:
    sys.path.insert(0, _EXT_ROOT)
from typing import Optional

from bridge.config import (
    VERSION, DEFAULT_EXCLUDE_DIRS, SOURCE_EXTS, TS_JS_EXTS,
    CPP_EXTS, GENERIC_EXTS, REVIEWABLE_EXTS, CONFIG_FILES,
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
from bridge.ast_singleton import get_ast_engine as _get_ast_engine
from bridge.i18n import t


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
    elif ext in CPP_EXTS:
        branches = (
            len(re.findall(r'\bif\s*\(', content))
            + len(re.findall(r'\bfor\s*\(', content))
            + len(re.findall(r'\bwhile\s*\(', content))
            + len(re.findall(r'\bswitch\s*\(', content))
            + len(re.findall(r'\bcatch\s*\(', content))
            + len(re.findall(r'\bcase\s+', content))
        )
    elif ext == '.rs':
        branches = (
            len(re.findall(r'\bif\s+', content))
            + len(re.findall(r'\bfor\s+', content))
            + len(re.findall(r'\bwhile\s+', content))
            + len(re.findall(r'\bmatch\s+', content))
            + len(re.findall(r'\bloop\s*\{', content))
        )
    else:
        if ext == '.go':
            branches = (
                len(re.findall(r'\bif\s+', content))
                + len(re.findall(r'\bfor\s+', content))
                + len(re.findall(r'\bswitch\s+', content))
                + len(re.findall(r'\bcase\s+', content))
                + len(re.findall(r'\bselect\s*\{', content))
            )
        else:
            branches = (
                len(re.findall(r'\bif\s+', content))
                + len(re.findall(r'\bfor\s+', content))
                + len(re.findall(r'\bwhile\s+', content))
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


def _review_project_core(target_path: Optional[str] = None, mode: str = "quality") -> str:
    """review_project의 내부 구현 — mode="quality"로 품질 검사만 수행

    Args:
        target_path: 분석 대상 경로 (생략 시 현재 작업 디렉토리 사용)
        mode: "quality" (품질 검사) | "full" (전체 리뷰)

    Returns:
        마크다운 보고서
    """
    if target_path is None:
        target_path = os.getcwd()
    root = Path(get_project_root(target_path))
    output = _markdown_header(t("Code Quality Check"))

    source_files = list(_iter_project_files_cached(root, extensions=SOURCE_EXTS, exclude_dirs=DEFAULT_EXCLUDE_DIRS, include_names=CONFIG_FILES))
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
        # TS 전용 지표: ext in TS_JS_EXTS 일 때만 카운트 (M2 fix)
        if ext in TS_JS_EXTS:
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

    output += f"## {t('Quality Metrics')}\n\n"
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

    output += f"\n## {t('Quality Grade')}\n\n"
    output += f"- **{t('Grade')}**: `{grade}` ({grade_desc})\n"
    output += f"- **{t('Score')}**: {score:.1f}/100\n"
    output += f"- **{t('Issues found')}**: {issues_found}\n\n"

    # 파일별 품질 등급 (상위/하위 5개)
    if file_grades:
        sorted_grades = sorted(file_grades.items(), key=lambda x: x[1])
        output += f"## {t('File-by-File Quality Grades')}\n\n"
        output += f"### {t('Top 5 Best')}\n\n"
        for fname, fgrade in sorted_grades[:5]:
            output += f"- `{fname}` → **{fgrade}**\n"
        output += f"\n### {t('Bottom 5 Worst')}\n\n"
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
                output += f"## ESLint\n\n✅ {t('No issues found.')}\n"
        except FileNotFoundError:
            output += f"## ESLint\n\n⚠️ {t('ESLint not installed.')}\n"
        except subprocess.TimeoutExpired:
            output += f"## ESLint\n\n⚠️ {t('ESLint timed out (30s).')}\n"
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
            return _markdown_header(t("Code Review Error"), "❌") + f"**{err}**\n" + _markdown_footer()

        p = Path(file_path)
        if not p.exists():
            p = Path(os.getcwd()) / file_path
        if not p.exists() or not p.is_file():
            return _markdown_header(t("Code Review Error"), "❌") + f"**{t('File not found: {0}', file_path)}**\n" + _markdown_footer()

        content = _read_file_content(p)
        if content is None:
            return _markdown_header(t("Code Review Error"), "❌") + f"**{t('Cannot read file: {0}', file_path)}**\n" + _markdown_footer()

        lines = content.split("\n")
        ext = p.suffix.lower()
        rel = _normalize_path(str(p))

        output = _markdown_header(f"Review: `{rel}`")
        output += f"{len(lines)} lines, {len(content)} bytes, `{ext}`\n\n"

        issues = []
        stats = {"functions": 0, "classes": 0, "interfaces": 0, "max_depth": 0}

        ast_engine = _get_ast_engine()
        ast_engine._init_legacy_tree_sitter()

        # M5: 지원하지 않는 파일 형식은 얼리 리턴
        if ext not in REVIEWABLE_EXTS and p.name not in CONFIG_FILES:
            return _markdown_header(f"Review: `{rel}`", "⚠️") \
                   + f"{t('File type `{0}` is not reviewable. Supported: {1}', ext, sorted(REVIEWABLE_EXTS))}\n" \
                   + _markdown_footer()

        # ════════════════════════════════════════════════════════════
        # if/elif 체인 순서 (M7):
        #   TS_JS → .py → .rs → CPP → Go → GENERIC (Shell/Docker/YAML/JSON)
        # ════════════════════════════════════════════════════════════

        # ── TS/JS AST 분석 (변경 없음) ──
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

        # ── Python AST 분석 (변경 없음) ──
        elif ext == ".py":
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

        # ── Rust AST 완전 분석 (M8: 기존 else 블록 Rust 코드 제거) ──
        elif ext == ".rs":
            ast = ast_engine.parse(content, ext)
            functions = ast.get("functions", [])
            classes = ast.get("classes", [])  # struct + enum
            enums = ast.get("enums", [])
            stats["functions"] = len(functions)
            stats["classes"] = len(classes)

            # ── 함수 길이 검사 ──
            if functions:
                long_funcs = []
                for fn in functions:
                    fn_start = fn.get('line', 0)
                    fn_end = fn.get('end_line', fn_start)
                    fn_lines = fn_end - fn_start
                    if fn_lines > 50:
                        long_funcs.append((fn.get('name', 'anonymous'), fn_lines, fn_start))
                for name, fn_lines, ln in long_funcs[:5]:
                    issues.append(("📏",
                        f"Long function `{name}()`: {fn_lines} lines (line {ln})"))

            if classes:
                for cls in classes:
                    cls_start = cls.get('line', 0)
                    cls_end = cls.get('end_line', cls_start)
                    cls_lines = cls_end - cls_start
                    if cls_lines > 200:
                        issues.append(("📏",
                            f"Large struct/enum `{cls.get('name', 'anonymous')}`: "
                            f"{cls_lines} lines (line {cls_start})"))

            # ── Cyclomatic complexity ──
            comp = _compute_cyclomatic_complexity(content, ext)
            if comp > 15:
                issues.append(("⚠️", f"Cyclomatic complexity: {comp}"))

            # ── 중첩 깊이 ──
            max_depth = _compute_nesting_depth(content, ext)
            stats["max_depth"] = max_depth
            if max_depth > 4:
                issues.append(("⚠️",
                    f"Maximum nesting depth: {max_depth} — use match or early returns"))

            # ═══ Rust 특화 규칙 ═══

            # R1. unsafe 블록 복잡도 제어
            unsafe_blocks = re.findall(r'\bunsafe\s*\{', content)
            if unsafe_blocks:
                unsafe_lines = []
                for m in re.finditer(r'\bunsafe\s*\{', content):
                    start = m.start()
                    depth = 1
                    pos = m.end()
                    while depth > 0 and pos < len(content):
                        if content[pos] == '{':
                            depth += 1
                        elif content[pos] == '}':
                            depth -= 1
                        pos += 1
                    block = content[m.start():pos]
                    block_lines = block.count('\n')
                    if block_lines > 15:
                        unsafe_lines.append((m.start(), block_lines))
                if unsafe_lines:
                    issues.append(("⚠️",
                        f"`unsafe` block(s) exceed 15 lines: "
                        f"{len(unsafe_lines)} occurrence(s) — extract safe wrappers"))
                elif len(unsafe_blocks) > 0:
                    issues.append(("⚠️",
                        f"`unsafe` block(s) found: {len(unsafe_blocks)} — review for safety"))

            # R2. 묵살된 Result/Option (`let _ = ...`)
            let_underscore = len(re.findall(r'\blet\s+_\s*=', content))
            if let_underscore > 0:
                issues.append(("⚠️",
                    f"`let _ = ...` pattern found {let_underscore} time(s) — "
                    f"Result/Option silently ignored, use `?` or proper match"))

            # R3. Panic 유발 지점
            unwrap_count = len(re.findall(r'\.unwrap\(\)', content))
            expect_count = len(re.findall(r'\.expect\(', content))
            panic_count = len(re.findall(r'panic!\(', content))
            if unwrap_count > 0:
                issues.append(("⚠️",
                    f"`.unwrap()` found {unwrap_count} time(s) — "
                    f"use `.expect()` with message or proper error handling"))
            if panic_count > 0:
                issues.append(("❌",
                    f"`panic!` macro found {panic_count} time(s) — "
                    f"consider graceful error propagation"))

            # R4. clone 남용 감지
            clone_count = len(re.findall(r'\.clone\(\)', content))
            if clone_count > 5:
                issues.append(("⚠️",
                    f"`.clone()` called {clone_count} times — "
                    f"consider borrowing or refactoring ownership"))

            # R5. `as` 타입 캐스트 (H4: 숫자 타입 캐스트만 감지, use ... as 제외)
            as_cast_count = len(re.findall(
                r'\b(\w+)\s+as\s+(?!_)(u8|u16|u32|u64|i8|i16|i32|i64|f32|f64|usize|isize)\b',
                content))
            if as_cast_count > 5:
                issues.append(("📝",
                    f"`as` numeric cast used {as_cast_count} times — "
                    f"consider `From`/`Into`/`TryFrom` for safe conversions"))

            # R6. `println!` 디버그 로그
            println_count = len(re.findall(r'println!\(', content))
            if println_count > 0:
                issues.append(("📝",
                    f"`println!()` found {println_count} time(s) — use `log` crate"))

            todos = len(re.findall(r'(TODO|FIXME|HACK)', content))
            if todos > 0:
                issues.append(("📝", f"TODO/FIXME/HACK: {todos} marker(s)"))

        # ── C/C++ AST 분석 (신규) ──
        elif ext in CPP_EXTS:
            ast = ast_engine.parse(content, ext)
            functions = ast.get("functions", [])
            classes = ast.get("classes", [])
            stats["functions"] = len(functions)
            stats["classes"] = len(classes)

            # 주석 제거한 코드 (H2: new/delete 오탐 방지)
            code_only = re.sub(r'//[^\n]*|/\*[\s\S]*?\*/', '', content)

            # ── 함수 길이 검사 ──
            if functions:
                long_funcs = []
                for fn in functions:
                    fn_start = fn.get('line', 0)
                    fn_end = fn.get('end_line', fn_start)
                    fn_lines = fn_end - fn_start
                    if fn_lines > 50:
                        long_funcs.append((fn.get('name', 'anonymous'), fn_lines, fn_start))
                for name, fn_lines, ln in long_funcs[:5]:
                    issues.append(("📏",
                        f"Long function `{name}()`: {fn_lines} lines (line {ln}) — consider splitting"))

            # ── Cyclomatic complexity ──
            comp = _compute_cyclomatic_complexity(content, ext)
            if comp > 15:
                issues.append(("⚠️", f"Cyclomatic complexity: {comp} — consider simplifying"))

            # ── 중첩 깊이 ──
            max_depth = _compute_nesting_depth(content, ext)
            stats["max_depth"] = max_depth
            if max_depth > 4:
                issues.append(("⚠️",
                    f"Maximum nesting depth: {max_depth} levels — consider early returns"))

            # ═══ C++ 특화 규칙 ═══

            # R1. Raw pointer vs smart pointer (H1: 정규식 개선)
            raw_ptr_count = len(re.findall(
                r'(?<!\w)(?:\w+\s*\*+\s+\w+|(?:int|char|float|double|void|bool|long|short|unsigned|signed)\s*\*+\s*\w+)',
                code_only))
            smart_ptr_count = len(re.findall(
                r'(std::unique_ptr|std::shared_ptr|std::weak_ptr)', code_only))
            if raw_ptr_count > 0 and smart_ptr_count == 0:
                issues.append(("⚠️",
                    f"Raw pointer(s) found ({raw_ptr_count}) — "
                    f"consider std::unique_ptr or std::shared_ptr (C++11+)"))

            # R2. new/delete 불일치 (H2: 주석 제거, placement new 제외, 임계값 도입)
            new_count = len(re.findall(
                r'\bnew\s+(?!\(\))(?!\s*std::make_unique)(?!\s*std::make_shared)', code_only))
            delete_count = len(re.findall(r'\bdelete\s+(?!\[\])', code_only))
            delete_array_count = len(re.findall(r'\bdelete\[\]\s+', code_only))
            if (new_count - (delete_count + delete_array_count)) > 3:
                issues.append(("❌",
                    f"Potential memory leak: {new_count} `new` vs "
                    f"{delete_count + delete_array_count} `delete`/`delete[]` (diff > 3)"))

            # R3. 경계검사 우회 (H3: 초기화/할당 컨텍스트만 매칭)
            bracket_access = len(re.findall(r'\w+\s*\[[^\]]*\]\s*[=;]', code_only))
            at_access = len(re.findall(r'\.at\(', code_only))
            if bracket_access > 10 and at_access == 0:
                issues.append(("⚠️",
                    f"Index operator `[]` used {bracket_access} times without `.at()` — "
                    f"no bounds checking"))

            # R4. RAII 락 누락: std::mutex without std::lock_guard/unique_lock
            mutex_count = len(re.findall(r'std::mutex\s+\w+', code_only))
            lock_guard_count = len(re.findall(
                r'(std::lock_guard|std::unique_lock|std::scoped_lock)', code_only))
            if mutex_count > 0 and lock_guard_count == 0:
                issues.append(("⚠️",
                    f"`std::mutex` used without RAII lock guard — "
                    f"consider std::lock_guard or std::scoped_lock (C++17)"))

            # R5. C 스타일 캐스트 (C++ 프로젝트에서, .c 제외)
            if ext in (".cpp", ".hpp", ".cc", ".h"):
                c_cast = len(re.findall(r'\(int\)|\(char\*\)|\(void\*\)|\(double\)|\(float\)',
                                        code_only))
                if c_cast > 0:
                    issues.append(("📝",
                        f"C-style cast found {c_cast} time(s) — "
                        f"use static_cast, dynamic_cast, const_cast, reinterpret_cast"))

            # R6. printf/scanf 대신 iostream 사용 권장 (.c 제외)
            if ext != ".c":
                printfs = len(re.findall(r'\b(printf|scanf|fprintf|sprintf)\s*\(', code_only))
                if printfs > 0:
                    issues.append(("📝",
                        f"`printf`/`scanf` family used {printfs} time(s) — "
                        f"consider std::cout / std::format (C++20)"))

            # TODO/디버그
            todos = len(re.findall(r'(TODO|FIXME|HACK|XXX)', code_only))
            if todos > 0:
                issues.append(("📝", f"TODO/FIXME/HACK: {todos} marker(s)"))

        # ── Go AST 분석 + 고도화 규칙 ──
        elif ext == ".go":
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

            # ═══ Go 고도화 규칙 (신규) ═══

            # G1. 고루틴 내 루프 변수 캡처 (H5: re.DOTALL + non-greedy)
            go_stmt_pattern = re.findall(
                r'for\s+\w+\s*:?=\s*range\s+.+?go\s+func\s*\(', content, re.DOTALL)
            if go_stmt_pattern:
                issues.append(("❌",
                    f"Goroutine inside range loop detected ({len(go_stmt_pattern)} time(s)) — "
                    f"loop variable may be captured by reference. "
                    f"Pass as parameter or use Go 1.22+"))

            # G2. defer 내 recover() 부재
            defer_funcs = re.findall(r'defer\s+func\s*\(\s*\)\s*\{', content)
            recover_calls = len(re.findall(r'\brecover\(\)', content))
            if defer_funcs and recover_calls == 0:
                issues.append(("⚠️",
                    f"`defer func()` found but no `recover()` — "
                    f"potential unhandled panic in deferred cleanup"))

            # G3. 채널 데드락 위험 (H6: flat_content 사용)
            flat_content = content.replace('\n', ' ')
            unbuffered_chan = re.findall(r'make\s*\(\s*chan\s+(?!.*,\s*\d+)', flat_content)
            if unbuffered_chan:
                issues.append(("⚠️",
                    f"Unbuffered channel(s) found ({len(unbuffered_chan)}) — "
                    f"ensure send/receive happen in different goroutines"))

            # G4. Mutex Unlock 누락 (defer mu.Unlock() 없는 경우)
            mutex_locks = len(re.findall(r'\.Lock\(\)', content))
            defer_unlocks = len(re.findall(r'defer\s+\w+\.Unlock\(\)', content))
            if mutex_locks > 0 and defer_unlocks < mutex_locks:
                issues.append(("❌",
                    f"Mutex `.Lock()` without matching `defer ... .Unlock()` — "
                    f"potential deadlock on panic/early return"))

            # G5. nil map assignment (var m map[K]V; m[key] = value)
            nil_map_assign = re.findall(
                r'(?:var\s+\w+\s+map\[)|(?:\w+\s*:=\s*(?:map\[|nil))', content)
            if nil_map_assign:
                issues.append(("⚠️",
                    f"Potential nil map assignment — use `make(map[...]...)` or "
                    f"composite literal"))

        # ── 일반 소스 파일 (Shell / Dockerfile / YAML / JSON) ──
        elif ext in GENERIC_EXTS:
            # ── Shell Script ──
            if ext in (".sh", ".bash"):
                # S1. 따옴표 누락 감지 (H7: 확장된 패턴)
                unquoted_vars = len(re.findall(
                    r'\$\{?\w+\}?|\$[@*#?!0-9]|\$\{[\w#%:-]+\}', content))
                quotes_ok = len(re.findall(r'"\$\{?\w+\}?"', content))
                if unquoted_vars > quotes_ok:
                    issues.append(("⚠️",
                        f"Unquoted variable expansion(s) — "
                        f"may cause word splitting on whitespace"))

                # S2. set -e / set -o pipefail 부재
                has_set_e = bool(re.search(r'set\s+-e', content))
                has_pipefail = bool(re.search(r'set\s+-o\s+pipefail', content))
                if not has_set_e:
                    issues.append(("⚠️",
                        "`set -e` not found — script continues on error"))
                if not has_pipefail:
                    issues.append(("📝",
                        "`set -o pipefail` not found — pipeline errors may be masked"))

                # S3. shellcheck 연동 시도 (optional, subprocess)
                try:
                    result = subprocess.run(
                        ["shellcheck", "-f", "json", str(p)],
                        capture_output=True, text=True, timeout=10
                    )
                    if result.returncode != 0 and result.stdout:
                        sc_data = json.loads(result.stdout)
                        for item in sc_data[:10]:
                            issues.append(("⚠️",
                                f"ShellCheck[{item.get('code','')}]: "
                                f"{item.get('message','')} "
                                f"(line {item.get('line','?')})"))
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    pass
                except Exception:
                    pass

            elif ext == ".ps1":
                has_strict_mode = bool(re.search(r'Set-StrictMode', content))
                if not has_strict_mode:
                    issues.append(("📝",
                        "`Set-StrictMode` not found — consider enabling for safer scripts"))

            # ── YAML ──
            if ext in (".yaml", ".yml"):
                # Y1. 중복 키 탐지 (H8: 들여쓰기 기반 복합 키)
                key_paths = {}
                for i, line in enumerate(lines, 1):
                    m = re.match(r'^(\s*)(\w[\w.-]*)\s*:', line)
                    if m:
                        key = m.group(2)
                        indent = len(m.group(1))
                        composite_key = f"{indent}:{key}"
                        if composite_key in key_paths:
                            issues.append(("❌",
                                f"Duplicate key `{key}` at indent level {indent}, line {i} "
                                f"(first at line {key_paths[composite_key]})"))
                        key_paths[composite_key] = i

                # Y2. 하드코딩된 시크릿
                secret_patterns = [
                    (r'(password|passwd|pwd)\s*:\s*\S+', 'password'),
                    (r'(secret|SECRET)\s*:\s*\S+', 'secret'),
                    (r'(api_key|apikey|api-key)\s*:\s*\S+', 'API key'),
                    (r'(token|TOKEN)\s*:\s*\S+', 'token'),
                ]
                for pattern, label in secret_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        issues.append(("❌",
                            f"Hardcoded {label}(s) found ({len(matches)}) — "
                            f"use environment variables or secrets manager"))

            # ── JSON ──
            elif ext == ".json":
                try:
                    parsed = json.loads(content)
                except json.JSONDecodeError as e:
                    issues.append(("❌",
                        f"Invalid JSON: {e.msg} (line {e.lineno}, col {e.colno})"))

                secret_matches = re.findall(
                    r'"(password|secret|api_key|token)"\s*:\s*"[^"]+"',
                    content, re.IGNORECASE)
                if secret_matches:
                    issues.append(("❌",
                        f"Hardcoded sensitive value(s) found ({len(secret_matches)})"))

            # ── 공통: 중첩 깊이, TODO ──
            max_depth = _compute_nesting_depth(content, ext)
            stats["max_depth"] = max_depth
            if max_depth > 4:
                issues.append(("⚠️", f"Maximum nesting depth: {max_depth} levels"))

            todos = len(re.findall(r'(TODO|FIXME|HACK|XXX)', content))
            if todos > 0:
                issues.append(("📝", f"TODO/FIXME/HACK: {todos} marker(s)"))

        # ── Dockerfile (확장자 없는 파일명 기반) ──
        elif p.name == "Dockerfile" or p.suffix.lower() == ".dockerfile":
            # D1. latest 태그 사용
            latest_tags = re.findall(r'FROM\s+\S+:latest', content)
            if latest_tags:
                issues.append(("⚠️",
                    f"`FROM ... :latest` tag(s) found ({len(latest_tags)}) — "
                    f"pin to specific version for reproducible builds"))

            # D2. apt-get 캐시 미삭제
            apt_installs = len(re.findall(r'apt-get\s+install', content))
            apt_cleans = len(re.findall(
                r'(rm -rf /var/lib/apt/lists|apt-get clean|apt-get autoclean)',
                content))
            if apt_installs > 0 and apt_cleans == 0:
                issues.append(("⚠️",
                    f"`apt-get install` without cache cleanup — "
                    f"add `rm -rf /var/lib/apt/lists/*` to reduce image size"))

            # D3. root 유저 사용
            if "USER" not in content:
                issues.append(("📝",
                    "No `USER` directive — container runs as root"))

            # D4. COPY 대신 ADD
            add_count = len(re.findall(r'\bADD\s+', content))
            copy_count = len(re.findall(r'\bCOPY\s+', content))
            if add_count > copy_count:
                issues.append(("📝",
                    f"`ADD` used {add_count} times — prefer `COPY` unless "
                    f"auto-extraction is needed"))

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
        output += f"## {t('Structure')}\n"
        if stats["functions"] > 0:
            output += f"- Functions/Methods: {stats['functions']}\n"
        if stats["classes"] > 0:
            output += f"- Classes: {stats['classes']}\n"
        if stats["interfaces"] > 0:
            output += f"- Interfaces/Types: {stats['interfaces']}\n"
        if stats["max_depth"] > 0:
            output += f"- Max nesting depth: {stats['max_depth']}\n"

        output += f"\n## {t('Issues')}\n"
        if issues:
            for level, msg in issues:
                output += f"- {level} {msg}\n"
            output += f"\n**{t('{0} issue(s) found.', len(issues))}**\n"
        else:
            output += f"✅ {t('No issues found.')}\n"

        try_crow_ingest(f"Reviewed {p.name}: {len(issues)} issues, {stats['functions']} functions", register="style")
        output += _markdown_footer()
        return output

