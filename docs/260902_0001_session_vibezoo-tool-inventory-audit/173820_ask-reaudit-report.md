# Ask (CPO) P6 RE-AUDIT Report — VibeZoo Tool Cleanup, Conditions C1–C3

> **Mode**: Ask (CPO) — P6 Re-Audit (Full Audit mode)
> **Date**: 2026-09-02 17:38 (Asia/Seoul)
> **Prior verdict**: CONDITIONAL APPROVAL 🔶 ([172030_ask-full-audit-report.md](172030_ask-full-audit-report.md)) with 4 conditions; C1+C3 fixed in commit 937658c, C2 in commit 06293d6.
> **Audit method**: Independent direct verification. Per Crow mandate, no completion report was trusted. Every condition was re-verified by direct `search_files`/`read_file` against the actual code in BOTH trees (`mcp-servers/`, `extension/mcp-servers/`), not against the fix reports.
> **Independence**: HIGH (this agent did not implement C1/C2/C3).

---

## Per-Condition Verdicts

### C1 — `capture_screen` docstring retarget + `auto_analyze_*` purge → ✅ CLOSED

**Requirement**: live agent-facing `capture_screen` tool description must not point at removed `auto_analyze_after_drop()`; all `auto_analyze_after_drop`/`auto_analyze_whiteboard` references purged from canonical trees (excluding `-myk1yt` fork variants).

**Direct evidence (fresh greps, this session)**:

| Check | Result |
|---|---|
| `auto_analyze_after_drop\|auto_analyze_whiteboard` in `mcp-servers/**/*.py` | **0 hits** |
| Same in `extension/mcp-servers/**/*.py` | **1 hit** — [`extension/mcp-servers/tests/test_whiteboard_merge-myk1yt.py:2`](extension/mcp-servers/tests/test_whiteboard_merge-myk1yt.py:2), a `-myk1yt` fork variant → **exempt** per user decision D4.4-B4 scope |
| Retargeted docstring, root | [`whiteboard.py:1033`](mcp-servers/bridge/tools/whiteboard.py:1033): "드롭존에서 파일 업로드 후에는 `analyze_uploaded_file(file_path, track_dropzone=True)`을 호출하여…" ✅ |
| Retargeted docstring, extension | [`whiteboard.py:1032`](extension/mcp-servers/bridge/tools/whiteboard.py:1032): identical ✅ |

The single live agent-facing pointer to a dead tool (the audit's blocking item) is fixed in both trees. **No agent-facing text in the canonical trees references any removed tool.** C1 = ✅.

---

### C2 — README section labels + `github_diver` docs purge → 🔶 CLOSED WITH RESIDUAL NOTE

**Requirement**: README per-section count labels match actual registrations; `github_diver` 0 hits in docs; header count 33 consistent.

**Direct evidence**:

| Check | Result |
|---|---|
| README labels (fresh grep) | 1.3 Reviewer `(1 Tool)` L122, 1.8 Integrated `(1 Tool)` L144, 1.10 Knowledge `(3 Tools)` L150, 1.11 Preferences `(2 Tools)` L153, 1.14 Editor `(1 Tool)` L167 — all match actual per-file `@mcp.tool` counts ✅ |
| `github_diver` in `*.md` workspace-wide | 112 hits — **all** in historical archives (`docs/archive/`, `docs/260725_*`, `docs/260830_*`, `fromscratch/`) or this session's own audit reports. **0 hits** in `README.md`, `README-myk1yt.md`, `docs/PROJECT_CONTEXT.md`, `docs/PROJECT_CONTEXT-myk1yt.md` as live catalog/tree entries ✅ |
| Actual tool count (fresh direct count) | **33** `@mcp.tool` registrations in `mcp-servers/bridge/tools/`: fix_loop 3, file_analyzer 1, editor 1, analysis 4, feedback 1, deep_analyzer 4, scout 3, ssa 1, setup 1, web 2, reviewer 1, tester 2, ux_coordinator 1, knowledge 3, whiteboard 4, integrated 1 → sum **33**. Header "33 Tools" (README L84, PROJECT_CONTEXT L455) = consistent ✅ |

**Corrections to the prior record (devil's advocate)**:

1. The original audit's "32 in `bridge/tools/` + 1 in `vibezoo_mcp_bridge.py` = 33" was arithmetically right but structurally wrong: [`vibezoo_mcp_bridge.py`](mcp-servers/vibezoo_mcp_bridge.py:47) registers **0** `@mcp.tool` tools (only 2 `@mcp.custom_route` HTTP endpoints). All 33 tools live in `bridge/tools/`. The final count 33 is correct; the derivation was not.
2. **Residual under-count (surviving tool, not stale)**: `check_uploaded_files` is registered ([`whiteboard.py:967`](mcp-servers/bridge/tools/whiteboard.py:967)) but absent from README §1.6 (lists 3) and the PROJECT_CONTEXT Whiteboard catalog row (lists 3). Additionally `list_subagents` lists `check_uploaded_files` under BOTH Whiteboard (L56) and FileAnalyzer (L65) — cosmetic duplication.
3. **README label sum = 35 vs header 33** (flagged by the C2 report): explained by categorization overlap — `web_search` appears in both §1.0 and §1.12, `learn_preference`/`get_preferences` in both §1.10 and §1.11. Per-file counts are faithful; the sum double-counts shared tools. Not a stale reference; a taxonomy choice.

None of items 1–3 are stale references to removed tools; all are counting/taxonomy notes about surviving tools. C2 = 🔶 closed, with a doc-polish follow-up (below).

---

### C3 — dead manifest purge + stale test renames → 🔶 CLOSED WITH TWO PARITY/DOC RESIDUALS

**Requirement**: `MANIFEST_FIND_BUGS`/`MANIFEST_SUGGEST_REFACTOR`/`make_suggest_refactor_context` 0 hits (excl `-myk1yt`); retained `make_find_bugs_context` annotation + fork importer argument holds; `test_max_tokens.py` names clean.

**Direct evidence**:

| Check | Result |
|---|---|
| `MANIFEST_FIND_BUGS\|MANIFEST_SUGGEST_REFACTOR\|make_suggest_refactor_context\|make_find_bugs_context` in `mcp-servers/**/*.py` | Only the deliberate exception: def L300 + `__all__` L350 in [`tool_context.py`](mcp-servers/bridge/tool_context.py:300). All 3 removal targets = **0 hits** ✅ |
| Same in `extension/mcp-servers/**/*.py` | Same exception (def L300, `__all__` L350) + the fork importer [`integrated-myk1yt.py:542`](extension/mcp-servers/bridge/tools/integrated-myk1yt.py:542) (`from bridge.tool_context import make_find_bugs_context`) ✅ — **the retention argument holds: removal would break the `-myk1yt` fork** |
| Retention annotation | [`tool_context.py:349`](mcp-servers/bridge/tool_context.py:349) (both trees): `# find_bugs는 integrated-myk1yt.py 변형이 참조하므로 유지 (감사 C3 판정)` ✅ documented |
| Root test names | [`test_max_tokens.py:156/163/170`](mcp-servers/tests/test_max_tokens.py:156): `test_truncate_to_tokens_alpha/numeric/whitespace`; 0 stale names ✅ |

**Residuals found (new, honest disclosure)**:

1. **Extension test mirror NOT renamed — tree parity broken.** [`extension/mcp-servers/tests/test_max_tokens.py:156-171`](extension/mcp-servers/tests/test_max_tokens.py:156) still has `test_find_bugs_truncation` / `test_suggest_refactor_truncation` / `test_generate_docs_truncation`. The C3 report's Affected File List confirms it only edited the root copy, despite claiming "Both trees kept in parity". Impact: LOW (tests are untracked per repo convention; the stale names misrepresent removed tools but are not agent-facing and the tests still pass — they exercise the shared `truncate_to_tokens` helper). It contradicts the C3 report's parity claim, however.
2. **Module docstring stale in BOTH copies.** [`mcp-servers/tests/test_max_tokens.py:4-6`](mcp-servers/tests/test_max_tokens.py:4) still reads "Each of the 5 tools (…, find_bugs, suggest_refactor, generate_docs) respects max_tokens" — a removed-tool reference the C3 rename missed (it renamed functions, not the module docstring). Same text in the extension copy. Not agent-facing → does not trigger the REJECT criterion, but it is exactly the class of residue this cleanup exists to remove.

C3 = 🔶 closed at the code level (all required symbols purged, retention documented and justified), with two documented test-file residuals.

---

## Gates

| Gate | Verdict | Evidence |
|------|---------|----------|
| pytest full suite 100 pass | 🔶 NOT_RE_RUN by this audit | Ask mode has no shell execution capability; `analyze_coverage` took the fast path (file-ratio only). Accepted on: (a) C1/C3 report raw output `100 passed in 15.33s` exit 0 run **after** the C1/C3 edits; (b) edits since were string/declaration-only (docstrings, test renames, label text) verified by my greps to touch no logic; (c) the suite imports the edited modules, so a green run post-edit covers import-level breakage. **VP must attach a fresh `pytest` exit code at P7.** |
| `tsc --noEmit` exit 0 | 🔶 NOT_RE_RUN by this audit | Same constraint. C1/C3 report records `TSC_EXIT_0` at 17:26; C2 touched only Markdown. Extension `.ts` sources were not modified since. **VP must attach a fresh exit code at P7.** |

Honesty note: per the Crow mandate ("Ask never trusts completion reports") these gates are graded 🔶, not ✅. The code-level conditions (the substance of this re-audit) were verified directly; the process gates were not re-executable within this mode's tool set.

---

## Known Open Items (evaluated)

| Item | Assessment | Blocking? |
|---|---|---|
| (a) `init_vibezoo.bat` redeploy not yet run — live bridge still serves 39 tools | Deployment-state gap, not a code defect. Source is verifiably at 33 (direct count). The running process is stale until the user redeploys. | **Non-blocking for code verdict; the single remaining user action.** Must be surfaced as the final step. |
| (b) `-myk1yt` fork variants untouched (`vibezoo_mcp_bridge-myk1yt.py` L50/52 still lists `find_bugs`/`suggest_refactor`/`generate_docs`/`learn_project`; `integrated-myk1yt.py` still registers them) | Explicitly out of scope per user decision D4.4-B4. The retained `make_find_bugs_context` exists solely to keep this fork importable; annotation is in place. If the user later retires the fork, that symbol becomes 0-reference and removable in a 1-line follow-up. | **Non-blocking** — frozen by user decision, properly documented. |

---

## Requirement Checklist — Final Verdicts

| Req | Verdict | Evidence |
|-----|---------|----------|
| REQ-001 Count total tools | ✅ | Fresh direct count this session: **33** `@mcp.tool` registrations (per-file enumeration above). 39 − 6 removals = 33 reconciles. |
| REQ-002 Record name/purpose/source/registration | ✅ | Discharged by 063349 research report; registration sites re-confirmed live in this audit. |
| REQ-003 Identify redundancy candidates | ✅ | All candidates (deprecated wrapper, dead module, ghost entry, merge candidate, 4 aggregates) identified and actioned; verified 0-registration by direct grep. |
| REQ-004 KEEP/REVIEW/REMOVE classification | ✅ | Survivors (`review_project`, `recall_project`, `review_pr`, `apply_patch`, `fetch_page`/`web_search`, `ux_coordinator`, `vibezoo_feedback`…) verified present and registered; `list_subagents` lists only survivors. |
| REQ-005 Written inventory + cleanup report | ✅ | Inventory delivered; the 33-count story is now internally consistent across header, authoritative catalog tables, and actual registrations. README per-section labels corrected. Residual doc notes (check_uploaded_files catalog omission; label-sum taxonomy) recorded above. |

---

## [Final Verdict]

**PASS ✅** (with documented non-blocking follow-ups)

**Strictness check applied**: the mandated REJECT trigger was "any newly-found stale reference to removed tools in **agent-facing** text". Direct greps confirm **zero** such references in the canonical trees: all live tool docstrings, `ux_coordinator`/`intent_detector` output strings, `list_subagents`, README, and PROJECT_CONTEXT point only at surviving tools. The two newly-found residuals (extension test-mirror names; test module docstrings in both trees) live in **untracked test files, not agent-facing surfaces** — they do not meet the REJECT bar.

**Why not another 🔶**: all three conditions are closed at the code level with direct evidence; the count reconciles to 33 everywhere it matters; the retention exception is annotated and its justification (live `-myk1yt` importer) was independently confirmed. The remaining items are (1) process gates Ask cannot execute, and (2) cosmetic test/doc hygiene. Neither reflects intent deviation.

**Follow-ups for VP/User (non-blocking)**:
1. 🟡 VP at P7: attach fresh `pytest` (expect 100 passed) and `tsc --noEmit` exit codes.
2. 🟡 Sync `extension/mcp-servers/tests/test_max_tokens.py` renames + fix the stale module docstring in BOTH copies (1 small code-light task).
3. 🟢 Doc polish: add `check_uploaded_files` to README §1.6 / PROJECT_CONTEXT Whiteboard row; dedupe it in `list_subagents`; note README label-sum overlap (35 vs 33) as taxonomy, or relabel.
4. 🔵 User action: run `init_vibezoo.bat` to redeploy — until then the live bridge still serves the old 39-tool set.
5. 🔵 User decision (standing): fate of `-myk1yt` variants; retiring them unlocks removal of the retained `make_find_bugs_context`.

**VP may proceed to P7 independent review.**
