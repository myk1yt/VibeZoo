# Project Research: Absolute Path & Local-Machine Reference Audit Report

**Date**: 2026-09-02 (17:33 KST)
**Scope**: Full repo sweep of `d:/OneDrive/Projects/VibeZoo` — all tracked files, all patterns
**Method**: 7 scan patterns via `search_files` (regex) + targeted `read_file` inspections
**Exclusions**: `.git/` internal data (findings noted but gitignored by nature), `node_modules/`, `__pycache__/`

---

## 1. Findings Table

| # | Pattern | File#LLine | Snippet | Classification | Recommended Fix |
|---|---------|-----------|---------|----------------|-----------------|
| **F1** | `k1yt` + `C:\Users` + `OneDrive` | [`HANDOFF.md#L42`](docs/260830_0001_session_reinstall-recovery-and-quality/HANDOFF.md:42) | `C:\Users\k1yt\AppData\Roaming\Code\User\globalStorage\...` | 🔴 LEAK-PRIVACY | Replace with `%APPDATA%\Code\User\globalStorage\...` (env-var form) |
| **F2** | `k1yt` + `OneDrive` | [`HANDOFF.md#L61`](docs/260830_0001_session_reinstall-recovery-and-quality/HANDOFF.md:61) | `cd c:/Users/k1yt/OneDrive/Projects/VibeZoo` | 🔴 LEAK-PRIVACY | Replace with `cd /d "%~dp0"` or generic `cd <repo-root>` |
| **F3** | `k1yt` + `C:\Users` | [`093000_project-research-report.md#L265`](docs/260830_0001_session_reinstall-recovery-and-quality/093000_project-research-report.md:265) | `C:\Users\k1yt\AppData\Roaming\Code\User\globalStorage\...` | 🔴 LEAK-PRIVACY | Genericize or archive-only; replace literal with `%APPDATA%\...` |
| **F4** | `k1yt` + `OneDrive` | [`093000_project-research-report.md#L273`](docs/260830_0001_session_reinstall-recovery-and-quality/093000_project-research-report.md:273) | `c:/Users/k1yt/OneDrive/Projects/VibeZoo/.roo/mcp.json` | 🔴 LEAK-PRIVACY | Genericize or archive-only; replace with relative path |
| **F5** | `DESKTOP-` hostname | `.git/logs/refs/heads/main` L1 (×4 log files) | `YONGTAI KIM <StefanoKim@DESKTOP-09GPFD1.(none)>` | 🟡 COSMETIC (git-internal) | Cannot fix without history rewrite; already gitignored by nature |
| **F6** | `k1yt` username + email | `.git/config` L16-17, `.git/config-myk1yt` L16-17 | `name = k1yt` / `email = myk1yt@gmail.com` | 🟢 OK (git-local) | Local git config; never pushed to remote |
| **F7** | `k1yt` (as `-myk1yt` suffix) | [`tool_context.py#L349`](mcp-servers/bridge/tool_context.py:349) | `# find_bugs는 integrated-myk1yt.py 변형이 참조하므로 유지` | 🟡 INTENTIONAL | Retention comment for personal fork; no path leak |
| **F8** | `OneDrive` | [`_st6_purge_nls.py#L23`](docs/260902_0001_session_vibezoo-tool-inventory-audit/_st6_purge_nls.py:23) | `EXT_DIR = os.path.join("d:", os.sep, "OneDrive", "Projects", "VibeZoo", "extension")` | 🔴 LEAK-CODE | Session audit helper script; contains hardcoded absolute path. Delete or rewrite with `os.path.dirname(__file__)` |
| **F9** | `OneDrive` | [`INSTALLATION.md#L160`](docs/INSTALLATION.md:160) | `C:\Projects\VibeZoo와 같은 순수 로컬 드라이브 경로로 이동` | 🟡 COSMETIC | Doc example uses a plausible generic path; no user-specific data |
| **F10** | `OneDrive` | [`ACTIVE_STATE-myk1yt.md#L40-41`](docs/ACTIVE_STATE-myk1yt.md:40) | `Windows OneDrive File Locking...` | 🟢 OK | General troubleshooting note; no user paths |
| **F11** | `C:\Users` | [`plans/error-collection-system-threat-analysis.md#L382`](plans/error-collection-system-threat-analysis.md:382) | `# Path.home() → "C:\\Users\\username"` | 🟢 OK | Code example in design doc; generic `username` placeholder |
| **F12** | `k1yt` (file names) | `extension/package-myk1yt.json`, `extension/l10n/bundle.l10n-myk1yt.json`, `init_vibezoo-myk1yt.bat`, `init_vibezoo-myk1yt.sh`, etc. | (filename only; `-myk1yt` suffix) | 🟡 INTENTIONAL | Personal fork naming convention; contents checked clean |
| **F13** | `k1yt` (email) | [`README.md#L359`](README.md:359), [`PROJECT_CONTEXT.md#L728`](docs/PROJECT_CONTEXT.md:728), [`README-myk1yt.md#L220`](README-myk1yt.md:220) | `myk1yt@gmail.com` | 🟢 OK | Contact email in public-facing docs; intentionally published |
| **F14** | `k1yt` (email) | [`init_vibezoo-myk1yt.bat#L79`](init_vibezoo-myk1yt.bat:79) | MCP JSON blob (no `k1yt` in content, only filename) | 🟡 INTENTIONAL | Personal installer variant |

---

## 2. Summary Counts

| Classification | Count | Push-Safe? |
|---------------|-------|------------|
| 🔴 LEAK-CODE | 1 (`_st6_purge_nls.py`) | ❌ No |
| 🔴 LEAK-PRIVACY | 4 (HANDOFF.md ×2, 093000 report ×2) | ❌ No |
| 🟡 COSMETIC | 3 (git-internal hostname, INSTALLATION doc example, docs referencing OneDrive as concept) | ⚠️ Acceptable but recommend cleanup |
| 🟡 INTENTIONAL | 4+ (all `-myk1yt` filename variants, retention comment) | ✅ By design |
| 🟢 OK | 5 (env-var paths, email contact, generic examples, `.gitignore`) | ✅ Safe |
| **Total actionable** | **5** (F1-F4 + F8) | |

---

## 3. Top-10 Must-Fix List

| Priority | Finding | Risk | File | Effort |
|----------|---------|------|------|--------|
| **P0** | F1-F2: `HANDOFF.md` contains literal `C:\Users\k1yt\...` and `c:/Users/k1yt/OneDrive/...` | Full username + home path exposed | [`HANDOFF.md#L42`](docs/260830_0001_session_reinstall-recovery-and-quality/HANDOFF.md:42), [`HANDOFF.md#L61`](docs/260830_0001_session_reinstall-recovery-and-quality/HANDOFF.md:61) | 5 min |
| **P1** | F3-F4: `093000_project-research-report.md` same literal paths | Full username + home path exposed | [`093000_project-research-report.md#L265`](docs/260830_0001_session_reinstall-recovery-and-quality/093000_project-research-report.md:265), [`093000_project-research-report.md#L273`](docs/260830_0001_session_reinstall-recovery-and-quality/093000_project-research-report.md:273) | 5 min |
| **P2** | F8: `_st6_purge_nls.py` hardcoded `d:\OneDrive\Projects\VibeZoo` | Hardcoded absolute path in executable Python | [`_st6_purge_nls.py#L23`](docs/260902_0001_session_vibezoo-tool-inventory-audit/_st6_purge_nls.py:23) | 2 min (delete or rewrite) |
| **P3** | F5: `.git/logs/` contains hostname `DESKTOP-09GPFD1` + real name | Machine identity in git history | `.git/logs/refs/heads/main` L1 | ⚠️ Requires `git filter-branch` / BFG; defer |

> **Note**: F1-F4 are the same pattern (hardcoded paths to the developer's home directory) in two documentation files from the `260830` session. F8 is a one-off session audit script. F5 is an immutable git history artifact.

---

## 4. Detailed Pattern-by-Pattern Analysis

### Pattern 1: `k1yt` (username)

**Non-.git, non-filename hits in tracked files:**

| Location | Context | Classification |
|----------|---------|---------------|
| [`README.md#L359`](README.md:359) | Contact email `myk1yt@gmail.com` | 🟢 OK (public contact) |
| [`docs/PROJECT_CONTEXT.md#L728`](docs/PROJECT_CONTEXT.md:728) | Same email | 🟢 OK |
| [`README-myk1yt.md#L220`](README-myk1yt.md:220) | Same email | 🟢 OK |
| [`mcp-servers/bridge/tool_context.py#L349`](mcp-servers/bridge/tool_context.py:349) | Comment: `integrated-myk1yt.py 변형이 참조하므로 유지` | 🟡 INTENTIONAL |
| [`extension/mcp-servers/bridge/tool_context.py#L349`](extension/mcp-servers/bridge/tool_context.py:349) | Same comment (mirror) | 🟡 INTENTIONAL |
| [`-p/i18n_verify_result.json#L29-149`](../-p/i18n_verify_result.json) | 87 filename matches in test result JSON | 🟡 INTENTIONAL |
| [`.gitignore` rules] | `-myk1yt` files ARE tracked (not gitignored) | Expected; these are intentional fork copies |

**`-myk1yt` filename variants (all INTENTIONAL):**
- `init_vibezoo-myk1yt.bat`, `init_vibezoo-myk1yt.sh`
- `extension/package-myk1yt.json`, `extension/package.nls-myk1yt.json` + 19 locale copies
- `extension/l10n/bundle.l10n-myk1yt.json` + 20 locale copies
- `extension/src/visual/VisualVibePanels-myk1yt.ts`
- `docs/PROJECT_CONTEXT-myk1yt.md`, `docs/ARCHITECTURE_CORE-myk1yt.md`, `docs/ACTIVE_STATE-myk1yt.md`
- `README-myk1yt.md`

### Pattern 2: `C:\Users` / `C:/Users`

| Location | Context | Classification |
|----------|---------|---------------|
| [`plans/error-collection-system-threat-analysis.md#L382`](plans/error-collection-system-threat-analysis.md:382) | `# Path.home() → "C:\\Users\\username"` (code example) | 🟢 OK (generic placeholder) |
| [`HANDOFF.md#L42`](docs/260830_0001_session_reinstall-recovery-and-quality/HANDOFF.md:42) | `C:\Users\k1yt\AppData\Roaming\...` | 🔴 LEAK-PRIVACY |
| [`093000_project-research-report.md#L265`](docs/260830_0001_session_reinstall-recovery-and-quality/093000_project-research-report.md:265) | `C:\Users\k1yt\AppData\Roaming\...` | 🔴 LEAK-PRIVACY |

### Pattern 3: `OneDrive`

| Location | Context | Classification |
|----------|---------|---------------|
| [`INSTALLATION.md#L157-160`](docs/INSTALLATION.md:157) | Troubleshooting note about OneDrive file locks | 🟢 OK (general guidance) |
| [`ACTIVE_STATE-myk1yt.md#L40`](docs/ACTIVE_STATE-myk1yt.md:40) | `Windows OneDrive File Locking` note | 🟢 OK (general guidance) |
| [`architecture-plan.md#L267`](docs/260830_0001_session_reinstall-recovery-and-quality/architecture-plan.md:267) | `Windows OneDrive 환경에서 정션 불안정` | 🟢 OK (design rationale) |
| [`HANDOFF.md#L61`](docs/260830_0001_session_reinstall-recovery-and-quality/HANDOFF.md:61) | `cd c:/Users/k1yt/OneDrive/Projects/VibeZoo` | 🔴 LEAK-PRIVACY |
| [`093000_project-research-report.md#L273`](docs/260830_0001_session_reinstall-recovery-and-quality/093000_project-research-report.md:273) | `c:/Users/k1yt/OneDrive/Projects/VibeZoo/.roo/mcp.json` | 🔴 LEAK-PRIVACY |
| [`_st6_purge_nls.py#L23`](docs/260902_0001_session_vibezoo-tool-inventory-audit/_st6_purge_nls.py:23) | `os.path.join("d:", os.sep, "OneDrive", "Projects", "VibeZoo", "extension")` | 🔴 LEAK-CODE |
| Other `docs/archive/`, `docs/260725_*`, `docs/260902_*` | Mention "OneDrive" as concept (not paths) | 🟢 OK |

### Pattern 4: `D:\` / Drive-letter absolute paths

**Zero hits** in tracked files. Clean.

### Pattern 5: `DESKTOP-` / hostname

| Location | Context | Classification |
|----------|---------|---------------|
| `.git/logs/refs/heads/main` L1 | `StefanoKim@DESKTOP-09GPFD1.(none)` (clone origin) | 🟡 COSMETIC (git-internal; not pushed to remote as a separate file but is in `.git` history) |
| `.git/logs/refs/heads/main-myk1yt` L1 | Same | 🟡 COSMETIC |
| `.git/logs/HEAD` L1 | Same | 🟡 COSMETIC |
| `.git/logs/HEAD-myk1yt` L1 | Same | 🟡 COSMETIC |

**Note**: `.git/logs/` is per-clone data and is never pushed. The `DESKTOP-09GPFD1` hostname exists only in the local clone history. No impact on remote push.

### Pattern 6: Hardcoded `C:\` in `.bat` files

**Zero hits.** All `.bat` scripts use `%USERPROFILE%`, `%APPDATA%`, `%~dp0` (relative), `%LOCALAPPDATA%`, `%SYSTEMROOT%` — fully portable.

### Pattern 7: `.gitignore` adequacy

The `.gitignore` correctly excludes:
- `node_modules/`, `extension/out/`, `dist/`, `build/` (build artifacts)
- `__pycache__/`, `*.pyc` (Python cache)
- `.zoo-code/` (runtime data)
- `.vscode/`, `*.vsix` (IDE/packaging)
- `*.bak`, `*.log`, `venv/` (temp/runtime)
- `%APPDATA%/`, `APPDATA/` (unexpanded env-var dirs)

**Not gitignored (and correctly so):**
- `.git/config`, `.git/logs/` — these are git-internal and never pushed to remote
- `.git/config-myk1yt` — this is a personal variant config file, tracked intentionally

---

## 5. Production Code Assessment

### Extension TypeScript (`extension/src/**/*.ts`)
**0 hits** for any local-machine pattern. The extension uses env-var-based path resolution throughout:
- [`McpConfigService.ts`](extension/src/mcp/McpConfigService.ts) — uses `%APPDATA%` for MCP config paths
- [`SubagentManager.ts`](extension/src/orchestra/SubagentManager.ts), [`FixLoopManager.ts`](extension/src/orchestra/FixLoopManager.ts), [`MentionRouter.ts`](extension/src/orchestra/MentionRouter.ts) — no path references

### Extension JSON configs (`extension/package*.json`, `extension/l10n/*.json`)
**0 hits** for local-machine patterns. The `-myk1yt` JSON variants contain identical content to their canonical counterparts (only the filename differs).

### MCP Bridge Python (`mcp-servers/**/*.py`, `extension/mcp-servers/**/*.py`)
**0 hits** for absolute paths or local references. The only `k1yt` match is the retention comment in [`tool_context.py#L349`](mcp-servers/bridge/tool_context.py:349).

### Installer scripts (`.bat`, `.sh`)
All use env-var-based paths:
- [`init_vibezoo.bat`](init_vibezoo.bat:2) — `%USERPROFILE%\mcp-servers\vibezoo`
- [`init_vibezoo.sh`](init_vibezoo.sh:4) — `$HOME/mcp-servers/vibezoo`
- [`init_vibezoo-myk1yt.bat`](init_vibezoo-myk1yt.bat:3) — `%USERPROFILE%\mcp-servers\vibezoo`
- [`start_vibezoo_bridge.bat`](start_vibezoo_bridge.bat:14) — `%LOCALAPPDATA%\Programs\Python\...` (fallback)
- [`start_vibezoo_servers.bat`](start_vibezoo_servers.bat:12) — `%USERPROFILE%\.vibezoo`, `%~dp0` (relative)

**Verdict: All installer scripts are fully portable.** ✅

---

## 6. Push-Safety Verdict

### 🟡 CONDITIONALLY PUSH-SAFE — 3 files need cleanup first

**The repo IS safe to push if:**

1. **F1-F4** are fixed: Replace 2 hardcoded `C:\Users\k1yt\...` path instances in [`HANDOFF.md`](docs/260830_0001_session_reinstall-recovery-and-quality/HANDOFF.md) and [`093000_project-research-report.md`](docs/260830_0001_session_reinstall-recovery-and-quality/093000_project-research-report.md) with generic env-var forms or relative paths.

2. **F8** is addressed: Either delete or rewrite [`_st6_purge_nls.py`](docs/260902_0001_session_vibezoo-tool-inventory-audit/_st6_purge_nls.py) to use `os.path.dirname(__file__)` instead of the hardcoded OneDrive path. (This is a session audit helper script, not production code.)

**No changes needed for:**
- Extension source code (`.ts`, `.py`, `.json`) — fully clean
- Installer scripts (`.bat`, `.sh`) — fully portable
- `-myk1yt` variant files — intentional by design
- `.git/` internal data — never pushed
- Contact email in README/docs — intentional public contact
- Design docs using generic examples

**Note on F5 (hostname)**: The hostname `DESKTOP-09GPFD1` in `.git/logs/` is a git-internal artifact of the initial clone. It exists only in the local `.git/` directory and is never pushed to the remote. No action needed unless the user wants to rewrite history with BFG.

---

## 7. Effort Estimate

| Task | Files | Time |
|------|-------|------|
| Fix F1-F2 (HANDOFF.md) | 1 | 5 min |
| Fix F3-F4 (093000 report) | 1 | 5 min |
| Fix F8 (_st6_purge_nls.py) | 1 | 2 min |
| **Total** | **3 files** | **~12 min** |

---

*Report generated by 🔍 Project Research mode — read-only audit, no modifications made.*
