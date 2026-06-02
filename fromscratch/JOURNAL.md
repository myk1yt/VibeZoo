# VibeZoo Development Journal

> Click `Table of Contents` in the upper right → navigate to desired date
> New changes are added at the **top**

---

- [2026-06-02 - v0.14.1: VibeZoo v2 업그레이드 (드랍존 범용화 + PDF 파이프라인 + OCR 전처리)](#2026-06-02---v0141-vibezoo-v2-업그레이드-드랍존-범용화--pdf-파이프라인--ocr-전처리)
- [2026-06-02 - v0.14.0: UX Workflow 구현 (의도 감지 + 자동 도구 체인)](#2026-06-02---v0140-ux-workflow-구현-의도-감지--자동-도구-체인)
- [2026-05-29 - v0.13.0: Performance optimization + bug fixes + documentation](#2026-05-29---v0130-performance-optimization--bug-fixes--documentation)
- [2026-05-28 - v0.13.0: Phase 1~6 Full Implementation](#2026-05-28-v0130-phase-16-full-implementation)
- [2026-05-27 - v0.10.0 Final: Go file cleanup, SSE path fix](#2026-05-27-v0100-final-go-file-cleanup-sse-path-fix)
- [2026-05-27 - v0.10.0: MCP auto-config fix, Whiteboard auto-integration](#2026-05-27-v0100-mcp-auto-config-fix-whiteboard-auto-integration)
- [2026-05-27 - v0.10.0: AI auto Whiteboard + UI Preview integration](#2026-05-27-v0100-ai-auto-whiteboard--ui-preview-integration)
- [2026-05-27 - v0.10.0: Python MCP bridge migration + Go removal](#2026-05-27-v0100-python-mcp-bridge-migration--go-removal)
- [2026-05-27 - v0.10.0: Initial implementation complete (26 files)](#2026-05-27-v0100-initial-implementation-complete-26-files)
- [2026-05-27 - Architecture design started](#2026-05-27-architecture-design-started)

---

## 2026-06-02 - v0.14.1: VibeZoo v2 업그레이드 (드랍존 범용화 + PDF 파이프라인 + OCR 전처리)

**Changes**:
- 실제 사용 피드백 기반 개선 (KOICA CTS PDF 업로드 → 분석 워크플로우)
- config.py: `get_uploaded_path()` 함수 추가 — 확장자 보존 동적 경로
- whiteboard.py: 드랍존 HTML/메시지 멀티파일 지원 (📎 모든 파일 타입)
- file_analyzer.py: `_analyze_pdf_as_image()` 신규 — PDF→이미지 변환(fitz)→SSA→OCR→MiniCPM 자동 연계
- ux_coordinator.py: PDF 파일 `analyze_file()` 직접 호출로 강화
- ocr_engine.py: `_preprocess_for_ocr()` — AdaptiveThresholding + 노이즈 제거 전처리
- 설계 문서: [`plans/vibezoo-v2-upgrade.md`](plans/vibezoo-v2-upgrade.md)
- GitHub: 6 files changed, 481 insertions, push 완료 (commit 20b8943)
- Cleanup: `_extract_pdf.py`, `_extract_pdf_v2.py` 삭제

---

## 2026-06-02 - v0.14.0: UX Workflow 구현 (의도 감지 + 자동 도구 체인)

**Changes**:
- 신규: [`bridge/intent_detector.py`](../mcp-servers/bridge/intent_detector.py) — 키워드 기반 자연어 의도 감지 모듈 (`file_share`, `drawing_request`, `whiteboard_input`, `code_analysis`, `general_question`)
- 신규: [`bridge/tools/ux_coordinator.py`](../mcp-servers/bridge/tools/ux_coordinator.py) — UX 코디네이터 (3개 도구: `ux_coordinator`, `auto_analyze_after_drop`, `auto_analyze_whiteboard`)
- 수정: [`tools/__init__.py`](../mcp-servers/bridge/tools/__init__.py), [`whiteboard.py`](../mcp-servers/bridge/tools/whiteboard.py), [`file_analyzer.py`](../mcp-servers/bridge/tools/file_analyzer.py), [`vibezoo_mcp_bridge_v2.py`](../mcp-servers/vibezoo_mcp_bridge_v2.py)
- 설계 문서: [`plans/ux-workflow-design.md`](../plans/ux-workflow-design.md)
- GitHub: 7 files changed, 918 insertions, push 완료
- MiniCPM 우선 사용 피드백 반영

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
