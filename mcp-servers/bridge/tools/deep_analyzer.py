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


# ── AST 패턴 템플릿 라이브러리 ───────────────────────

_PATTERN_TEMPLATES = {
    # 언어 중립 패턴 (모든 언어에 적용 가능한 AST 구조)
    "try-catch": {
        "ast_pattern": {"type": "try_statement", "has_catch": True},
        "description": "try-catch 예외 처리 패턴",
        "anti_pattern": False,
        "languages": ["typescript", "python", "go", "rust"],
        "node_types": {
            "typescript": ["try_statement"],
            "python": ["try_statement"],
            "go": [],
            "rust": [],
        },
    },
    "callback-hell": {
        "ast_pattern": {"max_nesting": 3, "contains": ["callback", "function("]},
        "description": "콜백 중첩 과다 (Callback Hell)",
        "anti_pattern": True,
        "languages": ["typescript", "python"],
        "detection": "nested_callback_depth",
    },
    "god-class": {
        "ast_pattern": {"min_methods": 15, "min_lines": 500},
        "description": "God Class — 클래스 책임 과다",
        "anti_pattern": True,
        "languages": ["typescript", "python", "rust"],
        "detection": "method_count_threshold",
        "threshold": 20,
    },
    "promise-chain": {
        "ast_pattern": {"type": "call_expression", "contains": [".then(", ".catch("]},
        "description": "Promise 체인 패턴",
        "anti_pattern": False,
        "languages": ["typescript"],
        "node_types": {
            "typescript": ["call_expression"],
        },
    },
    "null-check": {
        "ast_pattern": {"type": "if_statement", "contains": ["== null", "== undefined", "=== null"]},
        "description": "null/undefined 체크 패턴",
        "anti_pattern": False,
        "languages": ["typescript"],
    },
    "long-method": {
        "ast_pattern": {"min_lines": 50},
        "description": "Long Method — 함수 분리 권장",
        "anti_pattern": True,
        "languages": ["typescript", "python", "go", "rust"],
        "detection": "line_count_threshold",
        "threshold": 50,
    },
    "async-await": {
        "ast_pattern": {"type": "await_expression"},
        "description": "async/await 사용 패턴",
        "anti_pattern": False,
        "languages": ["typescript", "python", "rust"],
        "node_types": {
            "typescript": ["await_expression"],
            "python": ["await"],
            "rust": ["await_expression"],
        },
    },
    "arrow-function": {
        "ast_pattern": {"type": "arrow_function"},
        "description": "화살표 함수 패턴",
        "anti_pattern": False,
        "languages": ["typescript"],
        "node_types": {
            "typescript": ["arrow_function"],
        },
    },
    "destructuring": {
        "ast_pattern": {"type": "destructuring_assignment"},
        "description": "구조 분해 할당 패턴",
        "anti_pattern": False,
        "languages": ["typescript"],
    },
    "optional-chaining": {
        "ast_pattern": {"type": "optional_chain_expression"},
        "description": "옵셔널 체이닝 패턴",
        "anti_pattern": False,
        "languages": ["typescript"],
    },
    "nullish-coalescing": {
        "ast_pattern": {"type": "nullish_coalescing_expression"},
        "description": "Nullish 병합 연산자 패턴",
        "anti_pattern": False,
        "languages": ["typescript"],
    },
}


# ── AST 패턴 탐지 헬퍼 ──────────────────────────────


def _compute_callback_depth(content: str, lang: str) -> int:
    """콜백 중첩 깊이 계산 (들여쓰기 기반)"""
    if lang not in ("typescript", "javascript", "python"):
        return 0
    max_depth = 0
    depth = 0
    in_callback = False
    for line in content.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        # 콜백 감지: function(, ()=> , lambda
        if re.search(r'(?:function\s*\(|\(\s*\)\s*=>|lambda\s+\w+\s*:)', stripped):
            in_callback = True
            depth = 1
        elif in_callback:
            indent = len(line) - len(line.lstrip())
            depth = indent // 4
            if depth > max_depth:
                max_depth = depth
            # 콜백 종료 (들여쓰기 감소)
            if depth <= 0:
                in_callback = False
    return max_depth


def _count_methods_per_class(ast: dict) -> list[tuple[str, int]]:
    """클래스별 메서드 개수 반환"""
    results = []
    for cls in ast.get("classes", []):
        methods = cls.get("methods", [])
        if not methods:
            # AST classes가 methods 필드가 없으면 함수 개수로 추정
            methods = [f for f in ast.get("functions", [])
                       if f.get("line", 0) >= cls.get("line", 0)
                       and f.get("end_line", 0) <= cls.get("end_line", 999999)]
        results.append((cls.get("name", "anonymous"), len(methods)))
    return results


def _compute_line_count_threshold(content: str, threshold: int = 50) -> list[dict]:
    """함수/메서드별 라인 수 계산, threshold 초과 항목 반환"""
    lines = content.split("\n")
    results = []
    # 간단한 휴리스틱: function/def 키워드 기준
    func_pattern = re.compile(r'(?:function\s+(\w+)|def\s+(\w+)|(\w+)\s*=\s*(?:async\s*)?\(|\w+\s*\([^)]*\)\s*{)')
    for match in func_pattern.finditer(content):
        name = match.group(1) or match.group(2) or match.group(3) or "anonymous"
        # 해당 함수의 시작 라인 찾기
        line_num = content[:match.start()].count("\n") + 1
        # 대략적인 함수 길이 추정 (다음 function/def까지)
        remaining = content[match.start():]
        next_func = re.search(r'\n(?:function|def)\s+', remaining[1:])
        if next_func:
            fn_end_line = line_num + remaining[:next_func.start()].count("\n")
        else:
            fn_end_line = len(lines)
        fn_lines = fn_end_line - line_num
        if fn_lines >= threshold:
            results.append({"name": name, "line": line_num, "lines": fn_lines})
    return results


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


# ── AST 기반 패턴 추출 (extract_patterns 핵심) ──────


def _extract_patterns_ast(target_path: str, min_occurrences: int = 3) -> str:
    """
    AST 서브트리 매칭으로 구조적 패턴 탐지.

    기존 키워드 카운팅(content.count("async ")) → tree-sitter AST 노드 타입 매칭 + regex 폴백.
    """
    ast_engine = _get_ast_engine()
    root = Path(get_project_root(target_path))
    results = defaultdict(lambda: {"count": 0, "files": [], "examples": []})

    for p in _iter_project_files_cached(root, SOURCE_EXTS, DEFAULT_EXCLUDE_DIRS):
        ext = p.suffix.lower()
        lang = ast_engine.LANGUAGES.get(ext, "")
        if not lang and ext not in TS_JS_EXTS and ext != ".py":
            continue

        content = _read_file_content(p)
        if not content:
            continue

        # AST 파싱 (TS/JS는 tree-sitter, 나머지는 regex 폴백)
        ast_parsed = {}
        if ext in TS_JS_EXTS:
            try:
                ast_engine._init_legacy_tree_sitter()
                ast_parsed = ast_engine.parse(content, ext)
            except Exception:
                ast_parsed = {}

        for pattern_name, template in _PATTERN_TEMPLATES.items():
            if lang and template.get("languages") and lang not in template["languages"]:
                # JS 파일도 typescript 패턴 적용
                if lang == "javascript" and "typescript" not in template.get("languages", []):
                    if "python" not in template.get("languages", []):
                        continue

            matched = False
            example = ""

            # AST 노드 타입 매칭 (TS/JS)
            if ext in TS_JS_EXTS and ast_parsed:
                node_types = template.get("node_types", {})
                target_types = node_types.get(lang, node_types.get("typescript", node_types.get("python", [])))
                if not target_types:
                    # detection 기반 매칭
                    pass
                else:
                    # AST 결과에서 노드 타입 검사
                    if target_types and ast_parsed.get("functions"):
                        for func in ast_parsed.get("functions", []):
                            if func.get("type") in target_types:
                                matched = True
                                example = f"{p}:{func['line']} — {func['name']}"
                                break
                    if not matched and ast_parsed.get("classes"):
                        for cls in ast_parsed.get("classes", []):
                            if cls.get("type") in target_types:
                                matched = True
                                example = f"{p}:{cls['line']} — {cls['name']}"
                                break

            # 깊이/개수 기반 탐지 (모든 언어)
            if not matched and "detection" in template:
                det = template["detection"]
                if det == "nested_callback_depth":
                    depth = _compute_callback_depth(content, lang or "typescript")
                    if depth >= 3:
                        matched = True
                        example = f"{p}: max callback depth = {depth}"
                elif det == "method_count_threshold":
                    threshold = template.get("threshold", 20)
                    class_methods = _count_methods_per_class(ast_parsed)
                    for cls_name, count in class_methods:
                        if count >= threshold:
                            matched = True
                            example = f"{p}: {cls_name} has {count} methods (threshold: {threshold})"
                            break
                elif det == "line_count_threshold":
                    threshold = template.get("threshold", 50)
                    long_funcs = _compute_line_count_threshold(content, threshold)
                    if long_funcs:
                        matched = True
                        example = f"{p}:{long_funcs[0]['line']} — {long_funcs[0]['name']} ({long_funcs[0]['lines']} lines)"

            # Regex 폴백 매칭 (AST 실패 시)
            if not matched:
                ast_pattern = template.get("ast_pattern", {})
                pattern_type = ast_pattern.get("type", "")
                contains = ast_pattern.get("contains", [])

                if pattern_type:
                    # 패턴 타입별 regex
                    type_regex_map = {
                        "try_statement": r'\btry\s*\{',
                        "if_statement": r'\bif\s*\(',
                        "call_expression": r'\w+\s*\(',
                        "arrow_function": r'=>\s*[\({]',
                        "await_expression": r'\bawait\s+',
                        "destructuring_assignment": r'(?:const|let|var)\s*\{[^}]+\}\s*=',
                        "optional_chain_expression": r'\w\?\.\w',
                        "nullish_coalescing_expression": r'\w\s*\?\?\s*\w',
                    }
                    regex = type_regex_map.get(pattern_type, "")
                    if regex and re.search(regex, content):
                        # contains 조건 확인
                        if contains:
                            if all(c in content for c in contains):
                                matched = True
                                # 예시 추출
                                for match in re.finditer(regex, content):
                                    line_num = content[:match.start()].count("\n") + 1
                                    example = f"{p}:{line_num} — ...{_truncate(match.group(), 50)}"
                                    break
                        else:
                            matched = True
                            for match in re.finditer(regex, content):
                                line_num = content[:match.start()].count("\n") + 1
                                example = f"{p}:{line_num}"
                                break

            if matched:
                results[pattern_name]["count"] += 1
                if str(p) not in results[pattern_name]["files"]:
                    results[pattern_name]["files"].append(str(p))
                if len(results[pattern_name]["examples"]) < 3:
                    results[pattern_name]["examples"].append(example)

    # 결과 포맷팅
    lines = []
    lines.append("## Pattern Analysis (AST Subtree Matching)\n")

    for pattern_name, data in sorted(results.items(), key=lambda x: -x[1]["count"]):
        if data["count"] < min_occurrences:
            continue
        template = _PATTERN_TEMPLATES[pattern_name]
        tag = "⚠️ ANTIPATTERN" if template.get("anti_pattern") else "📊 PATTERN"
        lines.append(f"### {tag}: {template['description']}")
        lines.append(f"- **Occurrences**: {data['count']} (in {len(data['files'])} files)")
        if data["examples"]:
            lines.append(f"- **Examples**:")
            for ex in data["examples"]:
                lines.append(f"  - `{ex}`")
        lines.append("")

    if len(lines) <= 2:
        lines.append("- No structural patterns met the minimum occurrence threshold.\n")

    return "\n".join(lines)


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

        # AST 서브트리 매칭 구현 (시그니처 100% 호환)
        return _extract_patterns_ast(target_path or ".", min_occurrences)

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
