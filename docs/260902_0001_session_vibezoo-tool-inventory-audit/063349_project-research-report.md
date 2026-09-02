# Project Research Report: VibeZoo MCP Tool Inventory Audit

## Task Summary
READ-ONLY audit of all MCP tools exposed by the VibeZoo bridge server. Exact tool count extraction, full inventory with source mapping, redundancy analysis, and usage cross-reference for KEEP/REVIEW/REMOVE classification.

## [1] Exact Total Count

**39 tools** are registered via `@mcp.tool` across 16 Python source files.

Ground truth source: [`mcp-servers/bridge/tools/__init__.py`](mcp-servers/bridge/tools/__init__.py:19) calls `register(mcp)` on 16 modules. Each module's `register()` function contains `@mcp.tool`-decorated functions.

| Count Source | Value | Notes |
|---|---|---|
| Actual `@mcp.tool` registrations | **39** | Verified against source code |
| VP runtime system prompt list | ~40 | Includes `read_project_file` which is NOT registered (ghost entry) |
| `list_subagents` JSON in bridge | 40 entries (39 unique) | `read_project_file` listed but never implemented |
| Previous docs claims | 38-40 | Varies by session; closest is 38 from `093000_project-research-report.md` |

### Ghost Entry
`read_project_file` appears in [`vibezoo_mcp_bridge.py` L64](mcp-servers/vibezoo_mcp_bridge.py:64) (`list_subagents` JSON) and in [`McpConfigService.ts` L237](extension/src/mcp/McpConfigService.ts:237) (`alwaysAllow` list), but **has no `@mcp.tool` registration anywhere**. No function definition exists in any tool file.

---

## [2] Full Inventory Table

| # | Tool Name | Purpose (one-line) | Source File | Register Module | Line |
|---|---|---|---|---|---|
| 1 | `vibezoo_setup` | One-call VibeZoo installer (pip, system tools, MCP config, Zoo config, custom modes, model download) | [`setup.py`](mcp-servers/bridge/tools/setup.py:1166) | setup.py | L1166 |
| 2 | `search_codebase` | Code search with tree-sitter AST + regex fallback, fuzzy/semantic modes | [`scout.py`](mcp-servers/bridge/tools/scout.py:737) | scout.py | L737 |
| 3 | `find_references` | Find all references to a symbol (definitions vs usages, call chain) | [`scout.py`](mcp-servers/bridge/tools/scout.py:756) | scout.py | L756 |
| 4 | `summarize_architecture` | Project architecture analysis with dependency map + git trend (summary/full modes) | [`scout.py`](mcp-servers/bridge/tools/scout.py:767) | scout.py | L767 |
| 5 | `review_code` | Single-file code review with AST quality issue detection (multi-language) | [`reviewer.py`](mcp-servers/bridge/tools/reviewer.py:336) | reviewer.py | L336 |
| 6 | `analyze_call_graph` | Function call graph with fan-in/fan-out, dead code detection | [`deep_analyzer.py`](mcp-servers/bridge/tools/deep_analyzer.py:518) | deep_analyzer.py | L518 |
| 7 | `map_dependencies` | Import-based dependency map with circular dependency detection | [`deep_analyzer.py`](mcp-servers/bridge/tools/deep_analyzer.py:674) | deep_analyzer.py | L674 |
| 8 | `extract_patterns` | AST-based recurring code pattern extraction (anti-patterns detection) | [`deep_analyzer.py`](mcp-servers/bridge/tools/deep_analyzer.py:684) | deep_analyzer.py | L684 |
| 9 | `reverse_engineer` | Auto-generate architecture docs, API specs, ERD from codebase | [`deep_analyzer.py`](mcp-servers/bridge/tools/deep_analyzer.py:700) | deep_analyzer.py | L700 |
| 10 | `generate_tests` | Unit test generation from source file with AST-aware boundary/branch analysis | [`tester.py`](mcp-servers/bridge/tools/tester.py:38) | tester.py | L38 |
| 11 | `analyze_coverage` | Test coverage analysis (file-ratio + optional vitest/pytest runner) | [`tester.py`](mcp-servers/bridge/tools/tester.py:310) | tester.py | L310 |
| 12 | `analyze_uploaded_file` | Universal file analysis (image SSA+OCR+MiniCPM, code, docs, PDF) | [`file_analyzer.py`](mcp-servers/bridge/tools/file_analyzer.py:346) | file_analyzer.py | L346 |
| 13 | `check_uploaded_files` | List recently uploaded dropzone files (session-filtered) | [`whiteboard.py`](mcp-servers/bridge/tools/whiteboard.py:971) | whiteboard.py | L971 |
| 14 | `capture_screen` | Screen capture or open dropzone/file-picker for visual analysis | [`whiteboard.py`](mcp-servers/bridge/tools/whiteboard.py:1030) | whiteboard.py | L1030 |
| 15 | `draw_on_whiteboard` | Draw shapes on Fabric.js whiteboard via JSON commands | [`whiteboard.py`](mcp-servers/bridge/tools/whiteboard.py:1054) | whiteboard.py | L1054 |
| 16 | `get_whiteboard_state` | Read whiteboard state (Fabric.js→text/Mermaid, optional analyze mode) | [`whiteboard.py`](mcp-servers/bridge/tools/whiteboard.py:1091) | whiteboard.py | L1091 |
| 17 | `auto_fix_status` | Query active auto-fix session status + Crow Memory past fixes | [`fix_loop.py`](mcp-servers/bridge/tools/fix_loop.py:134) | fix_loop.py | L134 |
| 18 | `retry_build` | Re-run build, extract errors/warnings, track fix attempts | [`fix_loop.py`](mcp-servers/bridge/tools/fix_loop.py:178) | fix_loop.py | L178 |
| 19 | `check_intervention` | Check whiteboard annotations + pending chat messages before fix loop | [`fix_loop.py`](mcp-servers/bridge/tools/fix_loop.py:301) | fix_loop.py | L301 |
| 20 | `review_project` | Whole-project quality check (grades A-F, ESLint, cyclomatic complexity) | [`integrated.py`](mcp-servers/bridge/tools/integrated.py:100) | integrated.py | ~L100+ |
| 21 | `find_bugs` | Bug search across project (builds on extract_patterns + review_code) | [`integrated.py`](mcp-servers/bridge/tools/integrated.py:1) | integrated.py | - |
| 22 | `suggest_refactor` | Refactoring suggestions (builds on map_dependencies + extract_patterns + call graph) | [`integrated.py`](mcp-servers/bridge/tools/integrated.py:1) | integrated.py | - |
| 23 | `generate_docs` | Auto-generate docs (builds on reverse_engineer + summarize_architecture + whiteboard) | [`integrated.py`](mcp-servers/bridge/tools/integrated.py:1) | integrated.py | - |
| 24 | `explain_code` | AST-aware code explanation at specific line (context, blame, call graph) | [`analysis.py`](mcp-servers/bridge/tools/analysis.py:188) | analysis.py | L188 |
| 25 | `analyze_changes` | Git diff analysis with change classification + Crow context | [`analysis.py`](mcp-servers/bridge/tools/analysis.py:425) | analysis.py | L425 |
| 26 | `review_pr` | PR review (diff + per-file review + rollback risk + dependency analysis) | [`analysis.py`](mcp-servers/bridge/tools/analysis.py:526) | analysis.py | L526 |
| 27 | `refactor_across_files` | Multi-file AST-aware find-and-replace with proposal/apply modes | [`analysis.py`](mcp-servers/bridge/tools/analysis.py:697) | analysis.py | L697 |
| 28 | `learn_project` | Ingest architecture/patterns/deps into Crow Memory for cross-session context | [`knowledge.py`](mcp-servers/bridge/tools/knowledge.py:124) | knowledge.py | L124 |
| 29 | `recall_project` | Recall stored project knowledge from Crow arch/style/life_context registers | [`knowledge.py`](mcp-servers/bridge/tools/knowledge.py:216) | knowledge.py | L216 |
| 30 | `learn_preference` | Save user coding preferences to local file + Crow Memory | [`knowledge.py`](mcp-servers/bridge/tools/knowledge.py:271) | knowledge.py | L271 |
| 31 | `get_preferences` | Retrieve saved user preferences from local file + Crow Memory | [`knowledge.py`](mcp-servers/bridge/tools/knowledge.py:333) | knowledge.py | L333 |
| 32 | `fetch_page` | Fetch URL and convert HTML to Markdown (stdlib only) | [`web.py`](mcp-servers/bridge/tools/web.py:250) | web.py | L250 |
| 33 | `web_search` | Web search via Exa neural / DuckDuckGo fallback | [`web.py`](mcp-servers/bridge/tools/web.py:316) | web.py | L316 |
| 34 | `aggregate_spatial_pixels` | SSA v3 image analysis + optional OCR (OpenCV + Tesseract/PaddleOCR) | [`ssa.py`](mcp-servers/bridge/tools/ssa.py:643) | ssa.py | L643 |
| 35 | `apply_patch` | AI-safe transactional SEARCH/REPLACE patch with fuzzy match + ellipsis detection | [`editor.py`](mcp-servers/bridge/tools/editor.py:609) | editor.py | L609 |
| 36 | `ux_coordinator` | Intent detection + tool chain suggestion routing | [`ux_coordinator.py`](mcp-servers/bridge/tools/ux_coordinator.py:61) | ux_coordinator.py | L61 |
| 37 | `auto_analyze_after_drop` | Post-dropzone file analysis pipeline (image→SSA+OCR+MiniCPM, code, docs) | [`ux_coordinator.py`](mcp-servers/bridge/tools/ux_coordinator.py:137) | ux_coordinator.py | L137 |
| 38 | `auto_analyze_whiteboard` | **[DEPRECATED]** Alias for `get_whiteboard_state(analyze=True)` | [`ux_coordinator.py`](mcp-servers/bridge/tools/ux_coordinator.py:287) | ux_coordinator.py | L287 |
| 39 | `vibezoo_feedback` | Agent-to-user feedback submission (missing_tool, repetitive_task, bug_report) | [`feedback.py`](mcp-servers/bridge/tools/feedback.py:9) | feedback.py | L9 |

### Dead/Unregistered Files
| File | Status | Evidence |
|---|---|---|
| [`github_diver.py`](mcp-servers/bridge/tools/github_diver.py:1) | **Dead code** — not imported in `__init__.py` L56-76 | Contains `explore_github` function but never registered. Previous session `112000_code-delete-implement-report.md` claimed deletion but file persists. |
| `read_project_file` | **Ghost entry** — listed in `list_subagents` and `alwaysAllow` but no function definition exists anywhere | [`vibezoo_mcp_bridge.py` L64](mcp-servers/vibezoo_mcp_bridge.py:64), [`McpConfigService.ts` L237](extension/src/mcp/McpConfigService.ts:237) |

---

## [3] Redundancy & Overlap Analysis

### R1: Deprecated Tool (confirmed REMOVE-candidate)

| Tool | Issue | Evidence |
|---|---|---|
| `auto_analyze_whiteboard` #38 | Self-documented `[DEPRECATED]` at [`ux_coordinator.py` L288](mcp-servers/bridge/tools/ux_coordinator.py:288). Calls `get_whiteboard_state(analyze=True)` internally. Plan ADR-3 in [`architecture-plan.md` L345](plans/../docs/archive/260725/260725_0001_session_tools-ecosystem-overhaul/architecture-plan.md:345) explicitly schedules removal after one release. | Not referenced outside bridge/UX coordinator. |

### R2: Aggregate Tools vs Component Tools (REVIEW candidates)

| Aggregate Tool | Delegates To | Overlap Type |
|---|---|---|
| `review_project` #20 | `review_code` (internally) + `_review_project_core` | REVIEW: While it calls `_review_project_core` (not `review_code`), the quality check overlap is significant. `review_code` does single-file AST review; `review_project` does project-wide quality grades. **Different scope** — keep both but note overlap. |
| `find_bugs` #21 | `extract_patterns` + `review_code` | REVIEW: Combines pattern extraction with review. Purpose is convenience aggregation. |
| `suggest_refactor` #22 | `map_dependencies` + `extract_patterns` + `analyze_call_graph` | REVIEW: Pure aggregator of 3 existing tools. Could be a prompt-level composition instead. |
| `generate_docs` #23 | `reverse_engineer` + `summarize_architecture` + whiteboard drawing | REVIEW: Combines code-to-docs generation. Similar to `reverse_engineer` alone. |
| `review_pr` #26 | `analyze_changes` + `review_code` (per-file) + dependency analysis | REVIEW: Adds rollback risk + dependency cross-refs on top of per-file review. Higher value than pure aggregator. |
| `learn_project` #28 | `summarize_architecture` + `extract_patterns` + `map_dependencies` + Crow ingest | REVIEW: Pure composition + Crow storage. Could be agent-level prompt instead. |
| `auto_analyze_after_drop` #37 | `analyze_uploaded_file` + file-type routing + MiniCPM | REVIEW: Overlaps with `analyze_uploaded_file` (#12). The latter handles the full image/code/doc pipeline. `auto_analyze_after_drop` adds dropzone session tracking + suggestion prompts. |

### R3: Functional Overlap Pairs

| Tool A | Tool B | Overlap | Recommendation |
|---|---|---|---|
| `analyze_uploaded_file` #12 | `auto_analyze_after_drop` #37 | Significant: both run same SSA→OCR→MiniCPM pipeline for images | REVIEW: Consider merging; `auto_analyze_after_drop` adds session tracking but could be a parameter on `analyze_uploaded_file` |
| `fetch_page` #32 | `web_search` #33 | Low: `fetch_page` is a URL fetcher (GET → HTML→MD); `web_search` is a search engine | KEEP: Different purposes (fetch vs search), complementary |
| `apply_patch` #35 | platform-native `apply_diff` | Medium: both do SEARCH/REPLACE patching | REVIEW: `apply_patch` adds fuzzy match, ellipsis detection, auto-file-discovery, transactional rollback. Platform `apply_diff` is strict exact-match. **Complementary, not duplicate** |
| `get_whiteboard_state` #16 | `auto_analyze_whiteboard` #38 | 100%: latter is a deprecated alias | REMOVE `auto_analyze_whiteboard` |

### R4: `github_diver.py` Dead Code

[`github_diver.py`](mcp-servers/bridge/tools/github_diver.py:1) contains `explore_github` function (162 lines) that is **never registered** in `__init__.py`. The file is imported nowhere. It duplicates functionality now handled by the GitHub MCP server (`mcp--github`). Previous deletion report ([`112000_code-delete-implement-report.md`](docs/260830_0001_session_reinstall-recovery-and-quality/112000_code-delete-implement-report.md:12)) claimed deletion but the file persists in both `mcp-servers/bridge/tools/` and `extension/mcp-servers/bridge/tools/`.

---

## [4] Usage Cross-Reference (KEEP/REVIEW/REMOVE Classification)

### Evidence Sources
- [`extension/src/McpConfigService.ts` L228-241](extension/src/mcp/McpConfigService.ts:228): `alwaysAllow` list (tools auto-approved without user confirmation)
- [`extension/src/extension.ts` L547-721](extension/src/extension.ts:547): VS Code command registrations referencing MCP tools
- [`extension/src/visual/VisualVibePanels.ts` L213-215](extension/src/visual/VisualVibePanels.ts:213): Whiteboard file watcher for `draw_on_whiteboard`
- [`extension/src/orchestra/FixLoopManager.ts` L148-195](extension/src/orchestra/FixLoopManager.ts:148): Fix loop state machine referencing `auto_fix_status`, `retry_build`

### Classification Table

| # | Tool | Verdict | Evidence |
|---|---|---|---|
| 1 | `vibezoo_setup` | ✅ **KEEP** | `alwaysAllow` L239; Extension init depends on it |
| 2 | `search_codebase` | ✅ **KEEP** | `alwaysAllow` L229; extension.ts help text L548; core Scout tool |
| 3 | `find_references` | ✅ **KEEP** | `alwaysAllow` L229; core Scout tool |
| 4 | `summarize_architecture` | ✅ **KEEP** | `alwaysAllow` L229; extension.ts L549; used by `learn_project` |
| 5 | `review_code` | ✅ **KEEP** | `alwaysAllow` L229; extension.ts L549; core Reviewer tool |
| 6 | `analyze_call_graph` | ✅ **KEEP** | `alwaysAllow` L231; core DeepAnalyzer tool |
| 7 | `map_dependencies` | ✅ **KEEP** | `alwaysAllow` L231; extension.ts L550; used by `learn_project` |
| 8 | `extract_patterns` | ✅ **KEEP** | `alwaysAllow` L231; core DeepAnalyzer tool |
| 9 | `reverse_engineer` | ✅ **KEEP** | `alwaysAllow` L232; core DeepAnalyzer tool |
| 10 | `generate_tests` | ⚠️ **REVIEW** | `alwaysAllow` L231; extension.ts L670 help text references it. Previous audit (`112000`) marked for deletion but not executed. LLM-dependent quality |
| 11 | `analyze_coverage` | ⚠️ **REVIEW** | `alwaysAllow` L232; previous audit marked for deletion but not executed. Basic file-ratio analysis only |
| 12 | `analyze_uploaded_file` | ✅ **KEEP** | `alwaysAllow` L232; core file analysis pipeline |
| 13 | `check_uploaded_files` | ✅ **KEEP** | `alwaysAllow` L232; dropzone workflow essential |
| 14 | `capture_screen` | ✅ **KEEP** | `alwaysAllow` L240; dropzone + visual analysis essential |
| 15 | `draw_on_whiteboard` | ✅ **KEEP** | `alwaysAllow` L233; extension.ts L551; VisualVibePanels.ts watcher |
| 16 | `get_whiteboard_state` | ✅ **KEEP** | `alwaysAllow` L233; replaces deprecated `auto_analyze_whiteboard` |
| 17 | `auto_fix_status` | ✅ **KEEP** | `alwaysAllow` L234; FixLoopManager.ts L149 depends on it |
| 18 | `retry_build` | ✅ **KEEP** | `alwaysAllow` L234; FixLoopManager.ts L160 depends on it |
| 19 | `check_intervention` | ✅ **KEEP** | `alwaysAllow` L234; fix loop pre-check essential |
| 20 | `review_project` | ⚠️ **REVIEW** | `alwaysAllow` L235; aggregate of quality checks. Consider whether `review_code` covers enough |
| 21 | `find_bugs` | ⚠️ **REVIEW** | `alwaysAllow` L235; aggregate tool. Previous audit marked for deletion but not executed |
| 22 | `suggest_refactor` | ⚠️ **REVIEW** | `alwaysAllow` L235; pure aggregation of 3 existing tools |
| 23 | `generate_docs` | ⚠️ **REVIEW** | `alwaysAllow` L235; overlap with `reverse_engineer` |
| 24 | `explain_code` | ⚠️ **REVIEW** | `alwaysAllow` L230; extension.ts L670 command. Previous audit marked for deletion but not executed |
| 25 | `analyze_changes` | ⚠️ **REVIEW** | `alwaysAllow` L230; extension.ts L677 command. Previous audit marked for deletion but not executed |
| 26 | `review_pr` | ✅ **KEEP** | `alwaysAllow` L230; extension.ts L684; adds rollback risk + dependency analysis beyond simple aggregation |
| 27 | `refactor_across_files` | ✅ **KEEP** | `alwaysAllow` L230; extension.ts L691; unique AST-aware rename capability |
| 28 | `learn_project` | ⚠️ **REVIEW** | `alwaysAllow` L236; extension.ts L698; auto-learn on startup makes manual call less necessary |
| 29 | `recall_project` | ⚠️ **REVIEW** | `alwaysAllow` L236; extension.ts L705; auto-learn makes manual recall less necessary |
| 30 | `learn_preference` | ✅ **KEEP** | `alwaysAllow` L236; extension.ts L712; unique preference storage |
| 31 | `get_preferences` | ✅ **KEEP** | `alwaysAllow` L237; extension.ts L719; unique preference retrieval |
| 32 | `fetch_page` | ✅ **KEEP** | `alwaysAllow` L240; unique URL→Markdown fetcher |
| 33 | `web_search` | ✅ **KEEP** | `alwaysAllow` L240; unique search engine with Exa/DDG |
| 34 | `aggregate_spatial_pixels` | ✅ **KEEP** | `alwaysAllow` L240; unique SSA image analysis |
| 35 | `apply_patch` | ⚠️ **REVIEW** | `alwaysAllow` L237; platform has native `apply_diff`. Previous audit marked for deletion but not executed. Adds fuzzy match + ellipsis + auto-file-detect |
| 36 | `ux_coordinator` | ⚠️ **REVIEW** | `alwaysAllow` L238; intent routing can be prompt-level. Previous audit marked for deletion but not executed |
| 37 | `auto_analyze_after_drop` | ⚠️ **REVIEW** | `alwaysAllow` L238; overlaps with `analyze_uploaded_file`. Previous audit marked for deletion but not executed |
| 38 | `auto_analyze_whiteboard` | 🔴 **REMOVE** | `alwaysAllow` L238; self-deprecated L288; redundant with `get_whiteboard_state(analyze=True)` |
| 39 | `vibezoo_feedback` | ✅ **KEEP** | `alwaysAllow` L239; unique agent→user feedback channel |

### Summary Counts

| Verdict | Count | Tools |
|---|---|---|
| ✅ KEEP | **23** | Core analysis, whiteboard, fix loop, knowledge, web, SSA, setup, feedback |
| ⚠️ REVIEW | **15** | Aggregate tools, deprecated candidates, overlap candidates, previous-delete-not-executed |
| 🔴 REMOVE | **1** | `auto_analyze_whiteboard` (deprecated alias) |
| 💀 Dead Code | **1 file** | `github_diver.py` (unregistered, unused) |
| 👻 Ghost Entry | **1** | `read_project_file` (listed in configs, never implemented) |

---

## [5] Recommended Cleanup Actions

### Immediate (safe, no behavior change)

| Action | Target | Effort | Risk |
|---|---|---|---|
| A1: Delete `auto_analyze_whiteboard` | Remove from [`ux_coordinator.py` L286-308](mcp-servers/bridge/tools/ux_coordinator.py:286); remove from `alwaysAllow` and `list_subagents` | Small | 🟢 Low — deprecated, successor exists |
| A2: Delete `github_diver.py` | Delete file from both `mcp-servers/` and `extension/mcp-servers/`; remove any i18n references | Small | 🟢 Low — dead code, never registered |
| A3: Remove `read_project_file` ghost entry | Remove from [`vibezoo_mcp_bridge.py` L64](mcp-servers/vibezoo_mcp_bridge.py:64) `list_subagents` and [`McpConfigService.ts` L237](extension/src/mcp/McpConfigService.ts:237) `alwaysAllow` | Trivial | 🟢 Low — no implementation exists |

### Follow-up (needs user decision)

| Action | Target | Effort | Risk |
|---|---|---|---|
| B1: Merge `auto_analyze_after_drop` into `analyze_uploaded_file` | Add dropzone session tracking as parameter; remove `ux_coordinator.py` L136-284 | Medium | 🟡 Medium — agent prompts may reference old name |
| B2: Evaluate aggregate tools | `find_bugs`, `suggest_refactor`, `generate_docs`, `learn_project` — decide if prompt-level composition suffices | Medium | 🟡 Medium — may break existing agent workflows |
| B3: Evaluate `ux_coordinator` | Intent routing may work as agent prompt instead of MCP tool | Medium | 🟡 Medium — complex intent detection logic |
| B4: Sync extension/mcp-servers/ | Many files have `-myk1yt` variants and drift; full sync audit needed | Large | 🟡 Medium — 67 files, prior audit showed SHA mismatches |

### Not Recommended (KEEP as-is)

- `apply_patch` (#35): Despite platform overlap, adds unique fuzzy match + ellipsis detection + transactional rollback
- `review_project` (#20): Different scope (project-wide quality grades) from `review_code` (single-file review)
- `review_pr` (#26): Adds rollback risk + cross-file dependency analysis beyond aggregation
- `refactor_across_files` (#27): Unique AST-aware rename across files

---

## Issues Discovered

1. **Previous deletion reports are stale**: The `112000_code-delete-implement-report.md` claims deletion of 9 tools and 5 files, but all files and tools still exist in the current codebase. Either the changes were reverted, applied to a different branch, or the report is inaccurate.

2. **Extension copy drift**: `extension/mcp-servers/bridge/tools/` contains `-myk1yt` variant files (e.g., `__init__-myk1yt.py`, `analysis-myk1yt.py`, `scout-myk1yt.py`, `integrated-myk1yt.py`) that suggest parallel development or fork maintenance. These should be reconciled.

3. **Stale documentation**: Multiple docs reference `auto_analyze_whiteboard` as active (e.g., `PROJECT_CONTEXT.md` L472-477) despite it being deprecated since v0.16.0.

## Next Step Recommendations

1. Execute actions A1-A3 (immediate cleanup) — all low-risk, high-clarity
2. User decision on B1-B4 (aggregate tool consolidation)
3. Branch sync audit for `extension/mcp-servers/` vs `mcp-servers/`

## Affected File List

- `mcp-servers/bridge/tools/__init__.py` — registration entry point (no change needed)
- `mcp-servers/bridge/tools/ux_coordinator.py` — `auto_analyze_whiteboard` removal target
- `mcp-servers/bridge/tools/github_diver.py` — dead code deletion target
- `mcp-servers/vibezoo_mcp_bridge.py` — `list_subagents` ghost entry cleanup
- `extension/src/mcp/McpConfigService.ts` — `alwaysAllow` ghost entry cleanup
- `extension/mcp-servers/bridge/tools/` — sync target for all tool file changes
