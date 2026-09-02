# VibeZoo Project Context

> **VibeZoo = [Crow Memory](#crow-memory-overview) (Synaptic Memory) + [VibeZoo MCP Bridge](#mcp-tool-catalog) (33 Tools)**
>
> A Companion Extension for Zoo Code that helps the LLM search, analyze, review, and document code more intelligently.

- **Last Updated**: 2026-07-25
- **Version**: v0.16.0 (extension), v0.16.0 (bridge config)
- **License**: MIT
- **Repository**: <https://github.com/vibezoo/VibeZoo_forZoocode>

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Tech Stack](#2-tech-stack)
3. [System Architecture](#3-system-architecture)
4. [Entry Points](#4-entry-points)
5. [Data Flow](#5-data-flow)
6. [Module Map](#6-module-map)
7. [Communication Structure](#7-communication-structure)
8. [MCP Tool Catalog](#8-mcp-tool-catalog)
9. [Key Patterns and Conventions](#9-key-patterns-and-conventions)
10. [Known Issues and Bottlenecks](#10-known-issues-and-bottlenecks)
11. [Quick Start](#11-quick-start)
12. [Key Dependencies](#12-key-dependencies)

---

## 1. Project Overview

| Item | Details |
|------|---------|
| **Name** | VibeZoo |
| **Display Name** | `%vibezoo.displayName%` (i18n) |
| **Version** | `0.16.0` |
| **Type** | VS Code Extension + Python MCP Server (dual project) |
| **Purpose** | Companion extension for Zoo Code (AI coding assistant). Provides code search, review, visual collaboration, autonomous build fix, and memory-based personalization |
| **Target Platform** | VS Code `^1.90.0` |
| **Key Features** | Guard.git (`.git` protection), YOLO snapshots, Whiteboard/Dropzone, Crow Memory integration, 33 MCP tools |
| **License** | MIT |
| **Repository** | <https://github.com/vibezoo/vibezoo> |

VibeZoo extends Zoo Code's functionality without modifying a single line of its source code, using MCP/SSE and the VS Code Extension API. The core philosophy is **"Crow remembers not the code, but the hand that wrote it."** — remembering not the code itself, but the user's habits and context.

> **Crow Memory Core Concept**: Transformer-based LLMs are fixed at training time. Crow implements **"Creative Forgetting"** through fixed-size weight matrices and λ (decay rate), trading 100% accurate recall for responses biased toward **the current you**.
>
> Hebbian EMA update rule: `W_new = λ · W_old + (1 − λ) · (key ⊗ value)`

---

## 2. Tech Stack

### 2.1 VS Code Extension (TypeScript)

| Technology | Version / Purpose |
|------------|-------------------|
| TypeScript | `^5.3.0` — Extension logic implementation |
| VS Code API | `^1.90.0` — Extension, TreeView, Webview, StatusBar |
| CommonJS | Module system per `extension/tsconfig.json` |
| ES2022 | Target runtime |
| `minimatch` | Glob pattern matching |
| `eslint` | Linting |
| `@vscode/vsce` | VSIX packaging |
| `@vscode/l10n-dev` | Internationalization (i18n/l10n) support — English base + Korean (`ko`) translation pack |

### 2.2 MCP Bridge Server (Python)

| Technology | Purpose |
|------------|---------|
| Python | `3.10+` |
| `fastmcp` | FastMCP SSE server framework |
| `starlette` | HTTP routing (`/health`, `/tools/list_subagents`) |
| `tree_sitter_languages` | Multi-language AST parsing |
| `llama-cpp-python` | MiniCPM-V GGUF inference |
| `pytesseract` / `PaddleOCR` | OCR engine |
| `opencv-python` | Image preprocessing, SSA |
| `curl_cffi` + `selectolax` + `httpx` | Web search/parsing |
| `requests` | Crow Memory REST API client |

---

## 3. System Architecture

VibeZoo consists of a **3-Layer Hybrid Architecture**. Since v0.15.1, Zoo Code auto-starts the Python MCP Bridge (port 9027) via `autoStart` and `autoStartCommand` defined in `mcp_settings.json`. The VibeZoo extension monitors the physical port (`netstat`/`lsof`) to detect and clean up duplicate/zombie processes on port 9027, ensuring conflict-free auto-connect.

```text
┌───────────────────────────────────────────────────────────────────────┐
│                         VS Code Window                                 │
│  ┌───────────────────────┐    ┌────────────────────────────────────┐  │
│  │   Zoo Code (LLM)      │    │  VibeZoo Extension                  │  │
│  │  • LLM Reasoning      │    │  ┌──────────────────────────────┐  │  │
│  │  • Built-in Crow      │    │  │ Phase 0: Foundation           │  │  │
│  │    (localhost:9020)   │    │  │ Wave 1: Flow Keepers          │  │  │
│  │  • MCP Client         │    │  │ Wave 2: Safety Net            │  │  │
│  │  • @mention Chat      │    │  │ Wave 3: Context Intel         │  │  │
│  └───────────┬───────────┘    │  │ Wave 4: Orchestra             │  │  │
│              │ MCP/SSE        │  │ Wave 5: Visual Vibe           │  │  │
│              │                │  │ Wave 7: Error Collect         │  │  │
│              │                │  └──────────────────────────────┘  │  │
│              │                │  • Guard.git (Safety)               │  │
│              │                │  • StatusBar / TreeView             │  │
│              │                │  • Visual Panels (Webview)          │  │
│              │                │  • PythonResolver / McpConfigService│  │
│              │                │  • SelfCheck + Auto-Recovery        │  │
│  └───────────┼────────────────┴────────────────────────────────────┘  │
└──────────────┼───────────────────────────────────────────────────────┘
                │  MCP/Streamable — global `mcp_settings.json` (always synced)
                ▼
┌───────────────────────────────────────────────────────────────────────┐
│                         VibeZoo Extension Host                         │
│  ┌──────────────────────────────┐    ┌──────────────────────────────┐ │
│  │   PythonResolver             │    │   McpConfigService            │ │
│  │   (6-step discovery chain)   │    │   (project-level MCP config)  │ │
│  └──────────────┬───────────────┘    └──────────────┬───────────────┘ │
│                 │                                    │                 │
│  ┌──────────────▼───────────────┐    ┌──────────────▼───────────────┐ │
│  │   SubagentManager            │    │   VscodePaths                 │ │
│  │   spawnBridge()              │    │   (cross-platform paths)      │ │
│  │   /health polling            │    └──────────────────────────────┘ │
│  └──────────────┬───────────────┘                                     │
└─────────────────┼─────────────────────────────────────────────────────┘
                   │ child_process.spawn
                   ▼
┌─────────────────────────────┐  ┌─────────────────────────────────┐
│ Crow Memory (9020)          │  │ VibeZoo MCP Bridge (9027)       │
│ • Real Crow (proxy mode)    │  │ • 33 MCP Tools                  │
│ • Local in-memory fallback  │  │ • AST Engine (tree-sitter)      │
│ • /health, /ingest, /recall │  │ • Search Engine (rg→git→walk)   │
│                             │  │ • Fuzzy Matcher (trigram Dice)  │
│                             │  │ • Embedding Client (semantic)   │
│                             │  │ • OCR Engine (Tesseract/Paddle) │
│                             │  │ • Vision AI (MiniCPM-V GGUF)    │
│                             │  │ • Error Registry                 │
│                             │  │ • Intent Detector (Crow-Aware)   │
│                             │  │ • Fix Loop State Machine         │
└─────────────────────────────┘  └─────────────────────────────────┘
```

### 3.0 Auto-Connect Flow (v0.15.0)

When the extension activates, auto-connect proceeds in the following order:

1. **[`extension/src/extension.ts`](extension/src/extension.ts:55)** [`activate()`](extension/src/extension.ts:55) starts
2. **[`CrowServerManager.reconnect()`](extension/src/crow/CrowServerManager.ts:130)** — Health check on port 9020; on failure, spawns [`crow_memory_server.py`](extension/mcp-servers/crow_memory_server.py:208) via [`PythonResolver`](extension/src/python/PythonResolver.ts:27)
3. **[`SubagentManager.spawnBridge()`](extension/src/orchestra/SubagentManager.ts)** — Discovers Python interpreter via PythonResolver and runs [`extension/mcp-servers/vibezoo_mcp_bridge.py`](extension/mcp-servers/vibezoo_mcp_bridge.py)
4. **[`McpConfigService.writeGlobalMcp()`](extension/src/mcp/McpConfigService.ts:47)** — Regardless of Bridge success/failure, force-writes `mcpServers.vibezoo` to global `mcp_settings.json` and removes project-level `.roo/mcp.json` config
5. **[`SelfChecker.runAll()`](extension/src/safety/SelfCheck.ts:132)** — Runs diagnostics in background after 5 seconds; on failure, calls [`autoRecover()`](extension/src/safety/SelfCheck.ts:486) to auto-recover Bridge/MCP

> **Core Principle**: The global `mcp_settings.json` always stays up to date instead of project-level `.roo/mcp.json`, preventing duplicate registrations per project.

### 3.1 Layer Composition

| Layer | Directory | Responsibility |
|-------|-----------|----------------|
| **Layer 1** | [`extension/src/`](extension/src/) | VS Code Extension — UI, Safety, Flow, Orchestra, Visual |
| **Layer 2** | [`extension/mcp-servers/bridge/`](extension/mcp-servers/bridge/) | Python MCP Bridge — 33 tools, AST, search, OCR, vision, error handling |
| **Layer 3** | Crow Memory (external) | Synaptic memory server — Hebbian EMA, 8 Registers, `crow.bin` |

### 3.2 Crow Memory's 8 Registers

| Domain | Registers |
|--------|-----------|
| Code Domain | `style`, `bug`, `arch`, `context` |
| Life Domain | `life_pref`, `life_avoid`, `life_phil`, `life_context` |

---

## 4. Entry Points

### 4.1 VS Code Extension

| File | Role | Key Symbol |
|------|------|------------|
| [`extension/src/extension.ts`](extension/src/extension.ts:1) | Extension main entry point | [`activate()`](extension/src/extension.ts:55), [`deactivate()`](extension/src/extension.ts:638), [`autoConfigureMCP()`](extension/src/extension.ts:718), [`ensureTemplates()`](extension/src/extension.ts:725), `setRestartBridgeFn` |
| [`extension/src/python/PythonResolver.ts`](extension/src/python/PythonResolver.ts:1) | Python interpreter discovery/validation | [`PythonResolver.resolve()`](extension/src/python/PythonResolver.ts:61) (6-step chain) |
| [`extension/src/platform/VscodePaths.ts`](extension/src/platform/VscodePaths.ts:1) | Cross-platform VS Code paths | [`getCodeUserPath()`](extension/src/platform/VscodePaths.ts:51), [`getGlobalMcpSettingsPath()`](extension/src/platform/VscodePaths.ts:102) |
| [`extension/src/mcp/McpConfigService.ts`](extension/src/mcp/McpConfigService.ts:1) | Project/global MCP config sync | [`writeProjectMcp()`](extension/src/mcp/McpConfigService.ts:47), [`readGlobalMcp()`](extension/src/mcp/McpConfigService.ts:24) |
| [`extension/package.json`](extension/package.json:1) | Extension manifest | 29 commands, 27 settings, 3 TreeViews, 3 keybindings |
| [`extension/tsconfig.json`](extension/tsconfig.json:1) | TypeScript config | `strict`, ES2022, CommonJS |

### 4.2 MCP Bridge Server

| File | Role | Key Symbol |
|------|------|------------|
| [`extension/mcp-servers/vibezoo_mcp_bridge.py`](extension/mcp-servers/vibezoo_mcp_bridge.py:1) | FastMCP SSE server (port 9027) | `/health` GET, `/tools/list_subagents` POST, `bridge/tools/` module registration |
| [`extension/mcp-servers/crow_memory_server.py`](extension/mcp-servers/crow_memory_server.py:1) | REAL HTTP Crow Memory fallback server (port 9020) | [`run_server()`](extension/mcp-servers/crow_memory_server.py:208), Proxy/Local mode |

### 4.3 Bootstrap / Execution Scripts

| File | OS | Description |
|------|----|-------------|
| [`init_vibezoo.bat`](init_vibezoo.bat:1) | Windows | venv creation → pip install → npm install → tsc |
| [`init_vibezoo.sh`](init_vibezoo.sh:1) | Linux/macOS | Same as above for Linux/macOS |
| [`start_vibezoo_servers.bat`](start_vibezoo_servers.bat:1) | Windows | Auto-start Crow Memory (9020) + VibeZoo Bridge (9027) + Health Check |
| [`start_vibezoo_bridge.bat`](start_vibezoo_bridge.bat:1) | Windows | Standalone VibeZoo Bridge execution (from `%USERPROFILE%\mcp-servers\vibezoo\`) |
| [`watch_vibezoo_bridge.bat`](watch_vibezoo_bridge.bat:1) | Windows | 30-second interval watchdog — bridge health check and auto-restart |

---

## 5. Data Flow

### 5.1 Flow 1: LLM ↔ MCP Bridge (User Action)

```text
User (LM Studio/Zoo Code)
  │
  ├─ @mention parsing ──→ MentionRouter (extension/src/orchestra/MentionRouter.ts:21)
  │
  ├─ MCP/SSE ──→ VibeZoo MCP Bridge (port 9027)
  │                  │
  │                  ├─ tools/__init__.py (auto error capture decorator)
  │                  ├─ error_handler.py → ErrorRegistry (~/.vibezoo-errors/registry.json)
  │                  ├─ ast_singleton.py (shared tree-sitter AST engine)
  │                  ├─ search_engine.py (rg→git grep→walk)
  │                  ├─ fuzzy_matcher.py (trigram Dice coefficient)
  │                  ├─ embedding_client.py (semantic search, Ollama/OpenAI)
  │                  ├─ intent_detector.py (keyword + Crow bias)
  │                  └─ crow_client.py → Crow Memory REST API (port 9020)
  │
  └─ VS Code Extension ──→ SubagentManager (extension/src/orchestra/SubagentManager.ts:15)
                               │
                               ├─ spawnBridge() → Python process spawn
                               ├─ killBridgeOnPort() → kill old version
                               └─ waitForReady() → health check polling
```

### 5.2 Flow 2: Build Feedback

```text
User saves file
  → YoctoManager.executeDirectBackup() (extension/src/safety/YoctoManager.ts:222)
    → onWillSaveTextDocument event
      → createSnapshot('pre-edit') + atomicCopyFile
        → ~/.zoo-code/yocto/{sessionId}/{snapshotId}/ backup
  → BuildFeedback (extension/src/flow/BuildFeedback.ts:9)
    → onDidEndTaskProcess event
      → collectDiagnostics() (LSP)
        → FixLoopManager.onBuildFailure() (extension/src/orchestra/FixLoopManager.ts:116)
          → writeFixRequest() (~/.vibezoo-fix-request.json)
            → LLM responds via MCP tools (auto_fix_status, retry_build)
              → I_instability calculation → GuardMode decision
```

### 5.3 Flow 3: Dropzone File Upload

```text
User drag-and-drop / Ctrl+V
  → Dropzone Webview (VisualVibePanels.ts:963, Fabric.js)
    → postMessage({ type: 'uploadFile' | 'uploadLocalFile' })
      → handleDropzoneUpload() / handleLocalFileDrop()
        → ~/.vibezoo-uploads/{date}/ file saved
          → LLM prompt copied to clipboard
            → User pastes into LLM chat
              → LLM calls MCP tool (analyze_uploaded_file)
                → file_analyzer.py → SSA/OCR/MiniCPM-V pipeline
```

---

## 6. Module Map

### 6.1 Layer 1 — VS Code Extension (`extension/src/`)

| Module | File | Responsibility |
|--------|------|----------------|
| **Config** | [`config/ConfigService.ts`](extension/src/config/ConfigService.ts:3) | Central config access (Host, Port, Guard, toggles) |
| **MCP Config** | [`mcp/McpConfigService.ts`](extension/src/mcp/McpConfigService.ts:1) | Global `mcp_settings.json` forced sync and `.roo/mcp.json` project config cleanup |
| **Python** | [`python/PythonResolver.ts`](extension/src/python/PythonResolver.ts:1) | 6-step Python interpreter discovery chain (`setting` → `venv` → `pyenv` → `python3` → `python` → `py -3`) |
| **Platform** | [`platform/VscodePaths.ts`](extension/src/platform/VscodePaths.ts:1) | Cross-platform VS Code user/global config path calculation |
| **Context** | [`context/ContextIntelligence.ts`](extension/src/context/ContextIntelligence.ts:1) | ContextIndicator, ExplainLessSuggestor, SessionResume, EmotionalDetector |
| **Crow** | [`crow/CrowServerManager.ts`](extension/src/crow/CrowServerManager.ts:11) | Crow Memory connection detection, healthCheck, auto spawn |
| **Flow** | [`flow/BuildFeedback.ts`](extension/src/flow/BuildFeedback.ts:9) | `onDidEndTaskProcess` subscription → auto build feedback |
| | [`flow/BuildTaskProvider.ts`](extension/src/flow/BuildTaskProvider.ts:31) | Silent Build Task Provider (Node/Rust/Go, etc.) |
| | [`flow/ErrorCollection.ts`](extension/src/flow/ErrorCollection.ts:30) | `registry.json` polling (5s), Critical alerts |
| | [`flow/ProjectDetector.ts`](extension/src/flow/ProjectDetector.ts:22) | Workspace type detection + mode suggestion |
| | [`flow/ProjectTreeScanner.ts`](extension/src/flow/ProjectTreeScanner.ts:8) | Async Generator-based tree scan + 30s TTL cache |
| **Orchestra** | [`orchestra/SubagentManager.ts`](extension/src/orchestra/SubagentManager.ts:15) | MCP Bridge spawn/terminate + health check |
| | [`orchestra/MentionRouter.ts`](extension/src/orchestra/MentionRouter.ts:13) | @mention parsing + Chat Participant registration |
| | [`orchestra/FixLoopManager.ts`](extension/src/orchestra/FixLoopManager.ts:92) | State machine (idle→pending→in_progress→building→resolved), `I_instability` calculation, CIM monitoring |
| **Safety** | [`safety/GuardGitManager.ts`](extension/src/safety/GuardGitManager.ts:28) | `.git` directory OS ACL protection (multi-root, Worktree, Rename detection) |
| | [`safety/GuardGitACL.ts`](extension/src/safety/GuardGitACL.ts:107) | OS abstraction layer (icacls/chattr/chmod +a), `execFileSafe()` |
| | [`safety/GitStashManager.ts`](extension/src/safety/GitStashManager.ts:13) | Auto Git stash management on YOLO entry/exit |
| | [`safety/YoctoManager.ts`](extension/src/safety/YoctoManager.ts:13) | Lightweight snapshot system (`onWillSaveTextDocument`, 200ms debounce, Instant Rewind) |
| | [`safety/SelfCheck.ts`](extension/src/safety/SelfCheck.ts:106) | System self-diagnostics (8 check items, AlarmMonitor) |
| | [`safety/AutoBuildFix.ts`](extension/src/safety/AutoBuildFix.ts:23) | STUB — replaced by LLM-driven MCP tools |
| **UI** | [`ui/StatusBarManager.ts`](extension/src/ui/StatusBarManager.ts:100) | StatusBar integration (VibeZoo/Crow/YOLO/CIM/Guard/error count) |
| | [`ui/TreeViewProviders.ts`](extension/src/ui/TreeViewProviders.ts:29) | 3 TreeViews (ActiveSubagents, YOLO History, Session Resume) |
| **Visual** | [`visual/VisualVibePanels.ts`](extension/src/visual/VisualVibePanels.ts:86) | Whiteboard (Fabric.js) + UI Preview + Diagram (Mermaid) + Dropzone Webview |
| | [`visual/ErrorDashboard.ts`](extension/src/visual/ErrorDashboard.ts:12) | `registry.json` watch → Webview dashboard |
| **Types** | [`types/index.ts`](extension/src/types/index.ts:1) | Common type definitions (CrowServerConfig, BuildResult, SubagentNode, GuardGit, etc.) |

### 6.2 Layer 2 — Python MCP Bridge (`extension/mcp-servers/bridge/`)

| Module | File | Responsibility |
|--------|------|----------------|
| **Config** | [`config.py`](extension/mcp-servers/bridge/config.py:1) | Version, URLs, file paths, extension filters, cache settings |
| **Crow Client** | [`crow_client.py`](extension/mcp-servers/bridge/crow_client.py:1) | REST API client (`try_crow_ingest`, `try_crow_recall`, `crow_health_check`) |
| **AST Engine** | [`ast_engine.py`](extension/mcp-servers/bridge/ast_engine.py:16) | Multi-language tree-sitter parser (TS/JS/Python/Go/Rust/C/C++), regex fallback |
| **AST Singleton** | [`ast_singleton.py`](extension/mcp-servers/bridge/ast_singleton.py) | Shared AST engine singleton (consolidated from 5 duplicated copies in v0.16.0) |
| **Search Engine** | [`search_engine.py`](extension/mcp-servers/bridge/search_engine.py:21) | 3-tier search (rg → git grep → os.walk) |
| **Fuzzy Matcher** | [`fuzzy_matcher.py`](extension/mcp-servers/bridge/fuzzy_matcher.py) | Trigram Dice coefficient fuzzy matching for `search_codebase(mode="fuzzy")` (new in v0.16.0) |
| **Embedding Client** | [`embedding_client.py`](extension/mcp-servers/bridge/embedding_client.py) | Embedding-based semantic search with Ollama/OpenAI auto-detection and BM25 fallback (new in v0.16.0) |
| **OCR Engine** | [`ocr_engine.py`](extension/mcp-servers/bridge/ocr_engine.py:70) | Tesseract first, PaddleOCR fallback, AdaptiveThresholding preprocessing |
| **Intent Detector** | [`intent_detector.py`](extension/mcp-servers/bridge/intent_detector.py:1) | Keyword-based intent classification + Crow Memory bias + Dropzone time binding |
| **Error Handler** | [`error_handler.py`](extension/mcp-servers/bridge/error_handler.py:1) | Global error capture decorator, ErrorRegistry (JSON+DCLP singleton) |
| **Auto Fixer** | [`auto_fixer.py`](extension/mcp-servers/bridge/auto_fixer.py) | Known error pattern DB + fix suggestion generation |
| **File Cache** | [`file_cache.py`](extension/mcp-servers/bridge/file_cache.py) | L1 memory cache with 20s TTL for search results |
| **LLM Pipeline** | [`llm_pipeline.py`](extension/mcp-servers/bridge/llm_pipeline.py) | LLM call pipeline |
| **Result Ranker** | [`result_ranker.py`](extension/mcp-servers/bridge/result_ranker.py) | Search result ranking (BM25 + embedding cosine similarity) |
| **Tool Context** | [`tool_context.py`](extension/mcp-servers/bridge/tool_context.py) | Tool execution context management |
| **Utils** | [`utils.py`](extension/mcp-servers/bridge/utils.py) | Common utilities |
| **Vision** | [`vision/minicpm.py`](extension/mcp-servers/bridge/vision/minicpm.py:1) | MiniCPM-V GGUF wrapper (`llama-cpp-python`) |
| **Tools** | [`tools/`](extension/mcp-servers/bridge/tools/__init__.py:1) | 16 files, 33 MCP tools registered |

### 6.3 Directory Tree

```text
extension/src/
├── extension.ts
├── config/
│   └── ConfigService.ts
├── context/
│   └── ContextIntelligence.ts
├── crow/
│   └── CrowServerManager.ts
├── flow/
│   ├── BuildFeedback.ts
│   ├── BuildTaskProvider.ts
│   ├── ErrorCollection.ts
│   ├── ProjectDetector.ts
│   └── ProjectTreeScanner.ts
├── mcp/
│   └── McpConfigService.ts
├── orchestra/
│   ├── FixLoopManager.ts
│   ├── MentionRouter.ts
│   └── SubagentManager.ts
├── platform/
│   └── VscodePaths.ts
├── python/
│   └── PythonResolver.ts
├── safety/
│   ├── AutoBuildFix.ts
│   ├── GitStashManager.ts
│   ├── GuardGitACL.ts
│   ├── GuardGitManager.ts
│   ├── SelfCheck.ts
│   └── YoctoManager.ts
├── types/
│   └── index.ts
├── ui/
│   ├── StatusBarManager.ts
│   └── TreeViewProviders.ts
└── visual/
    ├── ErrorDashboard.ts
    └── VisualVibePanels.ts

extension/mcp-servers/
├── crow_memory_server.py
├── vibezoo_mcp_bridge.py
└── bridge/

mcp-servers/bridge/ (legacy mirror)
├── __init__.py
├── config.py
├── crow_client.py
├── ast_engine.py
├── ast_singleton.py          # NEW in v0.16.0
├── auto_fixer.py
├── embedding_client.py       # NEW in v0.16.0
├── error_handler.py
├── file_cache.py
├── fuzzy_matcher.py          # NEW in v0.16.0
├── intent_detector.py
├── llm_pipeline.py
├── ocr_engine.py
├── result_ranker.py
├── search_engine.py
├── tool_context.py
├── utils.py
├── tools/
│   ├── __init__.py
│   ├── _base.py
│   ├── analysis.py
│   ├── deep_analyzer.py
│   ├── editor.py
│   ├── feedback.py
│   ├── file_analyzer.py
│   ├── fix_loop.py
│   ├── integrated.py
│   ├── knowledge.py
│   ├── reviewer.py
│   ├── scout.py
│   ├── setup.py
│   ├── ssa.py
│   ├── tester.py
│   ├── ux_coordinator.py
│   ├── web.py
│   └── whiteboard.py
└── vision/
    └── minicpm.py
```

---

## 7. Communication Structure

### 7.1 VS Code Extension ↔ Python MCP Bridge

| Method | Port | Protocol/Purpose |
|--------|------|------------------|
| `child_process.spawn` | — | Process lifecycle management (start/stop/health check) |
| JSON file IPC | — | Async command delivery (whiteboard, dropzone, fix request) |
| HTTP fetch | 9027 | `/health` health check [`SubagentManager.ts:199`](extension/src/orchestra/SubagentManager.ts:199) |
| HTTP fetch | 9027 | `/tools/list_subagents` agent status polling [`TreeViewProviders.ts:91`](extension/src/ui/TreeViewProviders.ts:91) |

### 7.2 Zoo Code (LLM) ↔ VibeZoo MCP Bridge

| Method | Port | Protocol/Purpose |
|--------|------|------------------|
| MCP/Streamable | 9027 | `http://{host}:{port}/mcp` — all MCP tool calls |
| Global `mcp_settings.json` | — | Zoo Code auto-config ([`McpConfigService.writeGlobalMcp()`](extension/src/mcp/McpConfigService.ts:47)) |
| Global MCP (`mcp_settings.json`) | — | Read-only reference; never modified |

### 7.3 VibeZoo Bridge ↔ Crow Memory

| Method | Port | Endpoint | Description |
|--------|------|----------|-------------|
| HTTP REST | 9020 | `GET /health` | Health check |
| HTTP REST | 9020 | `POST /ingest` | Memory storage (errors, context) |
| HTTP REST | 9020 | `GET /recall` | Memory search (similar patterns, context) |

Crow Memory URL is configured via the `CROW_SERVER_URL` environment variable (default: `http://localhost:9020`) ([`config.py:13`](extension/mcp-servers/bridge/config.py:13)).

### 7.4 JSON File IPC Paths

Async communication between the VibeZoo Extension and Python Bridge/MCP tools uses **file-based IPC**.

| File Path | Purpose |
|-----------|---------|
| `~/.vibezoo-whiteboard.json` | AI drawing commands |
| `~/.vibezoo-whiteboard-action.json` | Whiteboard open/close |
| `~/.vibezoo-ui-action.json` | UI Preview rendering commands |
| `~/.vibezoo-dropzone-action.json` | Dropzone open |
| `~/.vibezoo-fix-request.json` | Fix Loop state (read by LLM) |
| `~/.vibezoo-errors/registry.json` | Error registry (read by Dashboard) |
| `~/.vibezoo-chat-pending.json` | Chat pending messages |

---

## 8. MCP Tool Catalog

The VibeZoo MCP Bridge provides 33 MCP tools modularized across 16 files.

| Category | File | Tools | Description |
|----------|------|-------|-------------|
| Setup | [`tools/setup.py`](extension/mcp-servers/bridge/tools/setup.py) | `vibezoo_setup` | Dependency installation and MCP/Zoo config automation |
| Scout | [`tools/scout.py`](extension/mcp-servers/bridge/tools/scout.py) | `search_codebase`, `find_references`, `summarize_architecture` | Code search and exploration |
| Reviewer | [`tools/reviewer.py`](extension/mcp-servers/bridge/tools/reviewer.py) | `review_code` | Code quality check (ESLint, go vet integration) |
| Tester | [`tools/tester.py`](extension/mcp-servers/bridge/tools/tester.py) | `generate_tests`, `analyze_coverage` | Test generation and coverage analysis |
| Deep Analyzer | [`tools/deep_analyzer.py`](extension/mcp-servers/bridge/tools/deep_analyzer.py) | `analyze_call_graph`, `map_dependencies`, `extract_patterns`, `reverse_engineer` | Deep AST analysis |
| File Analyzer | [`tools/file_analyzer.py`](extension/mcp-servers/bridge/tools/file_analyzer.py) | `analyze_uploaded_file` | Uploaded file analysis (list check and SSA/OCR/Vision support) |
| Whiteboard | [`tools/whiteboard.py`](extension/mcp-servers/bridge/tools/whiteboard.py) | `draw_on_whiteboard`, `get_whiteboard_state`, `capture_screen` | AI-Human visual collaboration |
| Fix Loop | [`tools/fix_loop.py`](extension/mcp-servers/bridge/tools/fix_loop.py) | `auto_fix_status`, `retry_build`, `check_intervention` | Autonomous build fix loop |
| Integrated | [`tools/integrated.py`](extension/mcp-servers/bridge/tools/integrated.py) | `review_project` | Unified project review |
| Analysis | [`tools/analysis.py`](extension/mcp-servers/bridge/tools/analysis.py) | `explain_code`, `analyze_changes`, `review_pr`, `refactor_across_files` | Code explanation and diff analysis |
| Knowledge | [`tools/knowledge.py`](extension/mcp-servers/bridge/tools/knowledge.py) | `recall_project`, `learn_preference`, `get_preferences` | User knowledge memory |
| Web | [`tools/web.py`](extension/mcp-servers/bridge/tools/web.py) | `fetch_page`, `web_search` | Web search and page analysis |
| SSA | [`tools/ssa.py`](extension/mcp-servers/bridge/tools/ssa.py) | `aggregate_spatial_pixels` | Spatial statistical analysis |
| Editor | [`tools/editor.py`](extension/mcp-servers/bridge/tools/editor.py) | `apply_patch` | AI-safe file editing |
| UX Coordinator | [`tools/ux_coordinator.py`](extension/mcp-servers/bridge/tools/ux_coordinator.py) | `ux_coordinator` | Intent detection and auto tool chains |
| Feedback | [`tools/feedback.py`](extension/mcp-servers/bridge/tools/feedback.py) | `vibezoo_feedback` | Feedback/telemetry logging |


### 8.1 Key Tool Highlights

- **[`apply_patch`](extension/mcp-servers/bridge/tools/editor.py)**
  - `path` optional — auto-detects target file from diff content
  - Fuzzy matching — auto-corrects up to 85% similarity
  - AST-Guided Smart Ellipsis — handles `// ...` placeholders
  - Transactional Apply — dry-run then atomic commit, rollback on failure
  - Auto backup — backs up to `~/.vibezoo-backup/` before modification

- **`ux_coordinator`**
  - Crow Memory-aware intent analysis
  - Intents: `file_share`, `drawing_request`, `code_analysis`, `project_setup`, `fix_loop`

- **`search_codebase`**
  - `target_path` parameter for searching a specific directory
  - ripgrep-based with substring fallback on invalid regex
  - **Search modes** (v0.16.0): `auto` (default), `exact`, `fuzzy` (trigram Dice coefficient), `ast` (tree-sitter), `semantic` (embedding cosine similarity with BM25 fallback)
  - Search result caching with 20s TTL via FileCache L1

- **`find_references`** (v0.16.0 fix)
  - Now uses word-boundary regex (`\b`) instead of substring matching
  - Eliminates false positives (e.g., searching `io` no longer matches `action`)

- **`web_search`** (v0.16.0 improvement)
  - Falls back to DuckDuckGo when `EXA_API_KEY` is absent
  - Structured error codes instead of silent `except: return []`
  - Retry logic: 2 retries with exponential backoff (0.5s, 1.5s)

---

## 9. Key Patterns and Conventions

### 9.1 Extension → Python Bridge via `child_process.spawn`

[`SubagentManager.ts:95`](extension/src/orchestra/SubagentManager.ts:95) spawns the Python MCP Bridge via `spawn('python', [bridgeScript, '--port', port])`. It runs in the background with `detached: true` + `unref()`. To prevent port conflicts on VS Code restart, [`killBridgeOnPort()`](extension/src/orchestra/SubagentManager.ts:146) kills old processes first.

### 9.2 JSON File IPC (Inter-Process Communication)

Async communication between the Extension and Python Bridge/MCP tools uses **file-based IPC**. See [7.4 JSON File IPC Paths](#74-json-file-ipc-paths) for key files.

### 9.3 Selection-Over-Fallback (Hierarchical Fallback)

| Area | Fallback Chain |
|------|----------------|
| Search | ripgrep → git grep → os.walk ([`search_engine.py:73-78`](extension/mcp-servers/bridge/search_engine.py:73)) |
| AST | tree_sitter_languages → individual tree-sitter packages → regex ([`ast_engine.py:127-166`](extension/mcp-servers/bridge/ast_engine.py:127)) |
| OCR | Tesseract → PaddleOCR → disabled ([`ocr_engine.py:203-218`](extension/mcp-servers/bridge/ocr_engine.py:203)) |
| Semantic Search | Embedding server (Ollama/OpenAI) → BM25 fallback with warning ([`embedding_client.py`](extension/mcp-servers/bridge/embedding_client.py)) |
| Session Restore | Crow Memory → local file → YOLO yocto directory ([`ContextIntelligence.ts:80-140`](extension/src/context/ContextIntelligence.ts:80)) |

### 9.4 Event-Driven Architecture (VS Code Events)

| Event | Handler | Result |
|-------|---------|--------|
| `onDidEndTaskProcess` | [`BuildFeedback.ts:10`](extension/src/flow/BuildFeedback.ts:10) | Build result → FixLoopManager |
| `onWillSaveTextDocument` | [`YoctoManager.ts:33`](extension/src/safety/YoctoManager.ts:33) | Pre-save snapshot backup |
| `onDidChangeWorkspaceFolders` | [`GuardGitManager.ts:70`](extension/src/safety/GuardGitManager.ts:70) | Multi-root Guard config |
| `fs.watchFile` | [`VisualVibePanels.ts:167`](extension/src/visual/VisualVibePanels.ts:167) | Action file watch |

### 9.5 Debounce + Stale-While-Revalidate (SWR)

| Target | Behavior | Location |
|--------|----------|----------|
| File change watch | 1000ms debounce | [`ProjectTreeScanner.ts:28`](extension/src/flow/ProjectTreeScanner.ts:28) |
| Whiteboard canvasState | 300ms debounce | [`VisualVibePanels.ts:637`](extension/src/visual/VisualVibePanels.ts:637) |
| Tree scan | 30s TTL + stale-while-revalidate | [`ProjectTreeScanner.ts:39-43`](extension/src/flow/ProjectTreeScanner.ts:39) |
| Notification | 3s same-message prevention + 10/min rate limit | [`StatusBarManager.ts:18-19`](extension/src/ui/StatusBarManager.ts:18) |
| Search results | 20s TTL cache | [`file_cache.py`](extension/mcp-servers/bridge/file_cache.py) |

### 9.6 Graceful Degradation (Best-Effort Architecture)

- Crow Memory connection failure → extension continues normally (all features available without Crow)
- MCP Bridge failure → VibeZoo stays active ([`extension.ts:178-179`](extension/src/extension.ts:178))
- Notification throttle → StatusBar fallback ([`StatusBarManager.ts:62-64`](extension/src/ui/StatusBarManager.ts:62))
- `capture_tool_errors` decorator → zero overhead on success ([`error_handler.py:227`](extension/mcp-servers/bridge/error_handler.py:227))
- Embedding server unavailable → BM25 fallback with visible warning ([`embedding_client.py`](extension/mcp-servers/bridge/embedding_client.py))

### 9.7 Thread Safety (Python Bridge)

- `ErrorRegistry`: DCLP singleton + `threading.Lock` ([`error_handler.py:51-68`](extension/mcp-servers/bridge/error_handler.py:51))
- `ThreadPoolExecutor` (max_workers=4) for async error logging ([`error_handler.py:29`](extension/mcp-servers/bridge/error_handler.py:29))
- `AstEngine`: `threading.Lock` + DCLP pattern ([`ast_engine.py:89`](extension/mcp-servers/bridge/ast_engine.py:89))
- Shared AST singleton via [`ast_singleton.py`](extension/mcp-servers/bridge/ast_singleton.py) (consolidated in v0.16.0)

### 9.8 Naming Convention

| Language | Rule |
|----------|------|
| TypeScript | Classes: `PascalCase` (`CrowServerManager`, `GuardGitManager`), methods/functions: `camelCase` |
| Python | Functions/variables: `snake_case` (`crow_health_check`, `detect_intent_v2`), classes: `PascalCase` |
| Files/directories | `kebab-case` (`mcp-servers`, `crow-memory-server.py`) and `PascalCase` (`ConfigService.ts`) |
| i18n | `%vibezoo.commandName.title%` pattern localization keys |

### 9.9 Error Handling Pattern

- **TypeScript**: `try/catch` with `console.warn` + graceful fallback (non-fatal failures are silently passed)
- **Python**: `try/except Exception` + `logger.debug` (silent failure philosophy)
- All MCP tools: auto-wrapped with [`@capture_tool_errors`](extension/mcp-servers/bridge/error_handler.py) → ErrorRegistry logging + Crow ingest → re-raise exception (propagated to LLM)
- `I_instability` (instability index): same-error repetition rate + edit count + build failures for early cutoff ([`FixLoopManager.ts:75-78`](extension/src/orchestra/FixLoopManager.ts:75))
- **v0.16.0**: `web_search` now surfaces structured error codes instead of silent `except: return []`

### 9.10 Security Patterns

- **Guard.git ACL**: `execFile()` only (no shell), path validation regex, 10-second timeout ([`GuardGitACL.ts:55-73`](extension/src/safety/GuardGitACL.ts:55))
- **C1/C2**: sudo never used, shell injection prevention, all OS commands via `execFileSafe()`
- **Anonymization**: User home path → masked as `~` ([`error_handler.py:34-38`](extension/mcp-servers/bridge/error_handler.py:34))
- **Duplicate activation prevention**: `_activeExtensions` Set blocks double activate ([`extension.ts:67`](extension/src/extension.ts:67))

---

## 10. Known Issues and Bottlenecks

| # | Issue | Description | Location/Evidence |
|---|-------|-------------|-------------------|
| 1 | **JSON file IPC reliability** | Async communication between Extension and Bridge relies entirely on JSON files. No file locking mechanism, so race conditions are possible. Mitigated with `fs.watchFile` + mtime comparison but not perfect. | `~/.vibezoo-*.json` |
| 2 | **Python Bridge SPOF** | 33 MCP tools run in a single Python process (`vibezoo_mcp_bridge.py`). If it crashes, all MCP features go down. | [`extension/mcp-servers/vibezoo_mcp_bridge.py`](extension/mcp-servers/vibezoo_mcp_bridge.py:1) |
| 3 | **Crow Memory FAKE server** | [`crow_memory_server.py`](extension/mcp-servers/crow_memory_server.py:1) simply prints DEPRECATED and exits. The real Crow server is in a separate repository ([vibezoo/crowmemory](https://github.com/vibezoo/crowmemory)), making dependency tracking difficult. | [`extension/mcp-servers/crow_memory_server.py`](extension/mcp-servers/crow_memory_server.py:1) |
| 3-fix | **(Resolved) Crow Memory fallback server** | In v0.15.0, [`extension/mcp-servers/crow_memory_server.py`](extension/mcp-servers/crow_memory_server.py:1) was replaced with a real HTTP server. Proxies to external Crow if present, otherwise serves Local in-memory mode. `sys.exit(0)` removed. | [`extension/mcp-servers/crow_memory_server.py`](extension/mcp-servers/crow_memory_server.py:1) |
| 6-fix | **(Resolved) Project-level MCP config missing** | Fixed bug where `autoConfigureMCP()` skipped writing `.roo/mcp.json` when vibezoo was registered in global MCP. Separated into [`McpConfigService`](extension/src/mcp/McpConfigService.ts:1) to always force-write project config regardless of global settings. | [`extension/src/mcp/McpConfigService.ts`](extension/src/mcp/McpConfigService.ts:1) |
| 7-fix | **(Resolved) Python interpreter discovery failure** | Bridge/Crow spawn failures across various environments (`python`/`python3`/venv/Microsoft Store). Introduced [`PythonResolver`](extension/src/python/PythonResolver.ts:1) with a 6-step chain for deterministic resolution. | [`extension/src/python/PythonResolver.ts`](extension/src/python/PythonResolver.ts:1) |
| 8-fix | **(Resolved) Python bridge missing from VSIX** | `extension/mcp-servers/` was not included in VSIX, so the installed extension couldn't find the Bridge. Moved `extension/mcp-servers/` to `extension/mcp-servers/` and excluded from `.vscodeignore`. | [`extension/mcp-servers/`](extension/mcp-servers/) |
| 9-fix | **(Resolved) Cross-platform global MCP path error** | Hardcoded Zoo Code global MCP settings path for Windows only. Introduced [`VscodePaths`](extension/src/platform/VscodePaths.ts:1) for Stable/Insiders distinction and OS-specific path calculation. | [`extension/src/platform/VscodePaths.ts`](extension/src/platform/VscodePaths.ts:1) |
| 4 | **Excessive `try/except Exception` usage** | Broad exception catches throughout the Python Bridge make debugging difficult. `capture_tool_errors` mitigates this, but silent failures still occur in `_try_crow_ingest`, `_try_auto_fix`, etc. | `extension/mcp-servers/bridge/*.py` |
| 5 | **Config duplication** | [`extension/package.json`](extension/package.json:180) `contributes.configuration` and [`ConfigService.ts`](extension/src/config/ConfigService.ts:3) reference the same settings. New settings may be missed. | [`extension/package.json`](extension/package.json:180), [`ConfigService.ts`](extension/src/config/ConfigService.ts:3) |
| 6 | **Insufficient documentation** | Interface design docs for `extension/mcp-servers/bridge/tools/_base.py` are unclear. JSDoc/Google-style docstrings for tool-specific parameters are lacking. | [`extension/mcp-servers/bridge/tools/_base.py`](extension/mcp-servers/bridge/tools/_base.py) |

---

## 11. Quick Start

### 11.1 Requirements

- Python `3.10+`
- Zoo Code (or MCP-compatible AI coding agent)
- Git
- VS Code `^1.90.0`

### 11.2 Initialization

**Windows:**

```powershell
git clone https://github.com/vibezoo/VibeZoo_forZoocode.git
cd VibeZoo_forZoocode
.\init_vibezoo.bat
```

**macOS / Linux:**

```bash
git clone https://github.com/vibezoo/VibeZoo_forZoocode.git
cd VibeZoo_forZoocode
bash init_vibezoo.sh
```

> The `init_vibezoo` script performs venv creation → pip install → npm install → `tsc` compilation in one step.

### 11.3 Server Execution

**Manual execution:**

```bash
# VibeZoo MCP Bridge (from standard runtime directory)
cd %USERPROFILE%\mcp-servers\vibezoo
python vibezoo_mcp_bridge.py --port 9027
```

**Windows auto-start (Crow Memory + Bridge):**

```powershell
%USERPROFILE%\mcp-servers\vibezoo\start_vibezoo_servers.bat
```

**Watchdog execution (Bridge monitoring):**

```powershell
%USERPROFILE%\mcp-servers\vibezoo\watch_vibezoo_bridge.bat
```

### 11.4 Zoo Code Integration

Running the `vibezoo_setup` tool automatically configures `.roo/mcp.json` and `.zoo/config.json`.

```text
vibezoo_setup(target="minimal", configure_custom_modes=True)
```

Manual configuration:

```json
// global mcp_settings.json
{
  "mcpServers": {
    "vibezoo": {
      "url": "http://localhost:9027/mcp"
    }
  }
}
```

### 11.5 Extension Build/Packaging

| Script | Command | Description |
|--------|---------|-------------|
| `vscode:prepublish` | `npm run compile` | Pre-publish compilation |
| `compile` | `tsc -p ./` | TypeScript compilation |
| `watch` | `tsc -watch -p ./` | Development watch mode |
| `package` | `vsce package` | VSIX packaging |
| `lint` | `eslint src --ext ts` | Linting |
| `l10n:export` | `npx @vscode/l10n-dev export --outDir ./l10n ./src` | Localization extraction |

> The root [`package.json`](package.json:1) only includes `@vscode/l10n-dev` as a dev dependency. Actual extension scripts are defined in [`extension/package.json`](extension/package.json:378).

---

## 12. Key Dependencies

### 12.1 TypeScript (VS Code Extension)

| Package | Version | Purpose |
|---------|---------|---------|
| `@types/vscode` | `^1.90.0` | VS Code Extension API types |
| `typescript` | `^5.3.0` | TypeScript compiler |
| `@vscode/vsce` | `^2.22.0` | VSIX packaging |
| `@vscode/l10n-dev` | `^0.0.35` | Localization tooling |
| `minimatch` | `^10.2.5` | Glob pattern matching |
| `eslint` | `^8.0.0` | Linting |
| `@types/node` | `^20.0.0` | Node.js API types |

### 12.2 Python (MCP Bridge)

| Package | Purpose |
|---------|---------|
| `fastmcp` | FastMCP SSE server framework |
| `starlette` | HTTP routing (custom_route) |
| `requests` | Crow Memory REST API client |
| `tree_sitter_languages` | Multi-language AST parsing |
| `llama-cpp-python` | MiniCPM-V GGUF inference |
| `pytesseract` | Tesseract OCR |
| `PaddleOCR` | OCR fallback |
| `opencv-python` | Image preprocessing, SSA |
| `curl_cffi` | Web search engine |
| `selectolax` + `httpx` | HTML parsing |

---

## Appendix: Reference Resources

- **VibeZoo Repository**: <https://github.com/vibezoo/VibeZoo_forZoocode>
- **Crow Memory Repository**: <https://github.com/vibezoo/crowmemory>
- **Sponsor**: <https://teamsunplaza.gumroad.com/l/vibezoo>
- **Contact**: <myk1yt@gmail.com>

---

*VibeZoo v0.16.0 — July 2026*  
*Co-designed by Stefano, Kim & AI*
