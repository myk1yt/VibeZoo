# Debug Task Report — Phase 5 Technical Review

## Task Summary
Verify the VibeZoo Tool Ecosystem Overhaul (9 sub-tasks across 3 waves), dual-applied to `mcp-servers/bridge/` and `extension/mcp-servers/bridge/`. Scope: full test suite, import smoke tests, new module imports, dual-apply consistency, dead code removal, behavioral spot checks.

## Verdict: 🔶 **CONDITIONAL PASS** (PASS with 1 required follow-up)

**Rationale**: All 5 verification categories pass on both roots. One dual-apply drift was detected in `tools/whiteboard.py` — the extension copy is missing the `check_uploaded_files` MCP tool (58 lines + 1 prompt string change) that exists in the primary copy. This is a Wave 9 dual-apply miss. Functionality on the primary root is intact; only the extension-side runtime is affected. Recommend immediate follow-up to backfill the missing tool, but this does NOT block the overhaul as a whole because:
- All 208 tests (104 per root) pass — extension tests were not gated on the missing tool
- Smoke tests + module imports pass on both roots
- All other 12 inspected files are byte-identical between roots
- All dead-code removal claims verified
- All behavioral spot checks pass

If the VP judges dual-apply parity to be a hard gate, this is a **REJECT** pending the backfill. If dual-apply drift in one MCP tool is acceptable as a tracked follow-up, this is a **PASS**.

---

## 1. Full Test Suite

| Root | Result | Duration |
|---|---|---|
| `mcp-servers/` | ✅ **104/104 PASSED** | 51.56s |
| `extension/mcp-servers/` | ✅ **104/104 PASSED** | 51.45s |

Test files exercised:
- `test_max_tokens.py` (15 tests)
- `test_search_cache.py` (10 tests)
- `test_semantic_search.py` (19 tests)
- `test_web_search.py` (14 tests)
- `test_whiteboard_merge.py` (15 tests)
- Plus `test_find_references.py`, `test_fuzzy_search.py`, `test_ast_singleton.py`, etc. (totalling 104)

No failures. No warnings (other than a benign PowerShell escape warning during my own scripting — unrelated to the codebase).

---

## 2. Import Smoke Test

```
mcp-servers:           OK
extension/mcp-servers: OK
```

Both `register_all_tools(FastMCP('t'))` calls succeed. No import errors.

---

## 3. New Module Imports

| Module | Symbols | mcp-servers | extension |
|---|---|---|---|
| `bridge.fuzzy_matcher` | `trigram_similarity`, `fuzzy_filter` | ✅ OK | ✅ OK |
| `bridge.embedding_client` | `EmbeddingClient`, `cosine_similarity` | ✅ OK | ✅ OK |
| `bridge.ast_singleton` | `get_ast_engine` | ✅ OK | ✅ OK |
| `bridge.utils` | `truncate_to_tokens` | ✅ OK | ✅ OK |

All 8 imports succeed on both roots.

---

## 4. Dual-Apply Consistency

Method: MD5 hash comparison across 13 high-traffic files.

| File | Status |
|---|---|
| `tools/scout.py` | ✅ IDENTICAL |
| `tools/web.py` | ✅ IDENTICAL |
| `tools/integrated.py` | ✅ IDENTICAL |
| `tools/_base.py` | ✅ IDENTICAL |
| `tools/deep_analyzer.py` | ✅ IDENTICAL |
| `tools/__init__.py` | ✅ IDENTICAL |
| `tools/whiteboard.py` | ❌ **DIFFER** |
| `fuzzy_matcher.py` | ✅ IDENTICAL |
| `embedding_client.py` | ✅ IDENTICAL |
| `ast_singleton.py` | ✅ IDENTICAL |
| `utils.py` | ✅ IDENTICAL |
| `result_ranker.py` | ✅ IDENTICAL |
| `search_engine.py` | ✅ IDENTICAL |

### ⚠️ Whiteboard.py Drift Detail

- **Primary (`mcp-servers/bridge/tools/whiteboard.py`)**: 1099 lines
- **Extension (`extension/mcp-servers/bridge/tools/whiteboard.py`)**: 1041 lines
- **Diff**: 59 primary-only lines, 1 extension-only line, 1 modified line

The extension copy is missing:
1. The entire `@mcp.tool` definition for `check_uploaded_files()` (~58 lines) — a tool that lists files uploaded to the dropzone for the current session.
2. One prompt string change: primary says "call `analyze_uploaded_file()` with no arguments", extension still says "call `check_uploaded_files()`".

**Direction**: One-way drift (primary is newer). No extension-only content is at risk of being lost.

**Recommended Action**: Backfill `check_uploaded_files` from primary into `extension/mcp-servers/bridge/tools/whiteboard.py`, then update the prompt string. This is a Wave 9 dual-apply miss.

---

## 5. Dead Code Removal

| Check | Expected | Actual | Status |
|---|---|---|---|
| `integrated.py::_tool_registry` entries | 8 | 8 | ✅ |
| `deep_analyzer.py` has `import subprocess` | NO | NO | ✅ |
| `_base.py` has `partial_result()` | NO | NO | ✅ |

`_tool_registry` keys (verified by calling `register(mcp)` and inspecting):
```
['analyze_call_graph', 'draw_on_whiteboard', 'extract_patterns',
 'map_dependencies', 'reverse_engineer', 'review_code',
 'search_codebase', 'summarize_architecture']
```

Note: `_tool_registry` is initialized as `{}` at module level and populated inside `register(mcp)`. A naive `python -c "from bridge.tools.integrated import _tool_registry; print(len(...))"` returns 0 because registration hasn't run yet. This is the intended lazy-init pattern.

---

## 6. Behavioral Spot Checks

### 6a. `search_codebase` mode="fuzzy" uses trigram matching ✅
- `bridge.fuzzy_matcher.trigram_similarity` is the active scoring function
- Dice coefficient on character 3-grams
- Special case: strings <3 chars fall back to substring containment (documented in code at `fuzzy_matcher.py:8-12`)

### 6b. `search_codebase` mode="semantic" attempts embedding server ✅
- Verified by `test_semantic_search.py::TestSemanticSearchIntegration::test_semantic_with_embedding_server_up` and `..._server_down` (both pass)
- `EmbeddingClient` supports both Ollama-style and OpenAI-style endpoints with availability caching

### 6c. `find_references("io")` does NOT match "action" ✅
- 14 total matches in primary codebase
- **0 false positives** (all 14 lines contain `io` as a word-bounded symbol, not as a substring of `action`/`configuration`/etc.)
- Word-boundary regex matching is functioning correctly

### 6d. `web_search` with no EXA_API_KEY uses DuckDuckGo ✅
- Verified via `test_web_search.py::TestEngineAutoResolution::test_auto_uses_ddg_when_no_key` (passes)
- Engine resolution: `web.py:36` checks `EXA_API_KEY` env var, falls back to keyring, then defaults to DDG
- `_duckduckgo_search` is stdlib-only HTML scraping, no new deps

---

## Issues Discovered

### 🔴 Issue 1: Wave 9 Dual-Apply Miss — `whiteboard.py`
- **Severity**: MEDIUM (one MCP tool missing in extension runtime)
- **Impact**: VS Code extension users will not have access to `check_uploaded_files` tool
- **Recommended routing**: `code-light` (single-file backfill, ~58 lines + 1 string change)
- **ETA**: <5 minutes

### 🟡 Issue 2: Trigram Short-String Edge Case (informational only)
- `trigram_similarity('io', 'action') = 1.0` due to substring containment fallback for short queries (`fuzzy_matcher.py:8-12`)
- This is **deliberate** and documented in code. It creates an interesting tension with `find_references` (which uses word-boundary matching), but the two tools have different contracts:
  - `find_references` → exact symbol lookup (precision-first)
  - `search_codebase --fuzzy` → fuzzy text search (recall-first)
- **No action needed**. Filed as informational.

---

## Test Environment Issues

**None.** The test environment was already properly configured. All 208 tests ran cleanly without any infrastructure fixes needed.

---

## Affected File List

**Inspected (read-only verification)**:
- `mcp-servers/bridge/tools/{scout,web,integrated,_base,deep_analyzer,whiteboard}.py`
- `mcp-servers/bridge/{fuzzy_matcher,embedding_client,ast_singleton,utils,result_ranker,search_engine}.py`
- `extension/mcp-servers/bridge/` (mirror set)
- `mcp-servers/tests/` (full suite, 104 tests)
- `extension/mcp-servers/tests/` (full suite, 104 tests)

**Created (temporary, cleaned up)**:
- `mcp-servers/_verify_fuzzy.py` (deleted after use)
- `mcp-servers/_verify_find_refs.py` (deleted after use)

**Modified**: NONE. This was a read-only verification.

---

## Next Step Recommendations

1. **Immediate** (blocking if dual-apply parity is a hard gate):
   - Route to `code-light`: Backfill `check_uploaded_files` from `mcp-servers/bridge/tools/whiteboard.py` into `extension/mcp-servers/bridge/tools/whiteboard.py`. Also update the prompt string at the location where extension still references the old function name.
   - Re-run this Phase 5 review's Step 4 (dual-apply check) to confirm parity.

2. **Optional** (not blocking):
   - Consider whether the trigram short-string substring fallback (`fuzzy_matcher.py:8-12`) should be tightened to word-boundary matching for consistency with `find_references`. Document as ADR if a decision is made.

3. **Proceed** to Phase 6 (Final Ask Audit) once the dual-apply backfill is complete and verified, OR proceed now if the VP accepts the drift as a tracked follow-up.
