# VibeZoo Development Journal

> Click `Table of Contents` in the upper right → navigate to desired date
> New changes are added at the **top**

---

- [2026-05-29 - v0.13.0: 성능 최적화 + 버그 수정 + 문서화](#2026-05-29---v0130-성능-최적화--버그-수정--문서화)
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

## 2026-05-29 - v0.13.0: 성능 최적화 + 버그 수정 + 문서화

**변경사항**:
- `SubagentManager.ts`: Crow URL 버그 수정 (bridge port 9027 → Crow port 9020)
- `FileGuard.ts`: ON/OFF 토글 기능 추가 (`_enabled`, `toggle()`, `isEnabled()`)
- `TreeViewProviders.ts` + `extension.ts`: 사이드바 FileGuard 토글 노드 (🛡️/🔓)
- `package.json`: `vibezoo.toggleFileGuard` 커맨드 등록
- `vibezoo_mcp_bridge.py`: `_iter_project_files` 최적화 (확장자별 N회 rglob → os.walk 1회)
- `vibezoo_mcp_bridge.py`: `suggest_refactor` 중복 스캔 제거 (_iter_project_files_cached 캐시)
- 31개 VibeZoo MCP 툴 전수 검증 완료 (전체 실구현 확인)
- Extension 전역 설치 경로 복사 자동화 (workspace out/ → %USERPROFILE%\.vscode\extensions\local.vibezoo-0.13.0\out\)

**GitHub**: 8개 커밋 main → main push 완료

### 2026-05-29 - 전역 MCP 중복 등록 방지

**변경사항**:
- `extension.ts`: `autoConfigureMCP()`에 전역 MCP 확인 로직 추가 (전역에 vibezoo 등록되어 있으면 프로젝트 레벨 `.roo/mcp.json` 생성 건너뜀)

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
