# Debug Task Report: 2 failing tests in test_whiteboard_merge.py

## Status
COMPLETE — Root cause proven (test-fixture scope bug, pre-existing), minimal test-side fix applied to both copies, full suite 100/100 green.

## Task Summary
Diagnosed the 2 failures in `mcp-servers/tests/test_whiteboard_merge.py` (`TestGetWhiteboardStateDefault::test_default_returns_state`, `test_default_has_hint_for_analyze`), proved they are pre-existing and NOT caused by the cleanup commits, and fixed them on the test side only.

## Root Cause Analysis

### Symptom
- `test_default_returns_state` failed: expected `"Raw JSON"` or `"objects"`, got `"## ✅ Whiteboard State\n\nWhiteboard is empty.\n"` — i.e. the **empty-whiteboard branch** ran despite the fixture providing commands data.
- `test_default_has_hint_for_analyze` failed: `analyze=True` hint missing — same reason (empty branch intentionally omits the hint).

### Actual root cause: fixture-scope bug in the test file — NOT stale assertions, NOT an implementation regression
The `registered_whiteboard_tools` fixture did:

```python
@pytest.fixture
def registered_whiteboard_tools(wb_file_commands):
    with patch("bridge.tools.whiteboard.WHITEBOARD_FILE", wb_file_commands), ...:
        from bridge.tools.whiteboard import register
        mcp = MockMCP()
        register(mcp)
        return mcp.tools   # ← BUG: plain return inside `with`
```

A non-yield fixture executes its **entire body** during setup; `return mcp.tools` exits the `with patch(...)` block, deactivating all patches **before any test body runs**. Consequently `WHITEBOARD_FILE` reverted to the real config path (which points at a nonexistent file on this machine), and `_get_whiteboard_state_impl()` ([whiteboard.py:898](../../../mcp-servers/bridge/tools/whiteboard.py)) hit the `not os.path.exists(WHITEBOARD_FILE)` empty branch (L898-904): heading + `"Whiteboard is empty."`, no hint, no Raw JSON, no suggestions.

The 2 failing tests were therefore asserting the contract they were *written* for (commands data → Raw JSON + `analyze=True` hint), but never actually received that data. Side observation: the other 2 tests in the same class (`test_default_no_suggestions`, and the analyze-class tests) passed only by coincidence of their assertions, not because the fixture worked — `test_default_no_suggestions` passed because the empty message trivially lacks "분석 제안"; the analyze tests passed *for the wrong path* (empty+analyze=True branch appends suggestions, so `"분석 제안"`, `"Mermaid"` etc. matched even though the commands fixture was never read).

### Design-intent check (implementation is correct)
The implementation's hint placement is deliberate:
- Empty branch (whiteboard.py L898-904): heading + `"Whiteboard is empty."` + (only if `analyze=True`) suggestions. **No** `analyze=True` hint — intentional, nothing to analyze.
- Every non-empty default branch (L923-924, L941-942, L956-957): appends `"> 💡 ... analyze=True ..."` hint.
So the tests' expectation (hint present in default non-empty output) matches the implementation exactly. The implementation needed no change.

## Pre-existing vs Regression Verdict: **PRE-EXISTING** (evidence)
1. `git log -- mcp-servers/tests/test_whiteboard_merge.py` returns **empty** — the test file is untracked (created this session-chain, never committed), so no cleanup commit could have altered it.
2. `git show 9ddeb79~1:mcp-servers/bridge/tools/whiteboard.py` (extracted read-only to `%TEMP%\whiteboard_precleanup.py`): the pre-cleanup implementation has an **identical** `_get_whiteboard_state_impl` — `"Whiteboard is empty.\n"` at L899, hint lines only at L923/L941/L956 (non-empty branches), empty branch skipping the hint. Empty-vs-nonempty behavior is unchanged across the cleanup.
3. The only uncommitted diff on `mcp-servers/bridge/tools/whiteboard.py` is one added (unused) import line, `from bridge.i18n import t`, which does not affect output logic. Last commit touching it (d60f300) also predates the cleanup session cleanup steps.
4. Because the fixture-scope bug depends only on the test file itself + the real `WHITEBOARD_FILE` config path being nonexistent (typical for CI/dev machines), these 2 tests failed identically before the cleanup commits. Not a regression.

## Fix Applied (test-side, minimal)
Converted `registered_whiteboard_tools` from a plain `return` fixture to a **`yield` fixture** in BOTH file copies:

- [test_whiteboard_merge.py](../../../mcp-servers/tests/test_whiteboard_merge.py) (mcp-servers copy)
- [test_whiteboard_merge.py](../../../extension/mcp-servers/tests/test_whiteboard_merge.py) (extension copy — verified byte-identical after edit)

```diff
         mcp = MockMCP()
         register(mcp)
-        return mcp.tools
+        yield mcp.tools
```

Plus a docstring note explaining WHY (a plain return inside `with patch(...)` deactivates patches before the test body runs). No assertion was changed, weakened, or deleted — the tests now exercise the code path they were written for.

Rationale for fixing the fixture instead of rewriting assertions to the empty-state output: rewriting the assertions would have made the tests assert the *accidental* real-config-path behavior (environment-dependent: on a machine where the real `WHITEBOARD_FILE` exists, the old assertions would have been flaky). The fixture fix is the minimal change that removes the root cause. This is a legitimate test-defect fix, not test weakening.

## Verification
| Check | Command | Result |
|---|---|---|
| Reproduce failures (pre-fix) | `cd mcp-servers && python -m pytest tests/test_whiteboard_merge.py -q` | 2 failed, 10 passed — exact reported failures reproduced |
| Pre-cleanup impl inspection | `git show 9ddeb79~1:mcp-servers/bridge/tools/whiteboard.py` (read-only, to %TEMP%) | empty-branch/hint logic identical to current — pre-existing confirmed |
| Targeted (post-fix) | `cd mcp-servers && python -m pytest tests/test_whiteboard_merge.py -q` | **12 passed** |
| Full suite (post-fix) | `cd mcp-servers && python -m pytest tests/ -q` | **100 passed in 15.40s** |
| Copy parity | Python equality check mcp vs extension test file | IDENTICAL |

## Environment Notes
- No test-env issues encountered (no env fixes needed; env worked throughout).
- No implementation files were modified. No git commit/push/reset/checkout performed.

## Issues Discovered (non-blocking, for VP awareness)
1. `mcp-servers/bridge/tools/whiteboard.py` has an uncommitted **unused import** (`from bridge.i18n import t`, line ~27) left over from earlier in this session chain (pre-session per VP note). Not touched per constraints — flagging for VP/cleanup owner: either wire up the i18n `t()` calls (further ST work) or remove the dead import in the VP commit.
2. `git log` shows `extension/mcp-servers/tests/test_whiteboard_merge.py` has no committed history either (both test copies are untracked/new — the extension copy existed on disk since before this fix; not created by me).
3. Other tests in the file (`test_default_no_suggestions`, all `TestGetWhiteboardStateAnalyze::*` except `test_empty_whiteboard_analyze`) were previously passing against the *wrong* code path (empty branch) — now, with the fixture fixed, they pass against the intended commands-data path. Same fix, no separate change needed.

## Affected File List
- `mcp-servers/tests/test_whiteboard_merge.py` (fixture: return → yield + docstring)
- `extension/mcp-servers/tests/test_whiteboard_merge.py` (same change; byte-identical parity confirmed)

## Next Step Recommendations
- VP: commit both test file copies together (suggested message: `fix(whiteboard/tests): yield fixture so WHITEBOARD_FILE patch stays active during test bodies`).
- Decide on the unused `t` import in `mcp-servers/bridge/tools/whiteboard.py` (see Issues #1) — do not commit it mixed with the test fix.
