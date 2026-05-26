# VibeZoo: Implementation PLAN

> **작성일**: 2026-05-27
> **기반**: Architecture.md v2.2 (API-First + Go MCP)
> **목표**: VibeZoo 전 기능을 처음부터 끝까지 구현

---

## Tech Stack (확정)

| 구성요소 | 언어 | 이유 |
|:---|:---|:---|
| **VibeZoo Extension** | TypeScript | VS Code 네이티브. 추가 런타임 불필요. |
| **MCP Servers** (Scout, Reviewer, Tester, Deep Analyzer) | **Go** | 단일 바이너리 컴파일. 가장 빠른 실행 속도. 최소 메모리. 설치 마찰 제로. |
| **Crow Memory** | Python | 기존 시스템. 외부 독립. SSE로 연동. |
| **통신 프로토콜** | MCP/SSE (JSON-RPC 2.0) | 표준. Zoo Code가 이미 MCP 지원. |

---

## File Structure

```
vibezoo/                              # 프로젝트 루트
├── PLAN.md                           # 이 파일
├── README.md                         # 설치&사용 가이드
│
├── extension/                        # VibeZoo VS Code Extension (TypeScript)
│   ├── package.json
│   ├── tsconfig.json
│   ├── .vscodeignore
│   ├── src/
│   │   ├── extension.ts              # activate/deactivate 진입점
│   │   ├── crow/
│   │   │   └── CrowServerManager.ts  # Crow SSE 서버 생명주기 관리
│   │   ├── ui/
│   │   │   ├── StatusBarManager.ts   # 상태바 통합 관리
│   │   │   ├── TreeViewProviders.ts  # YOLO History, Active Subagents
│   │   │   └── WebviewPanels.ts      # Whiteboard, UI Preview, Dashboard
│   │   ├── flow/
│   │   │   ├── BuildTaskProvider.ts  # Silent 빌드 태스크
│   │   │   ├── BuildFeedback.ts      # onDidEndTaskProcess 구독
│   │   │   ├── ProjectDetector.ts    # 프로젝트 타입 자동 감지
│   │   │   └── ProjectTreeScanner.ts # 트리 스캔 + 캐싱
│   │   ├── safety/
│   │   │   ├── YoctoManager.ts       # yocto 백업 시스템
│   │   │   ├── InstantRewind.ts      # 즉시 복구 커맨드
│   │   │   ├── FileGuard.ts          # .yoloignore 감시 + 자동 복구
│   │   │   ├── GitStashManager.ts    # YOLO 진입/퇴장 Git 자동화
│   │   │   └── AutoBuildFix.ts       # 빌드 실패 자동 복구 루프
│   │   ├── context/
│   │   │   ├── ContextIndicator.ts   # Crow Context freshness 표시
│   │   │   ├── ExplainLess.ts        # 반복 설명 패턴 감지
│   │   │   ├── SessionResume.ts      # 세션 복원 Webview
│   │   │   └── EmotionalDetector.ts  # 감정 신호 감지
│   │   ├── orchestra/
│   │   │   ├── SubagentManager.ts    # Go MCP 서버 spawn 관리
│   │   │   ├── MentionRouter.ts      # @mention prefix 파싱
│   │   │   ├── BackgroundTask.ts     # withProgress 연동
│   │   │   └── DashboardProvider.ts  # Orchestra 대시보드
│   │   ├── visual/
│   │   │   ├── WhiteboardPanel.ts    # Fabric.js 화이트보드
│   │   │   ├── UIPreviewPanel.ts     # React/Vue 실시간 미리보기
│   │   │   ├── ScreenshotAnalyzer.ts # 캡처 이미지 분석
│   │   │   └── DiagramEngine.ts      # Mermaid/D3 다이어그램
│   │   └── types/
│   │       └── index.ts              # 공통 타입 정의
│   └── resources/
│       └── icons/                    # 아이콘 에셋
│
├── mcp-servers/                      # Go MCP 서버들
│   ├── go.mod
│   ├── go.sum
│   ├── cmd/
│   │   ├── scout/main.go             # Scout 서버 진입점 (:9022)
│   │   ├── reviewer/main.go          # Reviewer 서버 진입점 (:9023)
│   │   ├── tester/main.go            # Tester 서버 진입점 (:9024)
│   │   └── deep-analyzer/main.go     # Deep Analyzer 진입점 (:9026)
│   ├── pkg/
│   │   ├── mcp/                      # MCP 프로토콜 핸들러
│   │   │   ├── server.go
│   │   │   └── transport.go
│   │   ├── scout/
│   │   │   ├── search.go             # 코드베이스 검색
│   │   │   ├── references.go         # 심볼 참조 찾기
│   │   │   └── architecture.go       # 아키텍처 요약
│   │   ├── reviewer/
│   │   │   ├── review.go             # 코드 리뷰
│   │   │   └── quality.go            # 품질 검사
│   │   ├── tester/
│   │   │   ├── generate.go           # 테스트 생성
│   │   │   └── coverage.go           # 커버리지 분석
│   │   └── analyzer/
│   │       ├── callgraph.go          # 호출 그래프
│   │       ├── dependency.go         # 의존성 분석
│   │       ├── pattern.go            # 패턴 추출
│   │       └── reverse.go            # 역설계
│   └── build/                        # 빌드 스크립트
│       ├── build-all.sh
│       └── build-all.ps1
│
├── templates/                        # 자동 생성 템플릿
│   ├── yoloignore
│   ├── zoo-config.json
│   └── vscode-settings.json
│
└── dist/                             # 빌드 산출물
    ├── vibezoo.vsix                   # Extension 패키지
    ├── scout.exe / scout              # Go 바이너리
    ├── reviewer.exe / reviewer
    ├── tester.exe / tester
    └── deep-analyzer.exe / deep-analyzer
```

---

## Implementation Sequence (의존성 순서)

### Step 1: Extension Skeleton + Crow Manager (Phase 0)
- `extension/package.json`
- `extension/tsconfig.json`
- `extension/src/extension.ts`
- `extension/src/crow/CrowServerManager.ts`
- `extension/src/types/index.ts`

### Step 2: UI Foundation (Phase 0)
- `extension/src/ui/StatusBarManager.ts`

### Step 3: Templates (Phase 0)
- `templates/yoloignore`
- `templates/zoo-config.json`
- `templates/vscode-settings.json`

### Step 4: Flow Keepers (Wave 1)
- `extension/src/flow/BuildTaskProvider.ts`
- `extension/src/flow/BuildFeedback.ts`
- `extension/src/flow/ProjectDetector.ts`
- `extension/src/flow/ProjectTreeScanner.ts`

### Step 5: Safety Net (Wave 2)
- `extension/src/safety/YoctoManager.ts`
- `extension/src/safety/InstantRewind.ts`
- `extension/src/safety/FileGuard.ts`
- `extension/src/safety/GitStashManager.ts`
- `extension/src/safety/AutoBuildFix.ts`
- `extension/src/ui/TreeViewProviders.ts` (YOLO History)

### Step 6: Context Intelligence (Wave 3)
- `extension/src/context/ContextIndicator.ts`
- `extension/src/context/SessionResume.ts`
- `extension/src/context/ExplainLess.ts`
- `extension/src/context/EmotionalDetector.ts`

### Step 7: Go MCP Servers Foundation
- `mcp-servers/go.mod`
- `mcp-servers/pkg/mcp/server.go`
- `mcp-servers/pkg/mcp/transport.go`

### Step 8: Scout MCP Server (Wave 4 core)
- `mcp-servers/cmd/scout/main.go`
- `mcp-servers/pkg/scout/search.go`

### Step 9: Orchestra Manager (Wave 4)
- `extension/src/orchestra/SubagentManager.ts`
- `extension/src/orchestra/MentionRouter.ts`
- `extension/src/orchestra/BackgroundTask.ts`
- `extension/src/orchestra/DashboardProvider.ts`
- `extension/src/ui/WebviewPanels.ts` (Dashboard)

### Step 10: Reviewer + Tester MCP Servers (Wave 4)
- `mcp-servers/cmd/reviewer/main.go`
- `mcp-servers/cmd/tester/main.go`

### Step 11: Visual Vibe (Wave 5)
- `extension/src/visual/WhiteboardPanel.ts`
- `extension/src/visual/UIPreviewPanel.ts`
- `extension/src/visual/ScreenshotAnalyzer.ts`
- `extension/src/visual/DiagramEngine.ts`

### Step 12: Deep Analyzer (Wave 6)
- `mcp-servers/cmd/deep-analyzer/main.go`
- `mcp-servers/pkg/analyzer/callgraph.go`
- `mcp-servers/pkg/analyzer/dependency.go`
- `mcp-servers/pkg/analyzer/pattern.go`
- `mcp-servers/pkg/analyzer/reverse.go`

---

## 설계 원칙 (VibeZoo 약속)

1. **가벼움**: Extension은 500KB 미만. Go 바이너리는 각 10MB 미만. 총 설치 크기 50MB 미만.
2. **빠름**: Extension 활성화 300ms 이내. Go 서버 시작 100ms 이내. yocto 백업 200ms debounce.
3. **쉬운 설치**: VSIX 설치 + Go 바이너리 다운로드. Zoo Code에 "VibeZoo 설치해줘" 한 마디로 완료.
4. **Zoo Code 소스 수정 제로**: 모든 기능은 VibeZoo Extension + Go MCP 서버 + Config 변경으로만 작동.
5. **Crow는 외부 시스템**: Crow Memory는 VibeZoo와 독립적. SSE로 유기적 연동.

---

## Go MCP SDK 선택

Go용 MCP 라이브러리로 `github.com/mark3labs/mcp-go` 사용.
- 순수 Go, CGo 불필요
- SSE transport 지원
- JSON-RPC 2.0 표준 준수
- 경량 (의존성 최소)

---

> **다음**: Step 1부터 순차적으로 모든 파일 생성 및 구현 시작.
