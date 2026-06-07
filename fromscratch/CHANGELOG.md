# Changelog

## [0.14.5] - 2026-06-07

### UX Upgrade — Pillar 1 & 2
- **Smart Ellipsis Patching**: `apply_patch` now detects and resolves `// ...` / `# ...` / `/* ... */` placeholders using AST-guided wildcard resolution
- **Transactional Apply**: Dry-run all blocks in memory, commit only if all succeed, rollback on any failure
- **Crow-Aware Intent**: `ux_coordinator` now queries Crow Memory for recent context when keyword matching is uncertain
- **Dropzone Binding**: Automatically detects recently uploaded files (within 3 min) and routes intent to file analysis
- **fix_loop Intent**: New intent signature for bug fix / error recovery scenarios

### Fixed
- `search_codebase`: `_fallback_to_walk` 확장자 제한 해제 — `.md`, `.txt`, `.toml` 등 모든 파일 검색 가능
- `search_codebase`: `mode` 파라미터(`exact`/`fuzzy`/`ast`/`semantic`)가 실제 동작하도록 수정
- `search_codebase`: ripgrep 미설치 경고를 HTML 주석에서 블록쿼트로 변경 (AI가 인지 가능)
- `search_codebase`: `is_ast_query` 조건 완화 — 단일 심볼명도 AST 검색 활성화
- `search_codebase`: `_parse_ripgrep_output` 컨텍스트 수집 개선 (`context_after` 정상 동작)
- `search_codebase`: `_fallback_to_walk` 패턴 매칭 로직 단순화
- `ResultRanker` 데드코드 통합 (`scout.py` 인라인 BM25 → `ResultRanker.rank()` 호출)
- `auto_fixer.py`: 존재하지 않는 `regex` 파라미터 참조 수정 → `query` 키 사용
- `search_codebase`: 폴백 호출 4곳에서 누락된 `mode` 파라미터 전달 (회귀 버그 수정)
- `scout.py`: 미사용 `_bm25_score` import 제거

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
