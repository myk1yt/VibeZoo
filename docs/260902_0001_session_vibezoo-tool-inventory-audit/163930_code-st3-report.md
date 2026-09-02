# Code Task Report — ST-3 (A2 + A3 ghost): dead file + bridge JSON + intent hints

- Session: `docs/260902_0001_session_vibezoo-tool-inventory-audit/`
- Mode: code · Time: 2026-09-02 16:39 KST
- User intent: "전면 정리 (A1-B3): 집계형 도구(find_bugs, suggest_refactor, generate_docs, learn_project)도 제거하고 프롬프트 조합으로 대체" (approved, `decisions.md`)
- Scope: ST-3 only. ST-1/ST-2 files (ux_coordinator.py, file_analyzer.py) untouched.

## Task Summary
Deleted dead `github_diver.py` (both mirror copies), purged removed/ghost tool names from `list_subagents` in both `vibezoo_mcp_bridge.py` copies, and retargeted the two stale `next_tool` hints in both `intent_detector.py` copies to live tools.

## Actions Taken

### 1. Pre-deletion safety check
- Searched both trees for `github_diver|explore_github` → only self-references inside the two `github_diver.py` files themselves (tips in output strings, function def, `register()`).
- Searched all `*.py` for `from bridge.tools.github_diver|import github_diver` → **0 hits**. No external importers. Safe to delete.

### 2. Deleted dead files (Recycle Bin, per guardrails)
- `mcp-servers/bridge/tools/github_diver.py` → Recycle Bin
- `extension/mcp-servers/bridge/tools/github_diver.py` → Recycle Bin
- Post-delete `Test-Path` on both → `False`, `False` (confirmed gone)
- Command: `[Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile(..., 'OnlyErrorDialogs', 'SendToRecycleBin')` — no permanent deletion used.

### 3. Purged names from `list_subagents` — both bridge copies
Identical edits applied to `mcp-servers/vibezoo_mcp_bridge.py` and `extension/mcp-servers/vibezoo_mcp_bridge.py`:

| Entry | Before | After |
|---|---|---|
| Integrated [L58] | `["review_project", "find_bugs", "suggest_refactor", "generate_docs"]` | `["review_project"]` |
| Knowledge [L60] | `["learn_project", "recall_project", "learn_preference", "get_preferences"]` | `["recall_project", "learn_preference", "get_preferences"]` |
| Editor [L64] | `["apply_patch", "read_project_file"]` | `["apply_patch"]` |

- UX entry check: no `auto_analyze_after_drop` / `auto_analyze_whiteboard` names existed in `list_subagents` in either copy (Whiteboard entry holds only `draw_on_whiteboard`, `get_whiteboard_state`, `capture_screen` [+`check_uploaded_files` root copy]) — nothing to remove there.

### 4. Retargeted intent hints — both intent_detector.py copies
Identical edits in `mcp-servers/bridge/intent_detector.py` and `extension/mcp-servers/bridge/intent_detector.py` (`get_workflow_hints`):
- `file_share` hint [L403]: `"next_tool": "auto_analyze_after_drop"` → `"analyze_uploaded_file"`; description updated to mention `analyze_uploaded_file(file_path, track_dropzone=True)`
- `whiteboard_input` hint [L417]: `"next_tool": "auto_analyze_whiteboard"` → `"get_whiteboard_state"` (adjacent description already said "상태를 읽고 분석", consistent with `get_whiteboard_state(analyze=True)`; no text change needed)

## Verification Evidence (actual outputs)

**1. py_compile — exit 0**
```
python -m py_compile mcp-servers\vibezoo_mcp_bridge.py extension\mcp-servers\vibezoo_mcp_bridge.py mcp-servers\bridge\intent_detector.py extension\mcp-servers\bridge\intent_detector.py
→ PY_COMPILE_OK exit=0
```

**2. Ghost-name sweep — `github_diver|explore_github|read_project_file` → 0 hits in both trees.**
Remaining `auto_analyze*` mentions (all ST-7 scope, docstrings/output strings only — no executable references to removed tools):
- `mcp-servers/bridge/tools/ux_coordinator.py:86` — output string suggesting `auto_analyze_after_drop(file_path=...)` call (ST-7 designated)
- `extension/mcp-servers/bridge/tools/ux_coordinator.py:86` — same, i18n'd variant `t("Suggest calling ...")` (ST-7 designated)
- `mcp-servers/bridge/tools/file_analyzer.py:19` — module docstring noting the v2.1 B1 move (descriptive, harmless)
- `extension/mcp-servers/bridge/tools/file_analyzer.py:19` — same
- `mcp-servers/bridge/tools/whiteboard.py:872,890,894,1036,1096` — docstrings referencing the deprecated `auto_analyze_whiteboard()` / `auto_analyze_after_drop()` descriptively
- `extension/mcp-servers/bridge/tools/whiteboard.py:872,890,894,1035,1095` — same
- intent_detector.py itself: 0 hits after retargeting ✓

**3. Import check — exit 0**
```
cd mcp-servers && python -c "import bridge.tools; print('tools OK')"  → tools OK
cd extension\mcp-servers && python -c "import bridge.tools; ..."      → tools OK ext
```

**4. Mirror parity (temp verify script, hash + line diff; script deleted after use)**
```
intent_detector copies byte-identical: True (sha16 aabb021bdbc7ad26 both)
Edited bridge lines L58/L60/L64: match=True in both copies
Bridge file-level diff (pre-existing, documented, NOT from ST-3):
  L56 Whiteboard: root has extra "check_uploaded_files"
  L65 FileAnalyzer: root has extra "check_uploaded_files"
  → this is the documented i18n-zone/pre-existing drift; edited lines themselves are identical.
```

## Issues Discovered
1. `list_subagents` UX entry contained no auto_* names — the delegation anticipated this possibility ("if present"); nothing removed, no action needed.
2. The L56/L65 `check_uploaded_files` asymmetry between bridge copies predates ST-3 (ST-1/ST-2 scope removed the ext-side registration context differently). Flagging to VP: not ST-3 scope, but worth deciding in ST-7 whether root's Whiteboard/FileAnalyzer entries should drop `check_uploaded_files` too (tool still exists — likely fine to keep as-is; only noting the drift).
3. `whiteboard.py` has 5 docstring lines mentioning deprecated tools — included in the ST-7 string-purge list above so they aren't missed.

## Next Step Recommendations
1. VP: commit ST-3 (forbidden to me). Suggested message: `refactor(mcp): delete dead github_diver tool and purge removed tool names from bridge metadata (ST-3)`
2. Route ST-4/ST-5 (integrated.py, knowledge.py aggregate removal) — independent of ST-3 files.
3. ST-7: purge the exact remaining `auto_analyze*` strings listed under Verification #2.

## Affected File List
- DELETED: `mcp-servers/bridge/tools/github_diver.py` (Recycle Bin)
- DELETED: `extension/mcp-servers/bridge/tools/github_diver.py` (Recycle Bin)
- EDITED: `mcp-servers/vibezoo_mcp_bridge.py` (L58, L60, L64)
- EDITED: `extension/mcp-servers/vibezoo_mcp_bridge.py` (L58, L60, L64)
- EDITED: `mcp-servers/bridge/intent_detector.py` (L403-404, L417)
- EDITED: `extension/mcp-servers/bridge/intent_detector.py` (L403-404, L417)
- TEMP (deleted): `docs/260902_0001_session_vibezoo-tool-inventory-audit/_st3_verify.py` (Recycle Bin)