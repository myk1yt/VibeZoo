# Code Task Report: ST-04 Fix `find_references` False Positives

## Task Summary
Fixed the `find_references` tool in [`scout.py`](mcp-servers/bridge/tools/scout.py) that used naive substring matching (`if symbol not in line`), causing false positives when searching for short symbols like `io` (which matched `action`, `configuration`, etc.). Replaced with a precompiled word-boundary regex.

## Actions Taken

### 1. Word-boundary regex precompilation
Added `symbol_pattern = re.compile(r'\b' + re.escape(symbol) + r'\b')` at the start of [`_find_references_impl`](mcp-servers/bridge/tools/scout.py:253), with a `# SRF` comment documenting the boundary contract.

### 2. Replaced substring check
- OLD: `if symbol not in line: continue`
- NEW: `if not symbol_pattern.search(line): continue`

### 3. Tightened ref-type classifiers
The `call`, `type_ref`, `read`, and `write` classifiers previously used f-string containment like `f"new {symbol}"` or `f"{symbol}("`. These now also check `symbol_pattern.search(stripped)` for consistency, ensuring the symbol appears as a whole word before classifying the reference type.

### 4. Dual-apply
All changes applied to BOTH:
- [`mcp-servers/bridge/tools/scout.py`](mcp-servers/bridge/tools/scout.py) (root copy)
- [`extension/mcp-servers/bridge/tools/scout.py`](extension/mcp-servers/bridge/tools/scout.py) (extension copy)

### 5. Test file created
Created [`mcp-servers/tests/test_find_references.py`](mcp-servers/tests/test_find_references.py) (and extension copy) with 6 test cases:
- `test_io_does_not_match_action` — verifies `io` search does NOT match `action`
- `test_io_does_not_match_configuration` — verifies `io` search does NOT match `configuration`
- `test_real_io_references_are_found` — verifies real `io` references ARE found
- `test_dotted_access_matched` — verifies dotted access like `obj.io` is matched
- `test_short_symbol_no_false_positives` — verifies no excessive matches
- `test_symbol_with_underscore` — verifies `re.escape()` handles metacharacters

## Result
✅ All 6 tests pass on BOTH roots:
- Root: `python -m unittest mcp-servers.tests.test_find_references -v` → 6 passed in 0.079s
- Extension: `python -m unittest extension.mcp-servers.tests.test_find_references -v` → 6 passed in 0.056s

## Edge Cases Handled
- **Regex metacharacters**: `re.escape()` handles symbols like `my_func`, `Class.Method`, etc.
- **Non-ASCII identifiers**: `\b` is Unicode-aware in Python 3 `re`
- **Dotted access**: `\b` matches after `.`, so `obj.io` is correctly matched

## Issues Discovered
None. The fix is surgical and does not affect any other functionality.

## Affected File List
- `mcp-servers/bridge/tools/scout.py` (lines 253-322: `_find_references_impl`)
- `extension/mcp-servers/bridge/tools/scout.py` (lines 253-322: `_find_references_impl`)
- `mcp-servers/tests/test_find_references.py` (new file)
- `extension/mcp-servers/tests/test_find_references.py` (new file)
