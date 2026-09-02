# External Dependencies & Infrastructure Map — VibeZoo MCP Tool Ecosystem

## 1. External Service Dependencies

| Service | Used By | Purpose | Required? | Failure Mode |
|---------|---------|---------|-----------|--------------|
| **Exa API** (`api.exa.ai`) | [`web.py`](mcp-servers/bridge/tools/web.py:50) | Neural web search | Only for `web_search` | Returns empty results |
| **Crow Memory** (`localhost:9020`) | [`crow_client.py`](mcp-servers/bridge/crow_client.py) | Long-term memory (ingest/recall) | No (graceful degradation) | Tools return results without Crow context |
| **GitHub API** (`api.github.com`) | [`github_diver.py`](mcp-servers/bridge/tools/github_diver.py:1) | Repository search/exploration | Only for `explore_github` | Rate limit errors (60/hr unauthenticated) |

## 2. System Tool Dependencies

| Tool | Required By | Purpose | Available? | Fallback |
|------|-------------|---------|------------|----------|
| **ripgrep** (`rg`) | [`search_engine.py`](mcp-servers/bridge/search_engine.py:34) | Fast code search | ⚠️ Optional (checked at runtime) | `git grep` → `os.walk` fallback |
| **git** | [`search_engine.py`](mcp-servers/bridge/search_engine.py:44), [`analysis.py`](mcp-servers/bridge/tools/analysis.py:42) | Version control, blame, diff | ⚠️ Optional | Features gracefully disabled |
| **Tesseract OCR** | [`ocr_engine.py`](mcp-servers/bridge/ocr_engine.py) | Image text extraction | ⚠️ Optional | OCR section skipped |
| **npx** | [`fix_loop.py`](mcp-servers/bridge/tools/fix_loop.py:194), [`tester.py`](mcp-servers/bridge/tools/tester.py:407) | Build/test execution | ⚠️ Optional | Build features disabled |
| **cargo** | [`integrated.py`](mcp-servers/bridge/tools/integrated.py:129) | Rust linting (clippy) | ⚠️ Optional | Rust analysis skipped |
| **go** | [`integrated.py`](mcp-servers/bridge/tools/integrated.py:187) | Go linting (go vet) | ⚠️ Optional | Go analysis skipped |
| **cppcheck** | [`integrated.py`](mcp-servers/bridge/tools/integrated.py:232) | C++ static analysis | ⚠️ Optional | C++ analysis skipped |
| **ESLint** | [`integrated.py`](mcp-servers/bridge/tools/integrated.py:65) | JS/TS linting | ⚠️ Optional (npx) | Linting skipped |
| **tsc** | [`integrated.py`](mcp-servers/bridge/tools/integrated.py:83), [`fix_loop.py`](mcp-servers/bridge/tools/fix_loop.py:194) | TypeScript compilation check | ⚠️ Optional (npx) | Type checking skipped |
| **winget/choco/scoop** | [`setup.py`](mcp-servers/bridge/tools/setup.py:318) | System tool installation | ⚠️ Optional | Manual installation guidance |
| **PowerShell 5+** | [`whiteboard.py`](mcp-servers/bridge/tools/whiteboard.py:737) | Screen capture fallback | ⚠️ Optional (Windows) | PIL/mss fallback |

## 3. Python Package Dependencies

### Core (Required)
| Package | Purpose | Import Location |
|---------|---------|-----------------|
| `fastmcp` | MCP server framework | `vibezoo_mcp_bridge.py` |
| `uvicorn` | ASGI server | `vibezoo_mcp_bridge.py` |
| `starlette` | HTTP framework | `vibezoo_mcp_bridge.py` |

### Optional — Code Analysis
| Package | Purpose | Used By | Installed? |
|---------|---------|---------|------------|
| `tree-sitter` | AST parsing core | [`ast_engine.py`](mcp-servers/bridge/ast_engine.py) | ⚠️ Check needed |
| `tree-sitter-python` | Python AST | [`ast_engine.py`](mcp-servers/bridge/ast_engine.py) | ⚠️ Check needed |
| `tree-sitter-go` | Go AST | [`ast_engine.py`](mcp-servers/bridge/ast_engine.py) | ⚠️ Check needed |
| `tree-sitter-rust` | Rust AST | [`ast_engine.py`](mcp-servers/bridge/ast_engine.py) | ⚠️ Check needed |

### Optional — Image Processing
| Package | Purpose | Used By | Installed? |
|---------|---------|---------|------------|
| `opencv-contrib-python-headless` | SSA image analysis | [`ssa.py`](mcp-servers/bridge/tools/ssa.py:29) | ⚠️ Check needed |
| `Pillow` | Image I/O, screen capture | [`file_analyzer.py`](mcp-servers/bridge/tools/file_analyzer.py:69), [`whiteboard.py`](mcp-servers/bridge/tools/whiteboard.py:730) | ⚠️ Check needed |
| `numpy` | Array operations (OpenCV) | [`ssa.py`](mcp-servers/bridge/tools/ssa.py:30) | ⚠️ Check needed |

### Optional — OCR
| Package | Purpose | Used By | Installed? |
|---------|---------|---------|------------|
| `pytesseract` | Tesseract Python binding | [`ocr_engine.py`](mcp-servers/bridge/ocr_engine.py) | ⚠️ Check needed |
| `paddlepaddle` | PaddleOCR backend | [`ocr_engine.py`](mcp-servers/bridge/ocr_engine.py) | ⚠️ Check needed |
| `paddleocr` | High-quality OCR engine | [`ocr_engine.py`](mcp-servers/bridge/ocr_engine.py) | ⚠️ Check needed |

### Optional — Vision AI
| Package | Purpose | Used By | Installed? |
|---------|---------|---------|------------|
| `llama-cpp-python` | MiniCPM-V GGUF inference | [`vision/minicpm.py`](mcp-servers/bridge/vision/minicpm.py) | ⚠️ Check needed |
| `huggingface-hub` | Model download | [`setup.py`](mcp-servers/bridge/tools/setup.py:919) | ⚠️ Check needed |

### Optional — Document Processing
| Package | Purpose | Used By | Installed? |
|---------|---------|---------|------------|
| `PyMuPDF` (fitz) | PDF text/image extraction | [`file_analyzer.py`](mcp-servers/bridge/tools/file_analyzer.py:216) | ⚠️ Check needed |
| `python-docx` | DOCX text extraction | [`file_analyzer.py`](mcp-servers/bridge/tools/file_analyzer.py:239) | ⚠️ Check needed |

### Optional — Utilities
| Package | Purpose | Used By | Installed? |
|---------|---------|---------|------------|
| `html2text` | HTML→Markdown conversion | [`utils.py`](mcp-servers/bridge/utils.py) | ⚠️ Check needed |
| `mss` | Cross-platform screen capture | [`whiteboard.py`](mcp-servers/bridge/tools/whiteboard.py:772) | ⚠️ Check needed |
| `requests` | HTTP client (Crow) | [`crow_client.py`](mcp-servers/bridge/crow_client.py) | ⚠️ Check needed |
| `keyring` | Secure API key storage | [`web.py`](mcp-servers/bridge/tools/web.py:27) | ⚠️ Check needed |

## 4. File System Dependencies (Home Directory)

| File/Directory | Purpose | Used By |
|----------------|---------|---------|
| `~/.vibezoo-whiteboard.json` | Whiteboard state | [`whiteboard.py`](mcp-servers/bridge/tools/whiteboard.py) |
| `~/.vibezoo-fix-request.json` | Fix loop session | [`fix_loop.py`](mcp-servers/bridge/tools/fix_loop.py) |
| `~/.vibezoo-chat-pending.json` | Pending chat messages | [`fix_loop.py`](mcp-servers/bridge/tools/fix_loop.py) |
| `~/.vibezoo-preferences.json` | User preferences | [`knowledge.py`](mcp-servers/bridge/tools/knowledge.py) |
| `~/.vibezoo-whiteboard-action.json` | Whiteboard UI actions | [`whiteboard.py`](mcp-servers/bridge/tools/whiteboard.py) |
| `~/.vibezoo-ui-action.json` | General UI actions | [`config.py`](mcp-servers/bridge/config.py) |
| `~/.vibezoo-dropzone-action.json` | Dropzone UI actions | [`whiteboard.py`](mcp-servers/bridge/tools/whiteboard.py) |
| `~/.vibezoo-uploads/` | Uploaded files + cache | [`config.py`](mcp-servers/bridge/config.py) |
| `~/.vibezoo-cache/` | General cache | [`config.py`](mcp-servers/bridge/config.py) |
| `~/.vibezoo-backup/` | File backups (apply_patch) | [`editor.py`](mcp-servers/bridge/tools/editor.py) |
| `~/.vibezoo-uploads/dz_session.json` | Dropzone session state | [`ux_coordinator.py`](mcp-servers/bridge/tools/ux_coordinator.py) |

## 5. Inter-Tool Dependency Graph

```
integrated.py (composite)
├── search_codebase (scout.py)
├── review_code (reviewer.py)
├── check_quality (reviewer.py) [internal only]
├── extract_patterns (deep_analyzer.py)
├── map_dependencies (deep_analyzer.py)
├── analyze_call_graph (deep_analyzer.py)
├── reverse_engineer (deep_analyzer.py)
├── summarize_architecture (scout.py)
└── draw_on_whiteboard (whiteboard.py)

analysis.py
├── review_code (reviewer.py) [for review_pr]
├── search_codebase (scout.py) [for refactor_across_files]
└── ast_engine.py

scout.py
├── search_engine.py → ripgrep/git grep/os.walk
├── result_ranker.py → BM25 scoring
├── ast_engine.py → tree-sitter
├── file_cache.py → L1/L2 caching
└── deep_analyzer.py._run_map_dependencies() [for summarize_architecture]

ux_coordinator.py
├── intent_detector.py
├── ssa.py [for image analysis]
├── file_analyzer.py [for PDF analysis]
├── whiteboard.py.get_whiteboard_state() [for whiteboard analysis]
└── vision/minicpm.py [for MiniCPM analysis]

knowledge.py
├── scout.py.summarize_architecture
├── deep_analyzer.py.extract_patterns
├── deep_analyzer.py.map_dependencies
└── crow_client.py

file_analyzer.py
├── ssa.py._analyze_image() [for images]
├── ocr_engine.py [for OCR]
├── vision/minicpm.py [for vision]
└── fitz (PyMuPDF) [for PDF]
```

## 6. Hardcoded Values & Configuration Risks

| Location | Value | Risk |
|----------|-------|------|
| [`config.py`](mcp-servers/bridge/config.py:13) L13 | `CROW_URL = "http://localhost:9020"` | Low — configurable via env var |
| [`config.py`](mcp-servers/bridge/config.py:14) L14 | `CROW_TIMEOUT = 3` | Low — hardcoded timeout |
| [`web.py`](mcp-servers/bridge/tools/web.py:50) L50 | `url = "https://api.exa.ai/search"` | Low — Exa API only |
| [`setup.py`](mcp-servers/bridge/tools/setup.py:404) L404 | `RG_URL = "https://github.com/...ripgrep-14.1.1..."` | 🟡 Medium — pinned version, will go stale |
| [`setup.py`](mcp-servers/bridge/tools/setup.py:495) L495 | `port=9027` | Low — configurable parameter |
| [`whiteboard.py`](mcp-servers/bridge/tools/whiteboard.py:113) L113 | `User-Agent: Mozilla/5.0 ...` | Low — standard browser UA |
| [`intent_detector.py`](mcp-servers/bridge/intent_detector.py:21) L21 | `CROW_BIAS_WEIGHT = 0.4` | Low — tuning constant |
| [`intent_detector.py`](mcp-servers/bridge/intent_detector.py:24) L24 | `DZ_TIME_THRESHOLD_MINUTES = 3` | Low — tuning constant |
