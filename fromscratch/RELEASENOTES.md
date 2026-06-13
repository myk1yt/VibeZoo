# VibeZoo v0.15.0 Release Notes

**Release Date**: 2026-06-13

## 🛠 Auto-Connect Fundamental Fix

This release fixes the root cause of VibeZoo failing to auto-connect when Zoo Code already had a global MCP configuration containing a `vibezoo` entry.

### What was fixed
- Previously, `autoConfigureMCP()` skipped writing the project-level `.roo/mcp.json` whenever it detected that the global Zoo Code `mcp_settings.json` already defined a `vibezoo` server. On a fresh clone or after resetting the workspace, Zoo Code therefore never received the correct SSE endpoint for the local Bridge.
- The old `crow_memory_server.py` was a stub that printed a deprecation warning and immediately exited with `sys.exit(0)`, so Crow health checks always failed when no external Crow server was running.
- The Python MCP Bridge and its dependencies lived under the workspace root `mcp-servers/`, which was **not** bundled into the VSIX. Installed extensions could not locate the bridge script at runtime.
- Bridge/Crow spawn logic relied on a hardcoded `python` command and failed on systems where only `python3` is available (macOS/Linux) or where the interpreter is inside a virtual environment.

### Why it happened
- The MCP configuration logic treated the **global** Zoo Code settings as authoritative and assumed that a global entry guaranteed local connectivity. In practice, the global entry often pointed to a different port, host, or stale workspace, so the project-level `.roo/mcp.json` was never created or updated.
- The Crow fallback was designed as a placeholder, with the expectation that a separate Crow Memory repository would always be present. This assumption broke standalone VibeZoo usage.
- The extension packaging ignored Python assets because `mcp-servers/` sat outside the `extension/` folder and `.vscodeignore` did not explicitly include it.

### How it was resolved
1. **Always write `.roo/mcp.json`**
   The new [`McpConfigService`](extension/src/mcp/McpConfigService.ts) reads the global `mcp_settings.json` only for logging/reference and unconditionally merges/updates the project `.roo/mcp.json`. Other user-defined servers in the file are preserved.

2. **Real Crow fallback server**
   [`extension/mcp-servers/crow_memory_server.py`](extension/mcp-servers/crow_memory_server.py) is now a real HTTP server. It detects an external Crow server and switches to Proxy mode; otherwise it serves an in-memory `/health`, `/ingest`, and `/recall` API. It no longer exits immediately.

3. **Deterministic Python discovery**
   [`PythonResolver`](extension/src/python/PythonResolver.ts) searches candidates in order: user setting → `.venv`/`venv` → `pyenv` → `python3` → `python` → Windows `py -3`, validating each with `--version`.

4. **Cross-platform VS Code paths**
   [`VscodePaths`](extension/src/platform/VscodePaths.ts) computes Stable/Insiders-aware config directories for Windows, macOS, and Linux so global MCP settings are located correctly everywhere.

5. **VSIX bundling**
   `mcp-servers/` was moved into `extension/mcp-servers/`, making the bridge and Crow fallback part of the packaged extension. Path resolution now uses `context.extensionPath` consistently.

6. **Self-recovery**
   [`SelfCheck`](extension/src/safety/SelfCheck.ts) registers a Bridge restart callback. If the Bridge or MCP config check fails, `autoRecover()` can terminate and respawn the Bridge and rewrite `.roo/mcp.json`.

### Files changed
- **New**: `extension/src/mcp/McpConfigService.ts`
- **New**: `extension/src/python/PythonResolver.ts`
- **New**: `extension/src/platform/VscodePaths.ts`
- **Moved**: `mcp-servers/` → `extension/mcp-servers/`
- **Modified**: `extension/src/extension.ts`, `extension/src/orchestra/SubagentManager.ts`, `extension/src/crow/CrowServerManager.ts`, `extension/src/safety/SelfCheck.ts`, `extension/src/ui/StatusBarManager.ts`, `extension/.vscodeignore`

---

# VibeZoo v0.14.4 Release Notes

**Release Date**: 2026-06-06

## 🆕 New Feature: Multi-language Analysis Engine Enhancement

VibeZoo Bridge's `review_code` and `find_bugs` tools now support C++, Rust (full AST), Go (enhanced), Shell, Dockerfile, YAML/JSON.

### C++ Support (AST-based)
- Raw pointer avoidance check, new/delete mismatch detection, bounds checking bypass (`[]` vs `.at()`), missing RAII lock, C-style cast, printf/scanf
- config.py: Added C++ extensions to SOURCE_EXTS

### Rust AST Full Analysis
- unsafe block complexity control, silenced Result/Option, panic/unwrap!, clone overuse, `as` cast, println! debug

### Go Analysis Enhancement
- Goroutine loop variable capture, missing recover() in defer, unbuffered channel deadlock, missing Mutex Unlock, nil map assignment

### General Source File Support
- Shell Script: Missing quotes, `set -e`/`pipefail`, shellcheck integration
- Dockerfile: latest tag, apt-get cache, missing USER, ADD vs COPY
- YAML/JSON: Duplicate keys, hardcoded secrets

### find_bugs Native Linter Integration
- Rust: `cargo clippy --frozen`
- Go: `go vet -mod=readonly`
- C++: `cppcheck --enable=all --xml`

### 🐛 Bug Fixes
- Fixed Dockerfile review path blocking (handling files without extension)
- Regex improvements: C++ raw pointer, Rust as cast, Go goroutine capture, Shell variables, etc.
- Increased subprocess timeout (cargo/cppcheck 120s, go vet 60s)
- Use xml.etree.ElementTree for cppcheck XML parsing
- Security: cargo clippy --frozen, go vet -mod=readonly

---

## 🆕 New Feature: Guard.git (v0.14.3)

Prevents AI agents from accidentally running `rm -rf *` / `rmdir /s /q` etc. and completely deleting the project's `.git` folder.

### Key Features
- **OS-level ACL Protection**: Windows `icacls` / Linux `chattr` / macOS `chmod` blocks `.git` folder deletion
- **VibeZoo Tab Toggle**: One-click Guard.git On/Off control from TreeView
- **Multi-root Workspace Support**: Simultaneous protection of multiple project folders
- **Git Worktree Compatibility**: Tracks and protects actual git directory in Worktree environments
- **FileSystemWatcher**: Real-time monitoring of `.git` deletion/rename
- **Yocto Snapshot**: Periodic backup of `.git` core files (HEAD, config, refs)
- **SelfCheck Integration**: `.git` integrity self-diagnostics

### Security Enhancements
- Uses only `execFile()` to prevent Shell injection (CVE prevention)
- Linux `sudo` usage prohibited (VS Code Extension has no TTY)
- Path validation regex + 10-second timeout
- Automatic residual ACL cleanup (Extension crash recovery)

### Configuration
- `vibezoo.guard.enabled`: Enable Guard.git overall (default: true)
- `vibezoo.guard.autoEnable`: Auto-activate on YOLO mode entry (default: true)
- `vibezoo.guard.yoctoBackupEnabled`: Use .git snapshots (default: true)
- `vibezoo.guard.yoctoBackupIntervalMin`: Snapshot interval (default: 30 min)
- `vibezoo.guard.integrityCheckIntervalMin`: Integrity diagnostic interval (default: 5 min)
- `vibezoo.guard.linuxUseChattr`: Use chattr on Linux (default: false)

### 🐛 Bug Fixes (v0.14.3)
- **Korean path issue**: Changed `SAFE_PATH_REGEX` to `DANGEROUS_PATH_REGEX` to allow Unicode characters (including Korean)
- **Race condition fix**: Added `await` to `activate()`/`enable()` to guarantee sequential execution
- **Extension loading path synchronization**: Resolved Guard.git operation mismatch by synchronizing TypeScript compilation with installed extension directory
- **Shell injection prevention**: Migrated `exec()` → `execFile()`, added path validation regex + 10-second timeout
- **sudo hang prevention**: Linux `sudo` usage prohibited, immediate switch to Watcher+Yocto fallback
- **Residual ACL cleanup**: Automatic cleanup on Extension restart after crash (`_cleanupResidualACL`)
- **Empty gitDirPaths false success**: Returns `{success:false}` when `.git` is absent
- **User notification**: Displays `showWarningMessage` on enable failure
