# VibeZoo Bridge — Tester 도구 그룹
# generate_tests + analyze_coverage

import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Optional

from bridge.config import (
    VERSION, DEFAULT_EXCLUDE_DIRS, SOURCE_EXTS, TS_JS_EXTS,
)
from bridge.utils import (
    _markdown_header, _markdown_footer,
    _validate_string, _validate_file_path, _validate_int,
    _read_file_content, _truncate, _normalize_path,
    _iter_project_files, _iter_project_files_cached,
    _npx_cmd, get_project_root,
)
from bridge.crow_client import try_crow_ingest, try_crow_recall
from bridge.ast_engine import AstEngine
from bridge.ast_singleton import get_ast_engine as _get_ast_engine
from bridge.tool_context import (
    make_generate_tests_context,
    format_manifest_markdown,
    MANIFEST_GENERATE_TESTS,
)
from bridge.i18n import t


def register(mcp):
    """Tester 도구 등록"""

    @mcp.tool
    def generate_tests(source_path: str, framework: Optional[str] = None) -> str:
        """지정된 소스 파일에 대한 단위 테스트를 생성합니다.
        tree-sitter AST로 함수 시그니처를 더 정확히 감지합니다.

        Args:
            source_path: 테스트 대상 소스 파일 경로
            framework: 테스트 프레임워크 (jest, vitest, pytest, go test). 자동 감지됨.
        """
        err = _validate_file_path(source_path)
        if err:
            return _markdown_header(t("Test Generation Error"), "❌") + f"**{err}**\n" + _markdown_footer()

        root = Path(os.getcwd())
        target = Path(source_path)
        if not target.is_absolute():
            target = root / source_path

        if not target.exists() or not target.is_file():
            return _markdown_header(t("Test Generation Error"), "❌") + f"**{t('File not found: {0}', source_path)}**\n" + _markdown_footer()

        content = _read_file_content(target)
        if content is None:
            return _markdown_header(t("Test Generation Error"), "❌") + f"**{t('Cannot read file: {0}', source_path)}**\n" + _markdown_footer()

        ext = target.suffix.lower()
        lines = content.split("\n")

        ast_engine = _get_ast_engine()
        ast_engine._init_legacy_tree_sitter()

        func_count = 0
        function_names = []
        function_details = []
        if ext in TS_JS_EXTS:
            ast = ast_engine.parse(content, ext)
            functions = ast.get("functions", [])
            func_count = len(functions)
            function_names = [fn["name"] for fn in functions[:20]]
            function_details = functions
        else:
            # Python/Go/Rust: AST or regex
            ast = ast_engine.parse(content, ext)
            if ast.get("functions"):
                functions = ast["functions"]
                func_count = len(functions)
                function_names = [fn["name"] for fn in functions[:20]]
                function_details = functions
            else:
                for line in lines:
                    if re.search(r'(?:export\s+)?(?:function|async function|const\s+\w+\s*=\s*(?:async\s*)?\(|def\s+\w+\s*\()', line):
                        func_count += 1

        # ── 데이터 수집 (함수 시그니처 + 타입 + 의존성) ──
        imports = []
        if ext in TS_JS_EXTS:
            ast_imports = ast_engine.extract_imports(content, ext)
            imports = [{"module": i["module"], "type": i.get("type", "import"), "line": i.get("line", 0)} for i in ast_imports]
        else:
            from bridge.utils import _extract_regex_imports
            raw_imports = _extract_regex_imports(str(target))
            imports = [{"module": i, "type": "import", "line": 0} for i in raw_imports]

        language = "python" if ext == ".py" else "go" if ext == ".go" else "rust" if ext == ".rs" else "typescript" if ext in (".ts", ".tsx") else "javascript"

        # ── 함수 의존성 그래프 추출 (호출하는 내부 함수 목록) ──
        dependencies = []
        try:
            calls = ast_engine.extract_calls(content, ext)
            # 함수 내에서 호출하는 내부 함수 식별
            for fn in function_details:
                fn_start = fn.get("line", 0)
                fn_end = fn.get("end_line", fn_start)
                fn_lines = content.split("\n")[fn_start:fn_end] if fn_start > 0 else []
                fn_calls = []
                for call in calls:
                    call_line = call.get("line", 0)
                    if fn_start <= call_line <= fn_end:
                        call_name = call.get("name", "")
                        # 자기 자신 호출 제외
                        if call_name != fn.get("name", ""):
                            fn_calls.append(call_name)
                if fn_calls:
                    dependencies.append({
                        "function": fn.get("name", "anonymous"),
                        "calls": list(set(fn_calls)),
                        "call_count": len(set(fn_calls)),
                    })
        except Exception:
            pass

        # ── Mock 제안 템플릿 생성 ──
        mock_suggestions = []
        for imp in imports:
            module = imp.get("module", "")
            if module.startswith(".") or module.startswith("/"):
                # 내부 모듈 → 모킹 필요
                base = os.path.basename(module)
                if ext in (".ts", ".tsx"):
                    mock_suggestions.append(f"jest.mock('{module}', ...)")
                elif ext == ".py":
                    mock_suggestions.append(f"unittest.mock.patch('{module}')")
                elif ext == ".go":
                    mock_suggestions.append(f"interface mock for '{module}'")

        # 외부 API 호출 모킹
        for dep in dependencies:
            for call_name in dep.get("calls", []):
                if call_name.startswith("fetch") or call_name.startswith("axios") or call_name.startswith("request"):
                    mock_for = f"{call_name}()"
                    if ext in (".ts", ".tsx"):
                        mock_suggestions.append(f"jest.spyOn(global, '{call_name}').mockResolvedValue(...)")
                    elif ext == ".py":
                        mock_suggestions.append(f"unittest.mock.patch('requests.get')")
                    break

        # 중복 제거
        mock_suggestions = list(dict.fromkeys(mock_suggestions))

        # ── ToolContext 생성 ──
        ctx = make_generate_tests_context(
            source_path=str(target),
            language=language,
            functions=function_details,
            imports=imports,
            existing_tests=[],  # 향후: 기존 테스트 파일 스캔
        )
        ctx.dependencies = dependencies
        ctx.mock_suggestions = mock_suggestions

        # ── 기존 템플릿 출력 ──
        output = _markdown_header(f"Test Generation: {target.name}")
        output += f"- **Framework**: {framework or 'auto-detect'}\n"
        output += f"- **Functions detected**: {func_count}\n"
        output += f"- **Lines**: {len(lines)}\n\n"

        if function_names:
            output += f"### {t('Functions Found')}\n\n"
            for name in function_names:
                output += f"- `{name}()`\n"
            output += "\n"

        output += f"## {t('Boundary Value Test Cases')}\n\n"
        if function_details:
            param_guesses = []
            for fn in function_details[:5]:
                fn_text = "\n".join(content.split("\n")[fn["line"]-1:min(len(content.split("\n")), fn["line"]+2)])
                params = re.findall(r'(\w+)\s*(?::\s*\w+)?\s*(?:[,)])', fn_text)
                if params:
                    real_params = [p for p in params if p not in (fn["name"], "async", "function", "export", "default")]
                    for p in real_params[:3]:
                        param_guesses.append((fn["name"], p, "any"))
            if param_guesses:
                for fn_name, param_name, param_type in param_guesses:
                    output += f"- `{fn_name}('{param_name}')`: boundary tests → null, empty, valid, invalid, large input\n"
            else:
                output += f"- {t('No parameters detected for boundary analysis.')}\n"
        else:
            output += f"- {t('No function details available.')}\n"
        output += "\n"

        output += f"## {t('Branch Coverage')}\n\n"
        branch_count = 0
        for line in lines:
            if re.search(r'\bif\s*\(', line) or 'else if' in line or 'else' in line.strip()[:4]:
                branch_count += 1
        output += f"- **Conditional branches detected**: {branch_count}\n"
        output += f"- **{t('Suggested test cases')}**: {t('test each branch (true/false)')}\n"
        switch_count = len(re.findall(r'\bswitch\s*\(', content))
        if switch_count > 0:
            output += f"- **Switch statements**: {switch_count} — test each case including default\n"
        output += "\n"

        output += f"## {t('Error Case Generation')}\n\n"
        error_indicators = {
            "try-catch": len(re.findall(r'\btry\s*\{', content)),
            "null check": len(re.findall(r'(?:===?\s*null|!==?\s*null|==\s*null)', content)),
            "undefined check": len(re.findall(r'(?:===?\s*undefined|!==?\s*undefined)', content)),
            "error return": len(re.findall(r'throw\s+new\s+', content)),
        }
        has_errors = False
        for name, count in error_indicators.items():
            if count > 0:
                output += f"- `{name}`: {count} occurrence(s) → add error-handling test\n"
                has_errors = True
        if not has_errors:
            output += f"- {t('No explicit error handling detected. Add tests for:')}\n"
            output += f"  - {t('Null/undefined inputs')}\n"
            output += f"  - {t('Empty collections')}\n"
            output += f"  - {t('Invalid parameter types')}\n"
        output += "\n"

        output += f"## {t('Mock Data Suggestions')}\n\n"
        mock_suggestions = []
        if ext == ".py":
            mock_suggestions.append("- Use `unittest.mock` or `pytest.fixture`")
        elif ext in (".ts", ".tsx"):
            mock_suggestions.append("- Use `vi.mock()` (Vitest) or `jest.mock()`")
        elif ext == ".go":
            mock_suggestions.append("- Use `testing` package with interface mocks")

        all_param_names = []
        for fn in function_details[:5]:
            fn_text_str = "\n".join(content.split("\n")[fn["line"]-1:fn["line"]+1])
            params_found = re.findall(r'\b(\w+)\s*:\s*(\w+)', fn_text_str)
            for pname, ptype in params_found:
                if pname not in (fn["name"], "async", "function"):
                    all_param_names.append((pname, ptype))

        seen_types = set()
        for pname, ptype in all_param_names:
            if ptype not in seen_types:
                seen_types.add(ptype)
                if ptype == "string":
                    mock_suggestions.append(f"- `{pname}` (string): use \"test-{pname}\"")
                elif ptype in ("number", "int"):
                    mock_suggestions.append(f"- `{pname}` ({ptype}): use `42`, `0`, `-1`")
                elif ptype == "boolean":
                    mock_suggestions.append(f"- `{pname}` (boolean): use `true`, `false`")
                elif ptype == "array":
                    mock_suggestions.append(f"- `{pname}` (array): use `[]`, `[1,2,3]`")
        for s in mock_suggestions:
            output += s + "\n"

        output += f"\n## {t('Expected Behavior Inference')}\n\n"
        for fn in function_details[:5]:
            fn_name = fn["name"]
            if fn_name.startswith("get") or fn_name.startswith("find") or fn_name.startswith("fetch"):
                output += f"- `{fn_name}()`: Returns data → expect defined result\n"
            elif fn_name.startswith("set") or fn_name.startswith("save") or fn_name.startswith("create"):
                output += f"- `{fn_name}()`: Mutates/creates state → expect side effect or return ID\n"
            elif fn_name.startswith("delete") or fn_name.startswith("remove"):
                output += f"- `{fn_name}()`: Deletes data → expect success/true\n"
            elif fn_name.startswith("validate") or fn_name.startswith("is") or fn_name.startswith("has"):
                output += f"- `{fn_name}()`: Returns boolean → expect true/false cases\n"
            elif fn_name.startswith("format") or fn_name.startswith("transform") or fn_name.startswith("convert"):
                output += f"- `{fn_name}()`: Transforms data → expect specific output format\n"
            elif fn_name.startswith("handle") or fn_name.startswith("on"):
                output += f"- `{fn_name}()`: Event handler → expect side effects or state changes\n"
            else:
                output += f"- `{fn_name}()`: Check function → test return value\n"

        if ext in (".ts", ".tsx"):
            output += f"\n## {t('Jest/Vitest Test Structure')}\n\n"
            output += "```typescript\nimport { describe, it, expect } from 'vitest';\n"
            output += f"import {{ ... }} from './{target.stem}';\n\n"
            output += "describe('', () => {\n  it('should work', () => {\n    // TODO: write test\n  });\n});\n```\n"
        elif ext == ".py":
            output += f"\n## {t('pytest Test Structure')}\n\n"
            output += '```python\nimport pytest\n\n\ndef test_():\n    """TODO: write test"""\n    pass\n```\n'
        elif ext == ".go":
            output += f"\n## {t('Go Test Structure')}\n\n"
            output += '```go\npackage main\n\nimport "testing"\n\nfunc Test_(t *testing.T) {\n\t// TODO: write test\n}\n```\n'

        # ── LLM_TASK 섹션 추가 ──
        output += "\n<!-- LLM_TASK\n"
        output += "도구: generate_tests\n"
        output += "버전: 1.0\n"
        output += "설명: 함수 시그니처를 기반으로 단위 테스트 케이스 생성\n"
        output += f"대상 파일: {source_path}\n"
        output += f"언어: {language}\n"
        output += f"감지된 함수 수: {func_count}\n"
        output += f"LLM 지시사항: LLM은 이 데이터로 실제 동작하는 테스트 케이스를 생성하세요.\n"
        output += "-->\n\n"

        # ── ToolContext 마크다운 추가 ──
        output += ctx.to_markdown() + "\n\n"

        try_crow_ingest(f"Generated tests for {target.name}: {func_count} functions, {branch_count} branches", register="context")
        output += _markdown_footer()
        return output

    @mcp.tool
    def analyze_coverage(target_path: Optional[str] = None) -> str:
        """테스트 커버리지를 분석합니다.
        빠른 경로: 테스트 파일 존재 여부, 테스트/소스 비율 자체 분석.
        전체 경로: vitest/pytest --cov 실행 (있을 경우).

        Args:
            target_path: 분석 대상 경로
        """
        root = Path(get_project_root(target_path))
        output = _markdown_header(t("Coverage Analysis"))

        test_patterns = {
            ".ts": [".test.ts", ".spec.ts", ".test.tsx", ".spec.tsx", "__tests__"],
            ".tsx": [".test.tsx", ".spec.tsx", "__tests__"],
            ".js": [".test.js", ".spec.js", "__tests__"],
            ".py": ["test_", "_test", "tests/"],
            ".go": ["_test.go"],
        }
        source_files = []
        test_files = []
        source_to_test = defaultdict(list)
        test_to_source = defaultdict(list)

        for p in _iter_project_files_cached(root, extensions=SOURCE_EXTS, exclude_dirs=DEFAULT_EXCLUDE_DIRS):
            rel = _normalize_path(str(p.relative_to(root)))
            fname = p.name
            ext = p.suffix.lower()
            is_test = False
            if ext in test_patterns:
                for pattern in test_patterns[ext]:
                    if pattern in fname or pattern in rel.replace("\\", "/"):
                        is_test = True
                        break
            if is_test:
                test_files.append(rel)
                for ext2 in [".ts", ".tsx", ".js", ".py", ".go"]:
                    src_patterns = [
                        rel.replace(".test", "").replace(".spec", "").replace("_test", ""),
                        rel.replace("__tests__/", "").replace("test/", "").replace("tests/", ""),
                    ]
                    for sp in src_patterns:
                        src_path = Path(root) / sp
                        if src_path.exists() and not any(tp in sp for tp in ["test", ".test.", ".spec."]):
                            source_to_test[sp].append(rel)
                            test_to_source[rel].append(sp)
            else:
                source_files.append(rel)

        total_source = len(source_files)
        total_tests = len(test_files)
        ratio = round(total_tests / max(total_source, 1), 2)

        output += f"## {t('Coverage Analysis (no external tools)')}\n\n"
        output += f"- **Source files**: {total_source}\n"
        output += f"- **Test files**: {total_tests}\n"
        output += f"- **Test/Source ratio**: {ratio}\n"
        if total_tests == 0:
            output += f"- ⚠️ **{t('No test files detected.')}**\n"
        elif ratio < 0.3:
            output += f"- ⚠️ Low coverage likely (ratio {ratio} < 0.3)\n"
        elif ratio >= 0.5:
            output += f"- ✅ Decent test presence (ratio {ratio})\n"

        output += f"\n## {t('Missing Test Detection')}\n\n"
        untested_sources = [src for src in source_files if src not in source_to_test]
        if untested_sources:
            output += f"⚠️ {len(untested_sources)} source files have NO corresponding test:\n\n"
            for src in untested_sources[:10]:
                output += f"- `{src}`\n"
            if len(untested_sources) > 10:
                output += f"- ... +{len(untested_sources)-10} more\n"
            output += f"\n> {t('Tip: Create test files following naming conventions (`.test.ts`, `_test.go`, `test_*.py`)')}\n"
        else:
            output += f"✅ {t('All source files have corresponding test files.')}\n"
        output += "\n"

        if test_files:
            output += f"### {t('Test Files')}\n"
            for tf in test_files[:10]:
                output += f"- `{tf}`\n"
            if len(test_files) > 10:
                output += f"- ... +{len(test_files)-10} {t('more')}\n"
        if test_to_source:
            output += f"\n### {t('Test → Source Mapping')}\n\n"
            for test_f, src_list in list(test_to_source.items())[:5]:
                output += f"- `{test_f}` → {', '.join(src_list[:3])}\n"

        ext_tool_used = False
        if (root / "package.json").exists() and (root / "node_modules" / ".bin" / "vitest").exists():
            try:
                result = subprocess.run([_npx_cmd(), "vitest", "run", "--coverage", "--reporter=text"],
                                       cwd=str(root), capture_output=True, text=True, timeout=30)
                if result.stdout:
                    lines = result.stdout.strip().split("\n")
                    output += "\n## Vitest Coverage (external)\n\n```\n" + "\n".join(lines[-20:]) + "\n```\n"
                    ext_tool_used = True
            except Exception:
                pass

        py_indicator = (root / "pyproject.toml").exists() or (root / "setup.py").exists() or (root / "requirements.txt").exists()
        if py_indicator and not ext_tool_used:
            try:
                result = subprocess.run([sys.executable, "-m", "pytest", "--co", "--quiet"],
                                       cwd=str(root), capture_output=True, text=True, timeout=30)
                if result.stdout and "test" in result.stdout.lower():
                    lines = result.stdout.strip().split("\n")
                    output += "\n## pytest (external)\n\n```\n" + "\n".join(lines[-15:]) + "\n```\n"
                    ext_tool_used = True
            except Exception:
                pass

        if not ext_tool_used and (root / "package.json").exists() or py_indicator:
            output += f"\n> ℹ️ {t('External coverage tool not available. Analysis based on file presence.')}\n"

        try_crow_ingest(json.dumps({"coverage_ratio": ratio, "source": total_source, "tests": total_tests, "untested": len(untested_sources)}), register="context")
        output += _markdown_footer()
        return output
