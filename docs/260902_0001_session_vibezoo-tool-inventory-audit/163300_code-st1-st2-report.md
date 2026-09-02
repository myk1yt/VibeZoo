# Code Task Report — ST-1 + ST-2 (Phase 1, VibeZoo Tool Cleanup)

## Task Summary
Executed Phase 1 of the VibeZoo MCP bridge tool cleanup per [architecture-plan.md](architecture-plan.md) §3 ST-1/ST-2 and Decision D1 (Option A):
- **ST-1 (A1+A3 partial)**: Deleted deprecated `auto_analyze_whiteboard()`, merged `auto_analyze_after_drop()`, and the relocated `_write_dz_session()` helper from `ux_coordinator.py` in BOTH trees (root mirror + extension source-of-truth). Deleted the obsolete `TestAutoAnalyzeWhiteboardDeprecated` test class from both test copies.
- **ST-2 (B1 core)**: Moved `_write_dz_session()` verbatim into `file_analyzer.py` (both copies) and added opt-in `track_dropzone: bool = False` parameter to `analyze_uploaded_file()` with backward-compatible single-arg calls.

## Actions Taken

### ST-1 — ux_coordinator.py (×2 copies)
1. Deleted `_write_dz_session()` (old L21-53) — moved to file_analyzer.py per Decision D1; after both auto_* deletions nothing in ux_coordinator.py uses it.
2. Deleted `auto_analyze_after_drop()` (old L136-284) — merged into `analyze_uploaded_file` per Decision D1 (only the unique dropzone-session-tracking behavior was ported; the inferior per-extension routing was NOT ported as the plan directs).
3. Deleted `auto_analyze_whiteboard()` (old L286-308) — deprecated alias of `get_whiteboard_state(analyze=True)`.
4. Removed now-unused imports: `json`, `time`, `DZ_SESSION_FILE` (verified: only `_write_dz_session` used them).
5. Updated module docstring: removed the `_write_dz_session()` bullet from the Pillar 2 header.
6. **Surviving `ux_coordinator` tool untouched** — its output strings mentioning `auto_analyze_after_drop` are ST-7 scope (separate later delegation, explicitly excluded from this task).
7. Deleted `TestAutoAnalyzeWhiteboardDeprecated` test class (old L186-207) AND the now-orphaned `registered_ux_tools` fixture (old L100-110, only consumer was the deleted class) from `mcp-servers/tests/test_whiteboard_merge.py` + `extension/mcp-servers/tests/test_whiteboard_merge.py`.

### ST-2 — file_analyzer.py (×2 copies)
1. Added module-level `_write_dz_session(file_path)` verbatim from ux_coordinator.py, with a `[v2.1 B1]` provenance note in the docstring.
2. Root copy: added imports `time` and `from bridge.config import DZ_SESSION_FILE` (root previously lacked both; `os`/`json` already imported). Extension copy already imported `time` + `DZ_SESSION_FILE` (pre-existing); only the helper body was added.
3. Signature change:
   - Root: `def analyze_uploaded_file(file_path: str, track_dropzone: bool = False) -> str`
   - Extension: `def analyze_uploaded_file(file_path: str = "", track_dropzone: bool = False) -> str` (preserves extension's pre-existing no-arg listing mode; NOT introduced by me)
4. Function top: `if track_dropzone: _write_dz_session(file_path)` before the existing body (`return analyze_file(file_path)` / listing branch). Placement chosen so session tracking happens even when the file path is later found nonexistent — matches the old wrapper's behavior (it wrote the session before the existence check).
5. Docstring updated to document `track_dropzone` (dropzone session tracking for post-dropzone-upload analysis; default False).

## Result: ✅ Success

### Verification Evidence (actual outputs)

**1. py_compile (exit 0, all 4 tool files + both test copies):**
```
> python -m py_compile mcp-servers\...\ux_coordinator.py mcp-servers\...\file_analyzer.py extension\...\ux_coordinator.py extension\...\file_analyzer.py (+tests)
PY_COMPILE_OK  (re-run after final edit: FINAL_PY_COMPILE_OK)
```

**2. pytest root copy — 12/12 PASS after test class deletion:**
```
tests/test_whiteboard_merge.py::TestGetWhiteboardStateDefault ... 4 PASSED
tests/test_whiteboard_merge.py::TestGetWhiteboardStateAnalyze ... 4 PASSED
tests/test_whiteboard_merge.py::TestSuggestionHelper ... 2 PASSED
tests/test_whiteboard_merge.py::TestImageWhiteboard ... 2 PASSED
======================== 12 passed in 15.53s =============================
```
Note: initial run showed 2 FAILED in `TestGetWhiteboardStateDefault` — root-caused (see Issues #1) as a **pre-existing fixture bug** (non-yield `with patch(...)` expires before test body), environmental, unrelated to my edits. Proven by experiment: creating a fixture-shaped `~/.vibezoo-whiteboard.json` made all 12 pass; diagnostic file was deleted afterwards.

**3. Imports OK (run from mcp-servers so `bridge` resolves):**
```
> python -c "import bridge.tools.ux_coordinator, bridge.tools.file_analyzer; print('imports OK')"
imports OK
```

**4. Runtime behavior check (temp verify script, both trees, identical results; scripts recycled after use):**
```
ST-1 ux_coordinator tools: ['ux_coordinator']          ← auto_* registrations gone
ST-2 signature: (file_path: str, track_dropzone: bool = False) -> str        (root)
ST-2 signature: (file_path: str = '', track_dropzone: bool = False) -> str  (extension)
ST-2 single-arg call OK (returns error report, no TypeError)  ← backward compat
ST-2 _write_dz_session OK: uploaded.png
ST-2 track_dropzone=True records session for drop.png
ALL ST-1/ST-2 RUNTIME CHECKS PASSED
```

**5. grep removed names:**
```
ux_coordinator.py (both copies): _write_dz_session / auto_analyze_whiteboard → 0 hits.
auto_analyze_after_drop → exactly 2 hits, BOTH inside the surviving ux_coordinator
tool's OUTPUT STRINGS (plan-designated ST-7 scope, untouched per task constraint).
file_analyzer.py (both copies): _write_dz_session present (helper + call site).
```

**6. Mirror parity:**
- `tests/test_whiteboard_merge.py`: `fc /b` → **no differences encountered** (byte-identical across trees).
- `ux_coordinator.py` / `file_analyzer.py`: byte-level differences exist ONLY in the **pre-existing i18n drift zones** (extension uses `t()` wrappers, extra listing mode; documented in plan §0 L13 as known SHA drift). My edits are logically identical in both trees: same 3 deletions, same verbatim helper insertion, same signature change — verified by identical runtime check results above.

## Issues Discovered

1. **🟡 Pre-existing test fixture bug (root tree, both test copies)**: `registered_whiteboard_tools` / `wb_file_*` fixtures use `with patch(...): return mcp.tools` — the patches are exited when the `with` block ends (before the test body runs), so `get_whiteboard_state` reads the REAL `~/.vibezoo-whiteboard.json`. On a clean machine (file absent) `TestGetWhiteboardStateDefault::test_default_returns_state` and `test_default_has_hint_for_analyze` FAIL. Fix = convert fixtures to yield-style. **Not caused by my edits** (proven by experiment); out of my scope (test file edits were limited to the deprecated-alias class deletion).
2. **🟡 Pre-existing i18n drift (extension tree)**: extension `whiteboard.py` outputs English via `t()` ("Analysis Suggestions") while `extension/.../tests/test_whiteboard_merge.py` asserts Korean ("분석 제안") → 7 pre-existing failures in `TestGetWhiteboardStateAnalyze`/`TestSuggestionHelper`/`TestImageWhiteboard`. Verified directly: `_generate_whiteboard_suggestions()` returns English. **Not caused by my edits**; needs test-copy i18n update or translation-key fix — recommend routing to a future code delegation.
3. **🟢 Root vs extension `file_analyzer.py` functional divergence (pre-existing)**: extension has no-arg listing mode (`file_path: str = ""` → `_check_uploaded_files_impl()`) and `_check_uploaded_files` tool; root does not. Preserved as-is (surgical scope). The `track_dropzone` addition is identical in both.
4. **🟢 Working tree has 49 files of pre-existing uncommitted changes** (git diff --stat), including `whiteboard.py` (114 lines) and both test dirs are untracked — so no clean HEAD baseline exists for A/B pytest comparison. Mitigated with the controlled experiment described above.

## Next Step Recommendations
1. VP: commit ST-1/ST-2 (forbidden to me).
2. Route **ST-3** (github_diver deletion, bridge JSON list_subagents, intent_detector retarget) — independent files, can proceed now.
3. When scheduling **ST-7** (ux_coordinator output strings), include retargeting the two `auto_analyze_after_drop` suggestion strings found in this report.
4. Consider a small follow-up delegation to fix Issues #1 (yield-style fixtures) and #2 (extension test i18n asserts) — they will keep failing on clean machines regardless of this cleanup.
5. Pre-flight before smoke test: re-run `init_vibezoo.bat` to deploy the edited extension tree (plan §5).

## Affected File List
- `mcp-servers/bridge/tools/ux_coordinator.py` (ST-1: -3 functions, -3 imports, docstring)
- `extension/mcp-servers/bridge/tools/ux_coordinator.py` (ST-1: identical)
- `mcp-servers/bridge/tools/file_analyzer.py` (ST-2: +helper, +imports, signature, docstring)
- `extension/mcp-servers/bridge/tools/file_analyzer.py` (ST-2: +helper, signature, docstring; imports pre-existing)
- `mcp-servers/tests/test_whiteboard_merge.py` (ST-1: -1 test class, -1 orphaned fixture)
- `extension/mcp-servers/tests/test_whiteboard_merge.py` (ST-1: identical)
- Temporary (created + recycled): `mcp-servers/tests/_st12_verify.py`, `extension/mcp-servers/tests/_st12_verify.py`