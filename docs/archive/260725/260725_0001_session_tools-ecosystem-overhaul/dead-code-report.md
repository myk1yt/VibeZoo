# Dead Code Report — VibeZoo MCP Tool Ecosystem

## 1. Unused Imports

### [`scout.py`](mcp-servers/bridge/tools/scout.py)
- **L10**: `from collections import Counter, defaultdict` — `Counter` is never used in this file (only `defaultdict` is used in `_summarize_architecture_impl`)
- **L17**: `from typing import Optional` — used, but `Optional` from `typing` is only needed for type hints that could be simplified

### [`analysis.py`](mcp-servers/bridge/tools/analysis.py)
- **L9**: `import time` — used only in `_get_git_blame()`, acceptable
- **L11**: `from collections import defaultdict` — used in `review_pr()`, acceptable
- No dead imports detected

### [`integrated.py`](mcp-servers/bridge/tools/integrated.py)
- **L5**: `import inspect` — used in `_run_tool()` for `inspect.signature()`, acceptable
- **L13**: `import sys` — only used for Pylance path fix, acceptable

### [`deep_analyzer.py`](mcp-servers/bridge/tools/deep_analyzer.py)
- **L7**: `import subprocess` — imported but **NEVER used** anywhere in the file. Dead import.
- **L8**: `from collections import Counter, defaultdict` — `Counter` is used in `analyze_call_graph()`, `defaultdict` in `_run_map_dependencies()`. Both used.

---

## 2. Dead Functions / Stub Functions

### [`_base.py`](mcp-servers/bridge/tools/_base.py)
- **L27-31**: `BaseTool.partial_result()` — described as "점진적 스트리밍 — 부분 결과 반환 (향후 확장)". This is a **placeholder/stub** that returns a raw JSON dict. No tool in the ecosystem actually calls `partial_result()`. **Dead code.**
- **L55-66**: `BaseTool.progress_chunk()` — actually used by [`scout.py`](mcp-servers/bridge/tools/scout.py:545), [`integrated.py`](mcp-servers/bridge/tools/integrated.py:464). ✅ Used
- **L68-82**: `BaseTool.final_result()` — used by [`integrated.py`](mcp-servers/bridge/tools/integrated.py:539). ✅ Used

### [`github_diver.py`](mcp-servers/bridge/tools/github_diver.py)
- **L52**: The text `"💡 Tip: Use github_explore_repository(repo_name) to view its file structure."` references a function name `github_explore_repository` that **does not exist**. The actual MCP tool is named `explore_github`. This is a **dead reference / stale hint**.
- **L102**: Similarly references `"github_read_file(repo_name, file_path)"` — this function also **does not exist** as an MCP tool. The actual interface is `explore_github(repo=..., file_path=...)`.

### [`integrated.py`](mcp-servers/bridge/tools/integrated.py)
- **L38-39**: `_tool_registry` — This is a module-level dict initialized at L303-323 with **all None values**. The lazy getters (`_get_search_codebase()`, etc.) are designed to populate it lazily, but the `_lazy_tool()` function at L337-343 is **never called** by anything. It appears to be dead code from an earlier design iteration.
- **L337-343**: `_lazy_tool()` function — **Dead code**. Never invoked. The actual lazy loading happens through the `_get_*()` functions directly.

---

## 3. Redundant / Duplicated Code

### `_get_ast_engine()` Singleton Pattern
This exact pattern is duplicated in **5 separate files**:
- [`scout.py`](mcp-servers/bridge/tools/scout.py:45) L45-49
- [`analysis.py`](mcp-servers/bridge/tools/analysis.py:35) L35-39
- [`deep_analyzer.py`](mcp-servers/bridge/tools/deep_analyzer.py:36) L36-40
- [`reviewer.py`](mcp-servers/bridge/tools/reviewer.py:37) L37-41
- [`tester.py`](mcp-servers/bridge/tools/tester.py:34) L34-38

Each creates its own global `_ast_engine = None` and its own `_get_ast_engine()` function. Since they all use the same class `AstEngine()`, these could be consolidated into a single shared singleton.

### `_validate_string` / `_validate_int` / `_validate_file_path` Imports
Imported in almost every tool file via `bridge.utils`. While not dead, the import pattern is repeated identically 16 times.

---

## 4. Unused Parameters

### [`search_codebase`](mcp-servers/bridge/tools/scout.py:702)
- **`context_lines`** parameter (L704): Accepted and forwarded to `SearchEngine.search()`, but when `mode == "semantic"`, the parameter is effectively ignored (ResultRanker.rank() doesn't use context_lines).

### [`summarize_architecture`](mcp-servers/bridge/tools/scout.py:731)
- **`max_tokens`** parameter (L734): Declared but **never used** in the implementation. The docstring says "LLM 컨텍스트 제한" but the code doesn't truncate output based on it.

### [`review_project`](mcp-servers/bridge/tools/integrated.py:400)
- **`max_tokens`** parameter (L401): Same as above — declared but never used in the summary or full path.

### [`find_bugs`](mcp-servers/bridge/tools/integrated.py:544)
- **`max_tokens`** parameter (L453): Declared but never used.

### [`suggest_refactor`](mcp-servers/bridge/tools/integrated.py:757)
- **`max_tokens`** parameter (L758): Declared but never used.

### [`generate_docs`](mcp-servers/bridge/tools/integrated.py:886)
- **`max_tokens`** parameter (L887): Declared but never used.

### [`analyze_call_graph`](mcp-servers/bridge/tools/deep_analyzer.py:528)
- **`include_external`** parameter (L530): Declared but **never used** in the implementation. All calls are processed regardless.

---

## 5. Commented-Out / Legacy Code

### [`reviewer.py`](mcp-servers/bridge/tools/reviewer.py)
- L3 comment: `# check_quality 함수는 내부용으로 유지 (더 이상 MCP 도구 아님)` — indicates `check_quality` was demoted from an MCP tool to an internal function. Its registration was removed but the function itself is still used internally by `integrated.py`.

### [`whiteboard.py`](mcp-servers/bridge/tools/whiteboard.py)
- L4 comment: `# open_whiteboard / open_ui_preview 는 MCP 도구에서 제거됨 (Extension 자동 처리)` — Two tools (`open_whiteboard`, `open_ui_preview`) were removed from MCP registration. No remnant code found, so this is clean.

---

## 6. Stale Tool References (Cross-file)

### `integrated.py` references
At [`integrated.py`](mcp-servers/bridge/tools/integrated.py:319), the `_tool_registry` dict lists:
- `"check_quality": None` — This tool was removed from MCP registration (as noted in reviewer.py L3). The registry entry is stale.
- `"generate_tests": None` — The lazy getter `_get_generate_tests()` is never defined, yet it's in the registry. This entry is dead.
- `"analyze_coverage": None` — Same issue — no lazy getter exists. Dead entry.
- `"explain_code": None` — No lazy getter. Dead entry.
- `"analyze_changes": None` — Lazy getter exists but is never called (it's defined at L392-395 but never invoked). Dead code.
- `"review_pr": None` — No lazy getter. Dead entry.
- `"refactor_across_files": None` — No lazy getter. Dead entry.
- `"learn_project": None` — No lazy getter. Dead entry.
- `"recall_project": None` — No lazy getter. Dead entry.
- `"learn_preference": None` — No lazy getter. Dead entry.
- `"get_preferences": None` — No lazy getter. Dead entry.

**Of the 20 entries in `_tool_registry`, only 8 have working lazy getters** (`search_codebase`, `review_code`, `extract_patterns`, `map_dependencies`, `analyze_call_graph`, `reverse_engineer`, `summarize_architecture`, `draw_on_whiteboard`). The remaining 12 are vestigial.

---

## Summary

| Category | Count | Severity |
|----------|-------|----------|
| Dead imports | 1 | 🟢 Low |
| Dead/stub functions | 2 | 🟡 Medium |
| Dead references in tool text | 2 | 🟡 Medium |
| Duplicated singleton pattern | 5x | 🟡 Medium (maintainability) |
| Unused parameters | 7 | 🟡 Medium |
| Dead entries in `_tool_registry` | 12/20 | 🔴 High (confusing, maintenance burden) |
| Stale comments/legacy | 1 | 🟢 Low |
