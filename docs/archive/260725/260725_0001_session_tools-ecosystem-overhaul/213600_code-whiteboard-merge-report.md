# Code Task Report: ST-09 Merge auto_analyze_whiteboard into get_whiteboard_state

## Task Summary
Merged the thin wrapper `auto_analyze_whiteboard()` into `get_whiteboard_state()` by adding an optional `analyze` parameter. The deprecated alias now delegates to the merged function. All changes dual-applied to root and extension copies.

## Actions Taken

### 1. Added `_generate_whiteboard_suggestions()` helper to `whiteboard.py`
- Module-level function that produces the suggestion block (Mermaid, code generation, design feedback, etc.)
- Previously this logic was inline in `auto_analyze_whiteboard()` in `ux_coordinator.py`

### 2. Extracted `_get_whiteboard_state_impl()` to module level in `whiteboard.py`
- The original `get_whiteboard_state()` was a closure inside `register(mcp)`, making it unimportable
- Extracted the full implementation to `_get_whiteboard_state_impl(analyze: bool)` at module level
- The MCP-registered `get_whiteboard_state(analyze)` now delegates to `_get_whiteboard_state_impl()`
- This allows `ux_coordinator.py` to import and call it directly

### 3. Added `analyze: bool = False` parameter to `get_whiteboard_state()`
- When `True`: returns whiteboard state + suggestion block
- When `False` (default): returns state only, with a hint pointing to `analyze=True`
- Handles all three data types: empty, image/screenshot, commands/Fabric.js

### 4. Converted `auto_analyze_whiteboard()` to deprecated alias in `ux_coordinator.py`
- Now calls `_get_whiteboard_state_impl(analyze=True)` internally
- Appends deprecation note: `> ⚠️ deprecated: use get_whiteboard_state(analyze=True) instead`
- MCP registration retained for backward compatibility
- Docstring updated with `[DEPRECATED]` prefix

### 5. Updated docstrings
- `get_whiteboard_state()`: documents the `analyze` parameter and relationship to deprecated alias
- `auto_analyze_whiteboard()`: documents deprecation and delegation behavior
- `_generate_whiteboard_suggestions()`: documents its role in both functions

### 6. Created test file `test_whiteboard_merge.py`
- 16 tests across 5 test classes
- Uses `MockMCP` class to capture registered tools
- Uses `tmp_path` fixtures for whiteboard JSON files
- Mocks `WHITEBOARD_FILE`, `try_crow_ingest`, `WHITEBOARD_ACTION_FILE`, `DZ_SESSION_FILE`
- All tests CI-safe (no network, no real files)

### 7. Dual-applied all changes
- Root: `mcp-servers/bridge/tools/whiteboard.py`, `mcp-servers/bridge/tools/ux_coordinator.py`
- Extension: `extension/mcp-servers/bridge/tools/whiteboard.py`, `extension/mcp-servers/bridge/tools/ux_coordinator.py`
- Tests: `mcp-servers/tests/test_whiteboard_merge.py`, `extension/mcp-servers/tests/test_whiteboard_merge.py`

## Result
✅ Success — 16/16 tests pass on both roots

```
# Root
cd mcp-servers; python -m pytest tests/test_whiteboard_merge.py -q
16 passed in 31.64s

# Extension
cd extension/mcp-servers; python -m pytest tests/test_whiteboard_merge.py -q
16 passed in 30.23s
```

## Issues Discovered
- **Closure import issue**: `get_whiteboard_state()` was originally a closure inside `register(mcp)`, making it unimportable from `ux_coordinator.py`. Fixed by extracting `_get_whiteboard_state_impl()` to module level. This is a clean architectural improvement that also makes the function unit-testable without MCP registration.

## Next Step Recommendations
- Update MCP tool descriptions/schema if the bridge exposes parameter metadata to the LLM
- Consider updating any documentation or examples that reference `auto_analyze_whiteboard()` to use `get_whiteboard_state(analyze=True)` instead
- The hint text in non-analyze mode now points to `get_whiteboard_state(analyze=True)` instead of `auto_analyze_whiteboard()`

## Affected File List
- `mcp-servers/bridge/tools/whiteboard.py` — added `_generate_whiteboard_suggestions()`, `_get_whiteboard_state_impl()`, `analyze` param
- `mcp-servers/bridge/tools/ux_coordinator.py` — converted `auto_analyze_whiteboard()` to deprecated alias
- `mcp-servers/tests/test_whiteboard_merge.py` — new test file (16 tests)
- `extension/mcp-servers/bridge/tools/whiteboard.py` — same changes as root
- `extension/mcp-servers/bridge/tools/ux_coordinator.py` — same changes as root
- `extension/mcp-servers/tests/test_whiteboard_merge.py` — same test file as root
