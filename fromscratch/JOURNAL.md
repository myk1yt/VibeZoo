# VibeZoo 개발 일지

> 우측 상단의 `목차` 클릭 → 원하는 날짜로 이동
> 새로운 변경사항은 **맨 위**에 추가

---

- [2026-05-27 - v0.10.0 최종: Go 파일 정리, SSE 경로 수정](#2026-05-27-v0100-최종-go-파일-정리-sse-경로-수정)
- [2026-05-27 - v0.10.0: MCP 자동 설정 수정, Whiteboard 자동 연동](#2026-05-27-v0100-mcp-자동-설정-수정-whiteboard-자동-연동)
- [2026-05-27 - v0.10.0: AI 자동 Whiteboard + UI Preview 연동](#2026-05-27-v0100-ai-자동-whiteboard--ui-preview-연동)
- [2026-05-27 - v0.10.0: Python MCP 브릿지 전환 + Go 제거](#2026-05-27-v0100-python-mcp-브릿지-전환--go-제거)
- [2026-05-27 - v0.10.0: 초기 구현 완료 (26개 파일)](#2026-05-27-v0100-초기-구현-완료-26개-파일)
- [2026-05-27 - Architecture 설계 시작](#2026-05-27-architecture-설계-시작)

---

## 2026-05-27 - v0.10.0 최종: Go 파일 정리, SSE 경로 수정

**변경**:
- Go MCP 서버 파일 6개 전부 삭제 (`mcp-servers/cmd/`, `go.mod`, `build.ps1`) — 1,074줄 제거
- `.roo/mcp.json` SSE 경로 수정: `http://localhost:9027` → `http://localhost:9027/sse`
- `extension.ts` autoConfigureMCP() 수정: 같은 변경 반영 + Crow 중복 추가 제거
- VSIX 재빌드 + 재설치 완료

**설치 완료**:
- VibeZoo VS Code Extension 설치됨 (onStartupFinished 자동 실행)
- VibeZoo Bridge (9027/sse) Zoo Code 연결 성공 (200 OK, 202 Accepted 확인)
- Crow Memory (9020)는 기존 사용자 설정 유지

**파일 목록**:
| 파일 | 용도 |
|:---|:---|
| `extension/` | VS Code Extension (TypeScript 16개 파일) |
| `mcp-servers/vibezoo_mcp_bridge.py` | 통합 MCP 브릿지 (Scout·Reviewer·Tester·DeepAnalyzer·Whiteboard) |
| `templates/` | yoloignore, zoo-config, vscode-settings 기본 템플릿 |
| `fromscratch/` | Architecture.md, PLAN.md, 분석 문서 |

---

## 2026-05-27 - v0.10.0: MCP 자동 설정 수정, Whiteboard 자동 연동

**변경**:
- `extension.ts` autoConfigureMCP() 수정: Crow는 추가하지 않도록 변경 (사용자 기존 설정 유지)
- `.roo/mcp.json`에서 Crow 제거, VibeZoo만 유지

---

## 2026-05-27 - v0.10.0: AI 자동 Whiteboard + UI Preview 연동

**변경**:
- `vibezoo_mcp_bridge.py`에 새 MCP 도구 추가:
  - `draw_on_whiteboard(commands)` — AI가 Fabric.js 드로잉 명령 전송
  - `get_whiteboard_state()` — 사용자 수정 내용 조회
  - `open_whiteboard(message)` — AI가 화이트보드 패널 열기 요청
  - `open_ui_preview(code, framework)` — AI가 UI Preview 열기 요청
- `VisualVibePanels.ts` — 파일 감시(watch) 기능 추가:
  - AI의 `draw_on_whiteboard` 호출 감지 → 자동 Whiteboard 열기 + 렌더링
  - AI의 `open_ui_preview` 호출 감지 → 자동 UI Preview 열기
  - 1초 간격 폴링으로 상태 변화 감지

---

## 2026-05-27 - v0.10.0: Python MCP 브릿지 전환 + Go 제거

**변경**:
- Go MCP 서버(Scout·Reviewer·Tester·DeepAnalyzer·build.ps1·go.mod) → `vibezoo_mcp_bridge.py` 단일 파일로 통합
- `SubagentManager.ts` 대폭 수정: Go spawn → Python FastMCP spawn
- Python 자동 의존성 설치 추가 (`fastmcp`, `uvicorn`, `requests`)

**아키텍처 변경**:
```
Before: VibeZoo Extension + Go MCP 4개 서버 + Crow(외부)
After:  VibeZoo Extension + vibezoo_mcp_bridge.py 1개 + Crow(외부)
```

---

## 2026-05-27 - v0.10.0: 초기 구현 완료 (26개 파일)

**생성된 파일** (26개):
- `extension/src/` — 16개 TypeScript 파일
- `mcp-servers/` — Go 서버 5개 + go.mod + build.ps1
- `templates/` — 3개 템플릿
- `fromscratch/` — Architecture.md + PLAN.md
- `README.md`, `package.json`, `tsconfig.json`

**Wave 1-5 기능 구현**:
| Wave | 기능 |
|:---|:---|
| Phase 0 | Crow 연결, StatusBar, 디렉토리 템플릿 |
| Wave 1 | Silent Build, 빌드 에러 캡처, 프로젝트 감지, 트리 스캔 |
| Wave 2 | yocto 백업, Instant Rewind, File Guard, Git Stash, AutoBuildFix |
| Wave 3 | ContextFreshness, ExplainLess 감지, SessionResume, EmotionalDetector |
| Wave 4 | SubagentManager, @mention 라우팅 |
| Wave 5 | Whiteboard, UI Preview, Diagram Webview 패널 |
| Wave 6 | Deep Analyzer (vibezoo_mcp_bridge.py에 통합) |

---

## 2026-05-27 - Architecture 설계 시작

**분석 완료**:
- `reportfromgemini.md` — 201줄 보고서 분석
- `zoo_code_upgrade.agent.final.md` — 6,704줄 상세 설계 분석

**결정 사항**:
- VS Code 소스 수정 0% 전략
- Companion-First 아키텍처 (Zoo Code에 붙는 확장팩)
- API 기반 LLM (로컬 모델 불필요)
- Crow Memory는 외부 독립 시스템
