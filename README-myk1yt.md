# VibeZoo — Intelligent Companion Extension for AI Coding Assistants

[![Guard.git - .git Protection](https://img.shields.io/badge/Guard.git-.git%20Protected-blueviolet)](https://github.com/vibezoo/VibeZoo_forZoocode)

> **VibeZoo = [Crow Memory](#3-crow-memory-overview) (Synaptic Memory) + [VibeZoo MCP Bridge](#1-vibezoo-mcp-bridge--tool-overview-33-tools) (33 Tools)**

VibeZoo is a Companion Extension for Zoo Code and MCP-enabled AI coding assistants. Without modifying a single line of Zoo Code's source code, it empowers LLMs to search, analyze, review, and refactor code with deep AST precision, automatically protect `.git` safety, remember developer preferences, and collaborate visually in real time (Whiteboard, Dropzone, Vision AI).

---

## Support VibeZoo Development ☕

If you find VibeZoo and Crow Memory helpful for your productivity, consider supporting our development!  
**[💖 Sponsor VibeZoo on Gumroad](https://teamsunplaza.gumroad.com/l/vibezoo)**

Your support helps us develop new features and keep the AI coding revolution moving forward.

---

## 🌍 Global i18n / l10n Full Support (20 Languages)

VibeZoo provides **100% native localization across 20 languages** without relying on unlocalized fallbacks. Built on the native `vscode.l10n` API, package manifest NLS, and Python bridge internationalization, VibeZoo automatically adapts to your VS Code display language:

- **Supported Locales**: English (`en`), Arabic (`ar`), Bulgarian (`bg`), Czech (`cs`), German (`de`), Spanish (`es`), French (`fr`), Hebrew (`he`), Hungarian (`hu`), Italian (`it`), Japanese (`ja`), Korean (`ko`), Polish (`pl`), Portuguese-Brazil (`pt-BR`), Russian (`ru`), Thai (`th`), Turkish (`tr`), Vietnamese (`vi`), Simplified Chinese (`zh-CN`), Traditional Chinese (`zh-TW`).

---

## 🚀 One-Shot Quick Setup & Installation

Get started with full MCP and extension setup in 3 simple steps (see [`docs/INSTALLATION.md`](docs/INSTALLATION.md) for full details):

1. **Clone Repository**:
   ```bash
   git clone https://github.com/vibezoo/VibeZoo_forZoocode.git
   cd VibeZoo_forZoocode
   ```
2. **Run One-Shot Bootstrapper**:
   - **Windows**: Double-click [`init_vibezoo.bat`](init_vibezoo.bat) (or execute in cmd).
   - **macOS / Linux**: Run `chmod +x init_vibezoo.sh && ./init_vibezoo.sh`.
3. **Open VS Code & Verify**:
   - Launch VS Code and run **`VibeZoo: Self Check`** from the Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`).

### What One-Shot Setup Does Automatically
- 📦 Creates Python `venv` at `%USERPROFILE%\mcp-servers\vibezoo` and installs required packages (`fastmcp`, `starlette`, `requests`, `tree_sitter_languages`).
- 🛠️ Compiles and packages the VSIX extension, then automatically installs it into VS Code (`code --install-extension`).
- 🌐 Automatically configures global `mcp_settings.json` with `vibezoo` (port 9027) and `crow-memory` (port 9021).
- 🚀 Starts the VibeZoo FastMCP Bridge (port 9027) and Crow Memory server (port 9021) in the background.

---

## 1. VibeZoo MCP Bridge — Tool Overview (33 Tools)

The VibeZoo MCP Bridge operates via FastMCP + Streamable HTTP at `http://localhost:9027/mcp`. It delivers **33 specialized MCP tools** categorized into 12 core domains.

Key infrastructure modules:
- [`ast_singleton.py`](extension/mcp-servers/bridge/ast_singleton.py) — High-performance tree-sitter AST engine singleton
- [`fuzzy_matcher.py`](extension/mcp-servers/bridge/fuzzy_matcher.py) — Trigram Dice coefficient fuzzy approximate matching
- [`embedding_client.py`](extension/mcp-servers/bridge/embedding_client.py) — Embedding client (LM Studio / Ollama auto-detection on port `8089` with BM25 fallback)
- [`result_ranker.py`](extension/mcp-servers/bridge/result_ranker.py) — Hybrid BM25 + cosine similarity ranker
- [`file_cache.py`](extension/mcp-servers/bridge/file_cache.py) — L1 memory cache with 20s TTL

> **Note**: `extension/mcp-servers/` is the SOURCE OF TRUTH for the Python bridge; root `mcp-servers/` is a manually-synced dev mirror. `init_vibezoo.bat` deploys the source of truth to `%USERPROFILE%\mcp-servers\vibezoo`.

---

### 1.1 Scout & Code Search (3 Tools)
Tools: [`search_codebase`](extension/mcp-servers/bridge/tools/scout.py), [`find_references`](extension/mcp-servers/bridge/tools/scout.py), [`summarize_architecture`](extension/mcp-servers/bridge/tools/scout.py)

- **`search_codebase`**: Multi-mode codebase search supporting `auto`, `exact`, `fuzzy`, `ast`, and `semantic` modes.
  - `semantic`: Embedding-based cosine similarity. Automatically falls back to BM25 when the embedding server (port `8089`) is offline.
  - `target_path`: Supports searching targeted subdirectories or external project paths.
- **`find_references`**: Word-boundary regex matching (`\b`) preventing substring false positives.
- **`summarize_architecture`**: AST-driven overview of modules, classes, and entry points.

### 1.2 Deep AST Analyzer (4 Tools)
Tools: [`analyze_call_graph`](extension/mcp-servers/bridge/tools/deep_analyzer.py), [`map_dependencies`](extension/mcp-servers/bridge/tools/deep_analyzer.py), [`extract_patterns`](extension/mcp-servers/bridge/tools/deep_analyzer.py), [`reverse_engineer`](extension/mcp-servers/bridge/tools/deep_analyzer.py)

- Traces call hierarchies, structural dependencies, and recurring implementation patterns across TypeScript, JavaScript, Python, Rust, Go, and C/C++.

### 1.3 Reviewer (1 Tool)
Tool: [`review_code`](extension/mcp-servers/bridge/tools/reviewer.py)

- Automates static analysis and code quality verification before commits or PR submission.

### 1.4 Whiteboard & Dropzone (4 Tools)
Tools: [`draw_on_whiteboard`](extension/mcp-servers/bridge/tools/whiteboard.py), [`get_whiteboard_state`](extension/mcp-servers/bridge/tools/whiteboard.py), [`capture_screen`](extension/mcp-servers/bridge/tools/whiteboard.py), [`check_uploaded_files`](extension/mcp-servers/bridge/tools/whiteboard.py)
<!-- 4 tools: 3 whiteboard + 1 upload monitor; upload analysis via analyze_uploaded_file (1.5) -->

- Real-time visual collaboration on a Fabric.js canvas. AI can draw diagrams, inspect user modifications, capture viewport snapshots, and monitor image uploads.

### 1.5 File Analyzer (1 Tool)
Tool: [`analyze_uploaded_file`](extension/mcp-servers/bridge/tools/file_analyzer.py)

- Handles image and document uploads dropped into the VibeZoo Dropzone panel. Runs OCR, pixel spatial statistical analysis (SSA), and MiniCPM vision inference.

### 1.6 Fix Loop & Autonomous Healing (3 Tools)
Tools: [`auto_fix_status`](extension/mcp-servers/bridge/tools/fix_loop.py), [`check_intervention`](extension/mcp-servers/bridge/tools/fix_loop.py), [`retry_build`](extension/mcp-servers/bridge/tools/fix_loop.py)

- Monitors terminal build failures, retrieves previous resolution patterns from Crow Memory, tracks auto-fix attempts, and supports Human-in-the-Loop interventions.

### 1.7 Integrated Scenarios (1 Tool)
Tools: [`review_project`](extension/mcp-servers/bridge/tools/integrated.py)

- High-level composite tool executing full multi-stage review workflow (search → review → quality scan → pattern extraction).

### 1.8 Analysis & Refactoring (2 Tools)
Tools: [`review_pr`](extension/mcp-servers/bridge/tools/analysis.py), [`refactor_across_files`](extension/mcp-servers/bridge/tools/analysis.py)

- Inspects Git PR diffs and generates coordinated cross-file refactoring plans.

### 1.9 Knowledge & Preferences (3 Tools)
Tools: [`recall_project`](extension/mcp-servers/bridge/tools/knowledge.py), [`learn_preference`](extension/mcp-servers/bridge/tools/knowledge.py), [`get_preferences`](extension/mcp-servers/bridge/tools/knowledge.py)

- Stores and retrieves user coding preferences into Crow Memory synaptic registers.

### 1.10 Web & Search (2 Tools)
Tools: [`web_search`](extension/mcp-servers/bridge/tools/web.py), [`fetch_page`](extension/mcp-servers/bridge/tools/web.py)

- **`web_search`**: Autonomous neural search using the **Exa API** (`EXA_API_KEY` environment variable). Automatically falls back to DuckDuckGo when no API key is provided.
- **`fetch_page`**: Fetches and extracts clean markdown/text content from external documentation URLs.

### 1.11 SSA — Spatial Statistical Analysis (1 Tool)
Tool: [`aggregate_spatial_pixels`](extension/mcp-servers/bridge/tools/ssa.py)

- OpenCV-based pixel color distributions, layout density, and spatial feature analysis.

### 1.12 Setup & Telemetry (2 Tools)
Tools: [`vibezoo_setup`](extension/mcp-servers/bridge/tools/setup.py), [`vibezoo_feedback`](extension/mcp-servers/bridge/tools/feedback.py)

- **`vibezoo_setup`**: Automatically configures global `mcp_settings.json`, custom mode templates, and system tools.
- **`vibezoo_feedback`**: Records telemetry feedback in `feedbacks/` for continuous agent optimization.

---

## 2. Vision AI Pipeline & Dropzone

VibeZoo includes an integrated vision analysis pipeline:
- **Image Dropzone (`vibezoo.openDropzone`)**: Paste or drag images directly into VS Code.
- **Auto-Analysis (`vibezoo.image.autoAnalyze`)**: Automatically runs OCR, SSA spatial statistics, and local MiniCPM vision inference when an image is received.
- **Vision Fallback**: Seamlessly falls back from local VLM to cloud LLM multimodal inputs when needed.

---

## 3. Crow Memory Overview

Standalone Crow Memory repository: **[vibezoo/crowmemory](https://github.com/vibezoo/crowmemory)**

### 3.1 Philosophy — "Crow remembers not the code, but the hand that wrote it."
Crow uses fixed-size synaptic weight matrices and exponential decay ($\lambda$) to implement **Creative Forgetting**. Rather than endlessly hoarding raw text, Crow compresses and personalizes memory to adapt to your evolving coding style.

### 3.2 The 8 Synaptic Registers
- **Code Domain**: `style`, `bug`, `arch`, `context`
- **Life Domain**: `life_pref`, `life_avoid`, `life_phil`, `life_context`

### 3.3 Hebbian EMA Update Rule
$$W_{\text{new}} = \lambda \cdot W_{\text{old}} + (1 - \lambda) \cdot (\text{key} \otimes \text{value})$$

All memories are compressed into a compact binary model (`crow.bin`).

---

## 4. VS Code Extension Commands (20 Commands)

Access these commands from the VS Code Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`):

| Command ID | Title | Description |
|---|---|---|
| `vibezoo.selfCheck` | **VibeZoo: Self Check** | Verifies bridge connectivity, Crow Memory status, and Guard.git |
| `vibezoo.verifyFoundation` | **VibeZoo: Verify Foundation** | Full health audit of MCP, python, and workspace settings |
| `vibezoo.reconnectCrow` | **VibeZoo: Reconnect Crow Memory** | Re-establishes connection to the Crow Memory server |
| `vibezoo.rebuildCodeIndex` | **VibeZoo: Rebuild Code Index** | Triggers full rebuild of semantic vector embedding cache |
| `vibezoo.openWhiteboard` | **VibeZoo: Open Visual Whiteboard** | Launches real-time collaborative Fabric.js whiteboard |
| `vibezoo.openDropzone` | **VibeZoo: Open Image Dropzone** | Opens the drag-and-drop / clipboard image ingestion panel |
| `vibezoo.openUIPreview` | **VibeZoo: Open UI Preview** | Opens live web preview panel |
| `vibezoo.openDashboard` | **VibeZoo: Open Visual Dashboard** | Opens VibeZoo metrics and activity dashboard |
| `vibezoo.openErrorDashboard` | **VibeZoo: Open Error Dashboard** | Displays captured runtime build/lint error diagnostics |
| `vibezoo.configureErrorDashboard` | **VibeZoo: Configure Error Dashboard** | Adjusts error notification thresholds |
| `vibezoo.toggleGuardGit` | **VibeZoo: Toggle Guard.git Protection** | Toggles OS ACL protection on the `.git` folder |
| `vibezoo.instantRewind` | **VibeZoo: Instant Rewind (YOLO)** | Restores files to the previous YOLO snapshot |
| `vibezoo.toggleYolo` | **VibeZoo: Toggle YOLO Mode** | Toggles automatic YOLO snapshot recording |
| `vibezoo.scanProject` | **VibeZoo: Scan Project** | Scans workspace structure and generates tree overview |
| `vibezoo.showSessionResume` | **VibeZoo: Show Session Resume** | Restores previous session context |
| `vibezoo.pauseFixLoop` | **VibeZoo: Pause Fix Loop** | Temporarily pauses automatic error-fixing loops |
| `vibezoo.resumeFixLoop` | **VibeZoo: Resume Fix Loop** | Resumes active error-fixing loops |
| `vibezoo.abortFixLoop` | **VibeZoo: Abort Fix Loop** | Cancels current error-fixing task |
| `vibezoo.startWatching` | **VibeZoo: Start Watching** | Starts file watcher for background build monitoring |
| `vibezoo.stopWatching` | **VibeZoo: Stop Watching** | Stops background file watcher |

---

## 5. Guard.git — Accidental Deletion Protection

VibeZoo's **Guard.git** engine prevents AI agents from executing destructive commands (`rm -rf *`, `rmdir /s /q`) that destroy version history.
- **OS-Level ACL Protection**: Uses Windows `icacls`, Linux `chattr`, and macOS `chmod` to deny write/delete access to `.git` from non-privileged processes.
- **Yocto Snapshot Backup**: Periodically creates micro-backups in `.zoo/yocto/` every 30 minutes.
- **Real-Time Integrity Monitoring**: Proactive `FileSystemWatcher` detects tampering and restores integrity instantly.

---

## 6. Project Architecture & Context

- [`docs/INSTALLATION.md`](docs/INSTALLATION.md) — Comprehensive installation and troubleshooting guide.
- [`docs/ARCHITECTURE_CORE.md`](docs/ARCHITECTURE_CORE.md) — Architectural invariants and bridge design specs.
- [`docs/PROJECT_CONTEXT.md`](docs/PROJECT_CONTEXT.md) — Project background, history, and integration design.
- [`docs/ACTIVE_STATE.md`](docs/ACTIVE_STATE.md) — Current active work session state, plans, and pending items.
- [`plans/`](plans/) — Active and architectural design records.
- [`fromscratch/`](fromscratch/) — Original foundational specifications and roadmap records.

---

## 7. License and Contact

MIT License — See [`extension/package.json`](extension/package.json) (or [MIT License](https://opensource.org/licenses/MIT)).

### Custom Development & Enterprise Solutions
- 🔒 **Secure Deployments** (Air-gapped, encrypted `crow.bin`, custom RBAC)
- 🏢 **Enterprise Customization** (Custom registers, domain decay profiles)
- 🤖 **LLM-Specific Optimization** (Fine-tuned embeddings, specialized MCP tools)

Contact: 📧 **myk1yt@gmail.com**

---
*VibeZoo v0.16.1 — September 2026*
*Co-designed by Stefano, Kim & AI*
