# VibeZoo Architecture — v0.13.0

> **Written**: 2026-05-27 (v0.10.0 draft) → 2026-05-28 (v0.13.0 full revision)
> **Baseline Version**: v0.13.0
> **Project**: VibeZoo — Standalone Companion Extension for Zoo Code
> **Core Constraint**: Do not modify Zoo Code source code. All features are implemented via VibeZoo Extension + MCP Bridge + configuration changes.

---

## 0. Document History and Change Summary

### 0.1 Key Changes from Original (v0.10.0 Design)

| # | Item | Original Design (v0.10.0) | Current Reality (v0.12.0) |
|:---|:---|:---|:---|
| 1 | **Crow Memory** | External system spawned/managed by VibeZoo | Built-in system of Zoo Code. VibeZoo only performs `/health` detection and Crow tool integration |
| 2 | **MCP Server** | 4 Go binaries (Scout:9022, Reviewer:9023, Tester:9024, Deep:9026) | Single Python bridge [`vibezoo_mcp_bridge.py`](../mcp-servers/vibezoo_mcp_bridge.py) (port 9020) |
| 3 | **AutoBuildFix** | [`extension/src/safety/AutoBuildFix.ts`](../extension/src/safety/AutoBuildFix.ts) — empty loop (rebuild only) | [`extension/src/orchestra/FixLoopManager.ts`](../extension/src/orchestra/FixLoopManager.ts) — autonomous fix state machine + CIM + HITL |
| 4 | **Session Resume** | Webview panel | Integrated into TreeView ([`extension/src/ui/TreeViewProviders.ts`](../extension/src/ui/TreeViewProviders.ts) `SessionResumeProvider`) |
| 5 | **MCP Tool Count** | 15 | 31 (tree-sitter AST-based semantic analysis) |
| 6 | **Autonomous Fix Loop** | Design only | Implemented — `FixLoopManager` + `auto_fix_status` + `retry_build` + `check_intervention` |
| 7 | **Self-healing CIM** | Design only | Implemented — `FixLoopManager.startWatching()` (file save → tsc → auto fix) |
| 8 | **HITL Intervention** | Design only | Implemented — `pause/resume/abort` + Whiteboard·Chat intervention channels |
| 9 | **StatusBar** | 2 items (Crow connection, VibeZoo status) | 1 unified — [`extension/src/ui/StatusBarManager.ts`](../extension/src/ui/StatusBarManager.ts) (Crow·YOLO·CIM·Bridge status integrated) |
| 10 | **Whiteboard Sync** | `setInterval` 1s polling | `fs.watchFile` event-based ([`extension/src/visual/VisualVibePanels.ts`](../extension/src/visual/VisualVibePanels.ts)) |
| 11 | **TreeView** | 1 (YOLO History) | 3 (Active Subagents, YOLO History, Session Resume) |
| 12 | **VS Code Commands** | 2 | 26 (Integrated scenarios, Fix Loop control, CIM, learn/recall, etc.) |
| 13 | **SelfCheck** (v0.13.0) | Not present | [`extension/src/safety/SelfCheck.ts`](../extension/src/safety/SelfCheck.ts) — AlarmMonitor (60s window throttle) + 7 diagnostic items |
| 14 | **NotificationThrottle** (v0.13.0) | Not present | [`extension/src/ui/StatusBarManager.ts`](../extension/src/ui/StatusBarManager.ts) — 10 per minute limit + 3s dedup |
| 15 | **I_instability Guardrail** (v0.13.0) | boolean oscillation | [`extension/src/orchestra/FixLoopManager.ts`](../extension/src/orchestra/FixLoopManager.ts) — continuous value I=α·nedits+β·autocorr+γ·buildFails |
| 16 | **Virtual Subagent** (v0.13.0) | Not present | [`mcp-servers/vibezoo_mcp_bridge.py`](../mcp-servers/vibezoo_mcp_bridge.py) — `SubagentPool` + asyncio.Semaphore(5) + 5 MCP tools |
| 17 | **Intent-to-Code Bridge** (v0.13.0) | Not present | [`mcp-servers/vibezoo_mcp_bridge.py`](../mcp-servers/vibezoo_mcp_bridge.py) — whiteboard rect→class, line→dependency extraction, TypeScript stub generation |
| 18 | **Fabric.js Local Bundling** (v0.13.0) | CDN only | [`extension/media/fabric.min.js`](../extension/media/fabric.min.js) — local file + CDN fallback |
| 19 | **Atomic Backup** (v0.13.0) | fs.copyFileSync | [`extension/src/safety/YoctoManager.ts`](../extension/src/safety/YoctoManager.ts) — `atomicCopyFile()` temp file+crypto.randomUUID+rename |
| 20 | **Crow Exponential Backoff** (v0.13.0) | Simple try/except | [`mcp-servers/vibezoo_mcp_bridge.py`](../mcp-servers/vibezoo_mcp_bridge.py) — 150ms start, 2x increase, max 3 attempts, random jitter |

---

## 1. Executive Summary

### 1.1 What is VibeZoo?

VibeZoo is a VS Code Companion Extension that assists Zoo Code **without modifying its source code**. If Zoo Code is the LLM reasoning engine, VibeZoo acts as the **operating system** surrounding it:

- **Status Display**: Unified StatusBar showing Bridge·Crow·YOLO·CIM status at a glance
- **Safety Net**: yocto real-time backup, `.yoloignore` File Guard, automated Git Stash
- **Autonomous Fix**: Build failure → LLM analysis → code fix → rebuild (max 3 attempts, oscillation detection)
- **Continuous Monitoring**: CIM (Continuous Improvement Mode) — automatic tsc check on file save
- **MCP Tools**: 31 tools (tree-sitter AST-based code search·review·analysis·reverse engineering·PR review·refactoring·preference learning)
- **Visual Collaboration**: Whiteboard, UI Preview, Diagram Engine
- **Memory Integration**: Crow Memory (Zoo Code built-in) + Crow tools for learning error patterns, project knowledge, coding preferences

### 1.2 Core Philosophy

```
Vibe = f(Usefulness, Predictability, Control_perceived)
```

- **"VS Code Lock-In"**: Never leaves VS Code.
- **"Controllable Automation"**: Human-in-the-Loop — users can intervene even during automated fixes.
- **"Zero Zoo Code Source Modification"**: No forking of Zoo Code. All features are implemented with VibeZoo Extension + MCP Bridge + Config only.
- **"Crow is Zoo Code's, VibeZoo only Detects"**: Crow Memory is Zoo Code's built-in system. VibeZoo only performs connection status detection and Crow tool integration.

---

## 2. Actual Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                        VS Code Window                              │
│                                                                   │
│  ┌────────────────────────┐    ┌──────────────────────────────┐  │
│  │     Zoo Code (LLM)     │    │  VibeZoo Extension            │  │
│  │                        │    │                               │  │
│  │  • LLM Reasoning Engine│    │  • StatusBarManager (unified)│  │
│  │  • Crow Memory built-in│    │  • TreeView 3 types          │  │
│  │    (localhost:9020)    │    │    - Active Subagents        │  │
│  │  • MCP Client          │    │    - YOLO History            │  │
│  │                        │    │    - Session Resume          │  │
│  │  ◄── MCP/SSE ──────────┼────┤  • FixLoopManager (auto)     │  │
│  │      tool call         │    │    - State machine (8 states)│  │
│  │                        │    │    - oscillation detection   │  │
│  │                        │    │    - CIM (continuous monitor)│  │
│  │                        │    │  • VisualVibePanels          │  │
│  │                        │    │    - Whiteboard (fs.watch)   │  │
│  │                        │    │    - UI Preview              │  │
│  │                        │    │  • YoctoManager (yocto backup│  │
│  │                        │    │  • FileGuard (.yoloignore)   │  │
│  │                        │    │  • GitStashManager           │  │
│  │                        │    │  • SubagentManager           │  │
│  │                        │    │  • CrowServerManager (detect)│  │
│  │                        │    │  • ContextIntelligence       │  │
│  └───────────┬────────────┘    └──────────────┬───────────────┘  │
│              │                                │                   │
└──────────────┼────────────────────────────────┼───────────────────┘
               │ MCP/SSE                        │ child_process.spawn
               ▼                                ▼
┌──────────────────────────┐    ┌──────────────────────────────────┐
│ Zoo Code Crow Memory     │    │ VibeZoo MCP Bridge               │
│ (Zoo Code built-in)      │    │ vibezoo_mcp_bridge.py            │
│ localhost:9020           │    │ localhost:9020/sse               │
│                          │    │                                  │
│ • crow_recall            │    │ • 31 MCP tools                  │
│ • crow_ingest            │    │ • tree-sitter AST parsing        │
│ • crow_compact           │    │ • Crow Memory integration        │
│ • crow_evolve_propose    │    │   (crow_recall/ingest wrappers)  │
│ • crow_diagnostics       │    │ • /health endpoint              │
│ • crow_manage_backup     │    │ • ~/.vibezoo-fix-request.json   │
│ • crow_manage_prompt     │    │ • ~/.vibezoo-whiteboard.json    │
│ • crow_get_user_bias     │    │ • ~/.vibezoo-preferences.json   │
│ • crow_check_drift       │    │                                  │
│ • crow_project_info       │    │ FastMCP + SSE transport          │
└──────────────────────────┘    └──────────────────────────────────┘
```

### 2.1 Port Allocation

| Port | System | Role | Owner |
|:---|:---|:---|:---|
| **9020** | Crow Memory | Knowledge store·recall·compact·diagnostics | Zoo Code (built-in) |
| **9027** | VibeZoo MCP Bridge | Code search·review·analysis·visualization·Fix Loop | VibeZoo Extension (`SubagentManager.spawnBridge()`) |

**Important**: Crow Memory (9020) is managed directly by Zoo Code. VibeZoo does not spawn the Crow server; [`CrowServerManager`](../extension/src/crow/CrowServerManager.ts) only performs `/health` checks and connection status monitoring.

---

## 3. File Structure (Actual)

```
VibeZoo_forZoocode/
├── extension/                        # VibeZoo VS Code Extension (TypeScript)
│   ├── package.json                  # v0.12.0, 26 commands, 3 TreeViews, 18 settings
│   ├── tsconfig.json
│   ├── .vscodeignore
│   └── src/
│       ├── extension.ts              # Entry point — activate(): 26 commands, Bridge spawn, module init
│       ├── context/
│       │   └── ContextIntelligence.ts # ContextIndicator, ExplainLessSuggestor, SessionResume, EmotionalDetector
│       ├── crow/
│       │   └── CrowServerManager.ts  # Zoo Code Crow detection only (health check, status notification)
│       ├── flow/
│       │   ├── BuildFeedback.ts      # Build end detection → FixLoopManager integration
│       │   ├── BuildTaskProvider.ts  # Silent Build Task registration
│       │   ├── ProjectDetector.ts    # Project type detection → mode suggestion
│       │   └── ProjectTreeScanner.ts # Project tree scan + caching
│       ├── orchestra/
│       │   ├── FixLoopManager.ts     # Autonomous fix loop (8-state machine) + CIM (file watch)
│       │   ├── MentionRouter.ts      # @mention routing
│       │   └── SubagentManager.ts    # Python MCP Bridge spawn·management
│       ├── safety/
│       │   ├── FileGuard.ts          # .yoloignore-based protected file watch·restore
│       │   ├── GitStashManager.ts    # YOLO entry/exit Git Stash automation
│       │   └── YoctoManager.ts       # yocto real-time backup·restore (FileSystemWatcher)
│       ├── types/
│       │   └── index.ts              # Common types (Diagnostic, SessionSummary, SubagentNode, etc.)
│       ├── ui/
│       │   ├── StatusBarManager.ts   # Unified StatusBar (Bridge·Crow·YOLO·CIM·mode suggestion)
│       │   └── TreeViewProviders.ts  # 3 Providers (ActiveSubagents, YOLO History, Session Resume)
│       └── visual/
│           └── VisualVibePanels.ts   # Whiteboard (fs.watchFile) + UI Preview + Diagram panels
│
├── mcp-servers/
│   └── vibezoo_mcp_bridge.py         # Single file, 31 MCP tools, FastMCP + SSE, port 9020
│
├── fromscratch/                      # Design documents
│   ├── Architecture.md               # ← This document
│   ├── PLAN.md                       # Implementation plan
│   ├── ROADMAP.md                    # Performance/utilization maximization roadmap
│   ├── JOURNAL.md                    # Development journal
│   ├── reportfromgemini.md           # Initial analysis report
│   └── zoo_code_upgrade.agent.final.md
│
├── plans/
│   └── autonomous-fix-loop.md        # FixLoopManager detailed design
│
└── templates/
    ├── yoloignore                    # .yoloignore template
    ├── zoo-config.json               # .zoo/config.json template
    └── vscode-settings.json          # .vscode/settings.json template
```

---

## 4. Core Component Details

### 4.1 [`extension.ts`](../extension/src/extension.ts) — Entry Point

The `activate()` function initializes in the following order:

```
1. Prevent duplicate activation
2. Auto-create directories and templates
3. CrowServerManager (Crow detection) + StatusBarManager
4. Crow connection check (independent early execution before Bridge start)
5. Flow Keepers: BuildTaskProvider, BuildFeedback, ProjectDetector, ProjectTreeScanner
6. Safety Net: YoctoManager, FileGuard, FixLoopManager, GitStashManager
7. Context Intelligence: ContextIndicator, ExplainLessSuggestor, SessionResume, EmotionalDetector
8. MCP Bridge spawn (SubagentManager.spawnBridge())
9. TreeView Providers: ActiveSubagents, YOLO History, Session Resume
10. Orchestra: MentionRouter
11. Visual Vibe: VisualVibePanels.activate()
12. Register 26 VS Code commands
```

**26 Registered Commands**:

| Category | Command |
|:---|:---|
| **Foundation** | `verifyFoundation`, `reconnectCrow` |
| **YOLO** | `instantRewind`, `toggleYolo` |
| **Scan** | `scanProject` |
| **Visual** | `openWhiteboard`, `openUIPreview`, `openDashboard` |
| **Session** | `showSessionResume`, `showHelp` |
| **Integrated Scenarios (Q1)** | `reviewProject`, `findBugs`, `suggestRefactor`, `generateDocs` |
| **Fix Loop Control** | `_autoBuildFix`, `_buildSuccess`, `pauseFixLoop`, `resumeFixLoop`, `abortFixLoop` |
| **CIM (M3)** | `startWatching`, `stopWatching` |
| **Analysis (M3-A/B/C)** | `explainCode`, `analyzeChanges`, `reviewPR`, `refactorAcrossFiles` |
| **Learn·Recall (M3-D/E)** | `learnProject`, `recallProject`, `learnPreference`, `getPreferences` |
| **Agent** | `showAgentInfo` |

### 4.2 [`FixLoopManager`](../extension/src/orchestra/FixLoopManager.ts) — Autonomous Fix Loop

**State Machine (8 states)**:

```
idle → pending → in_progress → building → resolved
                    │                │
                    │                ├── fail → pending (retry, max 3)
                    │                └── oscillation/max → abandoned
                    │
                    └── user intervention → awaiting_user → user_override → in_progress
```

**Core Functions**:

| Feature | Method | Description |
|:---|:---|:---|
| Build failure detection | `onBuildFailure()` | BuildFeedback → FixLoopManager, records fix request JSON |
| Start LLM analysis | `markInProgress()` | Changes state when `auto_fix_status()` MCP tool is called |
| Execute build | `markBuilding()` | Changes state before `retry_build()` MCP tool call |
| Build success | `markResolved()` | Success notification + fix request file cleanup |
| Build re-failure | `markBuildFailed()` | Oscillation check then retry or abandon |
| Oscillation detection | `isOscillating()` | A→B→A pattern, detects same error 2 consecutive times |
| Timeout | `resetSessionTimeout()` | Abandoned if unresolved within 120s |
| HITL | `pause()` / `resume()` / `abort()` | User intervention commands |

**CIM (Continuous Improvement Mode)**:

When `startWatching()` is called at [`extension/src/orchestra/FixLoopManager.ts`](../extension/src/orchestra/FixLoopManager.ts:421):
- TS/JS file save (`onDidSaveTextDocument`) → `npx tsc --noEmit` auto-execution
- tsc error occurs → `onBuildFailure()` → Auto-Fix trigger
- StatusBar shows `$(eye) VibeZoo: Watching`

### 4.3 [`vibezoo_mcp_bridge.py`](../mcp-servers/vibezoo_mcp_bridge.py) — MCP Bridge

**31 MCP Tools** (FastMCP + tree-sitter AST):

| Category | Tool | AST Usage |
|:---|:---|:---|
| **Scout** | `search_codebase`, `find_references`, `summarize_architecture` | tree-sitter function·class·interface search |
| **Reviewer** | `review_code`, `check_quality` | ESLint integration |
| **Tester** | `generate_tests`, `analyze_coverage` | — |
| **Deep Analyzer** | `analyze_call_graph`, `map_dependencies`, `extract_patterns`, `reverse_engineer` | AST call graph·import·field extraction |
| **Whiteboard** | `draw_on_whiteboard`, `get_whiteboard_state`, `open_whiteboard`, `capture_screen` | — |
| **UI Preview** | `open_ui_preview` | — |
| **Fix Loop (M1-A)** | `auto_fix_status`, `retry_build`, `check_intervention` | — |
| **Integrated Scenarios (Q1)** | `review_project`, `find_bugs`, `suggest_refactor`, `generate_docs` | Chain calls |
| **Explain (M3-A)** | `explain_code` | AST context (function·class·interface) |
| **Git Analysis (M3-B)** | `analyze_changes`, `review_pr` | — |
| **Refactoring (M3-C)** | `refactor_across_files` | — |
| **Knowledge (M3-D)** | `learn_project`, `recall_project` | Crow arch·style·life_context integration |
| **Preferences (M3-E)** | `learn_preference`, `get_preferences` | Crow life_context integration |

**Crow Integration**: `try_crow_ingest()` / `try_crow_recall()` wrappers enable optional integration with Crow Memory (9020) from all tools. Tool operation is unaffected even if Crow connection fails.

**tree-sitter AST Parser**: For TypeScript/JavaScript files, uses [`_parse_with_tree_sitter()`](../mcp-servers/vibezoo_mcp_bridge.py:108), [`_extract_ast_calls()`](../mcp-servers/vibezoo_mcp_bridge.py:164), [`_extract_ast_imports()`](../mcp-servers/vibezoo_mcp_bridge.py:200), [`_extract_ast_fields()`](../mcp-servers/vibezoo_mcp_bridge.py:257) functions for precise structural analysis. Falls back to regex when tree-sitter is not installed.

### 4.4 [`StatusBarManager`](../extension/src/ui/StatusBarManager.ts) — Unified Status Display

All status information integrated into a single StatusBar item `$(zap) VibeZoo`:

| State | Display | Description |
|:---|:---|:---|
| **Default** | `$(zap) VibeZoo` | Bridge connected |
| **CIM Active** | `$(eye) VibeZoo CIM` | File watch in progress |
| **YOLO Active** | `$(flame) VibeZoo YOLO` | YOLO mode ON |
| **Mode Suggestion** | `$(gear) Recommended: {mode}` | Project detection based (restores after 5s) |
| **In Progress** | `$(sync~spin) {message}` | MCP tool executing |

**Tooltip Integration**: Bridge status + Crow connection + CIM + YOLO status dynamically composed via `_composeTooltip()`. Prevents tooltip conflicts between `setActive()` and `setCrowStatus()`.

### 4.5 [`TreeViewProviders`](../extension/src/ui/TreeViewProviders.ts) — 3 TreeViews

| TreeView | Provider | Content |
|:---|:---|:---|
| **Active Subagents** | `ActiveSubagentsProvider` | Bridge·Scout·Reviewer·Tester·DeepAnalyzer·CIM Monitor nodes (30s health check) |
| **YOLO History** | `YoloHistoryProvider` | `~/.zoo-code/yocto/` directory-based session list, right-click → Rewind |
| **Session Resume** | `SessionResumeProvider` | 3-tier fallback: Crow recall + local file + yocto folder scan. Shows session summary·key decisions·modified files·incomplete tasks |

### 4.6 [`VisualVibePanels`](../extension/src/visual/VisualVibePanels.ts) — Visual Collaboration

| Panel | Sync Method | Description |
|:---|:---|:---|
| **Whiteboard** | `fs.watchFile` (200ms) | AI → Bridge → `~/.vibezoo-whiteboard.json` → file change detection → auto render |
| **UI Preview** | `fs.watchFile` | AI → Bridge → `~/.vibezoo-ui-action.json` → auto open + render |
| **Diagram** | Manual open | Mermaid.js / D3.js Webview |

### 4.7 Safety Net — 3-Layer Protection

```
LAYER 1: Prevention (Config-based)
├── .yoloignore file → FileGuard watches
└── Zoo Code MCP tool permission settings

LAYER 2: Real-time Detection & Recovery (VibeZoo)
├── YoctoManager: FileSystemWatcher + fs.copyFileSync (200ms debounce)
├── FileGuard: .yoloignore matching file change → immediate yocto restore
└── GitStashManager: YOLO entry/exit git stash automation

LAYER 3: Post-hoc Recovery & Auto-Healing
├── instantRewind(): yocto backup → full restore (<500ms)
├── FixLoopManager: build failure → LLM fix → rebuild (max 3)
└── CIM: file save → tsc auto check → error triggers Auto-Fix
```

### 4.8 Crow Memory Integration Architecture

```
Zoo Code (Crow Memory built-in, :9020)
    │
    ├── Zoo Code LLM → crow_recall / crow_ingest direct calls
    │
    └── VibeZoo MCP Bridge (:9020)
        ├── try_crow_ingest() → Crow /ingest
        ├── try_crow_recall() → Crow /recall
        └── Crow connection failure → ignored (tool works normally)
```

**Core Principle**: Crow Memory is Zoo Code's built-in system. VibeZoo does not spawn Crow; it only optionally integrates via the `try_crow_ingest()` / `try_crow_recall()` wrappers in the MCP Bridge. All VibeZoo features work normally even if Crow connection fails.

---

## 5. Data Flow

### 5.1 Autonomous Fix Loop

```
File save → BuildFeedback → FixLoopManager.onBuildFailure()
    │
    ├── ~/.vibezoo-fix-request.json recorded
    ├── StatusBar: "$(warning) Build Failed — [Auto Fix]"
    │
    ▼
LLM (Zoo Code):
    auto_fix_status() → receive error info + Crow past patterns
    search_codebase()  → search related code
    review_code()      → analyze problem files
    File edit
    retry_build()      → check build result
    │
    ├── success → FixLoopManager.markResolved()
    └── failure → oscillation check → retry or abandoned
```

### 5.2 Whiteboard Collaboration

```
AI (Zoo Code):
    draw_on_whiteboard(commands) → Bridge(:9020) → ~/.vibezoo-whiteboard.json
                                                          │
VibeZoo Extension:                                       │
    VisualVibePanels._startWatching()                    │
    → fs.watchFile (200ms)                               │
    → JSON change detection                              │
    → postMessage to Whiteboard Webview                   │
    → Render on Fabric.js canvas                          │
                                                          │
User:                                                   │
    Modify drawings/text on whiteboard                   │
    → get_whiteboard_state() ← AI checks                 │
    → check_intervention() ← Fix Loop checks              │
```

### 5.3 MCP Bridge ↔ Zoo Code Integration

```
1. VibeZoo Extension.activate()
2. SubagentManager.spawnBridge()
   → child_process.spawn("python", ["vibezoo_mcp_bridge.py", "--port", "9027"])
3. Bridge health check → OK
4. autoConfigureMCP()
   → Add {"vibezoo": {"url": "http://localhost:9020/sse"}} to .roo/mcp.json
5. Zoo Code restart loads MCP config → VibeZoo Bridge connects
6. LLM → MCP tool call → Bridge → Python tool execution → return result
```

---

## 6. Full MCP Tool List (31)

| # | Tool Name | Category | AST | Description |
|:---:|:---|:---|:---:|:---|
| 1 | `search_codebase` | Scout | ✅ | tree-sitter AST based structure search + regex fallback |
| 2 | `find_references` | Scout | — | Symbol reference search |
| 3 | `summarize_architecture` | Scout | — | Project structure·tech stack·file statistics |
| 4 | `review_code` | Reviewer | — | Line length·TODO·console.log detection |
| 5 | `check_quality` | Reviewer | — | ESLint·go vet integration |
| 6 | `analyze_call_graph` | DeepAnalyzer | ✅ | AST call_expression based call graph |
| 7 | `map_dependencies` | DeepAnalyzer | ✅ | AST import extraction + Tarjan circular ref detection |
| 8 | `extract_patterns` | DeepAnalyzer | — | async/try-catch/arrow pattern counting |
| 9 | `reverse_engineer` | DeepAnalyzer | ✅ | AST field extraction → Mermaid ERD·OpenAPI generation |
| 10 | `generate_tests` | Tester | — | Function detection → test template generation |
| 11 | `analyze_coverage` | Tester | — | vitest coverage execution |
| 12 | `draw_on_whiteboard` | Whiteboard | — | Fabric.js drawing command transmission |
| 13 | `get_whiteboard_state` | Whiteboard | — | Query user modifications |
| 14 | `open_whiteboard` | Whiteboard | — | Open whiteboard panel |
| 15 | `capture_screen` | Whiteboard | — | Screen capture → whiteboard |
| 16 | `open_ui_preview` | UI Preview | — | React/Vue real-time preview |
| 17 | `auto_fix_status` | Fix Loop | — | Fix request query + Crow past patterns |
| 18 | `retry_build` | Fix Loop | — | Build re-execution + result recording |
| 19 | `check_intervention` | Fix Loop | — | Whiteboard·Chat intervention check |
| 20 | `review_project` | Integrated (Q1) | — | search + review + quality + patterns |
| 21 | `find_bugs` | Integrated (Q1) | — | patterns + suspicious search + Crow recall |
| 22 | `suggest_refactor` | Integrated (Q1) | — | deps + patterns + callgraph |
| 23 | `generate_docs` | Integrated (Q1) | — | arch + reverse + whiteboard diagram |
| 24 | `explain_code` | Analysis (M3-A) | ✅ | AST context based code explanation |
| 25 | `analyze_changes` | Analysis (M3-B) | — | git diff analysis + Crow context |
| 26 | `review_pr` | Analysis (M3-B) | — | diff + review_code integrated PR review |
| 27 | `refactor_across_files` | Analysis (M3-C) | — | Pattern search → change proposal |
| 28 | `learn_project` | Knowledge (M3-D) | — | arch+patterns+deps → Crow accumulation |
| 29 | `recall_project` | Knowledge (M3-D) | — | Recall project knowledge from Crow |
| 30 | `learn_preference` | Preferences (M3-E) | — | Save user coding preferences |
| 31 | `get_preferences` | Preferences (M3-E) | — | Retrieve saved preferences |

---

## 7. Tech Stack

| Component | Technology | Description |
|:---|:---|:---|
| **Extension** | TypeScript 5.x | VS Code Extension API |
| **MCP Bridge** | Python 3.x + FastMCP | SSE transport, port 9020 |
| **AST Parsing** | tree-sitter + tree-sitter-typescript | TS/JS structure analysis (regex fallback when not installed) |
| **Communication** | MCP/SSE (JSON-RPC 2.0) | Zoo Code ↔ Bridge |
| **Whiteboard** | Fabric.js | HTML5 Canvas drawing |
| **UI Preview** | iframe sandbox + Babel standalone | React/Vue real-time rendering |
| **Diagram** | Mermaid.js + D3.js | ERD, call graph, dependency map |
| **Crow Memory** | Zoo Code built-in | Python FastMCP, port 9020 |

---

## 8. Design Constraints and Workarounds

| Constraint | Cause | Workaround | Loss |
|:---|:---|:---|:---|
| Cannot intercept LLM message pipeline | Internal communication limitation between extensions | `[Config]` custom_modes.yaml + `[Crow]` tool call + StatusBar context notification | ~10% |
| Cannot auto-switch custom modes | Zoo Code mode state cannot be changed externally | StatusBar "Recommended Mode" suggestion (1-click) | 3-click→1-click |
| Cannot pre-block file writes | WorkspaceEdit cannot be intercepted | FileSystemWatcher post-detection + yocto immediate restore (0.3s) | Prevention→Treatment |
| Cannot @mention in Zoo Code chat | Chat UI cannot be extended externally | VS Code Chat Participant API + MCP tool call based routing | Chat integration→Separate channel |

---

## 9. Key Performance Metrics

| Metric | Target | Current (v0.12.0) |
|:---|:---:|:---:|
| Extension activation time | < 500ms | Lazy Init + fs.watchFile applied |
| yocto single file restore | < 100ms | fs.copyFileSync |
| yocto 10 file restore | < 500ms | Sequential copy |
| Protected file change detection→restore | < 500ms | FileSystemWatcher + yocto |
| Fix Loop timeout | 120s | FixLoopManager.SESSION_TIMEOUT_MS |
| CIM tsc check | < 60s | npx tsc --noEmit |
| Whiteboard sync | 200ms debounce | fs.watchFile |
| Active Subagents health check | 30s interval | setInterval + /health |

---

## 10. Conclusion

VibeZoo v0.12.0 achieved the following **without modifying a single line of Zoo Code source code**:

- **31 MCP Tools**: tree-sitter AST based semantic code analysis
- **Autonomous Fix Loop**: Build failure → LLM analysis → fix → rebuild (oscillation detection + HITL)
- **Continuous Improvement Mode (CIM)**: File save → auto tsc check → Auto-Fix
- **Integrated Safety Net**: yocto backup + File Guard + Git Stash + Instant Rewind
- **3 TreeViews**: Active Subagents, YOLO History, Session Resume (Crow·local·yocto triple fallback)
- **Unified StatusBar**: Bridge·Crow·YOLO·CIM status displayed in a single item
- **Visual Collaboration**: Whiteboard (fs.watchFile), UI Preview

**Core Principles**:
1. Zero Zoo Code source modification — all features implemented via VibeZoo Extension + MCP Bridge + Config
2. Crow is Zoo Code's built-in system — VibeZoo only detects and integrates; all features work without Crow
3. Human-in-the-Loop — automation within user-controllable boundaries
4. tree-sitter AST first, regex fallback on failure — ensures Windows environment compatibility
