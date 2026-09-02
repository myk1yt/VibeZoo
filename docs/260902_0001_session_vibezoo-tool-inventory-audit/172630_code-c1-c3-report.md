# Code Task Report — P6 Audit Conditions C1 + C3

> **Mode**: Code
> **Date**: 2026-09-02 17:26 (Asia/Seoul)
> **Scope**: Conditions C1 + C3 from [172030_ask-full-audit-report.md](../172030_ask-full-audit-report.md)
> **Report Folder**: docs/260902_0001_session_vibezoo-tool-inventory-audit/

---

## Task Summary

Executed the two P6 audit conditions:
- **C1** (agent-facing): retarget the live `capture_screen` `@mcp.tool` docstring away from the removed `auto_analyze_after_drop()`, and purge all other `auto_analyze_*` docstring references.
- **C3** (dead code + stale test names): purge dead `MANIFEST_FIND_BUGS`/`MANIFEST_SUGGEST_REFACTOR` constants, their `_MANIFEST_REGISTRY` entries, and the 0-reference `make_suggest_refactor_context` factory; rename 3 stale test names in `test_max_tokens.py`.

All edits were strings/declarations only — no logic changes. Both trees (`mcp-servers/` and `extension/mcp-servers/`) kept in parity.

---

## Condition C1 — whiteboard.py docstrings (BOTH trees)

### C1-a: `capture_screen` docstring (agent-facing, the audit's blocking item)

**Before** ([mcp-servers/bridge/tools/whiteboard.py:1036](mcp-servers/bridge/tools/whiteboard.py:1036)):
```
드롭존에서 파일 업로드 후에는 auto_analyze_after_drop()을 호출하여
자동 분석을 실행하세요.
```
**After**:
```
드롭존에서 파일 업로드 후에는 analyze_uploaded_file(file_path, track_dropzone=True)을
호출하여 자동 분석을 실행하세요.
```

### C1-b: cosmetic `auto_analyze_whiteboard` references (same file, strings only)

| Location (root) | Change |
|---|---|
| [`_generate_whiteboard_suggestions` docstring, ~L872](mcp-servers/bridge/tools/whiteboard.py:868) | Removed trailing line "(deprecated)에서도 동일한 내용을 사용합니다." |
| [`_get_whiteboard_state_impl` docstring, ~L888](mcp-servers/bridge/tools/whiteboard.py:886) | "ux_coordinator.py의 auto_analyze_whiteboard() 양쪽에서 호출 가능합니다" → "register() 내부의 MCP 툴 래퍼에서 호출됩니다"; removed "(이전 auto_analyze_whiteboard()와 동일한 동작)" line |
| [`get_whiteboard_state` tool docstring, ~L1095](mcp-servers/bridge/tools/whiteboard.py:1090) | Removed "(이전 auto_analyze_whiteboard()와 동일한 동작)" line |

Identical edits applied to `extension/mcp-servers/bridge/tools/whiteboard.py`.

### C1-c: residual `auto_analyze_*` string references found during grep gate (fixed for 0-hit compliance)

| File (×2 trees) | Change |
|---|---|
| [`file_analyzer.py:19`](mcp-servers/bridge/tools/file_analyzer.py:19) `_write_dz_session` docstring | "[v2.1 B1] auto_analyze_after_drop 제거에 따라 …" → "[v2.1 B1] 드롭존 자동 분석 책임이 …" (comment only) |
| [`tests/test_whiteboard_merge.py:1-10`](mcp-servers/tests/test_whiteboard_merge.py:1) module docstring | Removed stale "auto_analyze_whiteboard() still works + includes deprecation note" bullet; title reworded. No test logic touched. |

---

## Condition C3 — tool_context.py + test_max_tokens.py

### Pre-edit importer search (required by delegation)

Pattern: `make_find_bugs_context|make_suggest_refactor_context|MANIFEST_FIND_BUGS|MANIFEST_SUGGEST_REFACTOR` across both trees:

| Symbol | External references | Decision |
|---|---|---|
| `MANIFEST_FIND_BUGS` | 0 (only its own definition + registry + `__all__`) | **REMOVED** (both trees) |
| `MANIFEST_SUGGEST_REFACTOR` | 0 | **REMOVED** (both trees) |
| `_MANIFEST_REGISTRY` entries `find_bugs`/`suggest_refactor` | 0 | **REMOVED** from registry (both trees) |
| `make_suggest_refactor_context` | 0 | **REMOVED** (both trees) |
| `make_find_bugs_context` | **1 — `extension/mcp-servers/bridge/tools/integrated-myk1yt.py:542`** (`from bridge.tool_context import make_find_bugs_context`) | **KEPT** per delegation rule "If a symbol HAS references, leave it and report" — the importer is a `-myk1yt` fork variant, out of cleanup scope, so removal would break it. Annotated in `__all__` with a comment explaining retention. |

Safe-removal note: `ToolContext.__post_init__` handles a missing manifest gracefully (`get_manifest(tool_name) or {}`), so removing the `find_bugs`/`suggest_refactor` registry entries cannot crash any caller.

### Edits applied ([mcp-servers/bridge/tool_context.py](mcp-servers/bridge/tool_context.py:105), mirrored in extension copy)

1. Deleted `MANIFEST_FIND_BUGS` block (was L61-80) and `MANIFEST_SUGGEST_REFACTOR` block (was L82-102).
2. `_MANIFEST_REGISTRY` now contains only `explain_code` + `generate_tests`.
3. Deleted `make_suggest_refactor_context` function (was L382-419).
4. `__all__`: removed `MANIFEST_FIND_BUGS`, `MANIFEST_SUGGEST_REFACTOR`, `make_suggest_refactor_context`; kept `make_find_bugs_context` with retention comment.

### test_max_tokens.py — 3 stale test names renamed

([mcp-servers/tests/test_max_tokens.py:156-175](mcp-servers/tests/test_max_tokens.py:156))

| Old name | New name | Logic |
|---|---|---|
| `test_find_bugs_truncation` | `test_truncate_to_tokens_alpha` | unchanged (same assertions) |
| `test_suggest_refactor_truncation` | `test_truncate_to_tokens_numeric` | unchanged |
| `test_generate_docs_truncation` | `test_truncate_to_tokens_whitespace` | unchanged |

No tests weakened, deleted, or merged — 3 renamed 1:1 with docstrings updated to describe the actual `truncate_to_tokens` helper behavior. Test count remains 100.

---

## Verification Evidence (actual outputs)

### 1. `python -m py_compile` — exit 0 ✅

```
$ python -m py_compile mcp-servers/bridge/tools/whiteboard.py \
    extension/mcp-servers/bridge/tools/whiteboard.py \
    mcp-servers/bridge/tool_context.py \
    extension/mcp-servers/bridge/tool_context.py \
    mcp-servers/tests/test_max_tokens.py
PY_COMPILE_EXIT_0   (exit code: 0)

$ python -m py_compile mcp-servers/bridge/tools/file_analyzer.py \
    extension/mcp-servers/bridge/tools/file_analyzer.py \
    mcp-servers/tests/test_whiteboard_merge.py \
    extension/mcp-servers/tests/test_whiteboard_merge.py
PY_COMPILE_EXIT_0   (exit code: 0)
```

### 2. `pytest tests/ -q` (in `mcp-servers/`) — 100 passed ✅

```
$ cd mcp-servers && python -m pytest tests/ -q
........................................................................ [ 72%]
............................                                             [100%]
100 passed in 15.33s      (exit code: 0)
```

(Identical result on the first run before the docstring-only follow-ups: `100 passed in 15.36s`.)

### 3. Grep for removed symbols in both trees (excluding `-myk1yt` variants)

```
$ Select-String over all *.py in mcp-servers/ + extension/mcp-servers/
  (excluding *myk1yt* filenames) for:
  auto_analyze_after_drop|auto_analyze_whiteboard|MANIFEST_FIND_BUGS|
  MANIFEST_SUGGEST_REFACTOR|make_find_bugs_context|make_suggest_refactor_context

REMAINING HITS (4, all deliberate exception):
  mcp-servers/bridge/tool_context.py:300:            def make_find_bugs_context(
  mcp-servers/bridge/tool_context.py:350:            "make_find_bugs_context",
  extension/mcp-servers/bridge/tool_context.py:300:  def make_find_bugs_context(
  extension/mcp-servers/bridge/tool_context.py:350:  "make_find_bugs_context",
```

**All 5 other target symbols = 0 hits.** The 4 remaining hits are the single deliberately-retained `make_find_bugs_context` symbol (definition + `__all__` export, in both trees for parity), kept because it has 1 external importer: `extension/mcp-servers/bridge/tools/integrated-myk1yt.py:542` — a frozen `-myk1yt` personal variant explicitly out of scope per the delegation ("excluding -myk1yt fork variants") and audit finding #2. `auto_analyze_after_drop`, `auto_analyze_whiteboard`, `MANIFEST_FIND_BUGS`, `MANIFEST_SUGGEST_REFACTOR`, `make_suggest_refactor_context` = **0 hits**.

### 4. `npx tsc --noEmit` (in `extension/`) — exit 0 ✅

```
$ cd extension && npx tsc --noEmit
TSC_EXIT_0   (exit code: 0)
```

---

## Issues Discovered

1. **`make_find_bugs_context` retention (documented exception)**: cannot be removed while the frozen `-myk1yt` fork imports it. If the user later decides to sync/purge the `-myk1yt` variants (audit inquiry #2), this symbol becomes 0-reference and can be removed in a 1-line follow-up.
2. **Audit item #2 (README count labels) and #4 (redeploy via `init_vizoo`-style `init_vibezoo.bat`)** remain open — outside C1/C3 scope, untouched.

## Next Step Recommendations

1. VP: commit (this task made no commits per instructions).
2. VP/User: resolve audit inquiries #2 (`-myk1yt` fate — unlocks removal of the retained `make_find_bugs_context`) and #4 (redeploy so the live bridge serves the 33-tool set).

## Affected File List

| File | Change type |
|---|---|
| `mcp-servers/bridge/tools/whiteboard.py` | C1: capture_screen docstring retarget + 3 cosmetic docstring purges |
| `extension/mcp-servers/bridge/tools/whiteboard.py` | identical to root |
| `mcp-servers/bridge/tool_context.py` | C3: dead constants/registry entry/factory removed; `__all__` updated |
| `extension/mcp-servers/bridge/tool_context.py` | identical to root |
| `mcp-servers/bridge/tools/file_analyzer.py` | C1-c: comment-only stale name removal |
| `extension/mcp-servers/bridge/tools/file_analyzer.py` | identical to root |
| `mcp-servers/tests/test_max_tokens.py` | C3: 3 test renames (logic untouched) |
| `mcp-servers/tests/test_whiteboard_merge.py` | C1-c: module docstring only |
| `extension/mcp-servers/tests/test_whiteboard_merge.py` | identical to root |

No git commit/push performed — VP commits.