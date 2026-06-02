# VibeZoo Development Journal

> Click `Table of Contents` in the upper right → navigate to desired date
> New changes are added at the **top**

---

## 2026-06-02 - Dropzone Webview Bug Fixes & Architecture Analysis

### 변경 요약 (Dropzone Webview 치명적 버그 수정)
- **파이썬 `os.replace` 와처 파괴 버그 수정**: `mcp-servers/bridge/utils.py`의 `_atomic_write_json` 함수에서 `os.replace` 방식 대신 윈도우 와처 호환을 위해 `with open(..., 'w')` 직접 덮어쓰기 방식으로 변경.
- **TS 파싱 에러 데드락 버그 수정**: `extension/src/visual/VisualVibePanels.ts`의 `handleFileChange` 콜백이 0바이트 파일에 의해 실패하는 것을 대비하여 `retries=5` (200ms 간격) 재시도 로직 구현.
- **TS 타임스탬프 해상도 버그 회피**: 윈도우 OS의 낮은 `mtimeMs` 해상도로 인한 이벤트 무시(씹힘) 현상을 막기 위해 파일 내용 기반 해시(`JSON.stringify(content)`) 비교 로직 도입.
- **Drag & Drop 새 창 열림 버그 수정**: Dropzone 웹뷰에서 파일을 떨어뜨릴 때 VS Code 기본 동작(새 탭에 이미지 열림)이 발동하지 않도록 `window` 객체 전역에 `dragover`, `dragleave`, `drop` 이벤트를 등록하여 `preventDefault()`, `stopPropagation()` 적용.
- **로컬 환경 동기화 (Hot-fix)**: `tsc` 빌드 결과물(`out/`)을 글로벌 확장 프로그램 경로(`~/.vscode/extensions/local.vibezoo-0.14.0/out/`)에 덮어씌워 런타임 적용.

### 추가 설치 현황 (Dropzone 3계층 분석 엔진 대비)
- **의존성 설치 완료**: `PyMuPDF`, `python-docx` (문서 텍스트 추출용), `paddlepaddle`, `paddleocr` (Tesseract 대체 및 fallback용 OCR 엔진).
- **모델 다운로드**: `models/` 디렉토리 생성 후 `huggingface-cli`를 통해 MiniCPM-V GGUF 로컬 Vision LLM 모델 백그라운드 다운로드 진행.
- **보고서 작성**: `feedbacks/260602_vibezoo_dropzone_ultimate_fix.md` 최종 리포트 커밋 완료.

---

- [2026-05-31 - v0.14.0 SOTA: 3 Cycle Evolution + bridge/ 모듈화 완료](#2026-05-31---v0140-sota-3-cycle-evolution--bridge-모듈화-완료)
- [2026-05-30 - v0.14.0: SOTA MCP Tool Upgrade Phase 1-3](#2026-05-30---v0140-sota-mcp-tool-upgrade-phase-1-3)
- [2026-05-29 - v0.13.0: Performance optimization + bug fixes + documentation](#2026-05-29---v0130-performance-optimization--bug-fixes--documentation)
- [2026-05-28 - v0.13.0: Phase 1~6 Full Implementation](#2026-05-28-v0130-phase-16-full-implementation)
- [2026-05-27 - v0.10.0 Final: Go file cleanup, SSE path fix](#2026-05-27-v0100-final-go-file-cleanup-sse-path-fix)
- [2026-05-27 - v0.10.0: MCP auto-config fix, Whiteboard auto-integration](#2026-05-27-v0100-mcp-auto-config-fix-whiteboard-auto-integration)
- [2026-05-27 - v0.10.0: AI auto Whiteboard + UI Preview integration](#2026-05-27-v0100-ai-auto-whiteboard--ui-preview-integration)
- [2026-05-27 - v0.10.0: Python MCP bridge migration + Go removal](#2026-05-27-v0100-python-mcp-bridge-migration--go-removal)
- [2026-05-27 - v0.10.0: Initial implementation complete (26 files)](#2026-05-27-v0100-initial-implementation-complete-26-files)
- [2026-05-27 - Architecture design started](#2026-05-27-architecture-design-started)

---

## 2026-05-31 - 도구 정리: 4개 도구 제거 + 보고서→설명서 전환

### 변경 요약
- **제거된 MCP 도구**: `check_quality`(→review_project), `open_image_dropzone`(→capture_screen), `open_whiteboard`(자동), `open_ui_preview`(LLM직접)
- **31개 도구**로 간소화 (35→31)
- **260531VibeZooReport.md**: 평가 보고서 → **설명서 형식**으로 전환. 각 도구의 역할/파라미터/사용예시/LLM힌트 중심
- **knowledge.py**: `global _auto_learn_scheduled` 선언 순서 버그 수정
- **커밋**: `dc40ba0`

---

## 2026-05-31 - v0.14.0 SOTA: 3 Cycle Evolution + bridge/ 모듈화 완료

### 변경 요약
- **대규모 리팩토링**: 4,627줄 단일 파일 → `bridge/` 24개 모듈로 분할 (v0.13.0→v0.14.0)
- **SearchEngine**: ripgrep→git grep→walk 3단계 폴백 검색
- **FileCache**: L1(LRU)+L2(디스크)+L3(mtime) 3계층 캐시
- **AstEngine**: TS/JS/Python/Go/Rust 멀티랭귀지 tree-sitter 동적 로딩
- **WhiteboardDataConverter**: Fabric.js JSON→텍스트/Mermaid/공간데이터 변환 (Deepseek 호환)
- **OcrEngine**: Tesseract+PaddleOCR fallback, SSA 통합
- **ToolContext + LLMToolPipeline**: LLM-도구 체인 (데이터 수집→LLM 분석→Crow 저장)
- **vibezoo_setup**: 통합 설치 도구 (pip+시스템 도구+MCP/Zoo 설정)

### 3 Cycle Evolution
- **Cycle 1**: LLM-도구 체인 + 컨텍스트 최적화(mode=summary) + AST 확장 + WebSearch SearXNG + FileCache.warm() + 폐기
- **Cycle 2**: suggest_refactor summary + LLM체인심화(dependencies/mock) + AST 활용 확대 + 병렬 WebSearch + retry_build 에러추출 + ESLint/tsc 통합
- **Cycle 3**: AST 멀티랭귀지 완전활용(analyze_call_graph/find_references/explain_code) + AST-aware rename(변수섀도잉) + Knowledge 자동연계(auto_learn_project)

### 보고서
- **260531VibeZooReport.md** — 35개 도구 최종 평가 (⭐⭐⭐ 18개, ⭐⭐ 12개, ⭐ 4개, 💀 1개)
- plans/major-refactor-plan.md — 모듈화 아키텍처 설계
- plans/sota-upgrade-plan.md — Phase A~F SOTA 업그레이드 설계

### Git 커밋
- `4ef0310` v0.13.0 bridge/ 모듈화
- `a58723f` Pylance 경고 해결
- `57c7e29` Cycle 1-2 리팩토링
- `d310c5f` Cycle 2-2 리팩토링
- `f4f257f` Cycle 3-2 리팩토링
- `95d294e` FINAL 최종 보고서

---

## 2026-05-30 - v0.14.0: SOTA MCP Tool Upgrade Phase 1-3

### 변경 요약
- **vibezoo_mcp_bridge.py**: 3,496라인 (+220라인). 10개 인프라 함수 추가 + search_codebase 업그레이드
- **vibezoo_mcp_bridge_v2.py**: 3,856라인, 167KB (신규). Phase 2+3+추가 7개 도구 전체 업그레이드 포함
- **글로벌 MCP 설정**: 31개 도구 alwaysAllow 등록
- **ripgrep 15.1.0**: winget 설치, PATH 영구 등록
- **plans/mcp-tool-sota-upgrade.md**: 상세 업그레이드 계획

### Phase 1 (적용 완료)
- BM25 TF-IDF, fuzzy match, secret detection(12패턴), duplicate blocks, complexity, git blame, related tests, Python/Go import

### Phase 2 (v2 파일)
- map_dependencies: 멀티랭귀지 import + Iterative DFS + package manager + Mermaid
- analyze_call_graph: function map + Fan-in/out + dead code
- reverse_engineer: AST API + model relations + OpenAPI 3.0

### Phase 3 + 추가 (v2 파일)
- generate_tests: boundary values + branch coverage + mock
- find_references: type classification + call chain
- summarize_architecture: import-based layers + tech debt
- check_quality: A-F grade, extract_patterns: lib stats
- analyze_coverage: test mapping, analyze_changes: change type
- review_pr: risk score, refactor_across_files: impact analysis

### 이슈
- vibezoo_mcp_bridge.py 파일 모니터링이 Phase 2/3 적용을 차단
- v2 파일은 생성됐으나 운영 브릿지 교체 불가
- 해결: VS Code 재시작 후 Extensions Disabled 상태에서 수동 교체

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
