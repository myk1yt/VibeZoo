# VibeZoo Bridge — Scout 도구 그룹
# search_codebase + find_references + summarize_architecture
# 점진적 스트리밍 지원 (summarize_architecture)

import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

# Pylance: ensure the extension root is in package search path
_EXT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _EXT_ROOT not in sys.path:
    sys.path.insert(0, _EXT_ROOT)
from typing import Optional

from bridge.config import (
    VERSION, CROW_URL, CROW_TIMEOUT,
    DEFAULT_EXCLUDE_DIRS, SOURCE_EXTS, TS_JS_EXTS,
)
from bridge.utils import (
    _markdown_header, _markdown_footer,
    _validate_string, _validate_int, _validate_file_path,
    _read_file_content, _truncate, _normalize_path,
    _iter_project_files, _iter_project_files_cached,
    _npx_cmd, _fuzzy_match, _auto_detect_query_type,
    _extract_regex_imports, _extract_python_imports, _extract_go_imports,
    get_project_root,
    truncate_to_tokens,
)
from bridge.crow_client import try_crow_ingest, try_crow_recall
from bridge.search_engine import SearchEngine
from bridge.result_ranker import ResultRanker
from bridge.embedding_client import EmbeddingClient, rank_by_embedding
from bridge.fuzzy_matcher import fuzzy_filter
from bridge.ast_engine import AstEngine
from bridge.ast_singleton import get_ast_engine as _get_ast_engine
from bridge.file_cache import FileCache
from bridge.tools._base import BaseTool
from bridge.i18n import t

# ── 싱글톤 인스턴스 ──────────────────────────────────

_file_cache = None


def _get_file_cache() -> FileCache:
    global _file_cache
    if _file_cache is None:
        _file_cache = FileCache()
    return _file_cache


def _get_search_engine(root: Path) -> SearchEngine:
    return SearchEngine(root)


# ── 모듈 레벨 구현 함수 (register() 외부) ──────────────


def _search_codebase_impl(query: str, file_patterns: Optional[str] = None,
                          max_results: int = 50, mode: str = "auto",
                          context_lines: int = 3,
                          target_path: Optional[str] = None) -> str:
    """search_codebase의 실제 구현 (모듈 레벨)"""
    err = _validate_string(query, "query")
    if err:
        return _markdown_header("Search Error", "❌") + f"**{err}**\n" + _markdown_footer()

    # max_results 상한: mode="exact"일 때 500까지 허용
    upper_limit = 500 if mode == "exact" else 200
    max_results = max(1, min(max_results, upper_limit))
    root = Path(get_project_root(target_path)) if target_path else Path(os.getcwd())

    # ── ripgrep 미설치 노트 ──
    rg_note = ""
    try:
        import subprocess
        rg_check = subprocess.run(["rg", "--version"], capture_output=True, timeout=2)
        if rg_check.returncode != 0:
            rg_note = "> ⚠️ **Note:** ripgrep not installed - falling back to os.walk (slower, extension-limited). Install with vibezoo_setup(target=full) for faster search.\n\n"
    except Exception:
        rg_note = "> ⚠️ **Note:** ripgrep not installed - falling back to os.walk (slower, extension-limited). Install with vibezoo_setup(target=full) for faster search.\n\n"

    if target_path and not Path(target_path).exists():
        rg_note += f"<!-- WARNING: target_path '{target_path}' not found, using current directory -->\n"

    # SearchEngine 사용 (ripgrep 우선)
    engine = _get_search_engine(root)
    # ── mode="fuzzy": broaden query then apply trigram fuzzy filter ──
    if mode == "fuzzy":
        # Strip regex metacharacters for a broader text search
        broadened_query = re.sub(r'[^\w\s]', ' ', query).strip()
        # Use longest alphanumeric token if broadened query is too short
        tokens = [t for t in broadened_query.split() if len(t) >= 2]
        if tokens:
            broadened_query = max(tokens, key=len)
        else:
            broadened_query = query
        search_results = engine.search(broadened_query, file_patterns, max_results * 2, "auto", context_lines)
        search_results = fuzzy_filter(query, search_results, threshold=0.35, max_results=max_results)
    else:
        search_results = engine.search(query, file_patterns, max_results, mode, context_lines)

    # ── mode="semantic": embedding-based reranking (BM25 fallback) ──
    semantic_note = ""
    if mode == "semantic" and search_results:
        embed_client = EmbeddingClient()
        if embed_client.is_available():
            query_vec = embed_client.embed([query])
            if query_vec and query_vec[0]:
                search_results = rank_by_embedding(
                    query_vec[0], search_results, embed_client.embed
                )[:max_results]
                semantic_note = "> 🧠 semantic: embedding-based ranking (rank_source=\"embedding\")\n\n"
            else:
                ranker = ResultRanker()
                search_results = ranker.rank(query, search_results, context_lines)[:max_results]
                semantic_note = "> ⚠️ semantic: embedding server returned empty, used BM25 keyword ranking\n\n"
        else:
            ranker = ResultRanker()
            search_results = ranker.rank(query, search_results, context_lines)[:max_results]
            semantic_note = "> ⚠️ semantic: embedding server unavailable, used BM25 keyword ranking\n\n"

    # AST 검색 (보완)
    ast_engine = _get_ast_engine()
    ast_engine._init_legacy_tree_sitter()

    # 파일 패턴 결정
    if file_patterns:
        patterns = [p.strip() for p in file_patterns.split(",") if p.strip()]
    else:
        query_lower = query.lower()
        if any(kw in query_lower for kw in ["def ", "import ", "pytest", "python"]):
            patterns = ["*.py"]
        elif any(kw in query_lower for kw in ["func ", "go ", "package ", "golang"]):
            patterns = ["*.go"]
        elif any(kw in query_lower for kw in ["fn ", "struct ", "impl ", "rust"]):
            patterns = ["*.rs"]
        else:
            patterns = ["*.ts", "*.tsx", "*.js", "*.jsx", "*.py"]

    ext_set = set()
    for pat in patterns:
        ext = os.path.splitext(pat)[1]
        if ext:
            ext_set.add(ext)

    # AST 검색 (심볼 검색 시)
    ast_results = []
    query_stripped = query.strip()
    is_single_symbol = bool(re.match(r'^[\w.]+$', query_stripped))
    is_ast_query = (
        mode == "ast"
        or is_single_symbol
        or any(keyword in query.lower() for keyword in [
            "function ", "class ", "interface ", "type ", "method ",
            "def ", "fn ", "func ", "struct ", "enum ", "trait ",
            "함수", "클래스", "인터페이스"
        ])
    )

    if is_ast_query and ast_engine.is_available():
        for pattern in patterns:
            try:
                for p in root.rglob(pattern.strip()):
                    if not p.is_file():
                        continue
                    rel = str(p.relative_to(root))
                    if any(part in rel for part in DEFAULT_EXCLUDE_DIRS):
                        continue
                    try:
                        content = p.read_text(encoding="utf-8", errors="ignore")
                    except Exception:
                        continue
                    ext = p.suffix.lower()
                    ast = ast_engine.parse(content, ext)
                    if not ast:
                        continue
                    # 함수/메서드 검색
                    for fn in ast.get("functions", []):
                        if query.lower() in fn["name"].lower():
                            ast_results.append(
                                f"`{_normalize_path(rel)}:{fn['line']}` — `{fn['type']} {fn['name']}()` (L{fn['line']}-{fn.get('end_line', fn['line'])})"
                            )
                    # 클래스/구조체 검색
                    for cls in ast.get("classes", []):
                        if query.lower() in cls["name"].lower():
                            cls_type = "class"
                            if ext in (".go", ".rs"):
                                cls_type = "struct" if ext == ".rs" else "type"
                            ast_results.append(
                                f"`{_normalize_path(rel)}:{cls['line']}` — `{cls_type} {cls['name']}`"
                            )
                    # 인터페이스/타입 검색 (TS/TSX)
                    if ext in (".ts", ".tsx"):
                        for iface in ast.get("interfaces", []):
                            if query.lower() in iface["name"].lower():
                                ast_results.append(
                                    f"`{_normalize_path(rel)}:{iface['line']}` — `{iface['type']} {iface['name']}`"
                                )
                    # Python: import_from_statement 검색
                    if ext == ".py":
                        py_imports = re.findall(r'from\s+(\S+)\s+import\s+(\S+)', content)
                        for module, name in py_imports:
                            if query.lower() in name.lower() or query.lower() in module.lower():
                                line_num = 0
                                for i, l in enumerate(content.split("\n"), 1):
                                    if f"from {module} import {name}" in l:
                                        line_num = i
                                        break
                                ast_results.append(
                                    f"`{_normalize_path(rel)}:{line_num}` — `from {module} import {name}`"
                                )
                    # Go: type_declaration 추가 검색
                    if ext == ".go":
                        go_types = re.findall(r'type\s+(\w+)\s+(struct|interface)\s*\{', content)
                        for tname, tkind in go_types:
                            if query.lower() in tname.lower():
                                line_num = 0
                                for i, l in enumerate(content.split("\n"), 1):
                                    if f"type {tname}" in l:
                                        line_num = i
                                        break
                                ast_results.append(
                                    f"`{_normalize_path(rel)}:{line_num}` — `type {tname} {tkind}`"
                                )
                    # Rust: struct_item 검색
                    if ext == ".rs":
                        rust_structs = re.findall(r'struct\s+(\w+)', content)
                        for sname in rust_structs:
                            if query.lower() in sname.lower():
                                line_num = 0
                                for i, l in enumerate(content.split("\n"), 1):
                                    if f"struct {sname}" in l:
                                        line_num = i
                                        break
                                ast_results.append(
                                    f"`{_normalize_path(rel)}:{line_num}` — `struct {sname}`"
                                )
            except (PermissionError, OSError):
                continue

    # 출력 구성
    output = _markdown_header(f'Search: "{query}"')
    output += rg_note
    output += semantic_note

    # AST 결과 우선
    if ast_results:
        output += f"AST matches: {len(ast_results)}. "
        unique_ast = list(dict.fromkeys(ast_results))[:max_results]
        output += "\n### Symbols\n"
        for r in unique_ast:
            output += f"- {r}\n"

    # SearchEngine 결과
    if search_results:
        output += f"Line matches: {len(search_results)} found, showing top {len(search_results)}.\n"
        output += "\n### Matches\n"
        for r in search_results[:max_results]:
            rel_path = _normalize_path(r.get("file", ""))
            line = r.get("line", 0)
            content = r.get("content", "")
            ctx_before = r.get("context_before", [])
            ctx_after = r.get("context_after", [])
            output += f"- `{rel_path}:{line}`\n"
            for bl in ctx_before[-1:]:
                output += f"  {str(bl).strip()[:100]}\n"
            output += f"  → **{content}**\n"
            for al in ctx_after[:1]:
                output += f"  {str(al).strip()[:100]}\n"
            output += "\n"

    if not ast_results and not search_results:
        output += "No matches.\n"

    try_crow_ingest(f"Search: {query} → {len(ast_results)} AST + {len(search_results)} line matches",
                   register="life_context")
    output += _markdown_footer()
    return output


def _find_references_impl(symbol: str, target_path: Optional[str] = None) -> str:
    """find_references의 실제 구현 (모듈 레벨)"""
    err = _validate_string(symbol, "symbol")
    if err:
        return _markdown_header("Find References Error", "❌") + f"**{err}**\n" + _markdown_footer()

    # SRF: Precompile a word-boundary regex so that searching for a short symbol
    # like "io" does NOT match substrings inside "action", "configuration", etc.
    # \b is Unicode-aware in Python 3 re, and re.escape() handles metacharacters.
    # Dotted access like "obj.symbol" is matched because \b asserts after ".".
    symbol_pattern = re.compile(r'\b' + re.escape(symbol) + r'\b')

    root = Path(get_project_root(target_path)) if target_path else Path(os.getcwd())
    definitions = []
    usages = []
    exclude = DEFAULT_EXCLUDE_DIRS

    ast_engine = _get_ast_engine()
    ast_engine._init_legacy_tree_sitter()

    ref_types = {"read": [], "write": [], "call": [], "type_ref": [], "import_ref": []}

    for p in _iter_project_files_cached(root, extensions=SOURCE_EXTS, exclude_dirs=exclude):
        content = _read_file_content(p)
        if content is None:
            continue
        rel = _normalize_path(str(p.relative_to(root)))
        ext = p.suffix.lower()
        file_lines = content.split("\n")

        # AST로 함수/클래스/구조체/인터페이스 정의 찾기 (멀티랭귀지)
        ast = ast_engine.parse(content, ext)
        if ast:
            # 모든 언어: 함수 정의
            for fn in ast.get("functions", []):
                if fn["name"] == symbol:
                    fn_type = fn.get("type", "function")
                    definitions.append({"file": rel, "line": fn["line"], "desc": f"`{fn_type} {fn['name']}()`", "type": "definition"})
            # 모든 언어: 클래스/구조체/인터페이스
            for cls in ast.get("classes", []):
                if cls["name"] == symbol:
                    cls_label = "class"
                    if ext in (".go", ".rs"):
                        cls_label = "struct" if ext == ".rs" else "type"
                    definitions.append({"file": rel, "line": cls["line"], "desc": f"`{cls_label} {cls['name']}`", "type": "definition"})
            # TS/JS: interfaces, type aliases
            for iface in ast.get("interfaces", []):
                if iface["name"] == symbol:
                    definitions.append({"file": rel, "line": iface["line"], "desc": f"`{iface.get('type', 'interface')} {iface['name']}`", "type": "definition"})
            # Rust: enums
            for enm in ast.get("enums", []):
                if enm["name"] == symbol:
                    definitions.append({"file": rel, "line": enm["line"], "desc": f"`enum {enm['name']}`", "type": "definition"})

        # 사용 위치 찾기 + 타입 분류
        # SRF: Use word-boundary regex instead of substring containment to avoid
        # false positives (e.g. "io" matching "action").
        for i, line in enumerate(file_lines, 1):
            if not symbol_pattern.search(line):
                continue
            is_def = any(d["file"] == rel and d["line"] == i for d in definitions)
            if is_def:
                continue
            stripped = line.strip()
            ref_type = "read"
            # SRF: All classifiers use the boundary regex for consistency.
            if f"import {symbol}" in stripped or f"from '{symbol}" in stripped or f'from "{symbol}"' in stripped:
                ref_type = "import_ref"
            elif symbol_pattern.search(stripped) and ("new " + symbol in stripped or "extends " + symbol in stripped or "implements " + symbol in stripped):
                ref_type = "type_ref"
            elif symbol_pattern.search(stripped) and (symbol + "(" in stripped):
                ref_type = "call"
            elif symbol_pattern.search(stripped) and ("= " + symbol in stripped or "=" + symbol in stripped):
                ref_type = "read"
            elif symbol_pattern.search(stripped) and ("let " + symbol in stripped or "const " + symbol in stripped or "var " + symbol in stripped):
                ref_type = "write"
            usages.append({"file": rel, "line": i, "text": stripped[:120], "type": ref_type})
            ref_types[ref_type].append(f"`{rel}:{i}`")

    output = _markdown_header(f'References: `{symbol}`')

    if definitions:
        output += f"## 📍 Definition ({len(definitions)})\n"
        for d in definitions:
            output += f"- `{d['file']}:{d['line']}` — {d['desc']}\n"
        output += "\n"

    if usages:
        output += f"## 🔗 References ({len(usages)})\n\n"
        output += "### By Reference Type\n\n"
        type_labels = {"call": "📞 Function Calls", "read": "📖 Read Access",
                      "write": "✏️ Write Access", "type_ref": "🔤 Type Reference",
                      "import_ref": "📦 Import Reference"}
        for t, label in type_labels.items():
            items = ref_types.get(t, [])
            if items:
                output += f"**{label}** ({len(items)})\n"
                for item in items[:8]:
                    output += f"- {item}\n"
                if len(items) > 8:
                    output += f"- ... +{len(items)-8} more\n"
                output += "\n"

        output += "### By File\n\n"
        by_file = defaultdict(list)
        for u in usages:
            by_file[u["file"]].append(u)
        for file_path, refs in sorted(by_file.items(), key=lambda x: -len(x[1]))[:10]:
            output += f"**`{file_path}`** ({len(refs)} refs)\n"
            for r in refs[:5]:
                output += f"- Line {r['line']}: [{r['type']}] `{r['text'][:80]}`\n"
            if len(refs) > 5:
                output += f"  ... +{len(refs)-5} more\n"
            output += "\n"

        # Call Chain
        output += "### Call Chain — Functions using this symbol\n\n"
        caller_functions = {}
        for u in usages:
            if u["type"] == "call":
                p = Path(root) / u["file"]
                if p.exists():
                    content2 = _read_file_content(p)
                    if content2:
                        ext2 = p.suffix.lower()
                        if ext2 in TS_JS_EXTS and ast_engine.is_available():
                            ast2 = ast_engine.parse(content2, ext2)
                            for fn in ast2.get("functions", []):
                                if fn["line"] <= u["line"] <= fn.get("end_line", fn["line"]):
                                    caller_key = f"{u['file']}::{fn['name']}"
                                    if caller_key not in caller_functions:
                                        caller_functions[caller_key] = {"file": u["file"], "function": fn["name"], "line": fn["line"], "call_lines": []}
                                    caller_functions[caller_key]["call_lines"].append(u["line"])
        if caller_functions:
            for ckey, cinfo in sorted(caller_functions.items(), key=lambda x: -len(x[1]["call_lines"]))[:10]:
                lines_str = ", ".join(str(l) for l in cinfo["call_lines"][:5])
                output += f"- `{cinfo['file']}` → `{cinfo['function']}()` (calls at line(s) {lines_str})\n"
        else:
            output += "- No call chain data available.\n"
    else:
        output += f"No references found for `{symbol}`.\n"

    output += _markdown_footer()
    return output


def _summarize_architecture_impl(target_path: Optional[str] = None, streaming: bool = True,
                                 mode: str = "summary", max_tokens: int = 500) -> str:
    """summarize_architecture의 실제 구현 (모듈 레벨)"""
    from bridge.tools.deep_analyzer import _run_map_dependencies
    from bridge.file_cache import FileCache

    root = Path(get_project_root(target_path))
    root_str = str(root)

    cache = FileCache()
    cache_stats = cache.stats()

    # ── 공통 데이터 수집 ──
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

    # ── 모든 파일 수집 ──
    all_files = []
    for p in _iter_project_files_cached(root, extensions=SOURCE_EXTS, exclude_dirs=DEFAULT_EXCLUDE_DIRS):
        all_files.append(p)

    total_files = len(all_files)

    output = _markdown_header("Architecture Analysis")
    output += f"**Project**: `{root.name}`\n"
    output += f"**Tech Stack**: {', '.join(found_techs) if found_techs else 'Auto-detect failed'}\n"
    output += f"**Mode**: `{mode}`  \n**Max tokens**: `{max_tokens if max_tokens > 0 else 'unlimited'}`\n\n"

    if mode == "summary":
        # ── Summary 모드: 핵심 요약만 (1000자 이내) ──

        # 진입점 식별
        entry_patterns = ["main.py", "index.ts", "index.js", "app.ts", "main.go", "__init__.py",
                          "extension.ts", "server.ts", "server.js"]
        entries = []
        for pattern in entry_patterns:
            for p in root.rglob(pattern):
                if p.is_file() and not any(part in str(p) for part in DEFAULT_EXCLUDE_DIRS):
                    rel = _normalize_path(str(p.relative_to(root)))
                    entries.append(rel)
        entries = entries[:5]

        # 파일 타입 분포
        ext_count = defaultdict(int)
        for p in all_files:
            ext_count[p.suffix] += 1

        # 기본 통계
        total_lines = 0
        for p in all_files:
            try:
                total_lines += len(p.read_text(encoding="utf-8", errors="ignore").split("\n"))
            except Exception:
                pass

        dep_output = _run_map_dependencies(target_path=root_str)
        has_cycles = "✅ No circular dependencies" not in dep_output

        output += "## Summary\n\n"
        output += f"- **Source files**: {total_files}\n"
        output += f"- **Total lines**: ~{total_lines}\n"
        if entries:
            output += f"- **Entry points**: {', '.join(entries)}\n"
        if found_techs:
            output += f"- **Primary language**: {found_techs[0]}\n"
        output += f"- **Tech stack**: {len(found_techs)} technology(s) detected\n"
        output += f"- **Circular dependencies**: {'⚠️ Yes' if has_cycles else '✅ No'}\n\n"

        # 주요 발견
        output += "### Key Findings\n"
        ext_summary = []
        for ext, count in sorted(ext_count.items(), key=lambda x: -x[1])[:3]:
            ext_summary.append(f"`{ext}`: {count}")
        output += f"- File distribution: {', '.join(ext_summary)}\n"

        # 캐시 통계 (접힘)
        output += f"\n<details>\n<summary>📊 Cache Statistics</summary>\n\n"
        output += f"- L1 size: {cache_stats.get('l1_size', 0)}/{cache_stats.get('l1_max', 50)}\n"
        output += f"- File list cache: {cache_stats.get('file_list_cache_size', 0)} entries\n"
        output += f"- L2 path: {cache_stats.get('l2_path', 'N/A')}\n"
        output += f"</details>\n\n"

    else:
        # ── Full 모드: 기존 상세 보고서 ──

        dep_output = _run_map_dependencies(target_path=root_str)
        highest_deps = []
        parsing_imports = False
        for line in dep_output.split("\n"):
            if "Import Count by File" in line:
                parsing_imports = True
                continue
            if parsing_imports and line.startswith("- `"):
                m = re.match(r'- `(.+?)`:\s*\*{0,2}(\d+)\*{0,2}\s*imports?', line)
                if m:
                    highest_deps.append((m.group(1), int(m.group(2))))
            if parsing_imports and line.startswith("---"):
                break

        # 진입점 식별
        entry_patterns = ["main.py", "index.ts", "index.js", "app.ts", "main.go", "__init__.py",
                          "extension.ts", "server.ts", "server.js"]
        entries = []
        for pattern in entry_patterns:
            for p in root.rglob(pattern):
                if p.is_file() and not any(part in str(p) for part in DEFAULT_EXCLUDE_DIRS):
                    rel = _normalize_path(str(p.relative_to(root)))
                    entries.append(rel)
        entries = entries[:5]
        if entries:
            output += "## Entry Points\n"
            for e in entries:
                output += f"- `{e}`\n"
            output += "\n"

        # 파일 타입 분포
        ext_count = defaultdict(int)
        for p in all_files:
            ext_count[p.suffix] += 1
        output += "## Code Metrics\n\n"
        output += "### File Type Distribution\n"
        for ext, count in sorted(ext_count.items(), key=lambda x: -x[1]):
            output += f"- `{ext}`: {count} files\n"

        # 기본 통계
        total_lines = 0
        for p in all_files:
            try:
                total_lines += len(p.read_text(encoding="utf-8", errors="ignore").split("\n"))
            except Exception:
                pass
        output += "\n### Basic Stats\n"
        output += f"- Source files: {total_files}\n"
        output += f"- Total lines: ~{total_lines}\n"
        if found_techs:
            output += f"- Primary language: {found_techs[0]}\n"
        output += "\n"

        # ── 스트리밍 분기점: Stage 1 완료 ──
        if streaming:
            output += BaseTool.progress_chunk(
                "1/2", 50,
                "🏗️ 기본 정보 확인 완료 — 의존성 분석 및 git 트렌드는 아래에 계속됩니다..."
            )
            output += "> **의존성 분석 및 git 트렌드는 아래에 계속됩니다...**\n\n"

        # ── Stage 2: 의존성 분석 + git 트렌드 ──

        # Import 기반 레이어 자동 발견
        output += "## Auto-Discovered Layers (import-based)\n\n"
        dir_import_count = defaultdict(int)
        for p in all_files:
            content = _read_file_content(p)
            if content is None:
                continue
            rel = _normalize_path(str(p.relative_to(root)))
            imports = []
            if p.suffix in TS_JS_EXTS:
                ast_imports = _get_ast_engine().extract_imports(content, p.suffix)
                imports = [i["module"] for i in ast_imports]
            else:
                imports = _extract_regex_imports(str(p))
            for imp in imports:
                if imp.startswith("."):
                    imp_dir = os.path.dirname(os.path.normpath(os.path.join(os.path.dirname(rel), imp)))
                    if imp_dir and imp_dir != ".":
                        dir_import_count[imp_dir] += 1

        top_dirs = sorted(dir_import_count.items(), key=lambda x: -x[1])[:5]
        if top_dirs:
            for dir_name, count in top_dirs:
                output += f"- **{dir_name}/** → imported by {count} files\n"
        else:
            output += "- No significant import-based layers detected.\n"
        output += "\n"

        # 기술 부채 진단
        output += "## Technical Debt Diagnosis\n\n"
        debt_items = []
        has_cycles = "✅ No circular dependencies" not in dep_output
        if has_cycles:
            debt_items.append("⚠️ Circular dependencies detected — high coupling risk")
        high_dep_files = [(f, c) for f, c in highest_deps if c > 10]
        if high_dep_files:
            for f, c in high_dep_files[:3]:
                debt_items.append(f"⚠️ `{f}` has {c} imports — too many responsibilities?")
        if total_files > 100:
            debt_items.append(f"📏 Large project ({total_files} source files) — consider modularization")
        if len(found_techs) > 2:
            debt_items.append(f"🔀 Multiple tech stacks ({', '.join(found_techs)}) — cognitive load")
        if debt_items:
            for item in debt_items:
                output += f"- {item}\n"
        else:
            output += "- ✅ No significant technical debt detected.\n"
        output += "\n"

        # Dependency Metrics
        output += "## Dependency Metrics\n"
        if highest_deps:
            output += f"- **Most imported files** (hub modules):\n"
            for fpath, count in highest_deps[:5]:
                output += f"  - `{fpath}` ← {count} dependents\n"
        output += f"- **Circular dependencies**: {'⚠️ Detected' if has_cycles else '✅ None'}\n\n"

        # Git 활동 트렌드
        output += "### Change Trend (git log)\n"
        try:
            git_result = subprocess.run(
                ["git", "log", "--oneline", "--since=30.days", "--format=%ad", "--date=short"],
                cwd=root_str, capture_output=True, text=True, timeout=10
            )
            if git_result.stdout.strip():
                commits = git_result.stdout.strip().split("\n")
                output += f"- Commits in last 30 days: {len(commits)}\n"
                date_counts = Counter(commits)
                most_active = date_counts.most_common(3)
                if most_active:
                    output += f"- Most active days: {', '.join(f'{d}({c})' for d, c in most_active)}\n"
            else:
                output += "- No recent git activity found.\n"
        except Exception:
            output += "- Git history not available.\n"
        output += "\n"

        # 레이어 분류 (path-based)
        layers = defaultdict(list)
        for p in all_files:
            rel = _normalize_path(str(p.relative_to(root)))
            if "extension/src" in rel or "src/" in rel or "lib/" in rel:
                sub = rel.split("/")
                if any(kw in sub for kw in ["ui", "visual", "view", "component"]):
                    layers["UI/Presentation"].append(rel)
                elif any(kw in sub for kw in ["safety", "guard", "security", "auth"]):
                    layers["Safety/Security"].append(rel)
                elif any(kw in sub for kw in ["flow", "orchestra", "controller", "service"]):
                    layers["Business Logic/Orchestration"].append(rel)
                elif any(kw in sub for kw in ["context", "crow", "memory", "data", "store"]):
                    layers["Data/Context"].append(rel)
                elif any(kw in sub for kw in ["types", "util", "helper", "common"]):
                    layers["Utilities/Types"].append(rel)
                elif any(kw in sub for kw in ["mcp", "bridge", "server", "api"]):
                    layers["API/MCP Interface"].append(rel)
                else:
                    layers["Core"].append(rel)
            elif "mcp-servers" in rel:
                layers["API/MCP Interface"].append(rel)
            elif "templates" in rel or "plans" in rel or "fromscratch" in rel:
                layers["Documentation/Config"].append(rel)
        if layers:
            output += "## Layer Structure (path-based)\n"
            for layer_name, files in sorted(layers.items(), key=lambda x: -len(x[1])):
                if files:
                    output += f"- **{layer_name}** ({len(files)} files)\n"
                    for f in files[:5]:
                        output += f"  - `{f}`\n"
                    if len(files) > 5:
                        output += f"  - ... +{len(files)-5} more\n"
            output += "\n"

        # ── 스트리밍 분기점: Stage 2 완료 ──
        if streaming:
            output += BaseTool.progress_chunk(
                "2/2", 100,
                "✅ 아키텍처 분석 완료"
            )

    # 캐시 통계 (접힘, full 모드에서도 추가)
    if mode == "full":
        output += f"<details>\n<summary>📊 Cache Statistics</summary>\n\n"
        output += f"- L1 size: {cache_stats.get('l1_size', 0)}/{cache_stats.get('l1_max', 50)}\n"
        output += f"- File list cache: {cache_stats.get('file_list_cache_size', 0)} entries\n"
        output += f"- L2 path: {cache_stats.get('l2_path', 'N/A')}\n"
        output += f"</details>\n\n"

    # Crow ingest
    try_crow_ingest(
        json.dumps({
            "action": "arch_summary",
            "files": total_files,
            "tech": found_techs,
            "mode": mode,
            "streaming": streaming,
        }),
        register="arch"
    )
    output += _markdown_footer()
    return truncate_to_tokens(output, max_tokens)


# ── register ──────────────────────────────────────────


def register(mcp):
    """Scout 도구 등록"""

    @mcp.tool
    def search_codebase(query: str, file_patterns: Optional[str] = None,
                        max_results: int = 50, mode: str = "auto",
                        context_lines: int = 3,
                        target_path: Optional[str] = None) -> str:
        """프로젝트 코드베이스에서 쿼리와 관련된 코드를 검색합니다.
        tree-sitter AST 파싱을 우선 시도하고, 실패 시 regex로 폴백합니다.

        Args:
            query: 검색할 내용 (자연어 또는 코드 스니펫)
            file_patterns: 검색 대상 파일 패턴 (예: *.ts,*.tsx). 쉼표로 구분.
            max_results: 최대 결과 수 (기본: 10)
            mode: 검색 모드 ("auto", "exact", "fuzzy", "ast", "semantic"). 기본: "auto"
                  "fuzzy" = trigram approximate match (Dice coefficient on character 3-grams, threshold 0.35)
            context_lines: 컨텍스트 라인 수 (기본: 3)
            target_path: 검색 대상 디렉토리 경로 (기본: 현재 워크스페이스)
        """
        return _search_codebase_impl(query, file_patterns, max_results, mode, context_lines, target_path)

    @mcp.tool
    def find_references(symbol: str, target_path: Optional[str] = None) -> str:
        """주어진 심볼(함수, 클래스, 변수)의 모든 참조를 찾습니다.
        정의와 사용 위치를 구분하여 반환합니다.

        Args:
            symbol: 찾을 심볼 이름
            target_path: 검색 대상 디렉토리 경로 (기본: 현재 워크스페이스)
        """
        return _find_references_impl(symbol, target_path)

    @mcp.tool
    def summarize_architecture(target_path: Optional[str] = None, streaming: bool = True,
                                mode: str = "summary", max_tokens: int = 500) -> str:
        """프로젝트 아키텍처를 분석하여 요약합니다.
        내부적으로 map_dependencies + analyze_call_graph를 호출하여
        실제 모듈 의존성, 진입점, 레이어 구조를 분석합니다.
        streaming=True 시 기본 정보를 먼저 반환하고, 의존성 분석 및 git 트렌드를 별도 섹션으로 추가합니다.

        Args:
            target_path: 분석 대상 디렉토리 경로
            streaming: True면 기본 정보 → 의존성 분석 → git 트렌드 순으로 점진적 결과 (기본: True)
            mode: "summary" (기본) — 핵심 요약만 (파일 수, 주요 발견, 등급) 1000자 이내
                  "full" — 전체 상세 보고서 (기존 동작)
            max_tokens: LLM 컨텍스트 제한 (기본: 500). 0이면 전체.
        """
        return _summarize_architecture_impl(target_path, streaming, mode, max_tokens)
