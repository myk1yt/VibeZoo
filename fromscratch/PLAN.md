# VibeZoo 구현 계획 — v0.12.0

> **작성일**: 2026-05-27 (v0.10.0 초안) → 2026-05-27 (v0.12.0 전면 개정)
> **기준 버전**: v0.12.0
> **기반 문서**: [Architecture.md](./Architecture.md), [ROADMAP.md](./ROADMAP.md), [JOURNAL.md](./JOURNAL.md)

---

## 0. 버전 히스토리

| 버전 | 날짜 | 주요 변경 | 비고 |
|:---|:---|:---|:---|
| **v0.10.0** | 2026-05-27 오전 | 초기 구현 완료 (26개 파일). Go MCP 서버 4개. AutoBuildFix 빈 루프. | 설계 → 구현 |
| **v0.10.0** | 2026-05-27 오후 | Python MCP 브릿지 전환. Go 서버 전부 제거. `vibezoo_mcp_bridge.py` 단일 파일. | Go→Python |
| **v0.10.0** | 2026-05-27 오후 | AI 자동 Whiteboard + UI Preview 연동. `draw_on_whiteboard` 등 4개 MCP 도구 추가. | `setInterval` 폴링 |
| **v0.10.0** | 2026-05-27 오후 | MCP 자동 설정 수정. Crow 중복 추가 제거. | 설정 안정화 |
| **v0.10.0** | 2026-05-27 최종 | Go 파일 정리(1,074줄 제거). SSE 경로 `/sse` 수정. VSIX 빌드 완료. | 클린업 |
| **v0.11.1** | 2026-05-27 | 30+ 버그 수정. 기능 골격 구현 완료. | 안정화 |
| **v0.12.0** | 2026-05-27 | Quick Wins 5종 + M1(Autonomous Fix Loop, Scout AST, Reviewer ESLint, Crow error patterns) + M3(explain_code, analyze_changes, review_pr, refactor_across_files, learn/recall_project, learn/get_preferences, CIM). TreeView 3종, StatusBar 통합, `fs.watchFile` 전환, Lazy Init. **31개 MCP 도구**. | |
| **v0.13.0** | 2026-05-28 (현재) | Phase 0~(SelfCheck, NotificationThrottle, FileGuard fix) + Phase 1~6. 화이트보드 안정화 + 4대 개선(I_instability, atomicCopy, hydrateContext, Crow backoff) + Virtual Subagent(SubagentPool+5 MCP 도구) + Intent-to-Code Bridge(화이트보드→TypeScript) + 전면 NotificationThrottle 적용 + 문서/GitHub/VSIX. **36개 MCP 도구**. | 현재 |

---

## 1. Tech Stack (확정)

| 구성요소 | 언어/기술 | 설명 |
|:---|:---|:---|
| **VibeZoo Extension** | TypeScript 5.x | VS Code Extension API. `onStartupFinished` 활성화. |
| **MCP Bridge** | Python 3.x + FastMCP | 단일 파일 [`vibezoo_mcp_bridge.py`](../mcp-servers/vibezoo_mcp_bridge.py). SSE transport, 포트 9027. |
| **AST 파싱** | tree-sitter (Python 바인딩) | TypeScript/JavaScript 구조 분석. 미설치 시 regex fallback. |
| **Crow Memory** | Zoo Code 내장 | Python FastMCP, 포트 9020. VibeZoo는 감지·연동만. |
| **통신 프로토콜** | MCP/SSE (JSON-RPC 2.0) | Zoo Code ↔ VibeZoo MCP Bridge |
| **화이트보드** | Fabric.js | HTML5 Canvas, `fs.watchFile` 이벤트 동기화 |
| **UI Preview** | iframe sandbox + Babel standalone | React/Vue 실시간 렌더링 |
| **다이어그램** | Mermaid.js + D3.js | ERD, 호출 그래프 시각화 |

---

## 2. 파일 구조 (실제)

```
VibeZoo_forZoocode/
├── extension/                        # VS Code Extension (TypeScript, 16개 소스 파일)
│   ├── package.json                  # v0.12.0, 26개 명령어, 18개 설정, 3개 TreeView
│   ├── tsconfig.json
│   └── src/
│       ├── extension.ts              # 진입점 (663줄, activate/deactivate)
│       ├── context/
│       │   └── ContextIntelligence.ts # 4개 클래스 (217줄)
│       ├── crow/
│       │   └── CrowServerManager.ts  # Crow 감지 전용
│       ├── flow/
│       │   ├── BuildFeedback.ts      # 빌드 결과 → FixLoopManager 연동
│       │   ├── BuildTaskProvider.ts  # Silent Build Task
│       │   ├── ProjectDetector.ts    # 프로젝트 타입 감지
│       │   └── ProjectTreeScanner.ts # 트리 스캔
│       ├── orchestra/
│       │   ├── FixLoopManager.ts     # 자율 수정 루프 + CIM (566줄)
│       │   ├── MentionRouter.ts      # @mention 라우팅
│       │   └── SubagentManager.ts    # Bridge spawn·관리
│       ├── safety/
│       │   ├── FileGuard.ts          # .yoloignore 감시
│       │   ├── GitStashManager.ts    # YOLO Git Stash
│       │   └── YoctoManager.ts       # yocto 백업·복구
│       ├── types/
│       │   └── index.ts              # 공통 타입 정의
│       ├── ui/
│       │   ├── StatusBarManager.ts   # 통합 StatusBar (142줄)
│       │   └── TreeViewProviders.ts  # 3개 Provider (443줄)
│       └── visual/
│           └── VisualVibePanels.ts   # Whiteboard + UI Preview + Diagram
│
├── mcp-servers/
│   └── vibezoo_mcp_bridge.py         # 31개 MCP 도구 (2,331줄)
│
├── fromscratch/                      # 설계 문서
│   ├── Architecture.md               # 아키텍처 문서
│   ├── PLAN.md                       # ← 이 문서
│   ├── ROADMAP.md                    # 성능 극대화 로드맵
│   └── JOURNAL.md                    # 개발 일지
│
├── plans/
│   └── autonomous-fix-loop.md        # FixLoopManager 상세 설계 (701줄)
│
└── templates/
    ├── yoloignore
    ├── zoo-config.json
    └── vscode-settings.json
```

---

## 3. 구현 완료 항목

### 3.1 Phase 0: Foundation — 완료 ✅

| # | 항목 | 파일 | 상태 |
|:---:|:---|:---|:---:|
| P0-1 | Extension 프로젝트 생성 | `extension/package.json`, `extension/tsconfig.json` | ✅ |
| P0-2 | CrowServerManager (Zoo Code Crow 감지) | [`extension/src/crow/CrowServerManager.ts`](../extension/src/crow/CrowServerManager.ts) | ✅ |
| P0-3 | StatusBar 통합 | [`extension/src/ui/StatusBarManager.ts`](../extension/src/ui/StatusBarManager.ts) | ✅ |
| P0-4 | 디렉토리 구조 자동 생성 (`~/.zoo-code/yocto/`, `.zoo/`) | [`extension/src/extension.ts`](../extension/src/extension.ts:728) | ✅ |
| P0-5 | 템플릿 자동 복사 (`.yoloignore`, `.zoo/config.json`, `.vscode/settings.json`) | [`extension/src/extension.ts`](../extension/src/extension.ts:742) | ✅ |
| P0-6 | MCP 자동 설정 (`autoConfigureMCP()`) | [`extension/src/extension.ts`](../extension/src/extension.ts:684) | ✅ |
| P0-7 | `VibeZoo: Verify Foundation` 진단 명령어 | [`extension/src/extension.ts`](../extension/src/extension.ts:238) | ✅ |
| P0-8 | `VibeZoo: Reconnect to Crow Memory` | [`extension/src/extension.ts`](../extension/src/extension.ts:271) | ✅ |

### 3.2 Wave 1: Unbreakable Flow — 완료 ✅

| # | 항목 | 파일 | 상태 |
|:---:|:---|:---|:---:|
| W1-1 | Silent Build Task Provider | [`extension/src/flow/BuildTaskProvider.ts`](../extension/src/flow/BuildTaskProvider.ts) | ✅ |
| W1-2 | BuildFeedback — 빌드 결과 수집 → Crow ingest | [`extension/src/flow/BuildFeedback.ts`](../extension/src/flow/BuildFeedback.ts) | ✅ |
| W1-3 | Project Auto-Detector → 모드 제안 | [`extension/src/flow/ProjectDetector.ts`](../extension/src/flow/ProjectDetector.ts) | ✅ |
| W1-4 | ProjectTreeScanner + 캐싱 | [`extension/src/flow/ProjectTreeScanner.ts`](../extension/src/flow/ProjectTreeScanner.ts) | ✅ |
| W1-5 | `VibeZoo: Scan Project Tree` 명령어 | [`extension/src/extension.ts`](../extension/src/extension.ts:225) | ✅ |

### 3.3 Wave 2: Fearless YOLO — 완료 ✅

| # | 항목 | 파일 | 상태 |
|:---:|:---|:---|:---:|
| W2-1 | YoctoManager — 실시간 파일 백업 (FileSystemWatcher) | [`extension/src/safety/YoctoManager.ts`](../extension/src/safety/YoctoManager.ts) | ✅ |
| W2-2 | Instant Rewind (`Ctrl+Shift+Z`) | [`extension/src/extension.ts`](../extension/src/extension.ts:185) | ✅ |
| W2-3 | FileGuard — `.yoloignore` 감시·복구 | [`extension/src/safety/FileGuard.ts`](../extension/src/safety/FileGuard.ts) | ✅ |
| W2-4 | GitStashManager — YOLO 진입/퇴장 자동화 | [`extension/src/safety/GitStashManager.ts`](../extension/src/safety/GitStashManager.ts) | ✅ |
| W2-5 | YOLO History TreeView | [`extension/src/ui/TreeViewProviders.ts`](../extension/src/ui/TreeViewProviders.ts:239) | ✅ |
| W2-6 | `VibeZoo: Toggle YOLO Mode` | [`extension/src/extension.ts`](../extension/src/extension.ts:210) | ✅ |

### 3.4 Wave 3: Explain-Less — 완료 ✅

| # | 항목 | 파일 | 상태 |
|:---:|:---|:---|:---:|
| W3-1 | ContextIndicator — Crow freshness | [`extension/src/context/ContextIntelligence.ts`](../extension/src/context/ContextIntelligence.ts:10) | ✅ |
| W3-2 | ExplainLessSuggestor — 반복 설명 패턴 감지 | [`extension/src/context/ContextIntelligence.ts`](../extension/src/context/ContextIntelligence.ts:35) | ✅ |
| W3-3 | SessionResume — TreeView 기반 세션 복원 (Crow·로컬·yocto 3중 fallback) | [`extension/src/context/ContextIntelligence.ts`](../extension/src/context/ContextIntelligence.ts:72) | ✅ |
| W3-4 | EmotionalDetector — 감정 신호 분석 (연속 거절 감지) | [`extension/src/context/ContextIntelligence.ts`](../extension/src/context/ContextIntelligence.ts:177) | ✅ |
| W3-5 | Session Resume TreeView + `Ctrl+Shift+R` | [`extension/src/ui/TreeViewProviders.ts`](../extension/src/ui/TreeViewProviders.ts:331) | ✅ |

### 3.5 Wave 4: Orchestra of One — 부분 완료

| # | 항목 | 파일 | 상태 |
|:---:|:---|:---|:---:|
| W4-1 | SubagentManager — Python Bridge spawn | [`extension/src/orchestra/SubagentManager.ts`](../extension/src/orchestra/SubagentManager.ts) | ✅ |
| W4-2 | MentionRouter — @mention 라우팅 | [`extension/src/orchestra/MentionRouter.ts`](../extension/src/orchestra/MentionRouter.ts) | ✅ |
| W4-3 | Active Subagents TreeView (Bridge health check) | [`extension/src/ui/TreeViewProviders.ts`](../extension/src/ui/TreeViewProviders.ts:29) | ✅ |
| W4-4 | Orchestra Dashboard (`openDashboard`) | [`extension/src/extension.ts`](../extension/src/extension.ts:302) | ✅ |
| W4-5 | 개별 Go MCP 서버 (Scout/Reviewer/Tester/Deep) | 삭제됨 | ❌ (Python 단일 브릿지로 대체) |

### 3.6 Wave 5: Visual Vibe — 완료 ✅

| # | 항목 | 파일 | 상태 |
|:---:|:---|:---|:---:|
| W5-1 | Whiteboard (Fabric.js + `fs.watchFile`) | [`extension/src/visual/VisualVibePanels.ts`](../extension/src/visual/VisualVibePanels.ts) | ✅ |
| W5-2 | UI Preview (iframe sandbox) | [`extension/src/visual/VisualVibePanels.ts`](../extension/src/visual/VisualVibePanels.ts) | ✅ |
| W5-3 | Diagram Webview (Mermaid.js + D3.js) | [`extension/src/visual/VisualVibePanels.ts`](../extension/src/visual/VisualVibePanels.ts) | ✅ |
| W5-4 | `capture_screen` MCP 도구 | [`mcp-servers/vibezoo_mcp_bridge.py`](../mcp-servers/vibezoo_mcp_bridge.py:327) | ✅ |
| W5-5 | `draw_on_whiteboard`, `get_whiteboard_state`, `open_whiteboard` | [`mcp-servers/vibezoo_mcp_bridge.py`](../mcp-servers/vibezoo_mcp_bridge.py:1069) | ✅ |
| W5-6 | `open_ui_preview` MCP 도구 | [`mcp-servers/vibezoo_mcp_bridge.py`](../mcp-servers/vibezoo_mcp_bridge.py:1109) | ✅ |

### 3.7 Wave 6: Deep Analysis — 완료 ✅

| # | 항목 | 파일 | 상태 |
|:---:|:---|:---|:---:|
| W6-1 | `analyze_call_graph` — tree-sitter AST 호출 그래프 | [`mcp-servers/vibezoo_mcp_bridge.py`](../mcp-servers/vibezoo_mcp_bridge.py:663) | ✅ |
| W6-2 | `map_dependencies` — AST 순환 참조 탐지 | [`mcp-servers/vibezoo_mcp_bridge.py`](../mcp-servers/vibezoo_mcp_bridge.py:741) | ✅ |
| W6-3 | `extract_patterns` — 코드 패턴 마이닝 | [`mcp-servers/vibezoo_mcp_bridge.py`](../mcp-servers/vibezoo_mcp_bridge.py:821) | ✅ |
| W6-4 | `reverse_engineer` — AST 기반 API·ERD·OpenAPI 생성 | [`mcp-servers/vibezoo_mcp_bridge.py`](../mcp-servers/vibezoo_mcp_bridge.py:880) | ✅ |

### 3.8 Quick Wins 5종 (M0) — 완료 ✅

| # | 항목 | 내용 | 상태 |
|:---:|:---|:---|:---:|
| Q1 | 시나리오 통합 커맨드 | `review_project`, `find_bugs`, `suggest_refactor`, `generate_docs` 4개 MCP 도구 | ✅ |
| Q2 | `setInterval` → `fs.watchFile` | Whiteboard·UI Preview 파일 감시 이벤트 기반 전환 | ✅ |
| Q3 | StatusBar 통합 | 1개 통합 항목 (`$(zap) VibeZoo`) + 알람 최소화 | ✅ |
| Q4 | Lazy Init | YoctoManager·FixLoopManager·VisualVibePanels 지연 초기화 | ✅ |
| Q5 | 원클릭 액션 | 우클릭 컨텍스트 메뉴 (Review·Find Bugs·Refactor·Docs) | ✅ |

### 3.9 M1: Autonomous Alpha (1개월 마일스톤) — 완료 ✅

| # | 항목 | 내용 | 상태 |
|:---:|:---|:---|:---:|
| A1.1 | **FixLoopManager** | 8개 상태 머신, oscillation 감지, 파일 기반 LLM 통신 | ✅ |
| A1.2 | `auto_fix_status` MCP 도구 | Fix request 조회 + Crow 과거 에러 패턴 | ✅ |
| A1.3 | `retry_build` MCP 도구 | 빌드 재실행 + 결과 기록 + Crow ingest | ✅ |
| A1.4 | `check_intervention` MCP 도구 | Whiteboard·채팅 개입 확인 | ✅ |
| A1.5 | BuildFeedback → FixLoopManager 연동 | 빌드 실패 시 자동 Fix Loop 트리거 | ✅ |
| A1.6 | HITL 개입 커맨드 | `pauseFixLoop`, `resumeFixLoop`, `abortFixLoop` | ✅ |
| A1.7 | Scout tree-sitter AST 검색 | `search_codebase` AST 구조 검색 | ✅ |
| A1.8 | Reviewer ESLint 통합 | `check_quality` ESLint·go vet 연동 | ✅ |
| A1.9 | Crow 에러 패턴 학습 | `auto_fix_status`·`retry_build` Crow bug 레지스터 연동 | ✅ |
| A1.10 | `AutoBuildFix` 제거 | [`extension/src/safety/AutoBuildFix.ts`]() → FixLoopManager로 대체 | ✅ |

### 3.10 M3: Intelligence (3개월 마일스톤) — 조기 완료 ✅

| # | 항목 | 내용 | 상태 |
|:---:|:---|:---|:---:|
| M3-A | `explain_code` + `VibeZoo: Explain Code` | AST 컨텍스트 기반 코드 설명 | ✅ |
| M3-B | `analyze_changes` + `review_pr` | git diff 분석 + PR 리뷰 | ✅ |
| M3-C | `refactor_across_files` + `VibeZoo: Refactor Across Files` | 멀티 파일 리팩토링 제안 | ✅ |
| M3-D | `learn_project` + `recall_project` | 프로젝트 지식 Crow 축적·회상 | ✅ |
| M3-E | `learn_preference` + `get_preferences` | 사용자 코딩 선호도 학습·조회 | ✅ |
| M3-F | CIM (Continuous Improvement Mode) | `startWatching`·`stopWatching` — 파일 저장 시 tsc 자동 검사 | ✅ |

---

## 4. 남은 작업 (ROADMAP.md 기반)

### 4.1 우선순위 매트릭스

> **평가 기준**: 난이도(1~10), 임팩트(1~10), 소요(S/M/L/XL)
> **Priority Score** = Impact × 0.5 + (11 − Difficulty) × 0.3

| # | 항목 | 축 | 난이도 | 임팩트 | 소요 | 점수 | 상태 |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---|
| 1 | **Self-healing 모니터링** | 1 | 7 | 7 | L | 5.7 | 🔜 예정 |
| 2 | **프로젝트 지식 축적 고도화** | 3 | 5 | 5 | L | 5.3 | 🔜 예정 |
| 3 | **메모리 누수 제거** | 4 | 6 | 5 | M | 6.2 | 🔜 예정 |
| 4 | **좌측 사이드바 단일화** | 5 | 5 | 5 | M | 5.3 | 🔜 예정 |
| 5 | **크로스 세션 컨텍스트 고도화** | 3 | 5 | 7 | M | 6.3 | 🔜 예정 |
| 6 | **사용자 선호도 학습 고도화** | 3 | 4 | 6 | L | 5.6 | 🔜 예정 |
| 7 | **DeepAnalyzer AST 호출 그래프 개선** | 2 | 8 | 8 | L | 6.4 | 진행 중 |
| 8 | **신규 MCP 도구 4종** (explain_code, suggest_refactor, find_bugs, analyze_pr) | 2 | 5 | 7 | M | 6.3 | ✅ 완료 (M3에서) |
| 9 | **활성화 시간 < 500ms 최적화** | 4 | 4 | 6 | S | 6.4 | ✅ 완료 (Q4) |
| 10 | **전체 통합 안정화** | 5 | 6 | 8 | XL | 5.5 | 진행 중 |

### 4.2 마일스톤 로드맵

```mermaid
gantt
    title VibeZoo 마일스톤 로드맵 (v0.12.0 기준)
    dateFormat  YYYY-MM-DD
    axisFormat  %m/%d

    section 완료 - Foundation
    Phase 0 - Extension 골격       :done, p0, 2026-05-27, 1d
    Wave 1 - Unbreakable Flow      :done, w1, 2026-05-27, 1d
    Wave 2 - Fearless YOLO         :done, w2, 2026-05-27, 1d

    section 완료 - Intelligence
    Wave 3 - Explain-Less          :done, w3, 2026-05-27, 1d
    Wave 5 - Visual Vibe           :done, w5, 2026-05-27, 1d
    Wave 6 - Deep Analysis         :done, w6, 2026-05-27, 1d

    section 완료 - Quick Wins + M1 + M3
    Q1-Q5 - Quick Wins 5종         :done, qw, 2026-05-27, 1d
    M1 - Autonomous Alpha          :done, m1, 2026-05-27, 1d
    M3 - Intelligence              :done, m3, 2026-05-27, 1d

    section 진행 중
    성능 최적화 + 안정화           :active, opt, 2026-05-28, 14d
    메모리 누수 제거               :mem, 2026-05-29, 7d
    DeepAnalyzer AST 개선          :da, 2026-05-30, 14d

    section M6 - Self-evolving
    Self-healing 모니터링          :sh, 2026-06-05, 21d
    프로젝트 지식 축적 고도화      :pk, 2026-06-10, 14d
    크로스 세션 컨텍스트           :cs, 2026-06-15, 10d
    사용자 선호도 학습 고도화      :up, 2026-06-15, 14d

    section 안정화
    전체 통합 안정화               :st, 2026-06-20, 60d
```

### 4.3 마일스톤 상세

| 마일스톤 | 상태 | 핵심 성과 | 성공 지표 |
|:---|:---:|:---|:---|
| **M0: Quick Wins** | ✅ 완료 | 5대 Quick Win. 시나리오 커맨드·성능·UX 개선 | 활성화 < 500ms, StatusBar 통합 |
| **M1: Autonomous Alpha** | ✅ 완료 | Fix Loop + Scout AST + Reviewer ESLint + Crow 에러 학습 | HITL 기반 자율 수정 루프 |
| **M3: Intelligence** | ✅ 완료 | explain_code, analyze_changes, review_pr, refactor_across_files, learn/recall_project, learn/get_preferences, CIM | 31개 MCP 도구, tree-sitter AST 분석 |
| **M6: Self-evolving** | 🔜 예정 | Self-healing + 프로젝트 지식 축적 + 전체 안정화 | 수동 개입 없이 60%+ 이슈 자동 해결 |

### 4.4 병렬 트랙

| 트랙 | 축 | 현재 상태 | 다음 단계 |
|:---|:---|:---|:---|
| **트랙 A: 도구 지능** | MCP 도구 | ✅ v0.12.0 완료 | DeepAnalyzer AST 고도화, 신규 언어 지원 |
| **트랙 B: 자율화** | Agent | ✅ M1 완료, M3 CIM 완료 | Self-healing 모니터링, 완전 자율화 |
| **트랙 C: 기억** | Crow | ✅ M3-D/E 완료 | 프로젝트 지식 축적 고도화, 크로스 세션 컨텍스트 |
| **트랙 D: 품질** | 성능·UX | ✅ Q2-Q5 완료 | 메모리 누수 제거, 활성화 시간 추가 단축 |
| **트랙 E: 안정화** | 통합 | 진행 중 | 전체 통합 테스트, 에지 케이스 대응 |

---

## 5. 설계 원칙 (VibeZoo 약속)

1. **Zoo Code 소스 수정 제로**: 모든 기능은 VibeZoo Extension + MCP Bridge + Config 변경만으로 작동한다.
2. **Crow는 Zoo Code 내장**: VibeZoo는 Crow를 spawn하지 않는다. 감지·연동만 수행하며, Crow 없이도 모든 기능이 정상 동작한다.
3. **Human-in-the-Loop**: 자동화는 사용자가 통제 가능한 범위 내에서. Fix Loop에는 pause/resume/abort, CIM에는 start/stop 커맨드가 항상 제공된다.
4. **tree-sitter AST 우선, regex fallback**: Windows 환경에서 tree-sitter 미설치 시에도 모든 도구가 정상 동작한다.
5. **가벼움**: Extension은 TypeScript 단일 컴파일, Bridge는 Python 단일 파일. 설치 마찰 최소화.
6. **실제 사용 경험 우선**: "도구 상자"가 아니라 "시나리오" 중심 설계. 사용자가 무슨 도구를 언제 써야 하는지 알 필요 없이, 자연어로 요청하면 된다.

---

## 6. 위험 요소 및 대응

| # | 리스크 | 확률 | 영향 | 대응책 | 상태 |
|:---|:---|:---:|:---:|:---|:---:|
| R1 | tree-sitter Python 바인딩 Windows 설치 이슈 | 30% | 중 | 사전 빌드 wheel 포함, 실패 시 regex fallback 유지 | ✅ 대응 완료 |
| R2 | Autonomous Fix Loop가 잘못된 수정으로 코드 망가뜨림 | 25% | 치명적 | HITL 필수 + yocto 백업 자동 생성 + oscillation 감지 | ✅ 대응 완료 |
| R3 | Crow Memory 서버(9020) 불안정 | 20% | 하 | 모든 Crow 호출 3초 타임아웃 + 실패해도 VibeZoo 정상 작동 | ✅ 대응 완료 |
| R4 | Zoo Code 업데이트로 MCP 프로토콜 변경 | 15% | 중 | MCP 표준 준수 + 버전 호환성 테스트 | ⚠️ 지속 모니터링 |
| R5 | 사용자가 여전히 도구를 안 씀 | 40% | 치명적 | 시나리오 커맨드 + StatusBar 액션 버튼 + 원클릭 컨텍스트 메뉴 | ✅ 대응 완료 |

---

## 7. 성공 지표 (KPI)

| 지표 | M0 (완료) | M1 (완료) | M3 (완료) | M6 (목표) |
|:---|:---:|:---:|:---:|:---:|
| **MCP 도구 수** | 16개 | 23개 | 31개 | 35개+ |
| **자율 해결률** (빌드 에러) | 0% | 40%+ (HITL) | 60%+ (CIM) | 80%+ |
| **Extension 활성화 시간** | < 500ms | < 500ms | < 500ms | < 300ms |
| **Crow 과거 해결 재활용률** | 0% | 10%+ | 30%+ | 50%+ |
| **StatusBar 항목 수** | 1개 (통합) | 1개 | 1개 | 1개 |
| **TreeView 수** | 3개 | 3개 | 3개 | 3개 |
| **VS Code 명령어 수** | 10개 | 18개 | 26개 | 30개+ |

---

## 8. 다음 우선 작업 (M6 준비)

| 순서 | 항목 | 예상 완료 | 설명 |
|:---:|:---|:---|:---|
| 1 | **Self-healing 모니터링** | M6 | CIM을 넘어 런타임 에러·린트·타입 에러까지 자동 감지·수정 |
| 2 | **메모리 누수 제거** | 1주 | `VisualVibePanels` dispose 확인, `FileSystemWatcher` subscriptions 정리 |
| 3 | **프로젝트 지식 축적 고도화** | M6 | `learn_project` 결과의 장기 보존·버전 관리·자동 만료 |
| 4 | **크로스 세션 컨텍스트** | M6 | 세션 간 작업 목표·진행 상황 자동 복원 |
| 5 | **DeepAnalyzer AST 다중 언어 지원** | M6 | Python, Go, Rust까지 tree-sitter 분석 확장 |
| 6 | **전체 통합 안정화** | M6 | 에지 케이스 테스트, 오류 복원력 강화, 문서화 |

---

> **핵심 원칙 되새김**:
> 1. "Zoo Code 소스 수정 제로 — 모든 기능은 VibeZoo Extension + MCP Bridge + Config로 구현"
> 2. "Crow는 Zoo Code 내장 — VibeZoo는 감지·연동만, Crow 없이도 모든 기능 정상 동작"
> 3. "완벽한 자동화보다 통제 가능한 자동화 — Human-in-the-Loop"
