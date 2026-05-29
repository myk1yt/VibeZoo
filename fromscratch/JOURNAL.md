# VibeZoo Development Journal

> Click `Table of Contents` in the upper right → navigate to desired date
> New changes are added at the **top**

---

- [2026-05-29 - v0.13.0: Bridge stability audit — critical issues found](#2026-05-29---v0130-bridge-stability-audit--critical-issues-found)
- [2026-05-29 - v0.13.0: Performance optimization + bug fixes + documentation](#2026-05-29---v0130-performance-optimization--bug-fixes--documentation)
- [2026-05-28 - v0.13.0: Phase 1~6 Full Implementation](#2026-05-28-v0130-phase-16-full-implementation)
- [2026-05-27 - v0.10.0 Final: Go file cleanup, SSE path fix](#2026-05-27-v0100-final-go-file-cleanup-sse-path-fix)
- [2026-05-27 - v0.10.0: MCP auto-config fix, Whiteboard auto-integration](#2026-05-27-v0100-mcp-auto-config-fix-whiteboard-auto-integration)
- [2026-05-27 - v0.10.0: AI auto Whiteboard + UI Preview integration](#2026-05-27-v0100-ai-auto-whiteboard--ui-preview-integration)
- [2026-05-27 - v0.10.0: Python MCP bridge migration + Go removal](#2026-05-27-v0100-python-mcp-bridge-migration--go-removal)
- [2026-05-27 - v0.10.0: Initial implementation complete (26 files)](#2026-05-27-v0100-initial-implementation-complete-26-files)
- [2026-05-27 - Architecture design started](#2026-05-27-architecture-design-started)

---

## 2026-05-27 - v0.10.0 Final: Go file cleanup, SSE path fix

**Changes**:
- All 6 Go MCP server files deleted (`mcp-servers/cmd/`, `go.mod`, `build.ps1`) — 1,074 lines removed
- `.roo/mcp.json` SSE path fix: `http://localhost:9027` → `http://localhost:9027/sse`
- `extension.ts` autoConfigureMCP() updated: same change reflected + duplicate Crow addition removed
- VSIX rebuilt + reinstalled

**Installation Complete**:
- VibeZoo VS Code Extension installed (onStartupFinished auto-run)
- VibeZoo Bridge (9027/sse) Zoo Code connection successful (200 OK, 202 Accepted confirmed)
- Crow Memory (9020) retains existing user settings

**File List**:
| File | Purpose |
|:---|:---|
| `extension/` | VS Code Extension (TypeScript 16 files) |
| `mcp-servers/vibezoo_mcp_bridge.py` | Unified MCP bridge (Scout·Reviewer·Tester·DeepAnalyzer·Whiteboard) |
| `templates/` | yoloignore, zoo-config, vscode-settings default templates |
| `fromscratch/` | Architecture.md, PLAN.md, analysis documents |

---

## 2026-05-27 - v0.10.0: MCP auto-config fix, Whiteboard auto-integration

**Changes**:
- `extension.ts` autoConfigureMCP() updated: Crow no longer added (preserves existing user config)
- Crow removed from `.roo/mcp.json`, only VibeZoo remains

---

## 2026-05-27 - v0.10.0: AI auto Whiteboard + UI Preview integration

**Changes**:
- New MCP tools added to `vibezoo_mcp_bridge.py`:
  - `draw_on_whiteboard(commands)` — AI sends Fabric.js drawing commands
  - `get_whiteboard_state()` — Query user modifications
  - `open_whiteboard(message)` — AI requests opening whiteboard panel
  - `open_ui_preview(code, framework)` — AI requests opening UI Preview
- `VisualVibePanels.ts` — File watch functionality added:
  - Detects AI's `draw_on_whiteboard` call → auto open Whiteboard + render
  - Detects AI's `open_ui_preview` call → auto open UI Preview
  - 1-second interval polling for state change detection

---

## 2026-05-27 - v0.10.0: Python MCP bridge migration + Go removal

**Changes**:
- Go MCP servers (Scout·Reviewer·Tester·DeepAnalyzer·build.ps1·go.mod) → unified into single `vibezoo_mcp_bridge.py` file
- `SubagentManager.ts` heavily modified: Go spawn → Python FastMCP spawn
- Auto Python dependency installation added (`fastmcp`, `uvicorn`, `requests`)

**Architecture Change**:
```
Before: VibeZoo Extension + Go MCP 4 servers + Crow(external)
After:  VibeZoo Extension + vibezoo_mcp_bridge.py 1 file + Crow(external)
```

---

## 2026-05-27 - v0.10.0: Initial implementation complete (26 files)

**Files Created** (26):
- `extension/src/` — 16 TypeScript files
- `mcp-servers/` — 5 Go servers + go.mod + build.ps1
- `templates/` — 3 templates
- `fromscratch/` — Architecture.md + PLAN.md
- `README.md`, `package.json`, `tsconfig.json`

**Wave 1-5 Features Implemented**:
| Wave | Feature |
|:---|:---|
| Phase 0 | Crow connection, StatusBar, directory templates |
| Wave 1 | Silent Build, build error capture, project detection, tree scan |
| Wave 2 | yocto backup, Instant Rewind, File Guard, Git Stash, AutoBuildFix |
| Wave 3 | ContextFreshness, ExplainLess detection, SessionResume, EmotionalDetector |
| Wave 4 | SubagentManager, @mention routing |
| Wave 5 | Whiteboard, UI Preview, Diagram Webview panels |
| Wave 6 | Deep Analyzer (integrated into vibezoo_mcp_bridge.py) |

---

## 2026-05-27 - Architecture design started

**Analysis Completed**:
- `reportfromgemini.md` — 201-line report analysis
- `zoo_code_upgrade.agent.final.md` — 6,704-line detailed design analysis

**Decisions**:
- VS Code source modification 0% strategy
- Companion-First architecture (extension pack for Zoo Code)
- API-based LLM (no local model needed)
- Crow Memory as external independent system

---

## 2026-05-29 - v0.13.0: Bridge stability audit — critical issues found

**Context**: Real-world testing session with AI agent (Orchestrator + Crow mode). 7 VibeZoo MCP tools tested. Crow Memory (9020) as comparison baseline — 0 failures across all operations.

### Results Summary

| Tool | Call Count | Success | Failure | Error Type |
|:---|:---:|:---:|:---:|:---|
| `summarize_architecture` | 1 | ✅ 1 | — | — |
| `learn_preference` | 2 | ✅ 2 | — | — |
| `get_preferences` | 1 | — | ❌ 1 | `-32602` Invalid params |
| `find_bugs` | 1 | — | ❌ 1 | 60s timeout |
| `review_code` | 1 | — | ❌ 1 | 60s timeout |
| `search_codebase` | 1 | — | ❌ 1 | `-32602` Invalid params |
| `check_quality` | 1 | — | ❌ 1 | `-32602` Invalid params |
| **Total** | **8** | **3** | **5** | **62.5% failure rate** |

### Root Cause Analysis

**Issue #1: Progressive state corruption (`-32602` epidemic)**
- [`vibezoo_mcp_bridge.py:54`](../mcp-servers/vibezoo_mcp_bridge.py:54): `mcp = FastMCP(name="vibezoo")` — global singleton, no request isolation
- [`vibezoo_mcp_bridge.py:156-177`](../mcp-servers/vibezoo_mcp_bridge.py:156): `_file_scan_cache` — module-level dict, state accumulates across requests
- [`vibezoo_mcp_bridge.py:230-234`](../mcp-servers/vibezoo_mcp_bridge.py:230): `_ts_available`, `_ts_parser`, `_ts_ts_language` — global tree-sitter state
- [`vibezoo_mcp_bridge.py:40-45`](../mcp-servers/vibezoo_mcp_bridge.py:40): `CROW_URL`, `WHITEBOARD_FILE` — all module-level globals
- **Likely mechanism**: `_init_tree_sitter()` at line 236 uses `pip install tree-sitter --quiet` with retries. Multiple concurrent tool calls may corrupt the global `_ts_parser` state, cascading `-32602` to all subsequent requests regardless of whether they use AST.

**Issue #2: Timeout cascade in integrated tools**
- [`vibezoo_mcp_bridge.py:1743-1766`](../mcp-servers/vibezoo_mcp_bridge.py:1743): `_run_tool()` — calls internal functions synchronously
- [`vibezoo_mcp_bridge.py:1780-1845`](../mcp-servers/vibezoo_mcp_bridge.py:1780): `review_project()` — chains 4+ internal tool calls sequentially
- [`vibezoo_mcp_bridge.py:1849-1909`](../mcp-servers/vibezoo_mcp_bridge.py:1849): `find_bugs()` — chains 10+ `search_codebase` calls + Crow recall
- **No partial result handling**: If step 3 of 10 fails, all 9 prior results are lost
- **No streaming**: 60-second silent wait → single failure message

**Issue #3: `summarize_architecture` lacks real architecture analysis**
- [`vibezoo_mcp_bridge.py:711-780`](../mcp-servers/vibezoo_mcp_bridge.py:711): Output is directory tree + file extension counts + `requirements.txt` detection
- Does NOT leverage: `map_dependencies` (AST imports), `analyze_call_graph` (AST call graph), `extract_patterns` (pattern mining)
- Missing: module dependency graph, data flow analysis, layer identification, design pattern detection

**Issue #4: Error message poverty**
- [`vibezoo_mcp_bridge.py:74-87`](../mcp-servers/vibezoo_mcp_bridge.py:74): `_validate_file_path()` returns "File not found: {file_path}" — no attempted path, no cwd context
- `-32602` errors: No parameter-level detail about which argument failed validation
- Timeouts: No intermediate progress, no partial results

**Issue #5: Crow Memory comparison — what Crow does right**
- Single-responsibility tools (one operation per tool)
- Lightweight responses (hundreds of bytes, not megabytes)
- Predictable failure: clear validation errors on bad parameters
- Zero state accumulation between requests

### Action Plan

| Priority | Item | Effort | Target |
|:---:|:---|:---:|:---|
| **P0** | Add global exception handler middleware to bridge — log tool name + parameters on all failures | S | Today |
| **P0** | Verify `_init_tree_sitter()` thread safety — add mutex/lock for global parser state | S | Today |
| **P1** | Add graceful degradation to `_run_tool()` — partial results on child tool failure | M | 2 days |
| **P1** | Add `--debug` flag for detailed parameter-level error reporting | S | 1 day |
| **P2** | Enhance `summarize_architecture` to call `map_dependencies` + `analyze_call_graph` internally | M | 3 days |
| **P2** | Add streaming/progress support to integrated tools (>5s operations) | L | 1 week |
| **P3** | Refactor integrated tools into composable primitives + separate orchestration layer | XL | 2 weeks |

---

## 2026-05-29 - v0.13.0: Performance optimization + bug fixes + documentation

**Changes**:
- `SubagentManager.ts`: Crow URL bug fix (bridge port 9027 → Crow port 9020)
- `FileGuard.ts`: ON/OFF toggle feature added (`_enabled`, `toggle()`, `isEnabled()`)
- `TreeViewProviders.ts` + `extension.ts`: Sidebar FileGuard toggle node (🛡️/🔓)
- `package.json`: `vibezoo.toggleFileGuard` command registered
- `vibezoo_mcp_bridge.py`: `_iter_project_files` optimization (N rglob per extension → 1 os.walk)
- `vibezoo_mcp_bridge.py`: `suggest_refactor` duplicate scan removal (_iter_project_files_cached cache)
- All 31 VibeZoo MCP tools verified (full real implementation confirmed)
- Extension global install path copy automation (workspace out/ → %USERPROFILE%\.vscode\extensions\local.vibezoo-0.13.0\out\)

**GitHub**: 8 commits main → main push completed

### 2026-05-29 - Global MCP duplicate registration prevention

**Changes**:
- `extension.ts`: Added global MCP check logic to `autoConfigureMCP()` (if vibezoo is registered globally, skip project-level `.roo/mcp.json` creation)

---

## 2026-05-28 - v0.13.0: Phase 1~6 Full Implementation

**Phase 0 Completed** (existing):
- SelfCheck.ts (AlarmMonitor + SelfChecker) ✅
- StatusBarManager.ts (NotificationThrottle + GuardMode) ✅
- types/index.ts (SelfCheckReport, ThrottleEntry) ✅
- FileGuard.ts (cooldown + syncFromCrow filter) ✅
- .roo/mcp.json (vibezoo SSE registration) ✅

**Phase 1: Whiteboard Stabilization**
- Fabric.js 5.3.1 local bundling: downloaded `extension/media/fabric.min.js`
- `getFabricJs()` helper: local file first, CDN fallback on failure
- Added `_context: vscode.ExtensionContext` field to `VisualVibePanels`
- `handleFileChange()`: early return with `lastMtime` mtime comparison
- `WATCH_INTERVAL_MS`: 500ms → 200ms
- Welcome message: shown only on first run via `context.globalState`
- Registered `vibezoo.selfCheck` command (uses SelfChecker)

**Phase 2: 4 Major Improvements**
- `InstabilityMetrics` + `calculateInstability()` (α=0.35, β=0.45, γ=0.20)
- `getGuardMode()`: <0.3=active, <0.7=warning, ≥0.7=safe
- `YoctoManager.atomicCopyFile()`: crypto.randomUUID temp file → rename
- `FixLoopManager.hydrateContext()`: file diff on resume → Crow ingest
- Crow `try_crow_ingest`/`try_crow_recall`: 150ms start, 2x increase, max 3, random jitter

**Phase 3: Virtual Subagent**
- `SubagentPool` class: asyncio.Semaphore(5) concurrency control
- `SubagentTask` dataclass + `ROLE_TOOLS` mapping
- 5 MCP tools: `create_subagent`, `check_subagent`, `get_subagent_result`, `list_subagents`, `cancel_subagent`
- `ActiveSubagentsProvider.pollSubagentTasks()`: 30s interval MCP Bridge polling

**Phase 4: Intent-to-Code Bridge**
- `extract_intent_from_whiteboard()`: rect→class, line/arrow→dependency
- `_find_nearby_text()`, `_extract_members_from_rect()`, `_find_nearest_class()` helpers
- `generate_code_from_whiteboard()`: TypeScript skeleton generation
- `_generate_class_stub()`: import/extends/members handling
- Whiteboard UI "📐 Code" button + preview + Apply

**Phase 5: Verification**
- `checkZooCodeCompatibility()`: vscode.extensions.getExtension('zoocodeorganization.zoo-code')
- `checkNotificationHealth()`: AlarmMonitor recentAlarmCount/throttled
- All `showInformationMessage`/`showWarningMessage` → `NotificationThrottle.showInfo()`/`showWarning()`
- Resource cleanup verification: setTimeout/clearTimeout, fs.watchFile/unwatchFile, spawn/kill

**Phase 6: Documentation + GitHub + VSIX**
- Architecture.md/PLAN.md/ROADMAP.md/JOURNAL.md updated
- git commit + push
- VSIX build + installation
