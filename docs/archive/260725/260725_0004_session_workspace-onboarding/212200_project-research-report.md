# 🔍 VibeZoo Workspace Onboarding — Precision Scan Report

## Project Identity

- **Name**: VibeZoo
- **Version**: 0.15.1 (extension), 0.14.4 (bridge)
- **License**: MIT
- **Repository**: https://github.com/vibezoo/vibezoo
- **Description**: A companion VS Code extension that provides MCP (Model Context Protocol) tools to Zoo Code (Roo Code fork), with integrated safety nets, visual panels, and an orchestration layer.

---

## 1. Tech Stack & Dependencies

### 1.1 Extension (TypeScript / Node.js)

| Category | Package | Version | Purpose |
|----------|---------|---------|---------|
| **Runtime** | VS Code Engine | ^1.90.0 | Minimum VS Code version |
| **Runtime** | `minimatch` | ^10.2.5 | Glob pattern matching (only runtime dep) |
| **Dev** | `typescript` | ^5.3.0 | TypeScript compiler |
| **Dev** | `@types/vscode` | ^1.90.0 | VS Code API type definitions |
| **Dev** | `@types/node` | ^20.0.0 | Node.js type definitions |
| **Dev** | `@vscode/vsce` | ^2.22.0 | VS Code extension packaging (`.vsix`) |
| **Dev** | `eslint` | ^8.0.0 | Linting |
| **Dev** | `@vscode/l10n-dev` | ^0.0.35 | Localization tooling (i18n) |
| **Root** | `@vscode/l10n-dev` | ^0.0.35 | Root-level l10n export tooling |

### 1.2 MCP Bridge Server (Python)

| Package | Purpose |
|---------|---------|
| `fastmcp` | MCP server framework (SSE transport) |
| `uvicorn` | ASGI server for FastMCP |
| `starlette` | HTTP framework (custom routes) |
| `requests` | HTTP client for Crow Memory communication |
| `tree-sitter` (optional) | AST parsing for code analysis |
| `tree-sitter-languages` (optional) | Multi-language grammar support |
| `Pillow` (optional) | Image processing for dropzone |
| `pytesseract` (optional) | OCR engine for uploaded images |
| `MiniCPM-V` (optional) | Vision model for image analysis |

### 1.3 Build & Packaging

| Tool | Purpose |
|------|---------|
| `tsc` (TypeScript) | Compiles `extension/src/` → `extension/out/` |
| `vsce package` | Packages into `.vsix` for installation |
| `npm run compile` | Triggered by `vscode:prepublish` |

---

## 2. Folder Structure & Purpose Annotations

```
VibeZoo/
├── .gitignore                    # Git ignore rules
├── .rooignore                    # Context pollution prevention for AI agents
├── .yoloignore                   # YOLO mode file guard rules
├── package.json                  # Root package (l10n dev dependency only)
├── init_vibezoo.bat / .sh       # Bootstrap scripts for fresh installs
├── journal.md                    # Development journal
│
├── extension/                    # ★ VS Code Extension (TypeScript)
│   ├── package.json              # Extension manifest (commands, views, config)
│   ├── tsconfig.json             # TypeScript compiler config
│   ├── .vscodeignore             # Files excluded from .vsix
│   ├── src/                      # TypeScript source (→ compiles to out/)
│   │   ├── extension.ts          # ★ MAIN ENTRY POINT — activate() / deactivate()
│   │   ├── config/               # Configuration service
│   │   ├── context/              # Context intelligence (freshness, emotion, session)
│   │   ├── crow/                 # Crow Memory connection manager
│   │   ├── flow/                 # Build feedback, project detection, error collection
│   │   ├── mcp/                  # MCP config service (global/project settings)
│   │   ├── orchestra/            # Subagent lifecycle, mention routing, fix loop
│   │   ├── platform/             # OS-specific paths (global MCP settings location)
│   │   ├── python/               # Python interpreter resolver (6-level chain)
│   │   ├── safety/               # Safety net modules (YOLO, Guard.git, SelfCheck)
│   │   ├── types/                # Shared TypeScript interfaces
│   │   ├── ui/                   # StatusBar, TreeView providers
│   │   └── visual/               # Webview panels (whiteboard, UI preview, dashboard)
│   ├── mcp-servers/              # Python MCP servers (bundled in .vsix)
│   │   ├── vibezoo_mcp_bridge.py # ★ Bridge entry point (FastMCP SSE on :9027)
│   │   ├── crow_memory_server.py # DEPRECATED — redirects to real Crow server
│   │   ├── start_vibezoo_bridge.bat  # Windows startup script
│   │   ├── tools/                # Legacy tool stubs (analyzer.py)
│   │   └── bridge/               # ★ Bridge Python package
│   │       ├── __init__.py
│   │       ├── config.py         # VERSION, CROW_URL, file paths, constants
│   │       ├── search_engine.py  # ripgrep → git grep → os.walk fallback
│   │       ├── ast_engine.py     # tree-sitter multi-language AST parser
│   │       ├── crow_client.py    # HTTP client for Crow Memory REST API
│   │       ├── embedding_client.py # Semantic search (Ollama/OpenAI embedding)
│   │       ├── auto_fixer.py     # Auto-fix loop logic
│   │       ├── error_handler.py  # Tool error capture decorator
│   │       ├── file_cache.py     # L1 memory cache for file contents
│   │       ├── fuzzy_matcher.py  # Fuzzy string matching
│   │       ├── intent_detector.py # User intent detection
│   │       ├── llm_pipeline.py   # LLM integration pipeline
│   │       ├── ocr_engine.py     # OCR for uploaded images
│   │       ├── result_ranker.py  # Search result ranking
│   │       ├── tool_context.py   # Tool execution context
│   │       ├── utils.py          # Shared utilities
│   │       ├── i18n/             # Internationalization (20 languages)
│   │       ├── tools/            # ★ MCP tool registrations (19 modules)
│   │       │   ├── scout.py      # search_codebase, find_references, etc.
│   │       │   ├── reviewer.py   # review_code
│   │       │   ├── deep_analyzer.py # analyze_call_graph, map_dependencies, etc.
│   │       │   ├── tester.py     # generate_tests, analyze_coverage
│   │       │   ├── whiteboard.py # draw_on_whiteboard, get_whiteboard_state
│   │       │   ├── fix_loop.py   # auto_fix_status, retry_build, check_intervention
│   │       │   ├── integrated.py # review_project, find_bugs, suggest_refactor, generate_docs
│   │       │   ├── analysis.py   # explain_code, analyze_changes, review_pr
│   │       │   ├── knowledge.py  # learn_project, recall_project, learn_preference
│   │       │   ├── web.py        # fetch_page, web_search
│   │       │   ├── ssa.py        # aggregate_spatial_pixels
│   │       │   ├── editor.py     # apply_patch, read_project_file
│   │       │   ├── setup.py      # vibezoo_setup
│   │       │   ├── ux_coordinator.py # ux_coordinator
│   │       │   ├── file_analyzer.py  # analyze_uploaded_file, check_uploaded_files
│   │       │   ├── feedback.py   # vibezoo_feedback
│   │       │   └── _base.py      # Base tool class
│   │       └── vision/
│   │           └── minicpm.py    # MiniCPM-V vision model integration
│   ├── l10n/                     # Localization bundles (20 languages)
│   └── media/
│       └── fabric.min.js         # Fabric.js library (bundled for whiteboard)
│
├── mcp-servers/                  # ★ Standalone MCP servers (duplicated from extension/)
│   ├── vibezoo_mcp_bridge.py     # Same as extension/mcp-servers/
│   ├── crow_memory_server.py     # DEPRECATED stub
│   └── bridge/                   # Same bridge package (source of truth)
│       ├── tools/                # All 19 tool modules
│       ├── i18n/translations/    # Translation files (20 languages)
│       └── ...                   # Same modules as extension/mcp-servers/bridge/
│
├── docs/                         # Project documentation & session reports
│   ├── PROJECT_CONTEXT.md        # Project context document
│   └── 260725_*_session_*/       # Session-specific reports
│
├── feedbacks/                    # Architecture & bug report documents
├── fromscratch/                  # Project plans, changelogs, roadmaps
├── global_install_templates/     # Template files for global installation
├── plans/                        # Design documents (bridge merge, guard-git, etc.)
├── templates/                    # Template files (.yoloignore, .zoo/config.json)
├── -p/                           # i18n verification scripts
└── .roo/                         # Roo Code configuration (MCP settings, custom modes)
```

---

## 3. Entry Points

### 3.1 VS Code Extension Activation

**File**: [`extension/src/extension.ts`](extension/src/extension.ts:55)

- **Activation Event**: `onStartupFinished` (defined in [`extension/package.json`](extension/package.json:20))
- **Main Export**: [`activate(context)`](extension/src/extension.ts:55) — async function
- **Deactivate Export**: [`deactivate()`](extension/src/extension.ts:698) — cleanup

The [`activate()`](extension/src/extension.ts:55) function initializes all modules in a specific order:
1. **Phase 0**: Foundation — directories, templates, Crow connection, StatusBar
2. **Wave 1**: Flow Keepers — BuildTaskProvider, BuildFeedback, ProjectDetector
3. **Wave 2**: Safety Net — YoctoManager, GuardGitManager, AutoBuildFix, GitStashManager
4. **Wave 3**: Context Intelligence — ContextIndicator, ExplainLessSuggestor, SessionResume, EmotionalDetector
5. **Wave 3.5**: MCP Bridge spawn — SubagentManager spawns Python bridge
6. **Wave 4**: Orchestra — MentionRouter, Chat Participants
7. **Wave 5**: Visual Vibe — VisualVibePanels (Whiteboard, UI Preview, Dashboard)
8. **Wave 7**: Error Collection — ErrorDashboard polling

### 3.2 MCP Bridge Server Startup

**File**: [`mcp-servers/vibezoo_mcp_bridge.py`](mcp-servers/vibezoo_mcp_bridge.py:1)

- **Transport**: SSE (Server-Sent Events) via FastMCP
- **Default Port**: 9027 (configurable via `vibezoo.bridge.port`)
- **Host**: 127.0.0.1 (local only)
- **Entry**: `mcp.run(transport="sse", host="127.0.0.1", port=args.port)` at [line 90](mcp-servers/vibezoo_mcp_bridge.py:90)
- **Tool Registration**: [`register_all_tools(mcp)`](mcp-servers/bridge/tools/__init__.py:19) — wraps all 16 tool modules
- **Health Check**: [`/health`](mcp-servers/vibezoo_mcp_bridge.py:66) GET endpoint returns `{"status": "ok", "crow": bool, "version": str}`
- **Subagent List**: [`/tools/list_subagents`](mcp-servers/vibezoo_mcp_bridge.py:40) POST endpoint for Zoo Code MCP compatibility

### 3.3 Crow Memory Server

**File**: [`mcp-servers/crow_memory_server.py`](mcp-servers/crow_memory_server.py:1)

- **Status**: DEPRECATED — this is a redirect stub
- **Real Server**: External Crow Memory project (separate `crow_mcp_server.py`)
- **Port**: 9020 (configurable via `vibezoo.crow.port`)
- **Protocol**: HTTP REST API (`/ingest`, `/recall`, `/health`)

### 3.4 Python Dependency Auto-Installation

**File**: [`extension/src/orchestra/SubagentManager.ts`](extension/src/orchestra/SubagentManager.ts:338)

The extension auto-installs Python dependencies (`fastmcp`, `uvicorn`, `requests`) if missing, using the resolved Python interpreter.

---

## 4. Core Architecture: Extension ↔ Bridge ↔ External Tools

### 4.1 Communication Layers

```
┌─────────────────────────────────────────────────────────────────────┐
│                        VS Code Extension                           │
│  (TypeScript, runs in VS Code Node.js host)                       │
│                                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │ Safety   │  │ Flow     │  │ Visual   │  │ Orchestra│          │
│  │ Modules  │  │ Modules  │  │ Panels   │  │ Modules  │          │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘          │
│       │              │              │              │                 │
│  ┌────┴──────────────┴──────────────┴──────────────┴─────┐         │
│  │           ConfigService (Central Config)               │         │
│  │    host: 127.0.0.1  bridge:9027  crow:9020            │         │
│  └────┬──────────────────────────────────────────────────┘         │
│       │                                                             │
│  ┌────┴──────────────────────────────────────────────────┐         │
│  │         SubagentManager (Bridge Lifecycle)             │         │
│  │   spawnBridge() → child_process.spawn(Python)         │         │
│  │   detached: true, unref() (survives VS Code reload)   │         │
│  └───────────────────────┬───────────────────────────────┘         │
│                          │                                          │
│  ┌───────────────────────┴───────────────────────────────┐         │
│  │         CrowServerManager (Crow Lifecycle)             │         │
│  │   reconnect() → HTTP health check → spawn if needed    │         │
│  └───────────────────────┬───────────────────────────────┘         │
│                          │                                          │
└──────────────────────────┼──────────────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
┌─────────────────┐ ┌──────────────┐ ┌─────────────────┐
│ MCP Bridge      │ │ Crow Memory  │ │ Zoo Code MCP    │
│ (Python, SSE)   │ │ (Python, REST│ │ Client (SSE)    │
│ Port: 9027      │ │  Port: 9020) │ │ Connects to     │
│                 │ │              │ │ :9027/sse       │
│ FastMCP +       │ │ Crow Server  │ │                 │
│ Starlette       │ │ (external)   │ │ Provides MCP    │
│                 │ │              │ │ tools to LLM    │
│ 19 tool modules │ │ /ingest      │ │                 │
│ via SSE stream  │ │ /recall      │ │                 │
│                 │ │ /health      │ │                 │
└────────┬────────┘ └──────┬───────┘ └─────────────────┘
         │                 │
         │  HTTP (requests)│
         └────────┬────────┘
                  ▼
         ┌──────────────┐
         │ Crow Memory  │
         │ REST API     │
         │ :9020        │
         └──────────────┘
```

### 4.2 Communication Methods

| Connection | Protocol | Port | Pattern |
|-----------|----------|------|---------|
| Extension → Bridge | HTTP (health check) | 9027 | `GET /health` polling |
| Extension → Crow | HTTP (health check) | 9020 | `GET /health` polling |
| Bridge → Crow | HTTP REST | 9020 | `POST /ingest`, `GET /recall` |
| Zoo Code → Bridge | SSE (MCP) | 9027 | `http://127.0.0.1:9027/sse` |
| Bridge → Extension | File watching | N/A | JSON files in `~/.vibezoo-*.json` |

### 4.3 IPC / Process Management

- **Extension spawns Bridge**: [`SubagentManager.spawnBridge()`](extension/src/orchestra/SubagentManager.ts:44) uses `child_process.spawn()` with `detached: true` and `unref()` so the Python process survives VS Code reloads
- **Extension spawns Crow**: [`CrowServerManager.spawnCrowServer()`](extension/src/crow/CrowServerManager.ts:63) — same pattern
- **Python Discovery**: [`PythonResolver`](extension/src/python/PythonResolver.ts:27) uses a 6-level chain: setting → venv → pyenv → python3 → python → py -3 (Windows fallback)
- **MCP Config Sync**: [`McpConfigService`](extension/src/mcp/McpConfigService.ts:11) writes to global `mcp_settings.json` and project `.roo/mcp.json` to register the Bridge as an MCP server
- **File-based IPC**: Bridge writes to `~/.vibezoo-whiteboard.json`, `~/.vibezoo-fix-request.json`, `~/.vibezoo-dropzone-action.json` — Extension's [`VisualVibePanels`](extension/src/visual/VisualVibePanels.ts:1) watches these files with `fs.watchFile` at 500ms intervals

### 4.4 Data Flow: User Action → Tool Execution

1. User types "search code" in Zoo Code chat
2. Zoo Code (MCP client) sends SSE request to `http://127.0.0.1:9027/sse`
3. Bridge's FastMCP server routes to [`scout.py:search_codebase()`](mcp-servers/bridge/tools/scout.py)
4. Scout uses [`SearchEngine`](mcp-servers/bridge/search_engine.py:23) (ripgrep → git grep → os.walk) + optional [`AstEngine`](mcp-servers/bridge/ast_engine.py:16) (tree-sitter)
5. Results returned via SSE to Zoo Code → displayed in chat

---

## 5. Key Modules — Detailed Description

### 5.1 Extension Modules (`extension/src/`)

#### Config Layer
- **[`ConfigService`](extension/src/config/ConfigService.ts:3)** — Central configuration reader. Provides typed accessors for all `vibezoo.*` VS Code settings (ports, guards, build options). Used by every other module.

#### Flow Layer (Wave 1)
- **[`BuildFeedback`](extension/src/flow/BuildFeedback.ts:9)** — Subscribes to `vscode.tasks.onDidEndTaskProcess`. On build failure, collects LSP diagnostics and dispatches to AutoBuildFix via `vibezoo._autoBuildFix` command.
- **[`BuildTaskProvider`](extension/src/flow/BuildTaskProvider.ts)** — Registers VibeZoo as a task source for VS Code's task system.
- **[`ProjectDetector`](extension/src/flow/ProjectDetector.ts:22)** — Scans workspace root for `.zoo/config.json`, `AGENTS.md`, `.roo/mcp.json` to auto-suggest the appropriate Zoo Code mode.
- **[`ProjectTreeScanner`](extension/src/flow/ProjectTreeScanner.ts)** — Scans project file tree and generates a markdown tree for LLM context.
- **[`ErrorCollection`](extension/src/flow/ErrorCollection.ts:30)** — Polls `~/.vibezoo-errors/registry.json` every 5 seconds for error dashboard data. Updates StatusBar on critical errors.

#### Safety Layer (Wave 2)
- **[`YoctoManager`](extension/src/safety/YoctoManager.ts:13)** — Lightweight snapshot system. Uses `onWillSaveTextDocument` to backup files before save. Stores snapshots in `~/.zoo-code/yocto/`. Supports `instantRewind()` to restore files.
- **[`GuardGitManager`](extension/src/safety/GuardGitManager.ts:28)** — Protects `.git` directory from accidental deletion/modification. Uses OS-specific ACLs (icacls on Windows, chmod on Linux/macOS). Multi-root workspace support. Periodic integrity checks.
- **[`GuardGitACL`](extension/src/safety/GuardGitACL.ts)** — Platform-specific ACL implementation (strategy pattern).
- **[`GitStashManager`](extension/src/safety/GitStashManager.ts)** — Manages git stashes for YOLO mode entry/exit.
- **[`AutoBuildFix`](extension/src/safety/AutoBuildFix.ts:23)** — Stub for future autonomous fix loop. Currently bypasses to LLM-driven MCP tools.
- **[`SelfCheck`](extension/src/safety/SelfCheck.ts:17)** — System self-diagnostics. Checks Bridge connectivity, Crow health, MCP config integrity, whiteboard files, yocto directory. Auto-recovery for recoverable failures. AlarmMonitor with 30/min throttle.

#### Context Intelligence (Wave 3)
- **[`ContextIndicator`](extension/src/context/ContextIntelligence.ts:11)** — Calculates Crow Memory freshness based on `crow.bin` access time.
- **[`ExplainLessSuggestor`](extension/src/context/ContextIntelligence.ts:36)** — Detects recurring explanation patterns in user messages and suggests shortcuts.
- **[`SessionResume`](extension/src/context/ContextIntelligence.ts)** — Manages session persistence and resumption data.
- **[`EmotionalDetector`](extension/src/context/ContextIntelligence.ts)** — Analyzes user message tone (neutral/frustrated/satisfied/urgent).

#### Orchestra Layer (Wave 4)
- **[`SubagentManager`](extension/src/orchestra/SubagentManager.ts:16)** — Core bridge lifecycle manager. Spawns Python MCP bridge, manages version checking, port conflict resolution, process cleanup. Emits status events for TreeView.
- **[`MentionRouter`](extension/src/orchestra/MentionRouter.ts:13)** — Parses `@mention` patterns in chat input and routes to appropriate agent. Registers VS Code Chat Participants for `@scout`, `@reviewer`, `@tester`.
- **[`FixLoopManager`](extension/src/orchestra/FixLoopManager.ts)** — Manages the auto-fix loop state machine.

#### Visual Layer (Wave 5)
- **[`VisualVibePanels`](extension/src/visual/VisualVibePanels.ts:1)** — Creates and manages Webview panels for Whiteboard (Fabric.js canvas), UI Preview (live dev server), Dashboard (Mermaid diagrams), Dropzone (file upload), Error Dashboard. Uses file watching (`fs.watchFile`) to detect MCP tool output files and auto-render.
- **[`ErrorDashboard`](extension/src/visual/ErrorDashboard.ts)** — Specialized Webview for error visualization.

#### MCP Config
- **[`McpConfigService`](extension/src/mcp/McpConfigService.ts:11)** — Manages MCP server registration in both global `mcp_settings.json` and project `.roo/mcp.json`. Merge logic preserves existing user configurations.

#### UI
- **[`StatusBarManager`](extension/src/ui/StatusBarManager.ts)** — Manages VS Code StatusBar items (active status, Crow connection, YOLO mode, CIM mode, suggested mode). Includes `NotificationThrottle` (3s dedup, 10/min limit).
- **[`TreeViewProviders`](extension/src/ui/TreeViewProviders.ts)** — Three TreeView data providers: `ActiveSubagentsProvider`, `YoloHistoryProvider`, `SessionResumeProvider`.

#### Platform
- **[`VscodePaths`](extension/src/platform/VscodePaths.ts)** — OS-specific path resolution for global MCP settings file.

#### Python
- **[`PythonResolver`](extension/src/python/PythonResolver.ts:27)** — Singleton Python interpreter finder. 6-level resolution chain: user setting → venv → pyenv → python3 → python → py -3. Caches result for session lifetime.

#### Types
- **[`types/index.ts`](extension/src/types/index.ts:1)** — All shared TypeScript interfaces: `McpServerDefinition`, `CrowServerConfig`, `PythonCommandCandidate`, `YoctoSnapshot`, `BuildResult`, `SubagentNode`, `SessionSummary`, `EmotionalState`, `GuardGitState`, etc.

### 5.2 Bridge Modules (`mcp-servers/bridge/`)

#### Core Engine
- **[`config.py`](mcp-servers/bridge/config.py:1)** — Central constants: VERSION, CROW_URL, file paths, extension groups, exclude directories.
- **[`search_engine.py`](mcp-servers/bridge/search_engine.py:23)** — 3-tier search: ripgrep → git grep → os.walk fallback. LRU memo cache (20s TTL, 64 entries).
- **[`ast_engine.py`](mcp-servers/bridge/ast_engine.py:16)** — Multi-language tree-sitter AST parser. Supports TS/JS/Python/Go/Rust/C++. Graceful regex fallback when tree-sitter unavailable.
- **[`crow_client.py`](mcp-servers/bridge/crow_client.py:1)** — HTTP client for Crow Memory REST API. Non-blocking: failures don't affect Bridge operation.
- **[`embedding_client.py`](mcp-servers/bridge/embedding_client.py:12)** — Optional semantic search via Ollama or OpenAI embedding server (port 8089).
- **[`error_handler.py`](mcp-servers/bridge/error_handler.py)** — `@capture_tool_errors` decorator that wraps all MCP tool calls in try/except.
- **[`file_cache.py`](mcp-servers/bridge/file_cache.py)** — L1 memory cache for file contents.
- **[`fuzzy_matcher.py`](mcp-servers/bridge/fuzzy_matcher.py)** — Fuzzy string matching for search results.
- **[`intent_detector.py`](mcp-servers/bridge/intent_detector.py)** — User intent detection from natural language.
- **[`llm_pipeline.py`](mcp-servers/bridge/llm_pipeline.py)** — LLM integration pipeline.
- **[`ocr_engine.py`](mcp-servers/bridge/ocr_engine.py)** — OCR for uploaded images (pytesseract).
- **[`result_ranker.py`](mcp-servers/bridge/result_ranker.py)** — Search result ranking/scoring.
- **[`tool_context.py`](mcp-servers/bridge/tool_context.py)** — Tool execution context management.

#### Tool Modules (16 registered)
| Module | Tools Provided |
|--------|---------------|
| [`scout.py`](mcp-servers/bridge/tools/scout.py) | `search_codebase`, `find_references`, `summarize_architecture` |
| [`reviewer.py`](mcp-servers/bridge/tools/reviewer.py) | `review_code` |
| [`deep_analyzer.py`](mcp-servers/bridge/tools/deep_analyzer.py) | `analyze_call_graph`, `map_dependencies`, `extract_patterns`, `reverse_engineer` |
| [`tester.py`](mcp-servers/bridge/tools/tester.py) | `generate_tests`, `analyze_coverage` |
| [`whiteboard.py`](mcp-servers/bridge/tools/whiteboard.py) | `draw_on_whiteboard`, `get_whiteboard_state`, `capture_screen`, `auto_analyze_whiteboard` |
| [`fix_loop.py`](mcp-servers/bridge/tools/fix_loop.py) | `auto_fix_status`, `retry_build`, `check_intervention` |
| [`integrated.py`](mcp-servers/bridge/tools/integrated.py) | `review_project`, `find_bugs`, `suggest_refactor`, `generate_docs` |
| [`analysis.py`](mcp-servers/bridge/tools/analysis.py) | `explain_code`, `analyze_changes`, `review_pr`, `refactor_across_files` |
| [`knowledge.py`](mcp-servers/bridge/tools/knowledge.py) | `learn_project`, `recall_project`, `learn_preference`, `get_preferences` |
| [`web.py`](mcp-servers/bridge/tools/web.py) | `fetch_page`, `web_search` |
| [`ssa.py`](mcp-servers/bridge/tools/ssa.py) | `aggregate_spatial_pixels` |
| [`editor.py`](mcp-servers/bridge/tools/editor.py) | `apply_patch`, `read_project_file` |
| [`setup.py`](mcp-servers/bridge/tools/setup.py) | `vibezoo_setup` |
| [`ux_coordinator.py`](mcp-servers/bridge/tools/ux_coordinator.py) | `ux_coordinator` |
| [`file_analyzer.py`](mcp-servers/bridge/tools/file_analyzer.py) | `analyze_uploaded_file`, `check_uploaded_files` |
| [`feedback.py`](mcp-servers/bridge/tools/feedback.py) | `vibezoo_feedback` |

#### Vision
- **[`minicpm.py`](mcp-servers/bridge/vision/minicpm.py)** — MiniCPM-V vision model integration for image analysis.

#### i18n
- **[`bridge/i18n/`](mcp-servers/bridge/i18n/)** — 20-language translation system initialized from `VIBEZOO_LANG` env var.

---

## 6. Build System

### 6.1 TypeScript Compilation

**Config**: [`extension/tsconfig.json`](extension/tsconfig.json:1)
- **Target**: ES2022
- **Module**: CommonJS
- **Root**: `extension/src/`
- **Output**: `extension/out/`
- **Strict mode**: Enabled
- **Source maps**: Enabled

**Scripts** (from [`extension/package.json`](extension/package.json:393)):
| Script | Command | Purpose |
|--------|---------|---------|
| `compile` | `tsc -p ./` | One-time TypeScript compilation |
| `watch` | `tsc -watch -p ./` | Incremental compilation (dev) |
| `vscode:prepublish` | `npm run compile` | Auto-compile before packaging |
| `package` | `vsce package` | Build `.vsix` file |
| `lint` | `eslint src --ext ts` | Lint TypeScript sources |
| `l10n:export` | `npx @vscode/l10n-dev export --outDir ./l10n ./src` | Export i18n strings |

### 6.2 Python MCP Server

- **No build step** — Python scripts run directly via `python` interpreter
- **Dependency installation**: Auto-installed by [`SubagentManager.installDependencies()`](extension/src/orchestra/SubagentManager.ts:338): `fastmcp`, `uvicorn`, `requests`
- **Optional deps**: `tree-sitter`, `tree-sitter-languages`, `Pillow`, `pytesseract` — installed via `vibezoo_setup` MCP tool
- **Runtime**: FastMCP with SSE transport on uvicorn ASGI server

### 6.3 VSIX Packaging

The extension packages as a single `.vsix` that bundles:
- Compiled TypeScript (`out/`)
- Python MCP servers (`mcp-servers/`) — both bridge and crow stubs
- Fabric.js media (`media/fabric.min.js`)
- Localization bundles (`l10n/`)
- Package manifest (`package.json` with all commands, views, config)

---

## 7. Port Allocation Map

| Port | Service | Direction | Protocol |
|------|---------|-----------|----------|
| 9020 | Crow Memory | Extension→Crow, Bridge→Crow | HTTP REST |
| 9022 | Scout (virtual) | Logged in TreeView | N/A (via Bridge :9027) |
| 9023 | Reviewer (virtual) | Logged in TreeView | N/A (via Bridge :9027) |
| 9024 | Tester (virtual) | Logged in TreeView | N/A (via Bridge :9027) |
| 9026 | DeepAnalyzer (virtual) | Logged in TreeView | N/A (via Bridge :9027) |
| 9027 | VibeZoo MCP Bridge | Zoo Code→Bridge | SSE (MCP) |
| 8089 | Embedding Server (optional) | Bridge→Ollama/OpenAI | HTTP |

---

## 8. Configuration Surface

All settings live under `vibezoo.*` namespace (defined in [`extension/package.json`](extension/package.json:180)):

| Setting | Default | Description |
|---------|---------|-------------|
| `crow.port` | 9020 | Crow Memory port |
| `crow.autoReconnect` | true | Auto-reconnect to Crow |
| `bridge.port` | 9027 | MCP Bridge port |
| `network.host` | 127.0.0.1 | Bind host |
| `yolo.enabled` | true | YOLO safety net |
| `yolo.rewindShortcut` | ctrl+shift+z | Rewind keybinding |
| `build.silentMode` | true | Silent build output |
| `build.autoFix` | false | Auto-fix build failures |
| `build.autoFixMaxAttempts` | 3 | Max auto-fix attempts |
| `guard.enabled` | true | Guard.git protection |
| `guard.autoEnable` | true | Auto-enable on YOLO |
| `guard.yoctoBackupEnabled` | true | .git backup to yocto |
| `guard.yoctoBackupIntervalMin` | 30 | Backup interval |
| `guard.integrityCheckIntervalMin` | 5 | Integrity check interval |
| `visual.whiteboardEnabled` | true | Whiteboard panel |
| `visual.uiPreviewEnabled` | true | UI Preview panel |
| `errorCollection.enabled` | true | Error collection |
| `errorCollection.maxEntries` | 100 | Max error entries |
| `advanced.pythonPath` | "" | Custom Python path |
| `session.autoResume` | true | Auto-resume sessions |

---

## 9. VS Code Contribution Points

### Commands (30 registered)
See [`extension/package.json`](extension/package.json:24) for the full list. Key commands:
- `vibezoo.selfCheck` — System diagnostics
- `vibezoo.verifyFoundation` — Foundation state check
- `vibezoo.instantRewind` — YOLO instant recovery
- `vibezoo.toggleYolo` — Toggle YOLO mode
- `vibezoo.toggleGuardGit` — Toggle Guard.git
- `vibezoo.openWhiteboard` — Open whiteboard Webview
- `vibezoo.openUIPreview` — Open UI Preview
- `vibezoo.openDashboard` — Open Orchestra Dashboard
- `vibezoo.openDropzone` — Open file dropzone
- `vibezoo.openErrorDashboard` — Open error dashboard

### Sidebar Views (3 TreeViews)
- `vibezoo.activeSubagents` — Active subagent nodes
- `vibezoo.yoloHistory` — YOLO session snapshots
- `vibezoo.sessionResume` — Session resume data

### Keybindings
- `Ctrl+Shift+Z` — Instant Rewind
- `Ctrl+Shift+R` — Session Resume
- `Ctrl+Shift+B` — Open Whiteboard

### Activity Bar
- `vibezoo-sidebar` — Dedicated sidebar with ⚡ icon

---

## 10. Potential Bottlenecks & Notes

1. **Bridge as Single Process**: All 19 MCP tool modules run in a single Python process on port 9027. A slow tool call (e.g., large file AST parsing) blocks other requests on the same SSE connection.

2. **File-based IPC for Visuals**: Whiteboard/UI Preview/Dropzone communication uses file watching (`fs.watchFile` at 500ms). This introduces up to 500ms latency for visual updates and is susceptible to race conditions on rapid updates.

3. **Python Dependency Bootstrap**: First startup requires `pip install` of `fastmcp`, `uvicorn`, `requests` (60s timeout). If Python is not in PATH or no venv exists, this can fail silently.

4. **Dual `mcp-servers/`**: The root-level `mcp-servers/` and `extension/mcp-servers/` contain duplicate Python code. The extension copies files to `~/mcp-servers/vibezoo/` for global `autoStartCommand` support.

5. **Crow Memory External Dependency**: The real Crow Memory server is an external project. VibeZoo only detects/spawns it; the deprecated `crow_memory_server.py` is a stub that exits immediately.

6. **Guard.git Platform Complexity**: [`GuardGitManager`](extension/src/safety/GuardGitManager.ts:28) handles Windows (icacls), Linux (chmod/chattr), and macOS (chmod) with multi-root workspace support — 669 lines of platform-specific logic.

7. **L10n Coverage**: 20 languages supported via `@vscode/l10n-dev` for the extension and custom i18n system for the Python bridge.
