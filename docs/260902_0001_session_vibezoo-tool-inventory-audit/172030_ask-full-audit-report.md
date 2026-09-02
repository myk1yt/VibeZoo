# Ask (CPO) Full Final Audit Report — VibeZoo Tool Cleanup

> **Mode**: Ask (CPO) — P6 Full Final Audit
> **Date**: 2026-09-02 17:20 (Asia/Seoul)
> **Audit method**: Independent spot-check. Per Crow mandate, no completion report was trusted; every scope item was verified by direct grep/read of the actual code in BOTH trees (`mcp-servers/` and `extension/mcp-servers/`).
> **Independence**: HIGH (this agent did not implement any phase).

---

## [1. Philosophy & UX/UI Diagnostics]

**North Star check.** The user's approved intent (decisions.md, 2026-09-02 15:54) was a *full* cleanup (A1–B3): remove deprecated/dead/ghost tools AND remove the 4 aggregate tools, replacing them with prompt-level composition. The implementation delivers exactly this. The surviving tool surface is coherent: every intent-detector hint, dropzone suggestion, and `list_subagents` entry points to a tool that actually exists. From a CPO seat, the outcome matches the spirit of the request — a leaner, honest tool catalog with no phantom capabilities advertised to the agent.

**UX/agent-experience impact.** The single most important UX property of this cleanup is that agents must never be told to call a tool that no longer exists. That property holds everywhere EXCEPT one live tool description (see 🔶 below). End users see no functional regression; the 6 removed capabilities are all reachable via prompt composition over surviving primitives.

---

## [2. 1:1 Cross-Validation Results — Requirements & Scope]

### Requirements (REQ-001..005)

| Req | Verdict | Evidence |
|-----|---------|----------|
| REQ-001 Count total tools | ✅ | Direct count of `@mcp.tool` registrations in `mcp-servers/bridge/tools/` = 32, + 1 in `vibezoo_mcp_bridge.py` = **33**. Matches plan's 39→33. |
| REQ-002 Record name/purpose/source/registration | ✅ | Discharged by 063349_project-research report; registration sites confirmed live during this audit. |
| REQ-003 Identify redundancy candidates | ✅ | Deprecated wrapper (`auto_analyze_whiteboard`), dead code (`github_diver.py`), ghost (`read_project_file`), merge candidate (`auto_analyze_after_drop`), 4 aggregates — all identified and actioned. |
| REQ-004 KEEP/REVIEW/REMOVE classification | ✅ | Survivors (`review_project`, `recall_project`, `review_pr`, `apply_patch`, `fetch_page`/`web_search`) verified present and registered. |
| REQ-005 Written inventory + cleanup report | 🔶 | Inventory delivered and the 33-count story is internally consistent in the **authoritative catalog tables**, but per-section count labels in README and one directory-tree entry in PROJECT_CONTEXT were not fully synced (see Scope item 8). |

### Cleanup scope items (A1–B3, FE contract, prompt-composition, docs)

| # | Item | Verdict | Code evidence (independent grep/read) |
|---|------|---------|----------------------------------------|
| A1 | `auto_analyze_whiteboard` gone | ✅ | 0 `@mcp.tool` registrations in both trees. Surviving mentions are docstring/test historical references only: `whiteboard.py:872,890,894,1096`, `tests/test_whiteboard_merge.py`. `ux_coordinator.py` (root L17-92, ext L17-86) registers only `ux_coordinator`. |
| A2 | `github_diver.py` absent | ✅ | 0 `.py` file under either `bridge/tools/`. Only historical references in `docs/260830_...` archives and `-p/i18n_verify.py:38` (a root utility list, not a live import). No import in `__init__.py`. |
| A3 | `read_project_file` absent | ✅ | 0 hits in `*.py` AND 0 hits in `*.ts` (whole workspace). Not in either `vibezoo_mcp_bridge.py` `list_subagents`, not in `McpConfigService.ts` alwaysAllow. |
| B1 | `analyze_uploaded_file(track_dropzone)` merged; `auto_analyze_after_drop` removed; dropzone strings retargeted | ✅ | `file_analyzer.py:388` (root) and `:443` (ext) both have `track_dropzone: bool = False` + `_write_dz_session`. `auto_analyze_after_drop` = 0 registrations both trees. Retargeted suggestion: root `ux_coordinator.py:86`, ext `ux_coordinator.py:86` (×2 = one per tree). |
| B2 | 4 aggregates have 0 registrations; survivors live; `list_subagents` lists only survivors | ✅ | `def find_bugs/suggest_refactor/generate_docs/learn_project` = 0 in `mcp-servers/**`. (3 hits are in `integrated-myk1yt.py` — a `-myk1yt` personal variant, out of cleanup scope, flagged below.) `integrated.py` registers only `review_project`; `knowledge.py` keeps `_auto_learn_project` (internal, no decorator) + `recall_project`. Both `list_subagents` bodies (root L50-67, ext L50-67) list only survivors. |
| FE | package.json / nls / alwaysAllow clean | ✅ | 0 hits for `vibezoo.findBugs/suggestRefactor/generateDocs/learnProject` in `extension/package.json`; 0 in `package.nls.json`; 0 removed-name in `McpConfigService.ts`. |
| 7 | Prompt-composition replacement in place | ✅ | `intent_detector.py:400-446` — all `primary_tool`/`next_tool` point to survivors (`capture_screen`, `analyze_uploaded_file` w/ `track_dropzone=True`, `review_code`, `vibezoo_setup`, etc.). `recall_project` hint at `knowledge.py:150-151`. |
| 8 | Docs show 33 tools, 0 removed-name references | 🔶 | **Authoritative catalog tables clean**: `PROJECT_CONTEXT.md:456-475` sums to exactly 33, no removed names. **BUT** (a) `README.md` per-section count labels still read "Integrated (4 Tools)" L144, "Reviewer (2)" L122, "Editor (2)" L167, "Knowledge (2)" L150, "Preferences (2)" L153 — these sum to 39, not 33, contradicting the L84/L86 "33 Tools" header; (b) `PROJECT_CONTEXT.md:392` directory tree still lists `github_diver.py`. ST-8's verification grep targeted removed *tool-name strings* (which are indeed gone) but missed stale *count labels* and the *file-tree entry*. |

### Verification gates

| Gate | Verdict | Evidence |
|------|---------|----------|
| Tests 100/100 | ✅ | Debug report raw command table (171230 L62-68): full suite `100 passed in 15.40s`, targeted 12 passed, copy parity IDENTICAL. The 2 prior failures were a pre-existing fixture-scope bug (`return`→`yield`), proven pre-existing via `git show 9ddeb79~1`. No assertion weakened. |
| Build (py_compile / tsc / compile) | 🔶 | Not re-executed by this audit (read-only CPO; build execution is delegated per Crow). Accepted on the strength of the per-phase reports + the fact that the test suite (which imports the edited modules) is green. **Recommend VP attach fresh exit-code evidence at P7.** |
| Traceability (commits reference session docs) | ✅ | Commits 9ddeb79/0b5d2ce/568cb64/55b78c2 cross-referenced across 163300/163930/164415/170000/080821 reports and the debug report. Chain is intact. |

---

## [3. Deviation Assessment — are the accepted deviations acceptable?]

| Deviation | Assessment | Verdict |
|-----------|-----------|---------|
| `tool_context.py` dead `MANIFEST_FIND_BUGS`/`MANIFEST_SUGGEST_REFACTOR` | **Understated.** It is more than 2 constants: `_MANIFEST_REGISTRY` still maps `find_bugs`/`suggest_refactor` (L107-112), and live helper functions `make_find_bugs_context`/`make_suggest_refactor_context` (L346, L382) are still exported (L437-438). Likely now-unused, but they are importable code paths advertising removed tools. Acceptable as a **documented follow-up**, not silent. | 🔶 Acceptable w/ required follow-up |
| `whiteboard.py` docstrings mention removed `auto_analyze_*` names (D4.4 "harmless") | **D4.4's "harmless" judgment is INCORRECT for one location.** `whiteboard.py:1036-1037` (both trees) is the docstring of the **`capture_screen` `@mcp.tool`** — a live, agent-facing tool description — and it instructs agents to call `auto_analyze_after_drop()`, a tool that no longer exists. Agents WILL attempt the call and error. The other mentions (L872/890/894/1096) are internal-helper docstrings and genuinely harmless. | 🔶 D4.4 partially wrong — the `capture_screen` description must be corrected (small, agent-facing) |
| Root↔extension i18n drift (B4 future session) | Pre-existing, explicitly deferred to a future session by user. Cosmetic (`t()` wrapping difference in `ux_coordinator.py:86`). Acceptable. | ✅ Acceptable (deferred w/ user knowledge) |
| Test files not committed (`tests/` gitignored) | Repo convention. The debug report (L39, L76) confirms both test copies are untracked per convention, not an oversight. Acceptable. | ✅ Acceptable |
| Redeploy (`init_vibezoo.bat`) not yet run — running bridge still serves 39 tools | A **deployment-state gap, not a code defect.** The source is correct at 33; the live process is stale until the user redeploys. Must be communicated as the single remaining action. | 🔶 Acceptable ONLY if surfaced to user as the required final step |
| **NEW — stale test names** | `test_max_tokens.py:156/163/170` are named `test_find_bugs_truncation`/`test_suggest_refactor_truncation`/`test_generate_docs_truncation` but only exercise the shared `truncate_to_tokens` helper — they no longer test the named (removed) tools. They pass, so no functional impact, but the names misrepresent removed tools. | 🔶 New finding — rename/merge into one helper test (cosmetic) |
| **NEW — `-myk1yt` variant files retain removed tools** | `extension/mcp-servers/bridge/tools/integrated-myk1yt.py:521/734/863` still registers `find_bugs`/`suggest_refactor`/`generate_docs`. These are the user's personal fork variants (`*-myk1yt.*` throughout), outside the canonical cleanup scope, but they still expose the removed tools if the `-myk1yt` bridge is ever launched. | 🔶 New finding — confirm with user whether `-myk1yt` copies should be synced |

---

## [4. Inquiries for VP & User]

1. **`capture_screen` tool description (blocking-ish, small):** `whiteboard.py:1036-1037` (both trees) tells agents to call the removed `auto_analyze_after_drop()`. This is the one place a *live tool description* points at a dead tool. **Option A:** retarget to `analyze_uploaded_file(track_dropzone=True)` now (1-line, low risk). **Option B:** defer with the other docstring cleanups. Recommend **A** — it directly defeats the cleanup's core purpose.
2. **`-myk1yt` variant files:** do you want `integrated-myk1yt.py` (and any other `*-myk1yt` copies) synced to the 33-tool set, or are they intentionally frozen personal variants? (User decision — not assumed.)
3. **Doc count labels:** README sections 1.8/1.3/1.14/1.10/1.11 still say "(4 Tools)/(2 Tools)" and sum to 39 against the "33" header. Fix labels (cosmetic) or accept the header-only correction?
4. **Redeploy:** confirm you will run `init_vibezoo.bat` to make the live bridge serve the 33-tool set. Until then the running process still advertises 39.

---

## [Final Verdict]

**CONDITIONAL APPROVAL 🔶**

The cleanup **fully achieves the user's approved intent** at the code level: all 6 removals verified by independent grep in both trees (0 registrations), the B1 merge is correct, FE contract is clean, prompt-composition is in place, the tool count genuinely reconciles to 33, tests are 100/100 with a legitimately-diagnosed pre-existing fixture fix, and commit traceability is intact. This is NOT a rejection — the North Star is met.

It is not a clean PASS because of four **non-blocking but real** gaps, all documentation/description hygiene rather than functional defects:

**Conditions to clear before final close (all small, none require re-architecture):**
1. **(Should-fix, agent-facing)** Retarget the `capture_screen` tool description at `whiteboard.py:1036-1037` (both trees) away from the removed `auto_analyze_after_drop()` → `analyze_uploaded_file(track_dropzone=True)`. This is the only live agent-facing pointer to a dead tool.
2. **(Should-fix, cosmetic)** Sync README per-section count labels (1.3/1.8/1.10/1.11/1.14) to sum to 33; remove `github_diver.py` from the `PROJECT_CONTEXT.md:392` tree diagram.
3. **(Follow-up, documented)** Remove or gate the dead `tool_context.py` registry entries + `make_find_bugs_context`/`make_suggest_refactor_context`; rename the 3 stale `test_max_tokens.py` test names.
4. **(User action)** Run `init_vibezoo.bat` to redeploy; decide the fate of the `-myk1yt` variant copies.

**VP may proceed to P7 review.** These conditions are recorded, scoped, and do not block the phase transition — but condition #1 should be closed before the tool is considered agent-safe, and VP should attach fresh build exit-code evidence at P7.
