# VibeZoo Bridge — Analysis 도구 그룹
# explain_code + analyze_changes + review_pr + refactor_across_files

import json
import os
import re
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Optional

from bridge.config import (
    VERSION, DEFAULT_EXCLUDE_DIRS, SOURCE_EXTS, TS_JS_EXTS,
)
from bridge.utils import (
    _markdown_header, _markdown_footer,
    _validate_string, _validate_int, _validate_file_path,
    _read_file_content, _truncate, _normalize_path,
    _iter_project_files, _iter_project_files_cached,
    _npx_cmd, get_project_root,
    _extract_regex_imports,
)
from bridge.crow_client import try_crow_ingest, try_crow_recall
from bridge.ast_engine import AstEngine
from bridge.tool_context import (
    make_explain_code_context,
    format_manifest_markdown,
)

_ast_engine = None


def _get_ast_engine() -> AstEngine:
    global _ast_engine
    if _ast_engine is None:
        _ast_engine = AstEngine()
    return _ast_engine


def _get_git_blame(target: Path, line_number: int) -> dict:
    """git blame 정보 조회 (author, date, commit_message, commit_hash)"""
    try:
        result = subprocess.run(
            ["git", "blame", "-L", f"{line_number},{line_number}", "--porcelain", str(target)],
            cwd=str(target.parent),
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            return {}
        
        blame_info = {}
        for line in result.stdout.split("\n"):
            if line.startswith("author "):
                blame_info["author"] = line[7:].strip()
            elif line.startswith("author-time "):
                ts = int(line[12:].strip())
                blame_info["date"] = time.strftime("%Y-%m-%d", time.localtime(ts))
            elif line.startswith("summary "):
                blame_info["commit_message"] = line[8:].strip()
            elif " " not in line and line.strip():
                blame_info["commit_hash"] = line.split(" ")[0] if " " in line else line[:10]
        
        if not blame_info.get("commit_hash"):
            # fallback: extract hash from first line
            first_line = result.stdout.split("\n")[0] if result.stdout else ""
            if first_line:
                blame_info["commit_hash"] = first_line.split(" ")[0][:10]
        
        return blame_info
    except Exception:
        return {}


def _find_related_tests(target: Path) -> list[dict]:
    """관련 테스트 파일 검색"""
    root = Path(os.getcwd())
    stem = target.stem
    related = []
    test_patterns = [
        f"**/test_{stem}.*", f"**/{stem}.test.*", f"**/{stem}.spec.*",
        f"**/test_*{stem}*", f"**/test*{stem}*",
    ]
    for pattern in test_patterns:
        for p in root.glob(pattern):
            if p.is_file() and p != target:
                related.append({
                    "file": str(p.relative_to(root)),
                    "name": p.name,
                })
    return related


def register(mcp):
    """Analysis 도구 등록"""

    @mcp.tool
    def explain_code(file_path: str, line_number: int) -> str:
        """지정된 파일의 특정 라인에 있는 코드가 무엇을 하는지 tree-sitter AST로 분석하여 설명합니다.
        AST 노드 트리를 통해 해당 라인의 함수/클래스/인터페이스 컨텍스트를 파악하고 간단한 설명을 생성합니다.

        Args:
            file_path: 분석할 파일의 상대 경로
            line_number: 설명을 원하는 1-based 라인 번호
        """
        err = _validate_string(file_path, "file_path")
        if err:
            return _markdown_header("Code Explanation Error", "❌") + f"**{err}**\n" + _markdown_footer()

        root = Path(os.getcwd())
        target = root / file_path
        if not target.exists():
            return (_markdown_header("Code Explanation Error", "❌")
                    + f"**File not found: `{file_path}`**\n"
                    + _markdown_footer())

        content = _read_file_content(target)
        if content is None:
            return (_markdown_header("Code Explanation Error", "❌")
                    + f"**Cannot read file: `{file_path}`**\n"
                    + _markdown_footer())

        lines = content.split("\n")
        if line_number < 1 or line_number > len(lines):
            return (_markdown_header("Code Explanation Error", "❌")
                    + f"**Line {line_number} is out of range (file has {len(lines)} lines)**\n"
                    + _markdown_footer())

        line_content = lines[line_number - 1].strip()
        if not line_content:
            return (_markdown_header("Code Explanation", "ℹ️")
                    + f"Line {line_number} is empty.\n"
                    + _markdown_footer())

        ast_engine = _get_ast_engine()
        ast_engine._init_legacy_tree_sitter()

        ext = target.suffix.lower()

        # ── TOOL_CONTEXT 마커 출력 ──
        output = "<!-- TOOL_CONTEXT: 설명에 필요한 데이터 수집 완료. LLM은 이 데이터로 종합 설명 생성 -->\n\n"

        output += _markdown_header(f'Code Explanation: `{_normalize_path(file_path)}:{line_number}`')
        output += f"> `{line_content}`\n\n"

        # ── git blame 정보 수집 ──
        blame_info = _get_git_blame(target, line_number)
        related_tests = _find_related_tests(target)

        if blame_info:
            output += "## Git Blame\n\n"
            output += f"- **Author**: {blame_info.get('author', 'N/A')}\n"
            output += f"- **Date**: {blame_info.get('date', 'N/A')}\n"
            output += f"- **Commit**: `{blame_info.get('commit_hash', 'N/A')[:10]}`\n"
            output += f"- **Message**: {blame_info.get('commit_message', 'N/A')}\n\n"

        if related_tests:
            output += "## Related Tests\n\n"
            for t in related_tests:
                output += f"- `{t['file']}`\n"
            output += "\n"

        if ext in TS_JS_EXTS and ast_engine.is_available():
            ast = ast_engine.parse(content, ext)

            enclosing_func = None
            enclosing_class = None
            enclosing_iface = None

            for fn in ast.get("functions", []):
                if fn["line"] <= line_number <= fn.get("end_line", fn["line"]):
                    enclosing_func = fn

            for cls in ast.get("classes", []):
                if cls["line"] <= line_number <= cls.get("end_line", cls["line"]):
                    enclosing_class = cls

            for iface in ast.get("interfaces", []):
                if iface["line"] <= line_number <= iface.get("end_line", iface["line"]):
                    enclosing_iface = iface

            output += "## Context\n\n"
            if enclosing_func:
                output += f"- **Function**: `{enclosing_func['name']}` ({enclosing_func['type']}, lines {enclosing_func['line']}-{enclosing_func['end_line']})\n"
            if enclosing_class:
                output += f"- **Class**: `{enclosing_class['name']}` (line {enclosing_class['line']})\n"
            if enclosing_iface:
                output += f"- **Interface/Type**: `{enclosing_iface['name']}` ({enclosing_iface['type']}, line {enclosing_iface['line']})\n"
            if not enclosing_func and not enclosing_class and not enclosing_iface:
                output += "- Top-level code (no enclosing function or class)\n"

            output += "\n## Line Analysis\n\n"
            line_lower = line_content.lower()

            if line_content.startswith("import ") or line_content.startswith("from ") or line_content.startswith("require("):
                output += "- **Import statement**: imports external module or dependency.\n"
            elif line_content.startswith("export ") or line_content.startswith("module.exports"):
                output += "- **Export statement**: exposes symbols to other modules.\n"
            elif line_content.startswith("function ") or line_content.startswith("async function"):
                output += "- **Function declaration**: defines a named function.\n"
            elif line_content.startswith("const ") or line_content.startswith("let ") or line_content.startswith("var "):
                output += "- **Variable declaration**: declares a new variable.\n"
            elif line_content.startswith("class "):
                output += "- **Class declaration**: defines a new class.\n"
            elif line_content.startswith("interface "):
                output += "- **Interface declaration**: defines a TypeScript interface.\n"
            elif line_content.startswith("type "):
                output += "- **Type alias**: defines a type alias.\n"
            elif line_content.startswith("return "):
                output += "- **Return statement**: returns a value from the current function.\n"
            elif line_content.startswith("if ") or line_content.startswith("else ") or line_content.startswith("else if"):
                output += "- **Conditional branch**: controls flow based on a condition.\n"
            elif line_content.startswith("for ") or line_content.startswith("while ") or line_content.startswith("do "):
                output += "- **Loop**: iterates over a collection or repeats execution.\n"
            elif line_content.startswith("try ") or line_content.startswith("catch ") or line_content.startswith("finally "):
                output += "- **Error handling**: catches and handles exceptions.\n"
            elif line_content.startswith("switch ") or line_content.startswith("case ") or line_content.startswith("default:"):
                output += "- **Switch/case**: multi-branch conditional.\n"
            elif line_content.startswith("//") or line_content.startswith("#") or line_content.startswith("/*") or line_content.startswith("*"):
                output += "- **Comment**: documentation or code note.\n"
            elif line_content.startswith("}"):
                output += "- **Closing brace**: closes a block (function, class, if, etc.).\n"
            elif "=>" in line_content:
                output += "- **Arrow function**: shorthand function expression.\n"
            elif " = " in line_content and "(" in line_content:
                output += "- **Assignment/call**: variable assignment with function call.\n"
            elif "(" in line_content and ")" in line_content:
                output += "- **Function/method call**: invokes a function or method.\n"
            else:
                output += "- Expression or statement.\n"
        else:
            output += "## Line Content\n\n"
            output += f"```\n{line_content}\n```\n"
            output += "\n> Note: tree-sitter AST analysis is only available for TypeScript/JavaScript files.\n"

        # ── 의존성 그래프 (호출하는 함수 / 호출되는 함수) ──
        if ext in TS_JS_EXTS and ast_engine.is_available():
            output += "\n## Dependency Graph\n\n"
            try:
                calls = ast_engine.extract_calls(content, ext)
                # 현재 라인을 포함하는 함수 찾기
                enclosing_fn = None
                for fn in ast.get("functions", []):
                    if fn["line"] <= line_number <= fn.get("end_line", fn["line"]):
                        enclosing_fn = fn
                        break
                if enclosing_fn:
                    fn_start = enclosing_fn["line"]
                    fn_end = enclosing_fn.get("end_line", fn_start)
                    # 이 함수가 호출하는 함수들
                    calls_from_fn = [c for c in calls if fn_start <= c.get("line", 0) <= fn_end and c.get("name") != enclosing_fn["name"]]
                    if calls_from_fn:
                        output += f"**`{enclosing_fn['name']}()` calls:**\n"
                        for c in calls_from_fn[:8]:
                            output += f"- `{c['name']}()` (line {c['line']})\n"
                    else:
                        output += f"- `{enclosing_fn['name']}()` calls no internal functions.\n"

                    # 이 함수를 호출하는 함수들
                    callers = [c for c in calls if c.get("name") == enclosing_fn["name"] and c.get("line") != line_number]
                    if callers:
                        caller_lines = {}
                        for c in callers:
                            for fn in ast.get("functions", []):
                                if fn["line"] <= c["line"] <= fn.get("end_line", fn["line"]):
                                    caller_lines[fn["name"]] = caller_lines.get(fn["name"], 0) + 1
                        if caller_lines:
                            output += f"\n**Called by:**\n"
                            for caller_name, count in sorted(caller_lines.items(), key=lambda x: -x[1])[:5]:
                                output += f"- `{caller_name}()` ({count} call(s))\n"
                    else:
                        output += f"\n- `{enclosing_fn['name']}()` is not called internally.\n"
                else:
                    output += "- Line is at top level (not inside a function).\n"
            except Exception:
                output += "- Could not extract dependency graph.\n"
        else:
            # Python/Go/Rust — regex 기반 간단 추출
            output += "\n## Dependency Graph\n\n"
            try:
                func_defs = re.findall(r'(?:def |func |fn |function |async function )(\w+)', content)
                current_fn = None
                for fn in reversed(lines[:line_number]):
                    m = re.match(r'\s*(?:def |func |fn |function |async function )(\w+)', fn)
                    if m:
                        current_fn = m.group(1)
                        break
                if current_fn:
                    # 이 함수가 호출하는 함수들
                    fn_start_line = max(0, line_number - 10)
                    fn_block = "\n".join(lines[fn_start_line:min(len(lines), fn_start_line + 30)])
                    called = [f for f in func_defs if f != current_fn and f in fn_block]
                    if called:
                        output += f"**`{current_fn}()` likely calls:**\n"
                        for c in called[:8]:
                            output += f"- `{c}()`\n"
                    else:
                        output += f"- `{current_fn}()` likely calls no internal functions.\n"
                else:
                    output += "- Could not determine enclosing function.\n"
            except Exception:
                output += "- Could not extract dependency graph.\n"

        output += "\n## Surrounding Context\n\n"
        start = max(0, line_number - 4)
        end = min(len(lines), line_number + 3)
        output += "```\n"
        for i in range(start, end):
            prefix = "→" if i + 1 == line_number else " "
            output += f"{prefix} {i+1:4d} | {lines[i]}\n"
        output += "```\n"

        try_crow_ingest(f"explain_code: {file_path}:{line_number} — {line_content[:60]}", register="context")
        output += _markdown_footer()
        return output

    @mcp.tool
    def analyze_changes() -> str:
        """현재 워크스페이스의 git diff를 분석하여 변경된 파일 목록과 diff 내용을 반환합니다.
        git diff --stat + git diff를 실행하여 변경 사항을 요약하고,
        Crow Memory에서 관련 컨텍스트를 조회합니다.

        Returns:
            Markdown 보고서: 변경 파일 목록, diff 내용, 관련 Crow 기억
        """
        root = os.getcwd()
        output = _markdown_header("Git Changes Analysis")

        try:
            stat_result = subprocess.run(["git", "diff", "--stat"], cwd=root, capture_output=True, text=True, timeout=10)
            stat_output = stat_result.stdout.strip()
            diff_result = subprocess.run(["git", "diff"], cwd=root, capture_output=True, text=True, timeout=10)
            diff_output = diff_result.stdout.strip()

            if not stat_output:
                output += "✅ No uncommitted changes detected.\n"
                output += _markdown_footer()
                return output

            changed_files = []
            for line in stat_output.split("\n"):
                if "|" in line:
                    parts = line.split("|")
                    file_path = parts[0].strip()
                    changed_files.append(file_path)

            output += f"## Changed Files ({len(changed_files)})\n\n"
            for f in changed_files:
                output += f"- `{_normalize_path(f)}`\n"
            output += "\n"

            output += "## Change Classification\n\n"
            classifications = {"refactoring": 0, "bugfix": 0, "feature": 0, "docs": 0, "other": 0}
            for f in changed_files:
                ext = os.path.splitext(f)[1].lower()
                if ext in (".md", ".txt", ".rst"):
                    classifications["docs"] += 1
                elif ext in (".ts", ".tsx", ".js", ".jsx", ".py", ".go"):
                    file_diff = ""
                    in_file = False
                    for line in diff_output.split("\n"):
                        if f"diff --git a/{f}" in line:
                            in_file = True
                        elif line.startswith("diff --git"):
                            in_file = False
                        if in_file:
                            file_diff += line + "\n"
                    if "TODO" in file_diff or "FIXME" in file_diff:
                        classifications["refactoring"] += 1
                    elif "fix" in file_diff.lower() or "bug" in file_diff.lower() or "error" in file_diff.lower():
                        classifications["bugfix"] += 1
                    elif "test" in file_diff.lower() or "feat" in file_diff.lower():
                        classifications["feature"] += 1
                    else:
                        classifications["feature"] += 1
                else:
                    classifications["other"] += 1
            for ctype, count in classifications.items():
                if count > 0:
                    emoji = {"refactoring": "🔧", "bugfix": "🐛", "feature": "✨", "docs": "📝", "other": "❓"}
                    output += f"- {emoji.get(ctype, '•')} **{ctype}**: {count} file(s)\n"
            output += "\n"

            output += "## Diff Content\n\n"
            if len(diff_output) > 8000:
                output += f"> Diff is too large ({len(diff_output)} chars), showing first 8000 chars\n\n"
                output += "```diff\n" + diff_output[:8000] + "\n```\n"
                output += f"\n> ... ({len(diff_output) - 8000} more chars)\n"
            else:
                output += "```diff\n" + diff_output + "\n```\n"

            if changed_files:
                output += "\n## 🧠 Related Crow Context\n\n"
                for f in changed_files[:5]:
                    try:
                        file_name = os.path.basename(f)
                        past_context = try_crow_recall(query=f"file changes in {file_name}", register="context", limit=2)
                        if past_context:
                            for item in past_context:
                                content = item.get("content", item.get("value", str(item)))
                                output += f"- `{file_name}`: {content[:200]}\n"
                        else:
                            output += f"- `{file_name}`: No Crow context found.\n"
                    except Exception:
                        output += f"- `{file_name}`: Could not query Crow.\n"

        except FileNotFoundError:
            output += "❌ Git not available. Make sure git is installed and this is a git repository.\n"
        except subprocess.TimeoutExpired:
            output += "❌ Git diff timed out.\n"
        except Exception as e:
            output += f"❌ Error: {e}\n"

        try_crow_ingest(f"analyze_changes: {len(changed_files)} files changed", register="life_context")
        output += _markdown_footer()
        return output

    @mcp.tool
    def review_pr(base_branch: str = "main", head_branch: str = "") -> str:
        """analyze_changes + review_code를 통합하여 PR 리뷰 보고서를 생성합니다.
        두 브랜치 간의 git diff를 분석하고, 변경된 파일들에 대해 코드 리뷰를 수행합니다.

        Args:
            base_branch: 기준 브랜치 (기본: main)
            head_branch: 대상 브랜치 (기본: 현재 브랜치)

        Returns:
            Markdown PR 리뷰 보고서
        """
        err = _validate_string(base_branch, "base_branch")
        if err:
            return _markdown_header("PR Review Error", "❌") + f"**{err}**\n" + _markdown_footer()

        root = os.getcwd()
        output = _markdown_header("Pull Request Review")
        output += f"> **Base**: `{base_branch}` → **Head**: `{head_branch or 'current'}`\n\n"

        try:
            diff_cmd = ["git", "diff"]
            if head_branch:
                diff_cmd.extend([f"{base_branch}...{head_branch}"])
            else:
                diff_cmd.append(f"{base_branch}..HEAD")

            stat_result = subprocess.run(diff_cmd + ["--stat"], cwd=root, capture_output=True, text=True, timeout=10)
            stat_output = stat_result.stdout.strip()
            diff_result = subprocess.run(diff_cmd, cwd=root, capture_output=True, text=True, timeout=10)
            diff_output = diff_result.stdout.strip()

            if not stat_output:
                output += "⚠️ No differences found between branches.\n"
                output += _markdown_footer()
                return output

            changed_files = []
            for line in stat_output.split("\n"):
                if "|" in line:
                    parts = line.split("|")
                    file_path = parts[0].strip()
                    changed_files.append(file_path)

            output += f"## 📂 Changed Files ({len(changed_files)})\n\n"
            for f in changed_files:
                output += f"- `{_normalize_path(f)}`\n"
            output += "\n"

            total_additions = 0
            total_deletions = 0
            for line in stat_output.split("\n"):
                m = re.search(r'(\d+) insertion', line)
                if m:
                    total_additions += int(m.group(1))
                m = re.search(r'(\d+) deletion', line)
                if m:
                    total_deletions += int(m.group(1))

            output += f"## 📈 Stats\n\n"
            output += f"- **{len(changed_files)}** files changed\n"
            output += f"- **+{total_additions}** / **-{total_deletions}** lines\n\n"

            # 의존성 분석
            output += "## 🔗 Dependency Analysis\n\n"
            changed_set = set(changed_files)
            project_root = Path(root)
            file_deps = defaultdict(set)
            for f in changed_files:
                p = project_root / f
                if p.exists():
                    content_f = _read_file_content(p)
                    if content_f:
                        ext_f = p.suffix.lower()
                        if ext_f in TS_JS_EXTS:
                            ast_imports = _get_ast_engine().extract_imports(content_f, ext_f)
                            for imp in ast_imports:
                                file_deps[f].add(imp["module"])
                        else:
                            regex_imports = _extract_regex_imports(str(p))
                            for imp in regex_imports:
                                file_deps[f].add(imp)
            cross_refs = []
            for f, deps_set in file_deps.items():
                for dep in deps_set:
                    for cf in changed_set:
                        if cf != f and (dep in cf or cf.endswith(dep.replace(".", "/"))):
                            cross_refs.append((f, cf))
            if cross_refs:
                output += "⚠️ Cross-file dependencies detected in this PR:\n\n"
                for src, target in cross_refs[:5]:
                    output += f"- `{src}` → imports `{target}`\n"
                output += "\n> These files should be reviewed together for consistency.\n"
            else:
                output += "✅ No cross-file dependencies detected.\n"
            output += "\n"

            # 롤백 위험도 평가
            output += "## ⚠️ Rollback Risk Assessment\n\n"
            risk_score = 0
            risk_factors = []
            if len(changed_files) > 10:
                risk_score += 2
                risk_factors.append(f"Large PR ({len(changed_files)} files)")
            if total_deletions > 100:
                risk_score += 2
                risk_factors.append(f"Heavy deletions ({total_deletions} lines)")
            if total_additions > 200:
                risk_score += 1
                risk_factors.append(f"Large additions ({total_additions} lines)")
            if cross_refs:
                risk_score += 2
                risk_factors.append(f"Cross-file dependencies ({len(cross_refs)})")
            if "package.json" in changed_set or "go.mod" in changed_set or "requirements.txt" in changed_set:
                risk_score += 3
                risk_factors.append("Dependency manifest changed")
            if risk_score == 0:
                output += "🟢 **Low risk** — Safe to merge after review.\n"
            elif risk_score <= 3:
                output += "🟡 **Medium risk** — Review carefully.\n"
            elif risk_score <= 6:
                output += "🟠 **High risk** — Multiple reviewers recommended.\n"
            else:
                output += "🔴 **Critical risk** — Consider splitting this PR.\n"
            if risk_factors:
                output += "\nRisk factors:\n"
                for rf in risk_factors:
                    output += f"- {rf}\n"
            output += "\n"

            output += "## 📝 Code Review per File\n\n"
            for f in changed_files[:10]:
                output += f"### `{_normalize_path(f)}`\n\n"
                p = project_root / f
                if p.exists():
                    from bridge.tools.reviewer import review_code as _review_code
                    review_result = _review_code(str(f))
                    for line in review_result.split("\n"):
                        if "⚠️" in line or "📝" in line or "✅" in line or "Found" in line:
                            output += line + "\n"
                else:
                    output += "*(file deleted in this PR)*\n"
                output += "\n"

            output += "## 🔍 Diff Preview\n\n"
            if len(diff_output) > 4000:
                output += f"```diff\n{diff_output[:4000]}\n```\n"
                output += f"\n> ... ({len(diff_output) - 4000} more chars)\n"
            else:
                output += f"```diff\n{diff_output}\n```\n"

            output += "\n## 🧠 Crow Memory Context\n\n"
            for f in changed_files[:3]:
                file_name = os.path.basename(f)
                past_context = try_crow_recall(query=f"review {file_name}", register="style", limit=2)
                if past_context:
                    for item in past_context:
                        content = item.get("content", item.get("value", str(item)))
                        output += f"- `{file_name}`: {content[:200]}\n"

        except FileNotFoundError:
            output += "❌ Git not available. Make sure git is installed and this is a git repository.\n"
        except subprocess.TimeoutExpired:
            output += "❌ Git diff timed out.\n"
        except Exception as e:
            output += f"❌ Error: {e}\n"

        try_crow_ingest(json.dumps({"action": "review_pr", "base": base_branch, "head": head_branch, "files": len(changed_files)}), register="context")
        output += _markdown_footer()
        return output

    @mcp.tool
    def refactor_across_files(pattern: str, new_pattern: str, file_patterns: Optional[str] = None,
                               dry_run: bool = True) -> str:
        """search_codebase로 패턴을 찾고, 모든 발생 위치에 대해 일괄 수정 제안을 생성합니다.
        dry_run=True면 변경 제안서만, dry_run=False면 yocto 백업 후 실제 파일 수정을 수행합니다.

        Args:
            pattern: 찾을 코드 패턴 (검색어)
            new_pattern: 대체할 새 패턴 (변경 제안)
            file_patterns: 검색 대상 파일 패턴 (예: *.ts,*.tsx). 쉼표로 구분.
            dry_run: True면 제안만 (기본값: True), False면 실제 파일 수정

        Returns:
            Markdown 리팩토링 제안서: 각 발생 위치와 제안된 변경 사항 (diff 블록 포함)
        """
        err = _validate_string(pattern, "pattern")
        if err:
            return _markdown_header("Refactoring Error", "❌") + f"**{err}**\n" + _markdown_footer()
        err = _validate_string(new_pattern, "new_pattern")
        if err:
            return _markdown_header("Refactoring Error", "❌") + f"**{err}**\n" + _markdown_footer()

        from bridge.tools.scout import search_codebase

        output = _markdown_header("Multi-File Refactoring Proposal")
        output += f"> **Search**: `{pattern}`\n"
        output += f"> **Replace with**: `{new_pattern}`\n"
        output += f"> **File patterns**: `{file_patterns or '*.ts,*.tsx,*.js,*.jsx,*.py'}`\n"
        output += f"> **Mode**: {'🔍 Dry run (proposal only)' if dry_run else '🚀 Apply changes'}\n\n"

        search_result = search_codebase(query=pattern, file_patterns=file_patterns, max_results=100)
        occurrences = []
        for line in search_result.split("\n"):
            m = re.match(r'^- `(.+?:\d+):', line)
            if m:
                occurrences.append(m.group(1))
            m2 = re.match(r'^- `(.+?:\d+)`', line)
            if m2:
                occurrences.append(m2.group(1))

        if not occurrences:
            output += "✅ No occurrences found for this pattern.\n"
            output += _markdown_footer()
            return output

        output += f"## Found {len(occurrences)} Occurrences\n\n"
        by_file = defaultdict(list)
        for occ in occurrences:
            parts = occ.split(":")
            if len(parts) >= 2:
                by_file[parts[0]].append(parts[1])

        output += f"### Files Affected: {len(by_file)}\n\n"
        for file_path, lines in sorted(by_file.items()):
            line_list = ", ".join(lines[:10])
            suffix = f" ... and {len(lines)-10} more" if len(lines) > 10 else ""
            output += f"- `{_normalize_path(file_path)}` — lines {line_list}{suffix}\n"

        output += "\n## Suggested Changes\n\n"
        for file_path, lines in sorted(by_file.items())[:10]:
            actual_path = Path(os.getcwd()) / file_path
            if not actual_path.exists():
                continue
            content = _read_file_content(actual_path)
            if content is None:
                continue
            file_lines = content.split("\n")
            output += f"### `{_normalize_path(file_path)}`\n\n"
            output += f"```diff\n"
            for line_num_str in lines[:5]:
                idx = int(line_num_str) - 1
                if 0 <= idx < len(file_lines):
                    original = file_lines[idx]
                    output += f"-{original}\n"
                    suggested = original.replace(pattern, new_pattern)
                    output += f"+{suggested}\n"
            output += f"```\n\n"

        output += "## 📊 Impact Analysis\n\n"
        total_affected_lines = sum(len(ls) for ls in by_file.values())
        output += f"- **Scale**: {len(occurrences)} changes across {len(by_file)} files\n"
        output += f"- **Total affected lines**: {total_affected_lines}\n"
        if total_affected_lines > 50:
            output += "- **Risk**: 🔴 **High** — extensive changes, may introduce side effects\n"
        elif total_affected_lines > 20:
            output += "- **Risk**: 🟡 **Medium** — moderate changes, review recommended\n"
        else:
            output += "- **Risk**: 🟢 **Low** — limited changes\n"
        if len(by_file) > 5:
            output += "- **Dependency impact**: Changes span multiple files — ensure imports are updated\n"

        # ── Apply changes (dry_run=False) ──
        if not dry_run:
            output += "\n## Applied Changes\n\n"
            applied_count = 0
            failed_count = 0
            for file_path, lines in sorted(by_file.items()):
                actual_path = Path(os.getcwd()) / file_path
                if not actual_path.exists():
                    failed_count += 1
                    continue
                try:
                    content = _read_file_content(actual_path)
                    if content is None:
                        failed_count += 1
                        continue
                    file_lines = content.split("\n")
                    new_lines = list(file_lines)
                    modified = False
                    for line_num_str in lines:
                        idx = int(line_num_str) - 1
                        if 0 <= idx < len(new_lines) and pattern in new_lines[idx]:
                            new_lines[idx] = new_lines[idx].replace(pattern, new_pattern)
                            modified = True
                    if modified:
                        # yocto 백업: create .bak file
                        bak_path = actual_path.with_suffix(actual_path.suffix + ".bak")
                        if not bak_path.exists():
                            import shutil
                            shutil.copy2(str(actual_path), str(bak_path))
                        actual_path.write_text("\n".join(new_lines), encoding="utf-8")
                        applied_count += 1
                        output += f"- ✅ `{_normalize_path(file_path)}` — {len(lines)} change(s) applied\n"
                except Exception:
                    failed_count += 1
            output += f"\n**Result**: {applied_count} files modified, {failed_count} failed\n"
            if applied_count > 0:
                output += "\n> ⚠️ Backup files (.bak) created in the same directory. Restore by renaming `.bak` to original.\n"
        else:
            output += "\n> Note: This is a **proposal only**. No files have been modified.\n"
            output += "> To apply changes, call with `dry_run=False` or use your editor's find-and-replace.\n"

        try_crow_ingest(json.dumps({"action": "refactor_across_files", "pattern": pattern, "new_pattern": new_pattern, "occurrences": len(occurrences), "files_affected": len(by_file), "dry_run": dry_run}), register="style")
        output += _markdown_footer()
        return output
