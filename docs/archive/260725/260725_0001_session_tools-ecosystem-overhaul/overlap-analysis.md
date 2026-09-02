# Cross-Tool Overlap Analysis — VibeZoo MCP Tool Ecosystem

## 1. Critical Overlaps

### Overlap 1: `review_project` vs `review_code` + `check_quality` + `extract_patterns`

**Severity: 🔴 High — Duplication by Design (Composite Pattern)**

[`review_project`](mcp-servers/bridge/tools/integrated.py:400) is a composite tool that internally calls:
- `search_codebase` (for TODO/FIXME/HACK)
- `review_code` (for each file)
- `check_quality` (quality metrics)
- `extract_patterns` (pattern analysis)

An agent can call these 4 tools individually or call `review_project` for the combined result. This is **intentional** (convenience wrapper), but creates confusion because:
- Both paths exist simultaneously
- The composite doesn't add unique logic beyond concatenation
- Performance: `review_project` runs ALL sub-tools even if only one is needed

**Recommendation**: Keep as-is (composite pattern is valid), but add documentation clarifying the relationship.

### Overlap 2: `find_bugs` vs `review_code` + `search_codebase`

**Severity: 🟡 Medium — Partial Overlap**

[`find_bugs`](mcp-servers/bridge/tools/integrated.py:544) searches for suspicious patterns (`console.log`, `debugger`, `as any`, etc.) using `search_codebase`. Meanwhile, `review_code` also detects some of these patterns through AST analysis.

**Overlap zones**:
- `console.log` detection: both tools find this
- `TODO/FIXME`: both search for these
- Code quality issues: `review_code` flags complexity; `find_bugs` flags specific anti-patterns

**Unique to `find_bugs`**: ESLint/tsc integration, Crow Memory recall, native linter execution (cargo clippy, go vet, cppcheck)
**Unique to `review_code`**: AST-based complexity analysis, cyclomatic complexity, per-file scoring

**Recommendation**: `review_code` could call `find_bugs` internally for its specific pattern detection, eliminating duplicate search code.

### Overlap 3: `suggest_refactor` vs `map_dependencies` + `extract_patterns` + `analyze_call_graph`

**Severity: 🟡 Medium — Composition Without Added Value**

[`suggest_refactor`](mcp-servers/bridge/tools/integrated.py:757) chains:
1. `map_dependencies` — finds circular deps
2. `extract_patterns` — finds duplicated patterns
3. `analyze_call_graph` — finds function relationships

In **summary mode**, it generates a grade and 3-5 suggestions. In **full mode**, it just concatenates the outputs of the three tools with minimal added synthesis.

**Unique to `suggest_refactor`**: The grade (A/B/C) assignment logic and summary formatting. This is a thin wrapper.

### Overlap 4: `generate_docs` vs `summarize_architecture` + `reverse_engineer`

**Severity: 🟡 Medium — Thin Wrapper**

[`generate_docs`](mcp-servers/bridge/tools/integrated.py:886) calls `summarize_architecture` and `reverse_engineer`, then draws a directory tree on the whiteboard. In summary mode, it only shows tech stack and file count.

---

## 2. Search Tool Overlaps

### `search_codebase` vs `find_references`

**Severity: 🟢 Low — Complementary**

| Feature | `search_codebase` | `find_references` |
|---------|-------------------|-------------------|
| Text search | ✅ Primary | ❌ |
| AST symbol search | ✅ Secondary | ✅ Primary |
| Definition vs usage separation | ❌ | ✅ |
| Reference type classification | ❌ | ✅ (call/read/write/type_ref/import_ref) |
| Call chain analysis | ❌ | ✅ |
| File pattern filtering | ✅ | ❌ |

**No direct overlap** — these are complementary tools. `search_codebase` is for broad discovery; `find_references` is for targeted symbol tracing.

### `search_codebase` vs `refactor_across_files`

**Severity: 🟢 Low — Sequential Dependency**

[`refactor_across_files`](mcp-servers/bridge/tools/analysis.py:704) internally calls `search_codebase` (L733) to find occurrences, then generates diff proposals. This is a proper composition, not overlap.

---

## 3. File Analysis Overlaps

### `analyze_uploaded_file` vs `auto_analyze_after_drop`

**Severity: 🟠 High — Significant Functional Overlap**

| Feature | `analyze_uploaded_file` | `auto_analyze_after_drop` |
|---------|------------------------|---------------------------|
| Image analysis pipeline | SSA → OCR → MiniCPM | SSA → OCR → MiniCPM |
| Code file preview | ✅ | ✅ |
| Document extraction | PDF (PyMuPDF), DOCX | Text, PDF (delegates to `analyze_file`) |
| Dropzone session tracking | ❌ | ✅ (writes dz_session.json) |
| Tool chain suggestion | ❌ | ✅ (suggests next tools) |

**Critical finding**: [`auto_analyze_after_drop`](mcp-servers/bridge/tools/ux_coordinator.py:136) delegates PDF analysis to `analyze_file()` (L254), meaning it's a superset of `analyze_uploaded_file` plus session tracking and workflow suggestions.

**`analyze_uploaded_file`** ([`file_analyzer.py`](mcp-servers/bridge/tools/file_analyzer.py:345)) is the actual implementation; `auto_analyze_after_drop` is a workflow wrapper.

**Recommendation**: Consider merging into a single tool with an optional `session_tracking` parameter, or make `auto_analyze_after_drop` the primary tool and remove `analyze_uploaded_file` from MCP registration.

### `capture_screen` vs `auto_analyze_after_drop`

**Severity: 🟢 Low — Sequential**

`capture_screen(source="dropzone")` opens the dropzone UI. `auto_analyze_after_drop` is called after the file is uploaded. Proper sequential workflow.

---

## 4. Whiteboard Overlaps

### `get_whiteboard_state` vs `auto_analyze_whiteboard`

**Severity: 🟡 Medium**

[`get_whiteboard_state`](mcp-servers/bridge/tools/whiteboard.py:988) reads whiteboard data and converts it to text via `WhiteboardDataConverter`.
[`auto_analyze_whiteboard`](mcp-servers/bridge/tools/ux_coordinator.py:286) calls `get_whiteboard_state()` internally (L299) and then adds analysis suggestions.

**`auto_analyze_whiteboard` adds**: Mermaid diagram suggestion, design feedback suggestions, code generation suggestions. But the actual conversion is done by `get_whiteboard_state`.

**Recommendation**: Merge analysis suggestions into `get_whiteboard_state` with an optional `analyze=True` parameter.

---

## 5. Knowledge/Memory Overlaps

### `learn_project` vs `auto_learn_project`

**Severity: 🟡 Medium — Implicit Duplicate**

[`learn_project`](mcp-servers/bridge/tools/knowledge.py:123) is the explicit MCP tool.
[`auto_learn_project`](mcp-servers/bridge/tools/knowledge.py:31) is an internal function that runs automatically on server start (L114-120, daemon thread with 3-second delay).

Both do the same thing (summarize_architecture → extract_patterns → map_dependencies → Crow ingest), but `auto_learn_project` has a guard (`_learned_projects` set) to prevent re-running.

**Risk**: If `learn_project()` is called manually after `auto_learn_project()` already ran, the Crow registers will be double-populated with duplicate data.

---

## 6. Merger Candidates

### Priority 1: Merge `analyze_uploaded_file` into `auto_analyze_after_drop`
- `auto_analyze_after_drop` is a strict superset
- Add `session_tracking` flag to control dz_session.json writing
- Remove `analyze_uploaded_file` from MCP registration (keep internal)

### Priority 2: Merge `auto_analyze_whiteboard` into `get_whiteboard_state`
- Add optional `analyze` parameter to `get_whiteboard_state`
- Remove `auto_analyze_whiteboard` from MCP registration

### Priority 3: Consolidate `_get_ast_engine()` singleton
- Create a shared `ast_singleton.py` module
- All 5 files import from the shared singleton

### Priority 4: Clean up `integrated.py` tool_registry
- Remove 12 dead entries from `_tool_registry`
- Remove `_lazy_tool()` function
- Simplify to only the 8 tools that have working lazy getters

---

## 7. Tools Unique Enough to Keep Separate

| Tool | Why Separate |
|------|-------------|
| `search_codebase` | Core search — widely used by all composite tools |
| `find_references` | Symbol tracing — distinct from text search |
| `review_code` | Per-file AST analysis — unique value |
| `explain_code` | Line-level explanation with git blame — unique |
| `apply_patch` | File editing — different category entirely |
| `generate_tests` | Test generation — unique capability |
| `analyze_coverage` | Coverage analysis — unique capability |
| `vibezoo_setup` | Installation — unique category |
| `web_search` | External search — unique category |
| `explore_github` | External API — unique category |
| `vibezoo_feedback` | Feedback collection — unique category |
| All `fix_loop` tools | Build-fix workflow — unique category |
| All `knowledge` tools | Memory persistence — unique category |
