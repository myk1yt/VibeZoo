# VibeZoo v0.13.0

> **AI Companion Extension for Zoo Code.** 0% Source Modification. 100% Companion-First.

<p align="center">
  <img src="https://img.shields.io/badge/version-0.13.0-blue" alt="version">
  <img src="https://img.shields.io/badge/MCP_tools-31-green" alt="mcp tools">
  <img src="https://img.shields.io/badge/TypeScript-16_files-orange" alt="typescript">
  <img src="https://img.shields.io/badge/Python-FastMCP-yellow" alt="python">
  <img src="https://img.shields.io/badge/tree--sitter-AST-purple" alt="tree-sitter">
  <img src="https://img.shields.io/badge/tested-96%25_pass-brightgreen" alt="tested">
</p>

---

## 🎯 Philosophy

**"Vibe = f(Usefulness, Predictability, Control_perceived)"**

VibeZoo does not fork Zoo Code — it assists from the side as a **Companion Extension**. Without modifying a single line of Zoo Code's source code, it maximizes the vibecoding experience using only the VS Code Extension API + MCP Protocol + Crow Memory.

### Core Principles
| Principle | Description |
|:---|:---|
| **Companion-First** | Operates alongside Zoo Code. No fork/patch. |
| **Controllable Automation** | Semi-autonomous with human intervention (HITL) |
| **VS Code Lock-In** | Never leaves VS Code. All UI is built into VS Code. |
| **Tools are Algorithms, Intelligence is the LLM** | MCP tools are pure Python functions. Reasoning/judgment is handled by Zoo Code's LLM. |

### Relationship with Crow Memory
VibeZoo unlocks its **true power when used with Crow Memory**:

- **Without Crow**: 31 MCP tools perform static analysis/searches
- **With Crow**: Learns error patterns, accumulates project knowledge, remembers coding style, cross-session context — **a self-evolving toolset**

VibeZoo does not run Crow Memory — it **auto-detects** and leverages Zoo Code's built-in Crow.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      VS Code Window (Singleton Bridge)   │
│  ┌──────────────────┐  ┌──────────────────────────────┐ │
│  │    Zoo Code       │  │   VibeZoo Extension (local)  │ │
│  │    (LLM + Crow)   │  │   ────────────────────────   │ │
│  │                   │  │   • StatusBar (1 unified)    │ │
│  │   deepseek-v4     │  │   • TreeView (3 panels)      │ │
│  │   or other LLM    │  │   • FixLoopManager (auto fix)│ │
│  │                   │  │   • VisualVibePanels (canvas)│ │
│  │   Crow Memory     │  │   • YoctoManager (backup/restore)│ │
│  │   (built-in, compatible)│   • FileGuard + GitStash  │ │
│  └────────┬─────────┘  └────────────┬─────────────────┘ │
│           │ MCP/SSE (:9027)         │ detect/spawn (single)│
└───────────┼─────────────────────────┼───────────────────┘
            │                         │
            ▼                         ▼
┌──────────────────────────────────────────────────────┐
│  VibeZoo Unified MCP Bridge (:9027) — Singleton      │
│  vibezoo_mcp_bridge.py                               │
│  ┌────────────────────────────────────────────────┐  │
│  │  10 Crow Memory Tools  │  31 VibeZoo Tools    │  │
│  │  • crow_recall          │  • search_codebase   │  │
│  │  • crow_ingest          │  • review_code       │  │
│  │  • crow_diagnostics     │  • map_dependencies  │  │
│  │  • ... (7 more)         │  • ... (28 more)     │  │
│  └────────────────────────────────────────────────┘  │
│  Storage: ~/.vibezoo-crow-memory/ (JSON files)       │
└──────────────────────────────────────────────────────┘
```

### Port Allocation
| Port | Service | Owner |
|:---|:---|:---|
| 9027 | VibeZoo Unified MCP Bridge (Crow Memory + VibeZoo) | VibeZoo Extension (Python spawn, singleton) |

### Data Flow
```
User chat → Zoo Code LLM → MCP tool call → VibeZoo Unified Bridge (:9027)
                                                     │
                           ┌─────────────────────────┤
                           ▼                         ▼
                     Static analysis tools       File system
                     (tree-sitter AST,          (~/.vibezoo-*.json,
                      regex, subprocess)        ~/.vibezoo-crow-memory/)
                           │                         │
                           ▼                         ▼
                     Crow Memory Store          VibeZoo Extension
                     (~/.vibezoo-crow-memory/   (file watch → Webview rendering)
                      JSON-based file storage)
```

---

## 🚀 Features

### 🧠 31 MCP Tools — AI's Hands and Eyes

All tools are **pure Python algorithms**. They operate via file I/O + tree-sitter AST + regex + subprocess, not LLM API calls.

| Category | Tool | Operation Principle |
|:---|:---|:---|
| **Scout** | `search_codebase`, `find_references`, `summarize_architecture` | AST-based function/class/interface search + glob file scan |
| **Reviewer** | `review_code`, `check_quality` | AST structure analysis + ESLint integration + 12 anti-pattern detection |
| **Tester** | `generate_tests`, `analyze_coverage` | AST function name extraction → test template generation |
| **Deep Analyzer** | `analyze_call_graph`, `map_dependencies`, `extract_patterns`, `reverse_engineer` | AST call graph + import DFS circular ref detection + data model field extraction |
| **Whiteboard** | `draw_on_whiteboard`, `get_whiteboard_state`, `open_whiteboard`, `capture_screen` | Fabric.js JSON generation → file watch → Webview rendering |
| **UI Preview** | `open_ui_preview` | Real-time HTML/CSS/JS rendering via iframe srcdoc |
| **Fix Loop** | `auto_fix_status`, `retry_build`, `check_intervention` | File-based LLM communication + tsc execution + Whiteboard/Chat HITL intervention |
| **Integrated Scenarios** | `review_project`, `find_bugs`, `suggest_refactor`, `generate_docs` | Existing tool chain calls + result integration |
| **Explain** | `explain_code` | AST-based enclosing function/class/interface context analysis |
| **Git Analysis** | `analyze_changes`, `review_pr` | `git diff` execution + Crow context lookup per changed file |
| **Refactoring** | `refactor_across_files` | `search_codebase` pattern search → per-file diff-style proposal |
| **Knowledge** | `learn_project`, `recall_project` | Project structure/patterns/dependencies → Crow arch·style register store/recall |
| **Preferences** | `learn_preference`, `get_preferences` | Dual storage: local JSON + Crow life_context |

### 🔄 Autonomous Fix Loop
- Auto-detect build failure → error analysis → Crow past pattern lookup → LLM fix request → rebuild
- 8-state state machine (idle → pending → in_progress → building → resolved/abandoned)
- Oscillation detection (A→B→A pattern), max 3 attempts, 120s timeout
- **HITL (Human-in-the-Loop)**: Whiteboard + Chat intervention (pause/resume/abort)

### 🖌️ Visual Vibe
- **Whiteboard**: Fabric.js canvas. AI generates shapes/text/images, users add annotations
- **UI Preview**: React/Vue/HTML real-time rendering
- **Diagram**: Mermaid.js + D3.js architecture/ERD diagrams

### 🛡️ Fearless YOLO (Safety Net)
- **Yocto**: Real-time file backup (200ms debounce)
- **Instant Rewind**: `Ctrl+Shift+Z` → full restore within 0.3s (with confirmation dialog)
- **File Guard**: Auto-restore `.yoloignore` protected files (sidebar ON/OFF toggle)
- **Git Stash**: Automated YOLO mode entry/exit

### 📊 StatusBar + TreeView
- 1 unified StatusBar (VibeZoo + Crow status + CIM/YOLO mode)
- 3 TreeViews: Active Subagents, YOLO History, Session Resume

---

## 🔧 Tech Stack

| Layer | Technology | Description |
|:---|:---|:---|
| **Extension** | TypeScript, VS Code Extension API | StatusBar, TreeView, Webview, FileSystemWatcher, Task Provider |
| **MCP Bridge** | Python, FastMCP, SSE | 31 tools, single file (`vibezoo_mcp_bridge.py`), port 9027 |
| **AST** | tree-sitter | TypeScript/JavaScript AST parsing (functions, classes, interfaces, call relations) |
| **Whiteboard** | Fabric.js 5.3 | Canvas-based drawing, file watch (`fs.watchFile`) |
| **Diagram** | Mermaid.js 10, D3.js | Architecture/ERD/call graph visualization |
| **Memory** | Crow Memory (Zoo Code built-in) | Error patterns, style rules, project knowledge, user preferences |

---

## 📦 Installation

### Prerequisites
- VS Code 1.85+
- Zoo Code Extension
- Python 3.10+ (for MCP Bridge)
- Node.js 18+ (for Extension compilation)

### 1. Install Extension
```bash
cd extension
npm install
npx tsc --noEmit
npx vsce package
code --install-extension vibezoo-0.13.0.vsix --force
```

### 2. Python Dependencies
```bash
pip install fastmcp uvicorn requests tree-sitter
```

### 3. Restart VS Code
`Ctrl+Shift+P` → `Developer: Reload Window`

VibeZoo will automatically:
1. Spawn the Python MCP Bridge (port 9027, singleton — first window only, subsequent windows share)
2. The Bridge provides 10 Crow Memory tools + 31 VibeZoo tools together
3. Auto-register the VibeZoo unified MCP server in `.roo/mcp.json`

### 4. Verify
`Ctrl+Shift+P` → `VibeZoo: Verify Foundation`

---

## 📁 Project Structure

```
VibeZoo/
├── extension/                    # VS Code Extension (TypeScript)
│   └── src/
│       ├── extension.ts          # Entry point (26 commands)
│       ├── context/              # ContextIntelligence (Session Resume, etc.)
│       ├── crow/                 # CrowServerManager (detection only)
│       ├── flow/                 # BuildFeedback, BuildTaskProvider, ProjectDetector, ProjectTreeScanner
│       ├── orchestra/            # FixLoopManager, SubagentManager, MentionRouter
│       ├── safety/               # YoctoManager, FileGuard, GitStashManager
│       ├── types/                # Type definitions
│       ├── ui/                   # StatusBarManager, TreeViewProviders
│       └── visual/               # VisualVibePanels (Whiteboard, UI Preview, Diagram)
├── mcp-servers/
│   └── vibezoo_mcp_bridge.py     # 31 MCP tools (Python FastMCP)
├── fromscratch/                  # Design documents
│   ├── Architecture.md           # Architecture details
│   ├── PLAN.md                   # Implementation plan
│   └── ROADMAP.md                # Roadmap
├── plans/                        # Feature designs
│   └── autonomous-fix-loop.md    # Autonomous fix loop design
└── templates/                    # Configuration templates
```

---

## 🗺️ Roadmap

| Milestone | Period | Description | Status |
|:---|:---|:---|:---|
| **M0** | Complete | Quick Wins: unified commands, fs.watchFile, StatusBar unification, Lazy Init | ✅ |
| **M1** | Complete | Autonomous Fix Loop + AST Scout + Crow learning | ✅ |
| **M3** | Complete | DeepAnalyzer AST + Self-healing CIM + Whiteboard enhancement | ✅ |
| **M6** | Planned | Self-evolving: full autonomy, multi-file refactoring, cross-session context | 📅 |

---

## 🤝 Contributing

VibeZoo is a personal project. Please use GitHub Issues for bug reports or feature suggestions.

## 📄 License

MIT License
