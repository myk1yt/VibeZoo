# Code Task Report: P6-beta+gamma 설치 가이드 신설 및 README/ACTIVE_STATE 전수 최신화

## Task Summary
사용자 요구사항 REQ-009, REQ-010, REQ-011에 따라 "컴맹도 원큐에 설치 가능한" 단계별 완전판 설치 가이드([`docs/INSTALLATION.md`](docs/INSTALLATION.md))를 신설하고, [`README.md`](README.md) 전수를 정독 및 조사하여 도구 수(33개) 및 VS Code 커맨드(20개), 신규 기능(`rebuildCodeIndex`, Dropzone `autoAnalyze`, Vision AI 파이프라인, Exa 검색 등)을 전면 갱신하였으며, [`docs/ACTIVE_STATE.md`](docs/ACTIVE_STATE.md)의 세션 상태 및 계획 현황을 최신화했습니다.

---

## Actions Taken

### 1. [`docs/INSTALLATION.md`](docs/INSTALLATION.md) 원큐 설치 가이드 신설 (REQ-009, REQ-010)
- **Windows 환경 원큐 8단계 가이드**:
  1. 사전 준비 (관리자 권한 없이 설치 가능 안내)
  2. Git for Windows 설치 링크 및 기본 옵션 마법사 안내
  3. Python 3.10+ 설치 시 `[x] Add python.exe to PATH` 필수 체크박스 ASCII 안내
  4. Node.js LTS 설치
  5. VibeZoo 클론 및 정확한 npm 의존성 설치 커맨드 (루트 + `extension/`)
  6. VS Code 및 Zoo Code 확장 설치
  7. `init_vibezoo.bat` 원클릭 부트스트래퍼 실행 (표준 타깃 디렉터리 `%USERPROFILE%\mcp-servers\vibezoo` 구성, venv 생성, pip 패키지 설치, TypeScript 빌드 자동화)
  8. Python 브릿지 구동, LM Studio/Ollama `nomic-embed-text` 로컬 임베딩(포트 8089) 연동, VSIX 패키징 및 확장 설치, 재시작
- **macOS / Linux 환경 원큐 8단계 가이드**:
  - Homebrew / apt 기반 동일 8단계 파이프라인 구축 (`init_vibezoo.sh` 실행, `~/mcp-servers/vibezoo/` 표준 경로, 파이썬 가상환경 활성화 및 브릿지 실행 커맨드 완비)
- **설치 후 확인 절차 (Self Check)**:
  - Command Palette(`Ctrl+Shift+P` / `Cmd+Shift+P`)에서 `VibeZoo: Self Check` 실행을 통한 전체 시스템 무결성 검증 안내
- **자주 묻는 질문 및 트러블슈팅 6선**:
  1. 포트 충돌 (9027, 8089, 9020) 해결법 (`netstat`/`lsof` 및 프로세스 종료)
  2. 임베딩 서버 미구동 시 자동 BM25 폴백 원리 및 8089 세팅 안내
  3. Git Push 시 GCM(Git Credential Manager) 브라우저 인증 활성화 (`credential.helper manager`)
  4. Windows OneDrive 동기화 파일 잠금 현상 해결 및 로컬 경로 권장
  5. 글로벌/로컬 MCP 설정 파일 위치(`%APPDATA%/.../mcp_settings.json` 및 `.roo/mcp.json`) 및 Streamable HTTP 설정
  6. 이미지 붙여넣기(`vibezoo.openDropzone`) 및 자동 비전 분석 파이프라인 요약

---

### 2. [`README.md`](README.md) 전수 조사 및 전면 갱신 (REQ-011)
- **도구 및 커맨드 수치 정합**:
  - 활성 MCP 도구 **33개** 및 VS Code 커맨드 **20개**로 전수 일치 갱신.
  - 삭제된 9개 도구(`explore_github`, `apply_patch`, `generate_tests`, `analyze_coverage`, `ux_coordinator`, `auto_analyze_after_drop`, `auto_analyze_whiteboard`, `explain_code`, `analyze_changes`) 및 13개 커맨드 언급 완전 제거.
  - 제거된 카테고리(Editor, Tester, UX) 정리 및 12개 활성 도구 도메인(Scout, Deep Analyzer, Reviewer, Whiteboard, File Analyzer, Fix Loop, Integrated, Analysis, Knowledge, Web, SSA, Setup) 매핑.
- **신규 기능 및 개선사항 상세 문서화**:
  - **Scout**: `rebuild_code_index`, `embedding_health_check` 도구 및 `vibezoo.rebuildCodeIndex` 커맨드 추가, SHA-256 증분 벡터 인덱스 캐시([`index_cache.py`](extension/mcp-servers/bridge/index_cache.py)) 명세.
  - **Vision & Dropzone**: 이미지 붙여넣기 및 `vibezoo.image.autoAnalyze` 설정 기반 자동 OCR/SSA/MiniCPM 분석 파이프라인 및 비전 폴백 소개.
  - **Web Search**: `EXA_API_KEY` 환경변수 기반 Exa 신경망 검색 및 DuckDuckGo 자동 폴백 설명.
  - **i18n**: 20개 언어 전수 키 100% 매핑 완료 상태 반영.
- **설치 섹션 간결화**:
  - 방대했던 설치 본문을 핵심 요약과 함께 [`docs/INSTALLATION.md`](docs/INSTALLATION.md) 링크로 깔끔하게 축약.
- **버전 및 설계 자산 보존**:
  - 버전 `0.15.1` 정합.
  - `plans/` (11개 설계 문서) 및 `fromscratch/` (6개 초기 로드맵/스펙)의 영구 보존 상태 반영.

---

### 3. [`docs/ACTIVE_STATE.md`](docs/ACTIVE_STATE.md) 세션 상태 갱신
- Current Session을 260830 세션(`docs/260830_0001_session_reinstall-recovery-and-quality/`)으로 갱신.
- Recent Changes에 D1~D5 및 P6-alpha/beta/gamma 전 작업 내역(i18n 20개 언어, 임베딩 캐시 및 검색 정상화, 드롭존/비전 파이프라인, 쓸모없는 9툴+13커맨드 정리, 단일 경로화, 설치 가이드/README 최신화) 요약 기록.
- Known Issues 및 Active Plans, Session Reports 링크 구조 최신화.
- Pending Tasks로 VP 레벨의 커밋 분할 및 GCM GitHub push 작업 명시.

---

### 4. 마크다운 링크 및 문법 무결성 검증
- 자체 링크 검증 스크립트를 통해 [`README.md`](README.md), [`docs/INSTALLATION.md`](docs/INSTALLATION.md), [`docs/ACTIVE_STATE.md`](docs/ACTIVE_STATE.md) 내의 모든 로컬 마크다운 링크에 대해 100% 파일 존재 여부를 검증 (`BROKEN LINKS: 0`).
- 마크다운 백틱 짝 및 코드 블록 문법 무결성 확인.

---

## Result
✅ **Success**: 설치 가이드 신설, README 전수 최신화, ACTIVE_STATE 갱신 및 링크 무결성 검증 100% 완료.

### 산출물 검증 결과표

| 산출물 | 상태 | 검증 항목 | 결과 |
|---|---|---|---|
| [`docs/INSTALLATION.md`](docs/INSTALLATION.md) | 신규 생성 | Win 8단계 + Mac/Linux 8단계 + 트러블슈팅 6선 + 코드블록 문법 | ✅ PASS |
| [`README.md`](README.md) | 전면 갱신 | 33개 툴 / 20개 커맨드 / 20개 언어 / 신기능 명세 / 링크 유효성 | ✅ PASS (0 broken links) |
| [`docs/ACTIVE_STATE.md`](docs/ACTIVE_STATE.md) | 전면 갱신 | 세션 요약 / 변경 이력 / 아카이브 현황 / Pending Tasks | ✅ PASS |

---

## Issues Discovered
- 특이사항 없음. 모든 문서 링크 및 코드베이스 경로가 단일화된 `extension/mcp-servers/` 및 표준 런타임 경로와 완벽하게 일치합니다.

---

## Next Step Recommendations
- REQ-009, REQ-010, REQ-011 문서화 작업이 완벽하게 완료되었습니다.
- VP 레벨에서 작업 내역을 검토한 후, REQ-001/012에 따른 논리적 단위 git commit 및 GCM 브라우저 인증을 통한 원격 저장소 push를 진행할 것을 권장합니다.

---

## Affected File List
- [`docs/INSTALLATION.md`](docs/INSTALLATION.md) (신규 생성)
- [`README.md`](README.md) (갱신)
- [`docs/ACTIVE_STATE.md`](docs/ACTIVE_STATE.md) (갱신)
- [`docs/260830_0001_session_reinstall-recovery-and-quality/115500_code-p6-beta-gamma-docs-report.md`](docs/260830_0001_session_reinstall-recovery-and-quality/115500_code-p6-beta-gamma-docs-report.md) (신규 보고서)
