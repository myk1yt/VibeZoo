# VibeZoo v0.12.0

> **Zoo Code를 위한 AI 동반자 확장.** 소스 코드 0% 수정. 100% Companion-First.

<p align="center">
  <img src="https://img.shields.io/badge/version-0.12.0-blue" alt="version">
  <img src="https://img.shields.io/badge/MCP_tools-31-green" alt="mcp tools">
  <img src="https://img.shields.io/badge/TypeScript-16_files-orange" alt="typescript">
  <img src="https://img.shields.io/badge/Python-FastMCP-yellow" alt="python">
  <img src="https://img.shields.io/badge/tree--sitter-AST-purple" alt="tree-sitter">
  <img src="https://img.shields.io/badge/tested-96%25_pass-brightgreen" alt="tested">
</p>

---

## 🎯 철학 (Philosophy)

**"Vibe = f(Usefulness, Predictability, Control_perceived)"**

VibeZoo는 Zoo Code를 **포크하지 않고**, 곁에서 돕는 **동반자(Companion) 확장**입니다. Zoo Code 소스 코드를 단 한 줄도 수정하지 않고, VS Code Extension API + MCP 프로토콜 + Crow Memory만으로 바이브코딩 경험을 극대화합니다.

### 핵심 원칙
| 원칙 | 설명 |
|:---|:---|
| **Companion-First** | Zoo Code 옆에서 동작. 포크/패치 없음 |
| **사용자 통제 가능한 자동화** | 완전 자동이 아닌, 인간이 개입할 수 있는 반자동 (HITL) |
| **VS Code Lock-In** | VS Code를 벗어나지 않음. 모든 UI는 VS Code 내장 |
| **도구는 알고리즘, 지능은 LLM** | MCP 도구는 순수 Python 함수. 추론/판단은 Zoo Code LLM이 |

### Crow Memory와의 관계
VibeZoo는 **Crow Memory와 함께 사용할 때 진정한 힘**을 발휘합니다:

- **Crow 없이**: 31개 MCP 도구가 정적 분석/검색 수행
- **Crow 있으면**: 에러 패턴 학습, 프로젝트 지식 축적, 코딩 스타일 기억, 크로스 세션 컨텍스트 — **스스로 진화하는 도구**

VibeZoo는 Crow Memory를 실행하지 않습니다 — Zoo Code의 내장 Crow를 **자동 감지**하여 활용합니다.

---

## 🏗️ 아키텍처 (Architecture)

```
┌─────────────────────────────────────────────────────────┐
│                      VS Code 창 (싱글톤 브릿지 공유)      │
│  ┌──────────────────┐  ┌──────────────────────────────┐ │
│  │    Zoo Code       │  │   VibeZoo Extension (local)  │ │
│  │    (LLM + Crow)   │  │   ────────────────────────   │ │
│  │                   │  │   • StatusBar (통합 1개)      │ │
│  │   deepseek-v4     │  │   • TreeView (3개 패널)       │ │
│  │   or other LLM    │  │   • FixLoopManager (자율 수정) │ │
│  │                   │  │   • VisualVibePanels (화이트)  │ │
│  │   Crow Memory     │  │   • YoctoManager (백업/복구)  │ │
│  │   (내장, 호환)    │  │   • FileGuard + GitStash      │ │
│  └────────┬─────────┘  └────────────┬─────────────────┘ │
│           │ MCP/SSE (:9027)         │ 감지/spawn (싱글톤) │
└───────────┼─────────────────────────┼───────────────────┘
            │                         │
            ▼                         ▼
┌──────────────────────────────────────────────────────┐
│  VibeZoo 통합 MCP Bridge (:9027) — 싱글톤 프로세스   │
│  vibezoo_mcp_bridge.py                               │
│  ┌────────────────────────────────────────────────┐  │
│  │  Crow Memory 10종 도구  │  VibeZoo 31종 도구   │  │
│  │  • crow_recall          │  • search_codebase   │  │
│  │  • crow_ingest          │  • review_code       │  │
│  │  • crow_diagnostics     │  • map_dependencies  │  │
│  │  • ... (7 more)         │  • ... (28 more)     │  │
│  └────────────────────────────────────────────────┘  │
│  저장소: ~/.vibezoo-crow-memory/ (JSON 파일)         │
└──────────────────────────────────────────────────────┘
```

### 포트 할당
| 포트 | 서비스 | 관리 주체 |
|:---|:---|:---|
| 9027 | VibeZoo 통합 MCP Bridge (Crow Memory + VibeZoo) | VibeZoo Extension (Python spawn, 싱글톤) |

### 데이터 흐름
```
사용자 채팅 → Zoo Code LLM → MCP tool call → VibeZoo 통합 Bridge (:9027)
                                                    │
                          ┌─────────────────────────┤
                          ▼                         ▼
                    정적 분석 도구              파일 시스템
                    (tree-sitter AST,          (~/.vibezoo-*.json,
                     regex, subprocess)        ~/.vibezoo-crow-memory/)
                          │                         │
                          ▼                         ▼
                    Crow Memory 저장소          VibeZoo Extension
                    (~/.vibezoo-crow-memory/    (파일 감시 → Webview 렌더링)
                     JSON 기반 파일 저장소)
```

---

## 🚀 주요 기능 (Features)

### 🧠 31개 MCP 도구 — AI의 손과 눈

모든 도구는 **순수 Python 알고리즘**입니다. LLM API 호출이 아닌, 파일 I/O + tree-sitter AST + 정규표현식 + 서브프로세스로 작동합니다.

| 카테고리 | 도구 | 작동 원리 |
|:---|:---|:---|
| **Scout** | `search_codebase`, `find_references`, `summarize_architecture` | AST 기반 함수/클래스/인터페이스 검색 + glob 파일 스캔 |
| **Reviewer** | `review_code`, `check_quality` | AST 구조 분석 + ESLint 연동 + 12종 안티패턴 감지 |
| **Tester** | `generate_tests`, `analyze_coverage` | AST로 함수명 추출 → 테스트 템플릿 생성 |
| **Deep Analyzer** | `analyze_call_graph`, `map_dependencies`, `extract_patterns`, `reverse_engineer` | AST 호출 그래프 + import DFS 순환 참조 탐지 + 데이터 모델 필드 추출 |
| **Whiteboard** | `draw_on_whiteboard`, `get_whiteboard_state`, `open_whiteboard`, `capture_screen` | Fabric.js JSON 생성 → 파일 감시 → Webview 렌더링 |
| **UI Preview** | `open_ui_preview` | iframe srcdoc에 HTML/CSS/JS 실시간 렌더링 |
| **Fix Loop** | `auto_fix_status`, `retry_build`, `check_intervention` | 파일 기반 LLM 통신 + tsc 실행 + Whiteboard/채팅 HITL 개입 |
| **통합 시나리오** | `review_project`, `find_bugs`, `suggest_refactor`, `generate_docs` | 기존 도구 체인 호출 + 결과 통합 |
| **설명** | `explain_code` | AST로 해당 라인의 enclosing 함수/클래스/인터페이스 컨텍스트 분석 |
| **Git 분석** | `analyze_changes`, `review_pr` | `git diff` 실행 + 변경 파일별 Crow 컨텍스트 조회 |
| **리팩토링** | `refactor_across_files` | `search_codebase`로 패턴 검색 → 파일별 diff-style 제안 |
| **지식** | `learn_project`, `recall_project` | 프로젝트 구조/패턴/의존성 → Crow arch·style 레지스터 저장/조회 |
| **선호도** | `learn_preference`, `get_preferences` | 로컬 JSON + Crow life_context 이중 저장 |

### 🔄 Autonomous Fix Loop (자율 수정)
- 빌드 실패 자동 감지 → 에러 분석 → Crow 과거 패턴 조회 → LLM에 수정 요청 → 재빌드
- 8단계 상태 머신 (idle → pending → in_progress → building → resolved/abandoned)
- Oscillation 감지 (A→B→A 패턴), 최대 3회 시도, 120초 타임아웃
- **HITL (Human-in-the-Loop)**: Whiteboard + 채팅 개입 가능 (pause/resume/abort)

### 🖌️ Visual Vibe (시각 협업)
- **Whiteboard**: Fabric.js 캔버스. AI가 도형/텍스트/이미지 생성, 사용자가 주석 추가
- **UI Preview**: React/Vue/HTML 실시간 렌더링
- **Diagram**: Mermaid.js + D3.js 아키텍처/ERD 다이어그램

### 🛡️ Fearless YOLO (안전망)
- **Yocto**: 실시간 파일 백업 (200ms debounce)
- **Instant Rewind**: `Ctrl+Shift+Z` → 0.3초 내 전체 복구 (확인 대화상자 추가)
- **File Guard**: `.yoloignore` 보호 파일 자동 복구
- **Git Stash**: YOLO 모드 진입/퇴장 자동화

### 📊 StatusBar + TreeView
- 통합 StatusBar 1개 (VibeZoo + Crow 상태 + CIM/YOLO 모드)
- TreeView 3종: Active Subagents, YOLO History, Session Resume

---

## 🔧 기술 스택 (Tech Stack)

| 계층 | 기술 | 설명 |
|:---|:---|:---|
| **Extension** | TypeScript, VS Code Extension API | StatusBar, TreeView, Webview, FileSystemWatcher, Task Provider |
| **MCP Bridge** | Python, FastMCP, SSE | 31개 도구, 단일 파일(`vibezoo_mcp_bridge.py`), 포트 9027 |
| **AST** | tree-sitter | TypeScript/JavaScript AST 파싱 (함수, 클래스, 인터페이스, 호출 관계) |
| **화이트보드** | Fabric.js 5.3 | Canvas 기반 드로잉, 파일 감시(`fs.watchFile`) |
| **다이어그램** | Mermaid.js 10, D3.js | 아키텍처/ERD/호출 그래프 시각화 |
| **기억** | Crow Memory (Zoo Code 내장) | 에러 패턴, 스타일 규칙, 프로젝트 지식, 사용자 선호도 |

---

## 📦 설치 (Installation)

### 사전 요구사항
- VS Code 1.85+
- Zoo Code Extension
- Python 3.10+ (MCP Bridge용)
- Node.js 18+ (Extension 컴파일용)

### 1. Extension 설치
```bash
cd extension
npm install
npx tsc --noEmit
npx vsce package
code --install-extension vibezoo-0.13.0.vsix --force
```

### 2. Python 의존성
```bash
pip install fastmcp uvicorn requests tree-sitter
```

### 3. VS Code 재시작
`Ctrl+Shift+P` → `Developer: Reload Window`

VibeZoo가 자동으로:
1. Python MCP Bridge를 spawn (port 9027, 싱글톤 — 첫 번째 창만 실행, 이후 창은 공유)
2. Bridge가 Crow Memory 10종 도구 + VibeZoo 31종 도구를 함께 제공
3. `.roo/mcp.json`에 VibeZoo 통합 MCP 서버 자동 등록

### 4. 확인
`Ctrl+Shift+P` → `VibeZoo: Verify Foundation`

---

## 📁 프로젝트 구조

```
VibeZoo/
├── extension/                    # VS Code Extension (TypeScript)
│   └── src/
│       ├── extension.ts          # 진입점 (26개 명령어)
│       ├── context/              # ContextIntelligence (Session Resume 등)
│       ├── crow/                 # CrowServerManager (감지 전용)
│       ├── flow/                 # BuildFeedback, BuildTaskProvider, ProjectDetector, ProjectTreeScanner
│       ├── orchestra/            # FixLoopManager, SubagentManager, MentionRouter
│       ├── safety/               # YoctoManager, FileGuard, GitStashManager
│       ├── types/                # 타입 정의
│       ├── ui/                   # StatusBarManager, TreeViewProviders
│       └── visual/               # VisualVibePanels (Whiteboard, UI Preview, Diagram)
├── mcp-servers/
│   └── vibezoo_mcp_bridge.py     # 31개 MCP 도구 (Python FastMCP)
├── fromscratch/                  # 설계 문서
│   ├── Architecture.md           # 아키텍처 상세
│   ├── PLAN.md                   # 구현 계획
│   └── ROADMAP.md                # 로드맵
├── plans/                        # 기능 설계
│   └── autonomous-fix-loop.md    # 자율 수정 루프 설계
└── templates/                    # 설정 템플릿
```

---

## 🗺️ 로드맵 (Roadmap)

| 마일스톤 | 시기 | 내용 | 상태 |
|:---|:---|:---|:---|
| **M0** | 완료 | Quick Wins: 통합 커맨드, fs.watchFile, StatusBar 통합, Lazy Init | ✅ |
| **M1** | 완료 | Autonomous Fix Loop + AST Scout + Crow 학습 | ✅ |
| **M3** | 완료 | DeepAnalyzer AST + Self-healing CIM + Whiteboard 강화 | ✅ |
| **M6** | 예정 | Self-evolving: 완전 자율, 멀티 파일 리팩토링, 크로스 세션 컨텍스트 | 📅 |

---

## 🤝 기여 (Contributing)

VibeZoo는 개인 프로젝트입니다. 버그 제보나 기능 제안은 GitHub Issues를 이용해주세요.

## 📄 라이선스

MIT License
