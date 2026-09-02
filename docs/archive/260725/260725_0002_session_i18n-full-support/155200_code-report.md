# Code Task Report: i18n t() Wrapping — Batch A (9 files)

## Task Summary
Wrapped all user-facing English strings with `t()` calls from `bridge.i18n` in 9 Bridge tool files. Added `from bridge.i18n import t` import to each file and replaced hardcoded user-facing strings with translatable `t()` calls using the English string as the lookup key.

## Actions Taken

### 1. `extension/mcp-servers/bridge/tools/analysis.py`
- Added `from bridge.i18n import t` import
- Wrapped 9 user-facing strings:
  - `File not found: \`{0}\`` (explain_code error)
  - `Cannot read file: \`{0}\`` (explain_code error)
  - `Line {0} is out of range (file has {1} lines)` (explain_code error)
  - `Line {0} is empty.` (explain_code info)
  - `No uncommitted changes detected.` (analyze_changes)
  - `No Crow context found.` / `Could not query Crow.` (analyze_changes Crow recall)
  - `Git not available...` / `Git diff timed out.` (analyze_changes exceptions, 2 occurrences)
  - `No differences found between branches.` (review_pr)
  - `No occurrences found for this pattern.` (refactor_across_files)

### 2. `extension/mcp-servers/bridge/tools/deep_analyzer.py`
- Added `from bridge.i18n import t` import
- Wrapped 11 user-facing strings:
  - `No package manager detected.`
  - `No circular dependencies detected.`
  - `No dependency data for impact analysis.`
  - `No structural patterns met the minimum occurrence threshold.`
  - `No function definitions found.`
  - `No call data available.`
  - `No dead code detected (or all functions have callers).`
  - `No supported source files found (TS/JS/Python/Go/Rust).`
  - `No function calls detected via AST.`
  - `Invalid format: \`{0}\`. Allowed: {1}` (reverse_engineer validation)
  - `No API endpoints detected.`, `No explicit model relationships detected.`, `No data models detected.`

### 3. `extension/mcp-servers/bridge/tools/editor.py`
- Added `from bridge.i18n import t` import
- Wrapped 6 user-facing strings (Korean → English t() keys):
  - `No SEARCH/REPLACE blocks found in \`diff\`.` (was Korean)
  - `Path is outside project root: \`{0}\`` (was Korean)
  - `File not found:` (was Korean)
  - `` `path` not specified and no matching file found... `` (was Korean)
  - `File read failed: \`{0}\`` (was Korean)
  - `File write failed: \`{0}\`` (was Korean)
- Note: The `<<<<<<< SEARCH` literal marker block required a Python script to apply due to diff tool marker conflicts.

### 4. `extension/mcp-servers/bridge/tools/feedback.py`
- Added `from bridge.i18n import t` import
- Wrapped 4 user-facing strings:
  - `Invalid category. Must be one of: {0}`
  - `Snippet Attached: Yes`
  - `Thank you for the autonomous suggestion. The user will review it.`
  - `Failed to save feedback: {0}`

### 5. `extension/mcp-servers/bridge/tools/file_analyzer.py`
- Added `from bridge.i18n import t` import
- Wrapped 13 user-facing strings (several Korean → English t() keys):
  - `File not found:` (was Korean)
  - `Cannot read image for spatial analysis`
  - `OpenCV not available (install opencv-python)`
  - `Analysis failed: {0}` (SSA + OCR sections)
  - `Not available (install Tesseract or PaddleOCR)`
  - `Module not loaded`
  - `PyMuPDF not installed. Run: \`pip install PyMuPDF\``
  - `PDF read error: {0}`
  - `python-docx not installed. Run: \`pip install python-docx\``
  - `DOCX read error: {0}`
  - `PDF has no pages.`
  - `Text extraction failed — {0} page(s) being analyzed as image.`
  - `OCR skipped: {0}`
  - `PyMuPDF not installed (required for scanned PDF analysis)`
  - `PDF image analysis failed: {0}`
  - `No uploaded files yet.` (was Korean)
  - `No files uploaded in the current session...` (was Korean)
  - `Upload registry read failed: {0}` (was Korean)

### 6. `extension/mcp-servers/bridge/tools/fix_loop.py`
- Added `from bridge.i18n import t` import
- Wrapped 5 user-facing strings:
  - `No active fix request`
  - `No build command detected (package.json not found)`
  - `Build timed out after 60s`
  - `Whiteboard annotations found`
  - `Pending chat messages found`

### 7. `extension/mcp-servers/bridge/tools/github_diver.py`
- Added `from bridge.i18n import t` import
- Wrapped 7 user-facing strings:
  - `GitHub API Rate limit exceeded...` (with {0} detail arg)
  - `Not found. The repository or file might not exist.`
  - `HTTP Error {0}: {1}`
  - `Request failed: {0}`
  - `No repositories found for query: '{0}'`
  - `Empty repository or cannot read tree.`
  - `Failed to read {0}. It might not exist in HEAD, main, or master branch.`
  - `Failed to read file: {0}`
  - `Error: You must provide either 'query', 'repo', or both 'repo' and 'file_path'.`

### 8. `extension/mcp-servers/bridge/tools/integrated.py`
- Added `from bridge.i18n import t` import
- Wrapped 13 user-facing strings:
  - `Tool not found: \`{0}\``
  - `cargo not found in PATH. Install Rust: https://rustup.rs`
  - `cargo clippy timed out (120s)`
  - `go not found in PATH. Install Go: https://go.dev/dl`
  - `go vet timed out (60s)`
  - `Failed to parse cppcheck XML output`
  - `cppcheck not found in PATH...`
  - `cppcheck timed out (120s)`
  - `No source files found to review.`
  - `No suspicious patterns found.` (2 occurrences: summary + full mode)
  - `No supported linter environment detected.`
  - `No relevant bug patterns found.`
  - `No relevant bug patterns found in Crow memory.`
  - `Invalid format: \`{0}\`. Allowed: {1}` (generate_docs validation)
  - `No directory structure to visualize.`

### 9. `extension/mcp-servers/bridge/tools/knowledge.py`
- Added `from bridge.i18n import t` import
- Wrapped 12 user-facing strings:
  - `Architecture stored in Crow \`arch\` register`
  - `Patterns stored in Crow \`style\` register`
  - `Dependencies stored in Crow \`arch\` register`
  - `Project identity stored in Crow \`life_context\` (key: \`{0}\`)`
  - `Project knowledge ingestion complete.`
  - `No architecture data found in Crow.`
  - `Run \`learn_project()\` first to store project knowledge.`
  - `No pattern data found in Crow.`
  - `No project identity found in Crow.`
  - `Invalid category: \`{0}\`. Allowed: {1}`
  - `Failed to save: \`{0}\``
  - `Stored in local preferences file and Crow Memory (\`life_context\`).`
  - `No preferences saved yet.`
  - `Use \`learn_preference(rule, category)\` to save your first preference.`
  - `Category not found.`
  - `No preference data in Crow.`

## Result
✅ Success — All 9 files modified, `from bridge.i18n import t` added to each, and all user-facing strings wrapped with `t()` calls. Python syntax verification (`py_compile`) passes for all 9 files with exit code 0.

### Verification
- Ran `python -m py_compile` on all 9 files simultaneously
- Exit code: 0 (all files compile successfully)
- One fix applied during verification: `github_diver.py` line 158 had escaped quote issue in f-string, resolved by extracting `t()` call to a variable

## Issues Discovered
- `editor.py` line 503 contained literal `<<<<<<< SEARCH` markers as part of a user-facing error message string, which conflicted with the `apply_diff` tool's syntax. Resolved by using a temporary Python script to perform the replacement.
- `github_diver.py` line 158: f-string with escaped double quotes (`\"`) inside a double-quoted f-string caused `SyntaxError`. Resolved by extracting the `t()` call to a separate variable before the f-string.
- Several files (`editor.py`, `file_analyzer.py`) had Korean user-facing strings that were replaced with English `t()` keys matching `en.json`, enabling proper i18n.

## Next Step Recommendations
- **Batch B**: Continue wrapping remaining tool files not in this batch (e.g., `reviewer.py`, `scout.py`, `setup.py`, `ssa.py`, `tester.py`, `ux_coordinator.py`, `web.py`, `whiteboard.py`)
- **Translation files**: Generate `ko.json`, `ja.json`, etc. translation files for the 168 keys in `en.json`
- **Runtime test**: Start the Bridge MCP server with `VIBEZOO_LANG=ko` and call each tool to verify Japanese/Korean translations appear correctly in responses

## Affected File List
1. `extension/mcp-servers/bridge/tools/analysis.py`
2. `extension/mcp-servers/bridge/tools/deep_analyzer.py`
3. `extension/mcp-servers/bridge/tools/editor.py`
4. `extension/mcp-servers/bridge/tools/feedback.py`
5. `extension/mcp-servers/bridge/tools/file_analyzer.py`
6. `extension/mcp-servers/bridge/tools/fix_loop.py`
7. `extension/mcp-servers/bridge/tools/github_diver.py`
8. `extension/mcp-servers/bridge/tools/integrated.py`
9. `extension/mcp-servers/bridge/tools/knowledge.py`
