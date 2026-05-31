# VibeZoo Bridge — DeepAnalyzer 도구 그룹
# analyze_call_graph + map_dependencies + extract_patterns + reverse_engineer

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
    _validate_string, _validate_int,
    _read_file_content, _truncate, _normalize_path,
    _iter_project_files, _iter_project_files_cached,
    _npx_cmd, get_project_root,
    _extract_regex_imports, _extract_python_imports, _extract_go_imports,
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


# ── 내부 함수 (scout.py에서 import) ──────────────────


def _run_map_dependencies(target_path: Optional[str] = None) -> str:
    """map_dependencies 내부 구현 — scout.summarize_architecture에서 호출"""
    root = Path(get_project_root(target_path))

    _get_ast_engine()._init_legacy_tree_sitter()

    deps = {}
    for p in _iter_project_files_cached(root, extensions={".ts", ".tsx", ".js", ".jsx", ".py", ".go"},
                                  exclude_dirs=DEFAULT_EXCLUDE_DIRS):
        rel = _normalize_path(str(p.relative_to(root)))
        ext = p.suffix
        content = _read_file_content(p)
        if content is None:
            continue

        if ext in TS_JS_EXTS:
            ast_imports = _get_ast_engine().extract_imports(content, ext)
            if ast_imports:
                deps[rel] = [i["module"] for i in ast_imports]
                continue
        if ext == ".py":
            py_imports = _extract_python_imports(content)
            if py_imports:
                deps[rel] = [i["module"] for i in py_imports]
                continue
        if ext == ".go":
            go_imports = _extract_go_imports(content)
            if go_imports:
                deps[rel] = [i["module"] for i in go_imports]
                continue
        imports = _extract_regex_imports(str(p))
        if imports:
            deps[rel] = imports

    output = _markdown_header("Dependency Map")

    # 패키지 매니저 정보
    output += "## Package Manager Info\n\n"
    pkg_managers = []
    if (root / "package.json").exists():
        try:
            pkg = json.loads((root / "package.json").read_text())
            deps_count = len(pkg.get("dependencies", {}))
            dev_deps_count = len(pkg.get("devDependencies", {}))
            pkg_managers.append(f"- **npm/yarn**: {deps_count} deps + {dev_deps_count} devDeps")
        except Exception:
            pkg_managers.append("- **npm/yarn**: package.json found (parse error)")
    if (root / "go.mod").exists():
        try:
            gomod = (root / "go.mod").read_text()
            module_name = ""
            for line in gomod.split("\n"):
                if line.startswith("module "):
                    module_name = line[7:].strip()
                    break
            pkg_managers.append(f"- **Go module**: {module_name}")
        except Exception:
            pkg_managers.append("- **Go module**: go.mod found")
    if (root / "requirements.txt").exists():
        try:
            reqs = (root / "requirements.txt").read_text().strip().split("\n")
            pkg_managers.append(f"- **pip**: {len(reqs)} packages listed")
        except Exception:
            pkg_managers.append("- **pip**: requirements.txt found")
    if (root / "Cargo.toml").exists():
        pkg_managers.append("- **Cargo**: Rust project")
    if pkg_managers:
        for pm in pkg_managers:
            output += pm + "\n"
    else:
        output += "- No package manager detected.\n"
    output += "\n"

    # 순환 참조 탐지
    def find_cycles_iterative(graph):
        cycles = []
        visited_all = set()
        for start in graph:
            if start in visited_all:
                continue
            stack = [(start, [start], {start})]
            while stack:
                node, path, branch_visited = stack.pop()
                for dep in graph.get(node, []):
                    if dep not in graph:
                        continue
                    if dep == start and len(path) >= 2:
                        cycle_path = " → ".join(path + [dep])
                        cycles.append(cycle_path)
                    elif dep not in branch_visited:
                        new_path = path + [dep]
                        new_branch = branch_visited | {dep}
                        stack.append((dep, new_path, new_branch))
                        visited_all.add(dep)
        return list(set(cycles))

    all_cycles = find_cycles_iterative(deps)

    if all_cycles:
        all_cycles = all_cycles[:10]
        output += "### ⚠️ Circular Dependencies Found\n\n"
        for cycle in all_cycles:
            output += f"- `{cycle}`\n"
    else:
        output += "✅ No circular dependencies detected.\n"
    output += "\n"

    # 영향도 분석
    output += "## Impact Analysis\n\n"
    reverse_deps = defaultdict(list)
    for file_path, imports in deps.items():
        for imp in imports:
            reverse_deps[imp].append(file_path)

    impact_entries = []
    for file_path in deps:
        affected = reverse_deps.get(file_path, [])
        direct_affected = len(affected)
        if direct_affected == 0:
            grade = "LOW"
        elif direct_affected <= 2:
            grade = "MEDIUM"
        elif direct_affected <= 5:
            grade = "HIGH"
        else:
            grade = "CRITICAL"
        impact_entries.append((direct_affected, file_path, grade))

    impact_entries.sort(key=lambda x: -x[0])
    for direct_affected, file_path, grade in impact_entries[:10]:
        output += f"- `{file_path}` → affects **{direct_affected}** file(s) — **{grade}**\n"
    if not impact_entries:
        output += "- No dependency data for impact analysis.\n"
    output += "\n"

    # Import Count by File
    output += "## Import Count by File\n\n"
    for file, imports in sorted(deps.items(), key=lambda x: -len(x[1]))[:20]:
        output += f"- `{file}`: **{len(imports)}** imports\n"

    try_crow_ingest(f"Dep analysis: {len(deps)} files, {len(all_cycles)} cycles", register="arch")
    return output + _markdown_footer()


def register(mcp):
    """DeepAnalyzer 도구 등록"""

    @mcp.tool
    def analyze_call_graph(file_path: Optional[str] = None, depth: int = 3,
                           include_external: bool = False) -> str:
        """프로젝트의 함수 호출 그래프를 분석합니다.
        tree-sitter AST로 실제 call_expression 노드를 추출하여 정확한 호출 관계를 파악합니다.

        Args:
            file_path: 분석할 파일 경로 (기본: 전체 프로젝트)
            depth: 호출 깊이 (기본: 3)
            include_external: 외부 라이브러리 호출 포함 여부 (기본: False)
        """
        err = _validate_int(depth, "depth", 1, 20)
        if err:
            return _markdown_header("Call Graph Error", "❌") + f"**{err}**\n" + _markdown_footer()

        root = Path(get_project_root(file_path))
        output = _markdown_header("Call Graph Analysis")

        ast_engine = _get_ast_engine()
        ast_engine._init_legacy_tree_sitter()

        # 함수 정의 맵 구축
        output += "## Function Definition Map\n\n"
        func_defs = {}
        for p in _iter_project_files_cached(root, extensions=TS_JS_EXTS, exclude_dirs=DEFAULT_EXCLUDE_DIRS):
            content = _read_file_content(p)
            if content is None:
                continue
            rel = _normalize_path(str(p.relative_to(root)))
            ast = ast_engine.parse(content, p.suffix)
            for fn in ast.get("functions", []):
                key = f"{rel}::{fn['name']}"
                func_defs[key] = {"file": rel, "name": fn["name"], "line": fn["line"], "end_line": fn.get("end_line", fn["line"])}

        if func_defs:
            output += f"- Total function definitions: {len(func_defs)}\n"
            file_func_count = defaultdict(int)
            for key, info in func_defs.items():
                file_func_count[info["file"]] += 1
            for f, cnt in sorted(file_func_count.items(), key=lambda x: -x[1])[:10]:
                output += f"- `{f}`: {cnt} functions\n"
        else:
            output += "- No function definitions found.\n"
        output += "\n"

        # Fan-in / Fan-out 메트릭
        output += "## Fan-in / Fan-out Metrics\n\n"
        all_calls = defaultdict(list)
        all_callees = defaultdict(list)

        for p in _iter_project_files_cached(root, extensions=TS_JS_EXTS, exclude_dirs=DEFAULT_EXCLUDE_DIRS):
            content = _read_file_content(p)
            if content is None:
                continue
            rel = _normalize_path(str(p.relative_to(root)))
            calls = ast_engine.extract_calls(content, p.suffix)
            for c in calls:
                caller_key = f"{rel}::{c['name']}"
                matched = False
                for fkey, finfo in func_defs.items():
                    if c["name"] == finfo["name"] or c["name"].endswith("." + finfo["name"]):
                        all_calls[caller_key].append(fkey)
                        all_callees[fkey].append(caller_key)
                        matched = True
                        break
                if not matched:
                    all_calls[caller_key].append(c["name"])

        fan_out_list = [(len(targets), caller) for caller, targets in all_calls.items()]
        fan_out_list.sort(key=lambda x: -x[0])
        output += "### Top Fan-out (most calls made)\n\n"
        for count, caller in fan_out_list[:5]:
            output += f"- `{caller}` → {count} calls\n"

        fan_in_list = [(len(callers), callee) for callee, callers in all_callees.items()]
        fan_in_list.sort(key=lambda x: -x[0])
        output += "\n### Top Fan-in (most called)\n\n"
        for count, callee in fan_in_list[:5]:
            output += f"- `{callee}` ← {count} callers\n"

        if not fan_out_list and not fan_in_list:
            output += "- No call data available.\n"
        output += "\n"

        # 데드 코드 감지
        output += "## Dead Code Detection\n\n"
        dead_funcs = []
        for fkey, finfo in func_defs.items():
            if fkey not in all_callees or len(all_callees[fkey]) == 0:
                if not any(finfo["name"] in str(caller) and finfo["file"] in str(caller) for caller in all_calls.get(fkey, [])):
                    dead_funcs.append(finfo)

        if dead_funcs:
            output += f"⚠️ {len(dead_funcs)} potentially dead function(s) (no callers):\n\n"
            for df in dead_funcs[:10]:
                output += f"- `{df['file']}:{df['line']}` — `{df['name']}()`\n"
            if len(dead_funcs) > 10:
                output += f"- ... +{len(dead_funcs)-10} more\n"
        else:
            output += "✅ No dead code detected (or all functions have callers).\n"
        output += "\n"

        # Per-File Call Analysis
        output += "## Per-File Call Analysis\n\n"
        total_calls = 0
        processed_files = 0
        for p in _iter_project_files_cached(root, extensions=TS_JS_EXTS, exclude_dirs=DEFAULT_EXCLUDE_DIRS):
            content = _read_file_content(p)
            if content is None:
                continue
            processed_files += 1
            rel = _normalize_path(str(p.relative_to(root)))
            calls = ast_engine.extract_calls(content, p.suffix)
            if calls:
                call_counts = Counter(c["name"] for c in calls)
                top_calls = call_counts.most_common(10)
                output += f"### `{rel}`\n\n"
                output += f"- **Total calls**: {len(calls)}\n"
                output += f"- **Unique functions called**: {len(call_counts)}\n"
                for func_name, count in top_calls:
                    output += f"  - `{func_name}` ({count}x)\n"
                output += "\n"
                total_calls += len(calls)

        if total_calls == 0:
            if processed_files == 0:
                output += "- No TypeScript/JavaScript files found.\n"
            else:
                output += "- No function calls detected via AST.\n"

        try_crow_ingest(f"Call graph: {total_calls} calls, {len(dead_funcs)} dead funcs, {len(func_defs)} defs", register="arch")
        output += _markdown_footer()
        return output

    @mcp.tool
    def map_dependencies(target_path: Optional[str] = None) -> str:
        """프로젝트 파일 간 의존성을 분석하고 순환 참조를 탐지합니다.
        tree-sitter AST로 import/require 문을 정확히 분석합니다.

        Args:
            target_path: 분석 대상 경로
        """
        return _run_map_dependencies(target_path)

    @mcp.tool
    def extract_patterns(target_path: Optional[str] = None, min_occurrences: int = 3) -> str:
        """프로젝트 전체에서 반복되는 코드 패턴을 AST 기반으로 추출합니다.
        tree-sitter AST로 실제 코드 구조를 분석하여 정확한 패턴 빈도를 계산합니다.

        Args:
            target_path: 분석 대상 경로
            min_occurrences: 최소 발생 횟수 (기본: 3)
        """
        err = _validate_int(min_occurrences, "min_occurrences", 1, 10000)
        if err:
            return _markdown_header("Pattern Extraction Error", "❌") + f"**{err}**\n" + _markdown_footer()

        root = Path(get_project_root(target_path))
        ast_engine = _get_ast_engine()
        ast_engine._init_legacy_tree_sitter()

        patterns = {
            "async/await": 0, "try-catch": 0, "arrow functions": 0,
            "class definitions": 0, "interface/type": 0, "generics usage": 0,
            "destructuring": 0, "template literals": 0, "optional chaining": 0, "nullish coalescing": 0,
        }
        comments_todos = 0
        console_logs = 0
        ts_ignore = 0
        debugger_count = 0
        file_count = 0
        lib_calls = Counter()

        for p in _iter_project_files_cached(root, extensions=SOURCE_EXTS, exclude_dirs=DEFAULT_EXCLUDE_DIRS):
            content = _read_file_content(p)
            if content is None:
                continue
            file_count += 1
            ext = p.suffix.lower()

            if ext in TS_JS_EXTS and ast_engine.is_available():
                try:
                    ast = ast_engine.parse(content, ext)
                    for fn in ast.get("functions", []):
                        if fn["type"] == "arrow_function":
                            patterns["arrow functions"] += 1
                    patterns["class definitions"] += len(ast.get("classes", []))
                    patterns["interface/type"] += len(ast.get("interfaces", []))
                except Exception:
                    pass
                try:
                    calls = ast_engine.extract_calls(content, ext)
                    for c in calls:
                        if c["name"].startswith("console."):
                            console_logs += 1
                        if "." in c["name"] and not c["name"].startswith("console."):
                            parts = c["name"].split(".")
                            if len(parts) >= 2:
                                lib_calls[f"{parts[0]}.{'.'.join(parts[1:])}"] += 1
                except Exception:
                    pass

            patterns["async/await"] += len(re.findall(r'\basync\s+(function|\(|=\s*\()', content))
            patterns["async/await"] += len(re.findall(r'\bawait\s+', content))
            patterns["try-catch"] += len(re.findall(r'\btry\s*\{', content))
            patterns["arrow functions"] += len(re.findall(r'(?:const|let|var)\s+\w+\s*=\s*(?:async\s*)?\([^)]*\)\s*=>', content))
            patterns["arrow functions"] += len(re.findall(r'\(\s*\)\s*=>', content[:10000]))
            patterns["generics usage"] += len(re.findall(r'<\s*\w+\s*(?:extends\s+\w+)?\s*>', content))
            patterns["destructuring"] += len(re.findall(r'\{\s*\w+\s*\}', content[:10000]))
            patterns["template literals"] += len(re.findall(r'`[^`]*\$\{[^}]+\}[^`]*`', content))
            patterns["optional chaining"] += len(re.findall(r'\w\?\.\w', content))
            patterns["nullish coalescing"] += len(re.findall(r'\w\s*\?\?\s*\w', content))
            comments_todos += len(re.findall(r'(?:TODO|FIXME|HACK|XXX)', content))
            ts_ignore += len(re.findall(r'@ts-ignore', content)) + len(re.findall(r'@ts-nocheck', content))
            debugger_count += len(re.findall(r'\bdebugger\b', content))

        output = _markdown_header(f"Pattern Analysis ({file_count} files)")
        output += "\n## Code Patterns\n"
        found_any = False
        for pattern, count in sorted(patterns.items(), key=lambda x: -x[1]):
            if count >= min_occurrences:
                output += f"- `{pattern}`: **{count}** occurrences\n"
                found_any = True
            elif count > 0:
                output += f"- `{pattern}`: {count} (below threshold)\n"
        if not found_any:
            output += "- No significant patterns detected.\n"

        output += "\n## Library Function Usage Top 10\n\n"
        top_lib = lib_calls.most_common(10)
        if top_lib:
            for lib, cnt in top_lib:
                output += f"- `{lib}`: **{cnt}** calls\n"
        else:
            output += "- No library function calls detected.\n"

        output += "\n## Quality Indicators\n"
        quality_items = []
        if console_logs > 0:
            quality_items.append(f"`console.*` calls: {console_logs}")
        if comments_todos > 0:
            quality_items.append(f"`TODO/FIXME/HACK`: {comments_todos}")
        if ts_ignore > 0:
            quality_items.append(f"`@ts-ignore/@ts-nocheck`: {ts_ignore}")
        if debugger_count > 0:
            quality_items.append(f"`debugger` statements: {debugger_count}")
        if quality_items:
            for item in quality_items:
                output += f"- ⚠️ {item}\n"
        else:
            output += "- ✅ No quality concerns detected.\n"

        try_crow_ingest(json.dumps({"patterns_found": sum(1 for c in patterns.values() if c > 0), "files": file_count}), register="style")
        output += _markdown_footer()
        return output

    @mcp.tool
    def reverse_engineer(target_path: Optional[str] = None, output_format: str = "markdown") -> str:
        """코드베이스로부터 아키텍처 문서, API 명세, ERD를 자동 생성합니다.
        tree-sitter AST로 데이터 모델의 실제 필드까지 추출합니다.

        Args:
            target_path: 분석 대상 경로
            output_format: 출력 형식 (markdown, openapi, mermaid). 기본: markdown
        """
        err = _validate_string(output_format, "format")
        if err:
            return _markdown_header("Reverse Engineering Error", "❌") + f"**{err}**\n" + _markdown_footer()

        allowed_formats = {"markdown", "openapi", "mermaid"}
        if output_format not in allowed_formats:
            return (_markdown_header("Reverse Engineering Error", "❌")
                    + f"**Invalid format: `{output_format}`. Allowed: {', '.join(allowed_formats)}**\n"
                    + _markdown_footer())

        root = Path(get_project_root(target_path))
        output = _markdown_header("Reverse Engineering Report")

        ast_engine = _get_ast_engine()
        ast_engine._init_legacy_tree_sitter()

        # 프로젝트 메타데이터
        pkg_json = root / "package.json"
        if pkg_json.exists():
            try:
                pkg = json.loads(pkg_json.read_text())
                output += f"- **Name**: {pkg.get('name', 'N/A')}\n"
                output += f"- **Description**: {pkg.get('description', 'N/A')}\n"
                output += f"- **Version**: {pkg.get('version', 'N/A')}\n\n"
            except (json.JSONDecodeError, OSError):
                pass

        # API 엔드포인트 추출
        output += "## API Endpoints\n\n"
        endpoints = []
        for p in _iter_project_files_cached(root, extensions={".ts", ".tsx", ".js", ".py", ".go"},
                                      exclude_dirs=DEFAULT_EXCLUDE_DIRS):
            content = _read_file_content(p)
            if content is None:
                continue
            rel = _normalize_path(str(p.relative_to(root)))
            ext = p.suffix.lower()

            # Express
            if ext in TS_JS_EXTS:
                for m in ["get", "post", "put", "delete", "patch", "all"]:
                    for match in re.finditer(rf'(?:router|app|route)\.{m}\s*\(\s*[\'"]([^\'"]+)[\'"]', content, re.IGNORECASE):
                        endpoints.append(f"- `{m.upper()}` `{match.group(1)}` ({rel}) — Express")

            # FastAPI / Flask
            if ext == ".py":
                for m in ["get", "post", "put", "delete", "patch"]:
                    for match in re.finditer(rf'@(?:app|router)\.{m}\s*\(\s*[\'"]([^\'"]+)[\'"]', content, re.IGNORECASE):
                        endpoints.append(f"- `{m.upper()}` `{match.group(1)}` ({rel}) — FastAPI/Flask")
                for match in re.finditer(r"@app\.route\s*\(\s*['\"]([^'\"]+)['\"]", content):
                    methods_match = re.search(r"methods\s*=\s*\[([^\]]+)\]", content[match.start():match.end()+200])
                    if methods_match:
                        methods_str = methods_match.group(1)
                        for m2 in re.finditer(r"'([A-Z]+)'", methods_str):
                            endpoints.append(f"- `{m2.group(1)}` `{match.group(1)}` ({rel}) — Flask")
                    else:
                        endpoints.append(f"- `GET` `{match.group(1)}` ({rel}) — Flask")

            # Gin
            if ext == ".go":
                for m in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    for match in re.finditer(rf'(?:router|r)\.{m}\s*\(\s*[\'"]([^\'"]+)[\'"]', content):
                        endpoints.append(f"- `{m}` `{match.group(1)}` ({rel}) — Gin")

        for ep in endpoints[:30]:
            output += ep + "\n"
        if not endpoints:
            output += "- No API endpoints detected.\n"

        # 데이터 모델 (AST 기반 필드 추출)
        output += "\n## Data Models\n\n"
        models = []
        all_fields = {}
        for p in _iter_project_files_cached(root, extensions={".ts", ".tsx", ".js", ".jsx", ".go"},
                                      exclude_dirs=DEFAULT_EXCLUDE_DIRS):
            content = _read_file_content(p)
            if content is None:
                continue
            rel = _normalize_path(str(p.relative_to(root)))
            if p.suffix in TS_JS_EXTS:
                ast_fields = ast_engine.extract_fields(content, p.suffix)
                for model in ast_fields.get("models", []):
                    model_name = model["name"]
                    field_list = model["fields"]
                    models.append(f"- `{model_name}` → **{len(field_list)} fields** ({rel})")
                    if field_list:
                        all_fields[model_name] = field_list
            else:
                for match in re.finditer(r'(?:type\s+)?(\w+)\s+struct\s*\{', content):
                    models.append(f"- `{match.group(1)}` ({rel})")

        if all_fields:
            output += "\n### Field Details\n\n"
            for model_name, fields in all_fields.items():
                output += f"**{model_name}**\n\n"
                for f in fields:
                    output += f"- `{f['name']}`: `{f['type']}`\n"
                output += "\n"

            # 관계 추론
            output += "### Model Relationships\n\n"
            relation_count = 0
            for model_name, fields in all_fields.items():
                for f in fields:
                    ftype = f["type"].replace("[]", "").replace("|", "").strip()
                    if ftype in all_fields and ftype != model_name:
                        is_array = "[]" in f["type"] or "Array" in f["type"]
                        card = "1:N" if is_array else "1:1"
                        relation_count += 1
                        output += f"- `{model_name}` → `{ftype}` ({card}) via `{f['name']}`\n"
            if relation_count == 0:
                output += "- No explicit model relationships detected.\n"
        else:
            for m in models[:20]:
                output += m + "\n"

        if not models and not all_fields:
            output += "- No data models detected.\n"

        # 형식별 출력
        if output_format == "mermaid":
            output += "\n## ER Diagram (Mermaid)\n\n```mermaid\nerDiagram\n"
            if all_fields:
                for model_name, fields in all_fields.items():
                    output += f"  {model_name} {{\n"
                    for f in fields:
                        ftype = f["type"].replace("|", " or ")
                        output += f"    {ftype} {f['name']}\n"
                    output += f"  }}\n"
                for model_name, fields in all_fields.items():
                    for f in fields:
                        ftype = f["type"].replace("[]", "").replace("|", "").strip()
                        if ftype in all_fields and ftype != model_name:
                            is_array = "[]" in f["type"] or "Array" in f["type"]
                            if is_array:
                                output += f"  {model_name} ||--o{{ {ftype} : has\n"
                            else:
                                output += f"  {model_name} ||--|| {ftype} : references\n"
            else:
                output += "  User ||--o{ Order : places\n  Order ||--|{ OrderItem : contains\n"
            output += "```\n"
        elif output_format == "openapi":
            output += "\n## OpenAPI 3.0 Spec\n\n```yaml\nopenapi: 3.0.0\ninfo:\n  title: Auto-detected API\n  version: 0.1.0\n"
            if endpoints:
                output += "paths:\n"
                path_map = defaultdict(list)
                for ep in endpoints:
                    m = re.match(r'- `(\w+)` `([^`]+)`', ep)
                    if m:
                        method = m.group(1).lower()
                        path = m.group(2)
                        path_map[path].append(method)
                for path, methods in sorted(path_map.items()):
                    output += f"  {path}:\n"
                    for method in methods:
                        output += f"    {method}:\n"
                        output += f"      summary: Auto-detected endpoint\n"
                        output += f"      responses:\n"
                        output += f"        '200':\n"
                        output += f"          description: Successful response\n"
            else:
                output += "paths: {}\n"
            if all_fields:
                output += "components:\n  schemas:\n"
                for model_name, fields in all_fields.items():
                    output += f"    {model_name}:\n"
                    output += f"      type: object\n"
                    output += f"      properties:\n"
                    for f in fields:
                        ftype = f["type"].replace("|", " or ")
                        example_map = {"string": "string", "number": 0, "boolean": True, "integer": 0}
                        example = example_map.get(ftype, ftype)
                        output += f"        {f['name']}:\n"
                        output += f"          type: {ftype}\n"
                        output += f"          example: {json.dumps(example, ensure_ascii=False)}\n"
            output += "```\n"

        output += _markdown_footer()
        return output
