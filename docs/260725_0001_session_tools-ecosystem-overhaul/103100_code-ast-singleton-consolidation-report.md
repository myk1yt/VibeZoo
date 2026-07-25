# Code Task Report: ST-03 Consolidate Duplicated AST Singleton

## Task Summary
Consolidated the duplicated `_get_ast_engine()` singleton pattern from 5 tool files into a single shared module `bridge/ast_singleton.py`, applied to both `mcp-servers/bridge/` (root) and `extension/mcp-servers/bridge/` (extension) copies.

## Actions Taken
1. Created [`ast_singleton.py`](mcp-servers/bridge/ast_singleton.py) in root copy with `get_ast_engine()` function
2. Created [`ast_singleton.py`](extension/mcp-servers/bridge/ast_singleton.py) in extension copy (identical)
3. Edited [`scout.py`](mcp-servers/bridge/tools/scout.py) — removed local `_ast_engine` variable and `_get_ast_engine()` function, added import alias
4. Edited [`analysis.py`](mcp-servers/bridge/tools/analysis.py) — same pattern
5. Edited [`deep_analyzer.py`](mcp-servers/bridge/tools/deep_analyzer.py) — same pattern
6. Edited [`reviewer.py`](mcp-servers/bridge/tools/reviewer.py) — same pattern
7. Edited [`tester.py`](mcp-servers/bridge/tools/tester.py) — same pattern
8. Applied all 5 edits to the extension copies as well (dual-apply constraint)
9. Ran verification on both roots

## Result
✅ Success — all 4 verification tests passed:

**Root copy (`mcp-servers/`):**
- `python -c "from bridge.ast_singleton import get_ast_engine; a=get_ast_engine(); b=get_ast_engine(); assert a is b; print('OK')"` → `OK`
- `python -c "from bridge.tools import register_all_tools; from fastmcp import FastMCP; m=FastMCP('t'); register_all_tools(m); print('OK')"` → `OK`

**Extension copy (`extension/mcp-servers/`):**
- `python -c "from bridge.ast_singleton import get_ast_engine; a=get_ast_engine(); b=get_ast_engine(); assert a is b; print('OK')"` → `OK`
- `python -c "from bridge.tools import register_all_tools; from fastmcp import FastMCP; m=FastMCP('t'); register_all_tools(m); print('OK')"` → `OK`

## Issues Discovered
None. All internal call sites (`_get_ast_engine()`) remain unchanged because the import alias `get_ast_engine as _get_ast_engine` preserves the local name.

## Next Step Recommendations
- Consider applying the same singleton consolidation pattern to `_file_cache` in [`scout.py`](mcp-servers/bridge/tools/scout.py) if cross-tool cache sharing is desired.
- [`analysis.py:112`](mcp-servers/bridge/tools/analysis.py:112) still creates a standalone `AstEngine()` instance (not via singleton) in a different function — this is intentional and left unchanged as it has different initialization logic (`_init_legacy_tree_sitter()`).

## Affected File List
- `mcp-servers/bridge/ast_singleton.py` (new)
- `mcp-servers/bridge/tools/scout.py`
- `mcp-servers/bridge/tools/analysis.py`
- `mcp-servers/bridge/tools/deep_analyzer.py`
- `mcp-servers/bridge/tools/reviewer.py`
- `mcp-servers/bridge/tools/tester.py`
- `extension/mcp-servers/bridge/ast_singleton.py` (new)
- `extension/mcp-servers/bridge/tools/scout.py`
- `extension/mcp-servers/bridge/tools/analysis.py`
- `extension/mcp-servers/bridge/tools/deep_analyzer.py`
- `extension/mcp-servers/bridge/tools/reviewer.py`
- `extension/mcp-servers/bridge/tools/tester.py`
