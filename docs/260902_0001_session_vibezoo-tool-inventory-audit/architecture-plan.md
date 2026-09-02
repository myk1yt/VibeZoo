# Architecture Plan — VibeZoo MCP Bridge Full Tool Cleanup

> Session: `docs/260902_0001_session_vibezoo-tool-inventory-audit/`
> Scope: User-approved A1, A2, A3, B1, B2 (verbatim: "전면 정리 (A1-B3): 집계형 도구(find_bugs, suggest_refactor, generate_docs, learn_project)도 제거하고 프롬프트 조합으로 대체")
> Mode: READ-ONLY analysis. NO implementation. Architecture plan only.

---

## 0. Executive Summary

The VibeZoo MCP bridge ships **39 registered tools**; this cleanup removes **6 tool registrations** (`auto_analyze_whiteboard`, `auto_analyze_after_drop`, `find_bugs`, `suggest_refactor`, `generate_docs`, `learn_project`), deletes **1 dead module** (`github_diver.py` ×2 copies), and purges **1 ghost entry** (`read_project_file`). Final count: **33 tools**.

**Critical deployment fact (resolves the "which copy runs" question):** [`init_vibezoo.bat` L18-21](init_vibezoo.bat:18) copies `extension\mcp-servers\` → `%USERPROFILE%\mcp-servers\vibezoo`, and [`McpConfigService.ts` L252](extension/src/mcp/McpConfigService.ts:252) `autoStartCommand` launches from that deployed dir. **The `extension/mcp-servers/` tree is the source-of-truth that actually runs; the root `mcp-servers/` tree is a development mirror.** Prior audit documented SHA drift between them. Both must be edited identically — there is NO codegen/copy script in [`extension/package.json` L417-424](extension/package.json:417) (scripts are only `compile/watch/package/lint/l10n`). Each cleanup edit is therefore applied **twice** (root mirror + extension source).

---

## [1. Technical Specification]

### 1.1 Goals & Core Constraints

| # | Item | Constraint |
|---|------|-----------|
| G1 | Remove deprecated alias `auto_analyze_whiteboard` | Zero callers remain; `_get_whiteboard_state_impl` stays (used by `get_whiteboard_state`) |
| G2 | Delete dead module `github_diver.py` | Both copies; never registered in [`__init__.py` L56-76](mcp-servers/bridge/tools/__init__.py:56) |
| G3 | Purge ghost `read_project_file` | From `list_subagents` JSON + `alwaysAllow` only; no impl exists |
| G4 | B1 merge: `auto_analyze_after_drop` → `analyze_uploaded_file` | Add opt-in dropzone session tracking; preserve `analyze_file()` as core; remove wrapper from `ux_coordinator.py` |
| G5 | B2: remove 4 aggregate tools | Replace with prompt-composition guidance; keep `review_project` (kept per decisions) |
| G6 | Purge all secondary references | `__init__.py` registration is UNCHANGED (modules stay registered; only inner `@mcp.tool` fns removed), `alwaysAllow`, `list_subagents`, extension commands, i18n keys |
| G7 | No two parallel code-mode tasks touch the same file | Both copies handled in ONE delegation per logical change (see §5) |

### 1.2 FE↔BE Data-Flow (removal impact)

```
[VS Code Extension TS]                [Deployed Python Bridge]              [Zoo Code Agent]
  package.json commands        MCP      vibezoo_mcp_bridge.py        SSE      system prompt
  (findBugs/suggestRefactor/  ───►      bridge/tools/__init__.py    ◄───     calls tools by name
   generateDocs/learnProject)  SSE       → register() per module    tools
  McpConfigService.alwaysAllow          integrated.py / knowledge.py /
  list_subagents JSON                   ux_coordinator.py
```

- **FE→BE contract broken by removal:** any TS command/help-text that names a removed tool must be deleted, else the agent is told to call a non-existent tool.
- **BE→Agent contract broken by removal:** `list_subagents` JSON (returned to agent) and `alwaysAllow` (auto-approve list) must drop removed names, else agent attempts unregistered calls.
- **i18n:** bridge `bridge/i18n/translations/*.json` (20 locales) hold `t()` keys whose *source strings* in removed Python functions disappear; extension `package.nls.*.json` (20 locales) hold command titles for the 4 removed command stubs.

### 1.3 Type Definitions Affected

**B1 — `analyze_uploaded_file` signature change** (the only signature change in scope):

```python
# BEFORE [mcp-servers/bridge/tools/file_analyzer.py L346]
def analyze_uploaded_file(file_path: str) -> str

# AFTER
def analyze_uploaded_file(file_path: str, track_dropzone: bool = False) -> str
```

All other removals are whole-function deletions — no signature drift. MCP tool schema for `analyze_uploaded_file` gains one optional boolean; existing single-arg calls remain valid (backward compatible).

---

## [2. Architecture Decisions]

### Decision D1 — B1 merge: parameterize, don't reroute (Option B — Practical)

`auto_analyze_after_drop` (ux_coordinator.py L136-284) is a *workflow superset* of `analyze_uploaded_file`: it (a) writes `dz_session.json` via `_write_dz_session()` [L152], (b) routes by extension to image/code/doc branches, (c) appends "무엇을 해드릴까요?" follow-ups. `analyze_file()` (file_analyzer.py) already implements the full image→SSA→OCR→MiniCPM + doc + code pipeline.

**Decision:** Move ONLY the unique behavior — dropzone session tracking — into `analyze_uploaded_file` as an opt-in flag. Do NOT port the per-extension text scaffolding in ux_coordinator.py L157-284 (it is inferior, duplicated routing that `analyze_file()` already does better).

- **A (Right Way):** Port `_write_dz_session` into `bridge/tools/file_analyzer.py`, add `track_dropzone: bool=False` param to `analyze_uploaded_file` that calls it. Delete `auto_analyze_after_drop` + `auto_analyze_whiteboard` from ux_coordinator.py; `ux_coordinator` tool STAYS. *Effort: M, Risk: 🟢 low, Outcome: single source of session-tracking, wrapper gone.*
- **B:** Same as A but keep `ux_coordinator.py` module importing `_write_dz_session` from file_analyzer (shared helper). *Chosen only if ux_coordinator still needs the helper — it does NOT after both auto_* tools are removed.*
- **C (Staging):** Leave a deprecated `auto_analyze_after_drop` shim calling `analyze_uploaded_file(track_dropzone=True)`. *Rejected — defeats the cleanup; user asked for removal, not another alias (A1 already removes one alias).*

**Chosen: A.** After removal, `_write_dz_session` is referenced ONLY by the deleted `auto_analyze_after_drop`; so the helper MOVES to file_analyzer.py and ux_coordinator.py loses it entirely. Verify no other module imports `_write_dz_session` — grep shows only ux_coordinator.py defines/uses it.

### Decision D2 — B2 aggregates: prompt-composition over MCP tools (Option A)

The four aggregates are pure compositions of surviving tools:

| Removed | Composed Of (all survive) |
|---------|---------------------------|
| `find_bugs` | `extract_patterns` + `review_code` + `search_codebase`("console.log\|debugger") + Crow recall |
| `suggest_refactor` | `map_dependencies` + `extract_patterns` + `analyze_call_graph` |
| `generate_docs` | `reverse_engineer` + `summarize_architecture` + `draw_on_whiteboard` |
| `learn_project` | `summarize_architecture` + `extract_patterns` + `map_dependencies` + Crow ingest (already auto-run at startup by `_auto_learn_project` [knowledge.py L32]) |

**Decision:** Delete the 4 `@mcp.tool` functions; replace with prompt-level guidance (§4). `learn_project`'s *storage* behavior is preserved via the automatic `_auto_learn_project()` deferred thread [knowledge.py L111-120] and the post-install hook [setup.py L1250-1253] — only the *manual MCP entrypoint* is removed. `recall_project` STAYS (decisions.md asymmetry note).

- **A (Right Way):** Full removal + prompt guidance. *Effort: M, Risk: 🟡 medium (agents trained on old names), Outcome: -4 tools, no functional loss.*
- **B:** Keep functions but unregister from MCP (dead code). *Rejected — leaves drift.*
- **C:** Deprecation shims. *Rejected — same alias anti-pattern as A1.*

**Chosen: A.**

### Decision D3 — Dependency analysis: survivors don't import removed code

| Check | Result | Evidence |
|-------|--------|----------|
| Does `review_project` (integrated.py, KEPT) share private helpers with removed `find_bugs`/`suggest_refactor`/`generate_docs`? | They cohabit the same `register()` closure and share module-level helpers (`truncate_to_tokens`, `_run_tool`, `_tool_registry`, `try_crow_ingest`). Removing the 3 inner functions must NOT delete these shared helpers — `review_project` and `test_max_tokens.py` still use them. | [test_max_tokens.py L177-184] imports `truncate_to_tokens` from both scout.py and integrated.py |
| Does anything call `_get_whiteboard_state_impl` besides deprecated tool? | YES — `get_whiteboard_state` [whiteboard.py L1091] is the primary caller. Removing `auto_analyze_whiteboard` is safe; impl stays. | [ux_coordinator.py L300-301], [whiteboard.py L889-890] |
| Does anything import `learn_project`? | Only as MCP tool name in TS/JSON; `_auto_learn_project` is a separate private fn that stays. | [setup.py L1252] imports `_auto_learn_project` (not the tool) |
| Does anything import `github_diver`? | NO — not in `__init__.py` L56-76 import list. Pure dead file. | audit §R4 |
| Does `ux_coordinator` tool reference removed names? | YES — its *output text* suggests `find_bugs`/`suggest_refactor`/`auto_analyze_after_drop`. These are user-facing strings inside the surviving `ux_coordinator` tool → must be edited (not deleted). | [ux_coordinator.py L128, L231-234] |
| intent_detector.py references? | `get_workflow_hints` returns `"next_tool": "auto_analyze_after_drop"` [L402-404] and `"auto_analyze_whiteboard"` [L416-418]. Consumed by surviving `ux_coordinator` tool → must retarget. | [mcp-servers/bridge/intent_detector.py L402-418] |

### Decision D4 — Risks & Edge Cases

1. **Shared-helper deletion (HIGH):** In integrated.py, deleting the 3 removed inner functions must preserve module-level `truncate_to_tokens`, `_run_tool`, `_tool_registry`, `try_crow_ingest`, and the kept `review_project`. *Mitigation: code-mode diff review must show only function-body removals.*
2. **`ux_coordinator` stale suggestions (MED):** Surviving tool would tell agents to call removed tools. *Mitigation: ST-3 edits its output strings (§5).*
3. **`alwaysAllow` dangling names (MED):** McpConfigService would auto-approve non-existent tools → agent runtime errors. *Mitigation: ST-5.*
4. **i18n orphan keys (LOW):** bridge `t()` keys whose only caller was a removed function. Removing them is optional-cosmetic; leaving them is harmless (no runtime cost). *Decision: remove extension `package.nls.*` command titles (mandatory, FE contract); leave bridge `translations/*.json` untouched (out of scope, B4 future sync).*
5. **Deployed copy staleness (HIGH):** Edits land in repo but the running bridge is `%USERPROFILE%\mcp-servers\vibezoo`. *Verification MUST re-run `init_vibezoo.bat` (or manual copy) before smoke test, else the old tools still respond.*

---

## [3. Implementation Plan — Atomic Task Subdivision]

Ordering respects: **no two parallel tasks touch the same file.** Both copies (root `mcp-servers/` + `extension/mcp-servers/`) are edited **within one delegation per file-pair** (not per-copy) to guarantee mirror consistency — a single code-mode agent applies the identical diff to both, avoiding cross-agent merge races.

> Report Folder for all sub-tasks: `docs/260902_0001_session_vibezoo-tool-inventory-audit/`

### Phase 1 — Safe Removals (A1, A2, A3) — sequential, low risk

**ST-1 (A1+A3 partial) — `ux_coordinator.py` ×2 copies** `[code]`
- Files: `mcp-servers/bridge/tools/ux_coordinator.py` + `extension/mcp-servers/bridge/tools/ux_coordinator.py`
- Delete `auto_analyze_whiteboard()` (L286-308).
- Delete `auto_analyze_after_drop()` (L136-284) AND the now-unused `_write_dz_session()` (L21-53) — but see ST-2 ordering note below.
- Prereq: none. **Do ST-1 and ST-2 in the SAME delegation** (both touch ux_coordinator.py + file_analyzer.py is separate). To avoid two tasks on ux_coordinator.py, fold B1's ux-side deletion here.
- Verification: `python -m py_compile` both copies; `cd mcp-servers && python -m pytest tests/test_whiteboard_merge.py -v` → the `TestAutoAnalyzeWhiteboardDeprecated` class (L186-207) will FAIL → that class must be DELETED from `tests/test_whiteboard_merge.py` (both copies) as part of this task.

**ST-2 (B1 core) — `file_analyzer.py` ×2 copies** `[code]` (same delegation as ST-1)
- Files: `mcp-servers/bridge/tools/file_analyzer.py` + `extension/mcp-servers/bridge/tools/file_analyzer.py`
- Add module-level `_write_dz_session(file_path)` (moved verbatim from ux_coordinator.py L21-53; needs `import json, time` and `from bridge.config import DZ_SESSION_FILE`).
- Change signature [L346] → `def analyze_uploaded_file(file_path: str, track_dropzone: bool = False) -> str`; at top, `if track_dropzone: _write_dz_session(file_path)`; body still `return analyze_file(file_path)`.
- Prereq: none (paired with ST-1).
- Verification: `python -c "import bridge.tools.file_analyzer"` both roots; call signature introspection.

**ST-3 (A2 + A3 ghost) — dead file + bridge JSON + intent hints** `[code]`
- Files: DELETE `mcp-servers/bridge/tools/github_diver.py` + `extension/mcp-servers/bridge/tools/github_diver.py` (Recycle Bin per guardrails).
- Edit `mcp-servers/vibezoo_mcp_bridge.py` + `extension/mcp-servers/vibezoo_mcp_bridge.py`: remove `"read_project_file"` from Editor entry [L64]; remove `"find_bugs", "suggest_refactor", "generate_docs"` from Integrated entry [L58] (keep `review_project`); remove `"learn_project"` from Knowledge entry [L60] (keep `recall_project`); remove the UX auto_* names if present.
- Edit `mcp-servers/bridge/intent_detector.py` + extension copy: retarget/remove `"next_tool": "auto_analyze_after_drop"` [L402-404] → `"analyze_uploaded_file"`; remove `"next_tool": "auto_analyze_whiteboard"` [L416-418] → `"get_whiteboard_state"`.
- Prereq: none. Independent of ST-1/ST-2 (different files).
- Verification: `python -m py_compile` both bridge entry files; grep for `read_project_file|github_diver|explore_github` returns 0 in `mcp-servers/`.

### Phase 2 — Aggregate Removal (B2) — depends on Phase 1 completing

**ST-4 (B2) — `integrated.py` ×2 copies** `[code]`
- Files: `mcp-servers/bridge/tools/integrated.py` + `extension/mcp-servers/bridge/tools/integrated.py`
- Delete inner `@mcp.tool def find_bugs` (L526+), `suggest_refactor` (L739+), `generate_docs` (L868+). KEEP `review_project`, `truncate_to_tokens`, `_run_tool`, `_tool_registry`, `try_crow_ingest`.
- Update module docstring L2 (remove the 3 names).
- Prereq: ST-1..ST-3 (ordering only; no file overlap with ST-4).
- Verification: `python -c "import bridge.tools.integrated"`; `cd mcp-servers && python -m pytest tests/test_max_tokens.py -v` (the `test_find_bugs/suggest_refactor/generate_docs_truncation` tests still PASS — they only test the shared `truncate_to_tokens` helper).

**ST-5 (B2) — `knowledge.py` ×2 copies** `[code]`
- Files: `mcp-servers/bridge/tools/knowledge.py` + `extension/mcp-servers/bridge/tools/knowledge.py`
- Delete inner `@mcp.tool def learn_project` (L124-~215). KEEP `_auto_learn_project` (L32), `register()` auto-schedule (L111-120), `recall_project`, `learn_preference`, `get_preferences`.
- Fix `recall_project` hint text [L243] "Run `learn_project()` first" → reference auto-learn.
- Prereq: ST-4 done (same logical phase, different file — can run parallel with ST-4).
- Verification: `python -c "import bridge.tools.knowledge"`.

### Phase 3 — FE Contract + Prompt Guidance — depends on Phase 2

**ST-6 (B2 FE + A3 FE) — extension TS + package.json + i18n** `[code]`
- Files: `extension/src/extension.ts`, `extension/package.json`, `extension/package.nls.json` + 19 locale variants, `extension/src/mcp/McpConfigService.ts`
- extension.ts: delete command registrations `vibezoo.explainCode`? NO — explainCode is KEPT. Delete only the stubs pointing to removed tools: `vibezoo.learnProject` [L697-701]. (findBugs/suggestRefactor/generateDocs have NO extension.ts stubs — they exist only as package.json command/menu declarations.)
- package.json: remove command entries `vibezoo.findBugs`, `vibezoo.suggestRefactor`, `vibezoo.generateDocs`, `vibezoo.learnProject` [L73-84, L121-124]; remove their `editor/context` [L382-395] and `commandPalette` [L402-413] menu entries.
- McpConfigService.ts `alwaysAllow` [L228-241]: remove `'find_bugs','suggest_refactor','generate_docs','learn_project','read_project_file','auto_analyze_after_drop','auto_analyze_whiteboard'`. KEEP all others.
- package.nls.*.json (20 files): remove keys `vibezoo.findBugs.title`, `vibezoo.suggestRefactor.title`, `vibezoo.generateDocs.title`, `vibezoo.learnProject.title`.
- Prereq: ST-4, ST-5.
- Verification: `cd extension && npx tsc --noEmit`; `npm run compile`.

**ST-7 (ux_coordinator output strings + prompt guidance) — `ux_coordinator.py` suggestions** `[code]`
- Files: `mcp-servers/bridge/tools/ux_coordinator.py` + extension copy
- Edit surviving `ux_coordinator` tool output [L128, L231-234]: replace `find_bugs`/`suggest_refactor` suggestions with prompt-composition text (§4); replace `auto_analyze_after_drop(...)` suggestion with `analyze_uploaded_file(..., track_dropzone=True)`.
- Prereq: ST-1 (same file — must be sequential after ST-1, NOT parallel).
- Verification: `python -m py_compile` both.

**ST-8 — Documentation sync** `[code-light]`
- Files: `docs/PROJECT_CONTEXT.md` L472-477, `docs/PROJECT_CONTEXT-myk1yt.md` L472-477, `README.md` L101, L138, L177, L260-262 — update tool counts (39→33) and remove deprecated/removed names.
- Prereq: all above.
- Verification: none (docs only).

---

## [4. Prompt-Composition Replacement Guidance]

Insert into agent-facing mode/prompt context (VP system prompt / `.roo` mode files) — NOTE: grep of `.roo/` returned **0 matches** for removed tool names, so no existing prompt file instructs agents to call them. This guidance is *added* to the surviving tool descriptions and `ux_coordinator` output instead:

- **find_bugs →** "To hunt bugs: (1) `extract_patterns(target_path)` for AST anti-patterns, (2) `search_codebase(query='console.log|debugger', mode='exact')` for debug leftovers, (3) `review_code(file)` on each suspect file. Synthesize findings yourself."
- **suggest_refactor →** "To plan refactoring: (1) `map_dependencies(target_path)` for coupling/cycles, (2) `analyze_call_graph(target_path)` for fan-in/out, (3) `extract_patterns(target_path)` for duplication. Rank by cycle-breaking impact."
- **generate_docs →** "To document: (1) `summarize_architecture(target_path)` for the overview, (2) `reverse_engineer(target_path, output_format='markdown'|'openapi'|'mermaid')` for API/ERD, (3) `draw_on_whiteboard(...)` to render the diagram."
- **learn_project →** "Project knowledge is captured automatically at bridge startup and after `vibezoo_setup`. To force a refresh, run `summarize_architecture` + `extract_patterns` + `map_dependencies` and note results; retrieval is via `recall_project()`."

---

## [5. Verification Plan]

| Phase | Command | Pass Criteria |
|-------|---------|---------------|
| Pre-flight | Re-deploy: `init_vibezoo.bat` (or `xcopy extension\mcp-servers %USERPROFILE%\mcp-servers\vibezoo /E /I /Y`) | Running bridge = edited source |
| ST-1/2 | `python -m py_compile mcp-servers\bridge\tools\ux_coordinator.py mcp-servers\bridge\tools\file_analyzer.py` (+ extension copies) | exit 0 |
| ST-1/2 | `cd mcp-servers && python -m pytest tests/test_whiteboard_merge.py -v` | pass AFTER deleting `TestAutoAnalyzeWhiteboardDeprecated` |
| ST-3 | `python -c "import bridge.tools.integrated, bridge.tools.knowledge"` from `mcp-servers/` | OK |
| ST-3 | `search_files "github_diver\|explore_github\|read_project_file" mcp-servers/` | 0 hits |
| ST-4/5 | `cd mcp-servers && python -m pytest tests/ -v` | all pass (no test exercises removed tool logic — confirmed: test_max_tokens only hits shared helper) |
| ST-6 | `cd extension && npm run compile` | tsc exit 0, no dangling command refs |
| Smoke | Launch bridge; call `list_subagents` → tool count 33; call each removed name → MCP "tool not found" | 33 tools; removed names rejected |
| Mirror parity | SHA-256 compare root vs extension copies of each edited file | identical |

**Regression risk:** `ux_coordinator` and `intent_detector` still suggest removed tools if ST-7 is skipped — ST-7 is therefore mandatory, not optional.

---

## Affected File List (consolidated)

**Python (×2 copies each — root + extension):**
- `bridge/tools/ux_coordinator.py` (A1 del, B1 del, ST-7 string edits)
- `bridge/tools/file_analyzer.py` (B1 signature + helper move)
- `bridge/tools/integrated.py` (B2: 3 fns)
- `bridge/tools/knowledge.py` (B2: 1 fn)
- `bridge/tools/github_diver.py` (A2 delete)
- `bridge/intent_detector.py` (retarget hints)
- `vibezoo_mcp_bridge.py` (A3 + B2 list_subagents)
- `tests/test_whiteboard_merge.py` (delete deprecated-alias test class)

**TypeScript / JSON / i18n:**
- `extension/src/extension.ts` (remove learnProject stub)
- `extension/src/mcp/McpConfigService.ts` (alwaysAllow purge)
- `extension/package.json` (commands + menus)
- `extension/package.nls.json` + 19 `package.nls.<locale>.json` (4 title keys each)

**Docs:** `README.md`, `docs/PROJECT_CONTEXT.md`, `docs/PROJECT_CONTEXT-myk1yt.md`

**Out of scope (unchanged):** `bridge/i18n/translations/*.json` (orphan keys harmless; deferred to B4 sync), `mcp-servers/tests/test_max_tokens.py` (tests only shared helper — survives), `.roo/` mode files (no references found).
