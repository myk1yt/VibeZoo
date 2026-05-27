# VibeZoo 아키텍처 — v0.12.0

> **작성일**: 2026-05-27 (v0.10.0 초안) → 2026-05-27 (v0.12.0 전면 개정)
> **기준 버전**: v0.12.0
> **프로젝트명**: VibeZoo — Zoo Code를 위한 독립형 동반자 확장
> **핵심 제약**: Zoo Code 소스 코드를 수정하지 않는다. 모든 기능은 VibeZoo Extension + MCP Bridge + 설정 파일 변경으로 구현한다.

---

## 0. 문서 이력 및 변경 요약

### 0.1 원본(v0.10.0 설계) 대비 주요 변경점

| # | 항목 | 원본 설계 (v0.10.0) | 현재 현실 (v0.12.0) |
|:---|:---|:---|:---|
| 1 | **Crow Memory** | VibeZoo가 spawn·관리하는 외부 시스템 | Zoo Code 내장 시스템. VibeZoo는 `/health` 감지 및 Crow 도구 연동만 수행 |
| 2 | **MCP 서버** | Go 4개 바이너리 (Scout:9022, Reviewer:9023, Tester:9024, Deep:9026) | Python 단일 브릿지 [`vibezoo_mcp_bridge.py`](../mcp-servers/vibezoo_mcp_bridge.py) (포트 9027) |
| 3 | **AutoBuildFix** | [`extension/src/safety/AutoBuildFix.ts`](../extension/src/safety/AutoBuildFix.ts) — 빈 루프 (rebuild만 반복) | [`extension/src/orchestra/FixLoopManager.ts`](../extension/src/orchestra/FixLoopManager.ts) — 자율 수정 상태 머신 + CIM + HITL |
| 4 | **Session Resume** | Webview 패널 | TreeView로 통합 ([`extension/src/ui/TreeViewProviders.ts`](../extension/src/ui/TreeViewProviders.ts) `SessionResumeProvider`) |
| 5 | **MCP 도구 수** | 15개 | 31개 (tree-sitter AST 기반 시맨틱 분석) |
| 6 | **Autonomous Fix Loop** | 설계만 존재 | 구현 완료 — `FixLoopManager` + `auto_fix_status` + `retry_build` + `check_intervention` |
| 7 | **Self-healing CIM** | 설계만 존재 | 구현 완료 — `FixLoopManager.startWatching()` (파일 저장 → tsc → 자동 수정) |
| 8 | **HITL 개입** | 설계만 존재 | 구현 완료 — `pause/resume/abort` + Whiteboard·채팅 개입 채널 |
| 9 | **StatusBar** | 2개 (Crow 연결, VibeZoo 상태) | 1개 통합 — [`extension/src/ui/StatusBarManager.ts`](../extension/src/ui/StatusBarManager.ts) (Crow·YOLO·CIM·Bridge 상태 통합) |
| 10 | **화이트보드 동기화** | `setInterval` 1초 폴링 | `fs.watchFile` 이벤트 기반 ([`extension/src/visual/VisualVibePanels.ts`](../extension/src/visual/VisualVibePanels.ts)) |
| 11 | **TreeView** | YOLO History 1개 | 3개 (Active Subagents, YOLO History, Session Resume) |
| 12 | **VS Code 명령어** | 2개 | 26개 (통합 시나리오, Fix Loop 제어, CIM, 학습/회상 등) |

---

## 1. Executive Summary

### 1.1 VibeZoo란?

VibeZoo는 Zoo Code를 **소스 코드 수정 없이** 보조하는 VS Code 동반자 확장(Companion Extension)이다. Zoo Code가 LLM 추론 엔진이라면, VibeZoo는 그 주변을 감싸는 **운영체제** 역할을 한다:

- **상태 표시**: 통합 StatusBar로 Bridge·Crow·YOLO·CIM 상태를 한눈에
- **안전망**: yocto 실시간 백업, `.yoloignore` File Guard, Git Stash 자동화
- **자율 수정**: 빌드 실패 → LLM 분석 → 코드 수정 → 재빌드 (최대 3회, oscillation 감지)
- **지속 감시**: CIM (Continuous Improvement Mode) — 파일 저장 시 자동 tsc 검사
- **MCP 도구**: 31개 도구 (tree-sitter AST 기반 코드 검색·리뷰·분석·역설계·PR 리뷰·리팩토링·선호도 학습)
- **시각 협업**: Whiteboard, UI Preview, Diagram Engine
- **기억 연동**: Crow Memory (Zoo Code 내장)와 Crow 도구로 에러 패턴·프로젝트 지식·코딩 선호도 학습

### 1.2 핵심 철학

```
Vibe = f(Usefulness, Predictability, Control_perceived)
```

- **"VS Code Lock-In"**: VS Code를 벗어나지 않는다.
- **"통제 가능한 자동화"**: Human-in-the-Loop — 자동 수정 중에도 사용자가 개입할 수 있다.
- **"Zoo Code 소스 수정 제로"**: Zoo Code를 포크하지 않는다. VibeZoo Extension + MCP Bridge + Config만으로 모든 기능 구현.
- **"Crow는 Zoo Code가, VibeZoo는 감지만"**: Crow Memory는 Zoo Code의 내장 시스템. VibeZoo는 연결 상태 감지 및 Crow 도구 연동만 수행한다.

---

## 2. 실제 아키텍처 다이어그램

```
┌──────────────────────────────────────────────────────────────────┐
│                        VS Code 창                                  │
│                                                                   │
│  ┌────────────────────────┐    ┌──────────────────────────────┐  │
│  │     Zoo Code (LLM)     │    │  VibeZoo Extension            │  │
│  │                        │    │                               │  │
│  │  • LLM 추론 엔진       │    │  • StatusBarManager (통합 1) │  │
│  │  • Crow Memory 내장    │    │  • TreeView 3종              │  │
│  │    (localhost:9020)    │    │    - Active Subagents        │  │
│  │  • MCP Client          │    │    - YOLO History            │  │
│  │                        │    │    - Session Resume          │  │
│  │  ◄── MCP/SSE ──────────┼────┤  • FixLoopManager (자율)     │  │
│  │      tool call         │    │    - 상태 머신 (8 states)    │  │
│  │                        │    │    - oscillation 감지        │  │
│  │                        │    │    - CIM (지속 감시)         │  │
│  │                        │    │  • VisualVibePanels          │  │
│  │                        │    │    - Whiteboard (fs.watch)   │  │
│  │                        │    │    - UI Preview              │  │
│  │                        │    │  • YoctoManager (yocto 백업) │  │
│  │                        │    │  • FileGuard (.yoloignore)   │  │
│  │                        │    │  • GitStashManager           │  │
│  │                        │    │  • SubagentManager           │  │
│  │                        │    │  • CrowServerManager (감지)  │  │
│  │                        │    │  • ContextIntelligence       │  │
│  └───────────┬────────────┘    └──────────────┬───────────────┘  │
│              │                                │                   │
└──────────────┼────────────────────────────────┼───────────────────┘
               │ MCP/SSE                        │ child_process.spawn
               ▼                                ▼
┌──────────────────────────┐    ┌──────────────────────────────────┐
│ Zoo Code Crow Memory     │    │ VibeZoo MCP Bridge               │
│ (Zoo Code 내장)          │    │ vibezoo_mcp_bridge.py            │
│ localhost:9020           │    │ localhost:9027/sse               │
│                          │    │                                  │
│ • crow_recall            │    │ • 31개 MCP 도구                  │
│ • crow_ingest            │    │ • tree-sitter AST 파싱           │
│ • crow_compact           │    │ • Crow Memory 연동               │
│ • crow_evolve_propose    │    │   (crow_recall/ingest 래퍼)      │
│ • crow_diagnostics       │    │ • /health 엔드포인트             │
│ • crow_manage_backup     │    │ • ~/.vibezoo-fix-request.json    │
│ • crow_manage_prompt     │    │ • ~/.vibezoo-whiteboard.json     │
│ • crow_get_user_bias     │    │ • ~/.vibezoo-preferences.json    │
│ • crow_check_drift       │    │                                  │
│ • crow_project_info       │    │ FastMCP + SSE transport          │
└──────────────────────────┘    └──────────────────────────────────┘
```

### 2.1 포트 할당

| 포트 | 시스템 | 역할 | 관리 주체 |
|:---|:---|:---|:---|
| **9020** | Crow Memory | 지식 저장·회상·압축·진단 | Zoo Code (내장) |
| **9027** | VibeZoo MCP Bridge | 코드 검색·리뷰·분석·시각화·Fix Loop | VibeZoo Extension (`SubagentManager.spawnBridge()`) |

**중요**: Crow Memory(9020)는 Zoo Code가 직접 관리한다. VibeZoo는 Crow 서버를 spawn하지 않으며, [`CrowServerManager`](../extension/src/crow/CrowServerManager.ts)는 오직 `/health` 확인과 연결 상태 감지만 수행한다.

---

## 3. 파일 구조 (실제)

```
VibeZoo_forZoocode/
├── extension/                        # VibeZoo VS Code Extension (TypeScript)
│   ├── package.json                  # v0.12.0, 26개 명령어, 3개 TreeView, 18개 설정
│   ├── tsconfig.json
│   ├── .vscodeignore
│   └── src/
│       ├── extension.ts              # 진입점 — activate(): 26개 커맨드, Bridge spawn, 모듈 초기화
│       ├── context/
│       │   └── ContextIntelligence.ts # ContextIndicator, ExplainLessSuggestor, SessionResume, EmotionalDetector
│       ├── crow/
│       │   └── CrowServerManager.ts  # Zoo Code Crow 감지 전용 (health check, 상태 알림)
│       ├── flow/
│       │   ├── BuildFeedback.ts      # 빌드 종료 감지 → FixLoopManager 연동
│       │   ├── BuildTaskProvider.ts  # Silent Build Task 등록
│       │   ├── ProjectDetector.ts    # 프로젝트 타입 감지 → 모드 제안
│       │   └── ProjectTreeScanner.ts # 프로젝트 트리 스캔 + 캐싱
│       ├── orchestra/
│       │   ├── FixLoopManager.ts     # 자율 수정 루프 (8개 상태 머신) + CIM (파일 감시)
│       │   ├── MentionRouter.ts      # @mention 라우팅
│       │   └── SubagentManager.ts    # Python MCP Bridge spawn·관리
│       ├── safety/
│       │   ├── FileGuard.ts          # .yoloignore 기반 보호 파일 감시·복구
│       │   ├── GitStashManager.ts    # YOLO 진입/퇴장 Git Stash 자동화
│       │   └── YoctoManager.ts       # yocto 실시간 백업·복구 (FileSystemWatcher)
│       ├── types/
│       │   └── index.ts              # 공통 타입 (Diagnostic, SessionSummary, SubagentNode 등)
│       ├── ui/
│       │   ├── StatusBarManager.ts   # 통합 StatusBar (Bridge·Crow·YOLO·CIM·모드 제안)
│       │   └── TreeViewProviders.ts  # 3개 Provider (ActiveSubagents, YOLO History, Session Resume)
│       └── visual/
│           └── VisualVibePanels.ts   # Whiteboard (fs.watchFile) + UI Preview + Diagram 패널
│
├── mcp-servers/
│   └── vibezoo_mcp_bridge.py         # 단일 파일, 31개 MCP 도구, FastMCP + SSE, 포트 9027
│
├── fromscratch/                      # 설계 문서
│   ├── Architecture.md               # ← 이 문서
│   ├── PLAN.md                       # 구현 계획
│   ├── ROADMAP.md                    # 성능·활용도 극대화 로드맵
│   ├── JOURNAL.md                    # 개발 일지
│   ├── reportfromgemini.md           # 초기 분석 보고서
│   └── zoo_code_upgrade.agent.final.md
│
├── plans/
│   └── autonomous-fix-loop.md        # FixLoopManager 상세 설계서
│
└── templates/
    ├── yoloignore                    # .yoloignore 템플릿
    ├── zoo-config.json               # .zoo/config.json 템플릿
    └── vscode-settings.json          # .vscode/settings.json 템플릿
```

---

## 4. 핵심 컴포넌트 상세

### 4.1 [`extension.ts`](../extension/src/extension.ts) — 진입점

`activate()` 함수에서 다음 순서로 초기화:

```
1. 중복 활성화 방지
2. 디렉토리·템플릿 자동 생성
3. CrowServerManager (Crow 감지) + StatusBarManager
4. Crow 연결 확인 (Bridge 시작과 독립적 조기 실행)
5. Flow Keepers: BuildTaskProvider, BuildFeedback, ProjectDetector, ProjectTreeScanner
6. Safety Net: YoctoManager, FileGuard, FixLoopManager, GitStashManager
7. Context Intelligence: ContextIndicator, ExplainLessSuggestor, SessionResume, EmotionalDetector
8. MCP Bridge spawn (SubagentManager.spawnBridge())
9. TreeView Providers: ActiveSubagents, YOLO History, Session Resume
10. Orchestra: MentionRouter
11. Visual Vibe: VisualVibePanels.activate()
12. 26개 VS Code 명령어 등록
```

**26개 등록 명령어**:

| 카테고리 | 명령어 |
|:---|:---|
| **Foundation** | `verifyFoundation`, `reconnectCrow` |
| **YOLO** | `instantRewind`, `toggleYolo` |
| **Scan** | `scanProject` |
| **Visual** | `openWhiteboard`, `openUIPreview`, `openDashboard` |
| **Session** | `showSessionResume`, `showHelp` |
| **통합 시나리오 (Q1)** | `reviewProject`, `findBugs`, `suggestRefactor`, `generateDocs` |
| **Fix Loop 제어** | `_autoBuildFix`, `_buildSuccess`, `pauseFixLoop`, `resumeFixLoop`, `abortFixLoop` |
| **CIM (M3)** | `startWatching`, `stopWatching` |
| **분석 (M3-A/B/C)** | `explainCode`, `analyzeChanges`, `reviewPR`, `refactorAcrossFiles` |
| **학습·회상 (M3-D/E)** | `learnProject`, `recallProject`, `learnPreference`, `getPreferences` |
| **Agent** | `showAgentInfo` |

### 4.2 [`FixLoopManager`](../extension/src/orchestra/FixLoopManager.ts) — 자율 수정 루프

**상태 머신 (8 states)**:

```
idle → pending → in_progress → building → resolved
                    │                │
                    │                ├── 실패 → pending (재시도, 최대 3회)
                    │                └── oscillation/max → abandoned
                    │
                    └── 사용자 개입 → awaiting_user → user_override → in_progress
```

**핵심 기능**:

| 기능 | 메서드 | 설명 |
|:---|:---|:---|
| 빌드 실패 감지 | `onBuildFailure()` | BuildFeedback → FixLoopManager, fix request JSON 기록 |
| LLM 분석 시작 | `markInProgress()` | `auto_fix_status()` MCP 도구 호출 시 상태 변경 |
| 빌드 실행 | `markBuilding()` | `retry_build()` MCP 도구 호출 전 상태 변경 |
| 빌드 성공 | `markResolved()` | 성공 알림 + fix request 파일 정리 |
| 빌드 재실패 | `markBuildFailed()` | oscillation 체크 후 재시도 또는 포기 |
| Oscillation 감지 | `isOscillating()` | A→B→A 패턴, 동일 에러 2회 연속 감지 |
| 타임아웃 | `resetSessionTimeout()` | 120초 내 미해결 시 abandoned |
| HITL | `pause()` / `resume()` / `abort()` | 사용자 개입 커맨드 |

**CIM (Continuous Improvement Mode)**:

`startWatching()` 호출 시 [`extension/src/orchestra/FixLoopManager.ts`](../extension/src/orchestra/FixLoopManager.ts:421)에서:
- TS/JS 파일 저장(`onDidSaveTextDocument`) → `npx tsc --noEmit` 자동 실행
- tsc 에러 발생 → `onBuildFailure()` → Auto-Fix 트리거
- 상태바에 `$(eye) VibeZoo: Watching` 표시

### 4.3 [`vibezoo_mcp_bridge.py`](../mcp-servers/vibezoo_mcp_bridge.py) — MCP Bridge

**31개 MCP 도구** (FastMCP + tree-sitter AST):

| 카테고리 | 도구 | AST 활용 |
|:---|:---|:---|
| **Scout** | `search_codebase`, `find_references`, `summarize_architecture` | tree-sitter 함수·클래스·인터페이스 검색 |
| **Reviewer** | `review_code`, `check_quality` | ESLint 연동 |
| **Tester** | `generate_tests`, `analyze_coverage` | — |
| **Deep Analyzer** | `analyze_call_graph`, `map_dependencies`, `extract_patterns`, `reverse_engineer` | AST 호출 그래프·import·필드 추출 |
| **Whiteboard** | `draw_on_whiteboard`, `get_whiteboard_state`, `open_whiteboard`, `capture_screen` | — |
| **UI Preview** | `open_ui_preview` | — |
| **Fix Loop (M1-A)** | `auto_fix_status`, `retry_build`, `check_intervention` | — |
| **통합 시나리오 (Q1)** | `review_project`, `find_bugs`, `suggest_refactor`, `generate_docs` | 연쇄 호출 |
| **설명 (M3-A)** | `explain_code` | AST 컨텍스트 (함수·클래스·인터페이스) |
| **Git 분석 (M3-B)** | `analyze_changes`, `review_pr` | — |
| **리팩토링 (M3-C)** | `refactor_across_files` | — |
| **지식 (M3-D)** | `learn_project`, `recall_project` | Crow arch·style·life_context 연동 |
| **선호도 (M3-E)** | `learn_preference`, `get_preferences` | Crow life_context 연동 |

**Crow 연동**: `try_crow_ingest()` / `try_crow_recall()` 래퍼로 모든 도구에서 Crow Memory(9020)와 선택적 연동. Crow 연결 실패 시에도 도구 동작에는 영향 없음.

**tree-sitter AST 파서**: TypeScript/JavaScript 파일에 대해 [`_parse_with_tree_sitter()`](../mcp-servers/vibezoo_mcp_bridge.py:108), [`_extract_ast_calls()`](../mcp-servers/vibezoo_mcp_bridge.py:164), [`_extract_ast_imports()`](../mcp-servers/vibezoo_mcp_bridge.py:200), [`_extract_ast_fields()`](../mcp-servers/vibezoo_mcp_bridge.py:257) 함수로 정확한 구조 분석. tree-sitter 미설치 시 regex fallback.

### 4.4 [`StatusBarManager`](../extension/src/ui/StatusBarManager.ts) — 통합 상태 표시

단일 StatusBar 항목 `$(zap) VibeZoo`에 모든 상태 정보 통합:

| 상태 | 표시 | 설명 |
|:---|:---|:---|
| **기본** | `$(zap) VibeZoo` | Bridge 연결됨 |
| **CIM 활성** | `$(eye) VibeZoo CIM` | 파일 감시 진행 중 |
| **YOLO 활성** | `$(flame) VibeZoo YOLO` | YOLO 모드 ON |
| **모드 제안** | `$(gear) 권장: {mode}` | 프로젝트 감지 기반 (5초 후 복원) |
| **진행 중** | `$(sync~spin) {message}` | MCP 도구 실행 중 |

**Tooltip 통합**: Bridge 상태 + Crow 연결 + CIM + YOLO 상태를 `_composeTooltip()`으로 동적 구성. `setActive()`와 `setCrowStatus()` 간 tooltip 충돌 방지.

### 4.5 [`TreeViewProviders`](../extension/src/ui/TreeViewProviders.ts) — 3개 TreeView

| TreeView | Provider | 내용 |
|:---|:---|:---|
| **Active Subagents** | `ActiveSubagentsProvider` | Bridge·Scout·Reviewer·Tester·DeepAnalyzer·CIM Monitor 노드 (30초 health check) |
| **YOLO History** | `YoloHistoryProvider` | `~/.zoo-code/yocto/` 디렉토리 기반 세션 목록, 우클릭 → Rewind |
| **Session Resume** | `SessionResumeProvider` | Crow recall + 로컬 파일 + yocto 폴더 스캔 3단계 fallback. 세션 요약·주요 결정·수정 파일·미완료 작업 표시 |

### 4.6 [`VisualVibePanels`](../extension/src/visual/VisualVibePanels.ts) — 시각 협업

| 패널 | 동기화 방식 | 설명 |
|:---|:---|:---|
| **Whiteboard** | `fs.watchFile` (200ms) | AI → Bridge → `~/.vibezoo-whiteboard.json` → 파일 변경 감지 → 자동 렌더링 |
| **UI Preview** | `fs.watchFile` | AI → Bridge → `~/.vibezoo-ui-action.json` → 자동 열기 + 렌더링 |
| **Diagram** | 수동 오픈 | Mermaid.js / D3.js Webview |

### 4.7 Safety Net — 3계층 안전망

```
LAYER 1: Prevention (Config 기반)
├── .yoloignore 파일 → FileGuard가 감시
└── Zoo Code MCP 도구 권한 설정

LAYER 2: Real-time Detection & Recovery (VibeZoo)
├── YoctoManager: FileSystemWatcher + fs.copyFileSync (200ms debounce)
├── FileGuard: .yoloignore 매칭 파일 변경 → 즉시 yocto 복구
└── GitStashManager: YOLO 진입/퇴장 시 git stash 자동화

LAYER 3: Post-hoc Recovery & Auto-Healing
├── instantRewind(): yocto 백업 → 전체 복구 (<500ms)
├── FixLoopManager: 빌드 실패 → LLM 수정 → 재빌드 (최대 3회)
└── CIM: 파일 저장 → tsc 자동 검사 → 에러 발생 시 Auto-Fix
```

### 4.8 Crow Memory 연동 아키텍처

```
Zoo Code (Crow Memory 내장, :9020)
    │
    ├── Zoo Code LLM → crow_recall / crow_ingest 직접 호출
    │
    └── VibeZoo MCP Bridge (:9027)
        ├── try_crow_ingest() → Crow /ingest
        ├── try_crow_recall() → Crow /recall
        └── Crow 연결 실패 → 무시 (도구 정상 동작)
```

**핵심 원칙**: Crow Memory는 Zoo Code의 내장 시스템이다. VibeZoo는 Crow를 spawn하지 않고, MCP Bridge의 `try_crow_ingest()` / `try_crow_recall()` 래퍼로 선택적 연동만 한다. Crow 연결 실패 시에도 VibeZoo의 모든 기능은 정상 동작한다.

---

## 5. 데이터 흐름

### 5.1 Autonomous Fix Loop

```
파일 저장 → BuildFeedback → FixLoopManager.onBuildFailure()
    │
    ├── ~/.vibezoo-fix-request.json 기록
    ├── StatusBar: "$(warning) 빌드 실패 — [자동 수정]"
    │
    ▼
LLM (Zoo Code):
    auto_fix_status() → 에러 정보 + Crow 과거 패턴 수신
    search_codebase()  → 관련 코드 검색
    review_code()      → 문제 파일 분석
    파일 수정 (edit)
    retry_build()      → 빌드 결과 확인
    │
    ├── 성공 → FixLoopManager.markResolved()
    └── 실패 → oscillation 체크 → 재시도 or abandoned
```

### 5.2 Whiteboard 협업

```
AI (Zoo Code):
    draw_on_whiteboard(commands) → Bridge(:9027) → ~/.vibezoo-whiteboard.json
                                                          │
VibeZoo Extension:                                        │
    VisualVibePanels._startWatching()                     │
    → fs.watchFile (200ms)                                │
    → JSON 변경 감지                                       │
    → Whiteboard Webview로 postMessage                     │
    → Fabric.js 캔버스에 렌더링                            │
                                                          │
사용자:                                                    │
    화이트보드에서 그림/텍스트 수정                          │
    → get_whiteboard_state() ← AI가 확인                   │
    → check_intervention() ← Fix Loop에서 확인              │
```

### 5.3 MCP Bridge ↔ Zoo Code 연동

```
1. VibeZoo Extension.activate()
2. SubagentManager.spawnBridge()
   → child_process.spawn("python", ["vibezoo_mcp_bridge.py", "--port", "9027"])
3. Bridge health check → OK
4. autoConfigureMCP()
   → .roo/mcp.json에 {"vibezoo": {"url": "http://localhost:9027/sse"}} 추가
5. Zoo Code 재시작 시 MCP 설정 로드 → VibeZoo Bridge 연결
6. LLM → MCP tool call → Bridge → Python 도구 실행 → 결과 반환
```

---

## 6. MCP 도구 전체 목록 (31개)

| # | 도구명 | 카테고리 | AST | 설명 |
|:---:|:---|:---|:---:|:---|
| 1 | `search_codebase` | Scout | ✅ | tree-sitter AST 기반 구조 검색 + regex fallback |
| 2 | `find_references` | Scout | — | 심볼 참조 검색 |
| 3 | `summarize_architecture` | Scout | — | 프로젝트 구조·기술 스택·파일 통계 |
| 4 | `review_code` | Reviewer | — | 줄 길이·TODO·console.log 감지 |
| 5 | `check_quality` | Reviewer | — | ESLint·go vet 연동 |
| 6 | `analyze_call_graph` | DeepAnalyzer | ✅ | AST call_expression 기반 호출 그래프 |
| 7 | `map_dependencies` | DeepAnalyzer | ✅ | AST import 추출 + Tarjan 순환 참조 탐지 |
| 8 | `extract_patterns` | DeepAnalyzer | — | async/try-catch/arrow 등 패턴 카운팅 |
| 9 | `reverse_engineer` | DeepAnalyzer | ✅ | AST 필드 추출 → Mermaid ERD·OpenAPI 생성 |
| 10 | `generate_tests` | Tester | — | 함수 감지 → 테스트 템플릿 생성 |
| 11 | `analyze_coverage` | Tester | — | vitest coverage 실행 |
| 12 | `draw_on_whiteboard` | Whiteboard | — | Fabric.js 드로잉 명령 전송 |
| 13 | `get_whiteboard_state` | Whiteboard | — | 사용자 수정 내용 조회 |
| 14 | `open_whiteboard` | Whiteboard | — | 화이트보드 패널 열기 |
| 15 | `capture_screen` | Whiteboard | — | 화면 캡처 → 화이트보드 |
| 16 | `open_ui_preview` | UI Preview | — | React/Vue 실시간 미리보기 |
| 17 | `auto_fix_status` | Fix Loop | — | Fix request 조회 + Crow 과거 패턴 |
| 18 | `retry_build` | Fix Loop | — | 빌드 재실행 + 결과 기록 |
| 19 | `check_intervention` | Fix Loop | — | Whiteboard·채팅 개입 확인 |
| 20 | `review_project` | 통합 (Q1) | — | search + review + quality + patterns |
| 21 | `find_bugs` | 통합 (Q1) | — | patterns + suspicious 검색 + Crow recall |
| 22 | `suggest_refactor` | 통합 (Q1) | — | deps + patterns + callgraph |
| 23 | `generate_docs` | 통합 (Q1) | — | arch + reverse + whiteboard diagram |
| 24 | `explain_code` | 분석 (M3-A) | ✅ | AST 컨텍스트 기반 코드 설명 |
| 25 | `analyze_changes` | 분석 (M3-B) | — | git diff 분석 + Crow context |
| 26 | `review_pr` | 분석 (M3-B) | — | diff + review_code 통합 PR 리뷰 |
| 27 | `refactor_across_files` | 분석 (M3-C) | — | 패턴 검색 → 변경 제안서 |
| 28 | `learn_project` | 지식 (M3-D) | — | arch+patterns+deps → Crow 축적 |
| 29 | `recall_project` | 지식 (M3-D) | — | Crow에서 프로젝트 지식 회상 |
| 30 | `learn_preference` | 선호도 (M3-E) | — | 사용자 코딩 선호도 저장 |
| 31 | `get_preferences` | 선호도 (M3-E) | — | 저장된 선호도 조회 |

---

## 7. 기술 스택

| 구성요소 | 기술 | 설명 |
|:---|:---|:---|
| **Extension** | TypeScript 5.x | VS Code Extension API |
| **MCP Bridge** | Python 3.x + FastMCP | SSE transport, 포트 9027 |
| **AST 파싱** | tree-sitter + tree-sitter-typescript | TS/JS 구조 분석 (미설치 시 regex fallback) |
| **통신** | MCP/SSE (JSON-RPC 2.0) | Zoo Code ↔ Bridge |
| **화이트보드** | Fabric.js | HTML5 Canvas 드로잉 |
| **UI Preview** | iframe sandbox + Babel standalone | React/Vue 실시간 렌더링 |
| **다이어그램** | Mermaid.js + D3.js | ERD, 호출 그래프, 의존성 지도 |
| **Crow Memory** | Zoo Code 내장 | Python FastMCP, 포트 9020 |

---

## 8. 설계 제약 및 우회 전략

| 제약 | 원인 | 우회 전략 | 손실 |
|:---|:---|:---|:---|
| LLM 메시지 파이프라인 가로채기 불가 | Extension 간 내부 통신 제한 | `[Config]` custom_modes.yaml + `[Crow]` tool call + StatusBar 컨텍스트 알림 | ~10% |
| Custom Mode 자동 전환 불가 | Zoo Code 모드 상태 외부 변경 불가 | StatusBar "권장 모드" 제안 (1클릭) | 3클릭→1클릭 |
| 파일 쓰기 사전 차단 불가 | WorkspaceEdit intercept 불가 | FileSystemWatcher 사후 감지 + yocto 즉시 복구 (0.3초) | 예방→치료 |
| Zoo Code 채팅 @mention 불가 | 채팅 UI 외부 확장 불가 | VS Code Chat Participant API + MCP tool call 기반 라우팅 | 채팅 통합→별도 채널 |

---

## 9. 핵심 성능 메트릭

| 지표 | 목표 | 현재 (v0.12.0) |
|:---|:---:|:---:|
| Extension 활성화 시간 | < 500ms | Lazy Init + fs.watchFile 적용 |
| yocto 단일 파일 복구 | < 100ms | fs.copyFileSync |
| yocto 10개 파일 복구 | < 500ms | 순차 복사 |
| 보호 파일 변경 감지→복구 | < 500ms | FileSystemWatcher + yocto |
| Fix Loop 타임아웃 | 120초 | FixLoopManager.SESSION_TIMEOUT_MS |
| CIM tsc 검사 | < 60초 | npx tsc --noEmit |
| Whiteboard 동기화 | 200ms debounce | fs.watchFile |
| Active Subagents health check | 30초 간격 | setInterval + /health |

---

## 10. 결론

VibeZoo v0.12.0은 Zoo Code 소스 코드를 **단 한 줄도 수정하지 않고** 다음을 달성했다:

- **31개 MCP 도구**: tree-sitter AST 기반 시맨틱 코드 분석
- **자율 수정 루프**: 빌드 실패 → LLM 분석 → 수정 → 재빌드 (oscillation 감지 + HITL)
- **지속 감시 (CIM)**: 파일 저장 → 자동 tsc 검사 → Auto-Fix
- **통합 안전망**: yocto 백업 + File Guard + Git Stash + Instant Rewind
- **3개 TreeView**: Active Subagents, YOLO History, Session Resume (Crow·로컬·yocto 3중 fallback)
- **통합 StatusBar**: Bridge·Crow·YOLO·CIM 상태를 단일 항목에 표시
- **시각 협업**: Whiteboard (fs.watchFile), UI Preview

**핵심 원칙**:
1. Zoo Code 소스 수정 제로 — 모든 기능은 VibeZoo Extension + MCP Bridge + Config로 구현
2. Crow는 Zoo Code 내장 시스템 — VibeZoo는 감지·연동만, Crow 없이도 모든 기능 정상 동작
3. Human-in-the-Loop — 자동화는 사용자가 통제 가능한 범위 내에서
4. tree-sitter AST 우선, 실패 시 regex fallback — Windows 환경 호환성 보장
