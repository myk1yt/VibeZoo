# Code Task Report — Phase 3: ST-6 (extension FE contract purge) + ST-7 (ux_coordinator output strings)

> Session: `docs/260902_0001_session_vibezoo-tool-inventory-audit/`
> Date: 2026-09-02 (Seoul, 17:01)
> Prereqs: ST-1..ST-5 complete (commits 9ddeb79, 0b5d2ce, 568cb64)
> Plan ref: architecture-plan.md §3 ST-6/ST-7, §4 prompt-composition, Decision D4 risks 2/3/4

## Task Summary

Purged all references to the 6 removed MCP tools (`auto_analyze_whiteboard`, `auto_analyze_after_drop`, `find_bugs`, `suggest_refactor`, `generate_docs`, `learn_project`) + ghost `read_project_file` from the extension FE contract layer (TypeScript, package.json commands/menus, 20 nls locale files), and retargeted the stale `auto_analyze_after_drop` suggestion string inside the surviving `ux_coordinator` tool in both Python trees.

## Actions Taken

### ST-6 — Extension TypeScript + package JSON

1. **[`extension/src/mcp/McpConfigService.ts`](extension/src/mcp/McpConfigService.ts:228)** — `alwaysAllow` list: removed all 7 dead names (`'find_bugs'`, `'suggest_refactor'`, `'generate_docs'`, `'learn_project'`, `'read_project_file'`, `'auto_analyze_after_drop'`, `'auto_analyze_whiteboard'`). All other entries preserved verbatim (`review_project`, `recall_project`, `learn_preference`, `get_preferences`, `ux_coordinator`, etc.).
2. **[`extension/src/extension.ts`](extension/src/extension.ts:696)** — deleted the `vibezoo.learnProject` command registration stub (former L696-701, "H." block, including its Korean section comment). Renumbered the following `vibezoo.recallProject` comment `I.` → kept its letter (comment sequence had a pre-existing gap at `H`; left J-Z as-is to stay surgical — only the deleted block's letter was folded). Verified via search: `findBugs`/`suggestRefactor`/`generateDocs` had NO extension.ts stubs (plan-confirmed), and no help-text strings elsewhere in `extension/src/` mention removed names.
3. **[`extension/package.json`](extension/package.json:73)** — removed 4 `contributes.commands` entries (`vibezoo.findBugs`, `vibezoo.suggestRefactor`, `vibezoo.generateDocs` at former L73-84; `vibezoo.learnProject` at former L121-124); removed the 3 `editor/context` menu entries (former L381-395, keeping `vibezoo.reviewProject` group `vibezoo@1`); removed the 3 `commandPalette` `when: "never"` entries (former L402-413, keeping `vibezoo.reviewProject`). NOTE: `vibezoo.learnProject` had NO menu entries (only a command declaration) — confirmed by content search.
4. **nls locale purge** — `docs/260902_0001_session_vibezoo-tool-inventory-audit/_st6_purge_nls.py` (line-surgical single-line key removal, BOM/CRLF-preserving, post-write `json.load` validation). Removed the 4 title keys (`vibezoo.findBugs.title`, `vibezoo.suggestRefactor.title`, `vibezoo.generateDocs.title`, `vibezoo.learnProject.title`) from **all 20 non-fork files**, 4 keys each (80 key removals total):
   `package.nls.json` (default) + locales `ar, bg, cs, de, es, fr, he, hu, it, ja, ko, pl, pt-BR, ru, th, tr, vi, zh-CN, zh-TW`.
   The 20 `package.nls.*-myk1yt.json` fork copies were explicitly skipped (out of scope).
   Residual key occurrences after purge: **0** (script-verified per file).

### ST-7 — ux_coordinator.py output strings (both copies)

5. **[`mcp-servers/bridge/tools/ux_coordinator.py`](mcp-servers/bridge/tools/ux_coordinator.py:86)** — L86 dropzone suggestion retargeted:
   - Before: `` `auto_analyze_after_drop(file_path="{dz_path}")` 호출을 제안합니다. ``
   - After: `` `analyze_uploaded_file(file_path="{dz_path}", track_dropzone=True)` 호출을 제안합니다. ``
6. **[`extension/mcp-servers/bridge/tools/ux_coordinator.py`](extension/mcp-servers/bridge/tools/ux_coordinator.py:86)** — same retarget in the i18n'd copy:
   - Before: `t("Suggest calling `auto_analyze_after_drop(file_path=\"{0}\")`.", dz_path)`
   - After: `t("Suggest calling `analyze_uploaded_file(file_path=\"{0}\", track_dropzone=True)`.", dz_path)`
   Logic/signature unchanged — string only, per scope.
7. **L128 / L231-234 `find_bugs`/`suggest_refactor` suggestions**: confirmed ALREADY REMOVED — those lines belonged to the `auto_analyze_after_drop` wrapper function deleted wholesale in ST-1. Current post-ST-1 file is 93 lines; a full-file scan for `find_bugs|suggest_refactor|generate_docs|learn_project|auto_analyze` returns 0 hits in both copies (see verification #5). The aggregate prompt-composition guidance is therefore delivered through `get_workflow_hints` in [`mcp-servers/bridge/intent_detector.py`](mcp-servers/bridge/intent_detector.py:397) (ST-3-retargeted: `file_share` hint already says "analyze_uploaded_file(file_path, track_dropzone=True)"; `code_analysis` hint recommends surviving `review_code`), which feeds the ux_coordinator output dynamically. No additional §4 text injection point exists in the current 93-line file.

## Verification (actual outputs)

### 1. `cd extension && npx tsc --noEmit` → exit 0 (FE contract gate)
```
Exit code: 0
Output:
TSC_EXIT_0_OK
```

### 2. `cd extension && npm run compile` → success
```
Exit code: 0
Output:
> vibezoo@0.15.1 compile
> tsc -p ./

COMPILE_OK
```
(node_modules present; full compile ran, not just --noEmit.)

### 3. 0-hit contract scan (all of `extension/src/**/*.ts` + `extension/package.json` + non-fork `package.nls*.json`, 49 files)
Pattern: `find_bugs|suggest_refactor|generate_docs|learn_project|read_project_file|auto_analyze_after_drop|auto_analyze_whiteboard|findBugs|suggestRefactor|generateDocs|learnProject`
```
SCANNED 49 FILES -> TOTAL HITS: 0
JSON_VALID_ALL: True
```

### 4. `python -m py_compile` both ux_coordinator copies → exit 0
```
PY_COMPILE_OK: ['mcp-servers/bridge/tools/ux_coordinator.py', 'extension/mcp-servers/bridge/tools/ux_coordinator.py']
```
(via [`_st67_verify.py`](docs/260902_0001_session_vibezoo-tool-inventory-audit/_st67_verify.py), exit 0)

### 5. ux_coordinator residual scan (both copies, pattern `find_bugs|suggest_refactor|generate_docs|learn_project|auto_analyze`)
```
UX_COORDINATOR_RESIDUAL_HITS: 0
```

### 6. JSON validity
`extension/package.json` + all 20 edited nls files parse with `json.load` → `JSON_VALID_ALL: True`. Each nls file was additionally re-parsed by the purge script immediately after write (80 keys removed, zero parse errors).

## Issues Discovered (non-blocking, for VP routing)

1. **`bridge/tool_context.py` dead manifests (both trees)** — [`mcp-servers/bridge/tool_context.py`](mcp-servers/bridge/tool_context.py:61) still defines `MANIFEST_FIND_BUGS`/`MANIFEST_SUGGEST_REFACTOR`, the `TOOL_MANIFESTS` registry entries, `make_find_bugs_context()`/`make_suggest_refactor_context()` factories, and `__all__` exports. Their only MCP-tool callers (`find_bugs`/`suggest_refactor` in integrated.py) were deleted in ST-4. NOT in ST-6/ST-7 scope (not in the plan's Affected File List). No runtime breakage — the module imports cleanly and nothing imports the removed factories. Recommend a follow-up dead-code ticket.
2. **Stale docstring references in `whiteboard.py` (both trees)** — [`extension/mcp-servers/bridge/tools/whiteboard.py`](extension/mcp-servers/bridge/tools/whiteboard.py:872) L872/L890/L894/L1035/L1095 mention `auto_analyze_whiteboard()`/`auto_analyze_after_drop()` in historical/deprecation docstrings. Cosmetic only (plan D4.4 treats such orphans as harmless); no callable path. `file_analyzer.py` L19 similarly references the removal in a changelog comment — that one is accurate history, keep.
3. **`integrated-myk1yt.py` fork copy untouched** — still registers `find_bugs`/`suggest_refactor`/`generate_docs`. Confirmed out of scope (myk1yt fork copies excluded). If that fork ever gets merged, ST-4/ST-6 must be re-applied to it.
4. **Mirror SHA note (ST-7 pair)** — root vs extension `ux_coordinator.py` intentionally differ: the extension copy is i18n'd (`t()` calls) while the root mirror uses raw Korean literals. This is pre-existing structural drift, not edit drift; both received the identical semantic retarget at L86.
5. **Deployment reminder (plan D4.5)** — running bridge is `%USERPROFILE%\mcp-servers\vibezoo`; VP must re-run `init_vibezoo.bat` (or equivalent copy) before smoke-testing FE/BE contract, else old TS bundle + old Python still serve removed commands/tools.

## Post-Implementation Verification

1. Checklist items: all 6 ST-6 sub-edits + ST-7 ×2 copies done ✅
2. Expected deliverable (no FE surface references any removed tool; ux_coordinator suggests only surviving tools) matches actual ✅
3. Impact analysis: `review_project`/`recall_project`/`ux_coordinator` registrations untouched; `vibezoo.reviewProject` command + menu + nls keys preserved; no signature/logic changes ✅
4. Original intent (A1-B3 full cleanup, FE contract purge) fulfilled for the ST-6/ST-7 scope ✅

## Affected File List (25 files)

| File | Change |
|------|--------|
| `extension/src/mcp/McpConfigService.ts` | alwaysAllow: −7 dead names |
| `extension/src/extension.ts` | −1 command stub (`vibezoo.learnProject`, L696-701) + comment renumber |
| `extension/package.json` | −4 commands, −3 editor/context entries, −3 commandPalette entries |
| `extension/package.nls.json` + 19 locale files | −4 title keys each (80 total). Locales with all 4 keys: ar, bg, cs, de, es, fr, he, hu, it, ja, ko, pl, pt-BR, ru, th, tr, vi, zh-CN, zh-TW (default `package.nls.json` included). 20 `-myk1yt` forks: untouched |
| `mcp-servers/bridge/tools/ux_coordinator.py` | L86 suggestion → `analyze_uploaded_file(..., track_dropzone=True)` |
| `extension/mcp-servers/bridge/tools/ux_coordinator.py` | same retarget (i18n `t()` form) |
| `docs/.../_st6_purge_nls.py`, `docs/.../_st67_verify.py` | helper scripts (evidence, retained) |

## Next Step Recommendations

1. VP: commit ST-6+ST-7 (no git actions taken here, per rules).
2. VP: re-run `init_vibezoo.bat` redeploy + smoke test (`list_subagents` → 33 tools; dropped-command palette check — `VibeZoo: Find Bugs` etc. must be gone in an English-locale VS Code window).
3. ST-8 (docs sync: 39→33 counts in README/PROJECT_CONTEXT) remains per plan.
4. Optional follow-up ticket: `tool_context.py` dead manifests (Issue 1).
