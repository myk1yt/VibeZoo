# VibeZoo — Intelligent Companion Extension for AI Coding Assistants

[![Guard.git - .git Protection](https://img.shields.io/badge/Guard.git-.git%20Protected-blueviolet)](https://github.com/vibezoo/VibeZoo_forZoocode)

> **VibeZoo = [Crow Memory](#3-crow-memory-overview) (Synaptic Memory) + [VibeZoo MCP Bridge](#1-vibezoo-mcp-bridge--tool-overview-38-tools) (38 Tools)**

VibeZoo is a Companion Extension for Zoo Code. Without modifying a single line of Zoo Code's source code, it enables the LLM to search, analyze, review, and document code more intelligently. It remembers your habits and preferences, and enables real-time visual collaboration (Whiteboard, Dropzone, Vision AI).

---

## Support VibeZoo Development ☕

If you find VibeZoo and Crow Memory helpful for your productivity, consider supporting our development!
**[💖 Sponsor VibeZoo on Gumroad](https://teamsunplaza.gumroad.com/l/vibezoo)**

Your support helps us develop new features and keep the AI coding revolution moving forward.

---

## 🌍 Global i18n / l10n Support

VibeZoo now fully supports global internationalization (i18n). Built on top of the native `vscode.l10n` API, VibeZoo automatically detects your VS Code display language. It currently provides a base English locale along with a fully translated Korean (`ko`) language pack, ensuring a native experience regardless of your region.


---

## 🚀 Out-of-the-Box Setup (Universal UX)

Getting started with VibeZoo is easier than ever. We provide a one-click bootstrapper to set up the Python environment, install dependencies, and build the frontend extension all at once.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/vibezoo/VibeZoo_forZoocode.git
   cd VibeZoo_forZoocode
   ```
2. **Run the bootstrapper:**
   - **Windows:** Double-click `init_vibezoo.bat` or run it in the terminal.
   - **macOS/Linux:** Run `bash init_vibezoo.sh`.
3. **Auto-Bootstrap Agent:** 
   Once the setup is done, open the workspace in your MCP client (like Zoo Code or VS Code). Run the AI Agent, and thanks to the `.zoo/Agent.md` protocol, it will intelligently guide you and configure your `mcp.json` automatically!
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
   - Configure `.roo/mcp.json` with VibeZoo SSE endpoint
   - Configure `.zoo/config.json`
   - **Install 6 custom modes** to Zoo Code's global `custom_modes.yaml` with VibeZoo tool priority enabled

   > **No regex errors!** All modes are instructed to prefer VibeZoo MCP tools (`search_codebase`, `review_code`, `find_bugs`, etc.) over native tools. VibeZoo tools handle invalid regex gracefully with automatic substring fallback.

   > **Tip:** You can still use the manual template from `global_install_templates/vibezoo_mode.yaml` if you prefer a hands-on approach. The `vibezoo_setup` tool automates this process for convenience.

---

## 1. VibeZoo MCP Bridge — Tool Overview (38 Tools)

The VibeZoo MCP Bridge operates based on FastMCP + SSE, communicating with the Zoo Code MCP client via `vibezoo_mcp_bridge.py` at `localhost:9027/sse`. It provides a total of **37+ MCP tools** through a modular architecture (`bridge/tools/`).

### 1.0 Autonomous Agents (2 Tools) — Web Search & Feedback
The `web_search` tool leverages a **Quad-Core Async Search Engine** architecture (powered by `curl_cffi` for advanced bypassing and `selectolax` + `httpx` for high-speed parsing) to autonomously fetch real-time data and documentation. The `vibezoo_feedback` allows the LLM to write telemetry logs (`feedbacks/`) to suggest new capabilities or highlight repetitive tasks for continuous improvement.

### 1.1 UX (3 Tools) — Intent Detection + Auto Tool Chains
When you say "I'll show you a file", the Dropzone opens. Uploaded files are automatically analyzed through the SSA→OCR→MiniCPM pipeline.

The [`ux_coordinator`](mcp-servers/bridge/tools/ux_coordinator.py) tool is now **Crow Memory-aware** — when keyword-based intent detection has low confidence, it queries Crow Memory for recent context (dropzone uploads, conversation history) to disambiguate. Detected intents include `file_share`, `drawing_request`, `code_analysis`, `project_setup`, and the new **`fix_loop`** — automatic bug fix / error recovery.

### 1.2 Scout (3 Tools) — Code Search and Exploration
Quickly grasp the project structure and find symbols or functions accurately using tree-sitter AST.
**`target_path` parameter added**: Enables global search in a specific directory (e.g., `search_codebase(query=..., target_path="C:/Projects/MyApp")`).

### 1.3 Reviewer (2 Tools) — Code Quality Check
Automatically check code quality before submitting a PR. Integrates with ESLint and go vet.

### 1.4 Tester (2 Tools) — Test Generation and Coverage
Detects function signatures to automatically generate test templates and measure coverage.

### 1.5 Deep Analyzer (4 Tools) — Deep AST Analysis
Analyzes call graphs, dependencies, and recurring patterns using tree-sitter AST, and automatically generates documentation.

### 1.6 Whiteboard (4 Tools) — AI-Human Visual Collaboration
The AI draws on a Fabric.js canvas, reads user modifications, and can capture the screen.

### 1.7 Fix Loop (3 Tools) — Autonomous Build & Fix Loop
If a build fails, the LLM automatically analyzes the error, looks up past fix patterns in Crow Memory, and suggests fixes. Supports Human-in-the-Loop.

New **`fix_loop` intent** — the [`ux_coordinator`](mcp-servers/bridge/tools/ux_coordinator.py) can now route bug-fix and error-recovery scenarios directly to the Fix Loop workflow, enabling seamless transitions from intent detection to autonomous repair.

### 1.8 Integrated (4 Tools) — Unified Scenario Tools
Combines multiple tools into a single workflow. Just say "Review this", and it runs search → review → quality → patterns sequentially.

### 1.9 Analysis (4 Tools) — Code Explanation and Diff Analysis
Explains what specific code lines do, analyzes git diffs, supports PR reviews, and proposes bulk refactoring.

### 1.10 Knowledge (2 Tools) — Project Knowledge Memory
Saves project structures and patterns into Crow Memory and recalls them later.

### 1.11 Preferences (2 Tools) — User Preference Learning
Stores your coding style and preferences in Crow Memory to be recalled when needed.

### 1.12 Web (2 Tools) — Web Search and Page Analysis
Used to reference external documentation or search for the latest technical information.

### 1.13 SSA (1 Tool) — Spatial Statistical Analysis
Spatial Statistical Aggregator: OpenCV-based image pixel statistics analysis, including OCR.

### 1.14 Editor (2 Tools) — AI-Safe File Editing
Apply patches to files without worrying about missing parameters. The [`apply_patch`](mcp-servers/bridge/tools/editor.py) tool:
- **`path` optional**: Auto-detects target file from diff content
- **Fuzzy matching**: Auto-corrects up to 85% similarity (ignores whitespace/indentation differences)
- **AST-Guided Smart Ellipsis**: Detects `// ...`, `# ...`, `/* ... */` placeholders in SEARCH blocks and resolves them via text fuzzy matching + optional AST scope verification — LLMs can safely use `// ... existing code ...` placeholders
- **Transactional Apply**: All SEARCH/REPLACE blocks are validated in an in-memory dry-run first (Phase 1). Only if all blocks succeed does the atomic commit (Phase 2) proceed; on any failure, the entire operation rolls back — no partial modifications
- **Auto backup**: Backs up to `~/.vibezoo-backup/` before modification
- **Supports both `=======` / `-------`**: Compatible with `apply_diff`

- **`read_project_file`**: Read file or list directory contents. If path is a file, returns content with syntax highlighting. If path is a directory, returns listing with sizes.

### 1.15 Setup (1 Tool) — Automation
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

VibeZoo Bridge는 Windows 부팅 시 자동 실행되며, Watchdog이 지속적으로 서버 상태를 모니터링합니다.

### Auto-Start (Windows Startup)
[`start_mcp_servers.bat`](start_mcp_servers.bat)이 Windows 부팅 시 다음을 자동 실행합니다:
1. **Crow Memory Server** (port 9020) — `start_crow_sse.bat`에 위임 (락 정리 + 헬스체크 내장)
2. **VibeZoo Bridge** (port 9027) — Python 절대경로로 실행, stderr/stdout 로깅
3. **Health Check** — 각 서버가 준비될 때까지 최대 60초 대기 (backoff: 2→2→3→5초)
4. **Watchdog** — Crow Memory + VibeZoo Bridge 각각 30초 간격 모니터링

### Watchdog
- **Crow Memory Watchdog**: [`watch_crow_sse.bat`](../Crow%20Memory/watch_crow_sse.bat)
- **VibeZoo Bridge Watchdog**: [`watch_vibezoo_bridge.bat`](watch_vibezoo_bridge.bat)
  - 30초마다 `netstat` + curl 헬스체크
  - 서버가 죽었으면 자동 재시작 (최대 5회 연속 실패 시 중지)
  - 로그: `%USERPROFILE%\.vibezoo\watchdog_bridge.log`

### REST API (Crow Memory 연동)
VibeZoo Bridge는 Crow Memory의 REST API를 통해 메모리를 저장하고 검색합니다:
- `GET /health` — 서버 상태 확인
- `POST /ingest` — 에러/컨텍스트 저장
- `GET /recall` — 유사 에러/패턴 검색

### 변경 이력
- **v0.00.1** (2026-06-12):
  - MCP 서버 안정화: REST API 연동, Startup batch 전면 재작성, Watchdog 도입
  - Broad `except Exception` → 구체적 예외 처리
  - FAKE Crow 서버 폐기 → REAL Crow로 단일화
  - 하드코딩된 Crow URL 제거 → `config.CROW_URL` 사용

---

## 5. Quick Start

### 5.1 Requirements
- **Python 3.10+**
- **Zoo Code** (or MCP-compatible AI Coding Agent)
- Git

### 5.2 Installation
**Windows (PowerShell):**
```powershell
git clone https://github.com/vibezoo/crowmemory.git
cd crowmemory
.\install.ps1
```

**macOS / Linux:**
```bash
git clone https://github.com/vibezoo/crowmemory.git
cd crowmemory
python install.py
```

### 5.3 Manual VibeZoo MCP Bridge Configuration
```json
// .roo/mcp.json
{
  "mcpServers": {
    "vibezoo": {
      "url": "http://localhost:9027/sse"
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
*VibeZoo v0.15.0 — June 2026*
*Co-designed by Stefano, Kim & AI*
