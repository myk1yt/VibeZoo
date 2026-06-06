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
