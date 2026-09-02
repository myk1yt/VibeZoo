# Code-Light Urgent Fix Report: editor.py f-string backslash SyntaxError (Python 3.11)

**Session Folder**: `docs/260902_0001_session_vibezoo-tool-inventory-audit/`
**Report Time**: 18:45 KST (2026-09-02)
**Mode**: code-light

## Task Summary

Fix Python 3.11 `SyntaxError: f-string expression part cannot include a backslash` at [`extension/mcp-servers/bridge/tools/editor.py:483`](../../extension/mcp-servers/bridge/tools/editor.py:483) blocking the deployed bridge, sweep all `bridge/**/*.py` in both trees with the venv Python 3.11 `py_compile`, and run the pytest regression suite.

## Root Cause

Deployed copy of editor.py (line 483) embeds a backslash literal inside an f-string expression:

```python
output += f"원본 SEARCH (처음 80자): `{failed_search[:80].replace(chr(10), '\\\\n')}`\n"
```

Backslash literals in f-string *expressions* are only legal in Python 3.12+ (PEP 701). The deployed venv runs **Python 3.11.9**, so the bridge fails at import time and stays DOWN.

**Key finding**: The fix already exists in both repo trees. Lines 483-485 in both
[`mcp-servers/bridge/tools/editor.py:483`](../../mcp-servers/bridge/tools/editor.py:483) and
[`extension/mcp-servers/bridge/tools/editor.py:483`](../../extension/mcp-servers/bridge/tools/editor.py:483)
already contain the 3.11-compatible hoisted form:

```python
output += f"실패한 블록의 SEARCH 텍스트와 가장 유사한 실제 코드를 찾지 못했습니다.\n"
search_preview_80 = failed_search[:80].replace("\n", "\\n")
output += f"원본 SEARCH (처음 80자): `{search_preview_80}`\n"
```

The backslash replace is hoisted into a local variable before the f-string. **The deployed trees were simply not synced with the repo** — no code edit was required in the repo.

## Actions Taken

1. Read both repo `editor.py` copies around line 483 — confirmed hoisted fix already present in both.
2. Searched both `bridge/tools` trees for residual bad patterns (`chr(10)`, `chr(13)`, in-f-string `\\n` literals) — **0 matches**; also confirmed `search_preview = search_text[:80].replace('\n', '\\n')` at editor.py:583-584 is a normal (non-f-string) statement, which is legal in 3.11.
3. Read the deployed copy (`C:\Users\k1yt\mcp-servers\vibezoo\extension\mcp-servers\bridge\tools\editor.py`) — still contains the broken line 483 (619 total lines vs 622 in repo; stale).
4. Wrote sweep script: [`_fstring311_verify.py`](../../docs/260902_0001_session_vibezoo-tool-inventory-audit/_fstring311_verify.py)
5. Ran the sweep with the venv Python 3.11 over 4 roots.
6. Ran pytest regression.
7. Verified repo line parity between the two trees.

## Verification Results

### 1. Python 3.11 py_compile sweep (venv `3.11.9`, 155 files across 4 roots)

| Root | Result |
|---|---|
| `mcp-servers/bridge/**/*.py` (repo, 37 files) | ✅ ALL PASS |
| `extension/mcp-servers/bridge/**/*.py` (repo, 48 files incl. -myk1yt variants) | ✅ ALL PASS |
| `C:\Users\k1yt\mcp-servers\vibezoo\extension\mcp-servers\bridge\**` (deployed) | ❌ 1 FAIL |
| `C:\Users\k1yt\mcp-servers\vibezoo\mcp-servers\bridge\**` (deployed) | ❌ 1 FAIL |

**Summary line**: `Result: 153/155 pass, 2 fail`

**The only 2 failures are the deployed `editor.py` copies** (both trees), failing at exactly line 483:

```
File "C:\Users\k1yt\mcp-servers\vibezoo\extension\mcp-servers\bridge\tools\editor.py", line 483
    output += f"원본 SEARCH (처음 80자): `{failed_search[:80].replace(chr(10), '\\\\n')}`\n"
SyntaxError: f-string expression part cannot include a backslash

File "C:\Users\k1yt\mcp-servers\vibezoo\mcp-servers\bridge\tools\editor.py", line 483
    output += f"원본 SEARCH (처음 80자): `{failed_search[:80].replace(chr(10), '\\\\n')}`\n"
SyntaxError: f-string expression part cannot include a backslash
```

No other file in any tree has the 3.12-only f-string pattern. Full per-file output preserved in command artifact (155 PASS/FAIL lines).

### 2. pytest regression (`cd mcp-servers && python -m pytest tests/ -q`)

```
........................................................................ [ 72%]
............................                                             [100%]
100 passed in 15.96s
```

✅ **100/100 pass** (exit 0). Note: system `python` used for pytest (venv lacks pytest module); the venv 3.11 was used for the py_compile syntax sweep as required.

### 3. Repo editor.py parity (the target line region)

Full-file SHA256 differs between trees (expected — trees have other known divergences), but the **f-string fix region is byte-identical**:

```
root L483-485 == ext L483-485  →  line parity: True

root : 6A207E1CF0F5C543135638428886BD672544B5A3A795086D7FB0189BCD897C1E  (mcp-servers/bridge/tools/editor.py)
ext  : 0781756F03DAD072C4939C0FBA0B5E55F97B3727D7D2367121BF1B5B4667B5BB  (extension/mcp-servers/bridge/tools/editor.py)
```

## Result

✅ **Success (scope: fix + 3.11 verification only)**

- Repo trees: both already 3.11-clean, fix region parity confirmed — no code change needed.
- Deployed trees: still stale with the broken line — **redeploy + bridge restart is VP's action** (per scope). Redeploying the fixed repo `editor.py` to `C:\Users\k1yt\mcp-servers\vibezoo\` in both `extension\mcp-servers\bridge\tools\` and `mcp-servers\bridge\tools\` will resolve both failures.
- The 3.11 sweep found **no additional files** with 3.11-incompatible f-string backslashes.

## Issues Discovered

- **Deployed tree is stale beyond editor.py**: the deployed extension tree is missing repo files present locally (e.g., `github_diver.py` exists deployed but there are file-count differences: repo ext tree has 48 files incl. `-myk1yt` variants, deployed has fewer and no `-myk1yt` variants). Redeploy should sync the full bridge tree, not just editor.py.
- Minor: venv has no `pytest` installed; regression tests must run with system Python.

## Next Step Recommendations (for VP)

1. **Redeploy now**: copy fixed repo `editor.py` (or full bridge trees) to `C:\Users\k1yt\mcp-servers\vibezoo\` × both locations, then re-run `_fstring311_verify.py` (expect 155/155) and restart the bridge.
2. Consider adding a CI/pre-deploy gate that runs the 3.11 `py_compile` sweep to catch 3.12-only syntax before deployment.
3. Consider installing `pytest` into the venv for self-contained verification.

## Affected File List

- No source files modified (repo already fixed; deployed tree is VP's redeploy scope).
- Created (verification tooling only):
  - `docs/260902_0001_session_vibezoo-tool-inventory-audit/_fstring311_verify.py`
  - `docs/260902_0001_session_vibezoo-tool-inventory-audit/184500_code-light-editor-fstring-report.md` (this file)