# VibeZoo — Intelligent Companion Extension for AI Coding Assistants

[![Guard.git - .git Protection](https://img.shields.io/badge/Guard.git-.git%20Protected-blueviolet)](https://github.com/vibezoo/VibeZoo_forZoocode)

> **VibeZoo = [Crow Memory](#3-crow-memory-overview) (Synaptic Memory) + [VibeZoo MCP Bridge](#1-vibezoo-mcp-bridge--tool-overview-33-tools) (33 Tools)**

VibeZoo is a Companion Extension for Zoo Code. Without modifying a single line of Zoo Code's source code, it enables the LLM to search, analyze, review, and document code more intelligently. It remembers your habits and preferences, and enables real-time visual collaboration (Whiteboard, Dropzone, Vision AI).

---

## Support VibeZoo Development ☕

If you find VibeZoo and Crow Memory helpful for your productivity, consider supporting our development!
**[💖 Sponsor VibeZoo on Gumroad](https://teamsunplaza.gumroad.com/l/vibezoo)**

Your support helps us develop new features and keep the AI coding revolution moving forward.

---

## 🌍 Global i18n / l10n Support

VibeZoo fully supports global internationalization (i18n) across **20 languages** (English base + ar, bg, cs, de, es, fr, he, hu, it, ja, ko, pl, pt-BR, ru, th, tr, vi, zh-CN, zh-TW). Built on top of the native `vscode.l10n` API, VibeZoo automatically detects your VS Code display language, ensuring a native experience regardless of your region.


---

## 🚀 Out-of-the-Box Setup (Universal UX)

Getting started with VibeZoo is easier than ever. We provide a one-click bootstrapper to set up the Python environment, install dependencies, and build the frontend extension all at once.

### Standard Directory Layout

VibeZoo now follows the same standard path scheme as Crow Memory:

| Platform | Runtime Directory |
|----------|-----------------|
| Windows  | `%USERPROFILE%\mcp-servers\vibezoo\` |
| macOS/Linux | `~/mcp-servers/vibezoo/` |

The auto-start command in MCP settings is:
```
cd /d "%USERPROFILE%\mcp-servers\vibezoo" && start_vibezoo_bridge.bat
```

All MCP servers (`crow-memory`, `vibezoo`, etc.) coexist under `%USERPROFILE%\mcp-servers\`.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/vibezoo/VibeZoo_forZoocode.git
   cd VibeZoo_forZoocode
   ```
2. **Run the bootstrapper:**
   - **Windows:** Double-click `init_vibezoo.bat` or run it in the terminal.
   - **macOS/Linux:** Run `bash init_vibezoo.sh`.
   
   This creates the standard runtime directory, copies bridge files, sets up a Python venv, and builds the extension.
3. **Auto-Connect:**
   Once the VibeZoo extension is active, it automatically starts the Python MCP Bridge on port `9027`, resolves a working Python interpreter across `python`/`python3`/venv environments, and keeps the global `mcp_settings.json` synchronized so Zoo Code connects via Streamable HTTP automatically.
4. **Global Mode Installation (via `vibezoo_setup` — Recommended):**
   VibeZoo provides a one-command setup that automatically installs all 6 custom modes (orchestrator-crow, project-research, architect, code, debug, ask) with VibeZoo tool priority enabled across ALL modes.

   **Step 1:** Start the VibeZoo Bridge:
   ```bash
   python mcp-servers/vibezoo_mcp_bridge.py --port 9027
   ```

   **Step 2:** In your Zoo Code chat, run the setup tool:
   ```
   vibezoo_setup(target="minimal", configure_custom_modes=True)
   ```

   This will:
   - Install/verify Python dependencies (fastmcp, uvicorn, starlette)
   - Configure global `mcp_settings.json` with VibeZoo Streamable HTTP endpoint
   - Configure `.zoo/config.json`
   - **Install 6 custom modes** to Zoo Code's global `custom_modes.yaml` with VibeZoo tool priority enabled

   > **No regex errors!** All modes are instructed to prefer VibeZoo MCP tools (`search_codebase`, `review_code`, `review_project`, etc.) over native tools. VibeZoo tools handle invalid regex gracefully with automatic substring fallback.

   > **Tip:** You can still use the manual template from `global_install_templates/vibezoo_mode.yaml` if you prefer a hands-on approach. The `vibezoo_setup` tool automates this process for convenience.

---

## 1. VibeZoo MCP Bridge — Tool Overview (33 Tools)

The VibeZoo MCP Bridge operates based on FastMCP + Streamable HTTP, communicating with the Zoo Code MCP client via `vibezoo_mcp_bridge.py` at `localhost:9027/mcp`. It provides a total of **33 MCP tools** through a modular architecture (`bridge/tools/`).

Key infrastructure modules:
- [`ast_singleton.py`](mcp-servers/bridge/ast_singleton.py) — Shared AST engine singleton (consolidated from 5 duplicated copies)
- [`fuzzy_matcher.py`](mcp-servers/bridge/fuzzy_matcher.py) — Trigram Dice coefficient fuzzy matching engine
- [`embedding_client.py`](mcp-servers/bridge/embedding_client.py) — Embedding-based semantic search client (Ollama/OpenAI auto-detection)
- [`result_ranker.py`](mcp-servers/bridge/result_ranker.py) — BM25 + embedding cosine similarity result ranking
- [`file_cache.py`](mcp-servers/bridge/file_cache.py) — L1 memory cache with 20s TTL for search results

### 1.0 Autonomous Agents — Feedback & Telemetry
The [`vibezoo_feedback`](mcp-servers/bridge/tools/feedback.py) tool lets the LLM write telemetry logs (`feedbacks/`) to suggest new capabilities or highlight repetitive tasks for continuous improvement. (Web search tools are covered in [1.11 Web](#111-web-2-tools--web-search-and-page-analysis).)

### 1.1 UX (2 Tools) — Intent Detection + Auto Tool Chains
When you say "I'll show you a file", the Dropzone opens. Uploaded files are automatically analyzed through the SSA→OCR→MiniCPM pipeline.

Tools: [`ux_coordinator`](mcp-servers/bridge/tools/ux_coordinator.py), [`analyze_uploaded_file`](mcp-servers/bridge/tools/file_analyzer.py)

The [`ux_coordinator`](mcp-servers/bridge/tools/ux_coordinator.py) tool is now **Crow Memory-aware** — when keyword-based intent detection has low confidence, it queries Crow Memory for recent context (dropzone uploads, conversation history) to disambiguate. Detected intents include `file_share`, `drawing_request`, `code_analysis`, `project_setup`, and the new **`fix_loop`** — automatic bug fix / error recovery.

### 1.2 Scout (3 Tools) — Code Search and Exploration
Tools: [`search_codebase`](mcp-servers/bridge/tools/scout.py), [`find_references`](mcp-servers/bridge/tools/scout.py), [`summarize_architecture`](mcp-servers/bridge/tools/scout.py)

Quickly grasp the project structure and find symbols or functions accurately using tree-sitter AST.
**`target_path` parameter added**: Enables global search in a specific directory (e.g., `search_codebase(query=..., target_path="C:/Projects/MyApp")`).

**Search modes** (v0.16.0 overhaul):
- `auto` (default) — AST-aware search with automatic fallback
- `exact` — Literal substring matching
- `fuzzy` — Real trigram Dice coefficient approximate matching via [`fuzzy_matcher.py`](mcp-servers/bridge/fuzzy_matcher.py) (previously identical to `auto`; now performs genuine fuzzy matching)
- `ast` — tree-sitter AST symbol extraction
- `semantic` — Embedding-based cosine similarity ranking via [`embedding_client.py`](mcp-servers/bridge/embedding_client.py) with Ollama/OpenAI auto-detection; falls back to BM25 with a visible warning when no embedding server is available

**`find_references` fix**: Now uses word-boundary regex (`\b`) instead of substring matching, eliminating false positives (e.g., searching for `io` no longer matches `action`).

**Search result caching**: Results are cached with a 20s TTL via the existing FileCache L1 layer.

### 1.3 Reviewer (1 Tool) — Code Quality Check
Automatically check code quality before submitting a PR. Integrates with ESLint and go vet.

### 1.4 Tester (2 Tools) — Test Generation and Coverage
Detects function signatures to automatically generate test templates and measure coverage.

### 1.5 Deep Analyzer (4 Tools) — Deep AST Analysis
Tools: [`analyze_call_graph`](mcp-servers/bridge/tools/deep_analyzer.py), [`map_dependencies`](mcp-servers/bridge/tools/deep_analyzer.py), [`extract_patterns`](mcp-servers/bridge/tools/deep_analyzer.py), [`reverse_engineer`](mcp-servers/bridge/tools/deep_analyzer.py)

Analyzes call graphs, dependencies, and recurring patterns using tree-sitter AST, and automatically generates documentation.

### 1.6 Whiteboard (4 Tools) — AI-Human Visual Collaboration
Tools: [`draw_on_whiteboard`](mcp-servers/bridge/tools/whiteboard.py), [`get_whiteboard_state`](mcp-servers/bridge/tools/whiteboard.py), [`capture_screen`](mcp-servers/bridge/tools/whiteboard.py), [`check_uploaded_files`](mcp-servers/bridge/tools/whiteboard.py)

The AI draws on a Fabric.js canvas, reads user modifications, captures the screen, and monitors files uploaded to the Dropzone.


### 1.7 Fix Loop (3 Tools) — Autonomous Build & Fix Loop
If a build fails, the LLM automatically analyzes the error, looks up past fix patterns in Crow Memory, and suggests fixes. Supports Human-in-the-Loop.

New **`fix_loop` intent** — the [`ux_coordinator`](mcp-servers/bridge/tools/ux_coordinator.py) can now route bug-fix and error-recovery scenarios directly to the Fix Loop workflow, enabling seamless transitions from intent detection to autonomous repair.

### 1.8 Integrated (1 Tool) — Unified Scenario Tools
Combines multiple tools into a single workflow. Just say "Review this", and it runs search → review → quality → patterns sequentially.

### 1.9 Analysis (4 Tools) — Code Explanation and Diff Analysis
Explains what specific code lines do, analyzes git diffs, supports PR reviews, and proposes bulk refactoring.

### 1.10 Knowledge & Preferences (3 Tools) — Project Knowledge Memory
[`recall_project`](mcp-servers/bridge/tools/knowledge.py) recalls auto-captured project knowledge (learned at bridge startup via `_auto_learn_project`), while [`learn_preference`](mcp-servers/bridge/tools/knowledge.py) and [`get_preferences`](mcp-servers/bridge/tools/knowledge.py) store and retrieve your coding style and preferences in Crow Memory.

### 1.11 Web (2 Tools) — Web Search and Page Analysis
Used to reference external documentation or search for the latest technical information.

**v0.16.0 improvements**:
- `web_search` now falls back to **DuckDuckGo** when `EXA_API_KEY` is absent, ensuring search always works out of the box
- Errors are surfaced with structured error codes instead of silent `except: return []`
- Retry logic: 2 retries with exponential backoff (0.5s, 1.5s)

### 1.12 SSA (1 Tool) — Spatial Statistical Analysis
Spatial Statistical Aggregator: OpenCV-based image pixel statistics analysis, including OCR.

### 1.13 Editor (1 Tool) — AI-Safe File Editing
Apply patches to files without worrying about missing parameters. The [`apply_patch`](mcp-servers/bridge/tools/editor.py) tool:
- **`path` optional**: Auto-detects target file from diff content
- **Fuzzy matching**: Auto-corrects up to 85% similarity (ignores whitespace/indentation differences)
- **AST-Guided Smart Ellipsis**: Detects `// ...`, `# ...`, `/* ... */` placeholders in SEARCH blocks and resolves them via text fuzzy matching + optional AST scope verification — LLMs can safely use `// ... existing code ...` placeholders
- **Transactional Apply**: All SEARCH/REPLACE blocks are validated in an in-memory dry-run first (Phase 1). Only if all blocks succeed does the atomic commit (Phase 2) proceed; on any failure, the entire operation rolls back — no partial modifications
- **Auto backup**: Backs up to `~/.vibezoo-backup/` before modification
- **Supports both `=======` / `-------`**: Compatible with `apply_diff`


### 1.14 Setup (1 Tool) — Automation
Installs VibeZoo dependencies and auto-configures MCP/Zoo settings.
**ripgrep auto-install**: When running `vibezoo_setup(target="full")`, automatically installs ripgrep via winget/choco/scoop or direct download.

---

## 2. Vision AI Pipeline

VibeZoo includes a built-in Vision AI pipeline for image analysis:
- **MiniCPM-V**: Lightweight Vision-Language Model. Performs image captioning and analysis locally (GGUF + llama-cpp-python).
- **OCR**: Tesseract / PaddleOCR for text extraction (supports Korean, English, Japanese, Chinese).
- **SSA**: OpenCV-based Spatial Statistical Aggregator for pixel statistics and spatial pattern analysis.

---

## 3. Crow Memory Overview

You can find the standalone Crow Memory repository and core engine here: **[vibezoo/crowmemory](https://github.com/vibezoo/crowmemory)**

### 3.1 Philosophy — "Crow remembers not the code, but the hand that wrote it."

Transformer-based LLMs are fixed at training time. RAG or SQLite-based solutions stack information infinitely like a "100% accurate notepad," but the human brain doesn't work that way.
**Forgetting is not a bug.** Crow's fixed-size weight matrices and λ (decay rate) implement "Creative Forgetting." By giving up 100% accurate recall, the AI responding through Crow becomes biased toward **the current you**.

### 3.2 The 8 Registers
- **Code Domain**: `style`, `bug`, `arch`, `context`
- **Life Domain**: `life_pref`, `life_avoid`, `life_phil`, `life_context`

### 3.3 Hebbian EMA Update Rule
Crow updates weights using an Exponential Moving Average (EMA) based on Hebbian learning:
`W_new = λ · W_old + (1 - λ) · (key ⊗ value)`

All memories are compressed into a fixed-size `crow.bin` (140MB). When capacity is exceeded, old memories naturally fade.

### 3.4 10 Crow MCP Tools
Includes tools like `crow_recall`, `crow_ingest`, `crow_diagnostics`, `crow_manage_backup`, and more to interact with the synaptic memory.

---

## 4. Windows Auto-Start & Stability

VibeZoo Bridge auto-starts on Windows boot, with the Watchdog continuously monitoring server health.

### Auto-Start (Windows Startup)
[`start_vibezoo_servers.bat`](start_vibezoo_servers.bat) auto-starts the following on Windows boot:
1. **Crow Memory Server** (port 9020) — Built-in lock cleanup and health check
2. **VibeZoo Bridge** (port 9027) — Runs via absolute Python path with stderr/stdout logging
3. **Health Check** — Waits up to 60 seconds for each server to become ready (backoff: 2→2→3→5s)
4. **Watchdog** — Monitors Crow Memory and VibeZoo Bridge at 30-second intervals

### VS Code Extension Auto-Connect
When the VibeZoo extension activates inside VS Code it performs the following auto-connect sequence:
1. Resolves a working Python interpreter via [`PythonResolver`](extension/src/python/PythonResolver.ts).
2. Spawns the VibeZoo MCP Bridge from the bundled `extension/mcp-servers/` directory.
3. Spawns a Crow Memory fallback server (or proxies to an existing external Crow server).
4. Writes/updates global `mcp_settings.json` with the current Streamable HTTP endpoint and removes legacy `.roo/mcp.json` config.
5. Runs [`SelfCheck`](extension/src/safety/SelfCheck.ts) diagnostics in the background and auto-recovers Bridge/MCP failures.

### Watchdog
- **Crow Memory Watchdog**: [`watch_crow_sse.bat`](../Crow%20Memory/watch_crow_sse.bat)
- **VibeZoo Bridge Watchdog**: [`watch_vibezoo_bridge.bat`](watch_vibezoo_bridge.bat)
  - Runs `netstat` + curl health check every 30 seconds
  - Auto-restarts the server if it dies (stops after 5 consecutive failures)
  - Logs to: `%USERPROFILE%\.vibezoo\watchdog_bridge.log`

### REST API (Crow Memory Integration)
VibeZoo Bridge stores and retrieves memories via Crow Memory's REST API:
- `GET /health` — Check server status
- `POST /ingest` — Store errors and context
- `GET /recall` — Search for similar errors and patterns

### Changelog
- **v0.16.0** (2026-09-02):
  - **Tool inventory cleanup (39→33)**: removed aggregate tools `find_bugs`, `suggest_refactor`, `generate_docs`, `learn_project`, `auto_analyze_whiteboard`, `auto_analyze_after_drop` — equivalent workflows are now prompt-level compositions of the remaining tools
  - Deleted dead `github_diver.py`; purged ghost tool `read_project_file`
  - `analyze_uploaded_file` now supports dropzone session tracking (`track_dropzone` parameter)
  - Removed extension wrapper commands `vibezoo.findBugs` / `vibezoo.suggestRefactor` / `vibezoo.generateDocs` / `vibezoo.learnProject` and orphaned NLS keys across 20 locales
  - Path-safety fixes: no absolute/user-specific paths in bridge output and docs
- **v0.15.2** (2026-07-25):
  - **Tool Ecosystem Overhaul**: Comprehensive enhancement of the VibeZoo MCP tool ecosystem
  - New modules: `fuzzy_matcher.py` (trigram fuzzy matching), `embedding_client.py` (embedding-based semantic search), `ast_singleton.py` (shared AST singleton)
  - `search_codebase(mode="fuzzy")` now performs real trigram approximate matching (was identical to `auto`)
  - `search_codebase(mode="semantic")` now uses embedding-based cosine similarity ranking with BM25 fallback
  - `find_references` fixed: word-boundary regex eliminates false positives
  - Search result caching with 20s TTL
  - `web_search` DuckDuckGo fallback when EXA_API_KEY absent
  - Dead code cleanup: 12 dead entries removed from `_tool_registry` (20→8)
  - Tool consolidation: 5 duplicated AST singletons → shared `ast_singleton.py`
  - `max_tokens` truncation now works in 5 tools
  - 104 CI tests pass
- **v0.15.1** (2026-06-16):
  - Standard path migration: runtime directory changed to `%USERPROFILE%\mcp-servers\vibezoo\` (Windows) / `~/mcp-servers/vibezoo/` (macOS/Linux)
  - `init_vibezoo.bat` / `init_vibezoo.sh` now copy bridge files to the standard target directory
  - `autoStartCommand` updated to `cd /d "%USERPROFILE%\mcp-servers\vibezoo" && start_vibezoo_bridge.bat`
  - Fixed auto-start process conflict: preserved `autoStart` and `autoStartCommand` configuration for Zoo Code auto-start capability. Added physical port occupancy check (`netstat`/`lsof`) and aggressive zombie cleanup to prevent `winerror 10048` socket bind errors.
- **v0.15.0** (2026-06-13):
  - Auto-connect fundamental fix: always write `.roo/mcp.json` even when global MCP config has a `vibezoo` entry
  - New [`PythonResolver`](extension/src/python/PythonResolver.ts), [`McpConfigService`](extension/src/mcp/McpConfigService.ts), [`VscodePaths`](extension/src/platform/VscodePaths.ts)
  - Bundled Python bridge and Crow fallback server inside the VSIX (`extension/mcp-servers/`)
  - Replaced `crow_memory_server.py` stub with a real HTTP fallback/proxy server
  - SelfCheck auto-recovery for Bridge and MCP configuration failures
- **v0.00.1** (2026-06-12):
  - MCP server stabilization: REST API integration, full startup batch rewrite, Watchdog introduction
  - Broad `except Exception` → specific exception handling
  - Retired FAKE Crow server → unified on real Crow
  - Removed hardcoded Crow URLs → uses `config.CROW_URL`

---

## 5. Quick Start

### 5.1 Requirements
- **Python 3.10+**
- **Zoo Code** (or MCP-compatible AI Coding Agent)
- Git

### 5.2 Installation
See the [Out-of-the-Box Setup](#-out-of-the-box-setup-universal-ux) section above, or [`docs/INSTALLATION.md`](docs/INSTALLATION.md) for the full guide:

```bash
git clone https://github.com/vibezoo/VibeZoo_forZoocode.git
cd VibeZoo_forZoocode
# Windows: init_vibezoo.bat   |   macOS/Linux: bash init_vibezoo.sh
```

### 5.3 Manual VibeZoo MCP Bridge Configuration
```json
// global mcp_settings.json
{
  "mcpServers": {
    "vibezoo-bridge": {
      "url": "http://localhost:9027/mcp",
      "type": "streamable-http"
    }
  }
}
```

---

## 6. Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                      VS Code Window                           │
│                                                               │
│  ┌──────────────────────┐    ┌────────────────────────────┐  │
│  │   Zoo Code (LLM)     │    │  VibeZoo Extension          │  │
│  │                      │    │                             │  │
│  │  • LLM Reasoning     │    │  • FixLoopManager          │  │
│  │  • Built-in Crow     │    │  • VisualVibePanels        │  │
│  │    (localhost:9020)  │    │  • Safety Net (Guard.git)  │  │
│  │  • MCP Client        │    │                            │  │
│  └──────────┬───────────┘    └─────────────┬──────────────┘  │
│             │ MCP/SSE                      │ child_process    │
└─────────────┼──────────────────────────────┼──────────────────┘
              ▼                              ▼
┌─────────────────────────┐  ┌─────────────────────────────────┐
│ Crow Memory (9020)      │  │ VibeZoo MCP Bridge (9027)       │
└─────────────────────────┘  └─────────────────────────────────┘
```

**Guard.git**: VibeZoo's Guard.git feature prevents AI agents from accidentally running `rm -rf *` / `rmdir /s /q` etc. and deleting the `.git` folder. It provides OS-level ACL protection using Windows `icacls`, Linux `chattr`, macOS `chmod`, multi-root workspace support, Git Worktree compatibility, FileSystemWatcher real-time monitoring, Yocto snapshot backup, and SelfCheck integrity diagnostics.

---

## 7. License and Contact

MIT License — See [`LICENSE`](LICENSE).

### Commercial Services / Custom Development

Crow Memory is free to use under the MIT license. However, organizations have different needs—security, proprietary LLM integration, custom encoding, compliance, etc.

**We provide custom development services:**
- 🔒 **Secure Deployments** (Air-gapped, encrypted `crow.bin`, RBAC)
- 🏢 **Enterprise Customization** (Custom registers, industry-specific decay profiles)
- 🤖 **LLM-Specific Optimization** (Fine-tuned embeddings, optimized weight matrices)
- 🧩 **Software Integration** (Non-VS Code IDEs, CI/CD hooks)
- 📊 **Enterprise Analytics** (Memory usage dashboards, drift alerts)

> **Contact us for enterprise, secure, or custom-tailored Crow Memory development:**
📧 **myk1yt@gmail.com**

---
*VibeZoo v0.16.0 — July 2026*
*Co-designed by Stefano, Kim & AI*
