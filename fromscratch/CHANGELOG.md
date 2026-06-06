# Changelog

## v0.14.4 (2026-06-06)

### 🆕 New Feature: Multi-language Analysis Engine Enhancement

VibeZoo Bridge's `review_code` and `find_bugs` tools now support C++, Rust (full AST), Go (enhanced), Shell, Dockerfile, YAML/JSON.

#### C++ Support (AST-based)
- Raw pointer avoidance check, new/delete mismatch detection, bounds checking bypass (`[]` vs `.at()`), missing RAII lock, C-style cast, printf/scanf
- config.py: Added C++ extensions to SOURCE_EXTS

#### Rust AST Full Analysis
- unsafe block complexity control, silenced Result/Option, panic/unwrap!, clone overuse, `as` cast, println! debug

#### Go Analysis Enhancement
- Goroutine loop variable capture, missing recover() in defer, unbuffered channel deadlock, missing Mutex Unlock, nil map assignment

#### General Source File Support
- Shell Script: Missing quotes, `set -e`/`pipefail`, shellcheck integration
- Dockerfile: latest tag, apt-get cache, missing USER, ADD vs COPY
- YAML/JSON: Duplicate keys, hardcoded secrets

#### find_bugs Native Linter Integration
- Rust: `cargo clippy --frozen`
- Go: `go vet -mod=readonly`
- C++: `cppcheck --enable=all --xml`

### 🐛 Bug Fixes
- Fixed Dockerfile review path blocking (handling files without extension)
- Regex improvements: C++ raw pointer, Rust as cast, Go goroutine capture, Shell variables, etc.
- Increased subprocess timeout (cargo/cppcheck 120s, go vet 60s)
- Use xml.etree.ElementTree for cppcheck XML parsing
- Security: cargo clippy --frozen, go vet -mod=readonly

## v0.14.3 (2026-06-05)

### 🆕 New Feature: Guard.git
- `.git` folder deletion prevention (OS-level ACL: Windows icacls / Linux chattr / macOS chmod)
- Guard.git On/Off toggle node in VibeZoo sidebar Active Subagents
- Multi-root workspace support
- Git Worktree compatibility
- Yocto snapshot + SelfCheck integrity diagnostics

### 🐛 Bug Fixes
- **Shell injection prevention**: `exec()` → `execFile()` migration, path validation, 10-second timeout
- **sudo hang prevention**: Linux `sudo` usage prohibited, immediate Watcher+Yocto fallback
- **Multi-root support**: Full iteration of `workspaceFolders` array, dynamic folder change handling
- **Korean path issue**: Changed `SAFE_PATH_REGEX` to `DANGEROUS_PATH_REGEX` (allows Unicode characters)
- **Race condition**: Added `await` to `activate()`/`enable()` to guarantee sequential execution
- **Residual ACL cleanup**: Automatic cleanup on Extension restart after crash
- **Empty gitDirPaths false success**: Returns `{success:false}` when `.git` is absent
- **User notification**: Displays `showWarningMessage` on enable failure

### 🔧 Maintenance
- TypeScript compilation + installed extension directory synchronization
- `out/` directory Git tracking (bypassing `.gitignore`)
- l10n: English/Korean localization
