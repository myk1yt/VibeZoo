# VibeZoo MCP Tool Ecosystem — Complete Inventory

## Registration System

All tools are registered via [`mcp-servers/bridge/tools/__init__.py`](mcp-servers/bridge/tools/__init__.py:19). The [`register_all_tools(mcp)`](mcp-servers/bridge/tools/__init__.py:19) function:
1. Wraps `mcp.tool()` with [`capture_tool_errors()`](mcp-servers/bridge/tools/__init__.py:41) for automatic error handling
2. Calls `register(mcp)` on each of the 16 tool modules in sequence
3. Restores the original `mcp.tool` after registration

**16 registered tool modules** (in registration order):
1. [`setup.py`](mcp-servers/bridge/tools/setup.py) → `reg_setup`
2. [`scout.py`](mcp-servers/bridge/tools/scout.py) → `reg_scout`
3. [`reviewer.py`](mcp-servers/bridge/tools/reviewer.py) → `reg_reviewer`
4. [`deep_analyzer.py`](mcp-servers/bridge/tools/deep_analyzer.py) → `reg_deep`
5. [`tester.py`](mcp-servers/bridge/tools/tester.py) → `reg_tester`
6. [`file_analyzer.py`](mcp-servers/bridge/tools/file_analyzer.py) → `register_file_analyzer`
7. [`whiteboard.py`](mcp-servers/bridge/tools/whiteboard.py) → `reg_wb`
8. [`fix_loop.py`](mcp-servers/bridge/tools/fix_loop.py) → `reg_fix`
9. [`integrated.py`](mcp-servers/bridge/tools/integrated.py) → `reg_integrated`
10. [`analysis.py`](mcp-servers/bridge/tools/analysis.py) → `reg_analysis`
11. [`knowledge.py`](mcp-servers/bridge/tools/knowledge.py) → `reg_knowledge`
12. [`web.py`](mcp-servers/bridge/tools/web.py) → `reg_web`
13. [`ssa.py`](mcp-servers/bridge/tools/ssa.py) → `reg_ssa`
14. [`editor.py`](mcp-servers/bridge/tools/editor.py) → `reg_editor`
15. [`ux_coordinator.py`](mcp-servers/bridge/tools/ux_coordinator.py) → `reg_ux`
16. [`feedback.py`](mcp-servers/bridge/tools/feedback.py) → `reg_feedback`

---

## Complete MCP Tool Inventory (45 tools)

### 🔧 Setup & Configuration
| # | Tool Name | File | Line | Purpose | Status |
|---|-----------|------|------|---------|--------|
| 1 | `vibezoo_setup` | [`setup.py`](mcp-servers/bridge/tools/setup.py:1165) | L1165 | Unified installer (pip, system tools, MCP config, Zoo config, custom modes, model download) | ✅ Working |

### 🔍 Search & Discovery
| # | Tool Name | File | Line | Purpose | Status |
|---|-----------|------|------|---------|--------|
| 2 | `search_codebase` | [`scout.py`](mcp-servers/bridge/tools/scout.py:702) | L702 | Codebase search (ripgrep → git grep → os.walk fallback + AST) | ✅ Working |
| 3 | `find_references` | [`scout.py`](mcp-servers/bridge/tools/scout.py:720) | L720 | Find all references to a symbol (definitions + usages + call chain) | ✅ Working |
| 4 | `summarize_architecture` | [`scout.py`](mcp-servers/bridge/tools/scout.py:731) | L731 | Project architecture analysis (summary + full modes, streaming) | ✅ Working |

### 📝 Code Review & Analysis
| # | Tool Name | File | Line | Purpose | Status |
|---|-----------|------|------|---------|--------|
| 5 | `review_code` | [`reviewer.py`](mcp-servers/bridge/tools/reviewer.py:345) | L345 | Single-file code review (AST-based complexity, cyclomatic analysis) | ✅ Working |
| 6 | `explain_code` | [`analysis.py`](mcp-servers/bridge/tools/analysis.py:195) | L195 | Explain code at specific line (AST context, git blame, related tests) | ✅ Working |
| 7 | `analyze_changes` | [`analysis.py`](mcp-servers/bridge/tools/analysis.py:432) | L432 | Git diff analysis (change classification + Crow context) | ✅ Working |
| 8 | `review_pr` | [`analysis.py`](mcp-servers/bridge/tools/analysis.py:533) | L533 | Full PR review (diff + code review + dependency analysis + rollback risk) | ✅ Working |

### 🔬 Deep Analysis
| # | Tool Name | File | Line | Purpose | Status |
|---|-----------|------|------|---------|--------|
| 9 | `analyze_call_graph` | [`deep_analyzer.py`](mcp-servers/bridge/tools/deep_analyzer.py:528) | L528 | Function call graph (fan-in/fan-out, dead code detection) | ✅ Working |
| 10 | `map_dependencies` | [`deep_analyzer.py`](mcp-servers/bridge/tools/deep_analyzer.py:670) | L670 | Dependency map (circular dependency detection, impact analysis) | ✅ Working |
| 11 | `extract_patterns` | [`deep_analyzer.py`](mcp-servers/bridge/tools/deep_analyzer.py:680) | L680 | AST-based pattern extraction (anti-pattern detection) | ✅ Working |
| 12 | `reverse_engineer` | [`deep_analyzer.py`](mcp-servers/bridge/tools/deep_analyzer.py:696) | L696 | Auto-generate API docs, data models, ER diagrams | ✅ Working |

### 🧪 Testing
| # | Tool Name | File | Line | Purpose | Status |
|---|-----------|------|------|---------|--------|
| 13 | `generate_tests` | [`tester.py`](mcp-servers/bridge/tools/tester.py:45) | L45 | Generate unit test scaffolding (AST-based function detection) | ✅ Working |
| 14 | `analyze_coverage` | [`tester.py`](mcp-servers/bridge/tools/tester.py:317) | L317 | Test coverage analysis (file-based + external tool execution) | ✅ Working |

### 🏗️ Integrated / Composite
| # | Tool Name | File | Line | Purpose | Status |
|---|-----------|------|------|---------|--------|
| 15 | `review_project` | [`integrated.py`](mcp-servers/bridge/tools/integrated.py:400) | L400 | Full project review (search + review + quality + patterns) | ✅ Working |
| 16 | `find_bugs` | [`integrated.py`](mcp-servers/bridge/tools/integrated.py:544) | L544 | Bug finder (patterns + suspicious code + ESLint/tsc + Crow) | ✅ Working |
| 17 | `suggest_refactor` | [`integrated.py`](mcp-servers/bridge/tools/integrated.py:757) | L757 | Refactoring suggestions (deps + patterns + call graph) | ✅ Working |
| 18 | `generate_docs` | [`integrated.py`](mcp-servers/bridge/tools/integrated.py:886) | L886 | Auto-generate docs (architecture + reverse engineering + whiteboard) | ✅ Working |

### ✏️ File Editing
| # | Tool Name | File | Line | Purpose | Status |
|---|-----------|------|------|---------|--------|
| 19 | `apply_patch` | [`editor.py`](mcp-servers/bridge/tools/editor.py:607) | L607 | AI-safe file patching (SEARCH/REPLACE with ellipsis resolution, transactional rollback) | ✅ Working |
| 20 | `refactor_across_files` | [`analysis.py`](mcp-servers/bridge/tools/analysis.py:704) | L704 | Multi-file refactoring (search + AST-aware rename + backup) | ✅ Working |

### 🌐 Web
| # | Tool Name | File | Line | Purpose | Status |
|---|-----------|------|------|---------|--------|
| 21 | `fetch_page` | [`web.py`](mcp-servers/bridge/tools/web.py:90) | L90 | Fetch web page and convert to markdown (pure stdlib) | ✅ Working |
| 22 | `web_search` | [`web.py`](mcp-servers/bridge/tools/web.py:156) | L156 | Neural web search via Exa API | ⚠️ Requires EXA_API_KEY |

### 🔗 GitHub
| # | Tool Name | File | Line | Purpose | Status |
|---|-----------|------|------|---------|--------|
| 23 | `explore_github` | [`github_diver.py`](mcp-servers/bridge/tools/github_diver.py:142) | L142 | Unified GitHub tool (search repos, explore structure, read files) | ✅ Working (rate-limited w/o token) |

### 📊 Analysis
| # | Tool Name | File | Line | Purpose | Status |
|---|-----------|------|------|---------|--------|
| 24 | `analyze_uploaded_file` | [`file_analyzer.py`](mcp-servers/bridge/tools/file_analyzer.py:345) | L345 | Universal file analyzer (image→SSA→OCR→MiniCPM, code→preview, doc→extract) | ✅ Working |

### 🖼️ Whiteboard & Vision
| # | Tool Name | File | Line | Purpose | Status |
|---|-----------|------|------|---------|--------|
| 25 | `draw_on_whiteboard` | [`whiteboard.py`](mcp-servers/bridge/tools/whiteboard.py:951) | L951 | Draw shapes on Fabric.js whiteboard | ✅ Working |
| 26 | `get_whiteboard_state` | [`whiteboard.py`](mcp-servers/bridge/tools/whiteboard.py:988) | L988 | Read whiteboard state (Fabric.js JSON → LLM text via WhiteboardDataConverter) | ✅ Working |
| 27 | `capture_screen` | [`whiteboard.py`](mcp-servers/bridge/tools/whiteboard.py:927) | L927 | Screen capture / dropzone / file picker (3-mode) | ✅ Working |
| 28 | `check_uploaded_files` | [`whiteboard.py`](mcp-servers/bridge/tools/whiteboard.py:868) | L868 | List recently uploaded files from dropzone | ✅ Working |

### 🔬 SSA (Image Analysis)
| # | Tool Name | File | Line | Purpose | Status |
|---|-----------|------|------|---------|--------|
| 29 | `aggregate_spatial_pixels` | [`ssa.py`](mcp-servers/bridge/tools/ssa.py) | — | Statistical Spatial Aggregator (image → spatial matrix + OCR) | ⚠️ Requires OpenCV |

### 🔄 Fix Loop
| # | Tool Name | File | Line | Purpose | Status |
|---|-----------|------|------|---------|--------|
| 30 | `auto_fix_status` | [`fix_loop.py`](mcp-servers/bridge/tools/fix_loop.py:133) | L133 | Query active auto-fix session state + Crow recall | ✅ Working |
| 31 | `retry_build` | [`fix_loop.py`](mcp-servers/bridge/tools/fix_loop.py:177) | L177 | Re-run build + extract errors/warnings | ✅ Working |
| 32 | `check_intervention` | [`fix_loop.py`](mcp-servers/bridge/tools/fix_loop.py:300) | L300 | Check for user intervention (whiteboard annotations, chat messages) | ✅ Working |

### 🧠 Knowledge & Memory
| # | Tool Name | File | Line | Purpose | Status |
|---|-----------|------|------|---------|--------|
| 33 | `learn_project` | [`knowledge.py`](mcp-servers/bridge/tools/knowledge.py:123) | L123 | Ingest project knowledge into Crow (arch + style + identity) | ✅ Working |
| 34 | `recall_project` | [`knowledge.py`](mcp-servers/bridge/tools/knowledge.py:215) | L215 | Recall project knowledge from Crow | ✅ Working |
| 35 | `learn_preference` | [`knowledge.py`](mcp-servers/bridge/tools/knowledge.py:270) | L270 | Save user preference to Crow + local file | ✅ Working |
| 36 | `get_preferences` | [`knowledge.py`](mcp-servers/bridge/tools/knowledge.py:332) | L332 | Retrieve saved user preferences | ✅ Working |

### 🧭 UX Coordination
| # | Tool Name | File | Line | Purpose | Status |
|---|-----------|------|------|---------|--------|
| 37 | `ux_coordinator` | [`ux_coordinator.py`](mcp-servers/bridge/tools/ux_coordinator.py:60) | L60 | Intent detection + workflow chain suggestion | ✅ Working |
| 38 | `auto_analyze_after_drop` | [`ux_coordinator.py`](mcp-servers/bridge/tools/ux_coordinator.py:136) | L136 | Post-dropzone auto-analysis pipeline | ✅ Working |
| 39 | `auto_analyze_whiteboard` | [`ux_coordinator.py`](mcp-servers/bridge/tools/ux_coordinator.py:286) | L286 | Auto-analyze whiteboard contents | ✅ Working |

### 💬 Feedback
| # | Tool Name | File | Line | Purpose | Status |
|---|-----------|------|------|---------|--------|
| 40 | `vibezoo_feedback` | [`feedback.py`](mcp-servers/bridge/tools/feedback.py:8) | L8 | Agent autonomous feedback submission | ✅ Working |

---

## Supporting Infrastructure

| Module | File | Purpose |
|--------|------|---------|
| `SearchEngine` | [`search_engine.py`](mcp-servers/bridge/search_engine.py:21) | 3-tier search: ripgrep → git grep → os.walk fallback |
| `ResultRanker` | [`result_ranker.py`](mcp-servers/bridge/result_ranker.py:8) | BM25 + exact match + location + context density scoring |
| `AstEngine` | [`ast_engine.py`](mcp-servers/bridge/ast_engine.py) | tree-sitter AST parsing (TS/JS/Python/Go/Rust) |
| `BaseTool` | [`_base.py`](mcp-servers/bridge/tools/_base.py:4) | Validation, error reporting, progress chunks, streaming |
| `FileCache` | [`file_cache.py`](mcp-servers/bridge/file_cache.py) | L1 memory + L2 file system caching |
| `ErrorRegistry` | [`error_handler.py`](mcp-servers/bridge/error_handler.py) | Tool error capture and structured reporting |
| `OcrEngine` | [`ocr_engine.py`](mcp-servers/bridge/ocr_engine.py) | Tesseract/PaddleOCR text extraction |
| `WhiteboardDataConverter` | [`whiteboard.py`](mcp-servers/bridge/tools/whiteboard.py:88) | Fabric.js JSON → LLM-readable text + Mermaid |
| `IntentDetector` | [`intent_detector.py`](mcp-servers/bridge/intent_detector.py:1) | Crow-aware intent routing (keyword + Crow bias + DZ binding) |
| `CrowClient` | [`crow_client.py`](mcp-servers/bridge/crow_client.py) | Crow Memory HTTP client (ingest/recall) |
| `ToolContext` | [`tool_context.py`](mcp-servers/bridge/tool_context.py) | LLM task context generation |
| `LLMPipeline` | [`llm_pipeline.py`](mcp-servers/bridge/llm_pipeline.py) | LLM inference pipeline (MiniCPM-V) |

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| Tool modules | 16 |
| MCP tools registered | 40 |
| Supporting modules | 12 |
| Total Python files | 28+ |
| Estimated total lines | ~8,000+ |
