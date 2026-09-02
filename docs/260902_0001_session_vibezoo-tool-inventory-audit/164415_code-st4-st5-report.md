# Code Task Report — ST-4 + ST-5 (Phase 2: Aggregate Tool Removal, B2)

> Session: `docs/260902_0001_session_vibezoo-tool-inventory-audit/`
> Scope: User-approved A1–B3 (verbatim: "전면 정리 (A1-B3): 집계형 도구(find_bugs, suggest_refactor, generate_docs, learn_project)도 제거하고 프롬프트 조합으로 대체") — [`decisions.md`](decisions.md)
> Plan refs: [`architecture-plan.md`](architecture-plan.md) §3 ST-4/ST-5, §4, Decision D2/D3/D4
> Prior commits: ST-1/ST-2 (9ddeb79), ST-3 (0b5d2ce)

## Task Summary

Removed the 4 aggregate MCP tool registrations per Decision D2 (prompt-composition replacement):
- **ST-4**: `find_bugs`, `suggest_refactor`, `generate_docs` from [`integrated.py`](../../mcp-servers/bridge/tools/integrated.py:1) ×2 copies (root + extension)
- **ST-5**: `learn_project` from [`knowledge.py`](../../mcp-servers/bridge/tools/knowledge.py:1) ×2 copies

Kept intact per Decision D3: `review_project`, `truncate_to_tokens`, `_run_tool`, `_tool_registry`, `try_crow_ingest`, `try_crow_recall`, `_auto_learn_project` + auto-schedule block, `recall_project`, `learn_preference`, `get_preferences`.

## Actions Taken

### ST-4 — integrated.py ×2 (1020 → 250 lines each)
1. Deleted `@mcp.tool def find_bugs` (was L525-736), `suggest_refactor` (L738-865), `generate_docs` (L867-1020)
2. Deleted private helpers used **ONLY** by removed tools (reference-checked before deletion):
   - Module-level `_run_eslint`, `_run_tsc`, `_run_native_linter` (only caller was `find_bugs`; verified via search across `mcp-servers/` — 0 other references)
   - `register()` closures `_get_search_codebase`, `_get_map_dependencies`, `_get_analyze_call_graph`, `_get_reverse_engineer`, `_get_summarize_architecture`, `_get_draw_on_whiteboard`, `_get_analyze_changes` (only callers were removed functions)
   - `import subprocess` (only user was the deleted helper block)
3. Updated module header comment L2 — removed the 3 names (also avoids grep hits)
4. **KEPT**: `review_project` (+ its `_get_review_code`/`_get_check_quality`/`_get_extract_patterns` closures), `_run_tool`, `_tool_registry`, `truncate_to_tokens` import, `try_crow_ingest`/`try_crow_recall`, FileCache warming in `register()`

### ST-5 — knowledge.py ×2 (389 → 297 lines each)
1. Deleted `@mcp.tool def learn_project` (was L123-213)
2. **KEPT**: `_auto_learn_project` (L32), `register()` auto-schedule thread block, `recall_project`, `learn_preference`, `get_preferences` — the `setup.py` L1252 startup hook dependency preserved
3. Updated all docstrings/comments referencing `learn_project`:
   - Module header L2-3, `# ── 자동 learn_project 관리 ──` section marker, `_auto_learn_project` docstring, `register()` docstring, `_deferred_learn` docstring, `recall_project` docstring
4. Fixed `recall_project` hint text per plan §4 learn_project guidance:
   - Root copy: `"Run learn_project() first..."` → `"Project knowledge is auto-captured at bridge startup (_auto_learn_project); force-refresh via summarize_architecture/extract_patterns/map_dependencies and recall again."`
   - Extension copy: same message text (it is i18n `t()`-wrapped there — see Mirror Parity)

### Prompt-composition guidance (plan §4)
Kept minimal per delegation instructions: the `recall_project` hint now embeds the learn_project force-refresh guidance. No new guidance blocks added (ST-7 owns ux_coordinator strings).

## Verification Evidence (actual outputs)

### 1. `python -m py_compile` ×4 files → exit 0
```
COMPILE_OK
RECOMPILE_OK   (after header-comment fix)
```

### 2. Import checks → OK
```
cd mcp-servers            && python -c "import bridge.tools.integrated, bridge.tools.knowledge" → ROOT_IMPORT_OK
cd extension/mcp-servers  && python -c "import bridge.tools.integrated, bridge.tools.knowledge" → EXT_IMPORT_OK
```

### 3. `python -m pytest tests/test_max_tokens.py -v` → 16 passed in 9.93s
```
TestTruncateToTokens ..................... 9 passed
TestSummarizeArchitectureTruncation ...... 2 passed
TestIntegratedToolsTruncation ............ 5 passed
  (incl. test_find_bugs/suggest_refactor/generate_docs_truncation —
   these test the shared truncate_to_tokens helper only, per plan §3 ST-4)
```

### 4. Removed-name grep in 4 edited files → 0 hits
```
mcp-servers/bridge/tools/integrated.py           -> OK (0 hits)
extension/mcp-servers/bridge/tools/integrated.py -> OK (0 hits)
mcp-servers/bridge/tools/knowledge.py            -> OK (0 hits)
extension/mcp-servers/bridge/tools/knowledge.py  -> OK (0 hits)
```
(Regex: `\b(find_bugs|suggest_refactor|generate_docs|learn_project)\b`)

### 5. Runtime registration check (stub mcp) → PASS both trees
```
mcp-servers (root):
    integrated.register -> ['review_project']
    knowledge.register  -> ['get_preferences', 'learn_preference', 'recall_project']
extension/mcp-servers:
    integrated.register -> ['review_project']
    knowledge.register  -> ['get_preferences', 'learn_preference', 'recall_project']
Shared-helper checks: _run_tool/_tool_registry/truncate_to_tokens present;
integrated.truncate_to_tokens is bridge.utils.truncate_to_tokens (same object);
knowledge._auto_learn_project present + callable.
```

### 6. Mirror parity → SHA differs, but drift is PRE-EXISTING i18n wrapping (not introduced by this task)
Line-level unified diff shows the extension tree differs from root ONLY in:
- **integrated.py**: extension wraps 2 user-facing strings in `t('...')` (`_run_tool` not-found message, "No source files found to review.") and places `from bridge.i18n import t` at a different import position.
- **knowledge.py**: extension wraps 11 user-facing strings in `t('...')` (incl. the `recall_project` hint I edited — its message text is IDENTICAL in both copies, only the `t()` wrapper differs) + same import-position difference.
- **No logical/structural drift**: deleted blocks and surviving code are content-identical on both sides. This i18n drift existed before ST-4/ST-5 (documented in prior audits as SHA drift between trees) and is out of scope per plan §5 (mirror parity = "documented drift").
- Note: `extension/mcp-servers/bridge/tools/integrated-myk1yt.py` still contains the old tools but is the user's private variant, outside the delegated file list — untouched.

## Issues Discovered
1. **Pre-existing i18n drift** between root and extension trees (documented above). Recommendation: future B4 i18n sync task should converge the trees.
2. **test_max_tokens.py test names** reference removed tools (`test_find_bugs_truncation` etc.) — they still PASS (they only exercise `truncate_to_tokens`) and the plan explicitly says this file survives unchanged. Cosmetic rename deferred to VP's discretion.
3. Extension tree lacks the root's Korean header-comment wording nuance — irrelevant, both now free of removed names.

## Next Step Recommendations
- VP: proceed to ST-6 (FE contract: package.json commands, `alwaysAllow`, package.nls.* keys) and ST-7 (ux_coordinator output strings — plan §4 guidance text goes there).
- VP: re-run `init_vibezoo.bat` before any smoke test against the deployed `%USERPROFILE%\mcp-servers\vibezoo` copy (plan Decision D4 #5).
- Optional (VP judgment): rename cosmetic test names in test_max_tokens.py.

## Affected File List
| File | Change |
|---|---|
| `mcp-servers/bridge/tools/integrated.py` | 1020 → 250 lines; 3 tools + orphan helpers removed |
| `extension/mcp-servers/bridge/tools/integrated.py` | identical deletions (i18n drift preserved) |
| `mcp-servers/bridge/tools/knowledge.py` | 389 → 297 lines; learn_project removed, hints/docstrings updated |
| `extension/mcp-servers/bridge/tools/knowledge.py` | same (hint via `t()` wrapper) |
| `docs/.../_st45_edit.py`, `_st45_edit_ext_knowledge.py`, `_st45_fix_header.py`, `_st45_verify.py`, `_st45_parity_diff.py` | session working scripts (deletable) |