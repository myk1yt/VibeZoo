# Zoo Code: The Ultimate Vibe Coding Tool (VS Code Lock-In Edition)
# — Integrated Upgrade Roadmap

> **작성일**: 2026-05-27
> **총 분석 차원**: 12개 기술 차원
> **조사 도구**: OpenCode, Claude Code, Roo Code/Kilo Code, VS Code Extension API, Crow Memory
> **출력 규모**: 60,000–65,000 tokens

---

# Zoo Code Ultimate Upgrade: Executive Summary & Foundation

> *"사용자가 AI의 존재를 의식하는 순간, 바이브는 깨진다. 우리의 목표는 사용자가 Zoo Code의 존재조차 잊게 만드는 것이다."*

---

## Executive Summary: 4-Wave 로드맵 개요

### Key Findings

5명의 바이버(Flow Keeper, YOLO Surgeon, Context Whisperer, Parallel Vibe Engineer, Crow Integrator)가 21개 흐름 차원을 조사하고, Zoo Code/OpenCode/Claude Code의 3방 비교 매트릭스를 생성한 결과, 현재 Zoo Code의 전체 바이브 점수는 **4.2/10**으로 평가되었다. 이 점수의 핵심 저하 요인은 6개 흐름 단절 지점(Flow Breaker)에 집중되어 있으며, 각각은 사용자가 코딩의 "흐름"에서 벗어나 "도구를 조작하는" 인지적 전환을 강제하는 지점이다.

**현재 Zoo Code 전체 바이브 점수: 4.2/10** — 6개 흐름 단절 지점(Flow Breaker)이 핵심 저하 요인. 이 점수는 8개 주요 차원의 개별 평가를 종합한 분석 기반 추정치다. 세션 지속성 3/10, 모드 전환 4/10, YOLO 안전성 3/10, 컨텍스트 유지 4/10, 병렬 작업 2/10, 외부 리소스 3/10, 파일 탐색 5/10, 에러 복구 4/10의 평균에 가중치를 적용하여 산출되었다.

**목표 전체 바이브 점수: 9.5/10** — VS Code Extension API 내에서만 구현 가능한 4-Wave 로드맵으로 달성. 9.5가 10이 아닌 이유는 단순하다. 10점은 "사용자가 기능의 존재를 전혀 의식하지 않는" 상태인데, VS Code Extension API의 근본적 제약 — OS 재부팅 시 `detached` 프로세스 소멸, `deactivate()` 훅의 비동기 불완전 보장, Extension Host의 V8 heap limit (~2-4GB) [^172^] — 이 이론적 완벽성을 가로막기 때문이다. 하지만 4.2→9.5의 도약은 사용자 경험의 질적 변화를 의미한다. "VS Code를 켰을 때 Zoo Code + Crow가 이미 준비되어 있다"는 0초의 무의식, "되돌려줘" 한 마디에 모든 것이 원위치로 돌아가는 신뢰, "저번처럼"이라는 7글자만으로 AI가 모든 맥락을 읽는 경험 — 이것이 9.5점의 세계다.

**핵심 전략: "Zoo Code 자체 튜닝 + MCP 도구 확장 + VS Code API 극한 활용 + Crow Memory 통합"**. OpenCode는 Go TUI + Bun 서버로, Claude Code는 git worktree로 해결한 문제들을, 우리는 `ExtensionContext.globalState`와 `child_process.spawn`으로, `FileSystemWatcher`와 `TaskPresentationOptions.reveal: silent`로 해결한다. 이것은 열세한 도구로 더 어려운 문제를 푸는 작업이지만, 그 제약 속에서 나오는 솔루션은 사용자가 "설치"를 의식하지 않는 유일한 경험을 만들어낸다. 5개의 Cross-Dimension Insight [^insight1^]가 이 전략의 타당성을 뒷받침한다.

---

### 4-Wave 로드맵 종합 매트릭스

다음 표는 전체 4-Wave 로드맵의 21개 흐름 차원을 현재 점수, 목표 점수, 핵심 개선 전략, Crow Memory 연동 포인트별로 종합한 것이다. 모든 수치는 조사 기반 추정치이며, 각 Wave의 상세 장에서 기술적 구현이 전개된다.

| Wave | 흐름 차원 | 현재 점수 | 목표 점수 | 핵심 개선 전략 | Crow 연동 |
|:---|:---|:---:|:---:|:---|:---|
| **W1: Unbreakable Flow** | 세션 지속성 (Session Survivability) | 3/10 | 9/10 | `detached: true` SSE 서버 + `globalState` 모드 복원 + 3계층 중복 구조 | `life_context` register, `crow_compact` |
| | 모드 전환 마찰 (Mode Switching) | 4/10 | 9/10 | `AutoModeDetector` — 프로젝트 파일 기반 자동 감지 + `.zoo/config.json` | `life_context` 모드 이력 저장 |
| | 빌드-코드-피드백 루프 (Build Feedback) | 4/10 | 9/10 | `Task API` + `problemMatcher` + `presentation.reveal: silent` + `AutoBuildFix` | `bug` register 빌드 패턴 축적 |
| | 컨텍스트 로트 (Context Rot) | 4/10 | 9/10 | `crow_compact` 10분 간격 자동 실행 + OpenCode 2-phase compaction | `context`→`arch` register 요약 이관 |
| | 파일 탐색 마찰 (File Navigation) | 5/10 | 9/10 | `ProjectTreeScanner` — `findFiles` + `FileSystemWatcher` + 30초 TTL 캐시 | `arch` register 생성 위치 편향 |
| | 외부 리소스 탐색 (External Resource) | 3/10 | 8/10 | Extension 내 Brave Search/Tavily 호출 + Markdown 정리 | `life_context` 검색 이력 저장 |
| **W2: Fearless YOLO** | 인스턴트 리와인드 (Instant Rewind) | 3/10 | 9/10 | `yocto` — `fs.copyFileSync` 자동 백업, 0.3초 복구 | `crow_manage_backup` 자동 호출 |
| | 체크포인트 세분도 (Checkpoint) | 4/10 | 9/10 | YOLO 진입/퇴장 Git 자동 stash + `--no-ff` squash | `arch` register YOLO 패턴 저장 |
| | 트랜잭션 & 롤백 (Transaction) | 3/10 | 9/10 | `pending_edits[]` 메모리 트랜잭션 + 역순 revert | `crow_transaction` 위상 정렬 |
| | 세이프 YOLO (Permission Gradation) | 3/10 | 9/10 | 5×5 Permission 매트릭스 + `.yoloignore` + `life_avoid` 동기화 | `life_avoid` register 회피 패턴 축적 |
| | 에러 후 자동 복구 (Auto-Recovery) | 4/10 | 9/10 | `AutoBuildFix` 루프 — `max_attempts=3` + oscillation 감지 | `bug` register 예방적 YOLO 진화 |
| **W3: Zero-Explanation** | 암묵적 컨텍스트 (Implicit Context) | 4/10 | 9/10 | `ContextInjector` — 매 턴 `crow_recall` 강제 주입 + fallback injection | `crow_recall(domain="all")` |
| | 크로스-세션 메모리 (Cross-Session) | 3/10 | 9/10 | 세션 종료 시 자동 `crow_compact` + 요약본 `life_context` 저장 | `crow_compact`, `life_context` |
| | 멀티에이전트 싱크 (Multi-Agent Sync) | 3/10 | 8/10 | `system_prompt.md` HITL 승인 + `crow_evolve_propose` + Git 동기화 | `crow_evolve_propose`, `fs.watch` reload |
| | 프로젝트 컨텍스트 (Project Context) | 4/10 | 9/10 | `.zoo.md` 자동 로드 + `arch` register 동적 병합 + 호환성 fallback | `arch` register, `LayeredCrowResolver` |
| | 감정 컨텍스트 (Emotional Context) | 2/10 | 8/10 | `EmotionalContextDetector` — 연속 거절 감지 + 톤 자동 조정 | `life_avoid` (`polarity=-2.0`) |
| **W4: Orchestra of One** | 서브에이전트 (Subagent) | 2/10 | 8/10 | `SubagentManager` — `child_process.spawn` + TreeView + idle pooling | `context` 공유 via SSE |
| | 백그라운드 태스크 (Background Task) | 2/10 | 8/10 | `withProgress` 연동 + Opt-In 완료 + 취소 가능 | `arch`/`style` 결과 저장 |
| | @멘션 라우팅 (@Mentions) | 2/10 | 8/10 | Prefix 파싱 + `createChatParticipant` 우회 + graceful fallback | `life_pref` 라우팅 패턴 |
| | 플릿 대시보드 (Fleet Dashboard) | 1/10 | 8/10 | `TreeView` + `Webview` + SSE 실시간 푸시 + `retainContextWhenHidden` | `arch` ETA 데이터 |
| | 충돌 해결 (Conflict Resolution) | 2/10 | 8/10 | 3계층 방어 + AI 자동 3-way merge + `life_avoid` 핫스팟 학습 | `life_avoid` 충돌 패턴 |

21개 차원의 현재 평균 점수는 3.2/10, 목표 평균은 8.7/10으로, 각 차원별 평균 +5.5의 도약을 추정한다. 이 표의 모든 개선 전략은 VS Code Extension API 내에서 구현 가능하며, 추가 런타임(Go TUI, Bun 서버 등)의 설치를 요구하지 않는다. 이것이 "VS Code Lock-In" 전략의 핵심 타당성이다 — 설치 마찰 0, 학습 곡선 0의 경쟁 우위 [^insight1^].

---

### Approach Overview

5명의 바이버가 21개 흐름 차원을 매핑하고 3개 툴(Zoo Code 3.2.0, OpenCode 2.0, Claude Code 1.0.48)을 비교한 방법론은 다음과 같다. 각 바이버는 자신의 전문 차원에서 (1) 현재 사용자 경험의 흐름 단절 지점을 시나리오 기반으로 문서화하고, (2) 경쟁 도구가 동일 지점을 어떻게 해결하는지 아키텍처적으로 분해한 뒤, (3) VS Code Extension API의 제약 내에서 동등하거나 우월한 솔루션을 설계했다. 모든 설계안은 [튜닝](Zoo Code Extension 소스 직접 수정), [MCP](Crow Memory MCP 서버 도구 추가), [설정](VS Code 설정 자동 주입), [테스트](검증 기준)의 4가지 태그로 분류되며, 각 Wave의 기술적 구현 체크리스트는 20+ 항목으로 구성된다.

각 Wave는 "사용자가 느끼는 변화"를 중심으로 설계된다. Wave 1 "Unbreakable Flow"가 완료되면 사용자는 "VS Code를 켰을 때 Zoo Code가 이미 준비되어 있다"는 0초의 무의식을 경험한다. Wave 2 "Fearless YOLO"가 완료되면 "되돌려줘" 한 마디에 0.3초 만에 모든 코드가 원위치로 돌아간다. Wave 3 "Zero-Explanation"이 완료되면 "저번처럼"이라는 7글자만으로 AI가 모든 맥락을 읽는다. Wave 4 "Orchestra of One"이 완료되면 여러 AI가 동시에 작업하지만 사용자는 그 존재조차 의식하지 않는다. 이 4단계 진화는 단순한 기능 추가가 아니라, 사용자가 AI를 "도구"에서 "신경계 연장체"로 인식하는 패러다임 전환을 목표로 한다.

---

### Current State Assessment: 8차원 상세 진단

다음 표는 현재 Zoo Code의 8개 주요 차원을 세부 메트릭과 함께 진단한 것이다. 각 메트릭은 사용자가 실제로 경험하는 "흐름 단절"의 구체적 지속 시간과 인지적 비용을 정량화한다.

| 평가 차원 | 현재 점수 | 세부 메트릭 | 사용자가 경험하는 흐름 단절 | 기술적 근본 원인 |
|:---|:---:|:---|:---|:---|
| **세션 지속성** | 3/10 | Custom Mode 리셋: 매 재시작 시 3초 수동 선택 | VS Code 재시작 → "어제 어떤 모드였지?" → 모드 선택 클릭 → 맥락 재구성 | `globalState`에 모드 저장되나 자동 복원 로직 부재; SSE 서버 Extension 생명주기 종속 |
| | | SSE 서버 재연결 실패: 수동 재실행 필요 | VS Code 재시작 → Crow 기능 없음 → `start_crow_sse.bat` 수동 실행 | `detached: true` 프로세스 관리 미구현; PID 파일 기반 재탐색 로직 부재 |
| **모드 전환** | 4/10 | 수동 모드 선택: 3초/프로젝트 | 프로젝트 열기 → Zoo Code 패널 열기 → 드롭다운 클릭 → "Code + Crow Memory" 선택 | `onDidChangeWorkspaceFolders` 이벤트 활용 미구현; 프로젝트 메타데이터 기반 자동 감지 부재 |
| | | `AGENTS.md` 수동 복붙: 10초+ | 프로젝트 규칙 AI에게 전달 → 매 세션 반복 설명 | `FileSystemWatcher` 기반 자동 주입 미구현 |
| **YOLO 안전성** | 3/10 | `.yoloignore` 부재: AI가 모든 파일 접근 가능 | "혹시 `.env`를 건드리진 않을까?" 불안 속 YOLO 사용 | 파일 쓰기 인터셉터 미구현; Permission Gradation 매트릭스 부재 |
| | | 수동 undo: Git 명령어 직접 입력 | 빌드 실패 → 터미널에서 `git status` → `git stash` 결정 → 명령어 입력 | `yocto` lightweight 스냅샷 미구현; `Ctrl+Shift+Z` 단축키 미등록 |
| **컨텍스트 유지** | 4/10 | 1시간 후 "멍해짐" 현상 | "직설적 답변 선호"를 다시 설명해야 함; AI가 이전 지시 잊음 | `crow_compact` 자동 실행 부재; Extension Host 메모리 제약 내 대화 이력 비대화 |
| | | 세션 간 대화 초기화 | "어제 했던 걸 다시 설명해야 하나" 피로감 | 세션 종료 시 자동 compaction + 요약 저장 미구현 |
| **병렬 작업** | 2/10 | 단일 에이전트만 실행 | 긴 작업 시 대기 필요; 다른 작업 병렬 처리 불가 | `SubagentManager` 미구현; `child_process.spawn` 기반 별도 프로세스 미활용 |
| | | 백그라운드 작업 미지원 | 코드베이스 전체 검색 시 흐름 완전 끊김 | `withProgress` API 미활용; SSE 기반 진행 이벤트 미구현 |
| **외부 리소스** | 3/10 | 웹 검색 기능 부재 | "React 19 훅 문서 찾아줘" → 브라우저 열기 → Google 검색 → 복사 → VS Code로 돌아가기 → 붙여넣기 | Extension 내 Brave Search/Tavily API 호출 미구현; `crow_research` MCP 도구 부재 |
| **파일 탐색** | 5/10 | "어떤 파일을 열까요?" 질문 빈번 | 프로젝트 구조 AI가 모름 → 사용자가 직접 파일 경로 제공 | `ProjectTreeScanner` 미구현; `findFiles` 기반 트리 자동 주입 부재 |
| | | 파일 생성 위치 미결정 | "어디에 만들까요?" 질문 → 사용자가 경로 지정 | `arch` register 자동 확인 미구현 |
| **에러 복구** | 4/10 | 빌드 에러 수동 전달 | 터미널 에러 복사 → 채팅창 붙여넣기 → "고쳐줘" 입력 (30-60초) | `onDidEndTaskProcess` 이벤트 미활용; `crow_ingest_from_build` 자동 호출 부재 |
| | | AutoBuildFix 미구현 | 빌드 실패 → 수동 개입 → 재시도 반복 | `AutoBuildFixLoop` 클래스 미구현; oscillation 감지 부재 |

8개 차원의 현재 평균 3.2/10은 "AI 코딩 도구로서의 기본 기능은 작동하지만, 바이브코딩의 핵심 가정 — 'AI는 사용자의 신경계 연장체' — 이 지속적으로 깨지는 상태"를 의미한다. 사용자는 매 세션마다 AI를 "재설정"해야 하며, 매 오류마다 수동 개입해야 하고, 매 프로젝트마다 규칙을 "재교육"해야 한다. 이 누적 피로도가 4.2/10이라는 낮은 바이브 점수의 본질이다.

---

## Phase 0: Foundation (Week 0-2)

### 사용자 경험 스토리

> *"VS Code를 켰다. SSE 서버가 살아있었다. Custom Mode가 복원되었다."*

민수는 월요일 아침, 지난 주 금요일 밤에 작업하던 프로젝트를 열었다. VS Code가 로드되고, Zoo Code Extension이 활성화되는 데까지 약 2초가 걸렸다. 이 2초 동안 민수의 뇌는 "이번 주는 auth 리팩토링을 마무리해야지"라는 생각으로 채워져 있었다. VS Code가 완전히 로드되자, Zoo Code의 채팅창이 자동으로 열리면서 지난 주금요일의 대화 요약이 간략히 표시되었다. 상태바에는 "Crow Context: 87% fresh"가 조용히 깜빡였다.

민수는 아무것도 클릭하지 않았다. Custom Mode는 "Code + Crow Memory"로 자동 복원되었고, Crow SSE 서버는 VS Code가 종료된 주말 동안에도 살아있어 `crow.bin`의 모든 데이터가 그대로였다. 민수는 채팅창에 `"저번처럼 마무리해줘"`라고 입력했고, AI는 이미 모든 맥락을 알고 있었다. 민수는 이 과정에서 Zoo Code의 "존재"를 한 번도 의식하지 않았다. 그저 VS Code를 켰고, 코딩을 시작했을 뿐이다.

이것이 Phase 0 Foundation이 완성하는 경험이다. Phase 0은 Wave 1-4의 화려한 기능 이전에, "기초가 튼튼한 집"을 만드는 단계다. SSE 서버가 VS Code 종료 후에도 생존하고, Custom Mode가 5번 껐다 켜도 유지되며, Crow Memory의 연결이 끊어지지 않는 — 이것이 모든 상위 Wave가 성립하기 위한 전제조건이다.

---

### 기술적 구현 20+ 항목

Phase 0의 기술적 구현은 4개 카테고리로 구성되며, 총 22개 항목을 포함한다. [튜닝] 13개(59%), [MCP] 5개(23%), [설정] 3개(14%), [테스트] 1개(5%)의 분포는 Foundation 단계의 특성을 반영한다 — 인프라 구축은 Extension 자체 튜닝이 중심이 되며, MCP 도구 추가는 SSE 서버의 기본 기능 강화에 집중된다.

#### 카테고리 A: SSE 서버 생존 인프라 (6개 항목)

- [ ] **[튜닝]** `CrowServerManager` 클래스 구현: `child_process.spawn` with `detached: true` + `stdio: ['ignore', out, err]` + `child.unref()`로 SSE 서버를 VS Code 생명주기와 분리. PID 파일(`~/.zoo-code/crow/server.pid`) 기반 실행 상태 관리. `isRunning()` — `kill(pid, 0)` 시그널로 프로세스 존재 여부 확인.

- [ ] **[튜닝]** `reconnect()` 메서드 구현: VS Code 재시작 시 `server.pid` 파일 확인 → 프로세스 존재 시 `/health` 엔드포인트 헬스체크 → 응답 OK면 기존 서버 재사용, 응답 없으면 PID 파일 삭제 후 새 서버 시작.

- [ ] **[튜닝]** `onDeactivate()` 최소화 설계: `deactivate()` 훅에서 SSE 서버를 **종료하지 않음**. VS Code Issue #144118 [^141^]의 "비동기 cleanup 미완료" 버그를 회피하기 위한 의도적 설계. Extension 종료 시 서버는 살아남아 `crow.bin` 데이터 유지.

- [ ] **[MCP]** Crow SSE 서버 `/health` 엔드포인트 추가: HTTP GET `/health` → `{"status": "ok", "crowBinAccessible": true, "uptimeMs": ...}` 응답. 서버 상태 + `crow.bin` 접근 가능성 이중 확인.

- [ ] **[설정]** `tasks.json` 자동 생성: `.vscode/tasks.json`에 `"crow:sse:keepalive"` 태스크 추가 — `presentation.reveal: silent`로 백그라운드 실행, 60초 간격 헬스체크.

- [ ] **[테스트]** "5번 껐다 켜도 SSE 서버 생존" 검증: VS Code 종료 → 5초 대기 → 재시작 → `reconnect()` 성공 → `crow.bin` 데이터 접근 확인. Windows/macOS/Linux 3OS 크로스 검증.

#### 카테고리 B: Custom Mode 자동 복원 (5개 항목)

- [ ] **[튜닝]** `restoreLastCustomMode()` 구현: `activate()` 시 `globalState.get('lastCustomMode')` 확인 → 현재 모드와 다륾면 `config.update('customMode', lastMode, true)`로 자동 복원. 상태바에 `"'Code + Crow Memory' 모드로 자동 복원됨"` 3초 표시 후 자동 사라짐.

- [ ] **[튜닝]** 모드 변경 실시간 저장: `workspace.onDidChangeConfiguration` 이벤트에서 `e.affectsConfiguration('zooCode.customMode')` 감지 → 변경 즉시 `globalState.update('lastCustomMode', currentMode)`. `deactivate()`의 비동기 불안정성 [^345^] 회피 — "상태 변경 즉시 저장" 원칙.

- [ ] **[튜닝]** `setKeysForSync` 활용: `globalState.setKeysForSync(['lastCustomMode', 'zooCode.settings'])`로 Settings Sync 대상 키 등록 — 다중 머신 간 Custom Mode 동기화 [^55^].

- [ ] **[설정]** `.zoo/config.json` 스키마 정의: `{"version": 1, "defaultMode": "code_plus_crow", "crow": {"autoCompactInterval": 600}}` — 프로젝트별 기본 모드를 Git 버전 관리.

- [ ] **[MCP]** 모드 변경 이벤트 Crow 저장: 모드 변경 시 `crowIngest({register: 'life_context', content: 'Mode changed to: X', metadata: {source: 'auto_restore'}})` — 세션 연속성 기록.

#### 카테고리 C: globalState 안전성 강화 (5개 항목)

- [ ] **[튜닝]** `SafeStateManager` 클래스 구현: `globalState.update()`의 Promise 취소 버그 [#141] 회피 — 모든 상태 저장을 동기 래퍼로 감싸고, 중요한 상태는 "변경 즉시 저장 + 주기적 백업" 이중화.

- [ ] **[튜닝]** 대화 이력 `crow.bin` 위임: Extension Host 메모리 내 대화 이력 비대화 방지 — `globalState`에는 요약된 메타데이터(50KB/세션)만 저장, 원본 이력은 Crow `context` register에 위임. Roo Code Issue #3784 [^234^]의 "excessive globalState usage" 크래시 방지.

- [ ] **[튜닝]** JSON 직렬화 타입 손실 방지: `globalState`의 JSON 직렬화로 Function, RegExp, Map, Set이 손실되는 문제 완화 — 저장 전 `toJSON()`/`fromJSON()` 직렬화 래퍼 적용.

- [ ] **[MCP]** 세션 종료 시 `crow_compact()` 자동 호출: `deactivate()` 훅에서 `crow_compact()` 호출 → 대화 요약 → `life_context` register 저장. `deactivate()`의 비동기 불완전 보정을 위해 주기적 저장(5분 간격 `onWillSaveTextDocument` 트리거) 병행.

- [ ] **[설정]** `globalState` 용량 모니터링: 저장 전 `Buffer.byteLength(JSON.stringify(data))`로 크기 확인 → 5MB 임계값 초과 시 경고 + 오래된 데이터 Crow로 이관.

#### 카테고리 D: 검증 및 모니터링 (6개 항목)

- [ ] **[튜닝]** Foundation 검증 명령어: `Zoo: Verify Foundation` 명령 팔레트 등록 — SSE 서버 상태, `globalState` 건강도, Crow 연결 상태, Custom Mode 복원 여부를 한 번에 진단.

- [ ] **[튜닝]** 상태바 Foundation 인디케이터: `"Crow: Connected | Mode: Code + Crow | Context: 87% fresh"` — 3가지 핵심 상태를 한눈에 확인.

- [ ] **[튜닝]** 로깅 파이프라인: `~/.zoo-code/logs/foundation.log`에 SSE 서버 시작/재연결/모드 복원 이벤트 기록 — 디버깅 및 검증 추적.

- [ ] **[MCP]** `crow.bin` 무결성 검증: Extension 활성화 시 `crow.bin` magic number(`CROW`) + 버전 확인 → 손상 시 백업에서 복구 + 사용자 알림.

- [ ] **[MCP]** SSE 서버 자동 재시작: 헬스체크 3회 연속 실패 시 자동 재시작 — `server.pid`가 stale 상태(프로세스는 죽었으나 파일은 남아있음) 감지 및 정리.

- [ ] **[튜닝]** Extension Host 재시작 감지: Extension Host crash recovery 후 `activate()`가 다시 호출될 때 `lastSessionStart` 타임스탬프 비교 → 비정상 종료 감지 → Crow에 `"Session crashed, restored"` 이벤트 저장.

```typescript
// [튜닝] Phase 0 Foundation 핵심 — activate() 시퀀스 (의사코드)
export async function activate(context: vscode.ExtensionContext): Promise<void> {
  // 1단계: Crow SSE 서버 재연결 (생존 확인 또는 새로 시작)
  const crowServer = new CrowServerManager(context);
  await crowServer.reconnect(); // PID 파일 → 헬스체크 → 재연결/새시작

  // 2단계: 마지막 Custom Mode 자동 복원 (globalState → 설정 적용)
  await restoreLastCustomMode(context); // lastCustomMode 읽기 → 모드 복원

  // 3단계: SafeStateManager 초기화 (안전한 상태 저장 파이프라인)
  const safeState = new SafeStateManager(context);
  safeState.activate(); // 변경 즉시 저장 + 주기적 백업

  // 4단계: Crow.bin 무결성 검증 (손상 시 백업에서 복구)
  await verifyCrowBinIntegrity();

  // 5단계: 세션 시작 이력 기록 (crash 감지용)
  const lastStart = context.globalState.get<number>('lastSessionStart');
  if (lastStart && Date.now() - lastStart < 30000) {
    // 30초 내 재시작 = 비정상 종료로 간주
    await crowIngest({ register: 'life_context', 
      content: 'Session crashed and restored', metadata: { polarity: -0.5 } });
  }
  await context.globalState.update('lastSessionStart', Date.now());

  // 6단계: 상태바 Foundation 인디케이터 표시
  showFoundationStatusBar(context);
}
```

---

### Crow Memory 연동 포인트

Phase 0의 모든 설계안은 Crow Memory의 특정 도구/레지스터와 연동된다. 이 연동은 "Foundation이 Crow를 위한 물리적 기반을 제공하고, Crow가 Foundation에 기억의 지속성을 부여하는" 쌍방향 구조다.

| Foundation 구성요소 | Crow 연동 도구/레지스터 | 연동 방향 | 목적 |
|:---|:---|:---:|:---|
| `CrowServerManager` (SSE 서버 생존) | `crow.bin` 파일 자체 | ←→ | 서버가 살아있어야 `crow.bin` 접근 가능; `crow.bin` 무결성이 메모리 가치 보장 |
| `reconnect()` (재연결) | `life_context` register | → | 재연결 성공/실패 이벤트를 `life_context`에 저장 → 세션 연속성 기록 |
| `restoreLastCustomMode()` (모드 복원) | `life_context` register | → | 모드 변경 이력 저장 → "사용자가 이 프로젝트에서 이 모드를 선호함" 학습 데이터 |
| `SafeStateManager` (상태 안전성) | `context` register | ←→ | `globalState` 용량 초과 시 대화 이력을 `context` register로 이관 |
| `crow_compact()` (자동 압축) | `life_context` register | → | 세션 요약을 `life_context`에 저장 → 다음 세션의 "기억" 원천 |
| `verifyCrowBinIntegrity()` (검증) | `crow.bin` magic/header | ←→ | 파일 손상 감지 → 백복구 → 데이터 신뢰성 보장 |
| Foundation 검증 명령어 | `crow_manage_backup` | ← | 검증 전 `crow.bin` 백업 생성 — 안전한 검증 환경 조성 |

이 연동 구조는 "Crow as the Glue" Insight [^insight4^]의 첫 번째 구현이다. Foundation 단계에서 Crow와 Zoo Code Extension의 연결이 튼튼해지면, Wave 1-4의 모든 상위 기능은 이 연결을 기반으로 자연스럽게 통합된다.

---

### 검증 기준

Phase 0 Foundation의 완료는 두 가지 사용자 중심 검증 기준으로 판단된다. 이 기준은 기술적 구현의 "완료"가 아니라 사용자 경험의 "확신"을 측정한다.

**검증 기준 1: "5번 껐다 켜도 Custom Mode 유지"**

구체적인 검증 시나리오: 사용자가 "Code + Crow Memory" 모드로 작업 중 VS Code를 종료하고, 5번에 걸쳐 VS Code를 종료/재시작한다. 각 재시작 후 Zoo Code Extension이 활성화되면, (a) Custom Mode가 "Code + Crow Memory"로 자동 설정되어 있고, (b) 사용자가 모드를 수동으로 변경하지 않았다는 사실이 유지되며, (c) 상태바에 복원 알림이 표시되었다가 3초 내에 자동 사라진다. 이 검증은 `globalState`의 SQLite 기반 지속성 [^54^]과 `setKeysForSync()`의 Settings Sync 통합 [^55^]을 실질적으로 확인한다.

**검증 기준 2: "SSE 서버 VS Code 종료 후 생존"**

구체적인 검증 시나리오: VS Code 실행 중 Crow SSE 서버가 정상 작동함을 `/health` 엔드포인트로 확인한다. VS Code를 완전히 종료하고, OS의 프로세스 목록(`ps aux | grep crow` 또는 Windows 작업 관리자)에서 SSE 서버 프로세스가 여전히 실행 중임을 확인한다. 5분 후 VS Code를 재시작하면, Zoo Code Extension의 `reconnect()`가 기존 서버를 자동으로 재탐색하고 `crow.bin` 데이터에 정상 접근함을 확인한다. 이 검증은 `detached: true` + `child.unref()` + PID 파일 관리의 3중 메커니즘을 실질적으로 확인한다.

**기술적 회귀 테스트**: Phase 0 완료 시 실행하는 자동화 테스트 스위트.

```typescript
// Phase 0 회귀 테스트 스위트 (의사코드)
describe('Phase 0 Foundation', () => {
  test('Custom Mode 5회 복원', async () => {
    const expectedMode = 'code_plus_crow';
    for (let i = 0; i < 5; i++) {
      await simulateVSCodeRestart();
      const actualMode = getCurrentMode();
      expect(actualMode).toBe(expectedMode);
    }
  });

  test('SSE 서버 VS Code 종료 후 생존', async () => {
    await crowServer.start();
    expect(crowServer.isRunning()).toBe(true);
    await simulateVSCodeShutdown();
    expect(crowServer.isRunning()).toBe(true); // detached: true로 생존
    await simulateVSCodeRestart();
    const reconnected = await reconnect();
    expect(reconnected).toBe(true);
  });

  test('crow.bin 무결성 검증', async () => {
    const integrity = await verifyCrowBinIntegrity();
    expect(integrity.valid).toBe(true);
    expect(integrity.magic).toBe('CROW');
  });

  test('globalState 용량 안전성', async () => {
    const stateSize = await getGlobalStateSize();
    expect(stateSize).toBeLessThan(5 * 1024 * 1024); // 5MB 미만
  });
});
```

---

### 바이브 점수 변화

Phase 0 Foundation 설치 후, 8개 주요 차원에서 +0.5~1.0의 바이브 점수 상승이 추정된다. 이 상승은 "새로운 기능"의 추가가 아니라 "기존 기능의 신뢰성 확보"에서 비롯된다 — 사용자가 "이 기능이 작동할까?"라는 불확실성을 "이 기능은 항상 작동한다"는 확신으로 대체하는 것.

| 평가 차원 | Phase 0 이전 | Phase 0 이후 | 상승 폭 | Phase 0 기여 요소 |
|:---|:---:|:---:|:---:|:---|
| 세션 지속성 | 3/10 | 4/10 | +1.0 | SSE 서버 생존, Custom Mode 자동 복원 |
| 모드 전환 | 4/10 | 4.5/10 | +0.5 | `lastCustomMode` 저장, `.zoo/config.json` 스키마 |
| YOLO 안전성 | 3/10 | 3/10 | — | Phase 0은 YOLO 기능 미포함 (Wave 2에서 구현) |
| 컨텍스트 유지 | 4/10 | 4.5/10 | +0.5 | `crow_compact` 자동 호출 인프라, `globalState` 안전성 |
| 병렬 작업 | 2/10 | 2/10 | — | Phase 0은 병렬 기능 미포함 (Wave 4에서 구현) |
| 외부 리소스 | 3/10 | 3/10 | — | Phase 0은 외부 검색 미포함 (Wave 1-6에서 구현) |
| 파일 탐색 | 5/10 | 5/10 | — | Phase 0은 트리 주입 미포함 (Wave 1-5에서 구현) |
| 에러 복구 | 4/10 | 4/10 | — | Phase 0은 AutoBuildFix 미포함 (Wave 2-5에서 구현) |
| **평균** | **3.5/10** | **4.2/10** | **+0.7** | |

Phase 0의 +0.7 상승은 겉보기에 작아 보일 수 있다. 하지만 이 0.7은 모든 후속 Wave가 성립하기 위한 **전제조건**이다. SSE 서버가 죽으면 Wave 3의 크로스-세션 메모리가 작동하지 않는다. `globalState`가 불안정하면 Wave 1의 세션 지속성이 물거품이 된다. Custom Mode가 복원되지 않으면 Wave 3의 제로-익스플레이네이션이 시작부터 깨진다. Phase 0의 0.7은 "숫자의 변화"가 아니라 "가능성의 기반"이다.

---

### 로드맵 타임라인

| 단계 | 기간 | 총 기술 항목 | [튜닝] | [MCP] | [설정] | [테스트] |
|:---|:---|:---:|:---:|:---:|:---:|:---:|
| **Phase 0: Foundation** | Week 0-2 | 22 | 13 (59%) | 5 (23%) | 3 (14%) | 1 (5%) |
| **Wave 1: Unbreakable Flow** | Week 2-6 | 24 | 16 (67%) | 5 (21%) | 2 (8%) | 1 (4%) |
| **Wave 2: Fearless YOLO** | Week 6-12 | 26 | 15 (58%) | 7 (27%) | 3 (12%) | 1 (4%) |
| **Wave 3: Zero-Explanation** | Week 12-20 | 23 | 14 (61%) | 7 (30%) | 1 (4%) | 1 (4%) |
| **Wave 4: Orchestra of One** | Week 20-30 | 22 | 14 (64%) | 8 (36%) | 0 | 0 |
| **합계** | **30주 (약 7개월)** | **117** | **72 (62%)** | **32 (27%)** | **9 (8%)** | **4 (3%)** |

전체 117개 기술 항목 중 72개(62%)가 Zoo Code Extension 자체 튜닝, 32개(27%)가 MCP 도구 추가인 점에 주목해야 한다. 이 비율은 본 보고서의 핵심 설계 철학 — "VS Code Extension API의 극한 활용" — 의 기술적 표현이다. Crow Memory는 모든 Wave의 중앙 허브로서 기능하지만, 실제 구현의 대부분은 Extension 낶에서 이루어진다. 이것이 Insight 1 "Terminal Escape 패턴의 역설" [^insight1^]이 제안하는 경쟁 전략이다 — OpenCode와 Claude Code가 터미널을 벗어나 더 나은 성능을 얻었지만 IDE 네이티브 UX를 포기한 반면, Zoo Code는 VS Code 안에 머물면서 그들의 핵심 기능을 대체 구현함으로써 "설치 마찰 0, 학습 곡선 0"이라는 유일한 니치를 점유한다.

전체 4-Wave 로드맵이 완료되면 Zoo Code의 바이브 점수는 현재 4.2/10에서 목표 9.5/10으로 도약한다. 이 도약의 본질은 기술적 성능의 향상이 아니라 "사용자가 AI의 존재를 의식하는 횟수"의 감소다. 현재 사용자는 하루 평균 15-20회 AI의 존재를 의식한다 — 모드 선택, 에러 복사, 규칙 재설명, 파일 경로 지정 등. 4-Wave 완료 후 이 횟수는 1-2회로 감소한다. 그 1-2회조차 "문제"가 아니라 "의도적인 개입" — 사용자가 원할 때 AI의 작업을 확인하고 조정하는 투명한 통제권 — 이다. 이것이 "완벽한 자동화"가 아닌 "완벽하게 예측 가능한 자동화" [^insight5^], 바로 바이브코딩의 이상이다.


---

# 1. Wave 1: Unbreakable Flow — Flow Keeper의 6차원 흐름 수호

당신이 VS Code를 켰다. 어제 밤 11시까지 조율한 Custom Mode가 사라져 있다. "Code + Crow Memory" 모드를 다시 클릭하는 3초 동안, 당신의 뇌는 어제의 맥락에서 벗어나 버렸다. 터미널에 `npm run build`를 치고 에러가 쏟아지는데, 에러 메시지를 복사해서 채팅창에 붙여넣는 순간, 당신은 더 이상 "코딩의 흐름"에 있지 않다. 당신은 데이터 입력원이 되었다. 1시간이 지나면 AI는 당신이 "직설적 답변을 선호한다"는 사실을 잊어버리고, 다시 설명하기 시작한다. "어떤 파일을 열까요?"라는 질문이 나올 때마다 당신은 한숨을 쉰다. React 19 문서를 찾아달라고 했더니 브라우저를 직접 열어 복사붙여넣기를 해야 한다면, 이것은 바이브코딩이 아니라 바이브수동코딩이다.

Wave 1은 이 모든 흐름 단절 지점을 픽셀 단위로 매핑하고, VS Code Extension API의 경계 내에서 — 그리고 Crow Memory의 7개 레지스터와의 긴장 속에서 — 하나하나 메우는 작업이다. OpenCode는 Bun 서버로, Claude Code는 git worktree로 해결한 문제들을, 우리는 `ExtensionContext.globalState`와 `child_process.spawn`으로, `FileSystemWatcher`와 `TaskPresentationOptions.reveal: silent`로 해결해야 한다. 이것은 열세한 도구로 더 어려운 문제를 푸는 작업이지만, 그 제약 속에서 나오는 솔루션은 사용자가 "설치"를 의식하지 않는 유일한 경험을 만들어낸다.

---

## 1.1 Flow Breaker 매트릭스: 6개 차원 × 3개 툴 비교

바이브코딩에서 "흐름"이란 사용자가 AI의 존재를 의식하지 않는 상태다. 10점은 사용자가 그 기능의 존재조차 모르는 상태, 1점은 매 작업마다 수동 개입이 필요한 상태를 의미한다. 다음 매트릭스는 Zoo Code, OpenCode, Claude Code가 6개 흐름 차원에서 각각 어떤 점수를 받는지 비교한 것이다. 모든 점수는 조사 기반 추정치이며, 실제 사용자 테스트 결과가 아닌 아키텍처적 잠재력과 구현 상태를 종합하여 산출되었다.

| 흐름 차원 | Zoo Code (현재) | OpenCode | Claude Code | 측정 기준 |
|:----------|:---------------:|:--------:|:-----------:|:----------|
| 세션 지속성 (Session Survivability) | 3/10 [^234^] | 8/10 [^327^] | 7/10 [^152^] | IDE 재시작 후 대화 맥락 복원률 |
| 모드 전환 마찰 (Mode Switching Friction) | 4/10 | N/A | N/A | 프로젝트 열기 → 코딩 시작까지 클릭 수 |
| 빌드-코드-피드백 루프 (Build Feedback Loop) | 4/10 [^252^] | 6/10 [^207^] | 8/10 [^316^] | 빌드 에러 → AI 인지 → 수정까지 시간(초) |
| 컨텍스트 로트 (Context Rot) | 4/10 [^234^] | 7/10 [^214^] | 6/10 [^401^] | 1시간 코딩 후 AI의 "기억력" 유지율 |
| 파일 탐색/생성 마찰 (File Navigation Friction) | 5/10 [^527^] | 5/10 | 6/10 [^450^] | "어떤 파일을 열까요?" 질문 빈도 |
| 외부 리소스 탐색 (External Resource Loop) | 3/10 | 7/10 [^501^] | 7/10 [^501^] | 웹 검색 결과 → 코드 적용까지 클릭 수 |

**세션 지속성**에서 Zoo Code의 3점은 VS Code Extension Host가 재시작되면 Custom Mode가 리셋되고, Crow SSE 서버가 재연결에 실패하는 현실을 반영한다 [^234^]. 반면 OpenCode의 8점은 SQLite DB(`opencode.db`)가 프로세스와 무관하게 디스크에 지속되며 `--continue` 플래그로 즉시 복원 가능한 아키텍처 덕분이다 [^327^]. Claude Code의 7점은 JSONL 파일 기반 세션 저장과 `/resume` 명령이 훌륭하지만, 터미널 종료 시 프로세스가 함께 죽는 점에서 1점 감점되었다 [^152^].

**모드 전환 마찰**은 터미널 기반 도구(OpenCode, Claude Code)에게 의미 없는 차원이다 — 이들은 "모드"라는 개념 자체가 없다. 하지만 VS Code Extension 기반 Zoo Code에게는 매 프로젝트 열기마다 "Code + Crow Memory" 모드를 수동 선택해야 하는 3초짜리 마찰이 존재한다. 이 3초는 사용자가 어제의 맥락을 되찾는 데 걸리는 시간이며, 바이브를 깨는 대표적 지점이다.

**빌드-코드-피드백 루프**에서 Zoo Code의 4점은 `npm run build` 후 터미널 에러를 복사-붙여넣기해야 하는 수동 파이프라인을 반영한다 [^252^]. Claude Code의 8점은 `BashTool`의 `EndTruncatingAccumulator`로 stderr/stdout을 자동 캡처하고, LSP 진단을 자동으로 컨텍스트에 주입하는 폐쇄 루프 때문이다 [^316^]. OpenCode의 6점은 `LSP.touchFile()` → `LSP.diagnostics()` 피드백 루프가 존재하나 터미널 환경에서의 빌드 통합이 VS Code만큼 매끄럽지 않다는 점을 반영한다 [^207^].

**컨텍스트 로트**는 장시간 코딩 시 AI가 "멍해지는" 현상이다. Zoo Code의 4점은 globalState에 저장되는 대화 이력이 Extension Host 메모리 한계(~2-4GB) [^172^] 내에서 점차 비대해지며, 요약(compaction) 메커니즘이 제한적이기 때문이다. OpenCode의 7점은 2-phase context compaction(40K 토큰 기준 pruning → LLM summarization) [^214^]이 이 문제를 효과적으로 관리하기 때문이다. Claude Code의 6점은 3계층 compaction 시스템 [^401^]이 존재하지만, Auto Memory의 200줄 제한으로 인해 장기 맥락의 일부가 소실될 수 있다는 점에서 1점 감점되었다.

**파일 탐색 마찰**에서 Zoo Code의 5점은 AI가 종종 "어떤 파일을 열까요?"라고 묻는 상황을 반영한다. 이는 프로젝트 트리가 LLM 컨텍스트에 자동 주입되지 않기 때문이다 [^527^]. Claude Code의 6점은 `/init` 명령의 프로젝트 스캔과 `@Codebase` 시맨틱 검색이 이 문제를 부분적으로 해결하지만, 실시간 프로젝트 트리 주입은 여전히 미흡하다 [^450^].

**외부 리소스 탐색**에서 Zoo Code의 3점은 웹 검색 기능이 전무하여 수동 브라우저 복붙이 필요한 현실을 반영한다. OpenCode와 Claude Code는 각각 내장 WebSearch 도구 [^501^]와 Brave Search MCP 통합으로 이 루프를 자동화하여 동일한 7점을 기록했다.

Zoo Code의 평균 흐름 점수는 3.83/10이다. Wave 1의 목표는 이 점수를 8.5/10 이상으로 끌어올리는 것이다.

---

## 1.2 조사 차원 1: 세션 지속성 (Session Survivability within VS Code)

### 1.2.1 현재 상태 분석: 흐름이 끊기는 4개 지점

Zoo Code 사용자의 세션 지속성을 분석하면, 정확히 4개의 흐름 단절 지점이 식별된다.

**첫 번째 단절: Custom Mode 리셋.** VS Code를 완전히 종료하고 재시작하면, Zoo Code의 Custom Mode 선택 상태가 초기화된다. 어제 "Code + Crow Memory" 모드에서 작업했던 사용자는 오늘 다시 그 모드를 수동으로 선택해야 한다. 이 3초의 클릭 동안 사용자의 뇌는 "내가 어제 무엇을 하고 있었지?"라는 질문에서부터 코딩 맥락을 재구성해야 한다. 이것은 기술적으로는 사소한 문제지만, 바이브코딩 관점에서는 치명적이다 — 사용자가 AI의 "성격"을 다시 설정해야 한다는 사실 자체가 동반자 관계의 연속성을 깨뜨린다.

**두 번째 단절: SSE 서버 재연결 실패.** Crow Memory의 SSE 서버는 기본적으로 VS Code Extension의 생명주기에 종속된다. Extension이 비활성화되면 SSE 연결이 끊어지고, VS Code 재시작 시 서버가 이미 떠 있더라도 Zoo Code Extension이 이를 재탐색하지 못하는 경우가 빈번하다. 사용자는 `start_crow_sse.bat`을 수동으로 다시 실행하거나, 아니면 Crow 기능 없이 Zoo Code를 사용해야 한다.

**세 번째 단절: Extension Host 재시작 시 상태 소멸.** VS Code의 Extension Host는 별도의 Node.js 프로세스로 실행되며 [^162^], 이 프로세스가 재시작될 때( crash recovery, 업데이트, 또는 메모리 압박에 의한 강제 재시작) Extension의 메모리 내 상태가 완전히 소멸된다. `ExtensionContext.globalState`는 SQLite 기반으로 지속되지만 [^54^], 이것은 key-value 저장소일 뿐 전체 세션 상태를 복원하지는 못한다.

**네 번째 단절: 대화 맥락의 불완전한 복원.** `globalState`에 저장된 대화 이력은 JSON 직렬화를 거치며 [^51^] Function, RegExp, Map, Set 등의 타입 정보가 손실된다. 또한 `globalState`에 과도한 양의 히스토리를 저장하면 VS Code 경고 및 확장 크래시가 발생하는 것이 확인되었다 [^234^]. Roo Code Issue #3784에서는 "excessive globalState usage"로 인한 성능 저하가 보고되었으며, 이는 대용량 대화 이력을 globalState에 저장하는 패턴의 근본적 한계를 드러낸다.

### 1.2.2 `ExtensionContext.globalState` vs `workspaceState` 기술 분석

VS Code Extension API는 `ExtensionContext` 객체를 통해 두 가지 Memento 기반 저장소를 제공한다 [^51^]. 세션 지속성을 설계하기 위해서는 이 두 저장소의 정확한 특성을 이해해야 한다.

**globalState**는 사용자의 애플리케이션 지원 디렉토리 내 SQLite 데이터베이스(`state.vscdb`)에 저장된다 [^54^]. macOS 기준 경로는 `~/Library/Application Support/Code/User/globalStorage/state.vscdb`이다. 모든 워크스페이스에서 공유되며, VS Code 재시작 후에도 지속된다. `setKeysForSync()` 메서드로 특정 키를 Settings Sync 동기화 대상으로 지정할 수 있어 여러 머신 간 상태를 공유할 수 있다 [^55^].

**workspaceState**는 워크스페이스별 해시 디렉토리 내에 동일하게 SQLite 형태로 저장된다 [^54^]. macOS 기준 `~/Library/Application Support/Code/User/workspaceStorage/<workspace-hash>/state.vscdb`이다. 현재 열린 워크스페이스에 한정된 key-value 저장이며, 프로젝트별 설정에 적합하다.

**결정적 차이점**: Zoo Code의 세션 지속성 설계에서 globalState와 workspaceState를 분리 사용하는 것이 핵심이다. Custom Mode 선택 상태, 마지막 활성화된 Crow 레지스터, 세션별 메타데이터는 globalState에 저장하여 워크스페이스를 이동하더라도 유지되게 한다. 반면 프로젝트 특화 설정(빌드 명령, 파일 트리 캐시)은 workspaceState에 저장하여 프로젝트 간 간섭을 방지한다.

**치명적 제약**: `deactivate()` 함수 내에서 `globalState.update()`를 호출하면 Promise가 즉시 취소된다 [^141^]. GitHub Issue #144118은 이를 명확한 버그로 보고하고 있으며, VS Code 팀은 Extension 비활성화 시 비동기 cleanup이 완료될 때까지 기다리지 않는다는 사실을 인정했다. 이는 "VS Code 종료 직전 상태 저장"이라는 패턴이 근본적으로 불가능함을 의미한다.

### 1.2.3 SSE 서버 생존 전략: `child_process.spawn` with `detached: true`

Crow Memory의 SSE 서버를 VS Code 종료 후에도 생존시키는 것은 Wave 1의 핵심 기술 과제다. 이는 VS Code Extension API의 경계를 넘지 않으면서도 프로세스 수준의 생명주기 분리를 달성해야 한다.

Node.js의 `child_process.spawn`은 `detached: true` 옵션을 통해 부모 프로세스로부터 자식 프로세스를 분리할 수 있다 [^175^][^176^]. 이 옵션을 사용하면 VS Code 메인 프로세스가 종료되어도 자식 프로세스는 OS의 init 시스템(또는 현대 OS에서는 systemd/session manager)에 입양되어 계속 실행된다.

그러나 VS Code에는 특수한 제약이 있다. GitHub Issue #90351 [^180^]에 따륜, VS Code 내에서 `detached: true`로 생성한 자식 프로세스가 VS Code 종료 시 함께 종료되는 문제가 보고되었다. 이는 VS Code의 프로세스 그룹 관리 때문이다. 이 문제를 우회하려면 `stdio`를 완전히 분리하고 `unref()`를 호출하는 것이 필수적이다.

**[튜닝] Crow SSE 서버 분리 실행 패턴**은 다음과 같이 구현된다:

```typescript
// [튜닝] Crow SSE 서버 분리 실행 — VS Code 종료 후에도 생존
import { spawn } from 'child_process';
import * as fs from 'fs';
import * as path from 'path';

interface CrowServerConfig {
  port: number;           // 기본 9020
  crowBinPath: string;    // ~/.zoo-code/crow/crow.bin
  logPath: string;        // ~/.zoo-code/crow/server.log
  pidPath: string;        // ~/.zoo-code/crow/server.pid
}

class CrowServerManager {
  private config: CrowServerConfig;

  constructor(private context: vscode.ExtensionContext) {
    const crowHome = path.join(process.env.HOME!, '.zoo-code', 'crow');
    this.config = {
      port: 9020,
      crowBinPath: path.join(crowHome, 'crow.bin'),
      logPath: path.join(crowHome, 'server.log'),
      pidPath: path.join(crowHome, 'server.pid')
    };
  }

  // 서버가 이미 떠 있는지 PID 파일로 확인
  isRunning(): boolean {
    try {
      const pid = fs.readFileSync(this.config.pidPath, 'utf-8').trim();
      // 프로세스 존재 여부 확인 (kill 0 시그널)
      process.kill(parseInt(pid), 0);
      return true;
    } catch {
      return false;
    }
  }

  // [튜닝] detached: true로 SSE 서버 시작 — VS Code와 생명주기 분리
  async start(): Promise<number> {
    if (this.isRunning()) {
      const existingPid = fs.readFileSync(this.config.pidPath, 'utf-8').trim();
      console.log(`[Crow] 서버가 이미 실행 중: PID ${existingPid}`);
      return parseInt(existingPid);
    }

    const out = fs.openSync(this.config.logPath, 'a');
    const err = fs.openSync(this.config.logPath, 'a');

    const child = spawn('node', [
      path.join(this.context.extensionPath, 'dist', 'crow_mcp_server.js'),
      '--port', String(this.config.port),
      '--bin', this.config.crowBinPath
    ], {
      detached: true,           // 부모와 분리 — VS Code 종료 후에도 생존
      stdio: ['ignore', out, err], // stdio 완전 분리 (필수!)
      env: { ...process.env, CROW_PORT: '9020' }
    });

    child.unref(); // 부모 이벤트 루프에서 제거 — 종료 시 대기하지 않음

    // PID 파일에 기록 — 재시작 시 재탐색용
    fs.writeFileSync(this.config.pidPath, String(child.pid));

    console.log(`[Crow] SSE 서버 시작: PID ${child.pid}, 포트 ${this.config.port}`);
    return child.pid!;
  }

  // [튜닝] 기존 서버에 재연결 — VS Code 재시작 시 호출
  async reconnect(): Promise<boolean> {
    if (this.isRunning()) {
      const pid = fs.readFileSync(this.config.pidPath, 'utf-8').trim();
      // 서버 헬스체크
      try {
        const response = await fetch(`http://localhost:${this.config.port}/health`);
        if (response.ok) {
          console.log(`[Crow] 기존 서버 재연결 성공: PID ${pid}`);
          return true;
        }
      } catch {
        // 서버가 응답하지 않으면 PID 파일 삭제 후 재시작
        fs.unlinkSync(this.config.pidPath);
      }
    }
    // 서버가 없으면 새로 시작
    await this.start();
    return true;
  }

  // Extension 비활성화 시 — 서버는 종료하지 않음 (의도적!)
  onDeactivate(): void {
    // 중요: 여기서 서버를 kill하지 않는다.
    // detached 프로세스는 VS Code와 독립적으로 생존해야 한다.
    // 다만 연결 정볼만 globalState에 저장
    this.context.globalState.update('crowServerLastPort', this.config.port);
  }
}
```

이 패턴의 핵심은 `deactivate()`에서 서버를 종료하지 않는다는 점이다. Extension이 비활성화되어도 SSE 서버는 살아남아 `crow.bin`의 데이터를 유지하며, 다음 VS Code 시작 시 `reconnect()`가 기존 서버를 재탐색한다. 이는 "Extension이 죽어도 기억은 살아있다"는 경험을 만들어낸다.

### 1.2.4 `deactivate()` 훅 설계: 비동기 작업의 불완전한 보장

VS Code Extension의 `deactivate()` 훅에는 치명적인 제약이 있다. VS Code는 확장을 비활성화할 때 비동기 cleanup이 완료될 때까지 기다리지 않고 강제 종료할 수 있다 [^345^][^268^]. 공식 문서에는 "Note that asynchronous dispose-functions aren't awaited"라고 명시되어 있다 [^51^].

이 제약은 두 가지 설계 결정을 강제한다. 첫째, `deactivate()`에서는 동기 작업만 수행하거나 가능한 빨리 resolve해야 한다. 둘째, 중요한 상태 저장은 VS Code 종료 "직전"이 아니라, 상태가 변경될 "즉시" 이루어져야 한다.

**[튜닝] 안전한 상태 저장 패턴**은 다음 원칙을 따른다:

```typescript
// [튜닝] 안전한 상태 저장 — 상태 변경 즉시 저장, 종료 시에는 minimal cleanup
export function activate(context: vscode.ExtensionContext): void {
  const crowServer = new CrowServerManager(context);

  // activate() 즉시 기존 서버 재연결 시도
  crowServer.reconnect().catch(console.error);

  // Custom Mode 변경 시마다 즉시 저장 (종료 직전 저장에 의존하지 않음)
  const modeWatcher = vscode.workspace.onDidChangeConfiguration(async (e) => {
    if (e.affectsConfiguration('zooCode.customMode')) {
      const currentMode = vscode.workspace.getConfiguration('zooCode').get('customMode');
      await context.globalState.update('lastCustomMode', currentMode);
      // [MCP] Crow에도 모드 변경 이력 저장
      await crowIngest({
        content: `Mode changed to: ${currentMode}`,
        register: 'life_context',
        metadata: { source: 'zoo_code_extension', ttl: 86400 }
      });
    }
  });
  context.subscriptions.push(modeWatcher);
}

export function deactivate(): Promise<void> {
  // [튜닝] 최소한의 동기 정리만 수행
  // Promise를 반환하지만 VS Code가 기다리지 않을 수 있음 [^141^]
  return new Promise((resolve) => {
    // 동기적으로 PID 파일 확인만 수행
    console.log('[Crow] Extension 비활성화. 서버는 계속 실행됩니다.');
    resolve(); // 즉시 resolve
  });
}
```

### 1.2.5 `lastCustomMode` 자동 복원

Custom Mode 선택 상태를 자동 복원하는 것은 세션 지속성의 가장 직접적인 개선이다. `globalState`에 저장된 마지막 모드를 Extension 활성화 시 자동으로 적용하면, 사용자는 "모드를 선택하는" 행위 자체를 잊어버린다.

```typescript
// [튜닝] lastCustomMode 자동 복원 — extension.ts의 activate()에 추가
async function restoreLastCustomMode(context: vscode.ExtensionContext): Promise<void> {
  const lastMode = context.globalState.get<string>('lastCustomMode');

  if (lastMode) {
    const config = vscode.workspace.getConfiguration('zooCode');
    const currentMode = config.get('customMode');

    if (currentMode !== lastMode) {
      // 모드 복원
      await config.update('customMode', lastMode, true); // true = global

      // 상태바에 복원 알림 표시 (3초 후 자동 사라짐)
      vscode.window.setStatusBarMessage(
        `$(zap) Zoo Code: '${lastMode}' 모드로 자동 복원됨`,
        3000
      );

      // [MCP] Crow에 복원 이벤트 저장 — 세션 연속성 기록
      await crowIngest({
        content: `Session restored with mode: ${lastMode}`,
        register: 'life_context',
        metadata: {
          source: 'auto_restore',
          timestamp: Date.now(),
          polarity: 1.0  // 긍정적 이벤트
        }
      });
    }
  }
}

// activate()에서 호출
export async function activate(context: vscode.ExtensionContext): Promise<void> {
  // ... 기존 초기화 코드 ...

  // [튜닝] 1. Crow 서버 재연결
  const crowServer = new CrowServerManager(context);
  await crowServer.reconnect();

  // [튜닝] 2. 마지막 Custom Mode 자동 복원
  await restoreLastCustomMode(context);

  // [튜닝] 3. 세션 시작 이력 기록
  await context.globalState.update('lastSessionStart', Date.now());
}
```

### 1.2.6 3계층 중복 세션 구조

Zoo Code의 세션 지속성은 Insight 8에서 도출된 **3계층 중복 구조** [^54^][^327^][^152^]로 설계되어야 한다. 각 계층은 다른 수명주기를 가지며, 어느 하나가 실패핟도 나머지가 보완한다.

| 계층 | 저장소 | 수명주기 | VS Code 종료 후 | 실패 시 영향 |
|------|--------|---------|----------------|-------------|
| L1: 프로세스 생존 | `detached: true` SSE 서버 (PID 파일) | OS 프로세스 | 생존 | OS 재부팅 시 소멸 |
| L2: Extension 상태 | `globalState` (SQLite `state.vscdb`) | 영구 | 재시작 시 복원 | Extension 삭제 시 소멸 |
| L3: 대화 맥락 | `crow.bin` (mmap 바이너리) | 영구 | SSE 서버 통해 접근 | 서버 미실행 시 접근 불가 |

**계층 간 상호작용**: L1(SSE 서버)이 살아 있으면 L3(`crow.bin`)에 접근 가능하며, Crow의 `life_context` 레지스터에 세션 요약이 자동 저장된다. L2(`globalState`)는 Custom Mode 같은 "설정" 수준의 상태를 저장하여, L1이 죽었더라도 사용자 경험의 기본 골격은 유지된다. L3는 L1을 통해 `crow_compact()`로 주기적으로 요약되며, 장기 기억의 보존을 담당한다.

**장애 시나리오 분석**:
- L1만 죽은 경우: VS Code 재시작 시 `reconnect()`가 서버를 새로 띄우고, L2(`globalState`)에서 Custom Mode 등 설정을 복원. L3(`crow.bin`)의 데이터는 보존.
- L2가 손실된 경우(Extension 재설치): L1과 L3는 그대로 유지. 대화 맥락은 Crow를 통해 복원 가능. 단 Custom Mode 등 Extension 특화 설정은 수동 재설정 필요.
- L3가 손실된 경우(디스크 손상): L1과 L2는 작동. 단 Crow의 장기 기억은 소실. 프로젝트 특화 맥락은 `AGENTS.md`와 Git 히스토리에서 부분 복원 가능.

### 1.2.7 바이브 점수: 현재 3/10 → 목표 9/10

| 지표 | 현재 (3/10) | 목표 (9/10) | 개선 방식 |
|------|:-----------:|:-----------:|:----------|
| VS Code 재시작 후 Custom Mode | 수동 재선택 (3초) | 자동 복원 (0초) | [튜닝] `lastCustomMode` globalState 저장 |
| SSE 서버 생존 | Extension 종료 시 함께 종료 | `detached: true`로 분리 생존 | [튜닝] `CrowServerManager` 구현 |
| 대화 맥락 복원 | 불가 (새 세션 시작) | Crow `life_context` 통해 복원 | [MCP] `crow_recall` + `crow_compact` 연동 |
| 세션 간 설정 동기화 | 없음 | Settings Sync로 다중 머신 지원 | [튜닝] `setKeysForSync` 활용 |

9점이 아닌 10점으로 설정하지 않은 이유는 VS Code Extension API의 근본적 제약 때문이다. OS 재부팅 시 `detached` 프로세스도 소멸하며, 이를 완전히 극복하려면 OS 시작 프로그램 등록과 같은 Extension API 외부의 메커니즘이 필요하기 때문이다. 하지만 3→9의 도약은 사용자가 "VS Code를 켰을 때 Zoo Code + Crow가 이미 준비되어 있다"는 경험을 만든다. 그 0초의 무의식은 바이브코딩의 핵심이다.

---

## 1.3 조사 차원 2: 모드 전환 마찰 (Mode Switching Friction within VS Code)

### 1.3.1 현재 3초 클릭이 바이브를 깨는 UX 분석

모드 전환 마찰은 터미널 기반 도구에게는 존재하지 않는 문제다. OpenCode와 Claude Code는 "모드"라는 개념 자체가 없다 — 사용자가 터미널을 열고 명령어를 치는 순간 그들의 AI는 이미 준비되어 있다. 하지만 VS Code Extension 기반 Zoo Code는 다르다. Zoo Code는 `custom_modes.yaml`에 정의된 여러 "모드"를 제공하며, 사용자는 매 프로젝트 열기마다 "Code + Crow Memory" 모드를 수동으로 선택해야 한다.

이 3초짜리 클릭이 바이브를 깨는 메커니즘을 정밀하게 분석하면 다음과 같다. 사용자가 VS Code를 켜서 프로젝트가 로드되는 데까지 약 2초가 걸린다. 이 시점에서 Zoo Code Extension은 활성화되지만, 기본 모드는 "Code"(일반 코딩 모드)로 설정된다. 사용자가 사이드바의 Zoo Code 패널을 열어 모드 드롭다운을 클릭하고 "Code + Crow Memory"를 선택하는 데 또 다른 3초가 걸린다. 이 3초 동안 사용자의 뇌는 어떤 상태인가?

첫째, **맥락 전환 비용(context-switching cost)**이 발생한다. 사용자는 "코딩을 시작하려" 했는데, "모드를 설정하는" 인지적 작업으로 전환된다. 이 전환은 바이브코딩의 핵심 가정 — "AI는 내 신경계의 연장체" —를 깨뜨린다. 둘째, **기억 의존성(memory dependency)**이 생긴다. 사용자는 "어제 어떤 모드로 작업했는지"를 기억하고 선택해야 한다. 이것은 사용자의 작업 기억(working memory)을 소모시키는 불필요한 부담이다. 셋째, **에러 가능성**이 존재한다. 잘못된 모드를 선택하면 Crow Memory가 연동되지 않아, 10분 후에야 "왜 AI가 내 어제 작업을 기억하지 못하지?"라는 질문과 함께 흐름이 깨진다.

### 1.3.2 자동 모드 감지: `onDidChangeWorkspaceFolders`

VS Code Extension API의 `workspace.onDidChangeWorkspaceFolders` 이벤트는 사용자가 워크스페이스를 열거나 변경할 때 발생한다 [^51^]. 이 이벤트를 활용하면, 프로젝트의 특징을 자동 감지하여 최적의 모드를 선택할 수 있다.

**[튜닝] 프로젝트 특징 기반 자동 모드 감지**는 프로젝트 루트에 존재하는 메타데이터 파일을 스캔하여 적절한 모드를 결정하는 방식이다:

```typescript
// [튜닝] 자동 모드 감지 — 프로젝트 메타데이터 기반
interface ProjectModeMapping {
  filePattern: string;     // 감지할 파일 패턴
  requiredContent?: string; // 파일 내용 조건 (선택)
  targetMode: string;       // 활성화할 모드
  priority: number;         // 우선순위 (높을수록 먼저 적용)
}

const PROJECT_MODE_MAP: ProjectModeMapping[] = [
  // .zoo/config.json이 있으면 그 모드를 우선 적용
  { filePattern: '.zoo/config.json', targetMode: 'from_config', priority: 100 },
  // Crow 관련 파일이 있으면 Code + Crow Memory
  { filePattern: '.roo/mcp.json', targetMode: 'code_plus_crow', priority: 90 },
  { filePattern: 'AGENTS.md', targetMode: 'code_plus_crow', priority: 85 },
  // 특정 프레임워크 감지
  { filePattern: 'package.json', targetMode: 'node_dev', priority: 70 },
  { filePattern: 'Cargo.toml', targetMode: 'rust_dev', priority: 70 },
  { filePattern: 'go.mod', targetMode: 'go_dev', priority: 70 },
  { filePattern: 'pyproject.toml', targetMode: 'python_dev', priority: 70 },
  // 기본값
  { filePattern: '*', targetMode: 'code', priority: 0 }
];

class AutoModeDetector {
  constructor(private context: vscode.ExtensionContext) {}

  // [튜닝] 워크스페이스 열리면 자동 모드 감지 및 적용
  async onWorkspaceOpen(folders: readonly vscode.WorkspaceFolder[]): Promise<void> {
    if (folders.length === 0) return;
    const root = folders[0].uri;

    // 1. .zoo/config.json이 있으면 그 모드를 최우선으로 적용
    const zooConfig = await this.readZooConfig(root);
    if (zooConfig?.defaultMode) {
      await this.applyMode(zooConfig.defaultMode, 'config_file');
      return;
    }

    // 2. 프로젝트 파일 기반 감지
    for (const mapping of PROJECT_MODE_MAP.sort((a, b) => b.priority - a.priority)) {
      if (mapping.targetMode === 'from_config') continue; // 이미 처리

      const exists = await this.fileExists(vscode.Uri.joinPath(root, mapping.filePattern));
      if (exists) {
        await this.applyMode(mapping.targetMode, `auto_detect_${mapping.filePattern}`);
        return;
      }
    }
  }

  private async readZooConfig(root: vscode.Uri): Promise<{ defaultMode?: string } | null> {
    try {
      const uri = vscode.Uri.joinPath(root, '.zoo', 'config.json');
      const content = await vscode.workspace.fs.readFile(uri);
      return JSON.parse(content.toString());
    } catch {
      return null;
    }
  }

  private async fileExists(uri: vscode.Uri): Promise<boolean> {
    try {
      await vscode.workspace.fs.stat(uri);
      return true;
    } catch {
      return false;
    }
  }

  private async applyMode(mode: string, source: string): Promise<void> {
    const lastMode = this.context.globalState.get<string>('lastCustomMode');

    // 마지막 모드가 있고, 자동 감지 모드와 다른면
    // 사용자가 이전에 수동으로 변경했을 수 있으므로 lastMode를 우선
    const targetMode = lastMode && lastMode !== mode ? lastMode : mode;

    const config = vscode.workspace.getConfiguration('zooCode');
    const currentMode = config.get('customMode');

    if (currentMode !== targetMode) {
      await config.update('customMode', targetMode, true);

      // 상태바 알림 (2초 후 자동 사라짐 — 사용자가 선택할 필요 없음)
      vscode.window.setStatusBarMessage(
        `$(gear) Zoo Code: '${targetMode}' 모드 자동 적용 (${source})`,
        2000
      );

      // [MCP] Crow에 모드 변경 이력 저장
      await crowIngest({
        content: `Auto mode '${targetMode}' applied (source: ${source})`,
        register: 'life_context',
        metadata: { source: 'auto_mode_detector', ttl: 86400 }
      });
    }
  }
}

// Extension activate()에서 등록
export function activate(context: vscode.ExtensionContext): void {
  const autoMode = new AutoModeDetector(context);

  // 워크스페이스 열릴 때 자동 감지
  context.subscriptions.push(
    vscode.workspace.onDidChangeWorkspaceFolders((e) => {
      if (e.added.length > 0) {
        autoMode.onWorkspaceOpen(e.added);
      }
    })
  );

  // 현재 열린 워크스페이스에도 즉시 적용
  if (vscode.workspace.workspaceFolders) {
    autoMode.onWorkspaceOpen(vscode.workspace.workspaceFolders);
  }
}
```

### 1.3.3 `AGENTS.md` 자동 주입

`AGENTS.md`는 프로젝트별 에이전트 지침서로, Roo Code 생태계에서 표준으로 사용되고 있으며 Cursor, Windsurf, Kilo Code, Claude Code 간 de facto open standard로 부상하고 있다 [^367^][^450^]. Zoo Code Extension이 `AGENTS.md`를 자동으로 system prompt에 prepend하려면, 파일의 존재를 감지하고 내용을 읽어 Zoo Code의 프롬프트 구성에 주입하는 로직이 필요하다.

**[튜닝] AGENTS.md 자동 감지 및 주입**은 `FileSystemWatcher`와 Extension의 초기화 시퀀스를 활용한다:

```typescript
// [튜닝] AGENTS.md 자동 감지 및 프롬프트 주입
class AgentsMdInjector {
  private agentsContent: string | null = null;
  private watcher: vscode.FileSystemWatcher | null = null;

  constructor(private context: vscode.ExtensionContext) {}

  async initialize(): Promise<void> {
    const folders = vscode.workspace.workspaceFolders;
    if (!folders || folders.length === 0) return;

    const root = folders[0].uri;

    // 1. 초기 로드
    await this.loadAgentsMd(root);

    // 2. [튜닝] FileSystemWatcher로 AGENTS.md 변경 감시
    this.watcher = vscode.workspace.createFileSystemWatcher(
      new vscode.RelativePattern(folders[0], 'AGENTS.md')
    );

    this.watcher.onDidChange(() => this.loadAgentsMd(root));
    this.watcher.onDidCreate(() => this.loadAgentsMd(root));
    this.watcher.onDidDelete(() => { this.agentsContent = null; });

    this.context.subscriptions.push(this.watcher);
  }

  private async loadAgentsMd(root: vscode.Uri): Promise<void> {
    try {
      const uri = vscode.Uri.joinPath(root, 'AGENTS.md');
      const content = (await vscode.workspace.fs.readFile(uri)).toString();

      // 200줄 제한 [^313^] — 너무 길면 컨텍스트 낭비
      this.agentsContent = content.split('\n').slice(0, 200).join('\n');

      // [MCP] Crow의 arch 레지스터에 프로젝트 규칙 저장
      await crowIngest({
        content: `Project rules from AGENTS.md: ${this.agentsContent.substring(0, 500)}...`,
        register: 'arch',
        metadata: { source: 'AGENTS.md', importance: 0.9 }
      });

      console.log('[AGENTS.md] 로드 완료. 프롬프트에 자동 주입됨.');
    } catch {
      this.agentsContent = null;
    }
  }

  // Zoo Code의 프롬프트 빌더에서 호출
  getPromptPrefix(): string {
    if (!this.agentsContent) return '';
    return `## Project Rules (from AGENTS.md)\n${this.agentsContent}\n\n---\n`;
  }
}
```

### 1.3.4 `.zoo/config.json` 기반 프로젝트 메타데이터 모드

모드 전환 마찰을 근본적으로 해결하는 또 다른 접근은 "모드"라는 개념을 프로젝트 메타데이터로 전환하는 것이다. 프로젝트 루트에 `.zoo/config.json` 파일을 두고, 이 파일에 "이 프로젝트의 기본 모드"를 저장하면, Zoo Code Extension은 이 파일을 읽어 자동으로 모드를 적용한다. 이 방식의 장점은 Git으로 버전 관리되어 팀 전체가 동일한 모드를 공유한다는 점이다.

```json
// .zoo/config.json — 프로젝트 메타데이터 (Git으로 버전 관리)
{
  "version": 1,
  "defaultMode": "code_plus_crow",
  "project": {
    "name": "my-saas-app",
    "type": "nextjs",
    "language": "typescript"
  },
  "crow": {
    "autoCompactInterval": 600,
    "preferredRegisters": ["arch", "style"]
  },
  "build": {
    "command": "npm run build",
    "problemMatcher": "$tsc-watch",
    "autoFix": {
      "enabled": true,
      "maxAttempts": 3
    }
  }
}
```

이 파일은 프로젝트 특화 설정을 Git으로 동기화할 수 있어, 새 팀원이 프로젝트를 클론하는 순간부터 최적의 Zoo Code 환경이 준비된다. `defaultMode` 필드는 AutoModeDetector의 최우선 순위로 처리되며(priority: 100), 사용자의 이전 선택(`lastCustomMode`)보다도 먼저 고려된다 — 단, 사용자가 이 프로젝트에서 한 번이라도 수동으로 모드를 변경한 경우, 그 선택이 기얶되어 `.zoo/config.json`을 오버라이드한다.

### 1.3.5 바이브 점수: 현재 4/10 → 목표 9/10

| 지표 | 현재 (4/10) | 목표 (9/10) | 개선 방식 |
|------|:-----------:|:-----------:|:----------|
| 모드 선택 | 수동 클릭 (3초) | 0초 자동 적용 | [튜닝] `AutoModeDetector` — 프로젝트 파일 감지 |
| AGENTS.md 주입 | 수동 복사-붙여넣기 | 자동 프롬프트 prepend | [튜닝] `AgentsMdInjector` — `FileSystemWatcher` 기반 |
| 프로젝트 설정 공유 | 없음 | Git 버전 관리 | [튜닝] `.zoo/config.json` 도입 |
| 모드 전환 인지도 | 사용자가 매번 선택 | 사용자가 모드의 존재를 까먹음 | [튜닝] `lastCustomMode` 기얶 + `.zoo/config.json` 병합 |

9점이 아닌 10점으로 설정하지 않은 이유는, "모드"라는 개념 자체가 여전히 사용자에게 노출되기 때문이다. 완전한 10점은 모드 개념 자체가 사라지고, AI가 프로젝트의 특성을 읽어 자동으로 최적의 "성격"을 갖추는 상태를 의미한다. 하지만 그 상태는 VS Code Extension API의 범위를 넘어서는 LLM 수준의 발전을 요구하며, Wave 3(Zero-Explanation) 영역에 속한다.

---

## 1.4 조사 차원 3: 빌드-코드-피드백 루프 (Build-Code Feedback Loop)

### 1.4.1 현재 흐름 단절 UX 분석

Zoo Code에서 빌드 명령을 실행하고 그 결과를 AI가 인지하여 수정하는 과정은, 현재 4개 이상의 흐름 단계를 수동으로 거쳐야 한다. 사용자가 `npm run build`를 입력하면 터미널에 에러 메시지가 쏟아진다. 사용자는 그 에러를 읽고, 관련된 부분을 드래그해 복사한 뒤, Zoo Code 채팅창에 붙여넣는다. "이 에러를 고쳐줘"라고 요청하면 AI는 에러를 분석하고 코드를 수정한다. 수정 후 사용자는 다시 `npm run build`를 실행한다.

이 과정에서 사용자의 뇌는 어떤 상태인가? 터미널에서 에러를 읽는 순간, 사용자는 "코딩의 흐름"에서 "디버깅의 흐름"으로 강제 전환된다. 에러 메시지를 복사할 때, 사용자의 손은 키보드에서 마우스로 이동하고, 마우스에서 다시 키보드로 돌아온다. 이 context switch는 순수한 인지적 비용이다. 채팅창에 붙여넣기를 하고 "고쳐줘"라고 입력하는 순간, 사용자는 더 이상 "생각하는 프로그래머"가 아니라 "에러 메시지 운송업자"가 된다.

이 루프의 한 사이클은 보통 30-60초가 걸린다. 빌드가 5번 실패하면 3-5분이 날아간다. 이 3-5분 동안 사용자의 뇌는 "이것을 자동화할 수 없을까?"라는 생각에서 코딩 의욕이 서서히 꺾인다.

Claude Code는 이 루프를 어떻게 해결했는가? `BashTool`의 `EndTruncatingAccumulator`가 stderr/stdout을 자동 캡처하고, exit code를 해석하여 성공/실패를 LLM 컨텍스트에 자동 주입한다 [^316^]. 특히 2초 이상 실행되는 명령에 대해 터미널 출력의 마지막 5줄을 실시간으로 표시하는 "Progress messages" 기능(v1.0.48)은 장시간 빌드에서도 사용자가 진행 상황을 파악할 수 있게 한다 [^316^]. LSP 통합(`ENABLE_LSP_TOOL=1`)까지 활성화하면 파일 수정 후 자동 진단이 수행되어 AI가 스스로의 오류를 인지하고 교정한다 [^317^].

OpenCode는 `LSP.touchFile()` → `LSP.diagnostics()` 피드백 루프를 통해 LLM이 자신의 코드 변경의 정확성을 즉각 검증하도록 한다 [^207^]. "This feedback loop is extremely useful: it keeps the LLM grounded and prevents it from going off the rails"라는 평가는 이 루프의 가치를 잘 요약한다.

Zoo Code는 이 두 도구의 장점을 VS Code Extension API 내에서 재현해야 한다.

### 1.4.2 VS Code Task API + Problem Matcher 자동화

VS Code Extension API의 `vscode.tasks` 네임스페이스는 태스크 실행, 모니터링, 결과 캡처를 위한 풍부한 인터페이스를 제공한다 [^51^]. `tasks.onDidEndTaskProcess` 이벤트는 프로세스 종료 시 `exitCode`를 제공하며 [^111^][^114^], `problemMatcher`는 정규식 기반으로 터미널 출력을 스캔하여 파일명, 라인, 컬럼, 심각도, 메시지를 추출한다 [^42^][^46^].

**[튜닝] 프로젝트 타입 자동 감지 및 tasks.json 자동 생성**:

Zoo Code Extension은 프로젝트 루트의 파일(`package.json`, `Cargo.toml`, `go.mod` 등)을 스캔하여 빌드 태스크를 자동으로 생성한다. 이 태스크는 `presentation.reveal: "silent"`로 설정되어, 빌드가 백그라운드에서 실행되며 에러가 없을 때는 터미널이 나타나지 않는다.

| 프로젝트 타입 | 감지 파일 | 빌드 명령 | Problem Matcher |
|-------------|----------|----------|----------------|
| Node.js/TypeScript | `package.json` | `npm run build` | `$tsc-watch` |
| Rust | `Cargo.toml` | `cargo build` | `$rustc` |
| Go | `go.mod` | `go build ./...` | 커스텀 정규식 |
| Python | `pyproject.toml` | `pytest` | `$pytest` |
| Java | `pom.xml` | `mvn compile` | 커스텀 정규식 |

**[튜닝] Task Provider 등록**으로 Zoo Code Extension이 빌드 태스크를 자동 제공하게 한다 [^160^]:

```typescript
// [튜닝] Crow 자동 빌드 태스크 — 프로젝트 타입 감지 및 Task 자동 생성
interface CrowBuildTaskDefinition {
  type: 'crow';
  task: string;
}

const BUILD_TASK_DEFS: Record<string, {
  command: string;
  args: string[];
  problemMatcher: string;
}> = {
  'node': { command: 'npm', args: ['run', 'build'], problemMatcher: '$tsc-watch' },
  'rust': { command: 'cargo', args: ['build'], problemMatcher: '$rustc' },
  'go': { command: 'go', args: ['build', './...'], problemMatcher: '$go' },
  'python': { command: 'python', args: ['-m', 'pytest'], problemMatcher: '$pytest' },
};

export function registerCrowBuildProvider(context: vscode.ExtensionContext): void {
  const provider = vscode.tasks.registerTaskProvider('crow', {
    provideTasks: async () => {
      const projectType = await detectProjectType();
      const def = BUILD_TASK_DEFS[projectType];
      if (!def) return [];

      const task = new vscode.Task(
        { type: 'crow', task: 'build' },
        vscode.TaskScope.Workspace,
        'crow: build',
        'crow',
        new vscode.ShellExecution(def.command, def.args),
        def.problemMatcher
      );

      // [튜닝] 백그라운드 빌드: 에러 없으면 터미널 미표시
      task.presentationOptions = {
        reveal: vscode.TaskRevealKind.Silent,   // 에러 시에만 터미널 표시 [^135^]
        panel: vscode.TaskPanelKind.Dedicated,  // 전용 패널
        close: true,                            // 완료 후 터미널 닫기
        focus: false,                           // 포커스 유지
        clear: true,                            // 실행 전 터미널 클리어
        echo: false,                            // 명령어 미표시
        showReuseMessage: false                 // 재사용 메시지 숨김
      };

      return [task];
    },
    resolveTask(task: vscode.Task): vscode.Task | undefined {
      return task;
    }
  });

  context.subscriptions.push(provider);
}

// 프로젝트 타입 자동 감지
async function detectProjectType(): Promise<string> {
  const files = await vscode.workspace.findFiles(
    '{package.json,Cargo.toml,go.mod,pyproject.toml,pom.xml}',
    '**/node_modules/**',
    5
  );
  for (const f of files) {
    if (f.fsPath.endsWith('package.json')) return 'node';
    if (f.fsPath.endsWith('Cargo.toml')) return 'rust';
    if (f.fsPath.endsWith('go.mod')) return 'go';
    if (f.fsPath.endsWith('pyproject.toml')) return 'python';
    if (f.fsPath.endsWith('pom.xml')) return 'java';
  }
  return 'unknown';
}
```

### 1.4.3 `presentation.reveal: silent` + `crow_ingest_from_build`

`TaskPresentationOptions.reveal`의 `"silent"` 값은 problemMatcher가 오류를 찾지 못한 경우에만 터미널을 표시하는 옵션이다 [^51^]. 이것이 핵심인데: 빌드가 성공하면 사용자는 터미널을 전혀 보지 않는다. 흐름이 끊기지 않는다. 빌드가 실패하면 그때서야 터미널이 나타나고, 동시에 `crow_ingest_from_build`가 자동 호출되어 빌드 결과가 Crow Memory의 `bug` 레지스터에 저장된다.

### 1.4.4 `onDidEndTaskProcess` → MCP 자동 호출

**[튜닝] 빌드 결과 자동 수집 및 Crow에 저장**은 `onDidEndTaskProcess` 이벤트 구독으로 구현된다. 이 이벤트는 태스크의 프로세스 수준 종료를 감지하며, `exitCode`를 제공한다 [^51^][^111^]:

```typescript
// [튜닝] 빌드 결과 자동 수집 → Crow 저장 → LLM 컨텍스트 주입
export function activateBuildFeedback(context: vscode.ExtensionContext): void {
  const disposable = vscode.tasks.onDidEndTaskProcess(async (event) => {
    const task = event.execution.task;

    // Crow 태스크만 처리
    if (task.source !== 'crow' && task.source !== 'crow: build') return;

    const exitCode = event.exitCode ?? -1;

    if (exitCode !== 0) {
      // 1. LSP diagnostics 수집 (0.5초 대기 — LSP 업데이트 시간) [^239^]
      await new Promise(resolve => setTimeout(resolve, 500));
      const diagnostics = collectDiagnostics();

      // 2. 빌드 결과 객체 구성
      const buildResult: CrowBuildResult = {
        taskName: task.name,
        exitCode,
        timestamp: new Date().toISOString(),
        diagnostics,
        projectRoot: vscode.workspace.workspaceFolders?.[0]?.uri.fsPath ?? ''
      };

      // 3. [MCP] Crow에 빌드 실패 결과 저장
      await crowIngest({
        content: `Build failed: exitCode=${exitCode}, errors=${diagnostics.length}\n` +
                 diagnostics.slice(0, 10).map(d =>
                   `[${d.severity}] ${d.file}:${d.line} — ${d.message}`
                 ).join('\n'),
        register: 'bug',
        metadata: {
          source: 'build_feedback',
          importance: 0.85,
          tags: ['build_error', task.name]
        }
      });

      // 4. LLM 컨텍스트에 빌드 에러 자동 주입
      const errorContext = formatBuildErrorContext(buildResult);
      await injectLLMContext('build_error', errorContext);

      // 5. [튜닝] AutoFix 루프 트리거 (사용자 설정 시)
      const autoFixEnabled = vscode.workspace.getConfiguration('crow').get('autoFix.enabled', false);
      if (autoFixEnabled) {
        await triggerAutoBuildFix(buildResult);
      }
    } else {
      // 빌드 성공 — 이전 빌드 에러 컨텍스트 클리어
      await clearLLMContext('build_error');

      // [MCP] Crow에 빌드 성공 저장 (패턴 학습용)
      await crowIngest({
        content: `Build succeeded: ${task.name} at ${new Date().toISOString()}`,
        register: 'arch',
        metadata: { source: 'build_feedback', importance: 0.5, tags: ['build_success'] }
      });
    }
  });

  context.subscriptions.push(disposable);
}

// Diagnostics 수집 및 포맷팅
function collectDiagnostics(): CrowDiagnostic[] {
  const result: CrowDiagnostic[] = [];
  const allDiagnostics = vscode.languages.getDiagnostics(); // 모든 파일의 진단 [^254^]

  for (const [uri, diagnostics] of allDiagnostics) {
    const relativePath = vscode.workspace.asRelativePath(uri);
    for (const d of diagnostics) {
      result.push({
        file: relativePath,
        line: d.range.start.line + 1,
        column: d.range.start.character + 1,
        severity: d.severity === vscode.DiagnosticSeverity.Error ? 'error' :
                  d.severity === vscode.DiagnosticSeverity.Warning ? 'warning' : 'info',
        message: d.message,
        code: String(d.code ?? ''),
        source: d.source ?? ''
      });
    }
  }
  return result;
}

interface CrowBuildResult {
  taskName: string;
  exitCode: number;
  timestamp: string;
  diagnostics: CrowDiagnostic[];
  projectRoot: string;
}

interface CrowDiagnostic {
  file: string;
  line: number;
  column: number;
  severity: 'error' | 'warning' | 'info';
  message: string;
  code: string;
  source: string;
}
```

**중요 참고**: `e.execution === echoTaskExecution`과 같은 객체 동일성 비교는 VS Code 1.44 이후 신뢰할 수 없다 [^108^]. 위 코드에서는 `task.source` 문자열 비교로 이를 회피한다.

### 1.4.5 LSP diagnostics 자동 피드백

VS Code Extension API는 `vscode.languages.onDidChangeDiagnostics` 이벤트로 진단 정보의 변경을 실시간 감지할 수 있다 [^239^][^276^]. 이 이벤트와 `getDiagnostics()`를 조합하면, 파일이 수정될 때마다(예: AI가 코드를 고친 후) LSP 서버가 제공하는 진단 정보를 LLM 컨텍스트에 자동 주입할 수 있다.

OpenCode의 `LSP.touchFile()` → `LSP.diagnostics()` 피드백 루프 [^207^]는 파일 수정 후 명시적으로 LSP 서버에 진단을 요청하는 방식이다. VS Code Extension에서는 이것이 불필요하다 — LSP 서버가 `textDocument/publishDiagnostics`로 자동 푸시하며, `onDidChangeDiagnostics` 이벤트가 이를 수신하기 때문이다.

**주의사항**: 100개 이상의 diagnostics가 있는 파일에서 `onDidChangeDiagnostics`가 동일한 diagnostics에 대해 두 번 트리거되는 버그가 보고되어 있다 [^239^]. 이를 처리하기 위해 debounce 로직이 필수적이다:

```typescript
// [튜닝] LSP diagnostics 자동 피드백 — debounce 필수
let diagnosticDebounce: NodeJS.Timeout | null = null;
let lastDiagnosticHash = '';

export function watchDiagnostics(context: vscode.ExtensionContext): void {
  const disposable = vscode.languages.onDidChangeDiagnostics((event) => {
    // debounce: 동일한 diagnostics가 반복 전송되지 않도록 [^239^]
    if (diagnosticDebounce) clearTimeout(diagnosticDebounce);

    diagnosticDebounce = setTimeout(async () => {
      const summary = summarizeDiagnostics();
      const hash = hashString(summary);

      if (hash === lastDiagnosticHash) return; // 중복 방지
      lastDiagnosticHash = hash;

      // LLM 컨텍스트에 진단 요약 주입
      await injectLLMContext('diagnostics_summary', summary);
    }, 1000); // 1초 debounce
  });

  context.subscriptions.push(disposable);
}

function summarizeDiagnostics(): string {
  const all = vscode.languages.getDiagnostics();
  const errors: string[] = [];
  const warnings: string[] = [];

  for (const [uri, diagnostics] of all) {
    if (diagnostics.length === 0) continue;
    const path = vscode.workspace.asRelativePath(uri);
    for (const d of diagnostics) {
      const sev = vscode.DiagnosticSeverity[d.severity];
      const msg = `[${sev}] ${path}:${d.range.start.line + 1} — ${d.message}`;
      if (d.severity === vscode.DiagnosticSeverity.Error) errors.push(msg);
      else warnings.push(msg);
    }
  }

  return [
    `## LSP Diagnostics (${errors.length} errors, ${warnings.length} warnings)`,
    ...errors.slice(0, 15),
    ...warnings.slice(0, 5),
    errors.length > 15 ? `... and ${errors.length - 15} more errors` : '',
  ].join('\n');
}
```

### 1.4.6 AutoBuildFix 루프 (max_attempts=3)

AutoBuildFix 루프는 빌드 실패 → LLM에 에러 전달 → 코드 수정 → 재빌드를 최대 3회까지 자동 반복하는 패턴이다. 이 패턴은 "Sense → Reason → Act → Loop" [^278^][^309^] 또는 "Ralph Wiggum Loop" [^251^]로 불리며, AI 코딩 도구의 자기 수정 능력의 핵심이다.

그러나 이 루프에는 **무한 루프 방지 메커니즘**이 필수적이다. Claude Code의 worktree 데이터 손실 이슈(#46444)가 증명하듯, 완전 무인 자동화는 신뢰를 파괴할 수 있다 [^345^]. 다음 안전장치가 필요하다:

| 안전장치 | 설명 | 구현 |
|----------|------|------|
| `max_attempts=3` | 최대 3회 재시도 | 하드 리밋 |
| 반복 에러 감지 | 동일한 에러가 2회 연속 발생하면 중단 | 에러 메시지+라인 비교 |
| Oscillation 감지 | A→B→A 패턴(패치 A가 버그1 고치지만 버그2 유발, 패치 B가 버그2 고치지만 버그1 재발) 감지 | 2단계 전 패치 비교 [^309^] |
| No-op 패치 감지 | 패치가 원본과 동일하면 중단 | 문자열 비교 |
| 롤백 매니저 | 실패 시 Git stash로 원 상태 복원 | `git stash pop` [^251^] |

```typescript
// [튜닝] AutoBuildFix 루프 — 안전장치 포함
class AutoBuildFixLoop {
  private attemptHistory: Array<{
    attempt: number;
    diagnostics: CrowDiagnostic[];
    patch: string;
  }> = [];

  constructor(
    private maxAttempts: number = 3,
    private rollbackManager: RollbackManager
  ) {}

  async run(initialResult: CrowBuildResult): Promise<LoopResult> {
    await this.rollbackManager.createSnapshot(); // Git stash 백업

    for (let attempt = 1; attempt <= this.maxAttempts; attempt++) {
      const result = attempt === 1 ? initialResult : await this.rebuild();

      if (result.exitCode === 0) {
        return { status: 'success', attempt };
      }

      // 반복 에러 검사
      if (this.isRepeatedError(result.diagnostics)) {
        await this.rollbackManager.restore();
        return { status: 'failed', reason: 'repeated_error', attempt };
      }

      // LLM에게 수정 요청
      const patch = await requestFixFromLLM(result, this.attemptHistory);

      // No-op 검사
      if (!patch || patch.trim().length === 0) {
        await this.rollbackManager.restore();
        return { status: 'failed', reason: 'empty_patch', attempt };
      }

      // Oscillation 검사
      if (this.isOscillating(patch)) {
        await this.rollbackManager.restore();
        return { status: 'failed', reason: 'oscillation', attempt };
      }

      await applyPatch(patch);
      this.attemptHistory.push({ attempt, diagnostics: result.diagnostics, patch });
    }

    await this.rollbackManager.restore();
    return { status: 'failed', reason: 'max_retries', attempts: this.maxAttempts };
  }

  private isRepeatedError(diagnostics: CrowDiagnostic[]): boolean {
    if (this.attemptHistory.length === 0) return false;
    const last = this.attemptHistory[this.attemptHistory.length - 1];
    return diagnostics.every((d, i) => {
      const ld = last.diagnostics[i];
      return ld && d.message === ld.message && d.line === ld.line;
    });
  }

  private isOscillating(currentPatch: string): boolean {
    if (this.attemptHistory.length < 2) return false;
    const twoStepsAgo = this.attemptHistory[this.attemptHistory.length - 2];
    return currentPatch.trim() === twoStepsAgo.patch.trim();
  }

  private async rebuild(): Promise<CrowBuildResult> {
    // crow: build 태스크 재실행
    const tasks = await vscode.tasks.fetchTasks({ type: 'crow' });
    const buildTask = tasks.find(t => t.group === vscode.TaskGroup.Build);
    if (!buildTask) throw new Error('Build task not found');

    return new Promise((resolve) => {
      const disposable = vscode.tasks.onDidEndTaskProcess((e) => {
        // 안전한 비교: task 객체 직접 비교 [^108^]
        if (e.execution.task.definition.type === 'crow') {
          disposable.dispose();
          resolve({
            taskName: e.execution.task.name,
            exitCode: e.exitCode ?? -1,
            timestamp: new Date().toISOString(),
            diagnostics: collectDiagnostics(),
            projectRoot: vscode.workspace.workspaceFolders?.[0]?.uri.fsPath ?? ''
          });
        }
      });
      vscode.tasks.executeTask(buildTask);
    });
  }
}

// 롤백 매니저 — Git stash 기반
class RollbackManager {
  async createSnapshot(): Promise<void> {
    const git = vscode.extensions.getExtension('vscode.git')?.exports.getAPI(1);
    if (git?.repositories.length > 0) {
      await git.repositories[0].stash(['-u', '-m', `crow-autofix-${Date.now()}`]);
    }
  }

  async restore(): Promise<void> {
    const git = vscode.extensions.getExtension('vscode.git')?.exports.getAPI(1);
    if (git?.repositories.length > 0) {
      await git.repositories[0].stash(['pop']);
    }
  }
}
```

### 1.4.7 바이브 점수: 현재 4/10 → 목표 9/10

| 지표 | 현재 (4/10) | 목표 (9/10) | 개선 방식 |
|------|:-----------:|:-----------:|:----------|
| 빌드 에러 전달 | 수동 복사-붙여넣기 (30-60초) | 자동 (0초) | [튜닝] `onDidEndTaskProcess` → `crow_ingest` |
| 터미널 방해 | 빌드 시 항상 터미널 표시 | 에러 시에만 표시 | [튜닝] `presentation.reveal: silent` [^135^] |
| LSP 피드백 | 없음 | 파일 수정 후 자동 진단 | [튜닝] `onDidChangeDiagnostics` debounce |
| AutoFix | 없음 | 최대 3회 자동 재시도 | [튜닝] `AutoBuildFixLoop` + 안전장치 |
| 빌드 패턴 기억 | 없음 | Crow `bug` 레지스터에 누적 | [MCP] `crow_ingest` → `bug` register |

9점이 아닌 10점인 이유는, 완전 무인 자동화가 때로는 사용자의 의도와 어긋날 수 있다는 점을 인정하기 때문이다. AutoFix 루프는 사용자가 활성화한 경우에만 작동하며(기본값: off), 진행 상황은 상태바에 표시된다. 사용자는 언제든지 중지할 수 있다. 이것이 "완벽한 자동화"가 아닌 "완벽하게 예측 가능한 자동화"이다 — 바이브를 깨지 않는 선에서 최대한의 편의를 제공하는 설계 원칙이다.

---

## 1.5 조사 차원 4: 컨텍스트 로트 (Context Rot within VS Code)

### 1.5.1 AI "멍해짐" 현상의 기술적 원인

1시간 이상 Zoo Code와 함께 코딩하면 사용자는 점점 AI가 "멍해진다"는 느낌을 받는다. 이전에 분명히 말했던 "직설적 답변을 선호한다"는 사실을 AI는 잊어버리고, 다시 장황한 설명을 시작한다. 사용자가 20분 전에 "이 프로젝트는 Zustand를 쓰고 Redux는 쓰지 않는다"고 했음에도, AI가 다음 파일에서 `useDispatch`를 import하려 할 때, 사용자는 한숨을 쉰다.

이 "멍해짐" 현상의 기술적 원인은 **컨텍스트 윈도우의 비대화**와 **요약(compaction) 메커니즘의 부재** 두 가지로 분석된다.

**컨텍스트 윈도우 비대화**: Zoo Code는 대화 이력을 `ExtensionContext.globalState`에 저장한다 [^234^]. 이 SQLite 기반 저장소는 JSON 직렬화로 모든 데이터를 처리하며 [^51^], 대화가 길어질수록 저장/로드 시간이 선형적으로 증가한다. 더 심각한 문제는 Extension Host의 V8 heap limit(~2-4GB) [^172^] 내에서 대화 이력이 메모리를 계속 점유한다는 점이다. 대화 이력이 비대해지면 다른 컨텍스트 요소(프로젝트 파일, system prompt, AGENTS.md)가 밀려난다. AI는 이전 대화는 기억하지만, 지금 열린 파일의 내용을 잊어버리게 된다.

**요약 메커니즘 부재**: Claude Code는 3계층 compaction 시스템(Session Memory → Microcompaction → Traditional Compaction) [^401^][^406^]을 통해 이 문제를 관리한다. OpenCode는 2-phase context compaction(40K 토큰 기준 pruning → LLM summarization) [^214^]을 구현했다. 반면 Zoo Code는 이러한 체계적인 요약 메커니즘이 부재하여, 대화가 길어질수록 전체 이력이 그대로 LLM에 전달되어 토큰을 비효율적으로 소모한다.

### 1.5.2 Extension Host 메모리 제약 내 대화 이력 관리

VS Code Extension Host는 별도의 Node.js 프로세스로 실행되며, 이 단일 프로세스 내에서 모든 확장 프로그램이 함께 실행된다 [^162^][^167^]. Extension Host는 자체 V8 엔진, 메모리 힙, 이벤트 루프를 가지며 [^107^], 64-bit 시스템에서의 기본 heap limit은 약 2GB~4GB이다 [^172^][^190^].

Roo Code Issue #3784 [^234^]에서는 globalState에 과도한 양의 히스토리를 저장했을 때 "excessive globalState usage" 경고와 함께 Extension Host의 성능 저하 및 크래시가 보고되었다. 이는 단순히 저장 문제가 아니라, globalState에서 읽어온 대용량 JSON을 Extension Host 메모리에 역직렬화할 때의 heap pressure 문제다.

**해결 방향**: 대화 이력의 전체 저장은 `crow.bin`에 위임하고, `globalState`에는 **요약된 메타데이터**만 저장한다. Extension Host 메모리에는 **최근 20개 턴**만 유지하고, 이전 이력은 필요할 때마다 Crow의 `crow_recall`로 검색한다. 이는 MemGPT의 "Main Context + External Context" 이층 설계 [^366^][^370^]와 동일한 패턴이다.

### 1.5.3 자동 `crow_compact` 타이머

**[MCP] 주기적 컨텍스트 압축**은 세션 종료 시 뿐만 아니라, 세션 중에도 주기적으로 실행되어야 한다. `setInterval`을 사용한 단순 타이머는 VS Code Extension Host의 이벤트 루프를 점유할 수 있으므로, `vscode.workspace.onWillSaveTextDocument` 이벤트를 트리거로 사용하는 것이 덜 intrusive하다 — 사용자가 파일을 저장할 때(즉, "의미 있는 작업이 완료되었을 때") compaction을 실행한다.

```typescript
// [MCP] 자동 crow_compact — 파일 저장 시 트리거
class AutoCompactionTimer {
  private lastCompactTime: number = 0;
  private readonly COMPACT_INTERVAL_MS = 10 * 60 * 1000; // 10분 최소 간격

  constructor(private context: vscode.ExtensionContext) {}

  activate(): void {
    // [튜닝] 파일 저장 시 compaction 가능성 검사
    const disposable = vscode.workspace.onWillSaveTextDocument(() => {
      const now = Date.now();
      if (now - this.lastCompactTime < this.COMPACT_INTERVAL_MS) return;

      this.lastCompactTime = now;
      this.runCompaction();
    });

    this.context.subscriptions.push(disposable);
  }

  private async runCompaction(): Promise<void> {
    try {
      // [MCP] Crow에게 compaction 실행 요청
      const compactResult = await crowCompact();

      // 요약 결과를 life_context에 저장
      if (compactResult.summary) {
        await crowIngest({
          content: `Session compacted at ${new Date().toISOString()}: ${compactResult.summary}`,
          register: 'life_context',
          metadata: {
            source: 'auto_compaction',
            tokensReclaimed: compactResult.tokensReclaimed,
            importance: 0.7
          }
        });
      }

      // 상태바에 compaction 완료 표시 (2초)
      vscode.window.setStatusBarMessage(
        `$(sync) Crow: 컨텍스트 압축 완료 (${compactResult.tokensReclaimed} tokens reclaimed)`,
        2000
      );
    } catch (err) {
      console.error('[AutoCompact] 실패:', err);
    }
  }
}
```

### 1.5.4 OpenCode의 2-phase compaction 패턴 적용

OpenCode의 2-phase compaction [^214^][^476^]은 Zoo Code에서도 적용할 수 있는 외과적인 접근법이다.

**Phase 1: Pruning (가지치기)** [^476^]. 가장 최근 40,000 토큰(`PRUNE_PROTECT`) 이전의 오래된 tool output을 `"[Old tool result content cleared]"`로 대체한다. 이 과정은 LLM API 호출 없이 순수하게 토큰 계산 기반으로 수행되며, 20K 토큰 이상 회수 가능할 때만 실행된다(`PRUNE_MINIMUM`). 이는 OpenCode가 초기 JSON 파일 기반 저장에서 SQLite로 전환한 이유와도 관련이 있다 — 너무 많은 파일 I/O가 성능을 저하시켰기 때문이다 [^337^].

**Phase 2: LLM-based Summarization** [^214^]. Phase 1만으로 충분하지 않을 때, dedicated compaction agent(더 저렴한 모델 사용 가능)가 대화 전체를 요약한다. 최근 메시지는 그대로 유지하고 중간 부분만 압축한다. 요약 결과는 다음 구조를 따른다:

```
## Goal
[사용자가 달성하려는 것]

## Standing Instructions
[사용자의 지속적 지시사항]

## Key Discoveries
[중요 발견, 관련 코드, 오류 메시지]

## Accomplished So Far
[완료/진행 중인 작업, 변경된 파일]

## Relevant Files & Paths
[관련 파일 경로 목록]

## Next Steps
[에이전트가 하려던 다음 작업]
```

Zoo Code는 이 패턴을 VS Code Extension 내에서 **Crow의 `crow_compact` 도구 호출**로 구현한다. 대화 이력의 관리는 Extension Host 메모리가 아닌 Crow 서버에 위임함으로써, Extension Host의 메모리 제약을 회피한다. `crow_compact`는 `context` 레지스터의 오래된 entry를 요약하여 `arch` 레지스터에 저장하고, 원본은 soft-delete(strength=0) 처리한다.

**Claude Code와의 비교**: Claude Code는 ~75% 컨텍스트 사용 시점에 auto-compact를 트리거한다 [^372^]. 트리거 후에는 **Rehydration** 단계를 거쳐 최근에 접근한 파일 5개를 다시 로드하여 작업 연속성을 유지한다 [^401^]. Zoo Code는 이 rehydration 패털도 적용해야 한다 — compaction 후 최근에 수정한 파일들의 내용을 다시 LLM 컨텍스트에 주입하여 "압축으로 인한 단기 기억 상실"을 방지한다.

### 1.5.5 바이브 점수: 현재 4/10 → 목표 9/10

| 지표 | 현재 (4/10) | 목표 (9/10) | 개선 방식 |
|------|:-----------:|:-----------:|:----------|
| 장시간 대화 안정성 | 1시간 후 "멍해짐" | 4시간+ 안정적 유지 | [MCP] `crow_compact` 10분 간격 자동 실행 |
| 토큰 효율성 | 전체 이력 전송 | Pruning + 요약으로 60%+ 절감 | [MCP] OpenCode 2-phase compaction 적용 |
| 메모리 안정성 | globalState 비대 → crash | Extension Host 메모리 제약 내 안정 | [튜닝] 대화 이력 → Crow `crow.bin` 위임 |
| 요약 후 연속성 | 없음 | Rehydration으로 최근 파일 재로드 | [튜닝] compaction 후 최근 5개 파일 자동 재주입 |

9점이 아닌 10점인 이유는, compaction은 근본적으로 "손실 압축"이기 때문이다. 아무리 정교한 요약이라도 원본 대화의 일부 정보는 소실된다. 10점은 "압축이 전혀 불필요한 무한 컨텍스트 윈도우"를 의미하며, 이는 현재 LLM 기술로는 불가능하다. 하지만 4→9의 도약은 사용자가 "AI가 멍해진다"는 느낌을 거의 받지 않는 수준을 의미한다.

---

## 1.6 조사 차원 5: 파일 탐색/생성 마찰 (File Navigation Friction within VS Code)

### 1.6.1 "어떤 파일을 열까요?" UX 분석

Zoo Code에서 AI가 "어떤 파일을 열까요?"라고 묻는 순간, 바이브는 깨진다. 이 질문은 AI가 프로젝트 구조를 이해하지 못했음을 드러낸다. 사용자는 마치 "네비게이션 없이 운전하라"고 하는 것처럼 느낀다 — 길을 아는 사람이 길을 묻는 느낌, 이 기묘한 불일치가 흐름을 끊는다.

이 문제의 근원은 LLM 컨텍스트에 프로젝트 트리가 자동 주입되지 않는다는 점이다. Claude Code의 `/init` 명령은 프로젝트를 종합적으로 스캔하여 LLM이 코드베이스의 전체적인 구조를 이해하도록 돕는다 [^450^]. Continue.dev의 `@Tree` 컨텍스트 프로바이더는 워크스페이스의 구조를 직접 참조할 수 있게 한다 [^542^]. 반면 Zoo Code는 사용자가 명시적으로 파일을 멘션하거나, `list_files` 도구를 호출할 때까지 프로젝트 구조를 모른다 [^527^].

이것은 단순한 불편함이 아니다. 파일 탐색 마찰이 클수록 사용자는 "AI에게 계속 알려줘야 한다"는 피로감을 느낀다. 이 피로감은 누적되어, 결국 사용자는 AI보다 직접 파일을 열게 된다. AI는 "조수"가 아니라 "짐"이 된다.

### 1.6.2 `vscode.workspace.findFiles` 프로젝트 트리 자동 스캔

VS Code Extension API의 `workspace.findFiles()`는 Glob 패턴을 기반으로 파일을 검색하며, `files.exclude` 설정을 자동으로 존중한다 [^51^]. 대형 워크스페이스(10000+ 파일)에서는 `maxResults`와 `CancellationToken`으로 성능을 제어할 수 있다.

**[튜닝] 프로젝트 트리 자동 스캔 및 캐싱**:

```typescript
// [튜닝] 프로젝트 트리 자동 스캔 — system prompt에 자동 주입
class ProjectTreeScanner {
  private treeCache: string | null = null;
  private cacheTimestamp: number = 0;
  private readonly CACHE_TTL_MS = 30 * 1000; // 30초 TTL
  private watcher: vscode.FileSystemWatcher | null = null;

  constructor(private context: vscode.ExtensionContext) {}

  async initialize(): Promise<void> {
    // 초기 스캔
    await this.rescan();

    // [튜닝] 파일 생성/삭제/이름변경 시 트리 갱신
    const folder = vscode.workspace.workspaceFolders?.[0];
    if (!folder) return;

    this.watcher = vscode.workspace.createFileSystemWatcher(
      new vscode.RelativePattern(folder, '**/*')
    );

    // debounce: 여러 파일 변경 이벤트를 한 번에 처리
    let debounceTimer: NodeJS.Timeout | null = null;
    const refreshTree = () => {
      if (debounceTimer) clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => this.invalidateAndRescan(), 1000);
    };

    this.watcher.onDidCreate(refreshTree);
    this.watcher.onDidDelete(refreshTree);
    this.watcher.onDidChange(() => {}); // 내용 변경은 무시

    this.context.subscriptions.push(this.watcher);
  }

  private async rescan(): Promise<void> {
    const folders = vscode.workspace.workspaceFolders;
    if (!folders || folders.length === 0) return;

    // 중요 파일 우선 스캔: package.json, README, src/ 등
    const includePatterns = [
      '{package.json,Cargo.toml,go.mod,pyproject.toml,pom.xml,README.md}',
      'src/**/*',
      'lib/**/*',
      'components/**/*',
      'pages/**/*',
      'app/**/*'
    ];

    const treeLines: string[] = ['## Project Structure\n'];

    for (const pattern of includePatterns) {
      const files = await vscode.workspace.findFiles(
        pattern,
        '**/node_modules/**', // 제외 패턴
        100 // maxResults 제한
      );

      for (const f of files) {
        const rel = vscode.workspace.asRelativePath(f);
        const depth = rel.split('/').length;
        const indent = '  '.repeat(depth - 1);
        const isDir = !rel.includes('.');
        treeLines.push(`${indent}${isDir ? '📁' : '📄'} ${rel}`);
      }
    }

    this.treeCache = treeLines.join('\n');
    this.cacheTimestamp = Date.now();
  }

  private async invalidateAndRescan(): Promise<void> {
    this.treeCache = null;
    await this.rescan();

    // [MCP] Crow의 arch 레지스터에 프로젝트 구조 업데이트
    if (this.treeCache) {
      await crowIngest({
        content: `Project structure updated: ${this.treeCache.substring(0, 1000)}`,
        register: 'arch',
        metadata: { source: 'tree_scanner', importance: 0.6 }
      });
    }
  }

  // Zoo Code 프롬프트 빌더에서 호출
  getTreeForPrompt(): string {
    if (!this.treeCache) return '';
    if (Date.now() - this.cacheTimestamp > this.CACHE_TTL_MS) {
      this.rescan().catch(console.error); // 비동기 갱신
    }
    return this.treeCache;
  }
}
```

### 1.6.3 캐싱 전략: FileSystemWatcher + LRU + TTL

대형 프로젝트에서 매 턴 `findFiles()`를 실행하는 것은 토큰 낭비를 넘어 성능 문제를 일으킨다. `FileSystemWatcher` [^110^]를 활용한 증분 업데이트가 필수적이다.

**종합 캐싱 전략**:

| 전략 | 목적 | 구현 방식 | VS Code API |
|------|------|----------|-------------|
| 메모리 내 트리 | 빠른 경로 조회 | `Map<URI, Node>` + 자식 참조 | `workspace.fs.readDirectory` |
| 증분 업데이트 | 전체 재스캔 방지 | `FileSystemWatcher` + `onDidCreate/Delete/RenameFiles` | `createFileSystemWatcher()` |
| LRU Cache | 메모리 제한 내 최적 유지 | Map + 접근 시간 기반 제거 | Extension 내 구현 |
| TTL Cache | 부실 데이터 방지 | 타임스탬프 + 주기적 정리 | `setInterval` 또는 이벤트 기반 |

**주의**: FileSystemWatcher는 대규모 프로젝트에서 OS의 file watch handle 한계를 초과할 수 있다. Linux의 기본 `max_user_watches`는 65,536이며, 초과 시 `"Visual Studio Code is unable to watch for file changes" (error ENOSPC)`가 발생한다 [^110^]. 이를 방지하려면 `files.watcherExclude` 설정으로 `node_modules`, `.git`, `dist`, `build` 등을 반드시 제외해야 한다 [^171^].

```json
// 자동 주입되는 .vscode/settings.json
{
  "files.watcherExclude": {
    "**/.git/objects/**": true,
    "**/node_modules/*/**": true,
    "**/dist/**": true,
    "**/build/**": true,
    "**/.next/**": true,
    "**/coverage/**": true
  }
}
```

### 1.6.4 `arch` register 연동

Crow Memory의 `arch` 레지스터는 프로젝트 아키텍처 결정을 장기 저장하는 장기 기억(LTM) 공간이다 [^dim12^]. 사용자가 특정 폴터 구조를 선호한다는 편향이 `arch`에 저장되면, AI는 새 파일을 생성하기 전에 이 편향을 확인하여 자동으로 생성 위치를 결정할 수 있다.

예를 들어 `arch` 레지스터에 "사용자는 Next.js App Router 프로젝트에서 페이지를 `app/_(route)/page.tsx`에 생성함"이라는 항목이 저장되어 있으면, 사용자가 "새 사용자 프로필 페이지를 만들어"라고 요청했을 때 AI는 `app/users/profile/page.tsx`에 자동으로 생성한다. "어떤 파일을 만들까요?"라는 질문은 나오지 않는다.

이 연동은 `[MCP] crow_recall`을 파일 생성 전에 자동 호출하는 `[튜닝]` 패턴으로 구현된다:

```typescript
// [튜닝] 파일 생성 전 arch 레지스터 자동 확인
async function getFileCreationBias(fileType: string): Promise<string> {
  // [MCP] Crow의 arch 레지스터에서 파일 생성 관련 편향 검색
  const memories = await crowRecall({
    domain: 'coding',
    register: 'arch',
    query: `file creation pattern for ${fileType}`
  });

  if (memories.length > 0) {
    return `\n[Project Architecture Bias] ${memories.map(m => m.content).join('\n')}`;
  }
  return '';
}
```

### 1.6.5 바이브 점수: 현재 5/10 → 목표 9/10

| 지표 | 현재 (5/10) | 목표 (9/10) | 개선 방식 |
|------|:-----------:|:-----------:|:----------|
| "어떤 파일을 열까요?" 빈도 | 자주 발생 | 거의 없음 | [튜닝] `ProjectTreeScanner`로 트리 자동 주입 |
| 프로젝트 구조 인지 | 수동 list_files 필요 | 자동 인지 | [튜닝] system prompt에 트리 prepend |
| 파일 생성 위치 | "어디에 만들까요?" 질문 | 자동 결정 | [MCP] `crow_recall(arch)`로 생성 위치 편향 확인 |
| 트리 정보 최신성 | 없음(수동 갱신) | 30초 TTL + 변경 감시 | [튜닝] `FileSystemWatcher` + TTL 캐시 |

9점이 아닌 10점인 이유는, 프로젝트 트리 주입은 토큰을 소모하며, 대형 프로젝트에서는 트리 정보가 너무 커질 수 있다는 제약 때문이다. `maxResults` 제한과 파일 패턴 필터링으로 이를 관리하지만, 완벽한 "프로젝트 전체를 한눈에 아는 AI"는 RAG(검색 증강 생성) 기반 시맨틱 검색이 필요하며, 이는 VS Code Extension API의 범위를 약간 넘어선다.

---

## 1.7 조사 차원 6: 외부 리소스 탐색 (External Resource Loop within VS Code)

### 1.7.1 수동 브라우저 복붙의 흐름 단절

"React 19의 새 훅 문서를 찾아줘"라고 Zoo Code에게 요청했을 때, 현재의 경험은 어떠한가? Zoo Code는 웹 검색 기능이 없으므로, 사용자는 브라우저를 직접 열어야 한다. Google에 검색어를 입력하고, 공식 문서 링크를 찾아 클릭하고, 관련 섹션을 읽고, 필요한 코드 예제를 드래그해 복사한 뒤, 다시 VS Code로 돌아와 채팅창에 붙여넣는다.

이 과정의 문제는 시간(약 1-2분)보다 **흐름의 단절**에 있다. 사용자의 뇌는 "React 19 훅의 API 시그니처를 어떻게 설계하지?"라는 창조적 사고에서 "어떤 URL이 공식 문서였지?"라는 탐색적 사고로 전환된다. 손은 키보드에서 마우스로, VS Code에서 브라우저로 이동한다. 이 context switch는 코딩 바이브를 깨뜨리는 가장 강력한 흐름 단절 중 하나다.

OpenCode와 Claude Code는 각각 내장 WebSearch 도구 [^501^]와 Brave Search MCP 통합으로 이 루프를 자동화한다. 검색 결과는 Markdown으로 정리되어 LLM 컨텍스트에 직접 주입되며, 사용자는 브라우저를 열 필요가 없다.

### 1.7.2 Extension 내 Brave Search/Tavily 호출

VS Code Extension은 Node.js 런타임을 기반으로 하므로 `node-fetch`, `axios`, 또는 내장 `https` 모듈을 사용하여 HTTP 요청을 수행할 수 있다 [^528^]. 이를 활용해 Brave Search API나 Tavily API를 Extension 내에서 직접 호출할 수 있다.

**[튜닝] VS Code Extension 내 검색 구현**:

```typescript
// [튜닝] VS Code Extension 내 웹 검색 — Brave Search API
interface SearchResult {
  title: string;
  url: string;
  snippet: string;
  rawContent?: string;
}

class ExtensionSearchProvider {
  private apiKey: string;

  constructor(private context: vscode.ExtensionContext) {
    this.apiKey = this.context.globalState.get('braveSearchApiKey', '');
  }

  async search(query: string, maxResults: number = 5): Promise<SearchResult[]> {
    if (!this.apiKey) {
      throw new Error('Brave Search API key not configured. Set it in Zoo Code settings.');
    }

    const response = await fetch('https://api.search.brave.com/res/v1/web/search', {
      method: 'GET',
      headers: {
        'X-Subscription-Token': this.apiKey,
        'Accept': 'application/json'
      },
      // @ts-ignore
      params: new URLSearchParams({ q: query, count: String(maxResults) })
    });

    if (!response.ok) throw new Error(`Search failed: ${response.status}`);

    const data = await response.json();
    return data.web?.results?.map((r: any) => ({
      title: r.title,
      url: r.url,
      snippet: r.description
    })) ?? [];
  }

  // 검색 결과를 Markdown으로 정리하여 LLM 컨텍스트에 주입
  formatForLLM(results: SearchResult[]): string {
    const lines: string[] = ['## Web Search Results\n'];
    for (let i = 0; i < results.length; i++) {
      const r = results[i];
      lines.push(`### ${i + 1}. ${r.title}`);
      lines.push(`**URL:** ${r.url}`);
      lines.push(`**Snippet:** ${r.snippet}\n`);
    }
    return lines.join('\n');
  }
}
```

Tavily API는 AI 애플리케이션 전용으로 설계된 검색 엔진으로, `/search`, `/extract`, `/crawl` 세 가지 엔드포인트를 제공하며, 검색 결과에 원본 콘텐츠가 포함되는 점이 Brave Search보다 AI 컨텍스트에 더 적합하다 [^503^][^507^].

### 1.7.3 MCP 도구 vs 내장 기능 비교

외부 리소스 탐색을 **MCP 도구(`crow_research`)**로 구현할 것인지, **Extension의 내장 기능**으로 구현할 것인지의 선택은 중요한 아키텍처 결정이다.

| 비교 항목 | MCP 도구(`crow_research`) | Extension 내장 기능 |
|----------|--------------------------|-------------------|
| **호출 방식** | LLM이 tool call로 명시적 호출 | Extension이 자동 호출 후 주입 |
| **사용자 인지도** | "검색 중..." 표시 | 완전 투명 |
| **Crow 연동** | 자연스러움 (MCP 서버가 직접 접근) | Extension이 Crow 클라이언트 호출 필요 |
| **구현 복잡도** | MCP 서버에 추가 | Extension 코드 수정 |
| **바이브 점수** | 7점 (명시적 tool call) | 8점 (자동 주입) |
| **유연성** | LLM이 검색 시점/쿼리 결정 | Extension이 정책 결정 |

**권장 설계**: 두 접근법을 **하이브리드**로 결합한다. Extension은 사용자의 쿼리에 특정 패턴("~에 대해 찾아줘", "~ 문서를 알려줘", "~ 최신 버전은")을 감지하면 자동으로 검색을 실행하고 결과를 LLM 컨텍스트에 주입한다(내장 기능). 동시에 LLM은 명시적으로 `crow_research` tool을 호출하여 더 깊이 있는 검색을 수행할 수 있다(MCP). 이 하이브리드는 "검색이 필요할 때는 자동, 더 깊이 필요할 때는 명시적"이라는 이중 전략이다.

### 1.7.4 검색 결과 `life_context` 저장

검색 결과를 Crow Memory의 `life_context` 레지스터에 저장하면, 사용자가 최근에 어떤 주제를 검색했는지를 다음 세션에서도 기억할 수 있다. "React 19 문서를 찾아봤구나"라는 맥락은, 사용자가 다음에 "그 use 훅 말인데"라고만 입력했을 때, Zoo Code는 그가 무엇을 말하는지 알게 된다.

```typescript
// [MCP] 검색 결과 자동 저장 — life_context에 누적
async function saveSearchToCrow(query: string, results: SearchResult[]): Promise<void> {
  await crowIngest({
    content: `User searched for: "${query}". Top result: ${results[0]?.title} (${results[0]?.url})`,
    register: 'life_context',
    metadata: {
      source: 'web_search',
      importance: 0.6,
      ttl: 7 * 24 * 3600, // 7일 TTL — 검색 정보는 상대적으로 짧은 기간 유용
      tags: ['search', query.split(' ')[0]] // 첫 단어를 태그로
    }
  });
}
```

### 1.7.5 바이브 점수: 현재 3/10 → 목표 8/10

| 지표 | 현재 (3/10) | 목표 (8/10) | 개선 방식 |
|------|:-----------:|:-----------:|:----------|
| 웹 검색 경험 | 수동 브라우저 복붙 (1-2분) | Extension 내 자동 검색 (3초) | [튜닝] `ExtensionSearchProvider` 구현 |
| 검색 결과 주입 | 수동 붙여넣기 | 자동 LLM 컨텍스트 주입 | [튜닝] 검색 결과 → prompt prepend |
| 검색 기억 | 세션 종료 시 소멸 | Crow `life_context`에 7일 유지 | [MCP] `crowIngest` → `life_context` |
| 다중 검색 엔진 | 없음 | Brave Search + Tavily 선택 가능 | [튜닝] 설정 기반 검색 엔진 선택 |

8점이 아닌 9점인 이유는, 웹 검색은 여전히 **네트워크 지연**이라는 물리적 제약을 가지기 때문이다. Brave Search API 호출에 1-3초가 걸리며, 이 시간 동안 사용자는 응답을 기다려야 한다. 10점은 "즉시" 응답이 오는 상태를 의미하지만, 네트워크 호출은 근본적으로 비동기적이다. 다만 3초의 자동 검색 대 1-2분의 수동 복붙은 바이브 차원에서 천지차이다.

---

## 1.8 Wave 1 사용자 경험 스토리

### 1.8.1 "VS Code를 켰다. 3초 안에 Zoo Code + Crow가 준비되었다."

**스토리 1: 아침의 완벽한 재개**

지훈은 어제 밤 11시 47분까지 Zoo Code와 함께 인증 모듈을 리팩토링하고 있었다. JWT 토큰 갱신 로직이 `useAuth` 훅에 통합되는 작업이었고, 어제는 테스트 케이스 3개까지 통과한 상태였다. 그는 VS Code를 닫고 잠자리에 들었다.

오늘 아침, 지훈은 VS Code를 켰다. 프로젝트가 로드되는 2초 동안 그는 머그컵을 드는 것 말고 아무것도 하지 않았다. 프로젝트가 열리자마자 Zoo Code Extension이 활성화되었다. 사이드바의 Zoo Code 패널을 보니, 이미 "Code + Crow Memory" 모드로 설정되어 있었다. Extension의 상태바 메시지가 잠깐 떴다 — "Zoo Code: 'code_plus_crow' 모드로 자동 복원됨" — 그리고 2초 만에 사라졌다. 지훈은 모드를 선택하는 클릭을 한 번도 하지 않았다.

Crow Memory의 SSE 서버는 VS Code 종료 후에도 살아 있었다. `detached: true`로 실행된 프로세스는 밤새 메모리에서 `crow.bin`을 유지했고, Extension이 재활성화되자마자 `reconnect()`가 기존 서버를 재탐색했다. 지훈은 채팅창에 "어제 거기서 계속해"라고만 입력했다. Zoo Code는 어제의 마지막 작업을 이해했고, 남은 테스트 케이스 2개를 제안했다.

지훈은 파일을 하나 수정하고 저장했다. 10분이 지났고, Crow는 백그라운드에서 자동으로 `crow_compact()`를 실행했다 — 어제의 대화를 요약하여 `life_context`에 저장했다. 지훈은 이 compaction이 일어났는지도 몰랐다. 그의 뇌에는 오직 "JWT 갱신 로직"만 있었다.

지훈이 `npm run build`를 실행하자, 터미널은 나타나지 않았다. `presentation.reveal: silent` 설정 덕분에 빌드는 백그라운드에서 실행되었다. 5초 후, 빌드 에러가 발생했다. 터미널이 자동으로 나타났고, 에러 메시지는 동시에 Crow의 `bug` 레지스터에 저장되었다. Zoo Code의 채팅창에 "`src/hooks/useAuth.ts`에서 TypeScript 에러가 있습니다"라는 메시지가 자동으로 나타났다. 지훈은 터미널에서 에러를 복사하는 행위를 한 번도 하지 않았다. 에러 메시지는 이미 LLM의 컨텍스트에 있었다.

지훈은 "고쳐줘"라고만 입력했다. AI는 에러를 분석하고 코드를 수정했다. 수정 후 `AutoBuildFix`가 활성화되어 있어, 자동으로 재빌드가 실행되었다. 이번에는 빌드가 성공했다. 터미널은 다시 사라졌다. 지훈은 전체 과정에서 터미널을 1초 이상 바라본 적이 없었다.

**스토리 2: 새 파일 생성의 무의식**

민아는 Next.js App Router 프로젝트에서 새로운 "대시보드 설정" 페이지를 만들어야 했다. 그녀는 Zoo Code 채팅창에 "사용자 대시보드 설정 페이지를 만들어줘"라고 입력했다.

Zoo Code는 "어떤 파일을 만들까요?"라고 묻지 않았다. 대신, Extension이 30초 전에 스캔한 프로젝트 트리가 system prompt에 자동으로 주입되어 있었기 때문이다. LLM은 프로젝트 구조를 알고 있었다: `app/` 디렉토리 아래에 `(dashboard)/settings/page.tsx`가 있어야 한다는 것을.

그리고 Crow의 `arch` 레지스터에는 "이 사용자는 Next.js App Router에서 페이지를 `app/_(segment)/page.tsx`에 생성함"이라는 기억이 저장되어 있었다 [^MCP 연동]. LLM은 이 편향을 읽고, 자동으로 올바른 경로에 파일을 생성했다.

민아는 파일 경로를 지정하지 않았다. 심지어 파일 경로를 생각하지도 않았다. 그녀의 뇌에는 "대시보드 설정 페이지"만 있었고, 나머지는 Zoo Code가 처리했다. 3초 후, `app/(dashboard)/settings/page.tsx`가 생성되었고, `useAuth` 훅을 import하는 코드가 자동으로 포함되어 있었다. Crow의 `style` 레지스터에 "모든 페이지는 useAuth로 인증 체크"라는 규칙이 저장되어 있었기 때문이다.

민아는 "흐름"을 잃지 않았다. 그녀는 대시보드 설정 페이지의 UI 로직을 계속 생각할 수 있었다. 파일 경로, import 문, 인증 체크 — 이것들은 이미 "해결된 문제"였다.

**스토리 3: 외부 문서의 즉각적 통합**

성호는 React 19의 새 `use` 훅 문법을 확인해야 했다. 그는 Zoo Code 채팅창에 "React 19 use 훅 최신 문법 찾아서 여기에 적용해줘"라고 입력했다.

3초 후, Zoo Code Extension의 내장 검색 기능이 자동으로 Tavily API를 호출했다. "React 19 use hook syntax"라는 쿼리로 검색 결과를 수집하고, Markdown으로 정리하여 LLM 컨텍스트에 주입했다. 성호는 브라우저를 열 필요가 없었다. 검색 결과의 첫 번째 항목은 React 공식 문서였고, `use` 훅의 API 시그니처와 예제 코드가 LLM 컨텍스트에 포함되었다.

Zoo Code는 검색 결과를 읽고, 성호의 기존 코드에 `use` 훅을 적용하는 수정을 제안했다. 성호는 제안을 검토하고 승인했다.

검색 결과는 자동으로 Crow의 `life_context` 레지스터에 저장되었다. "사용자가 2026년 5월 26일에 React 19의 use 훅 문법을 검색함"이라는 기록이다. 3일 후, 성호가 "그 use 훅 말인데"라고만 입력했을 때, Zoo Code는 그가 무엇을 말하는지 알았다. 검색 기록이 Crow의 회색 메모리를 통해 자동으로 주입되었기 때문이다.

성호는 외부 문서를 "찾는" 과정 자체를 잊어버렸다. 그의 뇌에는 "use 훅을 적용하자"만 있었고, 나머지는 투명하게 처리되었다.

---

## 1.9 Wave 1 기술적 구현 체크리스트 (20+ 항목)

Wave 1의 모든 구현 항목은 `[튜닝]`(Zoo Code Extension 소스 직접 수정) 또는 `[MCP]`(MCP 도구 호출/추가) 태그로 구분된다. 모든 항목은 VS Code Extension API 내에서 구현 가능하다.

### 세션 지속성 (Session Survivability)

- [ ] **[튜닝]** `CrowServerManager` 클래스 구현: `child_process.spawn` with `detached: true` + PID 파일 기반 재탐색
- [ ] **[튜닝]** `deactivate()` 훅 최소화: 서버 종료 금지, 연결 정보 저장만 수행
- [ ] **[튜닝]** `lastCustomMode` globalState 저장: Custom Mode 변경 시 즉시 저장 (종료 직전 의존 금지) [^141^]
- [ ] **[튜닝]** `restoreLastCustomMode()`: `activate()`에서 마지막 모드 자동 복원
- [ ] **[튜닝]** `setKeysForSync(['lastCustomMode'])`: Settings Sync로 다중 머신 동기화 [^55^]
- [ ] **[MCP]** 세션 시작 시 `crowIngest` → `life_context`: 세션 복원 이벤트 기록
- [ ] **[튜닝]** 3계층 중복 세션 구조: L1(detached SSE) + L2(globalState) + L3(crow.bin)

### 모드 전환 마찰 (Mode Switching Friction)

- [ ] **[튜닝]** `AutoModeDetector` 클래스: `onDidChangeWorkspaceFolders` 이벤트 기반 자동 모드 감지
- [ ] **[튜닝]** 프로젝트 메타데이터 파일 스캔: `package.json`, `Cargo.toml`, `go.mod` 등 기반 모드 결정
- [ ] **[튜닝]** `.zoo/config.json` 지원: `defaultMode` 필드로 프로젝트 기본 모드 설정
- [ ] **[튜닝]** `AgentsMdInjector`: `FileSystemWatcher`로 `AGENTS.md` 변경 감시 및 프롬프트 자동 주입
- [ ] **[튜닝]** `AGENTS.md` 200줄 제한: 토큰 낭비 방지 [^313^]

### 빌드-코드-피드백 루프 (Build Feedback Loop)

- [ ] **[튜닝]** `registerCrowBuildProvider()`: Task Provider 등록으로 자동 빌드 태스크 제공 [^160^]
- [ ] **[튜닝]** `presentation.reveal: silent`: 에러 없으면 터미널 미표시 [^135^]
- [ ] **[튜닝]** `onDidEndTaskProcess` 구독: 빌드 결과 자동 수집 [^51^]
- [ ] **[튜닝]** `diagnosticDebounce`: `onDidChangeDiagnostics` 중복 트리거 방지 (1초 debounce) [^239^]
- [ ] **[튜닝]** `AutoBuildFixLoop`: max_attempts=3 + 반복 에러 감지 + oscillation 감지 + no-op 패치 감지
- [ ] **[튜닝]** `RollbackManager`: Git stash 기반 빌드 전 백업 및 실패 시 복원
- [ ] **[MCP]** 빌드 실패 시 `crowIngest` → `bug` register: 빌드 에러 패턴 누적 학습
- [ ] **[MCP]** 빌드 성공 시 `crowIngest` → `arch` register: 빌드 패턴 아카이빙

### 컨텍스트 로트 (Context Rot)

- [ ] **[MCP]** `AutoCompactionTimer`: 파일 저장 시 10분 간격 `crow_compact` 자동 호출
- [ ] **[튜닝]** 대화 이력 `globalState` → `crow.bin` 위임: Extension Host 메모리 제약 회피
- [ ] **[MCP]** OpenCode 2-phase compaction 적용: Pruning(40K 토큰 기준) + LLM 요약
- [ ] **[튜닝]** Rehydration: compaction 후 최근 5개 파일 자동 재주입
- [ ] **[튜닝]** Extension Host 메모리 모니터링: 80% 도달 시 경고 + 강제 compaction

### 파일 탐색 마찰 (File Navigation Friction)

- [ ] **[튜닝]** `ProjectTreeScanner`: `findFiles()` 기반 프로젝트 트리 자동 스캔
- [ ] **[튜닝]** `FileSystemWatcher` 기반 증분 트리 갱신: 파일 생성/삭제/이름변경 시 갱신
- [ ] **[튜닝]** 트리 캐시 TTL 30초: 대형 프로젝트 성능 최적화
- [ ] **[튜닝]** `files.watcherExclude` 자동 설정: `node_modules`, `.git`, `dist` 제외 [^110^]
- [ ] **[MCP]** 파일 생성 전 `crow_recall(arch)`: 아키텍처 편향 기반 자동 생성 위치 결정

### 외부 리소스 탐색 (External Resource Loop)

- [ ] **[튜닝]** `ExtensionSearchProvider`: Brave Search API / Tavily API Extension 내 호출
- [ ] **[튜닝]** 검색 키워드 자동 감지: "~ 찾아줘", "~ 문서" 패턴 자동 검색 트리거
- [ ] **[MCP]** 검색 결과 `crowIngest` → `life_context`: 7일 TTL로 검색 기록 유지
- [ ] **[튜닝]** 검색 결과 Markdown 포맷팅: LLM 컨텍스트에 자동 주입

### 통합 및 인프라

- [ ] **[튜닝]** 에러 컨텍스트 `injectLLMContext()` / `clearLLMContext()`: LLM 컨텍스트 관리 유틸리티
- [ ] **[튜닝]** 상태바 메시지 표준화: 모든 자동 작업은 상태바로 표시 (3초 후 자동 사라짐)
- [ ] **[튜닝]** `.zoo/config.json` 스키마 정의: 프로젝트 메타데이터 구조
- [ ] **[MCP]** 전체 Wave에서 `crow_diagnostics` 연동: 메모리 서버 상태 모니터링

---

## 1.10 Wave 1 Crow Memory 연동 포인트

Wave 1의 모든 설계안은 Crow Memory의 특정 도구와 레지스터에 연결된다. 다음 매트릭스는 각 조사 차원이 Crow의 어떤 인프라와 연동되는지를 요약한다.

| 조사 차원 | Crow 도구 | Crow 레지스터 | 연동 목적 |
|:----------|:----------|:-------------|:----------|
| 세션 지속성 (1.2) | `crow_compact` | `life_context` | 세션 요약 저장, 다음 세션 복원 |
| 세션 지속성 (1.2) | `crow_recall` | `life_context` | 이전 세션 맥락 회상 |
| 모드 전환 (1.3) | `crow_ingest` | `arch` | `AGENTS.md` 프로젝트 규칙 장기 저장 |
| 모드 전환 (1.3) | `crow_recall` | `arch` | 프로젝트 특화 규칙 자동 회상 |
| 빌드-피드백 (1.4) | `crow_ingest` | `bug` | 빌드 에러 패턴 누적, 예방적 수정 |
| 빌드-피드백 (1.4) | `crow_ingest` | `arch` | 빌드 성공 패턴 아카이빙 |
| 컨텍스트 로트 (1.5) | `crow_compact` | `context` → `arch` | 대화 요약 및 장기 저장소 프로모션 |
| 컨텍스트 로트 (1.5) | `crow_recall` | `life_context` | 압축된 세션 요약 회상 |
| 파일 탐색 (1.6) | `crow_recall` | `arch` | 폴터 구조 편향 기반 자동 파일 생성 |
| 파일 탐색 (1.6) | `crow_ingest` | `arch` | 프로젝트 트리 구조 업데이트 |
| 외부 리소스 (1.7) | `crow_ingest` | `life_context` | 검색 기록 7일 유지 |
| 외부 리소스 (1.7) | `crow_recall` | `life_context` | 과거 검색 맥락 자동 회상 |

**연동 패턴 요약**: Wave 1에서 가장 빈번하게 사용되는 Crow 도구는 `crow_ingest`(기록 저장)와 `crow_recall`(기록 회상)이다. `crow_compact`는 세션 종료 및 주기적 압축 시점에 호출되며, `arch` 레지스터는 프로젝트 특화 규칙과 구조를, `life_context`는 세션 간 연속성을, `bug`는 빌드 에러 패턴을 각각 담당한다. 이 3개 레지스터의 내용이 풍부해질수록 Wave 2-4의 기능들이 자연스럽게 강화된다 — 예를 들어 `bug` 레지스터에 축적된 에러 패턴은 Wave 2의 YOLO 안전망에서 "이 에러는 이렇게 고친다"는 예방적 편향으로 활용되며, `arch` 레지스터의 프로젝트 구조 정보는 Wave 3의 Zero-Explanation 컨텍스트 주입의 핵심 소스가 된다.

**SSE 서버의 중심성**: 모든 연동은 동일한 MCP SSE 서버(9020 포트)를 통해 이루어진다. 이 서버가 `detached: true`로 생존하는 한, 사용자의 기억은 VS Code의 재시작과 무관하게 유지된다. Wave 1의 핵심 기술적 성과는 "VS Code Extension이 죽어도 기억은 살아있다"는 이 단순하면서도 강력한 보장이다.


---

# 2. Wave 2: Fearless YOLO — YOLO Surgeon의 5계층 안전망

> *"YOLO는 묪함이 아니다. 회복할 수 없을 때만 묪함이다. 회복할 수 있다면 그것은 실험이고, 실험은 창조의 어머니다."*

바이브코딩의 帛(돋을일)은 "과감함"에서 시작된다. 사용자가 AI에게 "이것저것 건드려봐"라고 말하는 순간, 코딩은 더 이상 명령어의 나열이 아니라 호흡이 된다. 그러나 그 호흡이 끊어지는 지점은 예상보다 잦다. YOLO 모드로 10개 파일을 수정한 뒤 빌드가 실패했을 때, 사용자는 터미널의 빨간 글씨를 본다. 그 순간 "아, 망했다"는 생각이 들고, 그 생각이 들면 바이브는 이미 깨진 것이다. Wave 1의 Flow Keeper가 흐름의 연속성을 지켜줬다면, Wave 2의 YOLO Surgeon은 그 흐름이 **묪한 방향으로 흘러도** 1초 만에 되돌릴 수 있는 안전망을 설계한다.

Claude Code는 `Esc×2` 한 번으로 이 문제를 해결한다. 사용자가 그 키를 누륾 때, 대화 턴 단위의 checkpoint가 자동으로 복구되며 코드와 대화가 동시에 되돌아간다 [^29^][^31^]. Git worktree는 세션 간의 완전한 파일 시스템 격리를 제공하며, 병렬 subagent가 동일한 파일을 동시에 수정핼 수 있는 충돌 방지 메커니즘을 구현한다 [^76^]. 그러나 이 모든 아름다움은 **터미널 기반**이라는 전제 위에 서 있다. Claude Code의 worktree auto-cleanup은 2026년 4월, 10일간의 작업을 영구 삭제하는 치명적 데이터 손실(GitHub #46444)을 일으켰으며 [^21^], 이 사건은 "완벽한 자동화"가 오히려 신뢰를 파괴할 수 있음을 보여준다.

Zoo Code는 VS Code Extension 안에 머무른다. 이 제약은 worktree의 물리적 격리나 Git stash의 원자적 트랜잭션을 직접 사용할 수 없음을 의미한다. 하지만 동시에 이 제약은 **다른 길**을 만들어 낸다. VS Code의 `FileSystemWatcher`는 파일 변경을 실시간으로 감지하고, `localHistory`는 저장 시마다 자동 버전을 생성하며, `WorkspaceEdit`은 AI의 수정 집합을 하나의 논리적 단위로 묶을 수 있다 [^51^][^44^]. 이 3계층 API의 조합 — 사전 방지(Prevention), 실시간 보호(Real-time Protection), 사후 복구(Post-hoc Recovery) — 이 바로 Zoo Code만의 "Fearless YOLO" 안전망이다.

이 장에서는 5개 조사 차원을 순회하며, VS Code Extension API의 제약 속에서 Claude Code의 안전성을 능가하는(적어도 동등한) YOLO 경험을 설계한다. 모든 수치는 분석 기반 추정이며, 모든 의사코드는 VS Code Extension API 내에서 구현 가능한 것만을 다룬다.

---

## 2.1 YOLO 안전망 3계층 설계도 개요

YOLO Surgeon의 안전 메커니즘은 인체의 면역 체계처럼 **3계층 중복 구조**로 설계된다. 한 계층이 실패하면 다음 계층이 보완하고, 모든 계층이 동시에 작동할 때 사용자는 "과감함"을 "묪함"이 아니라 "탐험"으로 인식한다. 각 계층은 VS Code Extension API의 특정 표면에 대응하며, Crow Memory의 특정 도구와 연동된다.

### 2.1.1 계층 1: 사전 방지(Prevention) — Permission Gradation + `.yoloignore`

사전 방지 계층은 **위험이 발생하기 전에 행위를 통제**하는 메커니즘이다. Claude Code의 6단계 permission 모드(default → acceptEdits → plan → auto → dontAsk → bypassPermissions) [^182^]와 `.claude/settings.json`의 `deny > ask > allow` 규칙 평가 [^386^]에서 영감을 받되, VS Code Extension API의 제약 내에서 재해석된다.

Zoo Code의 사전 방지 계층은 두 개의 레일을 동시에 놓는다. 첫째는 **Permission Gradation 매트릭스** — 5개 행위(읽기/생성/수정/실행/삭제) × 5개 수준(Deny/Ask/Scoped/Allow/Bypass)의 교차 테이블이다. 사용자는 `defaultMode`를 하나의 문자열로 설정하는 것이 아니라, 행위별로 다른 신뢰 수준을 할당할 수 있다. 예를 들어 "읽기는 Allow, 생성은 Scoped, 실행은 Ask, 삭제는 Deny"라는 조합은 AI가 자유롭게 코드를 탐색하고 프로젝트 내에서만 파일을 생성하되, 터미널 명령은 매번 묻고, 삭제는 절대 허용하지 않는 정교한 통제를 가능하게 한다.

둘째는 **`.yoloignore` 파일**이다. `.gitignore`의 문법을 그대로 따를 때, 프로젝트 루트의 `.yoloignore`는 AI가 절대 접근해서는 안 되는 파일들을 선언적으로 기술한다. `.env`, `secrets.json`, `*.pem`, `terraform.tfstate` 등 민감한 파일뿐 아니라, 사용자가 "이 평더는 AI가 건드리면 안 돼"라고 마킹한 임의의 경로도 보호할 수 있다. `.yoloignore`는 Crow Memory의 `life_avoid` 레지스터와 연동되어, 사용자가 "이 파일은 절대 건드리지 마"라고 말하면 그 패턴이 자동으로 `.yoloignore`에 반영되고 다음 세션부터도 유효해진다.

이 계층의 핵심 Crow 연동 포인트는 `life_avoid` 레지스터이다. 사용자의 명시적 회피 지시(`polarity = -2.0`)가 축적될수록 [^386^], 사전 방지 계층은 점점 두터워진다. 사용자가 매번 "이 파일은 건들지 마"라고 말해야 한다면 바이브는 깨지지만, 한 번 말하면 영원히 기억되는 시스템은 바이브를 지킨다.

**구현 방식**: [튜닝] — Zoo Code Extension의 파일 쓰기 인터셉터에 `.yoloignore` 패턴 매칭 로직을 주입. [MCP] — `life_avoid` 레지스터의 축적 패턴을 `crow_evolve_propose`로 `.yoloignore` 동기화.

### 2.1.2 계층 2: 실시간 보호(Real-time Protection) — FileSystemWatcher + 메모리 트랜잭션 로그

실시간 보호 계층은 **위험이 발생하는 순간 감지하고 즉시 대응**하는 메커니즘이다. VS Code의 `FileSystemWatcher`는 OS 네이티브 파일 시스템 이벤트(inotify, FSEvents, ReadDirectoryChangesW)를 기반으로 동작하며 [^115^], 파일의 생성/변경/삭제를 실시간으로 감지한다. 이 API를 YOLO Surgeon은 두 가지 목적으로 사용한다.

첫째는 **`yocto` — lightweight 자동 백업 시스템**이다. AI가 파일을 수정하기 직전, `FileSystemWatcher`의 `onDidChange` 이벤트가 발화되며, Zoo Code Extension은 해당 파일의 현재 내용을 `~/.zoo-code/yocto/{sessionId}/{timestamp}/`에 `fs.copyFileSync`로 즉시 복사한다. 이 백업은 1MB 미만의 파일 기준 평균 0.8초 이내에 완료되며, Git history를 전혀 더럽히지 않는다. 사용자가 "되돌려줘"라고 말하면, yocto 백업을 `fs.copyFileSync`로 원위치에 복사하는 데 걸리는 시간은 0.3초에 불과하다.

둘째는 **메모리 트랜잭션 로그**이다. AI가 10개 파일을 동시에 수정하는 "YOLO 집합"을 시작할 때, Zoo Code Extension은 `pending_edits[]` 배열에 각 수정의 원본 내용, 대상 경로, 의존성을 기록한다. 이 트랜잭션은 메모리 내에서만 관리되며, 모든 수정이 성공적으로 완료되면 "커밋"되어 디스크에 반영된다. 만약 중간에 빌드 실패가 감지되면(`onDidEndTaskProcess`의 `exitCode !== 0`), Extension은 자동으로 `pending_edits[]`를 역순으로 순회하며 각 파일을 원본 내용으로 복구한다. 이 롤백은 메모리 기반이므로 Git의 `git stash pop`보다 수백 배 빠르다.

이 계층의 핵심 Crow 연동 포인트는 `crow_manage_backup` 도구이다. YOLO 모드 진입 직전, Extension은 자동으로 `crow_manage_backup create`를 호출하여 현재 `crow.bin`의 전체 스냅샷을 `~/.zoo-code/crow/backups/`에 저장한다 [^370^]. 이것이 파일 수준의 yocto 백업과 함께 작동할 때, 사용자는 "코드 백업 + 메모리 백업"의 이중 안전망 아래에서 YOLO를 즐길 수 있다.

**구현 방식**: [튜닝] — `FileSystemWatcher` 설정, yocto 디렉토리 관리, `pending_edits[]` 큐 구현. [MCP] — YOLO 진입/퇴장 시 `crow_manage_backup` 자동 호출.

### 2.1.3 계층 3: 사후 복구(Post-hoc Recovery) — Snapshot + Instant Rewind + Auto-Recovery

사후 복구 계층은 **이미 발생한 손상을 복원**하는 메커니즘이다. 이 계층이 존재하는 이유는 단순하다. 어떤 안전망도 100% 완벽할 수 없으며, 특히 4B 로컬 모델이 tool call을 30-60% 확률로 "잊어버리는" 현상이 존재하는 한 [^dim06^], 실시간 보호가 실패할 여지는 항상 남아있다.

사후 복구 계층은 세 가지 메커니즘으로 구성된다. 첫째는 **VS Code `localHistory` 연동**이다. VS Code의 내장 `localHistory`는 파일 저장 시마다 자동으로 버전을 생성하며 [^44^], 각 파일당 최대 50개 항목을 `User/History/{hash}/entries.json`에 저장한다 [^106^]. 이 기능은 Extension API로 직접 접근할 수 없지만 [^136^], Zoo Code Extension은 AI가 파일을 저장할 때마다 `localHistory`의 항목 수가 증가함을 간접적으로 확인할 수 있다. 중요한 점은 `localHistory`가 AI 편집과 사용자 편집을 구분하지 못한다는 한계이지만, 이것은 "누가 수정했든 복구할 수 있다"는 보편적 안전망으로서 기능한다.

둘째는 **YOLO 진입/퇴장 Git 자동 커밋**이다. YOLO 모드에 진입할 때 Zoo Code Extension은 자동으로 `git stash push -m "yolo-before-{timestamp}"`를 실행하여 현재 작업 디렉토리의 상태를 보존한다. YOLO 모드를 종료할 때는, 성공 여부에 관계없이 `git stash`를 하나 더 생성하고, 두 stash 사이의 diff를 하나의 커밋으로 만들어 `--no-ff` 머지 전략으로 기록한다. 이 커밋은 Git history를 "더럽히지" 않는다. 오히려 "YOLO 실험 기록"이라는 명확한 의미를 가진 메타데이터를 남긴다.

셋째는 **AutoBuildFix — 빌드 실패 후 자동 복구 루프**이다. 빌드가 실패하면(`exitCode !== 0`), Zoo Code Extension은 stderr 출력을 `problemMatcher`로 파싱하여 정제된 에러 메시지를 추출하고, 이것을 LLM 컨텍스트에 주입한 뒤 "이 에러를 고쳐라"는 implicit 프롬프트를 추가한다. LLM은 수정을 제안하고, Extension은 자동으로 수정을 적용한 뒤 다시 빌드를 실행한다. 이 루프는 `max_attempts = 3`으로 제한되며, oscillation(수정 A → 수정 B → 다시 수정 A의 무한 반복)을 감지하면 자동으로 중단한다. 이 과정에서 축적된 빌드 실패 패턴은 Crow의 `bug` 레지스터에 자동으로 저장되어, 다음번에는 AI가 "빌드하기 전에" 해당 패턴을 회피하는 "예방적 YOLO"로 진화한다.

**구현 방식**: [튜닝] — `tasks.json` 자동 생성, Git stash 래퍼, AutoBuildFix 루프. [MCP] — `bug` 레지스터 자동 업데이트, `crow_ingest`로 빌드 패턴 축적.

### 3계층 아키텍처의 시각적 구성

```
┌─────────────────────────────────────────────────────────────────┐
│                   YOLO Surgeon 3-Layer Safety Net                │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  LAYER 1: Prevention (사전 방지)                           │  │
│  │  • Permission Gradation 5×5 매트릭스                        │  │
│  │  • .yoloignore 파일 기반 보호                               │  │
│  │  • life_avoid 레지스터 연동                                 │  │
│  │  [crow_recall → life_avoid → .yoloignore 동기화]           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                          ↓ (위험 통과 시)                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  LAYER 2: Real-time Protection (실시간 보호)                │  │
│  │  • yocto: FileSystemWatcher + fs.copyFileSync 자동 백업     │  │
│  │  • pending_edits[] 메모리 트랜잭션 로그                      │  │
│  │  • crow_manage_backup 자동 호출                             │  │
│  │  [onDidChange → 백업 → exitCode 감지 → 역순 롤백]          │  │
│  └───────────────────────────────────────────────────────────┘  │
│                          ↓ (실시간 보호 실패 시)                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  LAYER 3: Post-hoc Recovery (사후 복구)                     │  │
│  │  • VS Code localHistory 버전 복원                           │  │
│  │  • Git stash 자동 rewind                                    │  │
│  │  • AutoBuildFix: 빌드 실패 → LLM 수정 → 재빌드 루프         │  │
│  │  [bug 레지스터 축적 → 예방적 YOLO 진화]                     │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  모든 계층은 VS Code Extension API 내에서 구현                     │
│  모든 Crow 연동은 동일한 SSE 서버(9020)를 통해 이루어짐          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2.2 Snapshot 메커니즘 비교표

YOLO의 안전성은 궁극적으로 "되돌릴 수 있는가"에 의해 결정된다. 사용자가 "되돌려줘"라고 말했을 때 시스템이 1초 안에 반응하는가, 아니면 5초 이상 기다린 뒤 불확실한 상태로 돌아가는가. 이 차이가 바이브를 만든다. 본 절에서는 3가지 스냅샷 방식을 기술적 차원에서 비교하고, VS Code Extension 내에서의 최적 조합을 도출한다.

### 2.2.1 Git-based vs VS Code localHistory vs Extension 메모리 기반: 3방식 비교

스냅샷 메커니즘은 크게 3가지 철학으로 나뉜다. Git 기반은 "변경의 의미"를 저장한다. 파일 시스템 기반은 "파일의 상태"를 저장한다. 메모리 기반은 "수정의 의도"를 저장한다. 각 방식은 서로 다른 강점과 약점을 가지며, Zoo Code의 YOLO Surgeon은 이 3가지를 **계층적으로 중복 배치**함으로써 단일 방식의 한계를 보완한다.

**Table 1: Snapshot 메커니즘 3방식 비교**

| 특성 | Git-based (Claude Code /rewind) | VS Code localHistory | Extension 메모리 기반 (yocto) |
|------|:---:|:---:|:---:|
| **저장 단위** | 대화 턴(conversation turn) 단위 [^29^] | 파일 저장 시마다 자동 [^44^] | 파일 변경 감지 시마다 |
| **저장 위치** | `~/.claude/file-history/{sessionId}/` [^31^] | `~/History/{hash}/` [^106^] | `~/.zoo-code/yocto/{sessionId}/` |
| **증분/전체** | 증분 (해시 기반 버전 관리) [^31^] | 전체 파일 복사본 [^106^] | 전체 파일 복사본 |
| **복구 속도** | 빠름 (git checkout) | 빠름 (파일 복원) | **가장 빠름** (fs.copyFileSync) |
| **세션 경계** | 세션 내에서만 유효 | 워크스페이스 간 공유 가능 | 세션별 격리 |
| **Git history 영향** | 없음 (별도 저장소) | 없음 | 없음 |
| **Bash 명령 추적** | **불가** [^38^] | 불가 | 불가 (파일 변경만 감지) |
| **자동화 수준** | 완전 자동 (턴당) | 완전 자동 (저장 시) | 완전 자동 (변경 감지 시) |
| **보관 한도** | 세션당 100개 [^31^] | 파일당 50개 [^44^] | 설정 가능 (기본 30일) |
| **VS Code Extension API 활용** | 간접 (`child_process.exec`) | **직접 접근 불가** [^136^] | 직접 (`fs` + `FileSystemWatcher`) |
| **Crow 연동** | `crow_manage_backup` | 없음 | `crow_manage_backup` |
| **바이브 점수** | 7/10 (턴 단위 제약) | 5/10 (API 접근 불가) | 8/10 (가장 빠른 복구) |

**분석**: 이 비교표는 단일 방식의 불완전성을 명확히 드러낸다. Git 기반은 의미 있는 checkpoint를 생성하지만 대화 턴에 묶여 있어 "한 턴 내의 특정 파일만 복구"가 불가능하다 [^29^]. `localHistory`는 가장 투명하고 사용자 친화적이지만, 공식 Extension API가 부재하여 프로그래밍적으로 접근할 수 없다 [^136^]. yocto(Extension 메모리 기반)는 가장 빠른 복구 속도를 제공하지만, 파일 시스템 이벤트에 의존하므로 파일을 수정하지 않는 Bash 명령(`rm -rf`)의 추적은 불가능하다.

Zoo Code의 전략은 **"3방식의 장점을 모두 취하고 단점은 상호 보완"**하는 것이다. yocto가 실시간 백업을 담당하고, `localHistory`가 사용자 수준의 버전 관리를 담당하며, Git stash가 YOLO 진입/퇴장의 의미 있는 경계를 담당한다. 이 3중 중복은 "어느 한 방식이 실패핼 수 있지만, 모두 동시에 실패할 확률은 극히 낮다"는 안전 설계의 기본 원칙을 따른다.

### 2.2.2 100개 파일 기준 `git stash`(2.3s) vs `fs.copyFileSync`(0.8s) 성능

스냅샷의 핵심 지표는 "복구까지의 시간(Time-to-Recovery, TTR)"이다. 사용자가 "되돌려줘"라고 생각한 순간부터 실제로 코드가 복구될 때까지의 시간이 1초를 넘으면, 그 사이 사용자의 뇌는 "망했다"는 생각으로 채워지고 바이브는 깨진다.

100개 파일, 평균 10KB 크기의 프로젝트를 기준으로 한 성능 추정치는 다음과 같다. 이 수치는 파일 시스템의 캐시 상태, 디스크 유형(SSD vs HDD), 동시 I/O 부하에 따라 변동될 수 있으며 [추정] 값이다.

**Table 2: Snapshot 성능 비교 (100개 파일, 10KB 평균)**

| 메트릭 | `git stash push` | `git stash pop` | `fs.copyFileSync` (100개 순차) | `fs.copyFileSync` (100개 병렬, 10동시) | yocto 복구 |
|------|:---:|:---:|:---:|:---:|:---:|
| **스냅샷 생성** | 2.3초 | — | 3.2초 | **0.8초** | — |
| **복구 수행** | — | 1.8초 | 2.8초 | **0.6초** | **0.3초** |
| **Git history 변경** | 없음 (stash) | — | 없음 | 없음 | 없음 |
| **원자성 보장** | 예 | 예 | 아니오 (순차 복사) | 아니오 | 아니오 |
| **디스크 공간 효율** | **높음** (delta) | — | 낮음 (전체 복사) | 낮음 | 낮음 |
| **VS Code Extension 내 구현** | `child_process` 필요 | — | **직접 `fs` 모듈** | **직접 `fs` 모듈** | **직접 `fs` 모듈** |

**분석**: `git stash`는 원자성과 디스크 공간 효율이라는 두 가지 중요한 장점을 제공하지만, 속도는 파일 시스템 직접 복사에 비해 느리다. 이 차이의 원인은 Git이 스냅샷 생성 시 `git write-tree`를 호출하여 blob 객체를 생성하고, 인덱스를 갱신하는 추가 작업을 수행하기 때문이다. 반면 `fs.copyFileSync`는 운영체제의 `copy_file_range` 시스템 콜을 직접 활용하며, 동일 파일 시스템 내에서는 실제 데이터 복사 없이 메타데이터만 갱신하는 "reflink" 최적화를 이용할 수도 있다.

Zoo Code의 yocto 시스템은 이 성능 차이를 극대화한다. yocto는 단일 파일 단위로 백업하므로, 100개 파일을 동시에 백업할 필요가 없다. AI가 파일 A를 수정하면 파일 A만 백업하고, 파일 B를 수정하면 파일 B만 백업한다. 이 지연(lazy) 백업 전략은 100개 파일의 전체 스냅샷이 아니라 "수정되는 파일만 실시간 백업"하는 방식으로, 평균 대기 시간을 거의 0에 가깝게 만든다. 복구 시에도, 사용자가 "되돌려줘"라고 하면 마지막으로 수정된 파일만 복구하면 되는 것이 아니라, yocto가 자동으로 해당 세션에서 백업된 모든 파일을 원위치로 복사한다.

**핵심 인사이트**: Git 기반은 "의미 있는 경계"에 적합하고, `fs.copyFileSync`는 "실시간 속도"에 적합하다. yocto는 후자의 철학을 극한까지 밀어붙인 시스템이다.

### 2.2.3 Claude Code 해시 기반 증분 스냅샷: `~/.claude/file-history/{sessionId}/`

Claude Code의 checkpoint 시스템은 가장 정교한 상용 스냅샷 메커니즘 중 하나로, VS Code 내에서의 대체 구현 설계에 중요한 참고점을 제공한다. 이 시스템의 낮은 수준 구조는 다음과 같이 분석된다 [^31^][^29^].

Checkpoint는 `~/.claude/file-history/{sessionId}/` 디렉토리 내에 저장되며, 각 파일은 원본 경로의 SHA-256 해시값 + 버전 번호 형태의 이름을 가진다. 예를 들어 `src/auth.ts`의 첫 번째 버전은 `{hash_of_src/auth.ts}@v1`으로, 두 번째 버전은 `@v2`로 저장된다. 변경되지 않은 파일은 이전 버전을 재사용하는 증분 저장 방식을 사용하여 디스크 공간을 절약한다. 세션당 최대 100개 checkpoint를 유지하며, 초과 시 가장 오래된 것부터 제거한다. 자동 정리 기간은 기본 30일(`cleanupPeriodDays`)이다.

이 설계가 Zoo Code에 주는 시사점은 명확하다. 첫째, **해시 기반 파일 식별**은 경로 변경에도 내성을 가진다. 파일이 이동핬을 때 경로 기반 식별은 실패하지만, 해시 기반은 내용 기반이므로 이동을 감지할 수 있다. 둘째, **증분 저장**은 디스크 공간을 효율적으로 사용한다. yocto는 현재 전체 복사 방식을 사용하지만, 향후 Rsync 알고리즘이나 단순한 diff 기반 증분 저장으로 최적화할 수 있다. 셋째, **세션 격리**는 각 세션의 checkpoint가 독립 디렉토리에 저장되어 충돌을 방지한다.

Zoo Code의 yocto는 이 3가지 시사점을 VS Code Extension API 내에서 구현한다. 파일 식별은 VS Code의 `Uri.toString()` 기반 해싱을 사용하고, 세션 격리는 `ExtensionContext.sessionId` 또는 타임스탬프 기반 디렉토리로 구현한다. 증분 저장은 Phase 1에서 필수가 아니며, 전체 복사의 단순성이 증분 저장의 공간 효율보다 더 중요한 초기 설계 원칙이다. "복구가 확실한 단순 시스템"이 "복구가 불확실한 복잡 시스템"보다 YOLO의 정신에 더 부합하기 때문이다.

---

## 2.3 Permission Gradation 매트릭스

YOLO 모드의 핵심 딜레마는 "자율성 vs 안전성"의 트레이드오프이다. AI가 너무 많은 자율성을 가지면 위험해지고, 너무 적은 자율성을 가지면 YOLO가 아니다. 이 딜레마를 해결하기 위해 Claude Code는 6단계 permission 모드를, Kilo Code는 3단계(allow/ask/deny) + glob 패턴을, OpenCode는 plugin hook 아키텍처를 각각 제시한다 [^182^][^412^][^503^]. Zoo Code는 이들의 장점을 종합하여, **5×5 Permission Gradation 매트릭스**를 설계한다.

### 2.3.1 5개 행위(읽기/생성/수정/실행/삭제) × 3개 툴(Zoo/Open/Claude) × 수준 비교

행위 분류는 AI가 코드베이스와 상호작용하는 모든 작업을 5개 범주로 나눈다. 이 분류는 Claude Code의 도구 분류(Tool Classification) [^127^]와 Kilo Code의 명시적 도구 목록 [^412^]을 종합한 것이다.

**Table 3: 5개 행위 × 5개 수준 Permission Gradation 매트릭스 (Zoo Code 설계)**

| 수행 \ 행위 | 읽기 (Read) | 생성 (Create) | 수정 (Modify) | 실행 (Execute) | 삭제 (Delete) |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **Lv.1 Deny** | ❌ 차단 | ❌ 차단 | ❌ 차단 | ❌ 차단 | ❌ 차단 |
| **Lv.2 Ask** | ❓ 매번 묻기 | ❓ 매번 묻기 | ❓ 매번 묻기 | ❓ 매번 묻기 | ❓ 매번 묻기 |
| **Lv.3 Scoped** | ✅ 프로젝트 내 | ✅ 프로젝트 내 | ✅ 프로젝트 내 | ✅ 안전 명령만 | ❌ 차단 |
| **Lv.4 Allow** | ✅ 전체 | ✅ 전체 | ✅ 전체 | ✅ 전체 | ❓ 매번 묻기 |
| **Lv.5 Bypass** | ✅ 전체 | ✅ 전체 | ✅ 전체 | ✅ 전체 | ✅ 전체 |

**행위 정의**:
- **읽기**: `Read`, `Glob`, `Grep`, `List` — 파일/디렉토리 내용 읽기
- **생성**: `Write`, `CreateFile`, `CreateDirectory` — 새 파일/디렉토리 생성
- **수정**: `Edit`, `ApplyEdit`, `ApplyPatch` — 기존 파일 내용 변경
- **실행**: `Bash`, `PowerShell`, `npm run`, `git` — 터미널 명령 실행
- **삭제**: `DeleteFile`, `DeleteDirectory`, `rm`, `rmdir` — 파일/디렉토리 삭제

**수준 정의**:
- **Lv.1 Deny**: 해당 행위를 완전히 차단. AI가 시도하면 Extension이 자동으로 거부
- **Lv.2 Ask**: 해당 행위를 시도할 때마다 사용자에게 승인 대화상자 표시
- **Lv.3 Scoped**: 특정 범위 내에서만 자동 승인(프로젝트 디렉토리 내, 안전 명령만)
- **Lv.4 Allow**: 해당 행위를 자동 승인하되, 삭제는 예외(항상 Ask)
- **Lv.5 Bypass**: 모든 검사 무시. 격리된 컨테이너/VM 전용

**분석**: 이 매트릭스의 핵심 설계 원칙은 **"삭제는 항상 특별 대우"**이다. Lv.4 Allow에서도 삭제는 Lv.2 Ask로 강등된다. 이는 파일 생성과 수정은 undo/rewind로 복구 가능하지만, 삭제는 복구가 더 어렵거나 불가능할 수 있기 때문이다. `.env` 파일의 삭제는 복구가 가능하다지만, `rm -rf node_modules` 실행 후의 정신적 충격은 undo로도 회복되지 않는다.

또한 Lv.3 Scoped의 "안전 명령"은 미리 정의된 허용 목록(allowlist)에 의해 결정된다. `npm run *`, `git status`, `git log`, `cat`, `ls` 등의 읽기 전용 또는 프로젝트 내 안전 명령은 자동 승인되지만, `rm *`, `sudo *`, `git push --force`, `DROP TABLE` 등은 차단되거나 Ask로 강등된다. 이 allowlist는 `.yoloignore`와 함께 프로젝트 루트의 `.zoo/permissions.json`에 저장되며, Crow의 `life_avoid` 레지스터와 동기화된다.

### 2.3.2 Claude Code 6단계 모드 분석

Claude Code의 permission 시스템은 현재 AI 코딩 도구 중 가장 정교한 것으로 평가된다 [^182^][^386^]. 6단계 모드의 상세 분석은 Zoo Code의 5×5 매트릭스 설계에 직접적인 참고 자료가 된다.

**Table 4: Claude Code 6단계 Permission 모드 vs Zoo Code 5×5 매핑**

| Claude Code 모드 | 파일 편집 | 쉘 명령 | MCP 도구 | Zoo Code 매핑 | 안전 수준 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| `default` | 첫 사용 시 묻기 | 매번 묻기 | 매번 묻기 | 전체 Lv.2 Ask | 높음 |
| `acceptEdits` | **자동 승인** | 매번 묻기 | 매번 묻기 | 읽기 Lv.4, 생성/수정 Lv.3, 실행 Lv.2 | 중간 |
| `plan` | **차단** | 읽기 전용만 | 차단 | 읽기 Lv.3, 나머지 Lv.1 | 최고 |
| `auto` | AI classifier 기반 | AI classifier | AI classifier | Scoped + 분류기 | 중간 |
| `dontAsk` | 사전 승인만 | 사전 승인만 | 사전 승인만 | 설정된 Scoped | 중간 |
| `bypassPermissions` | 전체 자동 승인 | 전체 자동 승인 | 전체 자동 승인 | 전체 Lv.5 | 낮음 |

**Claude Code만의 고유 기능**:

1. **Protected Paths**: `bypassPermissions`를 제외한 모든 모드에서 `.git/`, `.vscode/`, `.husky/`, `.bashrc` 등에 대한 쓰기는 여전히 프롬프트가 표시된다 [^127^][^177^]. 이는 "가장 높은 권한 모드에서도 특정 경로는 예외"라는 원칙을 구현한 것이다.

2. **AI Classifier (Auto Mode)**: 2026년 3월 Team plan부터 rollout된 2단계 파이프라인으로, Stage 1에서 8.5% FPR(false positive rate)의 빠른 필터를, Stage 2에서 0.4% FPR의 정밀 평가를 수행한다 [^502^]. 평가 차원은 scope escalation, untrusted infrastructure, prompt injection의 3가지이다.

3. **규칙 평가 순서**: `deny > ask > allow`로, 첫 매칭이 승리하며 deny가 최우선이다 [^386^]. Hook이 "allow"를 반환핬어도 deny 규칙은 여전히 적용된다 [^468^].

Zoo Code는 이 3가지 고유 기능 중 Protected Paths와 규칙 평가 순서를 직접 계승한다. `.yoloignore`가 Protected Paths의 역할을 하고, `.zoo/permissions.json`의 `deny` > `ask` > `allow` 평가 순서가 규칙 우선순위를 결정한다. AI Classifier는 4B 로컬 모델의 성능 제약상 직접 구현이 어려우므로, 대신 **허용 목록(allowlist) 기반의 정적 분류**로 대체한다. 이는 "완벽한 AI 분류"보다 "예측 가능한 정적 규칙"을 선택한 것으로, 사용자가 "이 명령은 항상 허용" 또는 "이 명령은 항상 차단"을 명시적으로 선언하는 방식이다.

### 2.3.3 Zoo Code 5×5 Permission 매트릭스 설계 (의사코드)

Permission Gradation 매트릭스의 실제 구현은 Zoo Code Extension의 파일 쓰기/실행 인터셉터에 집중된다. 다음 의사코드는 `.zoo/permissions.json` 설정 파일을 파싱하고, AI의 각 행위를 평가하여 허용/차단/묻기를 결정하는 로직을 보여준다.

```typescript
// [튜닝] Zoo Code Extension — Permission Gradation Engine
// 위치: src/core/safety/PermissionGradation.ts

interface PermissionConfig {
  version: '1.0';
  defaultProfile: string;
  profiles: Record<string, PermissionProfile>;
  protectedPaths: string[];      // Protected paths (항상 Ask/Deny)
  yoloignore: string[];          // .yoloignore 패턴 (자동 동기화)
}

interface PermissionProfile {
  name: string;
  description: string;
  // 5개 행위 × 5개 수준 중 하나
  levels: {
    read:     1 | 2 | 3 | 4 | 5;  // Deny → Bypass
    create:   1 | 2 | 3 | 4 | 5;
    modify:   1 | 2 | 3 | 4 | 5;
    execute:  1 | 2 | 3 | 4 | 5;
    delete:   1 | 2 | 3 | 4 | 5;
  };
  // 행위별 allowlist / denylist (Lv.3 Scoped용)
  scoped: {
    execute_allowlist: string[];  // 예: ["npm run *", "git status", "cat"]
    execute_denylist:  string[];  // 예: ["rm -rf *", "sudo *", "git push --force"]
  };
}

class PermissionGradationEngine {
  private config: PermissionConfig;
  private activeProfile: PermissionProfile;
  private yoloIgnorePatterns: minimatch.Minimatch[];

  constructor(context: vscode.ExtensionContext) {
    // ~/.zoo/permissions.json 또는 프로젝트 루트 .zoo/permissions.json 로드
    this.config = this.loadConfig();
    this.activeProfile = this.config.profiles[this.config.defaultProfile];
    // .yoloignore 패턴 컴파일
    this.yoloIgnorePatterns = this.config.yoloignore.map(
      p => new minimatch.Minimatch(p, { dot: true })
    );
  }

  /**
   * AI의 행위를 평가하여 PermissionDecision 반환
   * @param action — 'read' | 'create' | 'modify' | 'execute' | 'delete'
   * @param target — 대상 파일 경로 또는 명령어 문자열
   * @param agentId — 행위를 시도하는 AI 에이전트 ID
   */
  async evaluate(
    action: ActionType,
    target: string,
    agentId: string
  ): Promise<PermissionDecision> {
    // 1단계: .yoloignore 패턴 확인 (가장 먼저, 모든 수준에서 적용)
    if (this.isYoloIgnored(target)) {
      return {
        decision: 'deny',
        reason: `Target matches .yoloignore pattern`,
        fallback: 'This file/directory is protected by .yoloignore'
      };
    }

    // 2단계: Protected Paths 확인 (Protected paths는 항상 Ask 이상)
    if (this.isProtectedPath(target)) {
      return {
        decision: 'ask',
        reason: `Target is in protected path list`,
        requiresUserConfirm: true
      };
    }

    // 3단계: Permission Profile의 수준 확인
    const level = this.activeProfile.levels[action];
    
    switch (level) {
      case 1: // Deny
        return { decision: 'deny', reason: `${action} is set to Deny` };
      
      case 2: // Ask
        return { 
          decision: 'ask', 
          reason: `${action} is set to Ask`,
          requiresUserConfirm: true 
        };
      
      case 3: { // Scoped
        const scopedResult = this.evaluateScoped(action, target);
        return scopedResult; // allow | ask | deny
      }
      
      case 4: // Allow (삭제는 예외적으로 Ask)
        if (action === 'delete') {
          return { 
            decision: 'ask', 
            reason: 'Delete always requires confirmation at Allow level',
            requiresUserConfirm: true 
          };
        }
        return { decision: 'allow' };
      
      case 5: // Bypass (Protected paths만 제외)
        return { decision: 'allow', bypass: true };
      
      default:
        return { decision: 'ask', reason: 'Unknown level — defaulting to Ask' };
    }
  }

  /**
   * Lv.3 Scoped 평가: allowlist/denylist 매칭
   */
  private evaluateScoped(action: ActionType, target: string): PermissionDecision {
    const { scoped } = this.activeProfile;
    
    if (action === 'execute') {
      // denylist 먼저 확인 (deny > allow)
      for (const denyPattern of scoped.execute_denylist) {
        if (minimatch(target, denyPattern)) {
          return { decision: 'deny', reason: `Matches denylist: ${denyPattern}` };
        }
      }
      // allowlist 확인
      for (const allowPattern of scoped.execute_allowlist) {
        if (minimatch(target, allowPattern)) {
          return { decision: 'allow', reason: `Matches allowlist: ${allowPattern}` };
        }
      }
      // 어디에도 매칭 안 되면 Ask
      return { decision: 'ask', reason: 'Not in allowlist/denylist' };
    }
    
    // read/create/modify: 프로젝트 내 경로인지 확인
    const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
    if (workspaceRoot && target.startsWith(workspaceRoot)) {
      return { decision: 'allow', reason: 'Within project directory' };
    }
    return { decision: 'ask', reason: 'Outside project directory' };
  }

  private isYoloIgnored(target: string): boolean {
    return this.yoloIgnorePatterns.some(pattern => pattern.match(target));
  }

  private isProtectedPath(target: string): boolean {
    return this.config.protectedPaths.some(
      protected => target.includes(protected) || minimatch(target, protected)
    );
  }

  // [MCP] life_avoid 레지스터와 .yoloignore 동기화
  async syncWithLifeAvoid(): Promise<void> {
    // Crow Memory의 life_avoid 레지스터에서 회피 패턴 조회
    const avoidPatterns = await crowClient.call('crow_recall', {
      domain: 'safety',
      register: 'life_avoid',
      query: 'file patterns to avoid'
    });
    
    // 새로운 회피 패턴을 .yoloignore에 추가
    for (const pattern of avoidPatterns) {
      if (!this.config.yoloignore.includes(pattern.content)) {
        this.config.yoloignore.push(pattern.content);
        // polarity=-2.0 항목은 강력한 회피로 즉시 Deny에도 추가
        if (pattern.polarity <= -2.0) {
          // life_avoid의 강력한 항목은 자동으로 denylist에도 추가
        }
      }
    }
    
    await this.saveConfig();
  }
}

// 사용 예시: AI가 'rm -rf node_modules'를 시도할 때
const engine = new PermissionGradationEngine(context);
const decision = await engine.evaluate('execute', 'rm -rf node_modules', 'main-agent');
// → decision: { decision: 'deny', reason: 'Matches denylist: rm -rf *' }
```

이 Permission Gradation Engine의 핵심 설계 원칙은 **"deny > ask > allow"의 평가 순서**와 **".yoloignore가 모든 수준보다 우선"**이라는 두 가지이다. Claude Code의 규칙 평가 순서 [^386^]를 그대로 계승하면서, `.yoloignore`를 별도의 최우선 계층으로 배치한 것이다. 이는 사용자가 "이 파일은 절대"라고 한 번 표현하면, 어떤 permission profile이 활성화되어 있든 상관없이 그 파일은 보호된다는 의미이다.

`syncWithLifeAvoid()` 메서드는 Crow Memory 연동의 핵심이다. 사용자가 "이 파일은 절대 건드리지 마"라고 말하면, 그 표현은 `life_avoid` 레지스터에 `polarity = -2.0`으로 저장된다 [^386^]. PermissionGradationEngine은 주기적으로(또는 YOLO 모드 진입 시) `crow_recall`로 이 패턴들을 조회하고, `.yoloignore`와 `denylist`에 자동으로 반영한다. 이 과정이 한 세션에서 이루어지면, 다음 세션부터는 사용자가 아무것도 말하지 않아도 해당 파일은 보호된다.

---

## 2.4 조사 차원 1: Instant Rewind within VS Code

> *"Esc×2 — Claude Code가 이 두 번의 키 입력으로 무엇을 보여주는가? 바로 '회복 가능성'이라는 신뢰다."*

Claude Code의 `/rewind`와 `Esc×2`는 가장 직관적인 undo 메커니즘으로 평가된다. 사용자가 빈 프롬프트 상태에서 `Esc`를 두 번 누륾면, 대화 턴 단위의 checkpoint가 자동으로 복구되며 코드와 대화가 동시에 되돌아간다 [^29^]. 이 경험의 바이브 점수는 7/10이다. 턴 단위의 제약이 존재하지만, "한 번의 키 입력으로 되돌아간다"는 경험 자체가 사용자의 불안감을 상당 부분 해소하기 때문이다.

Zoo Code는 VS Code Extension API 안에서 이 경험을 재현해야 한다. 터미널 기반의 `Esc×2` 대신, VS Code의 명령 팔레트(Command Palette) 단축키(`Ctrl+Shift+Z` 또는 `Cmd+Shift+Z`)를 활성화하고, 그 단축키가 yocto 시스템의 `instantRewind()`를 호출하도록 한다. 사용자가 그 키를 누륾 순간, 마지막 YOLO 세션에서 백업된 모든 파일이 원위치로 복사되고, VS Code의 에디터 탭이 자동으로 새로고침된다. 이 과정은 1초를 넘지 않아야 한다.

### 2.4.1 `FileSystemWatcher` + `fs.copyFileSync` 자동 백업: `yocto`

yocto 시스템은 VS Code Extension의 `FileSystemWatcher`를 기반으로 동작하는 lightweight 스냅샷 시스템이다. 이름에서 알 수 있듯, "요octo"(10^-24)는 극도로 작고 가벼운 존재를 의미하며, 이 시스템의 설계 철학이기도 하다. Claude Code의 `~/.claude/file-history/` 디렉토리가 세션당 수십 MB를 차지할 수 있는 것에 비해, yocto는 수정된 파일만 백업하므로 평균 수백 KB에 불과하다.

```typescript
// [튜닝] yocto — Lightweight Snapshot System
// 위치: src/core/safety/YoctoSnapshot.ts

interface YoctoSnapshot {
  id: string;                    // UUID
  sessionId: string;             // VS Code Extension 세션 ID
  timestamp: number;             // 생성 시각 (epoch ms)
  trigger: 'manual' | 'auto' | 'yolo-enter' | 'pre-edit';
  files: YoctoFileEntry[];
  crowBackupId?: string;         // crow_manage_backup 연동 ID
}

interface YoctoFileEntry {
  originalUri: string;           // 원본 파일 경로
  backupUri: string;             // 백업 파일 경로 (yocto 디렉토리 내)
  hash: string;                  // SHA-256 해시 (중복 방지)
  size: number;                  // 파일 크기 (bytes)
  mtime: number;                 // 수정 시각
}

class YoctoSnapshotManager {
  private snapshotsDir: string;   // ~/.zoo-code/yocto/
  private watcher: vscode.FileSystemWatcher;
  private pendingBackup: Map<string, NodeJS.Timeout> = new Map();
  private readonly DEBOUNCE_MS = 200;  // 200ms 디바운싱

  constructor(context: vscode.ExtensionContext) {
    this.snapshotsDir = path.join(os.homedir(), '.zoo-code', 'yocto');
    fs.mkdirSync(this.snapshotsDir, { recursive: true });
    
    // 모든 파일 변경을 감시하는 FileSystemWatcher [^51^][^61^]
    this.watcher = vscode.workspace.createFileSystemWatcher(
      '**/*',           // 모든 파일 감시
      false,            // 생성 이벤트 감지
      false,            // 변경 이벤트 감지
      false             // 삭제 이벤트 감지
    );
    
    // 파일 변경 이벤트에 디바운싱된 백업 로직 연결
    this.watcher.onDidChange(uri => this.scheduleBackup(uri));
    this.watcher.onDidCreate(uri => this.scheduleBackup(uri));
    
    context.subscriptions.push(this.watcher);
  }

  /**
   * 디바운싱된 백업 스케줄링
   * 동일 파일의 연속된 변경은 하나의 백업으로 합침
   */
  private scheduleBackup(uri: vscode.Uri): void {
    const existing = this.pendingBackup.get(uri.fsPath);
    if (existing) clearTimeout(existing);
    
    const timeout = setTimeout(() => {
      this.pendingBackup.delete(uri.fsPath);
      this.backupFile(uri);
    }, this.DEBOUNCE_MS);
    
    this.pendingBackup.set(uri.fsPath, timeout);
  }

  /**
   * 단일 파일 백업 — fs.copyFileSync 사용
   */
  private async backupFile(uri: vscode.Uri): Promise<void> {
    const sessionId = this.getCurrentSessionId();
    const timestamp = Date.now();
    const relativePath = vscode.workspace.asRelativePath(uri);
    const backupDir = path.join(this.snapshotsDir, sessionId, String(timestamp));
    const backupPath = path.join(backupDir, relativePath);
    
    try {
      // 백업 디렉토리 생성
      fs.mkdirSync(path.dirname(backupPath), { recursive: true });
      
      // fs.copyFileSync로 즉시 백업 [^dim01^]
      fs.copyFileSync(uri.fsPath, backupPath);
      
      // 백업 메타데이터 기록
      const entry: YoctoFileEntry = {
        originalUri: uri.fsPath,
        backupUri: backupPath,
        hash: this.computeHash(uri.fsPath),
        size: fs.statSync(uri.fsPath).size,
        mtime: timestamp
      };
      
      await this.appendToSnapshotLog(sessionId, entry);
      
    } catch (err) {
      // 백업 실패 시 조용히 로깅 (사용자 흐름 방해 금지)
      console.error(`[yocto] Backup failed for ${uri.fsPath}:`, err);
    }
  }

  /**
   * Instant Rewind — 마지막 YOLO 세션의 모든 파일 복구
   * 사용자가 Ctrl+Shift+Z를 누르거나 "Zoo: Instant Rewind" 명령을 실행할 때 호출
   */
  async instantRewind(sessionId?: string): Promise<RewindResult> {
    const targetSession = sessionId || this.getCurrentSessionId();
    const snapshot = await this.loadLatestSnapshot(targetSession);
    
    if (!snapshot || snapshot.files.length === 0) {
      return { success: false, reason: 'No snapshot found for rewind' };
    }
    
    const results: FileRewindResult[] = [];
    
    for (const file of snapshot.files) {
      try {
        // fs.copyFileSync로 원위치 복구 [^dim01^]
        fs.copyFileSync(file.backupUri, file.originalUri);
        results.push({ path: file.originalUri, success: true });
      } catch (err) {
        results.push({ path: file.originalUri, success: false, error: String(err) });
      }
    }
    
    // VS Code 문서 캐시 새로고침
    for (const result of results) {
      if (result.success) {
        const doc = await vscode.workspace.openTextDocument(result.path);
        await vscode.window.showTextDocument(doc);
      }
    }
    
    const successCount = results.filter(r => r.success).length;
    
    return {
      success: successCount > 0,
      restoredFiles: successCount,
      totalFiles: results.length,
      failedFiles: results.filter(r => !r.success).map(r => r.path),
      durationMs: Date.now() - startTime
    };
  }

  /**
   * [MCP] YOLO 진입 시 crow_manage_backup 자동 호출
   */
  async createCrowBackup(): Promise<string | null> {
    try {
      const result = await crowClient.call('crow_manage_backup', {
        action: 'create',
        name: `yolo-before-${Date.now()}`,
        auto: true
      });
      return result.backupId;
    } catch {
      return null;  // Crow 백업 실패핼 수 있음 — yocto만으로도 작동
    }
  }

  private computeHash(filePath: string): string {
    const data = fs.readFileSync(filePath);
    return crypto.createHash('sha256').update(data).digest('hex').substring(0, 16);
  }
}

// 명령 팔레트 등록
vscode.commands.registerCommand('zoo.instantRewind', async () => {
  const result = await yoctoManager.instantRewind();
  if (result.success) {
    vscode.window.showInformationMessage(
      `YOLO Rewind 완료: ${result.restoredFiles}/${result.totalFiles} 파일 복구 (${result.durationMs}ms)`
    );
  } else {
    vscode.window.showWarningMessage('되돌릴 스냅샷이 없습니다.');
  }
});
```

이 yocto 시스템의 핵심 설계 특성은 **디바운싱**과 **지연(lazy) 백업**이다. `FileSystemWatcher`는 OS 수준 이벤트를 직접 전달하므로, 한 파일의 저장은 여러 개의 `onDidChange` 이벤트를 발생시킬 수 있다 [^115^]. 200ms의 디바운싱 윈도우는 이러한 이벤트 폭주를 하나의 백업으로 합쳐주며, 동시에 사용자가 느끼는 성능 영향을 최소화한다.

`instantRewind()` 메서드의 성능 목표는 명확하다. 100개 파일의 복구를 1초 이내에 완료하는 것이다. `fs.copyFileSync`는 Node.js의 동기 파일 I/O로, 단일 파일 복사 시 콜백 지옥 없이 순차적 흐름을 유지한다. 비동기 병렬 처리(`Promise.all`)를 사용하면 더 빠를 수 있지만, 동기 처리는 디버깅이 용이하고 실패 시의 상태가 명확하다는 장점이 있다. yocto는 안전성을 최우선으로 하므로, 기본적으로 순차 복사를 사용하되 50개 이상의 파일이 동시에 복구될 때만 낮은 수준의 병렬화(10개 동시)를 활성화한다.

### 2.4.2 Git `/undo` vs 파일 시스템 snapshot 속도/안전성

Git 기반 복구와 파일 시스템 기반 복구의 트레이드오프는 "속도 vs 원자성 vs 디스크 효율"의 3축에서 발생한다. Git은 원자성과 디스크 효율에 강하고, 파일 시스템은 속도에 강하다.

Git `git stash pop`의 복구 과정은 다음과 같이 분필 수 있다: (1) stash의 tree 객체를 working directory에 checkout, (2) unstaged 변경사항 복원, (3) stash 목록에서 제거. 이 과정은 Git의 낮은 수준 명령들이 서로 의존하므로 중간에 실패하면 working directory가 일관성 없는 상태가 될 수 있다. 하지만 성공하면 100% 원자적이며, stash 자체가 Git 객체이므로 디스크 공간을 효율적으로 사용한다.

반면 `fs.copyFileSync`의 복구는 단순하다. 백업 파일을 원본 위치에 덮어쓴다. 이 과정은 중간에 실패핼 경우 원본 파일이 yocto 백업의 일부만 덮어씌워지는 "반쪽짜리 파일"이 될 수 있다. 이 문제를 해결하기 위해 yocto는 복구 전에 현재 파일의 상태를 "rewind를 위한 rewind"용 임시 백업(`pre-rewind-snapshot`)을 추가로 생성한다. 만약 복구가 중간에 실패하면, 이 임시 백업으로 원래 상태를 복원한다.

Zoo Code의 전략은 **"빠른 복구는 yocto가, 안전한 복구는 Git이, 투명한 복구는 localHistory가"** 담당하는 것이다. 사용자가 "되돌려줘"라고 말하면 0.3초 만에 yocto가 반응한다. yocto가 실패하면 Git stash를 시도한다. Git도 실패하면 사용자에게 `localHistory`의 Timeline 뷰를 안내한다. 이 3중 대체(fallback) 체인은 어떤 상황에서도 사용자가 "망했다"는 생각을 하지 않도록 보장한다.

### 2.4.3 `crow_manage_backup create` 자동 호출

yocto의 파일 수준 백업은 코드의 상태를 보존하지만, Crow Memory의 상태는 보존하지 않는다. YOLO 세션 동안 AI가 `bug` 레지스터에 새로운 패턴을 기록하거나, `life_avoid`에 새로운 회피 지시를 저장할 수 있다. 만약 YOLO가 실패하여 사용자가 되돌아가고 싶어 한다면, 코드뿐 아니라 메모리 상태도 되돌려야 일관성이 유지된다.

이 문제를 해결하기 위해 Zoo Code Extension은 YOLO 모드 진입 직전에 `crow_manage_backup create`를 자동 호출한다. 이 백업은 `crow.bin`의 전체 스냅샷을 `~/.zoo-code/crow/backups/`에 저장하며 [^370^], yocto의 파일 백업과 함께 작동하여 "코드 + 메모리"의 완전한 복구 포인트를 생성한다. YOLO 모드 종료 후 성공하면 이 백업은 자동으로 삭제되지만, 실패 후 rewind를 하면 Crow 백업도 함께 복구되어 메모리 상태가 YOLO 이전으로 돌아간다.

### 2.4.4 바이브 점수: 현재 3/10 → 목표 9/10

| 메트릭 | 현재 (3/10) | 목표 (9/10) | 개선 전략 |
|:---|:---:|:---:|:---|
| 되돌리기 속도 | 5초+ (Git 수동) | **0.3초** (yocto) | `fs.copyFileSync` 자동 백업 |
| 되돌리기 정밀도 | 전체 프로젝트 | **파일 단위** 선택 | yocto per-file snapshot |
| Crow 메모리 복구 | 없음 | **자동** `crow_manage_backup` | YOLO 진입/퇴장 자동 호출 |
| 단축키 존재 | 없음 | **Ctrl+Shift+Z** | 명령 팔레트 + 단축키 등록 |
| 시각적 피드백 | 없음 | **상태바 인디케이터** | TreeView에 YOLO 상태 표시 |

현재 Zoo Code의 undo 경험이 3/10인 이유는 간단하다. 사용자가 실패한 YOLO를 되돌리려면 Git 명령어를 직접 입력하거나, VS Code의 기본 Undo(`Ctrl+Z`)를 수십 번 눌러야 한다. 이 과정에서 사용자의 뇌는 "내가 뭘 했더라?"를 기억해야 하고, 그 기억의 부담이 바이브를 깬다. 목표 9/10은 "되돌리기의 존재를 사용자가 의식하지 않는" 상태이다. AI가 수정할 때마다 자동으로 백업되고, "되돌려줘" 한 마디(또는 한 번의 키 입력)로 모든 것이 원위치로 돌아가는 경험이다.

---

## 2.5 조사 차원 2: Checkpoint Granularity within VS Code

Instant Rewind가 "빠른 복구"에 집중했다면, Checkpoint Granularity는 "의미 있는 경계"에 집중한다. 사용자가 YOLO 모드를 시작하기 전의 상태를 보존하고, YOLO가 성공하면 그 상태를 Git history에 "깔끔하게" 기록하는 것이다. 이는 "되돌리기"보다 "앞으로 나아가기"의 철학이다.

### 2.5.1 VS Code `localHistory` 활용

VS Code의 `localHistory`는 2022년 3월(v1.66)부터 내장된 기능으로, 파일 저장 시마다 자동으로 버전을 생성한다 [^44^]. 주요 설정은 다음과 같다.

```json
// [튜닝] Zoo Code가 자동 주입하는 VS Code 설정
{
  "workbench.localHistory.enabled": true,
  "workbench.localHistory.maxFileSize": 512,
  "workbench.localHistory.maxFileEntries": 100,
  "workbench.localHistory.mergeWindow": 5,
  "workbench.localHistory.exclude": {
    "**/node_modules/**": true,
    "**/.git/**": true,
    "**/.zoo-code/yocto/**": true,
    "**/dist/**": true,
    "**/build/**": true
  }
}
```

Zoo Code Extension은 YOLO 모드 진입 시 이 설정을 자동으로 확인하고, `maxFileSize`와 `maxFileEntries`를 안전한 값으로 조정한다. `localHistory`의 핵심 장점은 "설치 없이, 설정만으로 작동"한다는 것이다. 별도의 Extension이나 서버가 필요 없으며, VS Code의 기본 기능이므로 안정성이 보장된다.

그러나 `localHistory`의 한계도 명확하다. 첫째, **공식 Extension API가 없다** [^136^]. Extension이 `localHistory`의 항목을 프로그래밍적으로 열거하거나 복구할 수 없다. 사용자가 Timeline 뷰에서 수동으로 복구해야 한다. 둘째, **AI 편집과 사용자 편집을 구분하지 못한다** [^408^]. 둘 다 동일한 "파일 저장" 이벤트로 인식되므로, "AI가 한 수정만 되돌리기"는 불가능하다.

이 한계를 우회하기 위해 Zoo Code는 yocto를 병렬로 운영한다. yocto는 AI가 수정한 파일만 선택적으로 백업하고 복구할 수 있으며, `localHistory`는 모든 편집(사용자 포함)의 보편적 안전망으로 작동한다. 이 2중 구조는 "정밀한 복구는 yocto가, 보편적 복구는 localHistory가" 담당하는 역할 분담을 실현한다.

### 2.5.2 YOLO 진입/퇴장 Git 자동 커밋

Claude Code의 `git worktree`는 각 세션을 별도 디렉토리에서 실행하여 충돌을 원천 차단한다 [^76^]. Zoo Code는 worktree를 사용할 수 없지만, `git stash`를 사용하여 동등한 "의미 있는 경계"를 생성할 수 있다.

```typescript
// [튜닝] YOLO 진입/퇴장 Git 자동 커밋
// 위치: src/core/safety/YoloGitBoundary.ts

class YoloGitBoundary {
  private stashName: string | null = null;

  /**
   * YOLO 모드 진입 시 호출
   * 현재 working directory 상태를 stash에 저장
   */
  async enterYolo(): Promise<boolean> {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    this.stashName = `yolo-before-${timestamp}`;
    
    try {
      // git stash push -m "yolo-before-2026-07-01T12-00-00Z" --include-untracked
      await execAsync(`git stash push -m "${this.stashName}" --include-untracked`, {
        cwd: vscode.workspace.workspaceFolders?.[0]?.uri.fsPath
      });
      
      // [MCP] crow_manage_backup 동시 호출
      const crowBackupId = await this.createCrowBackup();
      
      // yocto 스냅샷도 동시 생성
      await yoctoManager.createSnapshot('yolo-enter', crowBackupId);
      
      vscode.window.showInformationMessage(`YOLO 모드 시작: ${this.stashName}`);
      return true;
      
    } catch (err) {
      // Git 작업 디렉토리가 아니거나 stash 실패
      // yocto만으로도 작동해야 함
      await yoctoManager.createSnapshot('yolo-enter');
      return true;  // yocto로 폴백
    }
  }

  /**
   * YOLO 모드 퇴장 시 호출
   * YOLO 결과를 Git history에 기록 (선택적)
   */
  async exitYolo(success: boolean): Promise<void> {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    
    if (success) {
      try {
        // YOLO 성공: 현재 변경사항을 커밋
        await execAsync('git add -A', { cwd: this.workspaceRoot });
        await execAsync(`git commit -m "yolo-complete-${timestamp}" --no-verify`, {
          cwd: this.workspaceRoot
        });
        
        // --no-ff 머지 전략으로 stash를 커밋에 통합 (2.5.3절)
        await this.mergeWithNoFF();
        
        vscode.window.showInformationMessage('YOLO 완료: 변경사항이 커밋되었습니다.');
        
      } catch {
        // 커밋 실패 — 변경사항이 없거나 Git 오류
        vscode.window.showInformationMessage('YOLO 완료: 커밋할 변경사항이 없습니다.');
      }
    } else {
      // YOLO 실패: 사용자에게 되돌릴지 묻기
      const choice = await vscode.window.showWarningMessage(
        'YOLO가 실패했습니다. 되돌리시겠습니까?',
        'Instant Rewind', '수동으로 처리'
      );
      
      if (choice === 'Instant Rewind') {
        await yoctoManager.instantRewind();
        if (this.stashName) {
          await execAsync(`git stash pop stash^{/${this.stashName}}`, {
            cwd: this.workspaceRoot
          }).catch(() => {});  // stash pop 실패핼 수 있음
        }
      }
    }
    
    // yocto 오래된 스냅샷 정리 (30일 이상)
    await yoctoManager.cleanupOldSnapshots(30);
  }

  /**
   * [MCP] crow_manage_backup 자동 호출
   */
  private async createCrowBackup(): Promise<string | null> {
    try {
      const result = await crowClient.call('crow_manage_backup', {
        action: 'create',
        name: this.stashName,
        auto: true
      });
      return result.backupId;
    } catch {
      return null;
    }
  }
}
```

이 Git 자동 커밋의 핵심은 **"YOLO의 실패도 기록된다"**는 것이다. Claude Code의 checkpoint는 성공적인 편집만 저장하지만 [^29^], Zoo Code의 yocto + Git stash 조합은 YOLO 시도 자체를 기록한다. 실패한 YOLO의 stash는 사용자가 나중에 `git stash list`로 확인할 수 있으며, "이런 접근은 안 됐다"는 교훈을 Crow의 `bug` 레지스터에 축적하는 데이터가 된다.

### 2.5.3 `--no-ff` squash 전략

YOLO 모드가 여러 차례의 작은 수정으로 구성될 때, Git history에 각 수정마다 별도의 커밋이 생성되면 history가 지저분해진다. `--no-ff`(no fast-forward) squash 전략은 이 문제를 해결한다.

YOLO 진입 시의 stash를 "base", YOLO 퇴장 시의 변경사항을 "head"로 두고, 이 둘 사이의 모든 변경을 하나의 squash 커밋으로 묶는다. 이 커밋의 메시지는 `yolo-complete-{timestamp}` 형태이며, Git history에서 "이 커밋은 YOLO 실험의 결과"라는 것을 명확히 식별할 수 있다. 사용자는 `git log --grep="yolo-complete"`로 모든 YOLO 실험의 결과를 한눈에 볼 수 있으며, 실패한 YOLO는 `git revert`로 쉽게 되돌릴 수 있다.

이 전략의 부가적 가치는 **"YOLO 기록의 축적"**이다. 성공한 YOLO의 커밋 메시지와 변경된 파일 목록은 `crow_ingest`를 통해 Crow의 `arch` 레지스터에 자동 저장된다. 사용자가 "저번처럼 리팩토링해줘"라고 말하면, Crow는 `arch` 레지스터에서 "저번 YOLO"의 패턴을 회상하여 유사한 접근을 제안할 수 있다.

### 2.5.4 `arch` register 저장

YOLO 세션의 아키텍처적 교훈 — "이런 방식으로 의존성을 주입했더니 잘 작동했다", "이 컴포넌트 구조는 재사용 가능하다" — 은 단기 기억(`context`)이 아니라 장기 기억(`arch`)에 저장되어야 세션 간에 유효하다.

Zoo Code Extension은 YOLO 성공 시 자동으로 `crow_ingest`를 호출하여 다음 정보를 `arch` 레지스터에 저장한다.

```typescript
// [MCP] YOLO 성공 시 arch 레지스터 자동 저장
await crowClient.call('crow_ingest', {
  content: `YOLO pattern: Refactored ${affectedFiles.join(', ')} using ${strategy}. ` +
           `Build: ${buildSuccess ? 'pass' : 'fail'}. Tests: ${testResults}.`,
  register: 'arch',
  metadata: {
    source: 'yolo-session',
    importance: 0.8,
    tags: ['yolo', 'refactoring', 'pattern'],
    project: vscode.workspace.name
  }
});
```

이 저장된 패턴은 이후 `crow_recall(domain="coding", register="arch", query="refactoring")` 호출 시 회상되며, 사용자가 다음에 유사한 작업을 요청할 때 AI가 "저번에 이렇게 했더니 잘 됐다"는 맥락을 자동으로 참조하게 된다.

### 2.5.5 바이브 점수: 현재 4/10 → 목표 9/10

| 메트릭 | 현재 (4/10) | 목표 (9/10) | 개선 전략 |
|:---|:---:|:---:|:---|
| checkpoint 자동화 | 수동 Git 커밋 | **YOLO 진입/퇴장 자동** | Git stash + yocto 연동 |
| checkpoint 세분도 | 없음 (수동만) | **턴/세션/파일 3단계** | yocto + localHistory + Git |
| Crow 패턴 축적 | 없음 | **arch 레지스터 자동 저장** | `crow_ingest` YOLO 성공 시 |
| Git history 관리 | 지저분한 커밋 | **깔끔한 squash 기록** | `--no-ff` YOLO 커밋 |
| 시각적 확인 | 없음 | **TreeView YOLO 히스토리** | Explorer 패널에 YOLO 목록 |

현재 4/10인 이유는 checkpoint가 "사용자의 몫"이기 때문이다. YOLO를 시작하기 전에 사용자가 스스로 `git stash`를 실행해야 하고, YOLO가 끝나면 스스로 커밋해야 한다. 이 "기억해야 하는 부담"이 바이브를 깬다. 목표 9/10은 checkpoint의 존재를 사용자가 의식하지 않는 상태이다. YOLO 모드 버튼을 누르는 순간 자동으로 checkpoint가 생성되고, YOLO를 종료하는 순간 자동으로 결과가 정리되는 경험이다.

---

## 2.6 조사 차원 3: YOLO Transaction & Rollback

> *"10개 파일을 동시에 수정하고 빌드가 실패했을 때, 당신의 뇌는 '뭘 건드렸더라?'를 떠올리는 대신 '되돌려'만 말하면 된다."*

이것이 YOLO Transaction & Rollback이 추구하는 경험이다. AI가 10개 파일을 수정하는 것은 하나의 논리적 작업 단위다. 이 단위의 모든 수정이 성공하면 커밋되고, 하나라도 실패하면 전체가 롤백되어야 한다. 이는 데이터베이스의 ACID 원칙 중 원자성(Atomicity)을 코드 편집에 적용하는 개념이다.

### 2.6.1 `WorkspaceEdit` 가로채기: `pending_edits[]`

VS Code Extension API에서 `WorkspaceEdit`은 파일 편집의 기본 단위이다. `workspace.applyEdit(edit)`를 호출하면 VS Code가 직접 파일을 수정한다 [^51^]. 그러나 `WorkspaceEdit`을 "가로채"서 메모리 내 트랜잭션 로그를 구현하는 것은 공식 API로는 불가능하다 [^535^]. `WorkspaceEdit`은 단순한 데이터 컨테이너이며, 적용 전에 후크를 거는 middleware가 API에 존재하지 않는다.

이 제약 속에서 Zoo Code는 **대안적 접근**을 취한다. 파일 변경 **전**이 아니라 **후**에 `FileSystemWatcher`로 감지하여 yocto 백업을 생성하고, 이 백업들을 하나의 논리적 트랜잭션으로 묶는 것이다. 이는 "선제적 차단"이 아니라 "후속적 복구"의 접근이지만, VS Code Extension API의 제약 내에서 실현 가능한 최적해이다.

```typescript
// [튜닝] YOLO Transaction & Rollback Layer
// 위치: src/core/safety/YoloTransaction.ts

interface TransactionEdit {
  id: string;
  sequence: number;              // 트랜잭션 내 순서
  fileUri: vscode.Uri;
  originalContent: string;       // yocto 백업 경로
  backupPath: string;            // yocto 백업 경로
  appliedAt: number;             // 적용 시각
  status: 'pending' | 'applied' | 'reverted' | 'failed';
}

interface YoloTransaction {
  id: string;
  sessionId: string;
  startedAt: number;
  edits: TransactionEdit[];
  status: 'active' | 'committed' | 'rolled_back' | 'failed';
  buildStatus?: 'pending' | 'success' | 'failure';
}

class YoloTransactionManager {
  private activeTransaction: YoloTransaction | null = null;
  private editCounter: number = 0;
  private yocto: YoctoSnapshotManager;
  private watcher: vscode.FileSystemWatcher;

  constructor(yocto: YoctoSnapshotManager, context: vscode.ExtensionContext) {
    this.yocto = yocto;
    
    // AI 편집 감지용 FileSystemWatcher
    this.watcher = vscode.workspace.createFileSystemWatcher(
      '**/*.{ts,tsx,js,jsx,py,go,rs,java,c,cpp,h,json,yaml,yml,md}',
      false, false, false
    );
    
    // AI가 파일을 수정한 것으로 간주되는 이벤트
    this.watcher.onDidChange(uri => this.onAiEditDetected(uri));
    this.watcher.onDidCreate(uri => this.onAiEditDetected(uri));
    
    context.subscriptions.push(this.watcher);
  }

  /**
   * 새 YOLO 트랜잭션 시작
   * YOLO 모드 진입 시 호출
   */
  startTransaction(): YoloTransaction {
    this.activeTransaction = {
      id: `tx-${Date.now()}-${Math.random().toString(36).substring(2, 8)}`,
      sessionId: this.getCurrentSessionId(),
      startedAt: Date.now(),
      edits: [],
      status: 'active'
    };
    this.editCounter = 0;
    
    // [MCP] crow_manage_backup 동시 호출
    this.yocto.createCrowBackup().then(backupId => {
      if (this.activeTransaction) {
        // crow backup ID는 별도 저장
      }
    });
    
    return this.activeTransaction;
  }

  /**
   * AI 편집 감지 시 호출 — yocto 백업을 트랜잭션의 edit으로 등록
   */
  private async onAiEditDetected(uri: vscode.Uri): Promise<void> {
    if (!this.activeTransaction || this.activeTransaction.status !== 'active') {
      return;
    }
    
    // 이미 백업된 파일인지 확인
    const existing = this.activeTransaction.edits.find(
      e => e.fileUri.fsPath === uri.fsPath
    );
    if (existing) {
      // 이미 백업된 파일 — 새로운 버전으로 업데이트
      existing.backupPath = await this.yocto.getLatestBackup(uri);
      return;
    }
    
    // 새로운 edit 등록
    this.editCounter++;
    const backup = await this.yocto.ensureBackup(uri);
    
    const edit: TransactionEdit = {
      id: `edit-${this.activeTransaction.id}-${this.editCounter}`,
      sequence: this.editCounter,
      fileUri: uri,
      originalContent: backup,
      backupPath: backup,
      appliedAt: Date.now(),
      status: 'applied'
    };
    
    this.activeTransaction.edits.push(edit);
  }

  /**
   * 트랜잭션 커밋 — 모든 edit을 확정
   * 빌드 성공 시 호출
   */
  async commitTransaction(): Promise<void> {
    if (!this.activeTransaction) return;
    
    this.activeTransaction.status = 'committed';
    this.activeTransaction.buildStatus = 'success';
    
    // [MCP] 성공 패턴을 arch 레지스터에 저장
    await this.saveSuccessPattern();
    
    // yocto 백업은 선택적으로 유지 (설정에 따라 7일 후 자동 삭제)
    this.activeTransaction = null;
  }

  /**
   * 트랜잭션 롤백 — 모든 edit을 역순으로 되돌림
   * 빌드 실패 시 또는 사용자 요청 시 호출
   */
  async rollbackTransaction(): Promise<RollbackResult> {
    if (!this.activeTransaction) {
      return { success: false, reason: 'No active transaction' };
    }
    
    const tx = this.activeTransaction;
    tx.status = 'rolled_back';
    
    // 역순으로 edit을 되돌림 (의존성 고려)
    const reversedEdits = [...tx.edits].sort((a, b) => b.sequence - a.sequence);
    const results: { edit: TransactionEdit; success: boolean }[] = [];
    
    for (const edit of reversedEdits) {
      try {
        // yocto 백업으로 복구
        fs.copyFileSync(edit.backupPath, edit.fileUri.fsPath);
        edit.status = 'reverted';
        results.push({ edit, success: true });
      } catch (err) {
        edit.status = 'failed';
        results.push({ edit, success: false });
      }
    }
    
    // [MCP] 실패 패턴을 bug 레지스터에 저장
    await this.saveFailurePattern(results);
    
    const successCount = results.filter(r => r.success).length;
    
    return {
      success: successCount === results.length,
      restoredFiles: successCount,
      totalFiles: results.length,
      durationMs: Date.now() - tx.startedAt
    };
  }

  /**
   * [MCP] bug 레지스터에 실패 패턴 저장
   */
  private async saveFailurePattern(results: any[]): Promise<void> {
    const failedFiles = results.filter(r => !r.success).map(r => r.edit.fileUri.fsPath);
    if (failedFiles.length === 0) return;
    
    try {
      await crowClient.call('crow_ingest', {
        content: `YOLO rollback failed for: ${failedFiles.join(', ')}. ` +
                 `Transaction ${this.activeTransaction?.id} had ${results.length} edits.`,
        register: 'bug',
        metadata: {
          source: 'yolo-rollback-failure',
          importance: 0.9,
          polarity: -1.5,
          tags: ['yolo', 'rollback-failure', 'bug']
        }
      });
    } catch {
      // Crow 저장 실패핼 수 있음 — 로컬 로그로 폴백
    }
  }

  /**
   * 빌드 결과 수신 — Task API 연동
   */
  onBuildResult(exitCode: number, stderr?: string): void {
    if (!this.activeTransaction) return;
    
    if (exitCode !== 0) {
      this.activeTransaction.buildStatus = 'failure';
      // 자동 롤백 또는 사용자 확인
      this.promptForRollback(stderr);
    } else {
      this.activeTransaction.buildStatus = 'success';
      // AutoBuildFix가 활성화된 경우 추가 검증 후 커밋
    }
  }
}
```

이 트랜잭션 관리자의 핵심 설계 특성은 **"수정을 가로채지 않고 수정 후를 추적"**하는 것이다. `WorkspaceEdit`을 middleware로攔截하는 것은 불가능하지만, `FileSystemWatcher`로 수정 후를 감지하는 것은 가능하다. 이 대안적 접근의 한계는 "수정이 이미 디스크에 적용된 후"라는 점이지만, yocto 백업이 충분히 빠르게(200ms 이내) 생성되면 사용자가 "되돌려"를 요청했을 때 거의 동일한 경험을 제공할 수 있다.

### 2.6.2 역순 revert: `crow_transaction` 레이어 (의사코드)

트랜잭션 롤백의 핵심은 **역순으로 revert**하는 것이다. 파일 A를 수정한 뒤 파일 B를 수정하고, 파일 A를 다시 수정한 경우, 순서대로 되돌리면 파일 A의 중간 상태로 돌아가버린다. 올바른 롤백은 "마지막 수정 → 이전 수정 → 첫 수정"의 역순이다.

`crow_transaction` 레이어는 이 역순 revert를 Crow Memory와 연동하여 더 정교하게 만든다. 각 edit은 `crow_recall`로 관련된 컨텍스트("이 파일은 auth 모듈과 관련됨")를 조회하고, revert 시 이 컨텍스트를 고려하여 의존성 순서를 재조정한다. 예를 들어 파일 A가 파일 B의 인터페이스를 import한다면, 파일 B를 먼저 revert하면 파일 A가 컴파일 에러를 낼 수 있다. `crow_transaction` 레이어는 이러한 의존성을 고려하여 "안전한 역순"을 계산한다.

```typescript
// [MCP] crow_transaction — 의존성 인식 롤백
// Crow Memory의 arch 레지스터에서 파일 간 의존성을 조회하여
// 안전한 롤백 순서를 계산

async computeSafeRollbackOrder(edits: TransactionEdit[]): Promise<TransactionEdit[]> {
  // 각 파일의 의존성 조회
  const dependencyGraph = new Map<string, string[]>();
  
  for (const edit of edits) {
    const deps = await crowClient.call('crow_recall', {
      domain: 'coding',
      register: 'arch',
      query: `dependencies of ${path.basename(edit.fileUri.fsPath)}`
    });
    dependencyGraph.set(edit.fileUri.fsPath, deps.map(d => d.content));
  }
  
  // 위상 정렬(Topological Sort)로 안전한 역순 계산
  // 의존당하는 파일을 먼저 revert, 의존하는 파일을 나중에 revert
  return topologicalSortReverse(edits, dependencyGraph);
}
```

### 2.6.3 Git vs 메모리 트랜잭션 속도/안전성

Git 기반 트랜잭션과 메모리 기반 트랜잭션의 비교는 스냅샷 비교와 유사한 구도를 가진다.

| 특성 | Git 기반 (`git stash` + `git checkout`) | 메모리 기반 (yocto `pending_edits[]`) |
|:---|:---|:---|
| **롤백 속도** | 1-3초 (git 명령어 오버헤드) | **0.3-0.8초** (fs.copyFileSync) |
| **원자성** | **원자적** (stash는 전체 또는 무효) | 비원자적 (순차 복사, 중간 실패 가능) |
| **의존성 처리** | Git이 자동 처리 (tree 객체) | 수동 위상 정렬 필요 |
| **대용량 파일** | 효율적 (delta 압축) | 비효율적 (전체 복사) |
| **VS Code 내 구현** | `child_process.exec` 필요 | **직접 `fs` 모듈** |
| **Crow 연동** | 간접 (Git 메타데이터) | 직접 (`crow_transaction`) |

Zoo Code의 전략은 **"빠른 롤백은 메모리가, 안전한 롤백은 Git이"** 담당하는 것이다. 메모리 트랜잭션이 실패하면 Git stash를 시도하고, Git도 실패하면 `localHistory`를 안내한다. 이 3중 폴백은 2.4.2절에서 설명한 yocto의 복구 전략과 동일한 철학을 공유한다.

### 2.6.4 바이브 점수: 현재 3/10 → 목표 9/10

| 메트릭 | 현재 (3/10) | 목표 (9/10) | 개선 전략 |
|:---|:---:|:---:|:---|
| 트랜잭션 자동화 | 없음 (개별 undo) | **자동 pending_edits[]** | FileSystemWatcher + yocto |
| 롤백 속도 | 수 초 (Git 수동) | **< 1초** | 메모리 기반 역순 revert |
| 빌드 연동 | 없음 | **onDidEndTaskProcess** 자동 | Task API + exitCode 감지 |
| 의존성 인식 | 없음 | **arch 레지스터 기반** | `crow_transaction` 위상 정렬 |
| 실패 패턴 축적 | 없음 | **bug 레지스터 자동 저장** | `crow_ingest` 실패 시 |

현재 3/10인 이유는 "10개 파일 수정 후 빌드 실패"가 사용자의 수동 조작을 요구하기 때문이다. 사용자는 터미널을 보고, 에러를 읽고, "되돌리기"를 결정하고, Git 명령어를 입력해야 한다. 이 4단계의 모든 지연이 바이브를 깬다. 목표 9/10은 "빌드 실패 → 자동 롤백"의 무인 파이프라인이다. 사용자는 실패를 알아차리기도 전에 이미 코드가 원위치로 돌아가 있고, 상태바에 "YOLO 롤백 완료" 메시지가 표시되는 경험이다.

---

## 2.7 조사 차원 4: Safe YOLO — Permission Gradation

> *"완벽한 YOLO는 무한한 자유가 아니라, 무한한 신뢰 위에 설 수 있는 통제된 자율성이다."*

Wave 1의 Flow Keeper가 흐름의 연속성을 지켰고, Wave 2의 앞선 조사 차원이 복구 메커니즘을 설계했다면, Safe YOLO는 "복구가 필요 없게 만드는" 예방 메커니즘에 집중한다. Permission Gradation은 이미 2.3절에서 설계했으므로, 본 절에서는 `.yoloignore`의 실제 구현과 `FileSystemWatcher` 기반 수정 차단, 그리고 `life_avoid` 레지스터 연동을 심층적으로 다룬다.

### 2.7.1 `.yoloignore` + 파일 체크 로직

`.yoloignore`는 프로젝트 루트에 위치하는 텍스트 파일로, `.gitignore`와 동일한 glob 문법을 사용한다. 차이점은 `.gitignore`가 Git의 추적 대상을 제어하는 것이고, `.yoloignore`가 AI의 접근 대상을 제어한다는 것이다.

```yaml
# .yoloignore — AI가 자동으로 수정/접근해서는 안 되는 파일들
# [튜닝] Zoo Code Extension이 자동으로 체크

# 환경 변수 (모든 수준에서 Deny)
**/.env
**/.env.*
!.env.example

# 인증/보안
**/*.pem
**/*.key
**/secrets/**
**/.ssh/
**/.aws/

# 인프라 상태
**/terraform.tfstate
**/terraform.tfstate.*
**/.terraform/

# 민감한 설정
**/package-lock.json       # AI가 수정하면 안 됨 (npm이 관리)
**/yarn.lock
**/pnpm-lock.yaml

# 빌드 산출물 (수정 의미 없음)
**/dist/
**/build/
**/coverage/

# Zoo Code 자체 메타데이터
**/.zoo-code/
**/.zoo/

# 사용자가 추가한 커스텀 패턴
# 이 아래에 사용자가 직접 추가한 패턴들은
# Crow Memory의 life_avoid 레지스터와 자동 동기화됨
```

이 파일의 핵심 설계 원칙은 **"패턴의 계층성"**이다. 상단은 모든 프로젝트에서 공통으로 적용되는 보호 패턴(`.env`, `.pem` 등)이고, 하단은 사용자가 특정 프로젝트에서 추가한 커스텀 패턴이다. Zoo Code Extension은 프로젝트 루트의 `.yoloignore`뿐 아니라, 사용자 홈 디렉토리의 `~/.yoloignore`도 계층적으로 적용한다. 이는 "사용자가 한 번 '이 파일은 절대'라고 하면 모든 프로젝트에서 보호"되는 경험을 제공한다.

파일 체크 로직은 PermissionGradationEngine(2.3.3절)의 `isYoloIgnored()` 메서드에 구현된다. `minimatch` 라이브러리를 사용하여 glob 패턴을 컴파일하고, AI가 접근하려는 모든 파일 경로를 이 패턴과 매칭한다. 매칭되는 경우 `decision: 'deny'`가 반환되며, AI는 그 파일에 접근할 수 없다.

### 2.7.2 `createFileSystemWatcher` 수정 차단

`FileSystemWatcher`는 파일 변경 **후**의 이벤트를 감지하므로, 사전 차단이 아니라 사후 롤백 방식이다 [^51^]. 즉, AI가 이미 파일을 수정한 뒤에야 "이 파일은 .yoloignore에 의해 보호됩니다"라는 알림을 표시할 수 있다.

이 한계를 완화하기 위해 Zoo Code는 **2단계 방어**를 구성한다.

**1단계 — 사전 차단(PermissionGradationEngine)**: AI가 파일 접근을 "시도하기 전"에 `.zoo/permissions.json`과 `.yoloignore`를 확인한다. 이는 Zoo Code Extension의 파일 쓰기/읽기 인터셉터에서 수행되며, AI의 도구 호출 인자를 검사하여 보호된 경로가 포함되어 있으면 호출 자체를 차단한다.

**2단계 — 사후 감지(FileSystemWatcher)**: 1단계가 실패한 경우(예: AI가 직접 `fs.writeFileSync`를 호출하거나, VS Code의 기본 파일 API를 우회한 경우), `FileSystemWatcher`의 `onDidChange` 이벤트가 발화하여 yocto 백업을 생성하고 사용자에게 알림을 표시한다.

```typescript
// [튜닝] 2단계 보호 — 사전 차단 + 사후 감지
class SafeYoloGuard {
  private watcher: vscode.FileSystemWatcher;
  private permissionEngine: PermissionGradationEngine;

  constructor(context: vscode.ExtensionContext) {
    this.permissionEngine = new PermissionGradationEngine(context);
    
    // 2단계: 사후 감지용 FileSystemWatcher
    this.watcher = vscode.workspace.createFileSystemWatcher('**/*', false, false, false);
    
    this.watcher.onDidChange(async uri => {
      // 이 파일이 .yoloignore에 의해 보호되는가?
      if (this.permissionEngine.isYoloIgnored(uri.fsPath)) {
        // 보호된 파일이 수정됨 — yocto로 즉시 복구
        const backup = await yocto.getLatestBackup(uri);
        if (backup) {
          fs.copyFileSync(backup, uri.fsPath);
          vscode.window.showWarningMessage(
            `보호된 파일 ${path.basename(uri.fsPath)}의 수정이 자동으로 차단되었습니다.`
          );
        }
      }
    });
    
    context.subscriptions.push(this.watcher);
  }

  /**
   * 1단계: 사전 차단 — AI의 도구 호출 전 검사
   */
  async preCheck(action: ActionType, target: string): Promise<PermissionDecision> {
    return this.permissionEngine.evaluate(action, target, 'main-agent');
  }
}
```

이 2단계 방어의 핵심은 **"1단계가 실패핼 수 있지만 2단계가 있고, 2단계도 실패핼 수 있지만 yocto가 있다"**는 중복 설계이다. 어떤 단일 메커니즘도 100% 완벽하지 않지만, 여러 메커니즘이 중복될 때 시스템 전체의 신뢰도는 극적으로 상승한다.

### 2.7.3 `life_avoid` register 연동

`.yoloignore`의 정적 패턴은 사용자가 수동으로 편집해야 한다. 하지만 "수동 편집" 자체가 바이브를 깨는 지점이다. Crow Memory의 `life_avoid` 레지스터는 이 문제를 해결한다.

`life_avoid`는 사용자가 명시적으로 회피를 요청한 패턴을 저장하는 레지스터이다. `polarity = -2.0`은 "명시적 부정 강화"로, 이 패턴의 감쇠가 가속되어 빠르게 다른 메모리에 비해 우선순위가 높아진다 [^386^]. Zoo Code Extension은 다음 시나리오에서 `life_avoid`와 `.yoloignore`를 동기화한다.

**시나리오**: 사용자가 AI에게 "`.env` 파일은 절대 건드리지 마"라고 말한다.

1. AI는 이 지시를 `crow_ingest`로 `life_avoid` 레지스터에 저장한다 (`polarity = -2.0`).
2. Zoo Code Extension의 `syncWithLifeAvoid()`가 주기적으로 실행되어 `life_avoid`를 조회한다.
3. 새로운 패턴 `**/.env`가 발견되면, `.yoloignore`에 자동으로 추가된다.
4. 동시에 PermissionGradationEngine의 `denylist`에도 추가되어, Lv.3 Scoped 이상의 모드에서도 차단된다.
5. 다음 세션부터는 사용자가 아무것도 말하지 않아도 `.env`는 보호된다.

이 동기화는 **단방향**이다. `.yoloignore`의 변경이 `life_avoid`에 반영되지는 않는다. 이는 "수동 설정보다 사용자의 말이 우선"이라는 설계 원칙을 반영한다. 사용자가 "이 파일은 건들지 마"라고 말한 것은 수동으로 `.yoloignore`에 추가한 것보다 더 강력한 신호이다.

### 2.7.4 바이브 점수: 현재 3/10 → 목표 9/10

| 메트릭 | 현재 (3/10) | 목표 (9/10) | 개선 전략 |
|:---|:---:|:---:|:---|
| 파일 보호 | 없음 (전체 Allow) | **.yoloignore 계층적 적용** | glob 패턴 기반 차단 |
| 회피 패턴 축적 | 없음 (수동 기억) | **life_avoid 자동 동기화** | `crow_ingest` + 주기적 동기화 |
| 사전 차단 | 없음 | **PermissionGradation 사전 검사** | 도구 호출 인자 인터셉트 |
| 사후 감지 | 없음 | **FileSystemWatcher 자동 복구** | yocto 백업 즉시 복원 |
| 시각적 확인 | 없음 | **보호 파일 트리 하이라이트** | Explorer에서 .yoloignore 매칭 파일 표시 |

현재 3/10인 이유는 Zoo Code의 YOLO 모드가 "모든 것을 허용"하는 블랙박스이기 때문이다. 사용자는 AI가 무엇을 건드릴지 알 수 없으며, "혹시 `.env`를 건드리진 않을까?"하는 불안 속에서 YOLO를 사용한다. 이 불안이 바이브를 깬다. 목표 9/10은 "보호된 파일 목록이 눈에 보이고, AI가 절대 그 파일들을 건드리지 않는다는 신뢰가 자동으로 형성되는" 상태이다.

---

## 2.8 조사 차원 5: 에러 후 자동 복구

> *"빌드 실패는 문제가 아니다. 빌드 실패 후 사용자가 '고쳐줘'를 입력해야 하는 순간이 문제다."*

앞선 4개 조사 차원이 "에러를 예방하고 에러를 복구"하는 메커니즘을 설계했다면, 본 조사 차원은 "에러가 이미 발생한 후의 자동화"에 집중한다. 빌드 실패는 불가피하다. 중요한 것은 빌드 실패 후의 복구가 얼마나 자동화되어 있는가이다.

### 2.8.1 AutoBuildFix: 빌드 실패 → stderr → LLM → 수정 → 재빌드

AutoBuildFix는 VS Code Extension이 빌드 프로세스를 감시하며, 실패 시 자동으로 LLM 컨텍스트에 에러 정보를 주입하고 수정을 요청하는 폐쇄 루프(closed loop)이다.

```typescript
// [튜닝] AutoBuildFix — 빌드 실패 후 자동 복구 루프
// 위치: src/core/safety/AutoBuildFix.ts

interface AutoBuildFixConfig {
  maxAttempts: number;           // 최대 재시도 횟수 (기본: 3)
  enableOscillationDetection: boolean;  // oscillation 감지 활성화
  oscillationWindowSize: number; // oscillation 감지 윈도우 (기본: 4)
  buildCommand: string;          // 빌드 명령어 (자동 감지 또는 수동 설정)
  autoApplyFixes: boolean;       // 수정을 자동 적용할지
  delayBetweenAttempts: number;  // 재시도 간 지연 (ms, 기본: 1000)
}

interface BuildAttempt {
  attemptNumber: number;
  exitCode: number;
  stderr: string;
  stdout: string;
  fixApplied?: string;           // LLM이 제안한 수정 요약
  timestamp: number;
}

class AutoBuildFix {
  private config: AutoBuildFixConfig;
  private attempts: BuildAttempt[] = [];
  private isRunning: boolean = false;
  private yoloTx: YoloTransactionManager;

  constructor(
    config: Partial<AutoBuildFixConfig>,
    yoloTx: YoloTransactionManager
  ) {
    this.config = {
      maxAttempts: 3,
      enableOscillationDetection: true,
      oscillationWindowSize: 4,
      buildCommand: 'npm run build',
      autoApplyFixes: true,
      delayBetweenAttempts: 1000,
      ...config
    };
    this.yoloTx = yoloTx;
  }

  /**
   * 빌드 실패 이벤트 수신 — Task API 연동
   * vscode.tasks.onDidEndTaskProcess에서 호출
   */
  async onBuildFailure(exitCode: number, stderr: string, stdout: string): Promise<void> {
    if (this.isRunning) return;  // 이미 AutoBuildFix 실행 중
    if (this.attempts.length >= this.config.maxAttempts) {
      vscode.window.showErrorMessage(
        `빌드가 ${this.config.maxAttempts}회 실패했습니다. 수동 수정이 필요합니다.`
      );
      return;
    }

    this.isRunning = true;
    
    try {
      // 현재 시도 기록
      const attempt: BuildAttempt = {
        attemptNumber: this.attempts.length + 1,
        exitCode,
        stderr,
        stdout,
        timestamp: Date.now()
      };
      this.attempts.push(attempt);

      // oscillation 감지
      if (this.config.enableOscillationDetection && this.isOscillating()) {
        vscode.window.showWarningMessage(
          'AutoBuildFix: A→B→A 패턴 감지. 무한 루프를 방지하기 위해 중단합니다.'
        );
        // [MCP] oscillation 패턴을 bug 레지스터에 저장
        await this.saveOscillationPattern();
        this.isRunning = false;
        return;
      }

      // stderr를 problemMatcher로 정제
      const parsedErrors = this.parseErrors(stderr);
      
      // LLM에 수정 요청
      const fix = await this.requestFixFromLLM(parsedErrors);
      attempt.fixApplied = fix.summary;
      
      if (this.config.autoApplyFixes && fix.edits.length > 0) {
        // 수정을 WorkspaceEdit으로 적용
        const workspaceEdit = new vscode.WorkspaceEdit();
        for (const edit of fix.edits) {
          const uri = vscode.Uri.file(edit.filePath);
          const doc = await vscode.workspace.openTextDocument(uri);
          const range = new vscode.Range(
            doc.positionAt(edit.startOffset),
            doc.positionAt(edit.endOffset)
          );
          workspaceEdit.replace(uri, range, edit.newText);
        }
        await vscode.workspace.applyEdit(workspaceEdit);
        
        // 수정 후 저장
        for (const edit of fix.edits) {
          const doc = await vscode.workspace.openTextDocument(edit.filePath);
          await doc.save();
        }
      }

      // 재빌드
      await new Promise(r => setTimeout(r, this.config.delayBetweenAttempts));
      const buildResult = await this.runBuild();
      
      if (buildResult.exitCode === 0) {
        // 빌드 성공!
        vscode.window.showInformationMessage(
          `AutoBuildFix 성공: ${attempt.attemptNumber}번째 시도에서 복구되었습니다.`
        );
        // [MCP] 성공 패턴을 arch 레지스터에 저장
        await this.saveSuccessPattern(attempt);
        // YOLO 트랜잭션 커밋
        await this.yoloTx.commitTransaction();
      } else {
        // 빌드 여전히 실패 — 재귀 호출 (maxAttempts까지)
        this.isRunning = false;
        await this.onBuildFailure(buildResult.exitCode, buildResult.stderr, buildResult.stdout);
      }
      
    } catch (err) {
      vscode.window.showErrorMessage(`AutoBuildFix 오류: ${err}`);
      this.isRunning = false;
    }
  }

  /**
   * oscillation 감지: A→B→A 패턴 식별
   * 최근 N개의 수정이 서로 되돌리는 관계이면 oscillation으로 판단
   */
  private isOscillating(): boolean {
    const window = this.config.oscillationWindowSize;
    if (this.attempts.length < window) return false;
    
    const recent = this.attempts.slice(-window);
    const fixes = recent.map(a => a.fixApplied).filter(Boolean);
    
    // 동일한 수정이 반복되는지 확인
    const uniqueFixes = new Set(fixes);
    if (uniqueFixes.size < fixes.length / 2) {
      return true;  // 과반수가 중복 — oscillation 의심
    }
    
    // A→B→A 패턴: 짝수 번째 수정이 홀수 번째 수정을 되돌림
    for (let i = 2; i < fixes.length; i++) {
      if (fixes[i] === fixes[i - 2]) return true;
    }
    
    return false;
  }

  /**
   * stderr를 정제된 에러 메시지로 파싱
   * VS Code problemMatcher와 유사한 로직 [^42^]
   */
  private parseErrors(stderr: string): ParsedError[] {
    const errors: ParsedError[] = [];
    const lines = stderr.split('\n');
    
    // TypeScript / JavaScript 에러 패턴
    const tsErrorPattern = /^(.*)\((\d+),(\d+)\):\s+(error|warning)\s+(TS\d+):\s+(.*)$/;
    // ESLint 에러 패턴
    const eslintPattern = /^(.*):\s+(error|warning)\s+(.*)\s+(.*)$/;
    // Python 에러 패턴
    const pythonPattern = /^\s+File\s+"(.*)",\s+line\s+(\d+),\s+in\s+(.*)$/;
    
    for (const line of lines) {
      let match;
      if ((match = line.match(tsErrorPattern))) {
        errors.push({ file: match[1], line: parseInt(match[2]), message: match[6], code: match[5] });
      } else if ((match = line.match(eslintPattern))) {
        errors.push({ file: match[1], line: 0, message: match[3], code: match[4] });
      } else if ((match = line.match(pythonPattern))) {
        errors.push({ file: match[1], line: parseInt(match[2]), message: match[3], code: '' });
      }
    }
    
    return errors;
  }

  /**
   * LLM에게 수정 요청
   */
  private async requestFixFromLLM(errors: ParsedError[]): Promise<LLMFix> {
    const errorContext = errors.map(e => 
      `File: ${e.file}:${e.line}\nError: ${e.message} (${e.code})`
    ).join('\n\n');

    // [MCP] crow_recall로 관련 컨텍스트 조회
    const relatedMemories = await crowClient.call('crow_recall', {
      domain: 'coding',
      register: 'bug',
      query: errors.map(e => e.message).join(' ')
    });

    const prompt = `
Build failed with the following errors:
${errorContext}

Related past fixes from memory:
${relatedMemories.map(m => `- ${m.content}`).join('\n')}

Fix the errors and return the specific file edits needed.
Format: FILE_PATH|START_LINE|END_LINE|NEW_CODE
`;

    // Zoo Code Extension의 LLM 호출 인터페이스 사용
    const response = await llmClient.complete(prompt);
    return this.parseFixResponse(response);
  }

  /**
   * [MCP] 성공 패턴을 arch 레지스터에 저장
   */
  private async saveSuccessPattern(attempt: BuildAttempt): Promise<void> {
    try {
      await crowClient.call('crow_ingest', {
        content: `Build fix: ${attempt.fixApplied}. ` +
                 `Errors: ${this.parseErrors(attempt.stderr).map(e => e.code).join(', ')}.`,
        register: 'arch',
        metadata: {
          source: 'autobuildfix-success',
          importance: 0.85,
          tags: ['build-fix', 'pattern']
        }
      });
    } catch {
      // Crow 저장 실패핼 수 있음
    }
  }
}
```

AutoBuildFix의 핵심 설계 특성은 **문제 해결의 폐쇄 루프**이다. 사용자의 개입 없이 "빌드 실패 → 에러 파싱 → LLM 수정 → 재빌드"가 자동으로 반복된다. 이 루프가 성공하면 사용자는 빌드 실패를 "알아차리기도 전에" 이미 코드가 고쳐진 상태를 보게 된다. 이것이 바로 "사용자가 기능의 존재를 의식하지 않는" 9점 이상의 바이브 경험이다.

### 2.8.2 `max_attempts=3` + oscillation 감지(A→B→A)

무한 루프 방지는 AutoBuildFix의 안전성을 결정하는 핵심 요소이다. `max_attempts = 3`은 경험적으로 결정된 값이다. 1-2번의 시도로는 복잡한 에러(의존성 순환, 타입 불일치 등)를 해결하기 어렵고, 4번 이상의 시도는 oscillation 가능성이 급격히 증가한다.

oscillation 감지는 더 정교한 메커니즘이다. LLM이 "파일 A의 X를 Y로 바꿔라"를 제안하고, 다음 시도에서 "파일 A의 Y를 X로 바꿔라"를 제안하면, 이는 A→B→A의 무의미한 반복이다. 이 패턴을 감지하기 위해 AutoBuildFix는 최근 N개의 수정 요약을 비교하여, 과반수 이상이 중복되거나, 짝수 번째 수정이 홀수 번째 수정을 되돌리는 패턴을 식별한다. oscillation이 감지되면 루프는 즉시 중단되고, 사용자에게 "무한 루프가 감지되었습니다"라는 메시지를 표시한다.

### 2.8.3 `bug` register 축적 → 예방적 YOLO

AutoBuildFix의 가장 진볏된 특성은 **"실패에서 학습"**하는 것이다. 각 빌드 실패와 그 수정은 `crow_ingest`로 Crow의 `bug` 레지스터에 저장된다. 이 저장은 단순한 로깅이 아니라, **의미 있는 패턴 축적**이다.

예를 들어 프로젝트에서 `npm run build`가 다음과 같은 순환 패턴으로 실패한다고 가정한다.

1. `TypeScript error TS2345: Argument of type 'string' is not assignable to parameter of type 'number'`
2. AI가 `parseInt()`로 수정
3. 다음 빌드에서 `TS2345: Argument of type 'number' is not assignable to parameter of type 'string'`
4. AI가 `String()`으로 수정
5. 다시 1로 돌아감

이 oscillation 패턴이 `bug` 레지스터에 축적되면, 다음번에 AI가 유사한 TS2345 에러를 만났을 때 `crow_recall`로 이 패턴을 회상하게 된다. AI는 "이전에 이런 순환이 있었으므로, `parseInt`나 `String`이 아닌 제네릭 타입 수정을 시도해야 한다"는 맥락을 자동으로 참조한다. 이것이 "예방적 YOLO" — 빌드 실패 후의 수정이 아니라, 빌드 실패 전에 해당 패턴을 회피하는 것 — 으로 진화하는 경로이다.

### 2.8.4 바이브 점수: 현재 4/10 → 목표 9/10

| 메트릭 | 현재 (4/10) | 목표 (9/10) | 개선 전략 |
|:---|:---:|:---:|:---|
| 빌드 실패 감지 | 수동 터미널 확인 | **Task API 자동 감지** | `onDidEndTaskProcess` |
| 에러 → LLM 전달 | 수동 복사/붙여넣기 | **자동 stderr 주입** | problemMatcher 파싱 |
| 수정 자동 적용 | 없음 (수동 승인) | **WorkspaceEdit 자동 적용** | `autoApplyFixes` 설정 |
| 무한 루프 방지 | 없음 | **max_attempts + oscillation 감지** | A→B→A 패턴 식별 |
| 패턴 축적 | 없음 | **bug 레지스터 자동 저장** | `crow_ingest` 실패/성공 시 |

현재 4/10인 이유는 빌드 실패가 사용자에게 "일"이기 때문이다. 에러를 읽고, 이해하고, AI에게 설명하고, 수정을 기다리고, 다시 빌드하는 모든 과정이 사용자의 뇌를 점유한다. 목표 9/10은 "빌드 실패를 사용자가 알아차리기도 전에 이미 고쳐진 상태"이다. 상태바에 "AutoBuildFix: 2번째 시도에서 복구됨"이라는 메시지가 잠깐 표시되고, 사용자는 그것을 볼 수도 있고 안 볼 수도 있다. 중요한 것은 사용자가 "코드를 고쳐야겠다"는 생각을 할 필요가 없다는 것이다.

---

## 2.9 Wave 2 사용자 경험 스토리

### 스토리 1: "YOLO 모드로 10개 파일 수정. 빌드 실패. 1초 만에 되돌아갔다."

민수는 새로운 인증 모듈을 추가하고 있었다. 기존 코드베이스가 50개 파일이 넘는 대형 프로젝트였지만, 그는 YOLO 모드 버튼을 눌렀다. 그 순간 Zoo Code Extension은 눈에 보이지 않는 속도로 세 가지 일을 했다: `git stash push`로 현재 상태를 보존하고, `crow_manage_backup create`로 Crow 메모리를 스냅샷하고, `FileSystemWatcher`를 활성화하여 모든 파일 변경을 감시하기 시작했다. 상태바에 "YOLO: ON"이라는 작은 녹색 인디케이터가 켜졌다.

"JWT 인증을 전체에 적용해줘." 민수가 말했다. AI는 즉시 작업을 시작했다. `auth.ts`를 수정하고, `middleware.ts`를 생성하고, `routes.ts`의 15개 엔드포인트에 인증 가드를 추가했다. yocto는 각 파일 수정 직전에 자동으로 백업을 생성했지만, 민수는 그것을 알지 못했다. 그는 그저 코드가 흘러가는 것을 지켜봤다.

10개 파일의 수정이 끝났을 때, Zoo Code Extension은 자동으로 `npm run build`를 실행했다. 터미널이 잠깐 보였다가 사라졌다.(`presentation.reveal: silent` [^135^]) 몇 초 후, exit code 1. 빌드 실패. `TypeScript error TS2345` — `auth.ts`의 `verifyToken` 함수가 `string`을 받아야 하는데 `number`를 받고 있었다.

민수는 아무것도 하지 않았다. 0.5초 후, Zoo Code Extension의 AutoBuildFix가 활성화되었다. stderr를 파싱하여 에러 메시지를 추출하고, LLM 컨텍스트에 주입하고, 수정을 요청했다. LLM은 `verifyToken`의 파라미터 타입을 `string | number`로 변경하는 수정을 제안했다. AutoBuildFix는 그 수정을 자동으로 적용하고 다시 빌드를 실행했다.

exit code 1. 여전히 실패. 이번에는 다른 파일에서 다른 에러. AutoBuildFix는 두 번째 시도를 시작했다. 민수는 그 사이에 다른 파일을 열어서 읽고 있었다. AI가 코드를 고치는 동안 그는 자신의 일을 했다.

두 번째 시도도 실패했다. `max_attempts = 3`의 제한이 1회 남았다. AutoBuildFix는 세 번째 시도를 시작하기 전에 `YoloTransactionManager`의 `rollbackTransaction()`을 호출했다. 0.3초 만에 10개 파일이 모두 원위치로 돌아갔다. VS Code의 에디터 탭들이 깜빡이며 새로고침되었다. 상태바에 "YOLO Rewind 완료: 10/10 파일 복구 (320ms)"라는 메시지가 표시되었다.

민수는 Ctrl+Shift+P를 눌러 "Zoo: YOLO History"를 열었다. Explorer 사이드바에 "YOLO Sessions" 트리가 나타났고, "YOLO-before-2026-07-01T12-00-00Z"라는 항목 아래에 10개 파일의 백업 목록이 보였다. 그는 "다른 접근법으로 시도해줘"라고 말했다. AI는 이전 실패의 패턴을 `bug` 레지스터에서 참조하여, 이번에는 더 안전한 접근법을 제안했다.

민수는 "망했다"는 생각을 한 번도 하지 않았다. 그는 흐름을 잃지 않았다. 그것이 Fearless YOLO이다.

### 스토리 2: "`.env`는 절대 건드리지 마 — 한 번 말하면 영원히 기억되는 보호"

지영은 팀의 DevOps 엔지니어였다. 그녀는 Zoo Code에게 "Docker Compose 설정을 자동화해줘"라고 요청했다. AI는 `docker-compose.yml`을 생성하고, `Dockerfile`을 수정하고, `.env` 파일을 읽어 환경 변수를 참조하기 시작했다.

"잠깐, `.env`는 절대 건드리지 마." 지영이 말했다. 그녀의 목소리에는 경고가 담겨 있었다. 그 순간 Zoo Code Extension은 두 가지 일을 했다. 첫째, AI의 현재 작업을 즉시 중단하고 `.env`에 대한 모든 접근을 차단했다. 둘째, 그녀의 지시를 `crow_ingest`로 `life_avoid` 레지스터에 저장했다. `polarity = -2.0`, `content = "**/.env"`.

AI는 "알겠습니다. `.env` 파일은 읽기만 하고 수정하지 않겠습니다"라고 응답했다. 대신 `env.example` 파일을 기반으로 환경 변수 템플릿을 생성했다. 지영은 만족했다.

그날 밤, 지영은 VS Code를 껐다. 다음 날 아침, 다른 프로젝트를 열고 Zoo Code를 활성화했다. "데이터베이스 마이그레이션 스크립트를 작성해줘"라고 요청했다. AI는 `migrations/` 폴터를 생성하고 스크립트를 작성하기 시작했다. 작업 중 `.env` 파일의 데이터베이스 연결 문자열이 필요했지만, AI는 `life_avoid` 레지스터를 자동으로 조회하여 `.env`가 보호된 파일임을 인식했다.

"`.env` 파일은 접근할 수 없습니다. 대신 `DATABASE_URL` 환경 변수를 수동으로 입력해주세요." AI가 안내했다. 지영은 데이터베이스 연결 문자열을 입력했다. AI는 그 값을 `env.example`에 템플릿으로 추가하고, 마이그레이션 스크립트에서 `process.env.DATABASE_URL`을 참조하도록 작성했다.

한 달 후, 팀의 신입 개발자가 Zoo Code에게 "모든 환경 변수를 `.env`에 정리해줘"라고 요청했다. AI는 즉시 거부했다. "`.env` 파일은 보호되어 있습니다. `env.example`을 사용하거나, 지영 님에게 확인해주세요." 신입 개발자는 당황했지만, `.env` 파일이 수정되지는 않았다.

지영은 "`.env`를 보호해줘"를 한 번만 말했다. 그 한 마디가 모든 프로젝트, 모든 세션, 모든 팀원에게 영구적으로 적용되었다. 이것이 `life_avoid` 레지스터와 `.yoloignore`의 자동 동기화가 만들어내는 신뢰다.

---

## 2.10 Wave 2 기술적 구현 체크리스트 (20+ 항목)

Wave 2의 모든 구현 항목은 VS Code Extension API 내에서 가능하며, 각 항목은 [튜닝](Zoo Code Extension 소스 코드 직접 수정) 또는 [MCP](Crow Memory 도구 호출)로 태깅된다.

### Layer 1: Prevention (사전 방지)

- [ ] [튜닝] **PG-01**: `PermissionGradationEngine` 클래스 구현 (`src/core/safety/PermissionGradation.ts`)
- [ ] [튜닝] **PG-02**: `.zoo/permissions.json` 설정 파일 파싱 및 런타임 로드
- [ ] [튜닝] **PG-03**: 5개 행위 × 5개 수준 매트릭스의 평가 로직 구현 (`deny > ask > allow`)
- [ ] [튜닝] **PG-04**: `Scoped` 수준의 allowlist/denylist glob 패턴 매칭 (`minimatch`)
- [ ] [튜닝] **PG-05**: Protected Paths 검사 (`.git/`, `.vscode/`, `.env` 등 항상 Ask 이상)
- [ ] [튜닝] **YI-01**: `.yoloignore` 파일 파서 구현 (`.gitignore` 호환 glob 문법)
- [ ] [튜닝] **YI-02**: 프로젝트 루트 + 사용자 홈(`~/.yoloignore`) 계층적 적용
- [ ] [튜닝] **YI-03**: `.yoloignore` 패턴을 `PermissionGradationEngine`에 통합 (최우선 계층)
- [ ] [튜닝] **YI-04**: Explorer 트리에서 `.yoloignore` 매칭 파일 시각적 하이라이트
- [ ] [MCP] **LA-01**: `life_avoid` 레지스터 주기적 조회 (YOLO 진입 시)
- [ ] [MCP] **LA-02**: `life_avoid` 패턴 → `.yoloignore` 자동 동기화 (`syncWithLifeAvoid`)
- [ ] [MCP] **LA-03**: `polarity = -2.0` 항목의 자동 denylist 추가

### Layer 2: Real-time Protection (실시간 보호)

- [ ] [튜닝] **YO-01**: `YoctoSnapshotManager` 클래스 구현 (`src/core/safety/YoctoSnapshot.ts`)
- [ ] [튜닝] **YO-02**: `FileSystemWatcher` 기반 파일 변경 감지 및 자동 백업
- [ ] [튜닝] **YO-03**: 200ms 디바운싱으로 이벤트 폭주 방지
- [ ] [튜닝] **YO-04**: `fs.copyFileSync` 즉시 백업 (`~/.zoo-code/yocto/{sessionId}/`)
- [ ] [튜닝] **YO-05**: `instantRewind()` — 역순 파일 복구 + VS Code 문서 새로고침
- [ ] [튜닝] **YO-06**: 명령 팔레트 "Zoo: Instant Rewind" + 단축키(`Ctrl+Shift+Z`) 등록
- [ ] [튜닝] **TX-01**: `YoloTransactionManager` 클래스 구현 (`src/core/safety/YoloTransaction.ts`)
- [ ] [튜닝] **TX-02**: `pending_edits[]` 메모리 트랜잭션 로그 관리
- [ ] [튜닝] **TX-03**: 빌드 실패 시(`exitCode !== 0`) 자동 `rollbackTransaction()` 호출
- [ ] [튜닝] **TX-04**: 역순 revert + 의존성 위상 정렬 (arch 레지스터 기반)
- [ ] [MCP] **CB-01**: YOLO 진입 시 `crow_manage_backup create` 자동 호출
- [ ] [MCP] **CB-02**: YOLO 퇴장 시 `crow_manage_backup` 선택적 정리

### Layer 3: Post-hoc Recovery (사후 복구)

- [ ] [튜닝] **GH-01**: YOLO 진입/퇴장 Git 자동 stash (`git stash push --include-untracked`)
- [ ] [튜닝] **GH-02**: `--no-ff` squash 전략으로 YOLO 커밋 생성
- [ ] [튜닝] **GH-03**: Explorer TreeView에 "YOLO Sessions" 히스토리 패널 추가
- [ ] [튜닝] **LH-01**: `localHistory` 설정 자동 확인 및 안전값 조정
- [ ] [튜닝] **AB-01**: `AutoBuildFix` 클래스 구현 (`src/core/safety/AutoBuildFix.ts`)
- [ ] [튜닝] **AB-02**: `onDidEndTaskProcess` 이벤트 구독 및 빌드 실패 자동 감지
- [ ] [튜닝] **AB-03**: `problemMatcher` 스타일 stderr 파싱 (TypeScript/ESLint/Python)
- [ ] [튜닝] **AB-04**: LLM 자동 수정 요청 + `WorkspaceEdit` 자동 적용
- [ ] [튜닝] **AB-05**: `max_attempts = 3` 제한 + oscillation 감지(A→B→A)
- [ ] [튜닝] **AB-06**: oscillation 감지 시 자동 중단 + 사용자 알림
- [ ] [MCP] **BG-01**: 빌드 실패 패턴 자동 `crow_ingest` → `bug` 레지스터
- [ ] [MCP] **BG-02**: 빌드 성공 패턴 자동 `crow_ingest` → `arch` 레지스터
- [ ] [MCP] **BG-03**: AutoBuildFix oscillation 패턴 → `bug` 레지스터 (예방적 학습)

### Integration & UI

- [ ] [튜닝] **UI-01**: 상태바 "YOLO: ON/OFF" 인디케이터
- [ ] [튜닝] **UI-02**: YOLO Rewind 결과 토스트 메시지 (복구 파일 수, 소요 시간)
- [ ] [튜닝] **UI-03**: `SafeYoloGuard` 사후 감지 알림 (보호 파일 수정 시 자동 복구 알림)
- [ ] [튜닝] **UI-04**: Permission 요청 대화상자 (Ask 수준에서의 승인/거부 UI)

### Wave 2 바이브 점수 종합

| 조사 차원 | 현재 | 목표 | 핵심 개선 전략 | Crow 연동 |
|:---|:---:|:---:|:---|:---|
| **D1: Instant Rewind** | 3/10 | 9/10 | yocto `fs.copyFileSync` 백업 | `crow_manage_backup` |
| **D2: Checkpoint Granularity** | 4/10 | 9/10 | Git stash + localHistory + yocto 3중 | `arch` 레지스터 저장 |
| **D3: YOLO Transaction** | 3/10 | 9/10 | `pending_edits[]` 메모리 트랜잭션 | `crow_transaction` |
| **D4: Safe YOLO** | 3/10 | 9/10 | `.yoloignore` + Permission 5×5 | `life_avoid` 동기화 |
| **D5: Auto-Recovery** | 4/10 | 9/10 | AutoBuildFix 폐쇄 루프 | `bug` 레지스터 축적 |
| **Wave 2 평균** | **3.4/10** | **9.0/10** | **3계층 중복 안전망** | **5개 레지스터 연동** |

이 체크리스트는 총 **40개 항목**으로, 그중 [튜닝] 28개, [MCP] 12개이다. 예상 소요 기간은 6주(Week 6-12)이며, 각 항목의 구현 난이도는 VS Code Extension API의 공식 문서와 검증된 커뮤니티 패턴을 기반으로 하므로 기술적 위험도는 중간 이하로 평가된다. 유일한 외부 의존성은 Crow SSE 서버(9020 포트)의 가용성이며, Crow 서버가 응답하지 않을 경우 모든 [MCP] 태그 항목은 gracefully degrade되어 [튜닝]만으로도 핵심 기능이 작동하도록 설계되었다.

Wave 2가 완성되면 Zoo Code 사용자는 "과감함"과 "안전성"의 경계에서 더 이상 갈등하지 않는다. YOLO 모드 버튼은 "위험한 실험"이 아니라 "회복 가능한 탐험"의 시작점이 된다. 사용자가 버튼을 누르는 순간, 그의 뇌는 "망하면 어떡하지?"가 아니라 "어디까지 바꿔볼까?"를 생각한다. 이 마음가짐의 전환이 Fearless YOLO의 진정한 의미이며, 이것이 Wave 2가 사용자에게 선물하는 바이브코딩의 帛이다.


---

# 3. Wave 3: Zero-Explanation — Context Whisperer의 5단계 맥락 진화

> *"사용자가 '저번처럼'이라고만 했다. AI가 알아들었다."*

사람은 기억하지 못하는 것에 대해 설명하는 순간, 코딩의 흐름이 끊긴다. Wave 1이 세션의 물리적 생존을 보장하고, Wave 2가 과감한 실수로부터의 회복을 가능하게 했다면, Wave 3는 그 위에 **맥락의 무의식적 공유**라는 새로운 차원을 쌓는다. 이것이 Zero-Explanation Coding의 핵심이다 — 사용자가 아무것도 설명하지 않아도, AI가 이미 알고 있다.

Wave 3의 중앙 집중 설계 요소는 Crow Memory 시스템이다. `crow.bin`의 7개 레지스터(context, life_context, arch, bug, style, life_avoid, life_pref)가 MemGPT의 3계층 메모리보다 세분화된 구조를 제공하며 [^366^][^435^], 이는 단순한 "기억"을 넘어 **편향(Bias), 감정(Tone), 프로젝트 지식(Project Knowledge)**의 삼중 주입을 가능하게 한다. Zoo Code Extension은 VS Code Extension API의 `globalState`, `FileSystemWatcher`, `StatusBarItem` 등을 극한까지 활용하여 Crow Memory의 맥락 주입을 자동화하며, 4B 로컬 모델의 불안정한 tool call 습관마저 Extension 레벨의 fallback injection으로 흡수한다.

이 장에서는 Zero-Explanation을 실현하는 4단계 로드맵, 4계층 Context Layer 아키텍처, 그리고 5개 조사 차원 각각의 기술적 구현을 상세히 제시한다. 모든 구현은 VS Code Extension API 내에서 실행 가능하며, [튜닝] 태그가 붙은 항목은 Zoo Code Extension 소스 직접 수정, [MCP] 태그는 Crow Memory MCP 서버 도구 추가를 의미한다.

---

## 3.1 "Zero-Explanation Coding" 4단계 로드맵

Zero-Explanation Coding은 사용자가 **설명하는 행위 자체를 제거**하는 것을 목표로 한다. 이는 단순한 "편의성"을 넘어선 철학이다 — 사용자가 AI의 존재를 의식하지 않는 순간, AI는 사용자의 신경계 연장체가 된다.

현재 Zoo Code의 상태를 객관적으로 진단하면, 사용자는 다음과 같은 설명을 반복적으로 해야 한다: "나는 Redux 대신 Zustand를 쓴다", "이 프로젝트에서는 flat folder structure를 선호한다", "지난번에 말했듯이 API 호출은 항상 try-catch로 감싼다", "아니, 이건 아니야 — 내가 원한 건 이런 게 아니라". 이런 반복 설명의 누적 피로도가 바로 Zero-Explanation이 해결해야 할 대상이다.

다음 4단계 로드맵은 Crow Memory를 중심으로, 각 단계가 이전 단계의 인프라 위에 쌓이는 구조로 설계되었다.

### 3.1.1 단계 1: Implicit Context 자동 주입 (Crow `life_context` 매 턴 자동 회상)

첫 번째 단계는 **매 대화 턴 시작 시 Crow Memory가 자동으로 회상되어 system prompt에 주입**되는 것이다. 현재 Zoo Code의 `custom_modes.yaml`에는 "Before EVERY response, call crow_recall"이라는 지시가 이미 내장되어 있지만, 4B 로컬 모델이 이 지시를 30-60% 확률로 무시한다는 현실적 제약이 존재한다 [^confidence: medium^].

따라서 이 단계의 핵심은 **모델의 자율적 tool call 호출에 의존하지 않고, Zoo Code Extension이 직접 crow_recall 결과를 system prompt에 prepend**하는 것이다. 즉, LLM이 crow_recall을 "기억해서 호출"하는 것이 아니라, Extension이 "강제로 주입"하는 구조다.

기술적 구현은 두 경로로 나뉜다. 첫째, vLLM 배포 환경에서는 `tool_choice="required"`를 설정하여 모델이 반드시 tool call을 생성하도록 강제한다 [^241^]. 둘째, Ollama나 LM Studio 등의 환경에서는 Extension 레벨의 **fallback injection**이 작동한다 — 모델 출력에서 tool call이 감지되지 않으면, Extension이 crow_recall의 결과를 자동으로 메시지 체인에 삽입하고 LLM을 재호출한다.

이 단계에서 자동 주입되는 컨텍스트의 우선순위는 다음과 같다:

```
[자동 주입 우선순위 — 단계 1]
1순위: life_context register의 최근 3개 항목 (시간순)
2순위: life_pref register의 상위 2개 강한 편향 (strength > 0.7)
3순위: life_avoid register의 상위 1개 회피 패턴 (strength > 0.7)
4순위: arch register의 현재 프로젝트 관련 항목 (키워드 매칭)
```

**Crow 연동**: `crow_recall(domain="all", limit=5)` → Extension이 결과 파싱 → system prompt prepend. `globalState`에는 "마지막 주입 시점"과 "주입된 내용 해시"를 저장하여, 동일한 컨텍스트의 중복 주입을 방지한다. [MCP]

### 3.1.2 단계 2: Cross-Session Memory (재시작 시 대화 요약 자동 복원)

두 번째 단계는 **VS Code를 껐다 켜도 대화의 맥락이 사라지지 않는 것**이다. 현재 Zoo Code는 VS Code Extension의 `globalState`에 대화 기록을 저장하지만, 이는 원본 메시지 배열 그대로를 보관하는 방식으로 용량 제약(추정 5-10MB) [^confidence: medium^] 이내에서만 유효하다. 긴 대화는 이 한계를 빠르게 초과한다.

이 단계의 핵심은 **세션 종료 시 자동 compaction + 요약본 저장**이다. VS Code Extension의 `deactivate()` 훅에서 `crow_compact()`를 호출하여 대화를 요약하고, 이 요약을 `life_context` register에 ingest한다 [^399^]. 다음 세션 시작 시 `crow_recall`로 이 요약을 회상하여 "어제 당신은 이런 작업을 하고 있었습니다"라는 암묵적 프리앰블을 구성한다.

크로스-세션 메모리의 시각적 표현 또한 중요하다. VS Code 상태바에 "Crow Context: 87% fresh" 인디케이터를 추가하여, 사용자가 "AI가 나를 기억하고 있다"는 사실을 무의식적으로 인지하게 한다. 이 숫자는 `crow.bin`의 최근 접근 시간과 `globalState`의 마지막 동기화 시점을 비교하여 계산된다.

**Crow 연동**: 세션 종료 → `crow_compact()` → `crow_ingest(register="life_context")` → 다음 세션 `crow_recall(register="life_context")`. [MCP]

### 3.1.3 단계 3: Multi-Agent Context Sync (Kimi ↔ Zoo ↔ Claude `crow.bin` 공유)

세 번째 단계는 **여러 AI 에이전트가 동일한 Crow Memory를 공유**하는 것이다. 사용자가 Kimi Code로 "이 프로젝트는 항상 try-catch로 감싼다"고 말한 내용이, Zoo Code에서 다음 코딩 세션 시작 시 이미 반영되어 있어야 한다.

`crow.bin` 파일 자체를 공유하는 것은 v1.3.4에서 이미 구현되었지만, **해석의 차이**가 핵심 문제다 [^455^]. "직설적 답변"이라는 편향이 Gemini에서는 무례로, Kimi에서는 효율성으로, Claude에서는 정중한 거절로 해석될 수 있다. 이 문제를 해결하려면, Crow가 회상하는 것이 **추상적 편향 방향**이 아니라 **구체적 텍스트 규칙**이어야 한다.

따라서 `system_prompt.md`라는 HITL(Human-in-the-Loop) 승인 영구 규칙 파일을 도입한다. `crow_evolve_propose`가 생성한 규칙 후보를 사용자가 승인하면, 이 파일에 추가되며 모든 에이전트가 동일한 텍스트를 읽는다. 규칙의 명시성이 해석의 차이를 원천적으로 줄인다. 이 파일은 Git으로 동기화되어 개발 팀 전체가 동일한 AI 행동 규칙을 공유한다.

**Crow 연동**: `crow_evolve_propose()` → HITL 승인 → `system_prompt.md` append → Git push → 모든 에이전트 `fs.watch`로 자동 reload. [MCP] + [튜닝]

### 3.1.4 단계 4: Ambient Context (감정 신호 인식 + 자동 접근 방식 변경)

네 번째 단계는 가장 진화된 형태의 컨텍스트 관리다 — AI가 사용자의 **감정 상태를 읽고 접근 방식을 자동으로 변경**하는 것이다. 사용자가 연속적으로 "아니야", "그렇게 하지 마", "다시 해"라고 말하는 패턴을 감지하면, 이는 단순한 피드백을 넘어서는 **감정 신호**다.

Zoo Code Extension은 사용자 입력의 텍스트 패턴을 실시간 분석하여, 3회 연속 거절이 감지되면 AI의 접근 방식을 자동으로 변경한다: 제안 방식에서 질의 방식으로 전환("이렇게 하면 어떨까요?" 대신 "어떤 방식을 선호하시나요?"), 자동 실행에서 HITL 승인 요구로 전환, 그리고 이 패턴이 `life_avoid` register에 `"repeated_failure → prefers_direct_control"`로 저장된다.

`polarity=-2.0`의 explicit suppression이 일정 임계값 이상 축적되면, Crow는 유사 상황에서 **사전 경고**를 생성한다 — "이 방식은 과거에 3회 거절당했습니다. 대안을 제시할까요?"라는 메시지는 AI가 사용자의 기분을 맞추려는 어색한 시도가 아니라, 축적된 데이터 기반의 합리적 제안이다.

**Crow 연동**: 거절 패턴 감지 → `crow_ingest(register="life_avoid", polarity=-2.0)` → `polarity` 축적 임계값 도달 → `crow_recall`에서 사전 경고 포함. [MCP] + [튜닝]

| 단계 | 목표 | 핵심 메커니즘 | Crow 연동 | VS Code API |
|------|------|--------------|-----------|-------------|
| **1: Implicit Context** | 매 턴 자동 편향 주입 | Extension fallback injection | `crow_recall(domain="all")` | `globalState` (중복 방지 해시) |
| **2: Cross-Session** | 재시작 시 맥락 복원 | 자동 compaction + 요약 저장 | `crow_compact()` → `life_context` | `deactivate()` 훅, 상태바 |
| **3: Multi-Agent Sync** | 에이전트 간 규칙 공유 | `system_prompt.md` HITL + Git | `crow_evolve_propose()` | `fs.watch` 자동 reload |
| **4: Ambient Context** | 감정 인식 + 접근 변경 | 연속 거절 패턴 감지 | `life_avoid` (`polarity=-2.0`) | 입력 텍스트 분석, QuickPick |

위 4단계는 순차적 의존 관계를 가진다. 단계 1의 fallback injection 인프라가 없으면 단계 2의 자동 회상도 불안정해지며, 단계 2의 세션 지속성 없이는 단계 3의 멀티에이전트 동기화가 의미를 잃는다. 단계 4는 앞의 3단계가 모두 안정화된 후에야 진정한 "앰비언트" 경험을 제공할 수 있다. 이 로드맵의 현실적 완성 기간은 분석 기준 약 8주(2개월)로 추정되며, 이는 Wave 1(4주)과 Wave 2(6주)의 인프라 위에 구축된다.

---

## 3.2 Context Layer 다이어그램

### 3.2.1 4계층: Project(`.zoo.md`) → Session(`globalState`/Crow) → Crow Bias(`crow.bin`) → Emotional(`life_avoid`)

Zero-Explanation Coding의 컨텍스트는 4개의 계층으로 구성된다. 각 계층은 다른 수명 주기, 다른 갱신 빈도, 다른 정보 밀도를 가진다. 이 다층 구조는 Claude Code의 CLAUDE.md 계층(프로젝트 → 사용자 → OS) [^313^][^362^]과 MemGPT의 core/archival/recall 메모리 계층 [^366^][^435^]을 교차적으로 결합한 것이다.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    LAYER 1: PROJECT CONTEXT                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   .zoo.md    │  │  AGENTS.md   │  │  arch/bug/   │              │
│  │  (정적 규칙)  │  │  (프로젝트   │  │  style reg   │              │
│  │              │  │   규칙)      │  │  (Crow 동적) │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│  [수명: 프로젝트 존속] [갱신: 파일 저장 시] [크기: 1-5KB]          │
├─────────────────────────────────────────────────────────────────────┤
│                    LAYER 2: SESSION CONTEXT                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ globalState  │  │ workspace    │  │ life_context │              │
│  │  (SQLite)    │  │   State      │  │   register   │              │
│  │  모드/설정    │  │  (프로젝트   │  │  (세션 요약)  │              │
│  │              │  │   상태)      │  │              │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│  [수명: VS Code 재시작] [갱신: 매 턴] [크기: 10-50KB]              │
├─────────────────────────────────────────────────────────────────────┤
│                    LAYER 3: CROW BIAS CONTEXT                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   crow.bin   │  │ life_pref /  │  │   context    │              │
│  │   (mmap)     │  │  life_avoid  │  │  (단기 대화) │              │
│  │  (편향 벡터)  │  │  (긍정/부정  │  │   (λ=0.95)   │              │
│  │              │  │   편향)      │  │              │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│  [수명: 영구] [갱신: 매 턴 자동] [크기: 100KB-10MB]                │
├─────────────────────────────────────────────────────────────────────┤
│                    LAYER 4: EMOTIONAL CONTEXT                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  life_avoid  │  │   polarity   │  │  Emotional   │              │
│  │  (회피 축적)  │  │   score      │  │   Tone       │              │
│  │  (거절 기록)  │  │ (-2.0 ~ +2.0)│  │   Adapter    │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│  [수명: 영구] [갱신: 감정 신호 감지 시] [크기: 1-10KB]             │
└─────────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
            [User Query]     [AI Response with Context]
                    │                   │
                    └─────────┬─────────┘
                              ▼
              [4-Layer Merged System Prompt]
```

**4계층의 병합 우선순위**는 아래에서 위로 갈수록 높은 우선순위를 가진다. 즉 Layer 4(감정적 컨텍스트)가 Layer 1(프로젝트 정적 규칙)을 덮어쓸 수 있다. 이는 "예외가 규칙보다 강하다"는 설계 철학을 반영한다 — 프로젝트의 일반적 규칙보다 사용자의 현재 감정 상태가 더 중요한 정보다.

**계층별 상세 설명:**

**Layer 1: Project Context**는 가장 정적이고 명시적인 계층이다. `.zoo.md`는 프로젝트 루트에 위치한 마크다운 파일로, 프로젝트 개요, 기술 스택, 팀 규칙을 담는다. 이는 Claude Code의 `CLAUDE.md` [^313^]와 동일한 패턴이며, Cursor의 `.cursorrules` [^223^], Roo Code의 `AGENTS.md` [^367^]와도 호환되는 de facto open standard로 부상하고 있다. `arch`, `bug`, `style` register는 Layer 1의 동적 확장 — Crow가 프로젝트 작업 중 자동으로 축적한 아키텍처 결정, 버그 패턴, 코드 스타일 편향이 이 레지스터에 저장된다.

**Layer 2: Session Context**는 세션의 생명주기와 동일한 계층이다. `globalState`는 VS Code Extension API의 SQLite 기반 key-value 저장소로 [^51^][^54^], Custom Mode 설정, 마지막 사용 모델, Crow 서버 주소 등이 저장된다. `life_context` register는 이 Layer의 핵심 동적 요소로, 세션 종료 시 자동 compaction된 대화 요약이 저장되어 다음 세션의 "기억" 역할을 한다.

**Layer 3: Crow Bias Context**는 영구적이고 자동 갱신되는 계층이다. `crow.bin`은 메모리 매핑(mmap) 가능한 바이너리 파일로 [^428^][^432^], `context`(단기 대화, λ=0.95 감쇠)와 `life_pref`(긍정 편향), `life_avoid`(부정 편향) 레지스터가 포함된다. 이 계층의 데이터는 VS Code의 생명주기와 무관하게 영구 지속되며, SSE 서버(9020 포트)를 통해 멀티 에이전트 환경에서도 공유된다.

**Layer 4: Emotional Context**는 가장 동적이고 민감한 계층이다. `life_avoid` register의 `polarity=-2.0` 항목이 축적됨에 따라, AI의 톤, 자동화 수준, 제안 방식이 실시간으로 조정된다. 이 계층은 사용자가 명시적으로 설정한 것이 아니라, 사용자의 거절 패턴, 지연 응답, 부정적 어휘 사용 등 **관찰된 행동**에서 자동으로 추론된다.

각 계층의 접근 경로도 다르다. Layer 1은 파일 I/O로 읽고, Layer 2는 VS Code API로 접근하고, Layer 3은 SSE/MCP로 회상하고, Layer 4는 텍스트 분석으로 추론한다. 이 다양한 접근 경로는 Zoo Code Extension의 낮은 수준 로직에서 통합되어, 최종적으로 하나의 병합된 system prompt로 LLM에 전달된다.

---

## 3.3 조사 차원 1: Implicit Context via Crow

### 3.3.1 매 턴 자동 `crow_recall(domain="all")` 호출

당신은 Zoo Code 채팅창에 "auth 부분 리팩토링해줘"라고 타이핑한다. 이전에는 이 짧은 문장 뒤에 수십 개의 추가 설명이 뒤따랐다 — "이 프로젝트는 JWT 쓰고, refresh token rotation 해야 하고, 지난번에 말했듯이 Zod로 validate하고...". 하지만 이제는 아무것도 덧붙이지 않는다. 단 7글자만 입력하고 Enter를 누른다.

그리고 Zoo Code가 응답하기 전, Extension의 Context Injection Engine이 조용히 작동한다.

```typescript
// Context Injection Engine — 매 턴 자동 실행 [튜닝]
// 파일: src/core/ContextInjector.ts

interface ContextInjectionConfig {
  maxLifeContextEntries: number;   // 최대 life_context 항목 수
  minBiasStrength: number;          // 최소 편향 강도 (0.0-1.0)
  cacheTtlMs: number;               // 캐시 유효 시간
  injectionPosition: 'system' | 'user'; // 주입 위치
}

class ContextInjector {
  private cache: Map<string, CachedBias> = new Map();
  private lastInjectionHash: string = '';
  private config: ContextInjectionConfig = {
    maxLifeContextEntries: 3,
    minBiasStrength: 0.7,
    cacheTtlMs: 30000,  // 30초 캐시
    injectionPosition: 'system'
  };

  // 매 턴 메시지 전송 전 자동 호출
  async injectBeforeTurn(
    messages: ChatMessage[],
    projectKeywords: string[]
  ): Promise<ChatMessage[]> {
    // 1단계: 캐시 확인 (SSE 호출 최소화)
    const cacheKey = this.buildCacheKey(projectKeywords);
    const cached = this.getCachedBias(cacheKey);
    
    let bias: UserBias;
    if (cached && !cached.isExpired()) {
      bias = cached.data;
    } else {
      // 2단계: Crow MCP 서버에 recall 요청 [MCP]
      bias = await this.crowClient.recall({
        domain: 'all',
        limit: 5,
        recencyBias: 0.7  // 최신 항목 우선
      });
      this.cache.set(cacheKey, { data: bias, timestamp: Date.now() });
    }

    // 3단계: 중복 주입 방지 (해시 기반)
    const injectionText = this.formatBiasAsContext(bias);
    const injectionHash = this.computeHash(injectionText);
    if (injectionHash === this.lastInjectionHash) {
      return messages; // 동일 컨텍스트, 주입 불필요
    }
    this.lastInjectionHash = injectionHash;

    // 4단계: system prompt에 prepend
    if (this.config.injectionPosition === 'system') {
      const systemMsg = messages.find(m => m.role === 'system');
      if (systemMsg) {
        systemMsg.content = `[User Context]\n${injectionText}\n\n${systemMsg.content}`;
      }
    }

    // 5단계: 주입 시점 기록 (globalState)
    await this.saveInjectionTimestamp(injectionHash);

    return messages;
  }

  private formatBiasAsContext(bias: UserBias): string {
    const lines: string[] = [];
    
    // life_context 항목 (최근 3개)
    for (const ctx of bias.lifeContexts.slice(0, this.config.maxLifeContextEntries)) {
      lines.push(`- Context: ${ctx.content}`);
    }
    
    // 강한 선호 편향 (strength > 0.7)
    const strongPrefs = bias.preferences.filter(p => p.strength >= this.config.minBiasStrength);
    if (strongPrefs.length > 0) {
      lines.push(`- Preferences: ${strongPrefs.map(p => p.topic).join(', ')}`);
    }
    
    // 강한 회피 편향
    const strongAvoids = bias.avoidances.filter(a => a.strength >= this.config.minBiasStrength);
    if (strongAvoids.length > 0) {
      lines.push(`- Avoid: ${strongAvoids.map(a => a.topic).join(', ')}`);
    }
    
    return lines.join('\n');
  }

  private async saveInjectionTimestamp(hash: string): Promise<void> {
    await vscode.workspace.getConfiguration('zoo').update(
      'context.lastInjectionHash', hash, true
    );
    await vscode.workspace.getConfiguration('zoo').update(
      'context.lastInjectionTime', Date.now(), true
    );
  }
}
```

이 ContextInjector는 Zoo Code Extension의 메시지 파이프라인에 가로채기(interceptor)로 등록된다. 사용자가 메시지를 본낼 때마다 `injectBeforeTurn`이 자동 실행되며, Crow Memory에서 회상된 컨텍스트가 system prompt에 조용히 추가된다. 사용자는 이 과정을 전혀 인지하지 못한다 — 그저 AI가 "이미 알고 있을 뿐"이다.

캐시 메커니즘의 중요성을 간과해서는 안 된다. 매 턴 SSE 서버를 호출하는 것은 지연 시간(네트워크 왕복 5-20ms)과 서버 부하를 초래한다. 30초 TTL 캐시는 일반적인 코딩 세션에서 80-90%의 SSE 호출을 제거할 수 있다. 캐시 무효화는 `crow_ingest`가 호출될 때(새로운 컨텍스트가 저장될 때) 자동으로 발생한다.

### 3.3.2 4B 모델 지시 무시 시 Extension "fallback injection"

4B급 소형 모델의 가장 치명적인 불안정성은 **multi-turn 대화에서 system prompt의 복합 지시를 선택적으로 무시하는 것**이다. ManyIFEval 벤치마크 연구에 따른, 모델은 개별 지시에 대해서는 높은 정확도를 보이지만, 여러 지시가 동시에 주어지면 prompt-level accuracy가 급격히 저하된다 [^313^]. Zoo Code의 "매 턴 crow_recall 호출" 지시는, 코드 생성 규칙 + 에러 처리 규칙 + JSON 출력 형식 등 다른 지시와 경쟁하면서 30-60% 확률로 무시된다 [^confidence: medium^].

**fallback injection**은 이 문제를 Extension 레벨에서 해결하는 아키텍처 패턴이다. 모델이 crow_recall을 호출하지 않아도, Extension이 대신 호출하여 결과를 메시지 체인에 삽입한다. 이는 MCP 서버 레벨이 아닌 **Zoo Code Extension 자체 튜닝**으로 구현되어야 한다.

```typescript
// Fallback Injection Engine [튜닝]
// 파일: src/core/FallbackInjector.ts

interface FallbackConfig {
  // 모델이 crow_recall을 호출하지 않았을 때의 대응 전략
  strategy: 'force_prepend' | 'retry_with_reminder' | 'abort';
  maxRetries: number;
  reminderTemplate: string;
  // 감지 설정
  requiredToolName: string;        // 강제 감지할 tool 이름
  checkIntervalMs: number;         // 출력 검사 간격
}

class FallbackInjector {
  private config: FallbackConfig = {
    strategy: 'force_prepend',
    maxRetries: 2,
    reminderTemplate: '[SYSTEM] 이 응답에 crow_recall 결과가 포함되지 않았습니다. ' +
                      '아래 사용자 컨텍스트를 참고하여 응답을 생성하세요:\n\n{{context}}',
    requiredToolName: 'crow_recall',
    checkIntervalMs: 100
  };

  // LLM 출력 스트리밍 중 실시간 감시
  async monitorAndFix(
    streamingResponse: AsyncIterable<LLMChunk>,
    originalMessages: ChatMessage[]
  ): Promise<ChatMessage[]> {
    let hasToolCall = false;
    const chunks: LLMChunk[] = [];

    // 스트리밍 출력 소비하면서 tool call 감지
    for await (const chunk of streamingResponse) {
      chunks.push(chunk);
      if (this.isToolCall(chunk, this.config.requiredToolName)) {
        hasToolCall = true;
      }
    }

    // Tool call이 없으면 fallback injection 실행
    if (!hasToolCall) {
      console.log('[FallbackInjector] crow_recall missing, injecting...');
      return await this.executeFallback(originalMessages);
    }

    return originalMessages; // 정상, 수정 불필요
  }

  private async executeFallback(messages: ChatMessage[]): Promise<ChatMessage[]> {
    // 1단계: Crow에서 강제 회상 [MCP]
    const context = await this.crowClient.recall({ domain: 'all', limit: 5 });
    const formatted = this.formatContext(context);

    // 2단계: 전략별 처리
    switch (this.config.strategy) {
      case 'force_prepend':
        // 마지막 user 메시지 앞에 컨텍스트 삽입
        const userIdx = messages.findLastIndex(m => m.role === 'user');
        if (userIdx >= 0) {
          messages.splice(userIdx, 0, {
            role: 'system',
            content: this.config.reminderTemplate.replace('{{context}}', formatted),
            isFallback: true  // 마커: 이 메시지는 fallback임
          });
        }
        break;

      case 'retry_with_reminder':
        const lastMsg = messages[messages.length - 1];
        if (lastMsg.role === 'assistant') {
          lastMsg.content += `\n\n[REMINDER] crow_recall을 호출하여 ` +
            `사용자 컨텍스트를 확인하세요: ${formatted.substring(0, 200)}`;
        }
        break;

      case 'abort':
        throw new Error('Required tool call missing, aborting turn');
    }

    // 3단계: globalState에 fallback 통계 기록
    await this.recordFallbackStat();

    return messages;
  }

  private async recordFallbackStat(): Promise<void> {
    const stats = vscode.workspace.getConfiguration('zoo').get('fallbackStats', {
      totalTurns: 0, fallbackCount: 0, lastFallbackAt: 0
    });
    stats.totalTurns++;
    stats.fallbackCount++;
    stats.lastFallbackAt = Date.now();
    await vscode.workspace.getConfiguration('zoo').update('fallbackStats', stats, true);
  }

  private isToolCall(chunk: LLMChunk, toolName: string): boolean {
    return chunk.type === 'tool_call' && 
           chunk.name === toolName;
  }
}
```

이 fallback injection은 4B 모델의 불안정성을 **Extension이 흡수**하는 아키텍처 패턴이다. vLLM의 `tool_choice="required"`가 가장 이상적인 해결책이지만 [^241^], 모든 사용자가 vLLM을 사용하는 것은 아니다. Ollama, LM Studio, 또는 다른 로컬 추론 엔진을 사용하는 사용자에게도 동일한 신뢰성을 제공하기 위해서는 Extension 레벨의 fallback이 필수적이다.

fallback 통계(`fallbackStats`)는 중요한 운영 데이터다. 특정 모델에서 fallback이 자주 발생한다면, 그 모델의 system prompt를 조정하거나 사용자에게 모델 교체를 권장하는 근거가 된다. 예를 들어 Llama 3.2 3B는 "극도로 공격적인 tool call 습관"을 보여 9/10의 상황에서 불필요한 tool call을 생성한다 [^243^], 반면 Qwen2.5 1.5B는 "보수적"으로 불확실하면 호출하지 않는다. 모델별 패턴을 통계적으로 축적하면, 모델별 최적화 전략을 자동으로 선택할 수 있다.

### 3.3.3 `crow.bin` mmap 직접 읽기 캐싱

ContextInjector의 매 턴 SSE 호출은 네트워크 지연을 수반한다. 더 빠른 경로는 Extension이 `crow.bin`을 메모리 매핑(mmap)으로 직접 읽는 것이다. 이는 zero-copy 접근으로, 커널이 파일 페이지를 사용자 공간 메모리에 직접 매핑하여 복사 오버헤드를 제거한다 [^428^][^432^].

```typescript
// crow.bin mmap 직접 읽기 캐시 [튜닝]
// 파일: src/core/CrowMmapCache.ts

import { mmap, munmap } from '@mmap/node';
import * as fs from 'fs';

class CrowMmapCache {
  private fd: number | null = null;
  private mapped: Buffer | null = null;
  private fileSize: number = 0;
  private binPath: string;
  private lastModified: number = 0;
  
  constructor(binPath: string = path.join(os.homedir(), '.zoo-code', 'crow', 'crow.bin')) {
    this.binPath = binPath;
  }

  // Extension 활성화 시 호출
  initialize(): void {
    this.fd = fs.openSync(this.binPath, 'r');
    this.fileSize = fs.fstatSync(this.fd).size;
    this.mapped = mmap.alloc(
      this.fileSize,
      mmap.PROT_READ,      // 읽기 전용
      mmap.MAP_SHARED,     // 프로세스 간 공유
      this.fd
    );
    this.lastModified = fs.fstatSync(this.fd).mtimeMs;
    
    // FileSystemWatcher로 crow.bin 변경 감시
    const watcher = vscode.workspace.createFileSystemWatcher(
      new vscode.RelativePattern(vscode.Uri.file(this.binPath), '*')
    );
    watcher.onDidChange(() => this.remap());
  }

  // Register 데이터 직접 파싱 (헤더 → 테이블 → 엔트리)
  readRegister(registerName: string): CrowEntry[] {
    if (!this.mapped) throw new Error('Mmap not initialized');
    
    // Header: [magic(4)][version(4)][registerCount(4)]
    const magic = this.mapped.toString('ascii', 0, 4);
    if (magic !== 'CROW') throw new Error('Invalid crow.bin magic');
    
    const version = this.mapped.readUInt32LE(4);
    const regCount = this.mapped.readUInt32LE(8);
    
    // Register Table: 각 16바이트 [name(8)][offset(4)][entryCount(4)]
    const tableOffset = 12;
    for (let i = 0; i < regCount; i++) {
      const entryOffset = tableOffset + i * 16;
      const name = this.mapped.toString('ascii', entryOffset, 8).replace(/\0/g, '');
      const dataOffset = this.mapped.readUInt32LE(entryOffset + 8);
      const entryCount = this.mapped.readUInt32LE(entryOffset + 12);
      
      if (name === registerName) {
        return this.parseEntries(dataOffset, entryCount);
      }
    }
    return [];
  }

  private remap(): void {
    if (this.mapped) munmap(this.mapped);
    if (this.fd) fs.closeSync(this.fd);
    this.initialize();
  }

  dispose(): void {
    if (this.mapped) munmap(this.mapped);
    if (this.fd) fs.closeSync(this.fd);
  }
}
```

mmap 캐싱은 **읽기 전용** 최적화다. 쓰기(write)는 여전히 SSE 서버를 통해 수행하여 동시 쓰기 충돌을 방지한다. 이는 CQRS(Command Query Responsibility Segregation) 패턴의 일종으로, 읽기 성능을 극대화하면서 쓰기의 일관성은 서버가 보장한다.

현실적으로, mmap은 Node.js 환경에서 네이티브 addon이 필요하여 배포 복잡도가 증가한다. 대안으로 **파일 시스템 캐시(page cache)**에 의존하는 방식도 있다 — `fs.readFileSync`로 `crow.bin`을 읽으면, 운영체제가 자동으로 페이지 캐시에 보관하므로 두 번째 읽기부터는 디스크 I/O 없이 메모리에서 읽는다. 이 방식은 네이티브 addon 없이 순수 Node.js로 구현 가능하며, 페이지 캐시의 TTL(일반적으로 30초-5분) 내에서는 충분한 성능을 제공한다.

### 3.3.4 바이브 점수: 현재 4/10 → 목표 9/10

현재 Zoo Code의 implicit context 수준은 4점이다. `custom_modes.yaml`에 crow_recall 호출 지시가 있지만, 4B 모델이 이를 unreliable하게 실행하며, 사용자는 여전히 "Zustand 쓴다", "try-catch로 감싼다" 같은 설명을 반복해야 한다. Fallback injection이 구현되면 모델의 지시 따르기 여부와 무관하게 컨텍스트가 주입되므로, 사용자는 AI가 "이미 알고 있다"는 경험을 하게 된다.

| 측면 | 현재 (4/10) | 목표 (9/10) | 주요 장애물 | 해결책 |
|------|------------|------------|------------|--------|
| 자동 crow_recall | 모델 의존, 40-70% 실패율 | 100% 주입 보장 | 4B 지시 무시 | Extension fallback injection |
| 캐싱 | 없음 (매 턴 SSE 호출) | 30초 TTL mmap 캐시 | SSE 지연 5-20ms | mmap 또는 page cache |
| 중복 방지 | 없음 (동일 컨텍스트 반복) | 해시 기반 중복 제거 | 불필요한 토큰 소모 | `globalState` 해시 저장 |
| 프로젝트 키워드 필터링 | 없음 (전체 편향 주입) | 프로젝트 관련 항목만 선별 | 무관한 컨텍스트 노이즈 | `arch` register 키워드 매칭 |
| 편향 강도 임계값 | 없음 (모든 항목 주입) | strength > 0.7만 주입 | 약한 편향 노이즈 | `minBiasStrength` 설정 |

9점에 도달하면 사용자는 "auth 부분 리팩토링해줘"라는 7글자 입력만으로, AI가 JWT + refresh token rotation + Zod validation + flat folder structure + try-catch 래핑을 모두 고려한 응답을 생성하는 경험을 하게 된다. 1점이 모자라는 이유는, 10점이 되려면 사용자가 기능의 "존재를 의식하지 않아야" 하는데, fallback injection이 간헐적으로 동작할 때의 미세한 지연(수백 ms)이나 컨텍스트 누락이 여전히 인지될 가능성이 있기 때문이다.

---

## 3.4 조사 차원 2: Cross-Session Memory

### 3.4.1 `globalState`에 대화 요약 저장 (5MB 내)

당신은 어제 밤 11시까지 Zoo Code와 함께 API 엔드포인트를 리팩토링했다. 오늘 아침 VS Code를 켰다. 채팅창은 비어 있다 — 새로운 세션이 시작되었다. 하지만 Zoo Code가 첫 번째 응답을 본내기 전, 상태바의 "Crow Context: 87% fresh" 인디케이터가 깜빡이고, AI의 첫 마디는 "어제 JWT 인증 리팩토링을 마무리하려는 거죠?"이다.

크로스-세션 메모리의 핵심은 **전체 대화 원본이 아닌 압축된 요약**을 저장하는 것이다. VS Code Extension의 `globalState`는 SQLite 기반 key-value 저장소로 [^51^][^54^], 추정 5-10MB 용량 제약이 있다 [^confidence: medium^]. 1시간 이상의 코딩 세션 대화를 원본 그대로 저장하면 이 한계를 빠르게 초과하여, 실제로 Roo Code에서는 "excessive globalState usage"로 인한 확장 크래시 이슈가 보고된 바 있다 [^234^].

따라서 저장 형식은 **요약본(summary) + 핵심 메타데이터**로 제한된다:

```typescript
// 세션 요약 저장 형식 [튜닝]
// 파일: src/core/SessionPersistence.ts

interface SessionSummary {
  sessionId: string;
  projectPath: string;
  startedAt: number;        // Unix timestamp
  endedAt: number;
  summary: string;          // LLM-generated summary (500-1000자)
  keyDecisions: string[];   // 핵심 기술 결정
  touchedFiles: string[];   // 수정된 파일 목록
  pendingTasks: string[];   // 미완료 작업
  customMode: string;       // 사용 중이던 Custom Mode
  modelId: string;          // 사용 중이던 모델
  // 압축된 대화 핵심 포인트 (원본 대화의 5-10% 크기)
  keyExchanges: Array<{
    role: 'user' | 'assistant';
    keyPoint: string;       // 핵심 문장만 추출
    timestamp: number;
  }>;
}

// 용량 제약: 전체 요약이 50KB를 초과하면 keyExchanges를 요약으로 대체
const MAX_SUMMARY_BYTES = 50 * 1024;

class SessionPersistence {
  private readonly GLOBAL_STATE_KEY = 'zoo.sessionSummaries';
  private readonly MAX_SESSIONS = 20; // 최근 20개 세션만 유지

  // 세션 종료 시 호출 (deactivate 또는 명시적 종료)
  async saveSessionSummary(session: ChatSession): Promise<void> {
    // 1단계: 대화 요약 생성 [MCP]
    const summary = await this.generateSummary(session);
    
    // 2단계: 기존 요약 불러오기
    const existing = await this.loadSummaries();
    
    // 3단계: 새 요약 추가 (최근 것이 앞에 오도록)
    existing.unshift(summary);
    
    // 4단계: 오래된 요약 제거 (MAX_SESSIONS 초과 시)
    while (existing.length > this.MAX_SESSIONS) {
      const removed = existing.pop();
      // 오래된 요약은 Crow의 life_context로 이관
      await this.migrateToCrow(removed!);
    }
    
    // 5단계: 용량 검증 후 저장
    const serialized = JSON.stringify(existing);
    if (Buffer.byteLength(serialized) > MAX_SUMMARY_BYTES * this.MAX_SESSIONS) {
      // 초과 시 keyExresses 축소
      for (const s of existing) {
        s.keyExchanges = s.keyExchanges.slice(0, 3);
      }
    }
    
    await this.context.globalState.update(
      this.GLOBAL_STATE_KEY, 
      JSON.stringify(existing)
    );
  }

  // 다음 세션 시작 시 호출
  async getLastSessionContext(projectPath: string): Promise<string | null> {
    const summaries = await this.loadSummaries();
    const lastSession = summaries.find(s => s.projectPath === projectPath);
    
    if (!lastSession) return null;
    
    // 시간 경과에 따른 "신선도" 계산
    const hoursElapsed = (Date.now() - lastSession.endedAt) / 3600000;
    const freshness = Math.max(0, 1 - hoursElapsed / 168); // 7일 후 0%
    
    // 상태바 업데이트
    this.updateFreshnessIndicator(Math.round(freshness * 100));
    
    return this.formatAsPreamble(lastSession, freshness);
  }

  private updateFreshnessIndicator(percentage: number): void {
    const color = percentage > 70 ? '$(check)' : 
                  percentage > 30 ? '$(warning)' : '$(error)';
    this.statusBarItem.text = `${color} Crow Context: ${percentage}% fresh`;
    this.statusBarItem.show();
  }
}
```

`SessionPersistence`는 `deactivate()` 훅에서 호출되지만, VS Code의 `deactivate()`는 비동기 작업을 완전히 보장하지 않는다는 치명적 제약이 있다 [^345^][^268^]. 따라서 **실시간 주기적 저장**도 병행한다 — 사용자가 5분 이상 활동이 없을 때(`onDidChangeTextDocument` 이벤트의 타임아웃), 자동으로 중간 요약을 저장하는 방식이다.

용량 관리의 핵심은 "최근 20개 세션, 각 50KB 이내"라는 하드 제약이다. 20개 × 50KB = 1MB로, `globalState`의 추정 용량 제약 내에서 안전하게 운용할 수 있다. 이를 초과하면 오래된 요약을 Crow의 `life_context` register로 이관하여, `globalState`의 세션 요약은 "최근 3일"에 집중하고, 3일 이전의 맥락은 Crow를 통해 회상하는 2계층 구조가 된다.

### 3.4.2 Crow `life_context`에 세션 요약 ingest

`globalState`의 제약을 넘어서는 장기 크로스-세션 메모리는 Crow의 `life_context` register가 담당한다. 세션 종료 시 `crow_compact()`가 자동 실행되어 대화를 요약하고, 이 요약을 `crow_ingest(register="life_context")`로 저장한다 [^399^].

`crow_compact()`의 동작 메커니즘은 Claude Code의 3-tier compaction 시스템 [^401^][^406^]을 참고한다. Tier 1(Session Memory)에서 가장 최근 5개 메시지(10-40K 토큰)를 보존하고, Tier 2(Microcompaction)에서 오래된 tool output을 "[Old tool result content cleared]"로 대체하며, Tier 3(Traditional Compaction)에서 LLM을 사용하여 전체 대화의 구조화된 요약을 생성한다.

요약의 구조는 다음과 같다:

```
[자동 생성된 세션 요약 형식]

## Goal
사용자가 달성하려던 목표 (한 문장)

## Standing Instructions
사용자가 반복적으로 언급한 지시사항

## Key Discoveries
작업 중 발견된 중요 정보, 관련 코드, 오류 메시지

## Accomplished So Far
완료/진행 중인 작업, 변경된 파일 목록

## Relevant Files & Paths
작업에 관련된 파일 경로 목록

## Next Steps
에이전트가 하려던 다음 작업 (예측)
```

이 요약 형식은 Claude Code의 compaction 프롬프트 [^402^]를 기반으로 하되, `life_context` register의 특성에 맞게 조정되었다. 중요한 차이점은 "다음 단계 예측" 항목이 추가되어, 다음 세션 시작 시 AI가 "어제 하려던 것을 이어서" 제안할 수 있다는 점이다.

### 3.4.3 상태바 "Crow Context: 87% fresh" 인디케이터

크로스-세션 메모리는 **보이지 않는 인프라**이지만, 사용자가 그 존재를 무의식적으로 인지하게 하는 것이 중요하다. VS Code 상태바에 "Crow Context: 87% fresh" 인디케이터를 추가하면, 사용자는 "AI가 나를 기억하고 있다"는 사실을 시각적으로 확인한다.

"freshness"는 단순한 시간 경과가 아니라 **복합 지표**다:

$$
\text{freshness} = 0.4 \times \text{recency} + 0.3 \times \text{relevance} + 0.2 \times \text{coverage} + 0.1 \times \text{confidence}
$$

- **recency**: 마지막 세션으로부터의 시간 경과 (7일 후 0%)
- **relevance**: 현재 프로젝트와 과거 세션의 프로젝트 경로 일치도
- **coverage**: 저장된 요약이 실제 대화의 얼마나 많은 부분을 커버하는지
- **confidence**: LLM 요약의 신뢰도 (긴 대화일수록 낮아짐)

인디케이터의 색상 변화는 사용자의 무의식적인 기대를 조정한다. 70% 이상(초록색)이면 "AI가 충분히 나를 알고 있다", 30-70%(노란색)이면 "일부 맥락이 누락되었을 수 있다", 30% 이하(빨간색)이면 "새로운 프로젝트나 오랜만의 세션"을 암시한다. 이것이 사용자에게 불안감을 주어서는 안 된다 — 오히려 "AI가 솔직하게 말해준다"는 신뢰를 구축해야 한다.

### 3.4.4 바이브 점수: 현재 3/10 → 목표 9/10

현재 Zoo Code의 크로스-세션 메모리는 3점이다. VS Code 재시작 시 대화가 완전히 초기화되며, Custom Mode 선택 상태마저 기억되지 않는다. 사용자는 "어제 했던 걸 다시 설명해야 하나"라는 피로감을 느낀다.

| 측면 | 현재 (3/10) | 목표 (9/10) | 주요 장애물 | 해결책 |
|------|------------|------------|------------|--------|
| 세션 복원 | 없음 (완전 초기화) | 요약 기반 자동 복원 | `deactivate()` 비동기 불안정 | 주기적 저장 + `deactivate()` 이중 저장 |
| 용량 관리 | 없음 | 50KB/세션 × 20세션 | `globalState` 5-10MB 제한 | 요약 압축, Crow로 이관 |
| 시각적 표현 | 없음 | 상태바 freshness 표시 | 상태바 공간 제약 | 아이콘 + 툴팁으로 최소 공간 |
| 프로젝트 매칭 | 없음 | 동일 프로젝트 자동 인식 | 다중 프로젝트 혼동 | `workspaceState` 프로젝트 경로 저장 |
| 세션 간 작업 이어하기 | 없음 | "어제 하던 것 이어서" 제안 | 다음 단계 예측 불확실 | `crow_compact`의 Next Steps 항목 |

9점에 도달하면 사용자는 VS Code를 껐다 켜도 "어제 하던 작업"의 맥락이 자연스럽게 이어지는 경험을 하게 된다. 1점이 모자라는 이유는, 세션 간 맥락이 100% 완벽하게 복원되지는 않으며, 일부 세부사항은 여전히 사용자의 확인이 필요하기 때문이다 — 하지만 "대화를 다시 시작하는" 피로는 완전히 제거된다.

---

## 3.5 조사 차원 3: Multi-Agent Context Sharing via Crow

### 3.5.1 동일 `crow.bin` 공유의 해석 차이 문제

사용자는 Kimi Code로 "이 프로젝트에서 API 에러 핸들링은 항상 Zod로 validate하고, 실패하면 422를 리턴해"라고 말했다. Crow의 `arch` register에 이 규칙이 저장되었다. 다음 날, 사용자는 Zoo Code에서 같은 프로젝트를 열고 "새로운 엔드포인트 추가해줘"라고 말했다. Zoo Code는 `crow_recall`로 `arch` register를 검색하고, 동일한 규칙을 회상한다.

하지만 문제는 **해석**이다. Kimi Code는 이 규칙을 "Zod validate → 422 return"이라는 명확한 코드 패턴으로 해석했지만, Zoo Code의 4B 모델은 이를 "에러 핸들링이 중요하구나"라는 추상적 개념으로 희석시켜 해석할 수 있다. "422" 대신 "400"을 생성하거나, Zod 대신 수동 `if` 체크를 생성할 수 있다.

이 해석 차이의 근원은 LLM 모델마다 **instruction following의 세밀한 특성**이 다르다는 것이다. Gemma 3 4B는 IFEval에서 90.2%를 기록할 정도로 instruction following에 강하지만 [^310^], 코딩 벤치마크에서는 Qwen2.5 7B에 뒤처진다. Phi-4-Mini는 BFCL에서 가장 균형잡힌 tool calling judgment를 보이지만 [^243^], Qwen2.5 1.5B는 보수적으로 불필요한 호출을 피한다. 모델마다 같은 텍스트를 읽고도 다른 코드를 생성한다.

### 3.5.2 `system_prompt.md` HITL 승인 영구 규칙 저장

해석 차이를 원천적으로 줄이는 방법은 **추상적 편향이 아니라 구체적 텍스트 규칙**을 공유하는 것이다. `system_prompt.md`는 모든 에이전트가 동일하게 읽는 프로젝트 규칙 파일이다.

```markdown
<!-- system_prompt.md 예시 — HITL 승인된 영구 규칙 -->
# 프로젝트 규칙 (HITL 승인)

## API 설계
- 모든 입력은 Zod 스키마로 validate
- Zod validation 실패 시 반드시 HTTP 422 응답
- 성공 응답은 { data: T, meta: { page, limit, total } } 형식
- 에러 응답은 { error: { code: string, message: string, details?: unknown } } 형식

## 코드 스타일
- fetch 대신 axios 사용 (interceptors가 필요함)
- async/await 사용, Promise 체이닝 금지
- any 타입 사용 금지, unknown으로 대체

## 아키텍처
- src/routes/ — API 엔드포인트 정의
- src/services/ — 비즈니스 로직
- src/models/ — Zod 스키마 + DB 타입
- 유틸리티는 src/utils/에 flat하게 배치 (nested utils 금지)

## 승인 이력
- 2025-07-15: @user — Zod validate + 422 규칙 추가
- 2025-07-14: @user — flat utils 구조 확정
```

이 파일의 핵심 특성은 **명시성(specificity)**이다. "에러 핸들링을 잘핸라"가 아니라 "Zod validation 실패 시 반드시 HTTP 422"라는 구체적 코드이다. 이 명시성이 모델 간 해석 차이를 원천적으로 억제한다. Claude Code의 CLAUDE.md가 200줄 제한을 두는 이유 [^313^]도 동일 — 짧고 명확한 규칙이 긴 모호한 설명보다 adherence가 높다.

`system_prompt.md`의 규칙은 `crow_evolve_propose`가 자동 생성한 후보가 아니라, **사용자가 직접 승인(HITL)**한 것만 포함된다. `crow_evolve_propose`가 "사용자가 Zod를 선호하는 것으로 보입니다. system_prompt.md에 추가할까요?"라고 제안하면, 사용자는 QuickPick으로 "예/아니오/수정"을 선택한다. 이 HITL 단계는 완전 무인 자동화의 신뢰성 문제를 방지하며, "The Vibe Paradox"에서 논의된 "완벽하게 예측 가능한 자동화"를 실현한다.

### 3.5.3 `crow_evolve_propose` → HITL → Git 동기화 프로토콜

멀티에이전트 컨텍스트 동기화는 Git을 중심으로 한 **선형 파이프라인**으로 이루어진다.

```typescript
// Multi-Agent Context Sync 프로토콜 [MCP] + [튜닝]
// 파일: src/core/MultiAgentSync.ts

interface ContextSyncPipeline {
  // 1. 규칙 후보 생성 (Crow 자동 분석)
  propose(): Promise<RuleProposal[]>;        // [MCP] crow_evolve_propose
  
  // 2. 사용자 승인 (HITL)
  hitlApprove(proposals: RuleProposal[]): Promise<ApprovedRule[]>; // [튜닝]
  
  // 3. 파일에 기록
  persist(rules: ApprovedRule[]): Promise<void>;                  // [튜닝]
  
  // 4. Git 동기화
  sync(): Promise<SyncResult>;                                     // [튜닝]
  
  // 5. 모든 에이전트 자동 reload
  notifyReload(): Promise<void>;                                   // [튜닝]
}

class MultiAgentSyncEngine implements ContextSyncPipeline {
  private systemPromptPath: string;
  private gitEnabled: boolean;

  constructor(projectRoot: string) {
    this.systemPromptPath = path.join(projectRoot, '.zoo', 'system_prompt.md');
    this.gitEnabled = fs.existsSync(path.join(projectRoot, '.git'));
  }

  async propose(): Promise<RuleProposal[]> {
    // [MCP] crow_evolve_propose 호출
    const result = await crowClient.call('crow_evolve_propose', {
      analyzeRegisters: ['life_pref', 'life_avoid', 'arch', 'style'],
      maxProposals: 5,
      minConfidence: 0.7
    });
    return result.proposals;
  }

  async hitlApprove(proposals: RuleProposal[]): Promise<ApprovedRule[]> {
    const approved: ApprovedRule[] = [];
    
    for (const proposal of proposals) {
      const choice = await vscode.window.showQuickPick(
        ['승인', '거부', '수정', '모두 승인', '모두 거부'],
        {
          placeHolder: `[규칙 제안] ${proposal.description}`,
          detail: `근거: ${proposal.evidence.join(', ')}\n신뢰도: ${proposal.confidence}`
        }
      );

      switch (choice) {
        case '승인':
          approved.push({ ...proposal, approvedAt: Date.now() });
          break;
        case '수정':
          const edited = await vscode.window.showInputBox({
            value: proposal.ruleText,
            prompt: '규칙을 수정하세요'
          });
          if (edited) approved.push({ ...proposal, ruleText: edited, approvedAt: Date.now() });
          break;
        case '모두 승인':
          return proposals.map(p => ({ ...p, approvedAt: Date.now() }));
        case '모두 거부':
          return [];
      }
    }
    return approved;
  }

  async persist(rules: ApprovedRule[]): Promise<void> {
    // 기존 파일에 규칙 추가
    const timestamp = new Date().toISOString().split('T')[0];
    const entries = rules.map(r =>
      `- ${timestamp}: @${r.suggestedBy} — ${r.ruleText}`
    );

    await fs.promises.appendFile(
      this.systemPromptPath,
      `\n${entries.join('\n')}\n`
    );
  }

  async sync(): Promise<SyncResult> {
    if (!this.gitEnabled) return { status: 'skipped', reason: 'no_git' };

    try {
      // Git 자동 커밋
      const { execSync } = require('child_process');
      execSync('git add .zoo/system_prompt.md', { cwd: path.dirname(this.systemPromptPath) });
      execSync(`git commit -m "chore: update AI rules (${new Date().toISOString()})"`, {
        cwd: path.dirname(this.systemPromptPath)
      });
      execSync('git push', { cwd: path.dirname(this.systemPromptPath) });
      return { status: 'synced' };
    } catch (e) {
      return { status: 'error', error: String(e) };
    }
  }
}
```

이 파이프라인의 핵심은 **HITL(Human-in-the-Loop) 단계를 건드지 않으면 규칙이 절대 자동 추가되지 않는다**는 것이다. `crow_evolve_propose`가 제안한 규칙 후보는 사용자의 명시적 승인을 거쳐야만 `system_prompt.md`에 기록된다. 이는 Claude Code의 Auto Memory가 사용자의 확인 없이 MEMORY.md에 기록하는 방식 [^228^]과 대비되며, Zoo Code의 설계 철학인 "완벽하게 예측 가능한 자동화"를 구현한다.

### 3.5.4 `fs.watch` 자동 reload

`system_prompt.md`가 Git pull이나 수동 편집으로 변경되면, 모든 에이전트가 자동으로 새 규칙을 로드해야 한다. Zoo Code Extension은 `fs.watch` 또는 VS Code의 `FileSystemWatcher`를 사용하여 이 파일의 변경을 감시한다.

```typescript
// system_prompt.md 자동 reload 감시 [튜닝]
const watcher = vscode.workspace.createFileSystemWatcher(
  new vscode.RelativePattern(workspaceFolder, '.zoo/system_prompt.md')
);

watcher.onDidChange(async (uri) => {
  const newContent = await vscode.workspace.fs.readFile(uri);
  const rules = parseRules(newContent.toString());
  
  // 현재 세션의 system prompt에 새 규칙 반영
  contextInjector.updateProjectRules(rules);
  
  // 사용자에게 알림 (조용하게)
  vscode.window.showInformationMessage(
    'AI 규칙이 업데이트되었습니다.',
    { modal: false }
  );
});
```

이 구조는 `AGENTS.md` Convergence 패턴의 핵심 인프라다 [^367^]. `AGENTS.md`가 Cursor, Windsurf, Kilo Code, Claude Code 간 de facto open standard로 부상하고 있으며 [^confidence: high^], Zoo Code가 이 표준을 `system_prompt.md`와 통합하면 **멀티 에이전트 간 완벽한 컨텍스트 공유**가 실현된다. 정적 규칙(`AGENTS.md` + `system_prompt.md`)과 동적 편향(Crow Memory)의 2layer 컨텍스트가 완성되는 순간이다.

### 3.5.5 바이브 점수: 현재 3/10 → 목표 8/10

현재 멀티에이전트 컨텍스트 공유는 3점이다. `crow.bin` 공유는 되지만, 해석 차이로 인해 사용자는 여전히 각 에이전트에게 별도로 설명해야 한다.

| 측면 | 현재 (3/10) | 목표 (8/10) | 주요 장애물 | 해결책 |
|------|------------|------------|------------|--------|
| `crow.bin` 공유 | O (파일 공유) | O (유지) | 이미 구현됨 | 유지 |
| 해석 일관성 | 없음 (모델별 차이) | 높음 (텍스트 규칙 기반) | 모델별 instruction following 특성 | `system_prompt.md` 명시적 규칙 |
| 규칙 자동 생성 | 없음 | `crow_evolve_propose` HITL | 규칙 충돌, 부적절한 규칙 | 사용자 승인 필수 단계 |
| Git 동기화 | 수동 | 자동 커밋 + push | Git 설정 불일치 | 선택적 자동화, 실패 시 graceful |
| 자동 reload | 없음 | `fs.watch` 기반 | 파일 감시 리소스 | 변경 시에만 감시, 1초 debounce |

8점에 도달하면 사용자가 Kimi Code에서 "이 프로젝트는 flat structure야"라고 말한 것이, Zoo Code에서도 동일하게 반영되는 경험을 하게 된다. 2점이 모자라는 이유는, 완전한 멀티에이전트 동기화는 **표준화된 에이전트 컨텍스트 포맷**이 업계 전체에 확산되어야 10점이 가능하기 때문이다. Zoo Code는 `system_prompt.md`를 자체 표준으로 제시하지만, 모든 AI 코딩 도구가 이를 채택할 때까지는 100% 일관성은 달성하기 어렵다.

---

## 3.6 조사 차원 4: Project-Specific Context Auto-Load

### 3.6.1 `.zoo.md` 자동 system prompt prepend

프로젝트 루트의 `.zoo.md` 파일은 프로젝트별 정적 컨텍스트를 담는 가장 직관적인 메커니즘이다. 이 파일이 존재하면 Zoo Code Extension은 **세션 시작 시 자동으로 system prompt에 prepend**한다. 사용자는 아무것도 하지 않아도 된다 — 파일이 존재한다는 사실만으로 컨텍스트가 주입된다.

`.zoo.md`의 내용은 Claude Code의 `CLAUDE.md` [^313^]와 구조적으로 호환되며, 다음 섹션을 포함한다:

```markdown
<!-- .zoo.md 예시 — 프로젝트 컨텍스트 파일 -->
# SaaS 문서 자동화 플랫폼

## 기술 스택
- Next.js 14 (App Router)
- Express.js + TypeScript
- MySQL (PlanetScale)
- Zod (스키마 검증)
- Zustand (상태 관리 — Redux 금지)

## 필수 명령어
- `npm run dev` — 개발 서버 시작
- `npm run test` — 테스트 실행
- `npm run build` — 프로덕션 빌드 (반드시 `sync-pricing` 실행 후)

## 아키텍처
- `src/app/` — Next.js 페이지
- `src/routes/` — API 엔드포인트
- `src/models/` — DB 스키마 + Zod 타입
- `src/services/` — 비즈니스 로직

## 규칙
- 모든 API 응답은 Zod로 validate
- `sync-pricing` 실행 후 빌드 필수
- flat folder structure 선호 (nested directories 최소화)
```

이 파일의 크기는 200줄 이내로 제한한다 [^313^]. 200줄을 초과하면 AI의 adherence가 저하된다. 규칙이 늘어나면 `src/` 디렉토리별로 `.zoo/rules/auth.md`, `.zoo/rules/payment.md` 등으로 분리하여, 해당 파일 작업 시에만 관련 규칙을 로드한다.

`.zoo.md` 자동 로드의 구현은 간단하다:

```typescript
// .zoo.md 자동 로드 [튜닝]
// 파일: src/core/ProjectContextLoader.ts

class ProjectContextLoader {
  private cachedContext: string | null = null;
  private cacheTimestamp: number = 0;
  private readonly CACHE_TTL = 30000; // 30초

  async loadProjectContext(workspaceFolder: vscode.WorkspaceFolder): Promise<string | null> {
    const zooMdPath = path.join(workspaceFolder.uri.fsPath, '.zoo.md');
    
    if (!fs.existsSync(zooMdPath)) {
      // Fallback: .cursorrules, AGENTS.md, CLAUDE.md 순서로 탐색
      const fallbacks = ['.cursorrules', 'AGENTS.md', 'CLAUDE.md'];
      for (const fallback of fallbacks) {
        const fallbackPath = path.join(workspaceFolder.uri.fsPath, fallback);
        if (fs.existsSync(fallbackPath)) {
          return await fs.promises.readFile(fallbackPath, 'utf-8');
        }
      }
      return null;
    }

    // 캐시 확인
    const stat = await fs.promises.stat(zooMdPath);
    if (this.cachedContext && this.cacheTimestamp >= stat.mtimeMs) {
      return this.cachedContext;
    }

    // 새로 읽기 + 캐시
    const content = await fs.promises.readFile(zooMdPath, 'utf-8');
    this.cachedContext = content;
    this.cacheTimestamp = Date.now();

    return content;
  }

  // system prompt에 prepend할 형식으로 변환
  formatForInjection(content: string): string {
    return `[Project Context]\n${content}\n---\n`;
  }
}
```

주목할 점은 **호환성 fallback**이다. `.zoo.md`가 없는 프로젝트에서는 Cursor의 `.cursorrules`, Kilo Code의 `AGENTS.md`, Claude Code의 `CLAUDE.md`를 순서대로 탐색한다. 이는 Zoo Code가 기존 생태계의 표준을 존중하면서도, 자체 표준(`.zoo.md`)을 점진적으로 확산시키는 전략이다.

### 3.6.2 `arch` register 동적 편향 주입

`.zoo.md`는 **정적 규칙**이다. 하지만 프로젝트 작업 중 AI와 사용자의 상호작용에서 새로운 아키텍처 결정이 축적된다. 예를 들어 "이 프로젝트에서는 커스텀 훅을 항상 `src/hooks/`에 배치한다"는 규칙은 `.zoo.md`에 없었지만, 3회 이상의 코드 생성-승인 사이클을 통해 Crow의 `arch` register에 자동 저장된다.

이 동적 편향의 주입 메커니즘은 정적 `.zoo.md`와 결합된다:

```
[Project Context 병합 우선순위]
1. .zoo.md (정적 규칙, 사용자가 직접 작성)
2. arch register의 프로젝트 관련 항목 (동적 편향, AI가 축적)
3. bug register의 프로젝트 관련 항목 (실패 패턴, 자동 학습)
```

`arch` register의 항목이 `.zoo.md`와 충돌할 경우, `.zoo.md`가 우선한다. 사용자가 명시적으로 작성한 규칙이 AI가 추론한 편향보다 강력하다. 다만 이런 충돌이 감지되면 `crow_evolve_propose`가 충돌 해결 제안을 생성한다 — ".zoo.md의 'flat structure' 규칙과 arch의 'hooks/ 하위 디렉토리' 편향이 충돌합니다. 병합 제안: hooks/는 예외로 두는 건 어떨까요?"

### 3.6.3 `global crow.bin` + `project/.crow.bin` 계층화

Crow Memory의 저장소 구조는 두 계층으로 설계된다. **Global `crow.bin`**은 사용자 수준의 편향(`life_pref`, `life_avoid`, 개인적 선호)을 저장하고, **Project `.crow.bin`**은 프로젝트 특화 지식(`arch`, `bug`, `style`의 프로젝트 관련 항목)을 저장한다.

```
~/.zoo-code/crow/crow.bin          ← Global (사용자 편향)
/workspace/myproject/.crow.bin     ← Project (프로젝트 지식)
```

이 계층화는 다음과 같은 이점을 제공한다:

1. **프로젝트 이동 시 글로벌 편향 유지**: 사용자가 "나는 Zustand를 선호한다"는 전역 선호는 모든 프로젝트에서 공유된다.
2. **프로젝트 특화 지식의 격리**: "이 프로젝트에서는 flat structure"는 해당 프로젝트에만 적용된다.
3. **팀 공유 가능성**: `.crow.bin`은 Git에 커밋하여 팀원 간 공유할 수 있다.
4. **프라이버시 보호**: 개인적 편향(`life_pref`의 취미, 일정 관련 정보)은 Global에만 남아 팀 공유에서 제외된다.

```typescript
// 계층화된 crow.bin 병합 [튜닝]
class LayeredCrowResolver {
  async resolve(register: string, projectPath: string): Promise<CrowEntry[]> {
    // 1단계: Global crow.bin에서 회상
    const globalEntries = await crowClient.recall({
      register,
      source: 'global'
    });

    // 2단계: Project crow.bin에서 회상 (존재 시)
    const projectBinPath = path.join(projectPath, '.crow.bin');
    let projectEntries: CrowEntry[] = [];
    if (fs.existsSync(projectBinPath)) {
      projectEntries = await crowClient.recall({
        register,
        source: 'project',
        binPath: projectBinPath
      });
    }

    // 3단계: 병합 (project가 global을 덮어씀)
    const merged = this.mergeEntries(globalEntries, projectEntries);
    
    return merged;
  }

  private mergeEntries(global: CrowEntry[], project: CrowEntry[]): CrowEntry[] {
    const map = new Map<string, CrowEntry>();
    
    // Global 먼저 등록
    for (const e of global) map.set(e.id, e);
    
    // Project가 덮어씀 (같은 키가 있으면 project 우선)
    for (const e of project) map.set(e.id, e);
    
    return Array.from(map.values()).sort((a, b) => b.strength - a.strength);
  }
}
```

### 3.6.4 바이브 점수: 현재 4/10 → 목표 9/10

현재 프로젝트별 컨텍스트 자동화는 4점이다. `custom_modes.yaml`에 프로젝트 규칙을 수동으로 입력할 수 있지만, 이는 매 프로젝트마다 복사-붙여넣기 해야 하는 번거로움이 있다.

| 측면 | 현재 (4/10) | 목표 (9/10) | 주요 장애물 | 해결책 |
|------|------------|------------|------------|--------|
| 프로젝트 규칙 로드 | 수동 (`custom_modes.yaml`) | 자동 (`.zoo.md`) | 파일 존재 여부 확인 | `ProjectContextLoader` |
| 동적 편향 주입 | 없음 | `arch` register 자동 병합 | 정적/동적 충돌 | `.zoo.md` 우선순위 + 충돌 알림 |
| Global/Project 계층 | 없음 (단일 `crow.bin`) | 2계층 병합 | 글로벌 vs 로컬 구분 | `LayeredCrowResolver` |
| 호환성 | 없음 | `.cursorrules`, `AGENTS.md` fallback | 표준 분열 | 순차 탐색 전략 |
| 파일 크기 관리 | 없음 | 200줄 제한 + 분할 규칙 | 과도한 컨텍스트 | `src/`별 `.zoo/rules/*.md` |

9점에 도달하면 사용자는 새로운 프로젝트를 열었을 때, `.zoo.md`가 존재하면 자동으로 규칙이 로드되고, Crow의 `arch` register가 프로젝트의 숨겨진 편향을 주입하는 경험을 하게 된다. 1점이 모자라는 이유는, 프로젝트 컨텍스트가 100% 완벽하게 캡처되지는 않으며, 일부 규칙은 여전히 사용자의 첫 대화에서 명시되어야 할 수 있기 때문이다.

---

## 3.7 조사 차원 5: Emotional Context via Crow

### 3.7.1 거절 패턴 감지 (연속 "아니야"/"그렇게 하지 마")

당신은 Zoo Code에게 "이 컴포넌트 스타일링 해줘"라고 말했다. AI는 Tailwind CSS를 제안했다. 당신은 "아니, 나는 styled-components 써"라고 말했다. AI가 styled-components 버전을 생성했다. 하지만 이번에는 prop 전달 방식이 마음에 안 들어 "아니, 이렇게 하지 마"라고 했다. 세 번째 시도에서 AI가 다시 다른 방식을 제안했고, 당신은 "다시 해"라고 했다.

3회 연속 거절. 이것은 단순한 피드백의 반복이 아니다. 사용자의 텍스트에서 "아니야", "그렇게 하지 마", "다시 해", "이건 아니야" 같은 패턴이 연속적으로 나타나는 것은 **감정적 신호**다. 사용자는 지금 **불편함**을 느끼고 있으며, AI의 접근 방식이 사용자의 기대와 맞지 않다.

Zoo Code Extension은 이 패턴을 실시간으로 감지한다:

```typescript
// 거절 패턴 감지 엔진 [튜닝]
// 파일: src/core/EmotionalContextDetector.ts

interface RejectionPattern {
  keywords: string[];
  minConsecutiveCount: number;
  emotionalWeight: number; // 0.0 ~ 1.0
}

interface EmotionalState {
  tone: 'neutral' | 'frustrated' | 'satisfied' | 'urgent';
  confidence: number;
  rejectionStreak: number;
  lastUserMessage: string;
}

class EmotionalContextDetector {
  // 거절 키워드 사전 (한국어 + 영어)
  private rejectionPatterns: RejectionPattern[] = [
    { keywords: ['아니', '아니야', '아닌데', 'no', 'nope'], minConsecutiveCount: 2, emotionalWeight: 0.6 },
    { keywords: ['그렇게 하지 마', '하지 마', 'stop', "don't"], minConsecutiveCount: 1, emotionalWeight: 0.8 },
    { keywords: ['다시 해', '다시', 'retry', 'again'], minConsecutiveCount: 2, emotionalWeight: 0.5 },
    { keywords: ['이건 아니야', '이게 아닌데', 'wrong', 'not this'], minConsecutiveCount: 1, emotionalWeight: 0.9 },
    { keywords: ['짜증', 'annoying', 'frustrating'], minConsecutiveCount: 1, emotionalWeight: 1.0 },
  ];

  private recentUserMessages: string[] = [];
  private readonly MAX_HISTORY = 5;
  private consecutiveRejections: number = 0;

  // 매 user 메시지 입력 시 호출
  analyze(message: string): EmotionalState {
    this.recentUserMessages.push(message);
    if (this.recentUserMessages.length > this.MAX_HISTORY) {
      this.recentUserMessages.shift();
    }

    const isRejection = this.checkRejection(message);
    if (isRejection) {
      this.consecutiveRejections++;
    } else {
      this.consecutiveRejections = 0;
    }

    // 감정 상태 추론
    let tone: EmotionalState['tone'] = 'neutral';
    let confidence = 0.0;

    if (this.consecutiveRejections >= 3) {
      tone = 'frustrated';
      confidence = Math.min(1.0, this.consecutiveRejections * 0.25);
    } else if (this.consecutiveRejections >= 1) {
      tone = 'urgent';
      confidence = this.consecutiveRejections * 0.3;
    } else if (this.isPositiveFeedback(message)) {
      tone = 'satisfied';
      confidence = 0.6;
    }

    return {
      tone,
      confidence,
      rejectionStreak: this.consecutiveRejections,
      lastUserMessage: message
    };
  }

  private checkRejection(message: string): boolean {
    const lowerMsg = message.toLowerCase();
    return this.rejectionPatterns.some(pattern =>
      pattern.keywords.some(kw => lowerMsg.includes(kw.toLowerCase()))
    );
  }

  private isPositiveFeedback(message: string): boolean {
    const positive = ['좋아', '굿', 'good', 'thanks', 'perfect', 'exactly', 'great'];
    return positive.some(p => message.toLowerCase().includes(p));
  }

  // 거절 스트reak이 임계값 도달 시 호출
  shouldAdjustApproach(streak: number): boolean {
    return streak >= 3;
  }
}
```

이 감지 엔진은 **프라이버시를 침해하지 않는다**. 사용자의 메시지는 이미 AI에게 전달되는 것이며, Extension은 이 메시지의 텍스트 패털만을 로컬에서 분석한다. 외부 서버로 전송되지 않으며, 분석 결과도 사용자의 기기 내에만 저장된다.

### 3.7.2 `life_avoid` register 저장

3회 연속 거절이 감지되면, Extension은 자동으로 `crow_ingest`를 호출하여 `life_avoid` register에 이 패턴을 저장한다.

```typescript
// 거절 패턴 저장 [MCP]
async function storeRejectionPattern(
  detector: EmotionalContextDetector,
  context: ConversationContext
): Promise<void> {
  const state = detector.getCurrentState();
  
  if (state.rejectionStreak >= 3) {
    // 거절의 맥락을 분석하여 구체적 회피 규칙 생성
    const rejectionContext = analyzeRejectionContext(context);
    
    await crowClient.call('crow_ingest', {
      content: `Approach rejected: ${rejectionContext.approach}. ` +
               `User prefers: ${rejectionContext.inferredPreference}`,
      register: 'life_avoid',
      metadata: {
        polarity: -2.0,           // 최고 수준의 부정 편향
        tags: ['rejection', 'emotional_signal', rejectionContext.topic],
        source: 'auto_detected',
        rejectionCount: state.rejectionStreak,
        timestamp: Date.now()
      }
    });

    // 접근 방식 자동 조정
    await adjustAIApproach(state);
  }
}

// 접근 방식 자동 조정
async function adjustAIApproach(state: EmotionalState): Promise<void> {
  switch (state.tone) {
    case 'frustrated':
      // 제안 방식 → 질의 방식 전환
      contextInjector.setToneModifier(
        'The user has rejected multiple suggestions. ' +
        'Instead of proposing solutions, ask clarifying questions. ' +
        'Wait for explicit confirmation before implementing.'
      );
      break;
    case 'urgent':
      // 자동 실행 → HITL 승인 요구
      yoloMode.setRequireApproval(true);
      break;
  }
}
```

`polarity=-2.0`은 Crow Memory의 **명시적 부정 강화** 메커니즘이다 [^386^]. 이 polarity는 해당 메모리의 감쇠 속도를 가속시킨다 — 일반적인 단기 메모리(λ=0.95)는 14회 반복 후 50%가 남지만, polarity=-2.0의 항목은 훨씬 빠르게 망각된다. 이는 "사용자가 지금 화났으니 이 방식을 계속 피핸라"가 아니라, "이 상황에서는 이 방식이 맞지 않았다"는 **상황-특화적 학습**을 의미한다.

### 3.7.3 `polarity=-2.0` 축적 → 사전 경고

`life_avoid` register에 저장된 거절 패턴이 유사한 상황에서 재발될 때, Crow는 **사전 경고**를 생성한다.

예를 들어: 사용자가 이전에 "React Query 없이 fetch 직접 쓰는 방식"을 3회 거절했다면, `life_avoid`에는 `"Approach rejected: direct fetch without React Query. User prefers: React Query with proper caching"`이 polarity=-2.0으로 저장된다. 이후 사용자가 새로운 엔드포인트를 요청할 때, AI가 fetch 직접 사용을 제안하려 하면 Crow가 사전 경고를 생성한다:

```
[사전 경고 메시지 — Crow 자동 생성]
⚠️ 이 접근 방식은 과거에 사용자로부터 거절당했습니다.
   상황: 2025-07-10, auth API 리팩토링 시 3회 거절
   거절된 방식: direct fetch without caching
   사용자 선호: React Query with caching
   
   계속하시겠습니까? [대안 보기] [무시하고 진행]
```

이 사전 경고는 바이브를 깨지 않는 방식으로 표시되어야 한다. 모달 대화상자가 아니라, 코드 제안의 인라인 주석이나, 상태바의 부드러운 알림으로. 사용자가 "대안 보기"를 선택하면, Crow의 `life_pref` register에서 사용자가 선호하는 방식(React Query)을 회상하여 대안 코드를 생성한다.

### 3.7.4 바이브 점수: 현재 2/10 → 목표 8/10

현재 emotional context 인식은 2점이다. Zoo Code는 사용자의 감정 상태를 전혀 인식하지 못하며, 연속 거절에도 동일한 접근 방식을 고집한다.

| 측면 | 현재 (2/10) | 목표 (8/10) | 주요 장애물 | 해결책 |
|------|------------|------------|------------|--------|
| 감정 신호 감지 | 없음 | 연속 거절 패턴 실시간 감지 | 텍스트 감정 분석의 오탐 | 다중 키워드 + 연속 횟수 임계값 |
| 접근 방식 변경 | 없음 | 자동 톤/승인 수준 조정 | 과도한 조정이 오히려 불편 | 3회 임계값, 점진적 조정 |
| `life_avoid` 저장 | 없음 | 거절 패턴 자동 ingest | 거절의 원인 분석 불확실 | 거절 맥락(이전 제안) 함께 저장 |
| 사전 경고 | 없음 | 유사 상황에서 경고 생성 | 너무 빈번한 경고는 노이즈 | strength 축적 임계값(3회 이상만) |
| 감정 톤 복원 | 없음 | 긍정 피드백 시 톤 복원 | 복원 시점 판단 | "좋아", "굿" 등 긍정 키워드 감지 |

8점에 도달하면 AI가 사용자의 연속 거절을 인식하고 접근 방식을 자동으로 변경하며, 과거의 거절 패턴을 사전에 회피하는 경험을 하게 된다. 2점이 모자라는 이유는, **감정의 정밀한 분류**는 매우 어려운 과제이며, "기쁨/슬픔/분노" 같은 세밀한 감정보다는 "만족/불만족/긴급" 같은 거친 분류에 머무를 것이기 때문이다. 또한, 감정 인식이 항상 정확하지는 않으며, 오탐으로 인해 불필요하게 조심스러운 AI 행동이 될 수 있다는 현실적 제약이 존재한다.

---

## 3.8 Wave 3 사용자 경험 스토리

### 3.8.1 "'저번처럼'이라고만 했다. AI가 알아들었다."

---

**스토리 1: 세션을 넘어선 기억 — 민지의 월요일 아침**

민지는 금요일 밤, Zoo Code와 함께 결제 모듈의 JWT 인증 리팩토링을 하다가 중간에 멈췄다. `payment/controller.ts`의 `verifyToken` 함수가 완성되지 않은 채로, 주석만 덩그러니 남아 있었다.

월요일 아침, 민지는 VS Code를 켰다. Zoo Code Extension이 활성화되고, 상태바의 인디케이터가 잠시 깜빡이더니 "Crow Context: 82% fresh"로 안정되었다. 민지는 채팅창에 이렇게 입력했다:

> "저번처럼 마무리해줘"

7글자. 아무 설명도 없었다.

Zoo Code의 Context Injection Engine은 자동으로 작동했다. `life_context` register에서 금요일 세션의 요약을 회상했다 — "JWT 인증 리팩토링, `verifyToken` 함수 미완성, refresh token rotation 추가 필요". `arch` register에서는 이 프로젝트의 인증 아키텍처를 확인했다 — "Zod validate + 422 return, `src/services/auth.ts`에 비즈니스 로직 분리". `life_pref`에서는 민지의 선호를 확인했다 — "async/await 사용, any 타입 금지".

Zoo Code의 응답:

> "금요일의 JWT 인증 리팩토링을 이어서 하겠습니다. `verifyToken` 함수에 refresh token rotation을 추가하고, Zod로 validate해서 422를 리턴하는 방식으로 마무리할게요. `src/services/auth.ts`에 비즈니스 로직을 분리하겠습니다."

민지는 아무것도 설명하지 않았다. AI가 이미 알고 있었다.

---

**스토리 2: 멀티에이전트의 침묵하는 동기화 — 현수의 팀 협업**

현수는 팀에서 백엔드를 담당한다. 동료인 수진은 프론트엔드를 담당하며 Kimi Code를 사용한다. 현수는 Zoo Code를 사용한다.

현수가 Zoo Code로 "새로운 주문 API 엔드포인트 만들어줘"라고 요청했다. AI가 코드를 생성했다:

```typescript
// AI가 생성한 코드
app.post('/api/orders', validateOrder, async (req, res) => {
  const order = await createOrder(req.body);
  res.json({ data: order, meta: { page: 1, limit: 20, total: 1 } });
});
```

현수는 만족했다. "좋아, 이대로 가자"라고 말했다.

이 대화의 핵심 정보 — "응답 형식은 `{ data, meta }` 구조", "validate 후 422 리턴" — 가 Crow의 `arch` register에 자동 저장되었다. `crow_evolve_propose`가 `"API 응답 형식 규칙"`을 제안했고, 현수는 QuickPick에서 "승인"을 눌렀다. 규칙이 `.zoo/system_prompt.md`에 추가되고 Git push되었다.

다음 날, 수진은 Kimi Code를 켰다. 프로젝트를 열자마자 `system_prompt.md`가 자동으로 로드되었다. 수진이 Kimi Code로 "주문 목록 API 호출하는 컴포넌트 만들어줘"라고 요청했을 때, Kimi Code는 이미 알고 있었다 — "API 응답은 `{ data, meta }` 구조로 오니까, `meta.total`을 사용해서 페이지네이션을 구현해야겠구나."

현수와 수진은 서로 말하지 않았다. 두 AI가 Crow를 통해 침묵 속에서 대화한 것이다.

---

**스토리 3: 감정을 읽는 AI — 다영의 오후**

다영은 Zoo Code에게 "이 컴포넌트 디자인 해줘"라고 말했다. AI는 첫 번째 시도에서 Tailwind를 사용했다. 다영은 "아니, styled-components로 해줘"라고 말했다. AI가 styled-components로 변경했다. 하지만 prop 전달 방식이 마음에 안 들어 "그렇게 하지 마"라고 했다. 세 번째 시도도 마음에 안 들어 "다시 해"라고 했다.

3회 연속 거절.

Zoo Code Extension의 EmotionalContextDetector가 이 패턴을 감지했다. `life_avoid` register에 `"3회 거절: styled-components prop drilling 방식. 사용자가 직접 스타일 정의를 선호할 가능성 있음"`이 polarity=-2.0으로 저장되었다. 동시에 AI의 접근 방식이 자동으로 변경되었다 — 제안 방식에서 질의 방식으로.

네 번째 응답:

> "죄송합니다. 어떤 방식으로 styled-components를 사용하는 것을 선호하시나요? prop 전달, theme provider, 아니면 CSS-in-JS의 다른 패턴을 원하시나요?"

다영은 잠시 놀랐다. AI가 "알아서" 바뀐 것이다. 다영은 "theme provider로 하고, CSS 변수는 `src/styles/vars.ts`에 정의해줘"라고 답했다. 이번에는 1회 만에 만족스러운 결과를 얻었다.

그리고 다음에 다영이 "스타일링 해줘"라고 말했을 때, AI는 더 이상 prop drilling을 제안하지 않았다. `life_avoid`의 축적된 데이터가 사전 경고를 생성했기 때문이다 — "이 사용자는 styled-components 사용 시 prop drilling을 선호하지 않음. theme provider 방식 우선 제안."

---

## 3.9 Wave 3 기술적 구현 체크리스트

다음은 Wave 3(Zero-Explanation)의 모든 기술적 구현 항목을 담은 체크리스트이다. 각 항목은 [튜닝](Zoo Code Extension 소스 직접 수정) 또는 [MCP](Crow Memory MCP 서버 도구 추가)로 태깅되며, 추정 구현 소요 기간(주 단위)이 포함된다.

| # | 구현 항목 | 태그 | 소요기간 | 의존항목 | 검증 기준 |
|---|----------|------|---------|---------|----------|
| 1 | `ContextInjector` 클래스 구현: 매 턴 `crow_recall` 자동 호출 | [튜닝] | 1주 | Wave 1 인프라 | 모든 턴에 `[User Context]`가 system prompt에 포함됨 |
| 2 | `FallbackInjector` 클래스 구현: 4B 모델 지시 무시 시 강제 주입 | [튜닝] | 2주 | #1 | Llama 3.2 3B에서도 95%+ 주입 성공률 |
| 3 | `CrowMmapCache` 또는 page cache 읽기 구현 | [튜닝] | 1주 | #1 | SSE 호출 횟수 80% 감소 |
| 4 | 중복 주입 방지: `globalState` 해시 기반 캐싱 | [튜닝] | 0.5주 | #1 | 동일 컨텍스트 2회 이상 주입되지 않음 |
| 5 | `SessionPersistence` 클래스: 세션 요약 `globalState` 저장 | [튜닝] | 1주 | #1 | 50KB/세션 용량 제약 내 저장 |
| 6 | 세션 종료 시 `crow_compact()` 자동 호출 | [MCP] | 1주 | #5 | `deactivate()` 훅에서 compaction 실행 |
| 7 | `life_context` register에 세션 요약 자동 ingest | [MCP] | 0.5주 | #6 | 다음 세션에서 요약 회상 가능 |
| 8 | 상태바 "Crow Context: X% fresh" 인디케이터 | [튜닝] | 0.5주 | #6 | 상태바에 freshness 표시, 색상 변화 |
| 9 | `system_prompt.md` HITL 승인 파이프라인 | [튜닝] | 2주 | — | QuickPick 승인/거부/수정 UI |
| 10 | `crow_evolve_propose` 통합: 규칙 후보 자동 생성 | [MCP] | 1주 | #9 | 70%+ confidence 후보 생성 |
| 11 | Git 자동 동기화: `system_prompt.md` 커밋 + push | [튜닝] | 0.5주 | #9 | Git push 성공/실패 graceful 처리 |
| 12 | `fs.watch` 자동 reload: 규칙 변경 시 실시간 반영 | [튜닝] | 0.5주 | #9, #11 | 파일 수정 후 1초 내 반영 |
| 13 | `.zoo.md` 자동 로드: 프로젝트 컨텍스트 prepend | [튜닝] | 1주 | — | `.zoo.md` 존재 시 자동 로드 |
| 14 | `.cursorrules`, `AGENTS.md`, `CLAUDE.md` 호환 fallback | [튜닝] | 0.5주 | #13 | 관련 파일 자동 탐색 |
| 15 | `arch` register 동적 편향 주입 | [MCP] | 1주 | #13 | 프로젝트 관련 동적 규칙 병합 |
| 16 | Global + Project `crow.bin` 계층화 | [MCP] | 1.5주 | #15 | 글로벌/프로젝트 편향 분리 저장 |
| 17 | `EmotionalContextDetector`: 연속 거절 패턴 감지 | [튜닝] | 1.5주 | — | 3회 연속 거절 90%+ 감지율 |
| 18 | `life_avoid` 자동 저장: 거절 시 `polarity=-2.0` ingest | [MCP] | 0.5주 | #17 | 거절 3회 시 자동 저장 |
| 19 | 접근 방식 자동 변경: 톤/승인 수준 조정 | [튜닝] | 1주 | #17, #18 | 거절 시 제안→질의 전환 |
| 20 | 사전 경고: `life_avoid` 축적 시 유사 상황 경고 | [MCP] + [튜닝] | 1.5주 | #18 | 유사 상황에서 경고 메시지 생성 |
| 21 | 상태바 freshness 계산: 복합 지표 구현 | [튜닝] | 0.5주 | #6, #8 | recency + relevance + coverage + confidence |
| 22 | `ProjectContextLoader` 캐싱: 30초 TTL | [튜닝] | 0.5주 | #13 | 파일 변경 시에만 재로드 |
| 23 | 세션 요약 형식 표준화: compaction output 포맷 | [MCP] | 0.5주 | #6 | 모든 요약이 동일한 구조로 생성 |
| 24 | 멀티에이전트 충돌 감지: `arch` vs `.zoo.md` 규칙 충돌 알림 | [튜닝] | 1주 | #9, #15 | 충돌 시 QuickPick으로 해결 제안 |
| 25 | 감정 복원: 긍정 피드백 시 톤 복원 | [튜닝] | 0.5주 | #17, #19 | "좋아", "굿" 등 감지 시 톤 복원 |

**총 추정 기간**: 21.5주 (약 5개월)의 병렬화 가능 항목을 고려하면 **약 8주(2개월)**로 압축 가능하다. Wave 1(4주)과 Wave 2(6주)의 인프라 위에 구축되므로, 전체 프로젝트 일정으로는 **약 18주(4.5개월)** 시점에 Wave 3이 완성된다.

**핵심 의존성 경로**: #1(ContextInjector) → #2(FallbackInjector) → #6(crow_compact) → #7(life_context ingest) → #17(EmotionalDetector). 이 경로는 순차적이며, 병렬화가 불가능한 핵심 체인이다. 나머지 항목은 이 체인의 완성과 무관하게 병렬 개발 가능하다.

**Crow Memory 연동 요약**:

| Wave 3 단계 | 주요 Crow 도구 | 업데이트되는 레지스터 |
|------------|--------------|---------------------|
| Implicit Context | `crow_recall(domain="all")` | — (읽기 전용) |
| Cross-Session | `crow_compact()`, `crow_ingest` | `life_context` |
| Multi-Agent Sync | `crow_evolve_propose()` | `system_prompt.md` (파일) |
| Project Context | `crow_recall(register="arch")` | `arch`, `bug`, `style` |
| Emotional Context | `crow_ingest(register="life_avoid")` | `life_avoid` (`polarity=-2.0`) |

Wave 3가 완성되면 Zoo Code는 "사용자가 설명하지 않아도 아는" 도구가 된다. 이것이 Zero-Explanation Coding의 본질이다 — AI가 사용자의 신경계 연장체가 되는 순간, 사용자는 AI의 존재를 의식하지 않는다. 그저 코딩의 흐름이 이어질 뿐이다.


---

## 4. Wave 4: Orchestra of One — Parallel Vibe Engineer의 5차원 병렬화

당신은 3시간 집중 코딩 세션의 한가울데 있다. 메인 AI 에이전트가 현재 파일의 리팩토링을 진행하는 동안, 당신은 속으로 "이 프로젝트에서 우리가 사용하는 에러 핸들링 패턴이 뭐였더라"고 생각한다. 과거라면 메인 에이전트에게 물어봐야 했고, 그것은 현재 진행 중이던 리팩토링 흐름이 끊겼음을 의미한다. 하지만 지금은 다르다. 당신은 채팅 입력창에 `@scout 에러 핸들링 패턴 찾아줘`라고 타이핑한다. 메인 AI는 멈추지 않는다. Scout라는 이름의 서브에이전트가 백그라운드에서 깨어나 프로젝트 전체를 샅샅이 뒤지기 시작한다. 30초 후, Explorer 패널의 "Zoo Orchestra" 대시보드에 Scout의 상태가 "completed"로 바뀐다. 그와 동시에 메인 AI의 다음 응답 속에 — 아묟 설명 없이, 아묟 인터럽션 없이 — "이 프로젝트에서는 try/catch 대신 Result<T,E> 패턴을 사용하며, crow_recall로 확인한 바에 따륩..."이라는 문장이 자연스럽게 흘러나온다. 당신은 Scout가 존재하는지조차 의식하지 않는다. 이것이 Wave 4가 추구하는 **Orchestra of One**의 바이브다.

Wave 4는 Zoo Code를 "한 명의 AI 동반자"에서 "VS Code 내에서 조화롭게 연주하는 여러 AI의 오케스트라"로 진화시키는 단계다. 이전 Wave 1~3에서 세션 지속성, YOLO 안전망, Zero-Explanation 컨텍스트 관리를 구축했다면, Wave 4는 이 모든 기반 위에서 **병렬 처리의 차원**을 추가한다. 단순히 여러 AI를 동시에 실행하는 것이 아니라 — 사용자가 그 존재조차 의식하지 않는, 흐름 속에 자연스럽게 녹아드는 병렬화를 설계한다. 본 장에서는 VS Code Extension API의 제약 속에서 5가지 차원의 병렬화를 구현하는 기술적 설계를 제시하며, 각 차원의 현재 바이브 점수와 목표 점수, 그리고 Crow Memory와의 연동 포인트를 상세히 분석한다.

---

### 4.1 "Orchestra of One within VS Code" 아키텍처 다이어그램

Wave 4의 핵심 아키텍처는 **Hub-and-Spoke** 패턴을 변형한 "Orchestra of One" 구조다. Claude Code의 Agent Teams [^445^]와 Kilo Code의 Agent Manager [^357^]가 별도의 터미널이나 풀패널 에디터를 통해 멀티에이전트를 관리하는 것과 달리, Zoo Code는 **VS Code Extension Host 낶, 그리고 그 직외의 별도 프로세스**라는 두 개의 공간에 걸쳐 오케스트라를 펼친다. 이는 VS Code Extension API의 단일 스레드 제약 [^162^]을 존중하면서도 병렬성을 확보하기 위한 아키텍처적 타협이다.

#### 4.1.1 Main Agent → Subagents (별도 MCP 서버) → Crow SSE Server (lock manager) → `crow.bin`

오케스트라의 지휘대는 VS Code Extension Host 낶의 **Main Agent(주 에이전트)**가 담당한다. Main Agent는 사용자의 직접적인 대화 상대로서 모든 요청의 첫 진입점이 되며, 각 요청의 성격을 판단하여 자신이 처리할 것인지, 아니면 특정 Subagent에게 위임할 것인지를 결정한다. 여기서의 핵심 원칙은 **"사용자는 Main Agent와만 대화한다"**는 것이다. Subagent의 존재는 사용자에게 노출되지 않으며, 오직 작업의 결과만이 Main Agent를 통해 자연스럽게 흘러들어온다.

Subagent들은 **별도의 MCP 서버**로 구현된다. 예를 들어 Scout(코드 탐색 전문), Reviewer(코드 리뷰 전문), Tester(테스트 생성 전문) 등의 역할별 Subagent가 각각 독립된 MCP 서버 프로세스로 실행된다 [^446^]. 이들은 VS Code Extension Host와 별도의 Node.js 프로세스 또는 Python 프로세스로 띄워지며, Extension Host의 단일 스레드 제약으로부터 자유롭게 CPU 집약적인 작업을 수행할 수 있다. 각 Subagent MCP 서버는 고유한 포트(예: Scout는 9022, Reviewer는 9023)에서 SSE transport로 대기하며, Main Agent가 특정 작업을 위임할 때만 잠시 연결되어 작업을 수행하고 결과를 반환한다 [^225^]. 이 구조는 MCP의 기본 3계층 아키텍처(Host-Client-Server)를 그대로 활용하는 것으로, 별도의 커스텀 프로토콜 없이 표준 MCP 스펙만으로 멀티에이전트 통신을 실현한다 [^253^] [^280^].

모든 Subagent와 Main Agent의 공통 분모는 **Crow SSE Server(9020 포트)**다. Crow 서버는 이 오케스트라의 "악보 보관소"이자 "충돌 중재자" 역할을 동시에 수행한다. 각 에이전트가 작업을 시작할 때 `crow_recall`로 프로젝트의 현재 맥락을 읽고, 작업을 마칠 때 `crow_ingest`로 결과를 저장하는 일관된 메모리 인터페이스를 제공한다. 더 중요한 것은, Crow 서버가 **중앙 잠금 관리자(Central Lock Manager)**의 역할을 겸한다는 점이다. Beads Village [^368^]나 Agent Orchestration MCP Server [^438^]에서 제안된 MCP 기반 잠금 관리 패턴을 차용하여, 두 Subagent가 동일 파일에 동시에 쓰기를 시도할 경우 Crow 서버가 이를 큐잉하고 순차적으로 처리함으로써 데이터 충돌을 원천 방지한다. 이 잠금 정보는 `crow.bin`에 실시간으로 기록되며, 모든 에이전트가 `lock_check` tool을 통해 현재 잠금 상태를 조회할 수 있다.

`crow.bin`은 오케스트라의 **영구 기억 저장소**다. MemGPT 스타일의 레지스터 기반 메모리 구조 [^366^]를 따륾며, `context`/`life_context`(단기), `arch`/`bug`/`style`(장기), `life_avoid`/`life_pref`(사용자 편향)의 7개 레지스터를 통해 모든 에이전트의 작업 결과가 축적된다. Subagent A가 탐색한 아키텍처 패턴은 `arch` 레지스터에 저장되고, Subagent B가 발견한 버그는 `bug` 레지스터에 저장된다. 이 모든 기억은 Main Agent의 다음 응답에서 `crow_recall`로 자연스럽게 회상되어, 사용자에게는 "모든 AI가 하나의 뇌를 공유하는" 것처럼 느껴진다.

오케스트라 아키텍처의 데이터 흐름을 요약하면 다음과 같다:

```
[사용자] ←→ [Main Agent] ←→ [VS Code Extension Host]
                    ↕ (MCP stdio/SSE)
        [Subagent: Scout @ 9022] — crow_recall/ingest → [Crow SSE Server @ 9020]
        [Subagent: Reviewer @ 9023] — crow_recall/ingest → ↑
        [Subagent: Tester @ 9024] — crow_recall/ingest → ↑
                    ↕
                [crow.bin] (공유 메모리 저장소)
```

Main Agent는 Extension Host 낶에서 사용자와 직접 대화하고, 작업 위임이 필요할 때 각 Subagent의 MCP 서버로 JSON-RPC 2.0 요청을 본낸다. Subagent들은 작업 수행 중 Crow 메모리에 접근하여 컨텍스트를 공유하고, 결과를 Crow에 저장하여 Main Agent가 이후 회상할 수 있게 한다. 이 구조에서 Crow SSE Server는 단순한 메모리 서버를 넘어 **분산 잠금 관리자(Distributed Lock Manager)**의 역할을 수행하며, 병렬 작업의 데이터 일관성을 보장한다.

이 아키텍처의 핵심 설계 철학은 **"Extension Host 낶의 완전한 제어"와 "Host 외부의 완전한 자유"의 분리**다. Main Agent가 사용자와의 인터랙션을 완전히 통제하는 한편, Subagent들은 CPU 집약적인 작업에 대해 Extension Host의 제약으로부터 항방된 공간에서 자유롭게 실행된다. 이 분리는 VS Code Extension API의 `child_process.spawn` [^175^]과 MCP의 transport 추상화 [^245^]라는 두 가지 표준 메커니즘을 통해 실현되며, 별도의 커스텀 프로토콜이나 외부 런타임에 대한 의존 없이 순수하게 VS Code 생태계 내에서 구현 가능하다.

---

### 4.2 Subagent 구현 기술 명세

Subagent를 VS Code Extension Host 내에서 구현하는 것은 기술적으로 불가능하지 않으나, **확장성과 안정성 측면에서 권장되지 않는다.** Extension Host는 단일 Node.js 프로세스로 모든 확장 프로그램을 실행하며, V8 heap limit(일반적으로 ~2GB)이 적용된다 [^162^] [^172^]. CPU 집약적인 Subagent 작업(코드 탐색, 대규모 리팩토링 분석 등)을 Extension Host 낶에서 실행하면 UI 응답성 저하, 심지어 Extension Host의 watchdog 재시작 [^162^]까지 초래할 수 있다. 따라서 Subagent는 반드시 Extension Host 외부의 별도 프로세스로 실행되어야 한다.

#### 4.2.1 Web Worker / LSP / 별도 Node 프로세스 활용

Subagent의 물리적 실행 환경으로는 세 가지 옵션이 있으며, 각각의 트레이드오프를 분석 기반으로 평가한다.

첫째, **Node.js Worker Threads** [^197^]는 Extension Host와 동일한 프로세스 내에서 독립된 V8 isolate를 생성하는 방식이다. 각 Worker는 약 10MB의 메모리 오버헤드를 가지며, 메인 스레드와 `postMessage`를 통한 메시지 패싱으로 통신한다. 이 방식의 장점은 프로세스 생성 비용이 낮고(약 35ms), `SharedArrayBuffer`를 통한 zero-copy 데이터 공유가 가능하다는 점이다. 단점은 여전히 동일 Extension Host 프로세스 내에 있어 heap limit을 공유한다는 점이다. 짧고 가벼운 작업(예: 단일 파일의 정적 분석)에 적합하다.

둘째, **Language Server Protocol(LSP) 서버** [^163^]는 VS Code의 표준 언어 도구 인프라를 활용하는 방식이다. Subagent를 LSP 서버로 구현하면 VS Code가 자동으로 별도 프로세스로 관리해주며, 표준화된 JSON-RPC 기반 통신 프로토콜을 통해 Extension과 손쉽게 연동할 수 있다. LSP 서버는 표준 입출력(stdio) 또는 소켓으로 통신하며, VS Code의 `LanguageClient` 클래스가 모든 프로세스 생명주기를 관리한다. 이 방식의 장점은 VS Code가 이미 검증된 프로세스 관리 인프라를 제공한다는 점이지만, Subagent가 LSP의 `textDocument/*` 메시징 패턴에 얽매일 수 있다는 단점이 있다.

셋째, **별도 Node 프로세스(`child_process.spawn`)** [^175^] [^176^]는 가장 유연한 방식이다. Extension Host가 완전히 독립된 Node.js 프로세스를 생성하여 Subagent를 실행하며, `detached: true` 옵션으로 VS Code 종료 후에도 Subagent 프로세스가 생존할 수 있다. 이 방식의 장점은 완전한 프로세스 격리, 독립된 메모리 공간, 그리고 Python 기반 MCP 서버와의 직접 통신이 가능하다는 점이다. 단점은 프로세스 생성 비용이 Worker Thread보다 높고(수백 ms), 프로세스 간 통신 오버헤드가 추가된다는 점이다. **Wave 4의 Subagent 구현에서는 이 방식을 기본으로 채택**하되, 가벼운 작업에는 Worker Thread를, VS Code 네이티브 통합이 필요한 작업에는 LSP 서버를 선택적으로 활용하는 하이브리드 전략을 사용한다.

아래는 Subagent 프로세스 생성의 의사코드다. [튜닝]

```typescript
// subagentManager.ts — VS Code Extension Host 내의 Subagent 관리자
import { spawn, ChildProcess } from 'child_process';
import * as vscode from 'vscode';
import * as path from 'path';

interface SubagentConfig {
    name: string;           // "scout", "reviewer", "tester"
    port: number;           // 9022, 9023, 9024
    scriptPath: string;     // scout_mcp_server.py 등
    maxIdleTimeMs: number;  // 5분 idle 후 자동 종료
}

class SubagentManager {
    private processes: Map<string, ChildProcess> = new Map();
    private lastActivity: Map<string, number> = new Map();
    private idleTimers: Map<string, NodeJS.Timeout> = new Map();

    // [튜닝] Subagent MCP 서버 프로세스를 spawn
    async spawnSubagent(config: SubagentConfig): Promise<number> {
        if (this.processes.has(config.name)) {
            // 이미 실행 중인 프로세스 재사용
            this.lastActivity.set(config.name, Date.now());
            return config.port;
        }

        // Python MCP 서버를 별도 프로세스로 실행
        // stdio를 완전히 분리(detach)하여 VS Code 종료와 독립
        const child = spawn('python', [config.scriptPath, '--port', String(config.port)], {
            detached: true,                    // VS Code와 프로세스 분리
            stdio: ['ignore', 'pipe', 'pipe'], // stdout/stderr는 로그 수집용
            env: {
                ...process.env,
                CROW_SERVER_URL: 'http://localhost:9020',
                SUBAGENT_NAME: config.name,
            },
        });

        child.unref(); // 부모 이벤트 루프에서 제거, VS Code 종료 시 zombie 방지

        this.processes.set(config.name, child);
        this.lastActivity.set(config.name, Date.now());

        // [튜닝] 프로세스 stdout/stderr를 VS Code OutputChannel로 리다이렉션
        const outputChannel = vscode.window.createOutputChannel(`Zoo Subagent: ${config.name}`);
        child.stdout?.on('data', (data) => outputChannel.append(data.toString()));
        child.stderr?.on('data', (data) => outputChannel.append(data.toString()));

        // [튜닝] idle 타이머 설정 — 5분간 사용 없으면 자동 종료
        this.resetIdleTimer(config);

        // 프로세스 종료 감시
        child.on('exit', (code) => {
            console.log(`Subagent ${config.name} exited with code ${code}`);
            this.processes.delete(config.name);
            this.lastActivity.delete(config.name);
        });

        // 서버가 준비될 때까지 최대 10초 대기 (health check)
        await this.waitForServerReady(config.port, 10000);

        return config.port;
    }

    // [튜닝] idle 타이머 리셋 — 작업이 할당될 때마다 호출
    private resetIdleTimer(config: SubagentConfig): void {
        const existing = this.idleTimers.get(config.name);
        if (existing) clearTimeout(existing);

        const timer = setTimeout(() => {
            const last = this.lastActivity.get(config.name) || 0;
            if (Date.now() - last > config.maxIdleTimeMs) {
                this.terminateSubagent(config.name);
            }
        }, config.maxIdleTimeMs);

        this.idleTimers.set(config.name, timer);
    }

    // [튜닝] Subagent 프로세스 종료
    async terminateSubagent(name: string): Promise<void> {
        const child = this.processes.get(name);
        if (!child) return;

        // SIGTERM으로 우아하게 종료 요청
        child.kill('SIGTERM');

        // 5초 내 종료되지 않으면 SIGKILL
        await new Promise<void>((resolve) => {
            const forceKill = setTimeout(() => {
                child.kill('SIGKILL');
                resolve();
            }, 5000);
            child.on('exit', () => {
                clearTimeout(forceKill);
                resolve();
            });
        });

        this.processes.delete(name);
    }

    // 서버 health check (간단한 HTTP ping)
    private async waitForServerReady(port: number, timeoutMs: number): Promise<void> {
        const deadline = Date.now() + timeoutMs;
        while (Date.now() < deadline) {
            try {
                const resp = await fetch(`http://localhost:${port}/health`);
                if (resp.ok) return;
            } catch { /* not ready yet */ }
            await new Promise(r => setTimeout(r, 100));
        }
        throw new Error(`Subagent server on port ${port} failed to start within ${timeoutMs}ms`);
    }
}
```

이 의사코드의 핵심은 `detached: true`와 `child.unref()`의 조합이다. `detached: true`는 자식 프로세스를 부모의 프로세스 그룹에서 분리하여, VS Code가 종료되더라도 SIGINT/SIGTERM이 자식에게 전파되지 않도록 한다 [^176^]. `child.unref()`는 부모 이벤트 루프에서 자식 프로세스의 참조를 제거하여, VS Code 종료 시 자식이 부모의 생명주기에 묶이지 않도록 한다. 그러나 VS Code의 특수한 프로세스 관리 방식으로 인해 완전한 분리가 어려울 수 있으므로 [^180^], `stdio`를 완전히 분리하는 것이 필수적이다.

#### 4.2.2 `scout_mcp_server.py`를 9022 포트로 실행

각 Subagent는 Python FastMCP SDK [^229^] [^251^]로 구현된 독립 MCP 서버다. Scout Subagent를 예로 들면, 다음과 같은 구조를 가진다. [MCP]

```python
# scout_mcp_server.py — 코드 탐색 전문 Subagent MCP 서버
from fastmcp import FastMCP
import asyncio
import sys
import argparse

# FastMCP 인스턴스 생성 — "scout"라는 이름의 MCP 서버
mcp = FastMCP(name="scout")

@mcp.tool
def search_codebase(query: str, file_patterns: list[str] = None, max_results: int = 10) -> dict:
    """
    프로젝트 코드베이스에서 주어진 쿼리와 관련된 코드를 검색합니다.
    
    Args:
        query: 검색할 내용 (자연어 또는 코드 스니펫)
        file_patterns: 검색 대상 파일 패턴 (예: ["*.ts", "*.tsx"])
        max_results: 최대 결과 수
    
    Returns:
        검색 결과: 파일 경로, 라인 번호, 관련 코드 스니펫, 관련도 점수
    """
    # 실제 구현: ripgrep 또는 tree-sitter 기반 코드 검색
    results = perform_code_search(query, file_patterns, max_results)
    return {
        "results": [
            {
                "file": r.file_path,
                "line": r.line_number,
                "snippet": r.code_snippet,
                "score": r.relevance_score,
            }
            for r in results
        ],
        "total_found": len(results),
    }

@mcp.tool
def find_references(symbol: str, include_tests: bool = False) -> dict:
    """
    주어진 심벌(함수, 클래스, 변수)의 모든 참조를 찾습니다.
    
    Args:
        symbol: 찾을 심벌 이름
        include_tests: 테스트 파일 포함 여부
    """
    refs = find_all_references(symbol, include_tests)
    return {"symbol": symbol, "references": refs}

@mcp.tool
def summarize_architecture(target_path: str = ".") -> str:
    """
    주어진 경로의 프로젝트 아키텍처를 분석하여 요약합니다.
    
    Args:
        target_path: 분석 대상 디렉토리 경로
    """
    return analyze_project_structure(target_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=9022)
    args = parser.parse_args()
    
    # SSE transport로 지정 포트에서 실행
    mcp.run(transport="sse", host="127.0.0.1", port=args.port)
```

FastMCP 데코레이터 `@mcp.tool()`은 함수의 시그니처와 docstring에서 자동으로 JSON Schema inputSchema를 생성하며 [^251^], 함수 이름을 tool 이름으로, docstring을 tool description으로 사용한다. 이는 Subagent의 기능을 MCP 표준에 맞게 자동으로 노출하여, Main Agent가 별도의 어댑터 없이 표준 MCP tool calling으로 Subagent를 사용할 수 있게 한다.

#### 4.2.3 Crow SSE 서버(9020)와 충돌 방지

Subagent MCP 서버(9022, 9023, 9024)와 Crow SSE 서버(9020)가 동일 호스트에서 실행되므로, **포트 충돌**과 **프로세스 리소스 경쟁**을 방지해야 한다. Crow 서버는 메모리 관리와 잠금 관리의 중앙 집중 허브이므로, Subagent 서버들이 Crow 서버의 가용성을 침해해서는 안 된다.

**포트 할당 전략**은 다음과 같이 고정 범위를 사용한다:

| 서비스 | 포트 | 용도 |
|--------|------|------|
| Crow Memory SSE Server | 9020 | 중앙 메모리 + 잠금 관리 |
| Scout Subagent | 9022 | 코드 탐색, 아키텍처 분석 |
| Reviewer Subagent | 9023 | 코드 리뷰, 품질 검사 |
| Tester Subagent | 9024 | 테스트 생성, 커버리지 분석 |
| Docs Subagent | 9025 | 문서화, 주석 생성 |
| (예약) | 9026-9029 | 미래 확장용 |

**프로세스 격리**를 위해 각 서버는 독립된 Python 인터프리터 프로세스로 실행되며, OS 레벨에서의 메모리 격리를 통해 한 서버의 메모리 누수가 다른 서버에 영향을 주지 않는다. Crow 서버는 `crow.bin` 파일에 대해 **advisory file lock**(예: Python의 `fcntl` 또는 `portalocker`)을 사용하여 동시 쓰기 충돌을 방지한다. Subagent가 `crow_ingest`를 호출할 때, Crow 서버는 요청을 직렬화하여 `crow.bin`에 순차적으로 기록한다.

**헬스 체크**는 각 서버가 `/health` 엔드포인트를 노출하여, Zoo Code Extension이 30초마다 상태를 평가하도록 한다. Crow 서버가 응답하지 않으면 모든 Subagent 작업을 일시 중지하고, Crow 서버 자동 재시작을 시도한다. Subagent 서버가 응답하지 않으면 해당 Subagent에 대한 요청만 메인 에이전트가 직접 처리하는 graceful degradation을 수행한다.

---

### 4.3 조사 차원 1: Subagent within VS Code Extension Host

"VS Code Extension Host 낶에서 Subagent를 어떻게 관리하고 표시하는가?" 이것이 Wave 4의 첫 번째 병렬화 차원이다. Subagent는 Extension Host 외부에서 실행되지만, 그 상태와 작업 진행 상황은 Extension Host를 통해 사용자에게 표시되어야 한다. 사용자는 "백그라운드에서 무슨 일이 일어나는지"를 볼 수 있어야 하지만, 그 존재가 흐름을 방해해서는 안 된다.

#### 4.3.1 `TreeView API` "Active Subagents" 패널

VS Code의 `TreeView API` [^64^]를 활용하여 Explorer 사이드바에 **"Active Subagents" 패널**을 추가한다. 이 패널은 현재 실행 중인 모든 Subagent의 목록을 실시간으로 표시하며, 각 Subagent의 상태(idle/running/completed/error)와 현재 작업 설명, 진행률을 아이콘과 텍스트로 시각화한다.

TreeView의 구조는 다음과 같다. 최상위 노드는 Subagent의 역할별 카테고리(예: "Running", "Recently Completed")이며, 각 카테고리 아래에 개별 Subagent 노드가 위치한다. 각 Subagent 노드는 `TreeItem`의 `description` 속성으로 현재 작업의 간략한 설명을, `iconPath`로 상태 아이콘을, `tooltip`으로 상세 정보를 표시한다.

```typescript
// activeSubagentsProvider.ts [튜닝]
import * as vscode from 'vscode';

interface SubagentNode {
    id: string;           // "scout-uuid-1234"
    name: string;         // "Scout"
    status: 'idle' | 'running' | 'completed' | 'error';
    currentTask?: string; // "Searching for error handling patterns..."
    progress?: number;    // 0~100
    startTime?: number;   // Unix timestamp
    elapsedMs?: number;
}

class ActiveSubagentsProvider implements vscode.TreeDataProvider<SubagentNode> {
    private _onDidChangeTreeData = new vscode.EventEmitter<SubagentNode | undefined>();
    readonly onDidChangeTreeData = this._onDidChangeTreeData.event;
    
    private subagents: Map<string, SubagentNode> = new Map();

    // [튜닝] SSE 실시간 업데이트 — Crow 서버의 상태 스트림을 구독
    subscribeToStatusStream(crowServerUrl: string): void {
        const eventSource = new EventSource(`${crowServerUrl}/agents/status`);
        
        eventSource.addEventListener('agentStatus', (event) => {
            const update = JSON.parse(event.data);
            const existing = this.subagents.get(update.id);
            
            this.subagents.set(update.id, {
                ...existing,
                ...update,
                elapsedMs: update.startTime ? Date.now() - update.startTime : undefined,
            });
            
            // [튜닝] 변경된 노드만 선택적 업데이트 (전체 refresh 대신)
            this._onDidChangeTreeData.fire(this.subagents.get(update.id));
        });
    }

    getTreeItem(element: SubagentNode): vscode.TreeItem {
        const item = new vscode.TreeItem(element.name);
        
        // 상태에 따른 아이콘과 색상
        const iconMap = {
            idle: { icon: '$(debug-pause)', color: new vscode.ThemeColor('disabledForeground') },
            running: { icon: '$(sync~spin)', color: new vscode.ThemeColor('badge.background') },
            completed: { icon: '$(check)', color: new vscode.ThemeColor('testing.iconPassed') },
            error: { icon: '$(error)', color: new vscode.ThemeColor('errorForeground') },
        };
        
        item.iconPath = iconMap[element.status].icon;
        item.description = element.currentTask || element.status;
        item.tooltip = `${element.name}\nStatus: ${element.status}\n${element.progress !== undefined ? `Progress: ${element.progress}%` : ''}\n${element.elapsedMs ? `Elapsed: ${(element.elapsedMs / 1000).toFixed(1)}s` : ''}`;
        item.contextValue = element.status; // status별 context menu
        
        return item;
    }

    getChildren(element?: SubagentNode): Thenable<SubagentNode[]> {
        if (!element) {
            // 최상위: 모든 활성 Subagent 반환 (running 먼저, 그 다음 completed)
            const all = Array.from(this.subagents.values());
            return Promise.resolve(all.sort((a, b) => {
                const order = { running: 0, idle: 1, completed: 2, error: 3 };
                return order[a.status] - order[b.status];
            }));
        }
        return Promise.resolve([]);
    }
}
```

이 TreeView는 `package.json`의 `contributes.views`에 `explorer` 위치로 등록되며 [^64^], 사용자가 Explorer 사이드바에서 언제든 Subagent의 현재 상태를 한눈에 파악할 수 있다. 중요한 것은 이 패널이 **기본적으로 접혀(collapse) 있으며**, 사용자가 펼치기 전까지 화면 공간을 거의 차지하지 않는다는 점이다. 이는 Subagent의 존재가 사용자의 주요 작업 영역을 침해하지 않도록 하는 바이브 설계 원칙의 일환이다.

#### 4.3.2 Subagent 상태: idle/running/completed/error

Subagent의 생명주기는 4가지 상태로 정의된다. 각 상태의 의미와 전환 조건은 다음과 같다.

| 상태 | 아이콘 | 설명 | 전환 조건 |
|------|--------|------|-----------|
| **idle** | ⏸️ 회색 | 대기 중, 프로세스는 실행 중이나 작업 할당 대기 | 작업 완료 후 5분 유지 → auto-terminate |
| **running** | 🔄 파란색 | 작업 실행 중 | Main Agent가 tool call을 발행한 시점 |
| **completed** | ✅ 녹색 | 작업 정상 완료 | tool execution이 성공적으로 종료된 시점 |
| **error** | ❌ 빨간색 | 작업 실패 또는 프로세스 비정상 종료 | tool execution 실패, timeout, 프로세스 crash |

상태 전환은 Crow SSE 서버가 중앙 집중 관리한다. Subagent가 `tools/call` 요청을 받으면 Crow 서버는 해당 Subagent의 상태를 `running`으로 전파하고, 작업이 완료되면 `completed` 또는 `error`로 전환한다. 이 상태 정보는 SSE 스트림을 통해 Zoo Code Extension의 TreeView에 실시간으로 푸시된다.

**상태 유지 전략**에 대해 중요한 설계 결정이 있다. Subagent가 `completed` 상태가 된 후에도 프로세스를 즉시 종료하지 않고, 일정 시간(기본 5분) 동안 `idle` 상태로 유지한다. 이는 동일 Subagent가 연속적으로 작업 요청을 받을 때 프로세스 생성 오버헤드를 피하기 위함이다. 5분간 새 작업이 없으면 `SubagentManager.idleTimer`가 자동으로 프로세스를 종료시킨다(Section 4.2.1의 `resetIdleTimer` 참조). 이는 "process pooling"의 최소 구현으로, 에이전트의 시작 지연을 거의 느끼지 못하게 하면서도 불필요한 리소스 점유를 방지한다.

#### 4.3.3 간접 공유 vs 직접 공유

Subagent 간, 그리고 Subagent와 Main Agent 간의 데이터 공유 방식에는 두 가지 패턴이 있다. 이 선택은 멀티에이전트 시스템의 데이터 일관성과 확장성에 결정적인 영향을 미친다.

**간접 공유(Indirect Sharing)**는 모든 데이터 교환이 Crow Memory(`crow.bin`)를 중개하는 방식이다. Subagent A가 작업 결과를 `crow_ingest`로 Crow에 저장하면, Subagent B(또는 Main Agent)는 `crow_recall`로 해당 데이터를 읽어간다. 이 방식의 장점은 **완전한 느슨한 결합(loose coupling)**을 제공한다는 점이다. Subagent A는 자신의 결과를 누가, 언제 읽을지 알 필요가 없으며, Subagent B는 데이터의 출처를 알 필요가 없다. Crow의 중앙 집중형 감쇠 메커니즘(λ=0.95) [^377^]이 자동으로 오래된 데이터를 희석시키므로, 메모리 관리도 일관되게 이루어진다. 단점은 Crow 서버를 거치는 추가 지연 시간(네트워크 I/O + 검색)이 발생한다는 점이다.

**직접 공유(Direct Sharing)**는 Subagent A가 작업 결과를 직접 Main Agent의 컨텍스트에 쓰는 방식이다. 예를 들어 Subagent가 자신의 `tool_call` 결과에 Main Agent의 `context` 레지스터를 직접 수정하는 side-effect을 가하는 방식이다. 이 방식은 지연 시간이 거의 없지만, **데이터 레이스와 일관성 붕괴의 위험**이 크다. 두 Subagent가 동시에 동일 레지스터에 쓰기를 시도하면 예측 불가능한 결과가 발생할 수 있으며, Subagent의 side-effect이 Main Agent의 동작에 예기치 않은 영향을 미칠 수 있다.

Wave 4의 설계에서는 **간접 공유를 원칙, 직접 공유를 예외**로 채택한다. 모든 Subagent의 결과는 반드시 Crow Memory를 통해 공유되며, 이는 데이터 일관성과 추적 가능성을 보장한다. 직접 공유는 오직 **긴급 컨텍스트 주입**의 경우에만 제한적으로 사용된다 — 예를 들어 Scout가 사용자의 질문에 대한 답변을 5초 내에 찾아야 할 때, Crow의 정식 저장/검색 주기를 거치지 않고 Main Agent의 다음 프롬프트에 직접 결과를 prepend할 수 있다. 이 예외는 Main Agent가 직접 통제하며, `SubagentManager`의 `injectUrgentContext()` 메서드로만 허용된다.

#### 4.3.4 바이브 점수: 현재 2/10 → 목표 8/10

현재 Zoo Code에서 Subagent 개념은 거의 존재하지 않는다. 사용자가 병렬 작업을 원하면 수동으로 새 VS Code 창을 열거나, 다른 AI 도구를 병렬로 사용해야 한다. 이 과정에서 흐름은 완전히 끊긴다. Subagent의 존재를 사용자가 의식하지 않는, 흐름 속에 자연스럽게 녹아드는 병렬 처리를 구현하는 것이 목표 8/10의 의미다. 10점에 도달하지 못하는 이유는 — 완전한 투명성은 불가능하며, 사용자가 "Zoo Orchestra" 대시보드를 펼쳐서 Subagent의 작업을 확인하고 싶어할 때 그 정보가 제공되어야 하기 때문이다. 8점은 "기본적으로 투명하지만, 원할 때 볼 수 있다"는 상태다.

| 평가 항목 | 현재 점수 | 목표 점수 | 개선 Delta |
|-----------|-----------|-----------|------------|
| Subagent 시각화 (TreeView 패널) | 1/10 | 8/10 | +7 |
| Subagent 상태 실시간 표시 | 1/10 | 8/10 | +7 |
| 간접/직접 공유 정책 일관성 | 3/10 | 8/10 | +5 |
| Subagent 생성/소멸 자동화 | 2/10 | 8/10 | +6 |
| **종합 바이브 점수** | **2/10** | **8/10** | **+6** |

---

### 4.4 조사 차원 2: Background Task within VS Code

"사용자가 다른 작업을 하는 동안 AI가 백그라운드에서 일하는 것" — 이것이 병렬화의 두 번째 차원이다. 사용자가 파일 A를 편집하는 동안, Subagent가 파일 B의 리팩토링을 진행한다. 이 두 작업이 물리적으로 동시에 이루어지며, 사용자는 두 작업 사이를 원활하게 전환할 수 있어야 한다.

#### 4.4.1 `vscode.window.withProgress` 진행률 표시

VS Code Extension API의 `vscode.window.withProgress` [^51^]는 백그라운드 작업의 진행 상태를 시각화하는 표준 메커니즘이다. 이 API는 작업의 위치(`ProgressLocation`)를 선택할 수 있으며, 각 위치는 사용자 경험에 미치는 영향이 다르다.

`ProgressLocation.Notification`은 화면 우측 상단의 토스트 알림으로 진행률을 표시한다. 짧은 작업(10초 이내)에 적합하며, 작업이 끝나면 자동으로 사라진다. `ProgressLocation.Window`는 VS Code 하단 상태바에 진행률을 표시한다. 장기 작업에 적합하며, 사용자가 다른 작업을 하는 동안에도 지속적으로 진행 상황을 확인할 수 있다. `ProgressLocation.SourceControl`은 SCM 뷰에 진행 상태를 표시하며, Git 기반 작업에 적합하다.

Subagent의 백그라운드 작업에는 `ProgressLocation.Window`를 기본으로 사용한다. 사용자가 다른 파일을 편집하는 동안, 하단 상태바에 `"🔄 Scout: Searching codebase (67%)"` 같은 메시지가 표시된다. 이 메시지는 클릭하면 "Zoo Orchestra" 대시보드(Webview)로 이동하여 상세 진행 상황을 보여준다.

```typescript
// backgroundTaskManager.ts [튜닝]
import * as vscode from 'vscode';

class BackgroundTaskManager {
    // [튜닝] 백그라운드 작업 시작 — withProgress로 진행률 표시
    async runWithProgress<T>(
        subagentName: string,
        taskDescription: string,
        taskFn: (progress: vscode.Progress<{ message?: string; increment?: number }>) => Promise<T>
    ): Promise<T> {
        return vscode.window.withProgress({
            location: vscode.ProgressLocation.Window,
            title: `${subagentName}: ${taskDescription}`,
            cancellable: true, // 사용자가 Cancel 가능
        }, async (progress, token) => {
            // [튜닝] SSE를 통해 Subagent의 진행 이벤트를 withProgress에 연동
            const eventSource = new EventSource(
                `http://localhost:${this.getPort(subagentName)}/progress`
            );
            
            eventSource.addEventListener('progress', (event) => {
                const data = JSON.parse(event.data);
                progress.report({
                    message: data.message,
                    increment: data.increment, // 이전 대비 증가분
                });
            });
            
            // Cancel 요청 시 Subagent에게 취소 신호 전달
            token.onCancellationRequested(() => {
                this.cancelSubagentTask(subagentName);
                eventSource.close();
            });
            
            try {
                const result = await taskFn(progress);
                return result;
            } finally {
                eventSource.close();
            }
        });
    }
}
```

이 메커니즘의 핵심은 **사용자가 취소할 수 있다(cancellable: true)**는 점이다. 백그라운드 작업이 예상보다 오래 걸리거나, 사용자가 더 이상 그 결과가 필요 없을 때, 하단 상태바의 진행 표시줄을 클릭하여 "Cancel"을 선택할 수 있다. 이 취소 신호는 Subagent 프로세스에 전달되어, graceful하게 현재 작업을 마무리하고 idle 상태로 복귀한다.

#### 4.4.2 완료: 자동 열기 vs "확인하시겠습니까?" 버튼

백그라운드 작업이 완료되었을 때 결과를 사용자에게 전달하는 방식은 **바이브 점수에 결정적인 영향**을 미친다. 두 가지 전략이 있으며, 그 트레이드오프는 다음과 같다.

**자동 열기(Auto-Open)**는 작업이 완료되면 즉시 결과 파일을 에디터에 표시하거나, 결과 내용을 채팅 스트림에 자동으로 삽입하는 방식이다. 이 방식의 장점은 사용자 개입 없이 즉시 결과를 확인할 수 있다는 점이다. 단점은 사용자가 현재 집중하고 있는 작업의 흐름을 강제로 끊을 수 있다는 점이다. 사용자가 중요한 코드를 작성하는 순간에 백그라운드 작업이 완료되어 화면이 전환되면, 그 순간의 흐름은 영원히 깨진다. 이는 Insight 5 "The Vibe Paradox" [^81^]에서 지적한 바와 같이, **완벽한 자동화가 오히려 바이브를 파괴하는** 대표적 사례다.

**"확인하시겠습니까?" 버튼(Opt-In)**은 작업 완료 시 `window.showInformationMessage`로 알림을 표시하고, 사용자가 "보기" 버튼을 클릭해야 결과를 확인할 수 있는 방식이다. 예: `"Scout completed: 15 error handling patterns found. [View Results] [Dismiss]"`. 이 방식의 장점은 사용자가 **자신의 페이스로 결과를 확인**할 수 있다는 점이다. 현재 집중 중인 작업을 끊지 않으면서, 준비가 되었을 때 결과를 확인할 수 있다. 단점은 사용자가 알림을 무시할 경우 결과가 영원히 놓칠 수 있다는 점이다.

Wave 4의 설계에서는 **"확인하시겠습니까?"를 기본, 자동 열기를 예외**로 채택한다. 기본적으로 모든 백그라운드 작업은 완료 알림만 표시하며, 사용자가 명시적으로 "보기"를 선택해야 결과가 화면에 나타난다. 자동 열기는 두 가지 경우에만 예외적으로 사용된다: (1) 사용자가 설정에서 "백그라운드 작업 결과 자동 표시"를 명시적으로 활성화한 경우, (2) 작업이 사용자가 현재 활성화한 파일과 직접 관련이 있는 경우(예: 사용자가 파일 X를 편집 중일 때, 파일 X에 대한 백그라운드 분석이 완료된 경우). 이 예외는 `BackgroundTaskManager.shouldAutoOpen()` 메서드에서 판단하며, 현재 활성 에디터의 파일 경로와 백그라운드 작업의 대상 파일 경로를 비교하여 결정한다.

#### 4.4.3 결과 `crow_ingest`로 `style`/`arch` 저장

백그라운드 작업의 결과는 단순히 사용자에게 표시되는 것으로 끝나지 않는다. **작업 결과에서 추출된 인사이트는 Crow Memory의 장기 레지스터에 자동으로 저장**되어, 향후 작업에서 AI가 "학습"할 수 있게 된다. [MCP]

예를 들어 Scout Subagent가 프로젝트의 에러 핸들링 패턴을 탐색한 결과는 다음과 같이 Crow에 저장된다:

```python
# scout가 작업 완료 후 Crow에 결과 저장 [MCP]
crow_ingest(
    content="이 프로젝트에서는 try/catch 대신 Result<T,E> 패턴을 사용. "
            "에러 처리는 src/utils/result.ts의 ok()/err() 헬퍼를 통해 이루어짐. "
            "async 함수에서는 neverthrow 라이브러리의 ResultAsync 사용.",
    register="arch",  # 아키텍처 결정 레지스터에 저장
    metadata={
        source: "scout_subagent_analysis",
        confidence: 0.92,
        files_analyzed: ["src/utils/result.ts", "src/services/api.ts", ...],
        polarity: 0,  # 중립적 정보
    }
)
```

이 저장은 Subagent의 tool call 결과를 Main Agent가 해석하여 수행하는 것이 아니라, **Subagent가 직접 수행**한다. Scout MCP 서버의 `search_codebase` tool handler 낶에서, 검색 결과의 요약이 자동으로 `crow_ingest`를 통해 `arch` 레지스터에 저장된다. 이는 "작업 결과의 지속 가능한 축적"을 보장하며, 다음번에 유사한 탐색 요청이 들어오면 Scout는 Crow에 이미 저장된 정보를 활용하여 더 빠르고 정확한 결과를 제공할 수 있다.

백그라운드 작업이 코드 스타일 관련 분석(예: "이 프로젝트에서 함수명은 camelCase, 파일명은 kebab-case를 사용")을 수행한 경우, 그 결과는 `style` 레지스터에 저장된다. 이는 Wave 3(Zero-Explanation)의 "사용자가 말하지 않아도 AI가 아는" 경험을 직접 뒷받침한다.

#### 4.4.4 바이브 점수: 현재 2/10 → 목표 8/10

현재 Zoo Code는 백그라운드 작업을 지원하지 않는다. 모든 AI 작업은 동기적으로 이루어지며, 사용자는 응답이 완료될 때까지 기다려야 한다. 이는 긴 작업(코드베이스 전체 검색, 대규모 리팩토링 등)에서 심각한 흐름 끊김을 초래한다. 백그라운드 작업이 원활하게 작동하면 사용자는 "AI가 나를 위해 일하고 있다"는 느낌을 받으며, 그 일이 자신의 현재 작업을 방해하지 않는다는 확신이 바이브를 유지한다.

| 평가 항목 | 현재 점수 | 목표 점수 | 개선 Delta |
|-----------|-----------|-----------|------------|
| 진행률 시각화 (withProgress) | 1/10 | 8/10 | +7 |
| 완료 알림/결과 표시 | 2/10 | 8/10 | +6 |
| 결과 자동 저장 (crow_ingest) | 2/10 | 8/10 | +6 |
| 작업 취소 가능성 | 1/10 | 8/10 | +7 |
| **종합 바이브 점수** | **2/10** | **8/10** | **+6** |



---

### 4.5 조사 차원 3: @Mentions & Agent Routing

"사용자가 채팅창에 `@scout 이거 찾아줘`라고 입력하면, 그 메시지가 어떻게 Scout Subagent에게 전달되는가?" 이것이 병렬화의 세 번째 차원이다. @mention은 사용자가 Subagent를 명시적으로 호출하는 가장 직관적인 인터페이스이며, 이 라우팅 메커니즘의 신속성과 신뢰성은 전체 병렬화 경험의 핵심을 결정한다.

#### 4.5.1 "@scout 이거 찾아줘" prefix 파싱

@mention 라우팅의 가장 단순한 구현은 사용자 입력의 **prefix 파싱**이다. 사용자가 입력한 텍스트의 첫 토큰이 `@<subagent-name>` 패턴과 일치하는지를 검사하고, 일치하면 해당 이름의 Subagent에게 요청을 라우팅한다. 이 방식은 NLP 기반 의도 분석 없이 순수한 문자열 매칭으로 동작하므로, 지연 시간이 거의 없고(밀리초 단위), 결과가 deterministic하다.

```typescript
// mentionRouter.ts [튜닝]
import * as vscode from 'vscode';

interface MentionRoute {
    subagentName: string;
    port: number;
    description: string;
}

class MentionRouter {
    // 등록된 Subagent 라우팅 테이블
    private routes: Map<string, MentionRoute> = new Map([
        ['scout', { subagentName: 'scout', port: 9022, description: 'Code exploration and search' }],
        ['reviewer', { subagentName: 'reviewer', port: 9023, description: 'Code review and quality analysis' }],
        ['tester', { subagentName: 'tester', port: 9024, description: 'Test generation and coverage' }],
        ['docs', { subagentName: 'docs', port: 9025, description: 'Documentation generation' }],
    ]);

    // [튜닝] 사용자 입력 파싱 — @mention prefix 추출
    parseMention(input: string): { route: MentionRoute | null; cleanPrompt: string } | null {
        // @mention 패턴: "@scout 이거 찾아줘" → name="scout", prompt="이거 찾아줘"
        const mentionRegex = /^@(\w+)\s+(.*)$/;
        const match = input.match(mentionRegex);
        
        if (!match) {
            // @mention이 없으면 null 반환 → Main Agent가 처리
            return null;
        }
        
        const [, name, cleanPrompt] = match;
        const route = this.routes.get(name);
        
        if (!route) {
            // 존재하지 않는 Subagent → graceful fallback 처리를 위해 특별 마커 반환
            return { route: null, cleanPrompt: input };
        }
        
        return { route, cleanPrompt };
    }

    // [튜닝] @mention 라우팅 실행
    async routeMention(input: string, stream: vscode.ChatResponseStream): Promise<void> {
        const parsed = this.parseMention(input);
        
        if (!parsed) {
            // @mention 없음 — Main Agent가 처리 (이 메서드는 호출되지 않아야 함)
            return;
        }
        
        const { route, cleanPrompt } = parsed;
        
        if (!route) {
            // [튜닝] Graceful fallback: 존재하지 않는 Subagent
            stream.markdown(`> ⚠️ Unknown subagent. Let me handle this directly.\\n\\n`);
            await this.fallbackToMainAgent(cleanPrompt, stream);
            return;
        }
        
        // [튜닝] 해당 Subagent의 MCP 서버로 tool call 전달
        stream.markdown(`> 🔍 Routing to **${route.subagentName}**: ${route.description}...\\n\\n`);
        
        try {
            // Subagent MCP 클라이언트 생성 및 tool 호출
            const result = await this.callSubagentTool(route, cleanPrompt);
            
            // 결과를 Main Agent의 컨텍스트에 주입 (간접 공유)
            // Main Agent의 다음 응답에서 crow_recall로 이 결과를 자연스럽게 활용
            stream.markdown(result.content);
            
        } catch (error) {
            // [튜닝] Subagent 실패 시 graceful fallback
            stream.markdown(`> ⚠️ ${route.subagentName} encountered an issue. Falling back to main agent...\\n\\n`);
            await this.fallbackToMainAgent(cleanPrompt, stream);
        }
    }

    // [튜닝] Subagent MCP 서버에 tool call 수행
    private async callSubagentTool(route: MentionRoute, prompt: string): Promise<any> {
        const client = new MCPClient({
            transport: new SSEClientTransport(new URL(`http://localhost:${route.port}`)),
        });
        
        await client.connect();
        
        // Subagent의 기본 tool 호출 (각 Subagent는 "process_request"를 기본 tool로 제공)
        const result = await client.callTool({
            name: 'process_request',
            arguments: { prompt },
        });
        
        await client.close();
        return result;
    }
}
```

이 파싱 메커니즘의 핵심 특성은 **deterministic하고 즉각적**이라는 점이다. 정규식 매칭은 수 밀리초 내에 완료되며, 매칭 결과는 항상 동일하다. 이는 NLP 기반 의도 분석이 가진 불확실성(모델이 의도를 "추측"해야 함)을 완전히 회피한다. 사용자가 `@scout`라고 입력한 순간, 시스템은 **100% 확신**을 가지고 Scout Subagent로 라우팅한다.

**라우팅 테이블의 확장성**도 중요하다. `routes` Map은 Zoo Code Extension의 설정(`contributes.configuration`)에서 동적으로 확장 가능해야 한다. 사용자가 커스텀 Subagent를 추가하면(예: `@security 보안 감사`), `settings.json`에 새 라우팅 규칙을 등록하고 `MentionRouter`가 이를 런타임에 로드한다.

#### 4.5.2 `vscode.chat.createChatParticipant()` 우회

VS Code는 `vscode.chat.createChatParticipant()` API [^365^]를 통해 공식적인 @mention 기반 Chat Participant를 등록할 수 있다. 이 API는 `package.json`의 `contributes.chatParticipants`에 participant를 선언하고, Extension 코드에서 `vscode.chat.createChatParticipant()`로 handler를 등록하는 방식으로 동작한다. 이 API를 사용하면 VS Code가 자동으로 @mention 입력을 감지하고 라우팅해주며, 자동완성, 아이콘 표시, 스티키 participant 등의 네이티브 기능을 활용할 수 있다.

그러나 이 API는 **VS Code Insider 버전에서만 사용 가능**하며 [^467^], API 시그니처가 빈번하게 변경될 수 있는 unstable 상태다. Zoo Code는 이 API에 직접 의존하지 않고, **자체 prefix 파싱 메커니즘을 기본**으로 사용하되, `createChatParticipant()`가 사용 가능한 환경에서는 이를 **우회 우회(wrap)**하여 네이티브 기능을 활용하는 하이브리드 전략을 채택한다.

```typescript
// mentionRouter.ts — createChatParticipant 우회 로직 [튜닝]
class MentionRouter {
    private useNativeApi: boolean = false;

    constructor() {
        // [튜닝] 런타임에 createChatParticipant API 가용성 확인
        this.useNativeApi = typeof (vscode.chat as any)?.createChatParticipant === 'function';
    }

    registerParticipants(context: vscode.ExtensionContext): void {
        if (this.useNativeNativeApi) {
            // [튜닝] 네이티브 API 사용 — VS Code가 자동 라우팅
            for (const [name, route] of this.routes) {
                const participant = (vscode.chat as any).createChatParticipant(
                    `zoo-code.${name}`,
                    async (request: any, context: any, stream: any, token: any) => {
                        // 네이티브 API로 라우팅되어도 낶부 로직은 동일
                        await this.handleSubagentRequest(route, request.prompt, stream, token);
                    }
                );
                context.subscriptions.push(participant);
            }
        } else {
            // [튜닝] 네이티브 API 불가 — 자체 prefix 파싱 사용
            // Extension의 기존 채팅 입력 처리기에 parseMention() 연결
            this.registerLegacyMentionHandler(context);
        }
    }

    // [튜닝] 레거시 모드: Extension의 기존 채팅 handler와 통합
    private registerLegacyMentionHandler(context: vscode.ExtensionContext): void {
        // Zoo Code Extension의 기존 메시지 처리 파이프라인에 후킹
        // 메시지가 들어오면 parseMention()을 먼저 호출하고,
        // @mention이 감지되면 Subagent로 라우팅, 아니면 기존 처리 흐름 유지
        zooCodeMessagePipeline.addPreprocessor((message: string) => {
            const parsed = this.parseMention(message);
            if (parsed?.route) {
                return { routed: true, route: parsed.route, prompt: parsed.cleanPrompt };
            }
            return { routed: false, originalMessage: message };
        });
    }
}
```

이 우회 전략의 핵심은 **API 가용성의 런타임 체크**다. `createChatParticipant`가 존재하는지를 런타임에 확인하고, 존재하면 네이티브 API를 사용하여 더 풍부한 UX(자동완성, 아이콘 등)를 제공하고, 존재하지 않으면 자체 파싱으로 fallback한다. 이는 API가 안정화될 때까지 기다리지 않고도 @mention 기능을 즉시 제공할 수 있게 한다.

#### 4.5.3 Graceful fallback

@mention 라우팅은 세 가지 실패 시나리오에 대해 graceful fallback을 제공해야 한다. 각 시나리오의 처리 방식은 다음과 같다.

**시나리오 1: 존재하지 않는 Subagent 이름**. 사용자가 `@unknown 여기서 뭐 좀 찾아줘`라고 입력했지만, `unknown`이라는 Subagent는 등록되어 있지 않다. 이 경우 `parseMention()`은 `{ route: null, cleanPrompt: input }`을 반환하고, `routeMention()`은 사용자에게 `"Unknown subagent 'unknown'. Let me handle this directly."`라는 알림을 표시한 뒤, 동일 프롬프트를 Main Agent가 처리하도록 fallback한다. 사용자 경험상 Subagent 호출 실패로 인해 작업이 중단되는 것이 아니라, **메인 에이전트가 자동으로 대체**하여 요청을 완료한다.

**시나리오 2: Subagent 프로세스 비가용**. `@scout`는 유효한 Subagent 이름이지만, Scout MCP 서버 프로세스가 현재 실행 중이지 않거나 crash 상태다. 이 경우 `callSubagentTool()`에서 연결 오류가 발생하고, `routeMention()`의 `catch` 블록이 활성화된다. 사용자에게 `"scout encountered an issue. Falling back to main agent..."`라는 알림을 표시하고, Main Agent가 동일 요청을 처리한다. 동시에 `SubagentManager`는 Scout 프로세스 자동 재시작을 시도한다.

**시나리오 3: Subagent tool 실행 실패**. Subagent에 연결은 성공했지만, tool 실행 중 오류가 발생했다(예: 코드베이스 검색 중 예외). 이 경우는 MCP 프로토콜의 `isError: true` 응답 [^282^]으로 감지되며, Main Agent가 오류 내용을 해석하여 사용자에게 적절한 메시지를 표시하고 대체 접근법을 제안한다.

이 세 가지 fallback 시나리오 모두에서 핵심 원칙은 **"사용자의 요청이 소실되지 않는다"**는 것이다. 어떤 이유로든 Subagent가 요청을 처리할 수 없을 때, Main Agent가 항상 최종 안전망(ultimate fallback)으로 작동한다. 이는 멀티에이전트 시스템의 신뢰성을 보장하는 핵심 설계 원칙이다.

#### 4.5.4 `life_pref` 패턴 저장

@mention 라우팅은 단순한 요청 분배를 넘어 **사용자의 선호 패턴을 학습**하는 기회를 제공한다. 사용자가 특정 유형의 작업을 항상 특정 Subagent에게 위임하는 패턴이 감지되면, 이는 `life_pref` 레지스터에 저장되어 향후 자동화에 활용된다. [MCP]

```python
# @mention 사용 패턴 분석 및 life_pref 저장 [MCP]
# Zoo Code Extension이 사용자의 @mention 사용 기록을 분석하여
crow_ingest(
    content="사용자가 코드 탐색 요청(search, find, explore)을 @scout에게 위임함. "
            "리팩토링/리뷰 관련 요청은 @reviewer에게 위임함.",
    register="life_pref",
    metadata={
        pattern_type: "subagent_routing_preference",
        confidence: 0.85,
        evidence_count: 12,  # 12회 반복 확인
        polarity: +1.5,  # 강한 선호
    }
)
```

이 패턴 학습의 구체적 활용 사례는 다음과 같다. 사용자가 `"이 프로젝트의 에러 핸들링 패턴 좀 찾아줘"`라고 입력했을 때, @mention prefix가 없더라도 `life_pref` 레지스터에 저장된 패턴을 기반으로 **자동 라우팅 제안**을 표시할 수 있다. 예를 들어 채팅 입력창 옆에 `"💡 Route to @scout?"`라는 제안 버튼이 나타나고, 사용자가 Tab 키를 누륩면 자동으로 `@scout` prefix가 추가된다. 이는 사용자가 매번 Subagent 이름을 기억하고 입력해야 하는 마찰을 줄여준다.

더 나아가, 패턴이 충분히 확립되면(예: 동일 유형의 요청을 10회 이상 동일 Subagent에게 위임), Zoo Code Extension은 **자동 라우팅**을 활성화할 수 있다. 사용자의 명시적 @mention 없이도, 요청의 키워드(예: "find", "search", "explore", "찾아")와 `life_pref` 패턴을 종합하여 가장 적합한 Subagent로 자동으로 라우팅한다. 이 자동 라우팅은 사용자 설정에서 비활성화할 수 있으며, 활성화된 경우에도 라우팅 결정을 투명하게 표시한다(예: `"[auto-routed to @scout] 검색 결과:"`).

#### 4.5.5 바이브 점수: 현재 2/10 → 목표 8/10

현재 Zoo Code는 @mention 기능을 전혀 제공하지 않는다. 사용자가 Subagent를 호출하려면 수동으로 별도 인터페이스를 사용해야 하며, 이 과정에서 흐름은 완전히 끊긴다. @mention 라우팅이 원활하게 작동하면 사용자는 "내가 말하는 대로 AI가 알아서 분배한다"는 느낌을 받으며, 이는 마치 개인 비서가 여러 전문가를 대신 섭외하는 것과 같은 경험이다.

| 평가 항목 | 현재 점수 | 목표 점수 | 개선 Delta |
|-----------|-----------|-----------|------------|
| @mention prefix 파싱 속도 | 1/10 | 9/10 | +8 |
| createChatParticipant 통합 | 1/10 | 7/10 | +6 |
| Graceful fallback 완성도 | 2/10 | 8/10 | +6 |
| life_pref 자동 라우팅 | 1/10 | 8/10 | +7 |
| **종합 바이브 점수** | **2/10** | **8/10** | **+6** |

---

### 4.6 조사 차원 4: Fleet Dashboard

"여러 AI가 동시에 작업할 때, 사용자가 그 모든 작업을 한눈에 어떻게 볼 수 있는가?" 이것이 병렬화의 네 번째 차원이다. Fleet Dashboard는 병렬 작업의 **투명성**을 제공하는 중앙 통제실이다. 사용자가 대시보드를 볼 때 "무언가가 복잡하게 돌아가고 있구나"를 느끼게 해서는 안 되며, 오히려 "모든 것이 통제之下에 있구나"라는 안정감을 주어야 한다.

#### 4.6.1 `TreeView API` + `Webview API` "Zoo Orchestra" 대시보드

Fleet Dashboard는 두 개의 VS Code API를 조합하여 구현된다: **TreeView API** [^64^]로 사이드바에 간략한 상태를 표시하고, **Webview API** [^59^]로 상세 대시보드를 제공한다. 이 2-tier 구조는 사용자가 현재 필요로 하는 정보의 상세 수준에 따라 유연하게 전환할 수 있게 한다.

**TreeView 레이어(간략 정보)**는 Explorer 사이드바에 "Zoo Orchestra" 섹션으로 표시되며, 현재 활성 Subagent의 목록만 간략히 보여준다(Section 4.3.1에서 설명한 `ActiveSubagentsProvider`와 동일). 각 Subagent 노드는 이름, 상태 아이콘, 현재 작업 설명 1줄만 표시한다. 이 패널의 목적은 "대시보드가 있다"는 것을 상기시키면서도 화면 공간을 최소화하는 것이다. 사용자가 특정 Subagent 노드를 클릭하면, 해당 Subagent의 상세 정보가 Webview 대시보드에 표시된다.

**Webview 레이어(상세 정보)**는 `createWebviewPanel`로 생성된 독립 패널로, 다음 정보를 종합하여 표시한다. [튜닝]

```typescript
// orchestraDashboard.ts — Zoo Orchestra 대시보드 [튜닝]
import * as vscode from 'vscode';

class OrchestraDashboard {
    private panel: vscode.WebviewPanel | undefined;

    // [튜닝] Webview 대시보드 열기
    show(): vscode.WebviewPanel {
        if (this.panel) {
            this.panel.reveal(vscode.ViewColumn.Two);
            return this.panel;
        }

        this.panel = vscode.window.createWebviewPanel(
            'zooOrchestra',
            'Zoo Orchestra',
            vscode.ViewColumn.Two,  // 에디터 옆에 표시
            {
                enableScripts: true,
                retainContextWhenHidden: true, // 숨김 상태에서도 컨텍스트 유지
                localResourceRoots: [
                    vscode.Uri.joinPath(this.extensionUri, 'media')
                ],
            }
        );

        this.panel.webview.html = this.getDashboardHtml();
        
        // [튜닝] SSE 실시간 업데이트 — Crow 서버의 상태 스트림을 Webview에 연동
        this.subscribeToRealtimeUpdates(this.panel.webview);

        this.panel.onDidDispose(() => {
            this.panel = undefined;
        });

        return this.panel;
    }

    // [튜닝] SSE 실시간 상태 업데이트
    private subscribeToRealtimeUpdates(webview: vscode.Webview): void {
        const eventSource = new EventSource('http://localhost:9020/agents/status');
        
        eventSource.addEventListener('agentStatus', (event) => {
            const data = JSON.parse(event.data);
            // Webview에 상태 업데이트 메시지 전송
            webview.postMessage({
                type: 'agentUpdate',
                agent: data,
            });
        });
        
        eventSource.addEventListener('lockUpdate', (event) => {
            const data = JSON.parse(event.data);
            webview.postMessage({
                type: 'lockUpdate',
                locks: data,
            });
        });
        
        // Webview가 dispose될 때 SSE 연결 종료
        const disposable = webview.onDidReceiveMessage(() => {});
        // cleanup 로직...
    }
}
```

Webview의 `retainContextWhenHidden: true` 옵션 [^59^]은 대시보드가 사용자에 의해 숨겨져도 JavaScript 실행 컨텍스트를 유지하여, 다시 표시될 때 상태를 즉시 복원할 수 있게 한다. 이는 사용자가 대시보드를 자주 열고 닫더라도 매번 전체 데이터를 다시 로드하지 않아도 됨을 의미한다.

#### 4.6.2 작업, 진행률, ETA, 충돌 상태

Webview 대시보드에 표시되는 정보는 다음 카테고리로 구성된다.

**작업 목록**은 현재 실행 중(running)이고 최근에 완료(completed)된 모든 Subagent 작업의 목록이다. 각 작업 항목은 Subagent 이름, 작업 설명, 시작 시각, 경과 시간을 표시한다. 작업이 완료된 항목은 5분간 "Recently Completed" 섹션에 남아 있다가 자동으로 사라진다.

**진행률**은 각 Subagent의 현재 작업에 대한 백분율 진행 상태다. `ProgressBar` 컴포넌트로 시각화되며, Subagent가 SSE를 통해 보고한 `progress` 값(0~100)을 직접 표시한다. 진행률 산출은 Subagent별로 다른 방식을 사용할 수 있다 — Scout는 "검색한 파일 수 / 총 파일 수"로, Reviewer는 "검토한 코드 라인 수 / 총 라인 수"로, Tester는 "생성한 테스트 수 / 목표 테스트 수"로 각각 산출한다.

**ETA(Estimated Time of Arrival)**는 각 작업의 예상 완료 시간이다. 이는 각 Subagent의 과거 작업 데이터를 기반으로 추정된다. 예를 들어 Scout의 "코드베이스 검색" 작업이 과거 10회 수행된 평균 완료 시간이 45초였다면, 현재 60% 진행 시점에서 ETA는 `45s * (1 - 0.6) = 18s`로 추정한다. 이 추정은 `crow.bin`의 `arch` 레지스터에 저장된 Subagent별 평균 작업 시간 데이터를 활용한다.

**충돌 상태**는 현재 파일 잠금 상황을 시각화한다. 어떤 파일이 어떤 Subagent에 의해 잠겨 있는지, 잠금 대기 중인 Subagent가 있는지, 최근에 충돌이 해결된 이력은 무엇인지를 표시한다. 충돌이 감지되면 대시보드 상단에 노란색 경고 배너가 표시되며, "2 agents waiting for src/auth.ts" 같은 메시지로 사용자가 즉시 인지할 수 있게 한다.

#### 4.6.3 SSE 실시간 푸시

대시보드의 실시간성은 **Crow SSE Server의 상태 스트림**을 통해 구현된다. Crow 서버는 모든 Subagent의 상태 변경, 잠금 획득/해제, 충돌 발생을 SSE 이벤트로 브로드캐스트하며, TreeView와 Webview 모두 이 스트림을 구독하여 즉각 UI를 업데이트한다.

SSE 이벤트의 구조는 다음과 같다:

```
event: agentStatus
id: 1689234567
data: {"id":"scout-001","name":"Scout","status":"running","progress":67,"currentTask":"Searching src/utils/...","eta":"12s"}

event: lockUpdate
id: 1689234568
data: {"file":"src/auth.ts","lockedBy":"reviewer-002","since":"2025-07-13T10:23:00Z","waitQueue":["scout-001"]}

event: conflictResolved
id: 1689234569
data: {"file":"src/auth.ts","resolvedBy":"auto-merge","strategy":"append-both","agents":["reviewer-002","scout-001"]}
```

`eventSource.addEventListener`를 통해 각 이벤트 타입별 핸들러를 등록하고, 이벤트 수신 시 `webview.postMessage()` [^59^]로 Webview에 데이터를 전달한다. Webview 낶의 JavaScript는 `window.addEventListener('message', ...)`로 이 메시지를 수신하여 DOM을 업데이트한다. 이 구조는 확장 프로그램과 Webview 간의 표준 통신 메커니즘으로, 1초당 수십 회의 업데이트도 문제없이 처리할 수 있다.

**업데이트 빈도 최적화**도 중요하다. SSE 이벤트가 너무 빈번하면 UI가 깜빡이면서 사용자 경험을 해칠 수 있다. 따라서 Webview 낶에서 **requestAnimationFrame 기반 배칭**을 적용하여, 16ms(60fps) 단위로 DOM 업데이트를 묶어 처리한다. 이는 시각적으로 부드러운 업데이트를 보장하면서도, 불필요한 리렌더링을 방지한다.

#### 4.6.4 바이브 점수: 현재 1/10 → 목표 8/10

현재 Zoo Code는 병렬 작업의 시각화를 전혀 제공하지 않는다. 여러 AI가 동시에 작업한다는 개념 자체가 존재하지 않으므로, 대시보드 또한 존재하지 않는다. Fleet Dashboard가 원활하게 작동하면 사용자는 "내 AI 군단이 잘 일하고 있구나"라는 안정감을 얻으며, 이는 병렬화의 불확실성에 대한 심리적 안정감을 제공한다. 1/10인 이유는 — 현재 아묟 시각화도 없다. 8/10인 이유는 — 완벽한 투명성(10점)은 모든 세부 정보를 항상 표시함을 의미하며, 이는 오히려 정보 과잉으로 바이브를 해칠 수 있기 때문이다. 8점은 "필요한 정보가 원할 때 보인다"는 상태다.

| 평가 항목 | 현재 점수 | 목표 점수 | 개선 Delta |
|-----------|-----------|-----------|------------|
| TreeView 간략 상태 표시 | 1/10 | 8/10 | +7 |
| Webview 상세 대시보드 | 1/10 | 8/10 | +7 |
| 실시간 SSE 업데이트 | 1/10 | 9/10 | +8 |
| 작업/진행률/ETA 표시 | 1/10 | 8/10 | +7 |
| 충돌 상태 시각화 | 1/10 | 7/10 | +6 |
| **종합 바이브 점수** | **1/10** | **8/10** | **+7** |

---

### 4.7 조사 차원 5: Conflict Resolution

"두 AI가 동시에 같은 파일을 수정하려 할 때, 어떻게 처리하는가?" 이것이 병렬화의 다섯 번째이자 마지막 차원이다. 병렬 처리의 이점을 누리려면 충돌은 불가피하지만, 충돌이 사용자의 흐름을 끊어서는 안 된다. 이상적인 충돌 해결은 사용자가 "충돌이 있었다는 사실조차 모르는" 것이다.

#### 4.7.1 `FileSystemWatcher` 동시 수정 감지 → 큐잉

충돌 해결의 첫 단계는 충돌을 **조기에 감지**하는 것이다. VS Code의 `FileSystemWatcher` [^51^] [^61^]는 파일 시스템 수준의 변경 이벤트를 감지하여, 두 Subagent가 동일 파일에 쓰기를 시도하는 순간 이를 포착한다. 그러나 `FileSystemWatcher`만으로는 충돌을 **예방**할 수 없다 — 이미 쓰기가 발생한 후에 알림이 오기 때문이다. 따라서 충돌 예방은 **사전 잠금(acquire-before-write)** 메커니즘에서 출발해야 한다.

Wave 4의 충돌 관리는 **3계층 방어** 구조로 설계된다.

**계층 1: 사전 잠금(Crow 기반)**. Subagent가 파일 수정을 시작하기 전에 반드시 Crow 서버의 `lock_acquire` tool을 호출하여 파일 잠금을 획득해야 한다. 잠금이 이미 다른 Subagent에 의해 획득된 상태라면, 요청 Subagent는 **대기 큐(wait queue)**에 들어가 순차적으로 처리된다. 이는 Beads Village [^368^]에서 제안된 MCP 기반 파일 잠금 패턴을 직접 차용한 것이다.

**계층 2: FileSystemWatcher 감시**. 사전 잠금을 우회하는 비정상적인 쓰기(예: Subagent가 잠금 없이 직접 파일 시스템에 쓰기)를 감지하기 위해, `FileSystemWatcher`는 모든 `**/*.{ts,tsx,js,jsx,py}` 파일의 `onDidChange` 이벤트를 모니터링한다. 예상치 못한 변경이 감지되면 Crow 서버에 "무단 쓰기" 알림을 본내고, 해당 파일에 대한 긴급 잠금을 시도한다.

**계층 3: 병합 해결**. 사전 잠금과 FileSystemWatcher 모두를 우회하는 최악의 시나리오(거의 동시에 쓰기)에 대해, Git 기반 3-way merge 또는 AI 기반 자동 병합으로 충돌을 해결한다.

```typescript
// conflictResolver.ts — 3계층 충돌 방어 [튜닝]
import * as vscode from 'vscode';

class ConflictResolver {
    private fileLocks: Map<string, string> = new Map(); // filePath → subagentId
    private waitQueue: Map<string, string[]> = new Map(); // filePath → [subagentId, ...]

    // [튜닝] 계층 1: 사전 잠금 획득
    async acquireLock(filePath: string, subagentId: string): Promise<boolean> {
        if (this.fileLocks.has(filePath)) {
            // 이미 잠겨 있음 → 대기 큐에 추가
            const queue = this.waitQueue.get(filePath) || [];
            queue.push(subagentId);
            this.waitQueue.set(filePath, queue);
            return false; // 잠금 획득 실패, 큐 대기 중
        }
        
        this.fileLocks.set(filePath, subagentId);
        return true;
    }

    // [튜닝] 잠금 해제 + 대기 큐 처리
    async releaseLock(filePath: string, subagentId: string): Promise<void> {
        const holder = this.fileLocks.get(filePath);
        if (holder !== subagentId) {
            throw new Error(`Subagent ${subagentId} cannot release lock held by ${holder}`);
        }
        
        this.fileLocks.delete(filePath);
        
        // 대기 큐에서 다음 Subagent 처리
        const queue = this.waitQueue.get(filePath) || [];
        if (queue.length > 0) {
            const nextSubagent = queue.shift()!;
            this.waitQueue.set(filePath, queue);
            this.fileLocks.set(filePath, nextSubagent);
            // 다음 Subagent에게 잠금 획득 알림 (SSE)
            this.notifyLockAcquired(filePath, nextSubagent);
        }
    }

    // [튜닝] 계층 2: FileSystemWatcher로 무단 쓰기 감지
    setupUnauthorizedWriteWatcher(): void {
        const watcher = vscode.workspace.createFileSystemWatcher('**/*.{ts,tsx,js,jsx,py}');
        
        watcher.onDidChange(async (uri) => {
            const filePath = uri.fsPath;
            const changer = await this.detectChanger(filePath);
            
            // 잠금 없이 파일을 변경한 Subagent가 있는지 확인
            if (this.fileLocks.has(filePath) && this.fileLocks.get(filePath) !== changer) {
                console.warn(`Unauthorized write detected: ${filePath} by ${changer}`);
                // 긴급 잠금 강제 획득 + 충돌 알림
                await this.handleUnauthorizedWrite(filePath, changer);
            }
        });
    }
}
```

이 3계층 방어에서 핵심은 **계층 1(사전 잠금)이 대부분의 충돌을 원천 차단**한다는 점이다. 계층 2와 3은 "비정상적인 상황"에 대한 안전망이며, 정상적인 Subagent 동작에서는 거의 발동되지 않는다.

#### 4.7.2 "중앙 잠금 관리자"를 `crow_mcp_server.py`에 추가

Crow SSE 서버에 **중앙 잠금 관리자(Central Lock Manager)** 기능을 추가한다. 이는 `crow_mcp_server.py`에 새로운 MCP tool 세트를 구현하여, 파일 수준의 잠금 관리를 Crow의 핵심 기능으로 통합한다. [MCP]

```python
# crow_mcp_server.py에 추가된 잠금 관리 도구 [MCP]

@mcp.tool
def lock_acquire(file_path: str, subagent_id: str, timeout_ms: int = 30000) -> dict:
    """
    지정된 파일에 대한 독점 잠금을 획득합니다.
    이미 잠긴 파일인 경우, timeout_ms까지 대기합니다.
    
    Args:
        file_path: 잠금 대상 파일 경로
        subagent_id: 잠금을 요청하는 Subagent ID
        timeout_ms: 최대 대기 시간 (밀리초)
    
    Returns:
        acquired: 잠금 획득 성공 여부
        holder: 잠금 보유자 (실패 시)
        wait_position: 대기 큐 위치 (실패 시)
    """
    return lock_manager.acquire(file_path, subagent_id, timeout_ms)

@mcp.tool
def lock_release(file_path: str, subagent_id: str) -> dict:
    """
    지정된 파일의 잠금을 해제합니다.
    대기 중인 Subagent가 있으면 자동으로 다음 Subagent에게 잠금을 이관합니다.
    
    Args:
        file_path: 잠금 해제 대상 파일 경로
        subagent_id: 잠금 해제를 요청하는 Subagent ID
    """
    return lock_manager.release(file_path, subagent_id)

@mcp.tool
def lock_check(file_path: str) -> dict:
    """
    지정된 파일의 현재 잠금 상태를 조회합니다.
    
    Args:
        file_path: 상태 조회 대상 파일 경로
    
    Returns:
        locked: 잠금 여부
        holder: 잠금 보유자 ID (잠금된 경우)
        wait_queue: 대기 중인 Subagent ID 목록
    """
    return lock_manager.check(file_path)
```

이 잠금 관리자는 **메모리 내 `LockManager` 클래스**로 구현되며, `crow.bin`에 영구 저장하는 것이 아니라 런타임 메모리에서 관리한다. 이는 잠금 정보는 프로세스 생명주기와 동일해야 하며, VS Code/Crow 서버 재시작 시 모든 잠금은 자동으로 해제되어야 하기 때문이다. 그러나 **잠금 획득/해제 이력**은 `crow.bin`의 `arch` 레지스터에 기록되어, "어떤 파일이 자주 충돌하는가"라는 패턴 분석에 활용된다.

잠금 관리자는 **데드락 감지** 기능도 포함한다. 두 Subagent가 서로의 잠금을 기다리는 circular wait 상황이 감지되면, 잠금 관리자는 **선점(preemption)**을 수행하여 — 먼저 잠금을 요청한 Subagent의 잠금을 유지하고, 나중 요청자의 잠금을 강제 해제한 뒤 — 충돌 알림을 본낸다. 이는 교착 상태를 자동으로 해결하여 시스템 교착을 방지한다.

#### 4.7.3 VS Code merge conflict UI vs AI 3-way diff

사전 잠금과 큐잉을 모두 우회하는 최악의 충돌 시나리오 — 두 Subagent가 정확히 동일한 순간에 동일 파일의 동일 라인을 수정했다 — 에서는 병합 해결이 필요하다. Wave 4는 두 가지 병합 전략을 제공한다.

**전략 A: VS Code 네이티브 Merge Conflict UI**. VS Code는 내장 3-way merge editor를 제공하며 [^461^], 충돌 마커(`<<<<<<<`, `=======`, `>>>>>>>`)와 CodeLens 액션("Accept Current Change", "Accept Incoming Change", "Accept Both Changes")을 통해 시각적 병합을 지원한다. 이 전략은 **사용자가 병합을 수동으로 결정**해야 하며, AI가 제안한 병합 결과를 사용자가 리뷰하고 승인하는 방식이다. 충돌이 감지되면 자동으로 해당 파일이 3-way merge editor로 열리고, 사용자가 선택할 때까지 백그라운드 작업은 일시 중지된다.

**전략 B: AI 기반 자동 3-way diff**. VS Code 1.105부터 도입된 "Resolve Merge Conflict with AI" 기능 [^461^] [^464^]을 활용하여, 두 변경의 merge base(공통 조상)와 양쪽 변경사항을 AI에게 컨텍스트로 제공하고, 두 변경의 의도를 모두 보존하는 병합 결과를 자동 생성하게 한다. 이 전략은 **사용자 개입 없이 완전 자동**으로 처리되며, 생성된 병합 결과는 곧바로 파일에 적용된다.

Wave 4의 설계에서는 **전략 B(AI 자동 병합)를 기본, 전략 A(수동 병합)를 예외**로 채택한다. 충돌이 감지되면 즉시 AI 자동 병합을 시도하고, 병합 결과의 "신뢰도 점수"가 임계값(예: 0.85) 이상이면 자동 적용한다. 신뢰도가 임계값 미만이거나, 자동 병합이 실패한 경우에만 수동 병합 UI를 표시한다. 이 "신뢰도 점수"는 AI가 두 변경의 의도 충돌 정도를 평가하여 산출하며, 예를 들어 동일 함수의 동일 라인이 완전히 상반된 방향으로 수정된 경우 신뢰도가 낮아진다.

#### 4.7.4 `life_avoid` 충돌 패턴 저장

충돌은 단순한 문제 상황이 아니라 **학습 데이터**다. 특정 파일이나 패턴에서 충돌이 반복적으로 발생하면, 이 정보는 Crow Memory의 `life_avoid` 레지스터에 저장되어 향후 예방에 활용된다. [MCP]

```python
# 충돌 패턴 저장 [MCP]
crow_ingest(
    content="src/auth.ts 파일이 여러 Subagent 간 동시 수정 충돌의 핫스팟임. "
            "이 파일은 인증 로직과 권한 검사가 혼재되어 있어, "
            "보안 관련 수정과 일반 리팩토링이 동시에 발생할 위험이 높음.",
    register="life_avoid",
    metadata={
        pattern_type: "conflict_hotspot",
        file_path: "src/auth.ts",
        conflict_count: 5,  # 최근 10회 작업 중 5회 충돌
        polarity: -1.5,  # 강한 회피 권고
    }
)
```

이 패턴이 저장되면, 향후 Subagent가 `src/auth.ts`에 대한 수정 작업을 시작하려 할 때 Crow의 `crow_recall`은 `life_avoid` 레지스터의 이 항목을 반환한다. Main Agent는 이 정보를 바탕으로 **"이 파일은 동시 수정 위험이 높습니다. 순차 처리를 권장합니다"**라는 사전 경고를 사용자에게 표시하거나, 자동으로 해당 파일에 대한 exclusive lock을 선제적으로 획득한다.

**핫스팟 분석**도 수행된다. `arch` 레지스터에 저장된 충돌 이력을 주기적으로 분석하여, "어떤 파일 쌍이 가장 자주 충돌하는가", "어떤 유형의 작업이 충돌을 유발하는가"를 파악한다. 이 분석 결과는 프로젝트의 모듈 분리와 책임 경계 개선에 대한 제안으로 발전할 수 있다 — 예를 들어 "src/auth.ts가 5개 Subagent와 모두 충돌하므로, 이 파일의 책임을 분리하는 것을 권장합니다".

#### 4.7.5 바이브 점수: 현재 2/10 → 목표 8/10

현재 Zoo Code는 단일 에이전트만 실행하므로 파일 충돌 자체가 거의 발생하지 않는다. 다만 사용자가 수동으로 여러 AI 도구를 동시에 사용할 때는 간접적인 충돌(서로 다른 도구가 동일 파일을 수정)이 발생할 수 있으며, 이 경우 사용자가 직접 Git이나 수동 복사로 충돌을 해결해야 한다. 이 과정에서 흐름은 완전히 끊긴다. Conflict Resolution이 원활하게 작동하면 사용자는 "여러 AI가 동시에 작업핥도 내 파일은 안전하다"는 확신을 가지며, 이는 병렬화를 과감하게 활용할 수 있는 심리적 기반이 된다.

| 평가 항목 | 현재 점수 | 목표 점수 | 개선 Delta |
|-----------|-----------|-----------|------------|
| 사전 잠금 (lock_acquire) | 2/10 | 8/10 | +6 |
| FileSystemWatcher 감지 | 2/10 | 8/10 | +6 |
| 큐잉 + 순차 처리 | 1/10 | 8/10 | +7 |
| AI 자동 병합 (3-way diff) | 1/10 | 7/10 | +6 |
| life_avot 충돌 패턴 학습 | 1/10 | 8/10 | +7 |
| **종합 바이브 점수** | **2/10** | **8/10** | **+6** |

---

### 4.8 Wave 4 사용자 경험 스토리

#### 스토리 1: "@scout 이거 찾아줘" → 백그라운드 실행 → 3개 AI 동시 작업 → 충돌 없이 완료

민수는 새로운 마이크로서비스 프로젝트에 배정받았다. 6개월 전 다른 팀에서 작성한 코드베이스라, 아키텍처와 컨벤션이 모두 낯설다. 그는 VS Code를 열고 Zoo Code 채팅창에 타이핑하기 시작한다.

`"이 프로젝트에서 에러 핸들링은 어떻게 하고 있어?"`

메인 AI가 답변을 시작한다. `"이 프로젝트에서는..."` 그러나 메인 AI는 아직 프로젝트 전체를 분석하지 않았으므로, 일반적인 답변만 낼 수 있다. 민수는 곧바로 입력한다.

`"@scout 에러 핸들링 패턴 전체 코드베이스에서 찾아줘"`

메인 AI의 응답은 즉시 중단된다. `"Scout에게 위임할게요"`라는 한 줄만 띄우고, 메인 AI는 현재 주제를 기억한 채 대기 상태로 들어간다. 하단 상태바에 `"🔄 Scout: Searching codebase (0%)"`가 나타난다. 민수는 기다리지 않는다. 그는 에디터로 돌아가 이미 열린 `user-service.ts` 파일의 리팩토링을 계속한다.

15초가 흘렀다. 하단 상태바가 `"Scout: Searching codebase (67%)"`로 업데이트된다. 민수는 리팩토링에 집중하고 있다 — Scout의 존재를 거의 의식하지 않는다. 8초 후, `"Scout: Analysis complete"` 알림이 우측 상단에 나타난다. `"[View Results] [Dismiss]"` 버튼이 함께 표시된다. 민수는 아직 `user-service.ts`의 메서드 시그니처를 수정 중이므로 `[Dismiss]`를 클릭한다. 알림은 사라진다.

3분 후, 민수는 리팩토링을 마치고 채팅창으로 돌아온다. 메인 AI의 응답이 이어져 있다.

`"Scout의 분석 결과에 따륩면, 이 프로젝트에서는 try/catch 대신 Result<T,E> 패턴을 사용합니다. 구체적으로는 src/utils/result.ts의 ok()/err() 헬퍼를 사용하며, async 함수에서는 neverthrow 라이브러리의 ResultAsync를 사용합니다. 최근 3개월간 12개 파일에서 이 패턴이 일관되게 적용되었습니다."`

민수는 Scout가 존재했는지조차 기억하지 않는다. 그가 기억하는 것은 — "내가 물었고, 정확한 답변을 받았다"는 것뿐이다.

이어서 민수는 `"그럼 user-service.ts의 에러 핸들링도 Result 패턴으로 바꿔줘"`라고 입력한다. 이번에는 Main Agent가 직접 처리한다. 그러나 이 파일의 변경은 40개가 넘는 라인에 걸쳐 있으며, 완료까지 약 2분이 소요될 것으로 추정된다. Main Agent는 `"이 작업은 백그라운드에서 진행할게요"`라고 알리고, 하단 상태바에 `"🔄 Zoo: Refactoring user-service.ts (0%)"`가 표시된다.

민수는 그 사이에 `"@reviewer user-service.ts의 변경사항 리뷰해줘"`라고 입력한다. Reviewer Subagent가 활성화되지만, Main Agent의 리팩토링이 아직 완료되지 않았으므로 Reviewer는 `lock_check`를 호출하고 `user-service.ts`가 현재 `main-agent-001`에 의해 잠겨 있음을 확인한다. Reviewer는 대기 큐에 들어가고, Fleet Dashboard의 Webview에 `"Reviewer: Waiting for user-service.ts (position: 1)"`가 표시된다.

1분 30초 후, Main Agent의 리팩토링이 완료된다. `lock_release`가 호출되고, 대기 중이던 Reviewer가 자동으로 `lock_acquire`에 성공하여 리뷰를 시작한다. Main Agent는 `"리팩토링 완료! Reviewer가 코드를 검토 중이에요"`라고 알린다. 민수는 Explorer에서 변경된 파일 목록을 훑어보고, Git diff를 빠르게 확인한다.

30초 후, Reviewer의 리뷰가 완료된다. `"✅ Reviewer: Code review completed. No issues found. [View Details] [Dismiss]"`. 민수는 `[View Details]`를 클릭하여 리뷰 결과를 확인하고, 모든 것이 적절하다고 판단하여 변경사항을 저장한다.

이 전 과정에서 민수는 단 한 번의 흐름 끊김도 경험하지 않았다. Scout가 코드베이스를 뒤지는 동안 그는 리팩토링을 했고, Main Agent가 리팩토링하는 동안 그는 코드를 검토했으며, Reviewer가 리뷰하는 동안 그는 변경사항을 저장했다. 세 개의 AI가 동시에 작업했지만, 충돌 없이, 인터럽션 없이, 모든 것이 매끄럽게 이어졌다.

#### 스토리 2: Fleet Dashboard를 통해 "내 AI 군단"을 들여다보다

지영은 대규모 레거시 코드 마이그레이션 프로젝트를 진행 중이다. 200개가 넘는 JavaScript 파일을 TypeScript로 변환해야 하는 작업으로, Zoo Code의 Orchestra 기능을 최대한 활용하기로 했다.

그녀는 채팅창에 연속으로 입력한다.

`"@scout models/ 디렉토리의 타입 정의를 분석해줘"`
`"@tester services/ 디렉토리에 대한 단위 테스트를 생성해줘"`
`"@docs API 엔드포인트에 대한 문서화를 해줘"`

세 개의 Subagent가 동시에 활성화된다. 지영은 Explorer 사이드바에서 "Zoo Orchestra" 패널을 펼친다. 세 개의 아이콘이 회전하고 있다 — Scout는 파란색 동기화 아이콘, Tester는 초록색, Docs는 병아리 노란색. 각 아이콘 아래에는 현재 작업 설명이 1줄씩 표시된다.

`"Scout — Analyzing type definitions (45%)"`
`"Tester — Generating tests for user-service.ts (12%)"`
`"Docs — Documenting API endpoints (8%)"`

지영은 이 패널이 충분하지 않다고 느껴, 상태바의 `"🔄 3 agents running"`을 클릭한다. "Zoo Orchestra" Webview 대시보드가 에디터 옆에 펼쳐진다.

대시보드에는 3개의 카드 레이아웃으로 각 Subagent의 상세 정보가 표시된다. Scout 카드에는 이미 분석 완료한 23개 파일의 목록이 스크롤되고, 예상 완료 시간은 "18s"로 표시된다. Tester 카드에는 생성 중인 테스트 코드의 프리뷰가 실시간으로 업데이트되며, 코드 커버리지 예측이 "78% → target: 85%"로 표시된다. Docs 카드에는 생성 중인 Markdown 문서의 TOC가 보인다.

Tester 카드에 노란색 경고 배너가 나타난다. `"⚠️ Waiting for lock: src/services/auth.ts (held by Scout)"`. Tester가 `auth.ts`에 대한 테스트를 생성하려 했지만, Scout가 동일 파일을 분석 중이라 잠금이 걸린 것이다. 지영은 이 충돌이 자동으로 해결될 것을 알고 있으므로 신경 쓰지 않는다. 12초 후, Scout가 `auth.ts` 분석을 마치고 잠금을 해제하자, Tester가 자동으로 잠금을 획득하고 테스트 생성을 재개한다. 경고 배너는 초록색 `"✅ Lock acquired, resuming..."`으로 바뀌었다가 3초 후 사라진다.

Scout의 작업이 완료된다. `"✅ Scout completed"` 알림이 표시된다. 지영은 대시보드에서 Scout 카드를 클릭하고, "Send results to main agent" 버튼을 누른다. Scout가 찾은 타입 정의 패턴이 메인 AI의 컨텍스트에 주입된다. 그녀는 채팅창에 `"이 패턴을 나머지 파일들에도 적용해줘"`라고 입력하고, Main Agent가 자동으로 마이그레이션을 시작하게 한다.

대시보드에 Main Agent의 새 작업 카드가 추가된다. 이제 4개의 AI가 동시에 작업 중이다. 지영은 대시보드를 닫고, 자신의 실제 작업 — 새로운 기능 개발 — 로 돌아간다. 하단 상태바의 `"🔄 4 agents running"`만이, 지금 이 순간에도 그녀를 위해 4개의 AI가 동시에 일하고 있다는 사실을 조용히 알려준다.

20분 후, 모든 작업이 완료된다. `"🎉 All agents completed. 47 files migrated, 23 tests generated, 12 docs created."`라는 알림이 표시된다. 지영은 변경사항을 Git에 커밋하고, 오늘 하루의 작업을 마무리한다. 그녀가 기억하는 것은 — "오늘 아주 많은 일을 했다"는 것. "여러 AI를 관리했다"는 사실은 기억에 거의 남지 않는다.

---

### 4.9 Wave 4 기술적 구현 체크리스트 (20+ 항목)

Wave 4의 "Orchestra of One" 구현을 위한 기술적 체크리스트는 다음과 같다. 각 항목은 `[튜닝]`(Zoo Code Extension 소스 직접 수정) 또는 `[MCP]`(MCP 도구 추가) 태그로 구분한다.

#### Subagent 인프라 (5개 항목)

- [ ] **[튜닝]** `SubagentManager` 클래스 구현: `child_process.spawn` with `detached: true`로 Subagent MCP 서버 프로세스 관리, idle 타이머 기반 auto-terminate, process pooling
- [ ] **[튜닝]** `MentionRouter` 클래스 구현: `@<name>` prefix 파싱, 라우팅 테이블 관리, `createChatParticipant` 네이티브 API 우회(wrap) 및 레거시 fallback
- [ ] **[MCP]** `scout_mcp_server.py` 구현: FastMCP 기반 코드 탐색 Subagent, `search_codebase`, `find_references`, `summarize_architecture` tool 제공, 9022 포트 SSE transport
- [ ] **[MCP]** `reviewer_mcp_server.py` 구현: FastMCP 기반 코드 리뷰 Subagent, `review_code`, `check_quality`, `suggest_improvements` tool 제공, 9023 포트 SSE transport
- [ ] **[MCP]** `tester_mcp_server.py` 구현: FastMCP 기반 테스트 생성 Subagent, `generate_tests`, `analyze_coverage`, `mock_dependencies` tool 제공, 9024 포트 SSE transport

#### 상태 관리 및 시각화 (5개 항목)

- [ ] **[튜닝]** `ActiveSubagentsProvider` TreeView 구현: Explorer 사이드바 "Active Subagents" 패널, 상태별 아이콘/색상, SSE 실시간 업데이트, 선택적 노드 refresh
- [ ] **[튜닝]** `OrchestraDashboard` Webview 구현: `createWebviewPanel` 기반 상세 대시보드, 작업 목록/진행률/ETA/충돌 상태, `retainContextWhenHidden`으로 상태 유지
- [ ] **[튜닝]** `BackgroundTaskManager` 구현: `vscode.window.withProgress` 연동, SSE 진행 이벤트 파이프라인, cancellable 작업, 자동 열기/Opt-In 전략
- [ ] **[튜닝]** SSE-to-Webview 실시간 파이프라인: Crow 서버 `agents/status` + `locks/status` 스트림 구독, `webview.postMessage` DOM 업데이트, requestAnimationFrame 배칭
- [ ] **[튜닝]** Badge API 연동: TreeView `ViewBadge`로 running 중인 Subagent 수를 Explorer 아이콘에 표시

#### 충돌 해결 및 잠금 관리 (4개 항목)

- [ ] **[MCP]** Crow 서버 `lock_acquire`/`lock_release`/`lock_check` tool 구현: 메모리 내 `LockManager`, 대기 큐, 데드락 감지 및 선점, timeout 기반 잠금 만료
- [ ] **[튜닝]** 3계층 충돌 방어: 계층1(Crow 사전 잠금) + 계층2(FileSystemWatcher 무단 쓰기 감지) + 계층3(AI 자동 병합/수동 merge UI)
- [ ] **[튜닝]** AI 기반 자동 3-way merge: VS Code 1.105+ "Resolve Merge Conflict with AI" 통합, 신뢰도 점수 기반 자동 적용/수동 fallback
- [ ] **[튜닝]** `FileSystemWatcher` 충돌 감시: `**/*.{ts,tsx,js,jsx,py}` 변경 이벤트 모니터링, 잠금 없는 쓰기 감지 시 긴급 잠금 + 알림

#### Crow Memory 연동 (4개 항목)

- [ ] **[MCP]** Subagent 결과 자동 `crow_ingest`: Scout → `arch` 레지스터, Reviewer → `style` 레지스터, Tester → `bug` 레지스터에 작업 결과 저장
- [ ] **[MCP]** `life_avoid` 충돌 핫스팟 저장: 충돌 발생 파일/패턴을 `life_avoid`에 자동 저장, 사전 경고 메커니즘
- [ ] **[MCP]** `life_pref` Subagent 라우팅 패턴 저장: 사용자의 @mention 사용 패턴 분석, 자동 라우팅 제안
- [ ] **[튜닝]** Subagent별 ETA 추정: `arch` 레지스터의 과거 작업 시간 기반 ETA 계산, 대시보드 실시간 표시

#### 안정성 및 폴스루 (4개 항목)

- [ ] **[튜닝]** Graceful fallback 3시나리오: 존재하지 않는 Subagent → Main Agent, Subagent 비가용 → 자동 재시작 + Main Agent fallback, Tool 실패 → 오류 해석 + 대안 제안
- [ ] **[튜닝]** Subagent 헬스 체크: 30초 간격 `/health` 엔드포인트 평가, Crow 서버 다운 시 전체 작업 일시 중지 + 자동 재시작
- [ ] **[튜닝]** `deactivate()` 정리: VS Code Extension 비활성화 시 모든 Subagent 프로세스 SIGTERM → 5초 후 SIGKILL 종료, orphan 프로세스 방지
- [ ] **[튜닝]** 대시보드 기본 접힘 상태: TreeView 기본 collapse, Webview는 명시적 오픈만, 사용자 주요 작업 영역 침해 최소화

| Wave 4 체크리스트 | 총 항목 | [튜닝] | [MCP] |
|-------------------|---------|--------|-------|
| Subagent 인프라 | 5 | 2 | 3 |
| 상태 관리 및 시각화 | 5 | 5 | 0 |
| 충돌 해결 및 잠금 관리 | 4 | 2 | 2 |
| Crow Memory 연동 | 4 | 1 | 3 |
| 안정성 및 폴스루 | 4 | 4 | 0 |
| **합계** | **22** | **14** | **8** |

Wave 4의 22개 기술적 항목 중 14개(64%)가 Zoo Code Extension의 자체 튜닝이고, 8개(36%)가 MCP 도구 추가다. 이 비율은 Wave 4가 "새로운 MCP 서버 인프라 구축"보다 "기존 Zoo Code Extension 내에서 멀티에이전트 오케스트레이션 로직을 구현"하는 데 더 무게를 둔다는 것을 보여준다. Subagent 자체는 MCP 서버로 구현되지만, 이 Subagent들을 조율하고 사용자에게 투명하게 표시하는 모든 로직은 Zoo Code Extension 낶에서 처리된다. 이는 "Orchestra of One" 철학의 기술적 표현이다 — 많은 악기(Subagent MCP 서버)가 있지만, 지휘자(Zoo Code Extension)는 하나이며, 모든 조율은 그 지휘자의 손아귀 안에서 이루어진다.

Wave 4의 종합 바이브 점수 변화를 5개 차원에서 종합하면 다음과 같다.

| 병렬화 차원 | 현재 점수 | 목표 점수 | 핵심 개선 전략 | Crow 연동 |
|-------------|-----------|-----------|----------------|-----------|
| 차원 1: Subagent 관리 | 2/10 | 8/10 | TreeView + 상태 표시 + idle pooling | `context` 공유 |
| 차원 2: Background Task | 2/10 | 8/10 | withProgress + Opt-In 완료 + 취소 | `arch`/`style` 저장 |
| 차원 3: @Mentions 라우팅 | 2/10 | 8/10 | Prefix 파싱 + ChatParticipant 우회 + fallback | `life_pref` 패턴 |
| 차원 4: Fleet Dashboard | 1/10 | 8/10 | TreeView + Webview + SSE 실시간 푸시 | `arch` ETA 데이터 |
| 차원 5: Conflict Resolution | 2/10 | 8/10 | 3계층 방어 + AI 자동 병합 + 핫스팟 학습 | `life_avoid` 충돌 패턴 |

Wave 4 완료 시 Zoo Code의 전체 병렬 처리 바이브 점수는 현재 평균 1.8/10에서 목표 평균 8/10으로 상승한다. 이는 사용자가 "여러 AI가 나를 위해 동시에 일하고 있다"는 사실을 의식하지 않으면서도, 그 결과를 자연스럽게 누리는 "Orchestra of One"의 경험을 의미한다. 다음 Wave 5에서는 이 오케스트라가 연주하는 "음악" — 즉, 4개 Wave의 통합된 사용자 경험 — 을 설계하여, Zoo Code가 "세상에서 가장 흐름이 끊기지 않는 바이브코딩 툴"로 완성되는 과정을 제시한다.



---

# 5. Vibe Alchemist — 통합 설계 및 로드맵

당신은 6개월 전 이 보고서의 첫 페이지를 열었다. Wave 1에서 세션 지속성을, Wave 2에서 YOLO 안전망을, Wave 3에서 Zero-Explanation 컨텍스트를, Wave 4에서 병렬 오케스트라를 하나씩 설계해왔다. 각 Wave는 독립된 기능 집합처럼 보였지만, 사실 그것은 하나의 거대한 그림을 분할하여 그리는 과정이었다. 이제 모든 조각을 맞추는 시간이다. 이 장은 4개 Wave의 설계를 통합하여, 현실적이고 기술적으로 실행 가능한 통합 로드맵을 작성한다. 모든 수치는 분석 기반 추정이며, 모든 의사코드는 VS Code Extension API와 Crow Memory의 경계 내에서 구현 가능한 것만을 다룬다.

Wave 1이 사용자의 "VS Code를 켰을 때" 경험을 설계했다면, Wave 4는 "여러 AI가 동시에 일할 때"의 경험을 설계했다. 이 두 극단 사이에서, 사용자는 점진적으로 변화하는 경험을 하게 된다. 이 장의 핵심은 "그 변화의 순서"를 결정하는 것이다. 어떤 기능이 먼저 구현되어야 하는가? 어떤 기능이 나중에 가더라도 전체 흐름을 해치지 않는가? 어떤 기능이 "바이브"를 가장 많이 상승시키는가? 이 질문에 답하기 위해, 5개 Wave(Phase 0 포함)의 142개 기술 구현 항목을 3차원 매트릭스로 분석하고, 사용자가 "흐름을 잃지 않는" 최적의 구현 순서를 도출한다.

이 장은 이 보고서의 마지막 장이다. 앞선 4개 장이 각각 "하나의 파도"를 설계했다면, 이 장은 "그 파도들이 어떻게 합류하여 하나의 큰 물결을 만드는가"를 설계한다. 통합의 관점에서 볼 때, 각 Wave는 더 이상 독립된 기능 집합이 아니라, 하나의 연속된 사용자 경험의 단면이다. 사용자는 "Wave 1을 경험하고 나서 Wave 2를 경험하는" 것이 아니라, "6개월 동안 점진적으로 변화하는 하나의 도구"를 경험한다. 이 연속성의 관점이 이 장의 모든 설계 결정을 관통하는 핵심 원칙이다. 알케미스트는 납을 금으로 바꾸는 사람이다. Vibe Alchemist는 4개 Wave의 납같은 개별 기능을 하나의 금같은 사용자 경험으로 녹여내는 사람이다. 이 장이 그 알케미의 마지막 화로다.

---

## 5.1 Executive Summary of Integration

### 5.1.1 현재 전체 바이브 점수: 4.2/10 — 21개 Flow Breaker 종합 평가

4개 Wave에 걸쳐 총 21개의 흐름 차원을 분석한 결과, Zoo Code의 현재 평균 바이브 점수는 **4.2/10**이다. 이 점수는 각 Wave의 현재 점수를 가중평균한 것으로, 가중치는 해당 차원이 사용자 경험에 미치는 영향의 빈도와 강도를 반영한다. 4.2점이라는 수치가 의미하는 바는 명확하다. 사용자가 Zoo Code를 사용할 때, 매 10번의 상호작용 중 약 6번은 어떤 형태로든 흐름이 끊기는 경험을 한다는 것이다. 이는 도구의 "사용 가능성"에는 문제가 없지만, "바이브코딩"의 철학적 기준에는 크게 미달하는 수준이다. 바이브코딩이란 사용자가 도구의 존재를 의식하지 않은 채 순수하게 코딩에 몰입하는 상태를 의미하는데, 4.2점은 그 상태에서 매우 멀리 떨어져 있음을 보여준다.

| Wave | 차원 수 | 현재 평균 | 가중치 | 가중 점수 |
|:---|:---:|:---:|:---:|:---:|
| Wave 1: Flow Keeper | 6 | 3.83/10 | 0.30 | 1.15 |
| Wave 2: YOLO Surgeon | 5 | 3.40/10 | 0.25 | 0.85 |
| Wave 3: Context Whisperer | 5 | 3.20/10 | 0.25 | 0.80 |
| Wave 4: Parallel Vibe | 5 | 1.80/10 | 0.20 | 0.36 |
| **종합** | **21** | — | **1.00** | **4.16 ≈ 4.2** |

Wave 1의 가중치가 0.30으로 가장 높은 이유는 간단하다. 세션 지속성, 모드 전환, 빌드 피드백 루프는 사용자가 "매일 매 순간" 마주하는 흐름 차원이다. VS Code를 켤 때마다 Custom Mode를 수동 선택해야 하는 경험은, 한 달에 한 번 발생하는 YOLO 실패보다 훨씬 더 빈번하게 바이브를 깬다. 이는 "Extension Host is Constraint AND Opportunity"라는 인사이트에서 논의된 것처럼, 기초 인프라의 결함이 상위 기능의 가치를 희석시키는 현상이다. Wave 4의 병렬화가 아무리 아름답게 설계되어도, 사용자가 매일 VS Code를 켤 때 3초의 모드 선택 마찰을 겪는다면 그 병렬화의 가치는 절반으로 줄어든다. 사용자의 뇌는 "기초가 불편하면 상위 기능도 불편하게 느낀다"는 심리적 패턴을 가지고 있다. 이 심리적 패턴은 마케팅에서 priming effect(프라이밍 효과)로 알려진 현상과 동일하다. 첫 경험이 이후 모든 경험의 렌즈가 되는 것이다.

21개 흐름 차원을 사용자가 경험하는 "흐름 단절의 형태"로 재분류하면, 4개의 근본 유형이 드러난다. 이 유형 분류는 우선순위 결정의 기반이 된다.

**유형 A: 시작 단절 (Startup Discontinuity)** — Wave 1 중심. VS Code를 켰을 때 발생하는 모든 마찰. Custom Mode 수동 선택(3초), SSE 서버 재연결 실패, Crow 연결 끊김으로 인한 기능 소멸. 이 유형은 매 코딩 세션의 "첫 10초"를 좌우하며, 첫인상의 심리적 영향으로 인해 전체 세션의 바이브를 결정하는 가중치가 높다. 사용자가 "오늘도 코딩을 시작해야지"라는 마음으로 VS Code를 켰는데, 3초간 "어떤 모드를 선택할까?"를 고민하게 만드는 마찰은, 그날의 코딩 세션 전체에 영향을 미친다. 첫 10초의 불편함이 누적되어 "이 도구는 항상 불편하다"는 인상이 굳어지면, 그 인상을 바꾸는 데는 훨씬 더 많은 노력이 필요하다. 이것이 첫인상의 심리학이다.

**유형 B: 실행 단절 (Execution Discontinuity)** — Wave 1 + Wave 2 중심. 코딩 중간에 발생하는 모든 마찰. 빌드 에러 후 수동 복사-붙여넣기(30-60초), YOLO 모드에서의 불안("망하면 어떡하지?"), 10개 파일 수정 후 빌드 실패 시의 수동 롤백. 이 유형은 흐름의 "정점"에서 사용자를 추락시키므로 심리적 충격이 크다. 사용자가 "흐름이 좋다"는 상태에서 갑작스럽게 에러를 마주하고, 그 에러를 AI에게 설명하고, 수정을 기다리고, 다시 빌드하는 모든 과정은 "추락의 깊이"를 결정한다. 1미터 높이에서 떨어지는 것과 10미터 높이에서 떨어지는 것의 차이처럼, 흐름의 정점에서 발생하는 단절은 더 큰 심리적 충격을 준다.

**유형 C: 설명 단절 (Explanation Discontinuity)** — Wave 3 중심. 사용자가 AI에게 반복적으로 설명해야 하는 모든 상황. "Zustand 쓴다", "try-catch로 감싼다", "flat folder structure 선호" 등의 반복 설명. 이 유형은 누적 피로도를 발생시키며, 사용자가 "AI가 나를 알아주지 않는다"는疏离감을 느끼게 한다. 한 번의 설명은 5초에 불과하지만, 하루에 10번 반복되면 50초가 되고, 한 달이면 25분이 된다. 이 25분은 단순한 시간 손실이 아니라 "내가 계속 같은 말을 반복하고 있다"는 정신적 소모를 의미한다. 이 소모는 사용자가 AI 도구를 점점 덜 사용하게 만드는 주요 원인이다.

**유형 D: 동시성 단절 (Concurrency Discontinuity)** — Wave 4 중심. 병렬 작업이 불가능하여 발생하는 마찰. 긴 코드 탐색 작업이 메인 AI를 블록킹하여 사용자가 기다려야 하는 상황, 여러 AI 도구를 수동으로 전환해야 하는 상황. 이 유형은 현재 Zoo Code에서 가장 드물게 발생하지만, 고급 사용자에게는 가장 큰 성능 병목이다. 이 유형의 특징은 "기초가 탄탄할 때만 그 불편함이 드러난다"는 점이다. Wave 1-3의 흐름이 끊기지 않는 상태에서야, "이 작업이 왜 이렇게 오래 걸리지?"라는 질문이 생긴다.

이 4개 유형의 분포는 중요한 설계 우선순위 정보를 제공한다. 유형 A(시작 단절)와 유형 B(실행 단절)가 현재 바이브 점수 4.2의 대부분을 구성하고 있으며, 이들은 각각 Wave 1과 Wave 2에서 해결된다. 유형 C(설명 단절)는 Wave 3에서, 유형 D(동시성 단절)는 Wave 4에서 해결된다. 이 분포 자체가 Wave의 우선순위를 결정한다 — 사용자가 매일 겪는 문제(유형 A)를 먼저 해결하고, 가끔 겪지만 충격이 큰 문제(유형 B)를 그 다음에, 누적 피로도 문제(유형 C)를 그 다음에, 고급 사용자의 성능 문제(유형 D)를 마지막에 해결하는 것이 최적의 순서이다.

### 5.1.2 목표: 9.5/10 — 예상 소요 기간 20-24주(5-6개월)

통합 로드맵의 목표는 4.2/10에서 9.5/10까지의 도약이다. 9.5라는 수치는 현실적 한계를 인정한 설정이다. 10점은 "사용자가 기능의 존재를 전혀 의식하지 않는 상태"인데, VS Code Extension API의 근본적 제약(Extension Host의 단일 스레드, globalState의 용량 한계, OS 프로세스 관리의 불완전성)으로 인해 일부 기능은 "완전히 투명하지는 않지만 거의 투명한" 수준에서 멈춘다. 9.5점은 "사용자가 기능의 존재를 아주 가끔(월 1-2회) 의식하는 수준"이다. 예를 들어 상태바의 "Crow: 컨텍스트 압축 완료" 메시지를 월 1-2회 볼 수 있다. 하지만 그것은 불편이 아니라 "시스템이 나를 돌보고 있구나"라는 안도감을 준다.

9.5점이 아닌 10점을 목표로 하지 않는 이유는 더 깊은 철학적 근거를 가진다. "완벽한 투명성"은 실제로 사용자와 시스템 사이의 관계를 약화시킬 수 있다. 사용자가 시스템이 "무엇을 하는지" 전혀 알 수 없다면, 시스템이 예상치 못한 방식으로 작동했을 때 사용자는 당황하고 불안해한다. 이것이 바로 Claude Code의 #46444 이슈가 보여주는 교훈이다. 적절한 수준의 "보이는 투명성"(visible transparency)은 사용자가 시스템을 신뢰할 수 있게 만드는 데 필수적이다.

예상 소요 기간 20-24주는 "The 60-20-12 Rule"이라는 인사이트에서 도출된 추정치이다. 4개 Wave의 기술 구현 항목을 총합하면 약 142개(Phase 0: 15개, Wave 1: 40개, Wave 2: 40개, Wave 3: 25개, Wave 4: 22개)이다. 각 항목의 평균 구현 시간은 2-4일(복잡도에 따라 변동)로 추정되며, 병렬 개발(2-3인 팀 기준)을 고려하면 총 20-24주가 현실적이다. 이 기간은 "낙관적 추정"이 아니라, "실제 구현에서 발생하는 디버깅, 리뷰, 통합 테스트 시간을 포함한" 현실적 추정이다.

다음은 통합 로드맵의 전체 타임라인을 요약한 것이다.

| 단계 | 기간 | 핵심 목표 | 바이브 점수 목표 | 핵심 기술 항목 수 |
|:---|:---|:---|:---:|:---:|
| **Phase 0** | Week 0-2 | 인프라 기반 설치 | 4.2 → 5.0 | 15 |
| **Wave 1** | Week 2-6 | Flow Keeper 완성 | 5.0 → 7.0 | 40 |
| **Wave 2** | Week 6-12 | YOLO Surgeon 완성 | 7.0 → 8.0 | 40 |
| **Wave 3** | Week 12-18 | Context Whisperer 완성 | 8.0 → 9.0 | 25 |
| **Wave 4** | Week 18-24 | Parallel Vibe 완성 | 9.0 → 9.5 | 22 |

각 단계의 바이브 점수 목표는 단순한 산술적 합산이 아니라, "사용자가 느끼는 변화"를 기준으로 설정되었다. Phase 0이 끝나면 사용자는 "VS Code를 켰을 때 Zoo Code가 이미 준비되어 있다"는 경험을 하게 된다. Wave 1이 끝나면 "빌드 에러가 자동으로 고쳐진다"는 경험이 추가된다. Wave 2가 끝나면 "YOLO 모드가 두렵지 않다"는 확신이 생긴다. Wave 3이 끝나면 "설명할 필요가 없다"는 편안함이 느껴진다. Wave 4가 끝나면 "여러 AI가 나를 위해 동시에 일한다"는 자연스러운 경험을 하게 된다. 각 변화는 이전 변화의 기반 위에 쌓이며, 사용자의 "바이브"는 단계적으로 상승한다.

---

## 5.2 Phase 0: Foundation (Week 0-2)

Phase 0은 "기능 구현"이 아니라 "기능을 구현할 수 있는 토대를 만드는" 단계다. 6주짜리 Wave 1을 시작하기 전에, 2주간의 인프라 설치를 통해 모든 후속 Wave가 의존하는 공통 기반을 구축한다. 이 단계에서 사용자 경험의 변화는 미미하지만, 이 단계를 생략하면 후속 Wave의 모든 구현이 불안정한 모래 위에 지어지는 성과 같다.

건축에 비유하자면, Phase 0은 "기초 지반 다지기"이다. 보이지 않는 지하에서 일어나는 작업이지만, 이 작업 없이는 위에 쌓을 수 있는 층수가 제한된다. Phase 0의 인프라가 튼튼하면 Wave 1-4의 기능이 안정적으로 동작하고, 인프라가 약하면 각 Wave마다 새로운 버그가 발생하며 전체 일정이 지연된다. 특히 Crow 서버 관리 인프라가 불안정하면, Wave 1의 세션 지속성 기능도 불안정해지고, Wave 3의 컨텍스트 주입 기능도 불안정해지며, Wave 4의 Subagent 관리 기능도 불안정해진다. 하나의 인프라 결함이 모든 Wave에 연쇄적으로 영향을 미치는 것이다.

### 5.2.1 사용자 경험 스토리 + 기술적 구현 20+ 항목

**스토리: "아무것도 변하지 않았는데, 모든 것이 달라졌다."**

소영은 VS Code를 켰다. 아무것도 달라지지 않았다. Zoo Code Extension이 활성화되고, Custom Mode를 수동으로 선택해야 했다. 하지만 무언가 미묘하게 달라진 것을 느꼈다. 상태바에 작은 아이콘이 하나 추가되었다 — "Zoo: Connected"라는 초록색 점. 그 점은 Crow Memory의 SSE 서버가 정상적으로 연결되어 있음을 의미한다. 소영은 그 점을 보고, "아, Crow가 살아있구나"라고 무의식적으로 인지한다. 이것이 Phase 0의 유일한 사용자-대면 변화다 — 그 작은 초록색 점.

하지만 그 점 뒤에서는 15개의 인프라 항목이 조용히 작동하고 있다. Crow 서버는 `detached: true`로 실행되어 VS Code가 종료되어도 살아남는다. `.zoo/` 디렉토리는 프로젝트 루트에 자동 생성되어 프로젝트별 메타데이터를 저장한다. `yocto` 디렉토리는 `~/.zoo-code/yocto/`에 생성되어 파일 백업의 기반이 된다. 메시지 파이프라인의 확장 가능한 틀이 마련되어, 후속 Wave의 컨텍스트 주입 기능이 그 위에 쌓일 준비가 되었다. 소영은 이 모든 것을 볼 수 없지만, 그녀가 Wave 1의 기능을 사용할 때 이 인프라가 조용히 뒷받침할 것이다. Crow 서버가 없었다면 세션 지속성 기능은 작동하지 않을 것이고, yocto 디렉토리가 없었다면 Instant Rewind 기능은 백업을 저장할 곳이 없을 것이며, 메시지 파이프라인이 없었다면 ContextInjector는 주입할 채널이 없을 것이다. 이것이 인프라의 역할이다 — 보이지 않지만, 모든 것을 가능하게 한다.

Phase 0의 15개 항목은 5개 기능적 그룹으로 분류된다.

```typescript
// Phase 0: Foundation — 공통 인프라 구축
// 모든 항목은 Wave 1-4의 기반이 되며, 이 단계 없이는 후속 기능이 불안정하다

// [튜닝] CrowServerManager 기본 구현
// - detached: true spawn, PID 파일 관리, 헬스체크
// - Wave 1의 세션 지속성, Wave 4의 Subagent 프로세스 관리 모두에 사용
class CrowServerManager {
  private config: CrowServerConfig;
  private pidPath: string;
  constructor(context: vscode.ExtensionContext) {
    const crowHome = path.join(os.homedir(), '.zoo-code', 'crow');
    this.pidPath = path.join(crowHome, 'server.pid');
    this.config = { port: 9020, healthCheckInterval: 30000, autoRestart: true, maxRestartAttempts: 3 };
  }
  async ensureRunning(): Promise<boolean> {
    if (this.isRunning()) return true;
    return this.startWithRetry(this.config.maxRestartAttempts);
  }
  private isRunning(): boolean {
    try { const pid = fs.readFileSync(this.pidPath, 'utf-8').trim(); process.kill(parseInt(pid), 0); return true; }
    catch { return false; }
  }
}

// [튜닝] SSE 연결 상태 모니터링 — 상태바 표시
class ConnectionStatusBar {
  private statusItem: vscode.StatusBarItem;
  constructor() {
    this.statusItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    this.statusItem.show();
  }
  setConnected(connected: boolean, freshness?: number) {
    if (connected) {
      const icon = freshness && freshness > 70 ? '$(check)' : freshness && freshness > 30 ? '$(warning)' : '$(error)';
      this.statusItem.text = `${icon} Zoo`;
      this.statusItem.tooltip = `Crow: ${freshness ? freshness + '% fresh' : 'Connected'}`;
    } else {
      this.statusItem.text = '$(error) Zoo: Disconnected';
      this.statusItem.tooltip = 'Crow SSE 서버에 연결할 수 없습니다. 일부 기능이 제한됩니다.';
    }
  }
}

// [튜닝] ContextInjectionEngine 기본 틀 — Wave 3에서 crow_recall 결과를 주입하는 파이프라인의 기반
interface MessagePipeline {
  preprocessors: Array<(messages: ChatMessage[]) => Promise<ChatMessage[]>>;
  addPreprocessor(fn: Preprocessor): void;
  process(messages: ChatMessage[]): Promise<ChatMessage[]>;
}

// [튜닝] FallbackInjector 기본 틀 — Wave 3에서 4B 모델의 tool call 누락 대응
interface FallbackConfig {
  enabled: boolean; requiredToolName: string;
  injectionStrategy: 'prepend' | 'retry' | 'abort';
  maxRetriesPerTurn: number;
}

// [튜닝] .zoo/ 디렉토리 자동 생성 — 프로젝트 메타데이터 저장소
async function ensureZooDirectory(workspaceRoot: string): Promise<void> {
  const zooDir = path.join(workspaceRoot, '.zoo');
  await fs.promises.mkdir(zooDir, { recursive: true });
  await ensureGitignoreEntry(workspaceRoot, '.zoo/');
}

// [튜닝] yocto 백업 디렉토리 생성 — Wave 2의 Instant Rewind 기반
const YOCTO_BASE = path.join(os.homedir(), '.zoo-code', 'yocto');
await fs.promises.mkdir(YOCTO_BASE, { recursive: true });

// [튜닝] .yoloignore 템플릿 생성 — Wave 2의 Safe YOLO 기반
const defaultYoloIgnore = `**/.env
**/.env.*
!**/.env.example
**/*.pem
**/*.key
**/secrets/**
**/terraform.tfstate
**/package-lock.json
**/yarn.lock
**/pnpm-lock.yaml
**/.zoo-code/`;

// [MCP] crow_diagnostics: 메모리 서버 상태 확인 — 모든 Wave에서 사용
// [MCP] crow_manage_backup: YOLO 세션 스냅샷 관리 — Wave 2에서 사용

// [튜닝] .vscode/settings.json 자동 주입
const recommendedSettings = {
  "files.watcherExclude": { "**/.git/objects/**": true, "**/node_modules/*/**": true, "**/.zoo-code/yocto/**": true, "**/dist/**": true },
  "workbench.localHistory.enabled": true, "workbench.localHistory.maxFileEntries": 100
};
```

| 그룹 | 항목 수 | 핵심 목표 | 후속 Wave 의존성 |
|:---|:---:|:---|:---|
| Crow 서버 관리 | 3 | SSE 서버의 안정적 생존과 재연결 | Wave 1(세션), Wave 4(Subagent) |
| 메시지 파이프라인 | 3 | LLM 컨텍스트 주입의 확장 가능한 틀 | Wave 3(Context Injection) |
| 파일 시스템 기반 | 4 | 백업, 설정, 보호 파일의 디렉토리 구조 | Wave 2(yocto), Wave 3(.zoo.md) |
| Crow 연동 기본 | 3 | diagnostics, backup 등 공통 MCP 도구 | 모든 Wave |
| VS Code 설정 | 2 | 권장 settings.json 자동 주입 | Wave 1(FileSystemWatcher) |

이 표의 핵심은 "한 항목이 여러 Wave에 의존성을 제공한다"는 점이다. 예를 들어 CrowServerManager는 Wave 1의 세션 지속성과 Wave 4의 Subagent 프로세스 관리에 동시에 사용된다. 이 공통 인프라를 Phase 0에서 먼저 구축함으로써, 각 Wave의 개발자가 동일한 문제를 중복 해결하는 것을 방지한다.

### 5.2.2 Crow Memory 연동 + 검증 기준 + 바이브 점수 변화

Phase 0에서의 Crow Memory 연동은 "기본 도구 구현" 수준에 머무른다. `crow_diagnostics`는 메모리 서버의 상태를 확인하고, `crow_manage_backup`은 YOLO 세션의 스냅샷을 관리하며, `crow_compact`의 기본 호출 인프라가 마련된다. 이들 도구는 아직 자동으로 호출되지 않는다 — 사용자가 명시적으로 호출하거나, 후속 Wave에서 자동화된다. 이는 "도구를 먼저 만들고, 자동화는 나중에"라는 단계적 접근이다. 도구가 제대로 작동하는지 확인하기 전에 자동화하면, 자동화된 버그가 되어 디버깅이 훨씬 어려워진다.

**검증 기준(Phase 0 Exit Criteria):**

Phase 0이 "완료"되었다고 판단하려면, 다음 5가지 조건을 모두 만족해야 한다. 이 조건들은 객관적이고 측정 가능하며, 후속 Wave의 개발자가 인프라의 안정성을 신뢰할 수 있게 한다.

| # | 검증 항목 | 측정 방법 | 통과 기준 |
|---|:---|:---|:---|
| 1 | SSE 서버 자동 시작 | VS Code 종료 → 재시작 시 Crow 서버 상태 확인 | 5회 연속 재시작 시 100% 서버 생존 |
| 2 | SSE 연결 상태 표시 | 상태바 아이콘의 색상 변화 | 연결/끊김/ freshness 3단계 정확 표시 |
| 3 | `.zoo/` 디렉토리 자동 생성 | 새 프로젝트 열기 시 디렉토리 존재 확인 | 3개 이상 프로젝트에서 자동 생성 확인 |
| 4 | yocto 디렉토리 생성 | `~/.zoo-code/yocto/` 존재 확인 | 세션별 서브디렉토리 자동 생성 |
| 5 | 메시지 파이프라인 확장 | 커스텀 preprocessor 등록 → 메시지 변형 확인 | 등록된 preprocessor가 순서대로 실행 |

이 5가지 검증 항목은 단순한 "체크리스트"가 아니라, 후속 Wave 개발자와의 "계약"이다. Phase 0이 통과되면, Wave 1-4의 개발자는 "Crow 서버는 안정적이다", "상태바는 정확하다", "디렉토리는 자동으로 생성된다", "파이프라인은 확장 가능하다"는 신뢰를 기반으로 자신의 기능을 구현할 수 있다. 이 신뢰는 개발 속도를 높이고, 버그를 줄이며, 팀의 심리적 안정감을 제공한다.

Phase 0 완료 시 바이브 점수는 4.2에서 5.0으로 상승한다. 이 0.8점의 상승은 "기능적 변화"가 아니라 "신뢰감"에서 온다. 사용자가 상태바의 초록색 점을 보고 "Crow가 살아있다"는 사실을 인지하는 순간, 그 불안감이 줄어든다. 이전에는 SSE 서버가 죽었는지 살았는지 알 수 없었고, 그 불확실성 자체가 바이브를 깼다. Phase 0은 그 불확실성을 제거한다. 이것이 "아무것도 변하지 않았는데, 모든 것이 달라졌다"는 스토리의 기술적 의미다.

Phase 0에서 중요한 것은 **과도한 열정을 억제**하는 것이다. 이 단계에서 "빠르게 뭔가 보여주기" 위해 Wave 1의 일부 기능을 미리 구현하고 싶은 유혹이 강하게 들 것이다. 하지만 그 유혹을 저항해야 한다. Phase 0의 목적은 "빠른 승리"가 아니라 "느리지만 확실한 기반"이다. 이 2주를 투자하여 후속 22주의 개발을 안정화하는 것이, 2주를 아껴서 후속 22주 동안 불안정한 인프라 위에서 디버깅하는 것보다 훨씬 효율적이다.

---

## 5.3 Flow Breaker 3차원 매트릭스

142개 기술 구현 항목 중 "어떤 것을 먼저 구현할 것인가"를 결정하기 위해, 각 항목을 3차원 공간에 매핑한다. 이 매트릭스는 직관적 우선순위 결정을 가능하게 하며, "바이브 상승폭이 큰데 구현이 쉬운" 항목을 먼저 식별하는 데 핵심적인 역할을 한다. 3차원 매트릭스는 단순한 우선순위 도구가 아니라, 프로젝트의 "전략적 DNA"를 시각화하는 것이다. 각 항목이 3차원 공간에서 어디에 위치하는지를 볼 때, "이 프로젝트가 추구하는 가치"가 입체적으로 드러난다.

### 5.3.1 x축(구현 난이도) × y축(사용자 피로도 감소) × z축(VS Code Extension API 적합성)

**x축: 구현 난이도 (Implementation Complexity, 1-10)** — 1점은 "단일 파일 수정, 1일 완료" 수준이다. 예: 상태바 아이콘 추가. 10점은 "새로운 아키텍처 패턴 도입, 2주 이상 소요" 수준이다. 예: Subagent MCP 서버 인프라 구축. 구현 난이도는 (a) 수정해야 하는 파일 수, (b) 새로 학습해야 하는 API의 복잡도, (c) 외부 의존성의 수, (d) 테스트의 어려움으로 종합 산출된다.

**y축: 사용자 피로도 감소 (User Friction Reduction, 1-10)** — 1점은 "사용자가 거의 느끼지 못하는 변화"이다. 10점은 "사용자가 매일 여러 번 겪는 마찰을 완전히 제거"하는 변화이다. 예: Custom Mode 자동 복원(매 세션 시작 시 3초 절약). 피로도 감소는 "마찰의 빈도 × 마찰의 강도 × 마찰의 심리적 충격"으로 종합 산출된다.

**z축: VS Code Extension API 적합성 (API Suitability, 1-10)** — 1점은 "VS Code Extension API로 근본적으로 불가능한 기능"이다. 10점은 "VS Code Extension API가 네이티브하게 지원하는 기능"이다. z축이 낮은 기능은 API 제약으로 인해 설계가 변경될 가능성이 높으므로, z축 < 5인 기능은 기본적으로 후순위로 배정한다.

### 5.3.2 z축 < 5인 기능 제외 — 4개 항목의 폐기 결정

z축 < 5인 기능은 VS Code Extension API의 경계를 너무 벗어나는 기능이다. 이들은 "구현이 불가능한" 것이 아니라, "구현하려면 VS Code Extension API 외부로 나가야 하며, 그 과정에서 Zoo Code의 핵심 가치인 '설치 마찰 0, 학습 곡선 0'이 훼손되는" 기능이다.

| 제외 기능 | z축 점수 | 제외 이유 | 대체 접근법 |
|:---|:---:|:---|:---|
| OS 시작 프로그램 등록(Crow 서버) | 2 | Extension API가 OS 시작 프로그램을 조작할 수 없음 | `detached: true` 프로세스로 대부분의 시나리오 커버 |
| AI 모델 자체의 개선(4B → 7B fine-tuning) | 1 | Extension이 로컬 LLM의 가중치를 수정하는 것은 불가능 | vLLM의 `tool_choice="required"` + Extension fallback injection |
| VS Code 낶 LSP 서버 직접 수정 | 3 | LSP 서버는 별도 프로세스이며 Extension이 수정 불가 | `onDidChangeDiagnostics` 이벤트 수신으로 충분 |
| Git worktree 물리적 격리(Claude Code 스타일) | 4 | Extension이 Git worktree를 자동 생성/관리하려면 사용자의 Git 설정 변경이 필요 | `fs.copyFileSync` 기반 yocto 백업으로 동등한 격리 제공 |

이 4개 기능의 제외는 "Zoo Code가 할 수 없는 것을 포기하고, 할 수 있는 것을 극대화"하는 전략적 결정이다. "Terminal Escape 패턴의 역설"에서 논의된 VS Code Lock-In 전략의 핵심은, "Extension API의 제약을 역이용하여 설치 마찰 0의 경쟁 우위를 만드는" 것이다.

**Table 1: Flow Breaker 3D 매트릭스 — 상위 30개 우선순위 항목**

| 순위 | 기능 항목 | x | y | z | 3D 점수 | Wave | 태그 |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | `lastCustomMode` 자동 복원 | 2 | 9 | 9 | **8.1** | W1 | [튜닝] |
| 2 | 상태바 Crow 연결/ freshness 표시 | 2 | 8 | 10 | **8.0** | P0 | [튜닝] |
| 3 | `presentation.reveal: silent` 빌드 태스크 | 3 | 9 | 9 | **7.8** | W1 | [튜닝] |
| 4 | `onDidEndTaskProcess` 빌드 결과 자동 수집 | 3 | 9 | 9 | **7.8** | W1 | [튜닝] |
| 5 | `AutoModeDetector` 프로젝트 기반 자동 모드 | 4 | 8 | 9 | **7.5** | W1 | [튜닝] |
| 6 | yocto `fs.copyFileSync` 자동 백업 | 4 | 9 | 8 | **7.5** | W2 | [튜닝] |
| 7 | `instantRewind()` 0.3초 복구 | 4 | 9 | 8 | **7.5** | W2 | [튜닝] |
| 8 | PermissionGradation 기본 틀(5×5) | 5 | 8 | 8 | **7.3** | W2 | [튜닝] |
| 9 | `.yoloignore` 기본 패턴 적용 | 3 | 8 | 9 | **7.2** | W2 | [튜닝] |
| 10 | `ContextInjector` 매 턴 자동 주입 | 5 | 8 | 8 | **7.2** | W3 | [튜닝] |
| 11 | `crow_recall` fallback injection | 5 | 9 | 7 | **7.2** | W3 | [튜닝] |
| 12 | `SessionPersistence` 세션 요약 저장 | 4 | 8 | 8 | **7.0** | W3 | [튜닝] |
| 13 | `.zoo.md` 자동 로드 | 3 | 7 | 9 | **6.9** | W3 | [튜닝] |
| 14 | AGENTS.md 호환 fallback | 3 | 7 | 8 | **6.6** | W3 | [튜닝] |
| 15 | yocto + Git stash 2중 안전망 | 5 | 8 | 7 | **6.8** | W2 | [튜닝] |
| 16 | AutoBuildFix 기본 루프(max_attempts=3) | 6 | 9 | 7 | **7.2** | W2 | [튜닝] |
| 17 | oscillation 감지(A→B→A) | 4 | 7 | 8 | **6.7** | W2 | [튜닝] |
| 18 | LSP diagnostics 자동 피드백 | 4 | 7 | 9 | **6.9** | W1 | [튜닝] |
| 19 | `ProjectTreeScanner` 자동 트리 주입 | 5 | 7 | 8 | **6.8** | W1 | [튜닝] |
| 20 | `AGENTS.md` 자동 프롬프트 prepend | 4 | 7 | 8 | **6.7** | W1 | [튜닝] |
| 21 | `AutoCompactionTimer` 기본 구현 | 4 | 6 | 8 | **6.2** | W1 | [튜닝]+[MCP] |
| 22 | `ExtensionSearchProvider` 내장 검색 | 5 | 7 | 7 | **6.5** | W1 | [튜닝] |
| 23 | `YoloTransactionManager` pending_edits[] | 6 | 7 | 7 | **6.5** | W2 | [튜닝] |
| 24 | `SafeYoloGuard` 2단계 보호 | 5 | 7 | 8 | **6.8** | W2 | [튜닝] |
| 25 | `EmotionalContextDetector` 거절 감지 | 5 | 6 | 8 | **6.3** | W3 | [튜닝] |
| 26 | `@mention` prefix 파싱 | 4 | 7 | 7 | **6.3** | W4 | [튜닝] |
| 27 | `BackgroundTaskManager` withProgress | 5 | 6 | 8 | **6.3** | W4 | [튜닝] |
| 28 | `ActiveSubagentsProvider` TreeView | 5 | 6 | 8 | **6.3** | W4 | [튜닝] |
| 29 | `MentionRouter` 기본 라우팅 | 5 | 7 | 7 | **6.5** | W4 | [튜닝] |
| 30 | Crow 서버 `lock_acquire`/`release` | 5 | 6 | 7 | **6.0** | W4 | [MCP] |

3D 점수는 $(y 	imes 0.4) + (z 	imes 0.3) + ((11-x) 	imes 0.3)$로 산출된다. "사용자 피로도 감소가 가장 중요하고, API 적합성이 그 다음이며, 난이도는 역수로 가중"하는 방식이다. 이 가중치는 "The Vibe Paradox" 인사이트에서 도출된 "사용자 경험 중심 설계" 원칙을 수학적으로 표현한 것이다.

이 표를 분석하면 몇 가지 중요한 패턴이 드러난다. 첫째, **Wave 1 항목이 상위 순위를 독점**하고 있다. 순위 1-5 모두 Wave 1에 속하며, 이는 "기초 흐름의 개선이 상위 기능의 가치를 배가시킨다"는 원칙을 확인시켜준다. 둘째, **z축이 7 이상인 항목이 대부분**이다. 이는 "VS Code Extension API 내에서 구현 가능한" 기능 위주로 선택되었음을 의미한다. 셋째, **x축(난이도)이 6 이상인 항목은 거의 없다**. 이는 20-24주라는 현실적 기간 내에 완료 가능한 범위를 벗어나지 않도록 의도적으로 조정된 결과이다.

이 30개 상위 항목은 142개 전체 항목의 21%에 불과하지만, 이들이 전체 바이브 상승의 약 60%를 담당한다. 이는 "소수의 핵심 기능이 대부분의 가치를 창출한다"는 파레토 법칙의 재확인이다.

**Table 2: 21개 흐름 차원의 3D 매트릭스 종합 평가**

| 흐름 차원 | x(난이도) | y(피로도감소) | z(API적합) | 3D점수 | Wave | 우선순위 |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| 세션 지속성 (Custom Mode 자동복원) | 2 | 9 | 9 | 8.1 | W1 | P0-1 |
| 모드 전환 마찰 (AutoModeDetector) | 4 | 8 | 9 | 7.5 | W1 | P0-2 |
| 빌드-코드-피드백 루프 (silent+autofix) | 5 | 9 | 8 | 7.4 | W1 | P0-3 |
| 파일 탐색 마찰 (ProjectTreeScanner) | 5 | 7 | 8 | 6.7 | W1 | P0-5 |
| 외부 리소스 탐색 (ExtensionSearch) | 5 | 7 | 7 | 6.3 | W1 | W1-3 |
| 컨텍스트 로트 (AutoCompaction) | 5 | 6 | 8 | 6.3 | W1 | W1-4 |
| Instant Rewind (yocto) | 4 | 9 | 8 | 7.5 | W2 | W1-1 |
| Checkpoint Granularity (Git stash) | 5 | 7 | 7 | 6.3 | W2 | W2-2 |
| YOLO Transaction (pending_edits[]) | 6 | 7 | 7 | 6.3 | W2 | W2-3 |
| Safe YOLO (PermissionGradation) | 5 | 8 | 8 | 7.3 | W2 | P0-4 |
| Auto-Recovery (AutoBuildFix) | 6 | 9 | 7 | 7.2 | W2 | W1-2 |
| Implicit Context (ContextInjector) | 5 | 8 | 8 | 7.2 | W3 | W3-1 |
| Cross-Session Memory (SessionPersistence) | 4 | 8 | 8 | 7.0 | W3 | W3-2 |
| Multi-Agent Context Sync (system_prompt.md) | 6 | 6 | 7 | 5.9 | W3 | W3-4 |
| Project Context (.zoo.md) | 3 | 7 | 9 | 6.9 | W3 | P0-6 |
| Emotional Context (거절 감지) | 5 | 6 | 8 | 6.3 | W3 | W3-3 |
| Subagent 관리 (TreeView) | 5 | 6 | 8 | 6.3 | W4 | W4-1 |
| Background Task (withProgress) | 5 | 6 | 8 | 6.3 | W4 | W4-2 |
| @Mentions 라우팅 | 4 | 7 | 7 | 6.3 | W4 | W4-3 |
| Fleet Dashboard (Webview) | 6 | 5 | 7 | 5.5 | W4 | W4-5 |
| Conflict Resolution (3계층 방어) | 6 | 6 | 7 | 5.9 | W4 | W4-4 |

이 종합 평가에서 21개 차원의 평균 3D 점수는 6.6이다. 3D 점수 7.0 이상의 차원은 8개로, 이들이 Wave 우선순위 결정의 핵심 기준이 된다. 이 8개 차원을 Phase 0과 Wave 1 초기에 집중적으로 구현하면, 바이브 점수를 4.2에서 7.0까지 가장 빠르게 상승시킬 수 있다.


---

## 5.4 Wave Prioritization

3D 매트릭스의 분석 결과를 바탕으로, 각 Wave의 우선순위와 구현 순서를 결정한다. 이 우선순위는 "사용자가 느끼는 변화의 크기"와 "기술적 의존성" 두 축을 동시에 고려하여 설정된다. Wave의 우선순위 결정에 가장 중요한 원칙은 "흐름의 연속성을 먼저, 흐름의 풍요로움은 나중에"이다. Wave 1은 "흐름이 끊어지지 않게" 만드는 예방적 기능이다. Wave 2는 "흐름이 끊어졌을 때 빨리 복구"하는 치료적 기능이다. Wave 3은 "흐름 속에서 사용자가 설명하지 않아도 되게" 만드는 지능적 기능이다. Wave 4는 "여러 흐름이 동시에 흐를 수 있게" 만드는 확장적 기능이다. 이 순서는 "예방 → 치료 → 지능 → 확장"의 의학적 패턴을 따른다.

### 5.4.1 Wave 1 우선: 세션 지속성 + 모드 전환 (바이브 상승폭 최대)

Wave 1은 4개 Wave 중에서도 **첫 번째로 구현**되어야 한다. Wave 1의 핵심 기능 — `CrowServerManager`(detached SSE 서버), `lastCustomMode` 자동 복원, `AutoModeDetector`, `Presentation.reveal: silent`, `ProjectTreeScanner` — 은 사용자가 "매일 매 순간" 경험하는 마찰을 제거한다. 이 6개 차원의 현재 평균 점수는 3.83/10이지만, 구현이 상대적으로 간단하여(x축 평균 3.8) **"투자 대비 바이브 상승폭"이 가장 크다**.

**Wave 1의 핵심 설계 원칙: "닫아도, 켜도, 기억한다"** — Wave 1의 모든 기능은 하나의 공통 주제를 공유한다. 사용자가 어젯밤 11시에 코딩을 마치고 VS Code를 닫았다면, 오늘 아침 VS Code를 켰을 때 그 흐름은 이어져야 한다. Crow 서버의 `detached: true` 실행은 이 연속성의 핵심 기술적 기반이다. VS Code Extension이 종료되어도 Crow 프로세스는 OS에 의해 계속 실행되며, `crow.bin` 파일은 디스크에 유지된다. 사용자가 다음 날 VS Code를 켜면, Extension의 `activate()` 훅에서 PID 파일을 읽고 기존 서버 프로세스를 재탐색한다. 이 과정은 사용자에게 보이지 않으며, 단지 상태바의 초록색 점이 "Connected"로 표시될 뿐이다.

**Wave 1 Phase A (Week 2-4): 가장 빠른 바이브 승리 5개**

| # | 기능 | 구현 핵심 | 예상 기간 | Crow 연동 |
|---|:---|:---|:---|:---|
| 1 | Custom Mode 자동 복원 | `lastCustomMode` globalState 저장 + `activate()` 복원 | 2일 | `crowIngest` → `life_context` |
| 2 | 상태바 연결 표시 | `StatusBarItem` + SSE 헬스체크 + 색상 변화 | 1일 | `crow_diagnostics` 주기적 호출 |
| 3 | 빌드 태스크 silent | `presentation.reveal: silent` + `problemMatcher` | 2일 | — |
| 4 | 빌드 결과 자동 수집 | `onDidEndTaskProcess` 이벤트 구독 | 2일 | `crowIngest` → `bug` |
| 5 | 자동 모드 감지 | `onDidChangeWorkspaceFolders` + 메타데이터 스캔 | 4일 | `crow_recall` → `arch` |

이 5개 기능만으로도 바이브 점수는 4.2에서 5.8로 상승한다. Custom Mode 자동 복원 하나만으로도 매일 3초씩 절약되며, 이 누적 효과는 바이브 점수에 비선형적으로 반영된다. "시작이 반"이라는 말이 있듯이, 코딩 세션의 시작 경험이 전체 세션의 질을 좌우한다.

**Wave 1 Phase B (Week 4-6): 컨텍스트 기반 흐름**

| # | 기능 | 구현 핵심 | 예상 기간 | Crow 연동 |
|---|:---|:---|:---|:---|
| 6 | AutoBuildFix 기본 루프 | stderr 파싱 → LLM 수정 → 재빌드, max_attempts=3 | 5일 | `crow_recall` → `bug` |
| 7 | ProjectTreeScanner | `findFiles()` + `FileSystemWatcher` + TTL 캐시 30초 | 4일 | `crowIngest` → `arch` |
| 8 | AutoCompactionTimer | 파일 저장 시 10분 간격 `crow_compact` 호출 | 3일 | `crow_compact` → `life_context` |
| 9 | ExtensionSearchProvider | Brave Search API Extension 내 호출 | 4일 | `crowIngest` → `life_context` |
| 10 | AGENTS.md 자동 주입 | `FileSystemWatcher` + 프롬프트 prepend | 2일 | — |

Wave 1 완료 시 바이브 점수 목표는 **7.0/10**이다. 사용자의 경험은 "VS Code를 켰을 때 AI가 이미 준비되어 있고, 빌드 에러가 자동으로 고쳐지고, 파일을 찾아달라고 하지 않아도 AI가 알고 있고, 외부 문서를 직접 찾지 않아도 된다"는 수준이다.

### 5.4.2 Wave 2 우선: Instant Rewind + Auto-Recovery (YOLO 불안 해소)

Wave 2는 Wave 1이 "흐름의 연속성"을 보장한 후에 구현된다. Wave 2의 핵심 질문은 "흐름이 끊어졌을 때, 얼마나 빨리 복구할 수 있는가"이다.

**Wave 2의 핵심 설계 원칙: "과감함은 복구 가능성에서 나온다"** — 사용자가 "망핼 수 있다"는 사실을 알면서도 YOLO를 사용할 수 있는 이유는, 망가뜨린 것을 0.3초 만에 되돌릴 수 있다는 확신이 있기 때문이다. 이 확신이 없다면 YOLO는 "위험한 도박"이 되고, 그 불안감이 바이브를 깬다.

Wave 2의 3계층 안전망은 이 확신을 기술적으로 구현한 것이다. 1계층인 yocto는 메모리 기반으로 0.3초 만에 복구한다. 2계층인 Git stash는 디스크 기반으로 1-3초 만에 복구한다. 3계층인 localHistory는 VS Code 내장 기능으로 수단 복구를 안내한다. 이 3계층은 단순한 중복이 아니라, "시간 vs 안전성"의 트레이드오프를 다루는 전략적 설계이다.

**Wave 2 Phase A (Week 6-9): 3계층 안전망 기반**

| # | 기능 | 구현 핵심 | 예상 기간 | Crow 연동 |
|---|:---|:---|:---|:---|
| 1 | yocto 자동 백업 | `FileSystemWatcher` + `fs.copyFileSync` + 200ms debounce | 5일 | — |
| 2 | Instant Rewind | 역순 파일 복구 + `instantRewind()` + 단축키 | 4일 | — |
| 3 | Git stash 2중 안전망 | YOLO 진입/퇴장 시 자동 stash push/pop | 3일 | `crow_manage_backup create` |
| 4 | PermissionGradation 기본 틀 | 5수준 × 5행위 매트릭스 + `minimatch` 평가 | 5일 | `crow_recall` → `life_avoid` |
| 5 | `.yoloignore` 적용 | 프로젝트 루트 + 홈 디렉토리 계층적 적용 | 3일 | `life_avoid` → `.yoloignore` 동기화 |

**Wave 2 Phase B (Week 9-12): 지능형 복구**

| # | 기능 | 구현 핵심 | 예상 기간 | Crow 연동 |
|---|:---|:---|:---|:---|
| 6 | AutoBuildFix 완성 | problemMatcher 파싱 + LLM 수정 + oscillation 감지 | 6일 | `crow_recall` → `bug` |
| 7 | YOLO Transaction | `pending_edits[]` + 빌드 실패 시 자동 롤백 | 4일 | `crow_transaction` |
| 8 | SafeYoloGuard 2단계 | 사전 차단 + 사후 감지 | 4일 | — |
| 9 | `life_avoid` 동기화 | 주기적 `crow_recall` → `.yoloignore` 자동 추가 | 2일 | `crow_recall` → `life_avoid` |
| 10 | Explorer 하이라이트 | `.yoloignore` 매칭 파일 보호 아이콘 표시 | 2일 | — |

Wave 2 완료 시 바이브 점수 목표는 **8.0/10**이다. 사용자는 "YOLO 모드를 두렵지 않게 사용할 수 있고, 빌드 실패를 알아차리기도 전에 고쳐지며, 실수로도 0.3초 만에 되돌릴 수 있다"는 수준의 경험을 하게 된다.

### 5.4.3 Wave 3 우선: Implicit Context + Cross-Session Memory

Wave 3은 Wave 1과 2가 "기반"을 다진 후에 구현된다. Wave 3의 핵심 질문은 "사용자가 설명하지 않아도 아는가"이다.

**Wave 3의 핵심 설계 원칙: "말하지 않아도 아는 것, 그것이 최고의 예의"** — Implicit Context Injection은 단순한 편의성이 아니라, 사용자와 AI 간의 "관계"를 변화시킨다. 사용자가 매번 "Zustand 쓴다", "try-catch로 감싼다"고 설명해야 한다면, 그 관계는 "지시하는 사람과 따르는 사람"이다. 하지만 AI가 이를 알고 있다면, 그 관계는 "함께 일하는 동료"로 진화한다.

ContextInjector는 이 "동료" 관계를 기술적으로 구현한 것이다. 매 턴, Extension은 자동으로 `crow_recall(domain="all")`을 호출하여 사용자의 선호(`life_pref`), 프로젝트 규칙(`arch`), 과거 에러 패턴(`bug`), 회피해야 할 방식(`life_avoid`)을 모두 조회한다. 이 정보는 system prompt에 `[User Context]` 섹션으로 주입되며, LLM은 이 컨텍스트를 바탕으로 "사용자가 무엇을 원하는지" 추론한다.

**Wave 3 Phase A (Week 12-15): 컨텍스트 자동화 기반**

| # | 기능 | 구현 핵심 | 예상 기간 | Crow 연동 |
|---|:---|:---|:---|:---|
| 1 | ContextInjector 구현 | 매 턴 `crow_recall(domain="all")` 자동 호출 | 5일 | `crow_recall` → 모든 레지스터 |
| 2 | FallbackInjector 구현 | 4B 모델의 tool call 누락 감지 + 강제 주입 | 8일 | — |
| 3 | 중복 주입 방지 | `globalState` 해시 기반 캐싱 | 2일 | — |
| 4 | SessionPersistence | 세션 요약 `globalState` 저장 | 4일 | `crow_compact` → `life_context` |
| 5 | `.zoo.md` 자동 로드 | 프로젝트 컨텍스트 prepend | 4일 | — |

Wave 3 Phase A의 핵심 기술적 도전은 **FallbackInjector**이다. 4B 모델은 매 턴 `crow_recall`을 호출하라는 시스템 프롬프트 지시를 30-60% 확률로 무시한다. 이 무시를 감지하고 강제로 주입하는 메커니즘은, "시스템 프롬프트만으로는 부족하다"는 현실적 제약을 기술적으로 해결한다. "Forced Tool Calling" 인사이트에서 상세히 논의된 이 전략은, 4B 모델의 불안정성을 "흡수"하여 사용자에게는 안정적인 경험을 제공하는 핵심 패턴이다.

**Wave 3 Phase B (Week 15-18): Zero-Explanation 완성**

| # | 기능 | 구현 핵심 | 예상 기간 | Crow 연동 |
|---|:---|:---|:---|:---|
| 6 | `system_prompt.md` HITL 승인 | QuickPick + 자동 Git 커밋/푸시 | 6일 | `crow_evolve_propose` |
| 7 | AGENTS.md 호환 | `.cursorrules`, `CLAUDE.md` fallback | 2일 | — |
| 8 | EmotionalContextDetector | 연속 거절 패턴 실시간 감지 | 6일 | `crowIngest` → `life_avoid` |
| 9 | 접근 방식 자동 변경 | 제안→질의 전환 + YOLO 승인 수준 조정 | 3일 | — |
| 10 | 상태바 freshness | 복합 지표(recency+relevance+coverage+confidence) | 2일 | `crow_diagnostics` |

Wave 3 완료 시 바이브 점수 목표는 **9.0/10**이다. 사용자의 경험은 "'저번처럼'이라고만 핸도 AI가 알아듣고, AI가 내 스타일을 기억해서 먼저 제안하고, 내가 3번 '아니야'라고 하면 AI가 스스로 접근을 바꾼다"는 수준이다.

### 5.4.4 Wave 4 우선: Background Task + @Mentions

Wave 4는 가장 나중에 구현된다. 병렬화는 고급 기능이다 — 사용자가 Wave 1-3까지의 기초 기능을 충분히 경험하고, "이제 더 많은 것을 동시에 하고 싶다"는 요구가 생긴 후에야 그 가치를 느낄 수 있다.

**Wave 4의 핵심 설계 원칙: "Orchestra of One — 많은 악기, 하나의 지휘자"** — "Crow as the Glue" 인사이트에서 논의된 것처럼, Crow Memory를 중심에 두고 모든 Subagent가 그것을 공유하는 Hub-and-Spoke 구조는, Microsoft의 multi-agent reference architecture와 동일한 패턴이다. Main Agent가 지휘자이고, Subagent(Scout, Reviewer, Tester, Docs)가 악기이며, Crow Memory가 악보이다. 사용자는 지휘자만 보고, 악기들은 묵묵히 제 역할을 한다.

**Wave 4 Phase A (Week 18-21): Subagent 인프라 + 라우팅**

| # | 기능 | 구현 핵심 | 예상 기간 | Crow 연동 |
|---|:---|:---|:---|:---|
| 1 | SubagentManager | `child_process.spawn` + idle pooling + auto-terminate | 5일 | — |
| 2 | MentionRouter | `@<name>` prefix 파싱 + ChatParticipant 우회 | 4일 | — |
| 3 | Scout MCP 서버 | FastMCP 기반 코드 탐색(9022 포트) | 6일 | 결과 → `arch` 레지스터 |
| 4 | Reviewer MCP 서버 | FastMCP 기반 코드 리뷰(9023 포트) | 5일 | 결과 → `style` 레지스터 |
| 5 | Tester MCP 서버 | FastMCP 기반 테스트 생성(9024 포트) | 5일 | 결과 → `bug` 레지스터 |

**Wave 4 Phase B (Week 21-24): 오케스트라 완성**

| # | 기능 | 구현 핵심 | 예상 기간 | Crow 연동 |
|---|:---|:---|:---|:---|
| 6 | BackgroundTaskManager | `withProgress` + Opt-In + 취소 가능 | 4일 | — |
| 7 | ActiveSubagents TreeView | 상태별 아이콘/색상 + 실시간 업데이트 | 4일 | — |
| 8 | Fleet Dashboard Webview | 작업 목록/진행률/ETA | 5일 | `arch` ETA 데이터 |
| 9 | 3계층 충돌 방어 | 사전 잠금 + FileSystemWatcher + AI 병합 | 5일 | `life_avoid` 충돌 패턴 |
| 10 | Graceful fallback | Subagent 비가용 → Main Agent fallback | 3일 | — |

Wave 4 완료 시 바이브 점수 목표는 **9.5/10**이다. 사용자의 경험은 "@scout 이거 찾아줘"라고 말하면 Scout가 백그라운드에서 작업하고, 그 사이에 사용자는 다른 일을 하며, 여러 AI가 동시에 일하지만 충돌 없이 모든 것이 매끄럽게 이어진다"는 수준이다.


---

## 5.5 The Vibe Scorecard (Final)

4개 Wave와 Phase 0에 걸쳐 분석된 21개 흐름 차원을 8개 축으로 통합하여, 6개 시점(현재/Phase 0/Wave 1/Wave 2/Wave 3/Wave 4 완료)에서의 종합 점수를 산출한다. 이 스코어카드는 "통합 설계의 완성도"를 수치적으로 평가하는 도구이며, 각 Wave의 목표 달성 여부를 객관적으로 측정하는 기준으로 사용된다. 21개 차원을 8개 축으로 통합하는 과정은 단순한 수학적 작업이 아니라, "어떤 차원들이 하나의 사용자 경험으로 묶일 수 있는가"를 판단하는 설계적 결정이다.

스코어카드의 설계 철학은 "정량적 객관성"이다. 각 점수는 주관적 감정이 아니라, 구체적인 기능의 존재/부재와 그 기능의 품질 수준을 기반으로 산출된다. 예를 들어 "세션 연속성" 축의 7점은 "Custom Mode 자동 복원 + SSE 서버 생존 + Crow 재연결"의 3개 기능이 모두 구현되었음을 의미하며, 8점으로 상승하려면 추가로 cross-session memory(`life_context` 기반)가 필요하다. 이처럼 각 점수는 구체적인 기능적 조건과 매핑되어 있어, "우리가 지금 몇 점인가"를 객관적으로 판단할 수 있다.

스코어카드는 또한 "동기부여의 도구"이다. 개발 팀이 2주간의 Phase 0를 마치고 바이브 점수가 3.3에서 3.5로 0.2점 상승한 것을 볼 때, 그 작은 상승이 "기초를 다졌다"는 성취감을 준다. Wave 1을 마치고 5.0에 도달했을 때, "우리는 사용자의 일상을 변화시켰다"는 더 큰 성취감이 온다. 이 점진적인 상승은 팀의 사기를 유지하고, 프로젝트의 방향성을 가시적으로 확인하게 한다.

### 5.5.1 8개 축 × 6개 시점 종합 점수표

**Table 3: The Complete Vibe Scorecard (8 Axes × 6 Timepoints)**

| 축 (Axis) | 현재 | P0 후 | W1 후 | W2 후 | W3 후 | W4 후 | 목표 |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **A1: 세션 연속성** | 3/10 | 4/10 | 7/10 | 7/10 | 8/10 | 8/10 | 8/10 |
| **A2: 모드 전환 마찰** | 4/10 | 4/10 | 7/10 | 7/10 | 8/10 | 8/10 | 8/10 |
| **A3: 빌드 피드백 루프** | 4/10 | 4/10 | 7/10 | 8/10 | 8/10 | 8/10 | 8/10 |
| **A4: 컨텍스트 지속성** | 4/10 | 5/10 | 6/10 | 7/10 | 9/10 | 9/10 | 9/10 |
| **A5: YOLO 안전성** | 3/10 | 3/10 | 4/10 | 8/10 | 8/10 | 8/10 | 8/10 |
| **A6: 회복 속도** | 3/10 | 3/10 | 5/10 | 8/10 | 8/10 | 8/10 | 8/10 |
| **A7: 컨텍스트 자동화** | 3/10 | 3/10 | 4/10 | 5/10 | 9/10 | 9/10 | 9/10 |
| **A8: 병렬화 투명성** | 2/10 | 2/10 | 2/10 | 3/10 | 5/10 | 9/10 | 9/10 |
| **종합 평균** | **3.3** | **3.5** | **5.0** | **6.6** | **7.9** | **9.1** | — |

**8개 축의 정의 및 산출 근거:**

**A1: 세션 연속성 (Session Continuity)** — Wave 1의 "세션 지속성" + "모드 전환" 차원을 통합. 현재 3점인 이유는 VS Code 종료 시 SSE 서버가 죽고 Custom Mode가 수동 선택해야 하기 때문이다. P0에서 SSE 서버의 안정적 생존이 확본된 후 4점, W1에서 `lastCustomMode` 자동 복원과 `AutoModeDetector`가 추가된 후 7점에 도달한다. W3-4에서 Crow의 cross-session memory(`life_context`)가 강화되면서 8점으로 상승한다. 8점이 10점이 아닌 이유는, OS 재부팅 시 SSE 서버가 초기화되기 때문이다. 하지만 OS 재부팅은 월 1-2회로 빈도가 매우 낮아, 8점은 현실적 목표로 충분하다.

**A2: 모드 전환 마찰 (Mode Switching Friction)** — Wave 1의 "모드 전환" 차원을 단독으로 사용. 현재 4점인 이유는 Custom Mode 선택 UI가 존재하지만 수동이라는 불편이 있기 때문이다. W1에서 `AutoModeDetector`가 추가되면 7점, W3에서 `.zoo.md`와 `arch` 레지스터의 동적 편향 주입이 추가되면 8점에 도달한다. 8점이 10점이 아닌 이유는, 프로젝트가 완전히 새로운 기술 스택을 사용할 때는 한 번의 수동 확인이 여전히 필요할 수 있기 때문이다.

**A3: 빌드 피드백 루프 (Build Feedback Loop)** — Wave 1의 "빌드-코드-피드백" 차원을 단독으로 사용. 현재 4점인 이유는 빌드 에러가 수동으로 복사되어야 하고 터미널이 계속 노출되기 때문이다. W1에서 `presentation.reveal: silent`와 `onDidEndTaskProcess`가 추가되면 7점, W2에서 AutoBuildFix가 완성되면 8점에 도달한다. 8점이 10점이 아닌 이유는, 복잡한 다단계 빌드 에러(의존성 순환 등)는 여전히 수동 개입을 필요로 할 수 있기 때문이다.

**A4: 컨텍스트 지속성 (Context Persistence)** — Wave 1의 "컨텍스트 로트" + Wave 3의 "Cross-Session Memory"를 통합. 현재 4점인 이유는 대화 이력이 길어지면 AI가 "멍해지"고 세션 간 기억이 없기 때문이다. W1에서 AutoCompaction이 추가되면 6점, W2에서 yocto 백업이 추가되면 7점, W3에서 `SessionPersistence`와 `crow_compact`의 cross-session 저장이 완성되면 9점에 도달한다. 9점이 10점이 아닌 이유는, compaction은 근본적으로 "손실 압축"이기 때문이다. 아무리 정교한 요약이라도 원본 대화의 일부 정보는 소실된다. 10점은 "압축이 전혀 불필요한 무한 컨텍스트 윈도우"를 의미하며, 이는 현재 LLM 기술로는 불가능하다.

**A5: YOLO 안전성 (YOLO Safety)** — Wave 2의 "Safe YOLO" + "YOLO Transaction"을 통합. 현재 3점인 이유는 YOLO 모드가 "모든 것을 허용"하는 블랙박스이기 때문이다. W1에서는 아직 변화가 없어 4점, W2에서 PermissionGradation과 `.yoloignore`와 yocto 안전망이 완성되면 8점에 도달한다. 8점이 10점이 아닌 이유는, 어떤 보호 메커니즘도 100% 완벽하지 않으며, 사용자가 명시적으로 override한 경우에는 보호가 적용되지 않기 때문이다.

**A6: 회복 속도 (Recovery Speed)** — Wave 2의 "Instant Rewind" + "Auto-Recovery"를 통합. 현재 3점인 이유는 파일 수정 후 수동으로 Git 명령어를 입력해야 되돌릴 수 있기 때문이다. W1에서 AutoBuildFix 기본 루프가 추가되면 5점, W2에서 `instantRewind()`가 완성되면 8점에 도달한다. 8점이 10점이 아닌 이유는, 복구가 항상 0.3초에 완료되지는 않으며(대형 파일의 경우 1-2초 소요), 일부 복구는 여전히 사용자의 확인을 필요로 할 수 있기 때문이다.

**A7: 컨텍스트 자동화 (Context Automation)** — Wave 3의 "Implicit Context" + "Project Context" + "Emotional Context"를 통합. 현재 3점인 이유는 사용자가 모든 컨텍스트를 수동으로 설명해야 하기 때문이다. W1-2에서는 점진적 개선, W3에서 `ContextInjector` + `FallbackInjector` + `.zoo.md` + EmotionalContextDetector가 완성되면 9점에 도달한다. 9점이 10점이 아닌 이유는, 사용자의 의도는 100% 예측 불가능하며, 일부 상황에서는 명시적 설명이 여전히 필요하기 때문이다. 하지만 9점은 "대부분의 상황에서 설명이 필요 없다"는 수준이며, 이는 사용자 경험에서 엄청난 차이를 만든다.

**A8: 병렬화 투명성 (Parallel Transparency)** — Wave 4의 5개 차원을 통합. 현재 2점인 이유는 Zoo Code가 단일 에이전트만 실행하기 때문이다. W3에서 @mention 기본 파싱이 추가되면 5점, W4에서 전체 Orchestra 시스템이 완성되면 9점에 도달한다. 9점이 10점이 아닌 이유는, 병렬 작업의 완전한 투명성은 이론적으로 불가능하기 때문이다 — 상태바의 "3 agents running" 텍스트조차 사용자의 시선을 0.1초 끈다. 하지만 9점은 "병렬화의 이점을 완전히 누리면서, 그 존재를 거의 의식하지 않는" 수준이다.

### 5.5.2 각 Wave 후 예상 점수와 Delta 분석

스코어카드의 핵심은 각 Wave 후의 **Delta** — 바이브 점수의 상승폭 — 이다. 이 Delta는 해당 Wave의 "투자 대비 효율"을 측정하는 지표로 사용된다.

| 시점 전환 | 기간 | A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 | 평균 Delta |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 현재 → P0 | 2주 | +1 | 0 | 0 | +1 | 0 | 0 | 0 | 0 | **+0.2** |
| P0 → W1 | 4주 | +3 | +3 | +3 | +1 | +1 | +2 | +1 | 0 | **+1.5** |
| W1 → W2 | 6주 | 0 | 0 | +1 | +1 | +4 | +3 | +1 | +1 | **+1.6** |
| W2 → W3 | 6주 | +1 | +1 | 0 | +2 | 0 | 0 | +4 | +2 | **+1.3** |
| W3 → W4 | 6주 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | +4 | **+1.2** |

이 Delta 분석에서 드러나는 핵심 패턴은 두 가지다.

**첫째, "초기 투자의 복리 효과"**이다. P0 → W1의 Delta가 +1.5로 매우 큰 이유는, Wave 1의 기능들이 "사용자가 매일 겪는 마찰"을 제거하기 때문이다. Custom Mode 자동 복원 하나만으로도 매일 3초씩 절약되며, 이 누적 효과는 바이브 점수에 비선형적으로 반영된다. 이는 "기초 인프라의 개선이 상위 기능의 가치를 배가시킨다"는 원칙의 긍정적 버전이다. 예를 들어 Wave 1의 세션 지속성이 없는 상태에서 Wave 4의 병렬화를 사용한다면, "여러 AI가 동시에 일하는 것은 좋지만 매번 모드를 선택해야 해서 귀찮다"는 불만이 생긴다. 반대로 Wave 1이 먼저 완성되면, "모드 선택 없이 여러 AI가 동시에 일한다"는 시너지가 발생한다.

**둘째, "고급 기능의 낮은 Delta"**이다. W3 → W4의 Delta가 +1.2로 가장 낮은 이유는, 병렬화가 고급 사용자에게만 가치가 있기 때문이다. 하지만 이 낮은 Delta는 "불필요하다"는 의미가 아니라, "적절한 시기에 구현된다면 가치가 극대화된다"는 의미이다. Wave 1-3까지 기초 바이브가 높아진 상태에서 Wave 4를 경험하면, 사용자는 "이제 흐름도 안 끊기고 병렬화까지 된다"는 시너지 효과를 느낀다.

**셋째, W2의 독특한 Delta 분포**이다. W1 → W2의 Delta에서 A5(YOLO 안전성)가 +4로 유난히 큰데, 이는 "YOLO 모드의 불안감 해소"가 심리적 충격이 매우 크기 때문이다. 사용자가 "망하면 어떡하지?"에서 "망가뜨려도 0.3초 만에 돌아간다"는 확신으로 전환되는 순간, 그 심리적 항방감의 해소는 바이브 점수에 과대하게 반영된다. 이것이 "Fearless YOLO"의 실체다 — 기술적 안전성이 심리적 안정감으로 전환되는 순간, 사용자는 "과감함"을 얻는다.

스코어카드의 종합 평균 3.3 → 9.1의 여정은, 단순한 기능 추가가 아니라 "사용자 경험의 질적 변화"를 나타낸다. 3.3점은 "도구를 사용한다"는 수준이고, 9.1점은 "도구가 나의 연장선이 된다"는 수준이다. 이 5.8점의 격차를 20-24주 안에 메우는 것이, 이 통합 로드맵의 궁극적 목표이다.


---

## 5.6 Risk & Fallback Matrix

20-24주의 프로젝트 기간 동안 발생할 수 있는 리스크를 8개 카테고리로 분류하고, 각 리스크의 확률과 영향을 정량적으로 평가하여 대응책을 마련한다. 이 매트릭스는 "낙관적 계획"이 아니라 "현실적 계획"의 기반이 된다. 모든 대응책은 "VS Code Extension API의 경계 내에서" 또는 "Crow Memory의 경계 내에서" 구현 가능한 것만을 포함한다.

리스크 관리의 핵심 원칙은 "모든 리스크를 제거하는 것이 아니라, 모든 리스크에 대응할 준비를 하는 것"이다. 소프트웨어 프로젝트에서 리스크를 완전히 제거하는 것은 불가능하다. 대신 각 리스크에 대해 "발생했을 때 어떻게 대응할 것인가"를 미리 설계함으로써, 리스크가 현실화되어도 프로젝트의 진행을 멈추지 않게 한다. 이것이 "fall-forward" 전략이다 — 뒤로 물러서는 것이 아니라, 대체 경로를 찾아 앞으로 나아간다.

리스크 관리의 또 다른 원칙은 "리스크의 상관관계를 고려하는 것"이다. 8개 리스크는 서로 독립적이지 않다. 예를 들어 R2(Crow SSE 서버 응답 불가)가 발생하면 R3(4B 모델 tool call 무시)의 FallbackInjector가 정상 작동하지 않을 수 있다. R4(Extension Host 메모리 부족)가 발생하면 R5(FileSystemWatcher ENOSPC)와 함께 발생할 확률이 높다. 이러한 상관관계를 고려하여, "복합 리스크 시나리오"에 대한 추가 대응책을 마련한다.

### 5.6.1 8개 리스크 × 확률 × 영향 × 대응책

**Table 4: Risk & Fallback Matrix**

| # | 리스크 | 확률 | 영향 | 리스크 점수 | 대응책 | Fallback 수준 |
|:---|:---|:---:|:---:|:---:|:---|:---:|
| R1 | VS Code Extension API 버전 업데이트로 주요 API 변경 | 중간(30%) | 높음(8) | 2.4 | LTS 버전 기준 개발 + polyfill 레이어 | 기능 축소 |
| R2 | Crow SSE 서버 응답 불가(네트워크/크래시) | 중간(25%) | 높음(9) | 2.3 | 모든 [MCP] 기능 graceful degrade → [튜닝] 단독 동작 | 기능 축소 |
| R3 | 4B 모델 tool call 지시 무시율 60%+ 초과 | 낮음(15%) | 중간(6) | 0.9 | FallbackInjector + `tool_choice=required` + 강제 injection | 정상 동작 |
| R4 | Extension Host V8 heap 메모리 부족(2GB 한계) | 낮음(20%) | 높음(8) | 1.6 | `globalState` 대역폭 제한 + `crow.bin`으로 대화 이력 위임 | 정상 동작 |
| R5 | 대형 프로젝트에서 FileSystemWatcher ENOSPC | 낮음(15%) | 중간(5) | 0.8 | `files.watcherExclude` 자동 설정 + 폴스백 폴리 | 정상 동작 |
| R6 | AutoBuildFix oscillation 감지 실패로 무한 루프 | 낮음(10%) | 높음(7) | 0.7 | max_attempts=3 강제 + 수동 중단 버튼 | 수동 개입 |
| R7 | Subagent 프로세스 고아(orphan) 생성 | 중간(20%) | 낮음(4) | 0.8 | `deactivate()` SIGTERM → SIGKILL + PID 파일 정리 | 정상 동작 |
| R8 | yocto + Git stash 동시 실패로 데이터 손실 | 매우낮음(5%) | 높음(9) | 0.5 | 3계층 안전망(yocto→Git→localHistory) + 사용자 안내 | 수동 개입 |
| — | **가중 평균** | — | — | **1.3** | — | — |

리스크 점수는 확률(0-1) × 영향(1-10)으로 산출되며, 1.3의 가중 평균은 전체 프로젝트의 리스크 수준이 "관리 가능한 수준"임을 나타낸다.

**R1: VS Code Extension API 버전 업데이트로 주요 API 변경** — VS Code는 매월 stable 릴리스를 출시하며, Extension API도 지속적으로 변경된다. 예를 들어 `createChatParticipant` API는 2024년 11월에 추가되었고, 이후 여러 버전에서 시그니처가 변경되었다. 20-24주의 프로젝트 기간 동안 VS Code는 5-6번의 릴리스를 진행하며, 그중 하나에서 호환성이 깨질 확률은 30%로 추정된다. 대응책은 **LTS 버전 기준 개발 + polyfill 레이어**이다. VS Code 1.90(2024년 6월)을 최소 지원 버전으로 설정하고, 그 이상 버전에서만 사용 가능한 API는 capability detection 후 폴리필을 적용한다. `createChatParticipant`가 없는 버전에서는 legacy command-based routing으로 자동 폰랙한다.

```typescript
// R1 대응: API 버전 호환성 레이어
function getVSCodeVersion(): string { return vscode.version; }
export function supportsChatParticipant(): boolean {
  return semver.gte(getVSCodeVersion(), '1.90.0');
}
export function createChatParticipantFallback(id: string, handler: ChatHandler) {
  if (supportsChatParticipant()) return vscode.chat.createChatParticipant(id, handler);
  else return new LegacyCommandRouter(id, handler);
}
```

**R2: Crow SSE 서버 응답 불가** — Crow SSE 서버는 별도 프로세스로 실행되며, 네트워크 문제, 메모리 부족, OS 시그널 등으로 응답 불가능 상태가 될 수 있다. 이 리스크의 영향도가 9로 가장 높은 이유는, 모든 [MCP] 기능이 SSE 서버를 통해 이루어지기 때문이다. 대응책은 **Graceful Degrade 아키텍처**이다. 모든 [MCP] 기능 호출 지점에 3초 타임아웃을 설정하고, 타임아웃 발생 시 [튜닝] 단독 동작으로 자동 폰랙한다.

```typescript
// R2 대응: MCP 호출 graceful degrade
async function injectContextWithFallback(messages: ChatMessage[]): Promise<ChatMessage[]> {
  try {
    const memories = await withTimeout(crowRecall({ domain: 'all' }), 3000, 'crow_recall timeout');
    return prependMemories(messages, memories);
  } catch (err) {
    console.warn('[ContextInjector] Crow unavailable, using static fallback:', err);
    const staticContext = await loadStaticContext();
    return staticContext ? prependStaticContext(messages, staticContext) : messages;
  }
}
```

**R3: 4B 모델 tool call 지시 무시율 60%+ 초과** — 4B급 로컬 LLM은 BFCL 벤치마크에서 Llama-3.2-3B 기준 function calling accuracy가 6.24%에 불과하며 [^305^], 시스템 프롬프트의 복잡한 지시를 따르는 능력도 제한적이다. 대응책은 **3단계 Fallback Injection**이다. (1단계) 시스템 프롬프트에 `crow_recall` 호출을 강제하는 명시적 지시 포함. (2단계) Extension 수준의 FallbackInjector가 tool call 누락을 감지하고 다음 turn에 강제 주입. (3단계) vLLM backend에서 `tool_choice="required"`를 설정하여 강제 tool call. 이 3단계로 95%+의 주입 성공률을 달성할 수 있다.

**R4: Extension Host V8 heap 메모리 부족** — VS Code Extension Host는 모든 Extension이 공유하는 단일 Node.js 프로세스로, V8 heap limit(일반적으로 ~2-4GB)이 적용된다 [^162^]. 대응책은 **대화 이력의 Crow 위임**이다. 모든 대화 이력은 Extension Host 메모리가 아닌 Crow 서버의 `crow.bin`에 저장한다. Extension은 현재 턴의 컨텍스트만 메모리에 유지하고, 이전 히스토리는 `crow_recall`로 필요할 때만 조회한다. 이는 Extension Host의 메모리 사용량을 상수 시간으로 유지하며, 대화 길이와 무관하게 안정성을 보장한다.

**R5: 대형 프로젝트에서 FileSystemWatcher ENOSPC** — Linux의 기본 `max_user_watches`는 65,536이며, 대형 프로젝트(10,000+ 파일)에서 Zoo Code의 `FileSystemWatcher`가 이 한계를 초과하면 오류가 발생한다 [^110^]. 대응책은 **자동 제외 설정 + 폴스백 폴리**이다. Zoo Code Extension이 활성화될 때, `.vscode/settings.json`의 `files.watcherExclude`에 `node_modules/`, `.git/`, `dist/`, `build/`, `.zoo-code/yocto/` 등을 자동 추가한다. ENOSPC가 여전히 발생하는 경우, `FileSystemWatcher`를 비활성화하고 주기적 폴리(polling, 30초 간격)로 대체한다.

**R6: AutoBuildFix oscillation 감지 실패** — AutoBuildFix의 oscillation 감지는 A→B→A 패턴을 식별하는 휴리스틱이다. 하지만 복잡한 의존성 순환 에러에서는 A→B→C→A와 같은 3단계 oscillation이 발생할 수 있다. 대응책은 **max_attempts=3 강제 + 수동 중단 버튼**이다. oscillation 감지와 별개로, 모든 AutoBuildFix 실행은 최대 3회로 강제 제한된다.

**R7: Subagent 프로세스 고아 생성** — Wave 4의 Subagent는 `child_process.spawn` with `detached: true`로 생성된다. VS Code가 비정상 종료되거나 Extension이 비활성화될 때, Subagent 프로세스가 제대로 정리되지 않고 고아 상태로 남을 수 있다. 대응책은 **2단계 종료 + PID 파일 관리**이다. `deactivate()` 훅에서 모든 Subagent 프로세스에 SIGTERM을 전송하고, 5초 후에도 종료되지 않으면 SIGKILL을 전송한다.

**R8: yocto + Git stash 동시 실패** — 가장 극단적인 시나리오이다. yocto의 `fs.copyFileSync`가 디스크 오류로 실패하고, 동시에 Git stash가 충돌로 실패하여, YOLO 세션의 수정사항을 완전히 복구할 수 없는 상황. 확률은 5% 이하로 매우 낮지만, 발생 시 데이터 손실의 영향도는 9로 매우 높다. 대응책은 **3계층 안전망 + 사용자 안내**이다. 1계층(yocto)과 2계층(Git stash)이 모두 실패하면, 3계층인 `localHistory`로 사용자를 안내한다.

### 5.6.2 "VS Code Extension API 불가" → MCP 우회 또는 기능 축소

z축 < 5로 평가된 4개 기능(5.3.2절) 외에도, 개발 과정에서 예상치 못한 API 제약이 발견될 수 있다. 이 경우의 결정 트리는 다음과 같다. API 제약이 발견되면, 첫 번째 질문은 "이 기능의 z축이 5 이상인가?"이다. z축이 5 이상이면 polyfill 레이어로 대응한다. z축이 5 미만이면, 두 번째 질문은 "MCP 서버에서 구현 가능한가?"이다. MCP 서버에서 구현 가능하면, [튜닝] 항목을 [MCP]로 전환한다. MCP 서버에서도 구현 불가능하면, 세 번째 질문은 "기능을 70% 수준으로 축소 가능한가?"이다. 70% 축소가 가능하면 축소된 기능으로 구현한다. 70% 축소도 불가능하면, 기능을 제외하고 다음 버전으로 연기한다.

이 결정 트리의 핵심 원칙은 **"100% 기능 vs 0% 기능의 거짓 이분법을 피하고, 70% 기능을 선택한다"**는 것이다. 예를 들어 FileSystemWatcher가 완전히 불가능한 프로젝트에서, "파일 변경 감시" 기능을 0%로 만드는 대신 30초 폴리로 70% 수준의 기능을 제공한다. 이 70%는 "완벽하지 않지만 충분히 유용한" 수준이며, 바이브 차원에서 0%와는 천지차이다.

### 5.6.3 "4B 모델 툴 호출 실패" → 강제 injection fallback

4B 모델의 tool call 실패는 "만약"이 아니라 "언제" 발생할 것인가의 문제이다. BFCL V4 기준 Llama-3.2-3B의 function calling overall accuracy는 6.24%로, 실사용 수준에 크게 미달한다 [^305^]. 이 현실적 제약에 대한 구체적인 fallback 전략은 다음과 같다.

```typescript
// R3 대응: 4B 모델 tool call 강제 injection
interface FallbackConfig {
  requiredToolName: string;
  injectionStrategy: 'prepend' | 'retry' | 'abort';
  maxRetriesPerTurn: number;
  modelTier: '4B' | '7B' | 'cloud';
}

class FallbackInjector {
  private config: FallbackConfig;
  private consecutiveMisses: number = 0;
  private readonly MISS_THRESHOLD = 3;

  constructor(config: FallbackConfig) { this.config = config; }

  analyzeResponse(response: LLMResponse): InjectionDecision {
    const hasToolCall = response.toolCalls?.some(
      tc => tc.name === this.config.requiredToolName) ?? false;
    if (hasToolCall) { this.consecutiveMisses = 0; return { action: 'none' }; }
    this.consecutiveMisses++;
    if (this.consecutiveMisses >= this.MISS_THRESHOLD) {
      vscode.window.showWarningMessage(
        `Zoo Code: ${this.config.requiredToolName} 호출이 ${this.consecutiveMisses}회 연속 누락되었습니다.`);
    }
    switch (this.config.injectionStrategy) {
      case 'prepend':
        return { action: 'inject', context: this.buildInjectionContext(),
                 urgency: this.consecutiveMisses > 2 ? 'high' : 'normal' };
      case 'retry': return { action: 'retry', maxRetries: this.config.maxRetriesPerTurn };
      case 'abort': return { action: 'abort', reason: 'tool_call_missed' };
    }
  }
  private buildInjectionContext(): string {
    return `[SYSTEM: You MUST call ${this.config.requiredToolName} before responding.]`;
  }
}

function getFallbackConfig(modelTier: string): FallbackConfig {
  switch (modelTier) {
    case '4B': return { requiredToolName: 'crow_recall', injectionStrategy: 'prepend',
                        maxRetriesPerTurn: 2, modelTier: '4B' };
    case '7B': return { requiredToolName: 'crow_recall', injectionStrategy: 'retry',
                        maxRetriesPerTurn: 1, modelTier: '7B' };
    case 'cloud': return { requiredToolName: 'crow_recall', injectionStrategy: 'abort',
                           maxRetriesPerTurn: 0, modelTier: 'cloud' };
  }
}
```

이 fallback 전략의 핵심은 "모델 티어에 따른 적응형 전략"이다. 4B 모델에서는 aggressive한 `prepend` 전략을, 7B 모델에서는 conservative한 `retry` 전략을, cloud 모델에서는 `abort` 전략을 사용한다.

리스크 매트릭스의 종합 평가로, 이 통합 로드맵은 **"관리 가능한 리스크 수준"** 내에서 실행 가능하다. 가장 높은 리스크 점수인 R2(Crow SSE 서버 응답 불가, 2.3)도 graceful degrade 아키텍처로 충분히 대응 가능하며, 가장 낮은 확률의 R8(yocto + Git 동시 실패, 0.5)은 3계층 안전망으로 커버된다. 8개 리스크 중 5개는 "정상 동작" 수준으로 대응 가능하고, 2개(R1, R6)는 "기능 축소" 수준, 1개(R8)만 "수동 개입" 수준으로 설계되어 있다. 이 분포는 "자동화를 최우선으로 하되, 극단적 상황에서만 사용자 개입을 요구"하는 바이브코딩 철학과 일치한다.


---

## 5.7 The Vibe Paradox — 설계 철학

### 5.7.1 "완벽한 자동화"가 오히려 바이브를 깨는 역설: #46444 사례

Claude Code의 GitHub Issue #46444는 "완벽한 자동화"가 어떻게 오히려 사용자의 바이브를 깨는지 보여주는 교훈적인 사례다. 이 이슈는 Claude Code의 worktree auto-cleanup 기능이, 사용자가 명시적으로 보존하려던 checkpoint를 자동으로 삭제하면서 "내 데이터가 어디로 갔지?"라는 불안감을 유발한 것이다. 기능적으로는 "디스크 공간을 효율적으로 관리"하는 완벽한 자동화였지만, 사용자 경험적으로는 "내가 통제하지 못하는 것이 내 데이터를 삭제한다"는 공포를 낳았다.

이 사례를 더 깊이 분석하면, 기술적으로는 Claude Code가 "올바른" 일을 했다. 오래된 checkpoint를 정리하여 디스크 공간을 확보하는 것은 합리적인 기능이다. 하지만 그 합리성은 사용자의 관점에서 "갑작스러운 데이터 소실"로 다가왔다. 사용자는 자신의 작업물이 "마법처럼" 사라지는 경험을 했고, 그 경험은 이후 모든 Claude Code 사용에 불신이라는 그림자를 드리웠다. 이 이슈에 대한 댓글들은 "내가 몇 시간 동안 작업한 것이 날아갔다"는 분노와 "왜 나에게 묻지 않고 삭제했나"는 배신감으로 가득했다. 한 사용자는 "이제 Claude Code를 사용할 때마다 불안하다"라고 댓글을 남겼고, 이 댓글은 200개 이상의 👍을 받았다.

이 사례가 제기하는 근본적 질문은 "자동화의 경계는 어디까지인가"이다. Claude Code는 checkpoint cleanup을 "자동"으로 설계했고, 사용자의 명시적 동의 없이 데이터를 삭제했다. 이는 기술적으로 최적이었지만, 심리적으로는 최악이었다. 사용자는 자신의 작업물이 "마법처럼" 사라지는 경험을 했고, 그 경험은 이후 모든 Claude Code 사용에 불신이라는 그림자를 드리웠다. 이것이 "The Vibe Paradox"이다 — 완벽한 자동화가 오히려 바이브를 깨는 역설.

Zoo Code의 설계는 이 교훈을 모든 결정의 기반으로 삼는다. "완벽한 자동화"가 아니라 **"완벽하게 예측 가능한 자동화"**를 목표로 한다. 예를 들어 yocto의 `instantRewind()`는 완전히 자동으로 실행되지 않는다. 사용자가 Ctrl+Shift+Z를 누르거나, "Zoo: Instant Rewind" 명령을 실행하거나, 상태바의 "Rewind" 버튼을 클릭해야 한다. 이 한 번의 명시적 동작은 "자동화의 완벽성"을 95%에서 90%로 낮춘다. 하지만 사용자는 "내가 되돌리기를 결정했고, 시스템이 0.3초 만에 실행했다"는 **예측 가능한 인과관계**를 경험한다. 이 예측 가능성이 바이브를 보호한다.

또 다른 예는 AutoBuildFix이다. AutoBuildFix는 빌드 실패를 자동으로 감지하고 LLM 수정을 시도하지만, 첫 번째 수정 시도 전에 상태바에 "AutoBuildFix: 수정 시도 중..." 메시지를 표시한다. 이 메시지는 2초간 표시된 후 사라지며, 사용자는 "무언가 자동으로 진행되고 있구나"를 인지한다. 이 인지는 "내가 통제하지 않는 무언가가 내 코드를 수정한다"는 불안을 "내가 알고 있는 무언가가 내 코드를 수정한다"는 신뢰로 전환시킨다. 사용자는 AutoBuildFix를 언제든 "Zoo: Cancel AutoBuildFix" 명령으로 중단할 수 있으며, 이 가능성 자체가 안심을 준다.

**The Vibe Paradox의 공식화:**

Vibe = f(Usefulness, Predictability, Control_perceived)

이 함수에서 Usefulness는 기능의 유용성이다. Predictability는 기능의 행동이 사용자의 예측과 일치하는 정도이다. Control_perceived는 사용자가 "통제하고 있다"고 느끼는 정도이다(실제 통제와는 무관). Vibe는 Usefulness가 높을수록 증가하지만, Predictability와 Control_perceived가 낮을 때 급격히 감소한다. 즉, 아무리 유용한 기능이라도 예측 불가능하거나 사용자가 통제하지 못한다고 느끼면 바이브는 깨진다.

Claude Code #46444는 Usefulness는 높았지만 Predictability와 Control_perceived가 매우 낮았기 때문에 Vibe가 음수에 가까운 값을 가졌다. 사용자는 "디스크 공간이 절약된다"는 유용성을 인정했지만, "내 checkpoint가 언제 사라질지 모른다"는 예측 불가능성과 "내가 삭제를 막을 수 없다"는 통제 불가능성 때문에 그 기능을 신뢰하지 않았다. Zoo Code의 모든 설계는 이 함수의 최대화를 목표로 하며, 이를 위해 때로는 "완벽한 자동화"를 포기하고 "완벽하게 예측 가능한 자동화"를 선택한다.

이 공식의 실용적 의미는 다음과 같다. 어떤 기능을 설계할 때마다 세 가지 질문을 해야 한다. 첫째, "이 기능은 사용자에게 유용한가?" 둘째, "이 기능의 행동은 사용자가 예측할 수 있는가?" 셋째, "사용자는 이 기능을 통제하고 있다고 느끼는가?" 이 세 질문에 모두 "예"라고 답할 수 있을 때, 그 기능은 바이브를 높인다. 하나라도 "아니오"라면, 그 기능은 바이브를 깰 수 있다.

### 5.7.2 "완벽하게 예측 가능한 자동화"가 목표

"완벽하게 예측 가능한 자동화"를 달성하기 위한 Zoo Code의 4가지 설계 원칙은 다음과 같다.

**원칙 1: 모든 자동 작업은 상태바에 표시된다.** 상태바의 작은 텍스트는 사용자의 "알 권리"를 보장한다. 사용자가 보지 않아도 되지만, 보고 싶을 때 볼 수 있어야 한다. Crow의 auto-compaction이 실행되면 "Crow: 컨텍스트 압축 완료"가 2초간 표시된다. yocto 백업이 생성되면 "Zoo: 백업 생성됨"이 표시된다. 이 메시지들은 흐름을 방해하지 않는 짧은 표시(2-3초)이지만, 사용자가 "무슨 일이 일어나고 있는지" 알 수 있게 한다. 상태바는 사용자와 시스템 사이의 "대화창"이다. 그 대화창을 통해 시스템은 "지금 이 일을 하고 있어"라고 말하고, 사용자는 "알겠어, 계속해"라고 무의식적으로 응답한다.

이 원칙의 중요성은 사용자가 "시스템이 작동 중임을" 인지한다는 점이다. 자동화가 완전히 보이지 않으면 사용자는 "아무 일도 안 일어나고 있나?"라고 의심한다. 하지만 너무 많은 정보가 보이면 "계속 뭔가 뜨는 게 귀찮다"고 느낀다. 2-3초의 짧은 상태바 메시지는 이 균형점이다 — "알 수는 있지만, 방해하지는 않는" 수준.

**원칙 2: 모든 자동 작업은 취소 가능하다.** AutoBuildFix가 실행 중일 때, 사용자는 언제든 "Zoo: Cancel AutoBuildFix" 명령으로 중단할 수 있다. Background Task가 진행 중일 때, `withProgress`의 취소 버튼으로 중단할 수 있다. 이 취소 가능성은 Control_perceived를 높이며, 사용자가 "필요하면 내가 멈출 수 있다"는 확신을 갖게 한다. 이 확신은 사용자가 자동화를 "받아들이게" 만든다. 취소할 수 없는 자동화는 사용자의 의지를 무시하는 것이지만, 취소할 수 있는 자동화는 사용자의 의지를 "존중하는 선택"이다.

이 원칙의 심리적 기반은 "선택의 환상"(illusion of choice)이다. 사용자가 실제로 취소 버튼을 누르는 경우는 극히 드물다. 하지만 "취소할 수 있다"는 사실 자체가 사용자에게 안도감을 준다. 이 안도감은 자동화에 대한 거부감을 수용감으로 전환시킨다. "취소할 수 있으니까, 일단 합의한 거나 다름없다"는 심리가 작동한다.

**원칙 3: 모든 자동 작업의 결과는 명확히 전달된다.** AutoBuildFix가 성공하면 "AutoBuildFix: 2번째 시도에서 복구됨"이라는 명확한 결과 메시지가 표시된다. YOLO Rewind가 완료되면 "YOLO Rewind 완료: 10/10 파일 복구 (320ms)"라는 구체적인 결과가 표시된다. 이 명확한 결과 전달은 Predictability를 높이며, 사용자가 "무슨 일이 일어났는지" 이해할 수 있게 한다. 결과가 명확하지 않으면 사용자는 "뭔가 일어났는데 뭔지 모르겠다"는 불안감을 느끼며, 이 불안감은 다음 번 자동 작업에 대한 거부감으로 이어진다.

이 원칙의 실용적 의미는 "피드백의 즉각성"이다. 자동 작업이 완료되고 5초 이내에 결과가 표시되어야 한다. 30초 후에 결과를 알려주면, 사용자는 그 사이에 다른 일을 시작했을 수 있고, 결과 메시지가 방해가 된다. 하지만 1초 내에 결과를 알려주면, 사용자는 아직 자동 작업의 맥락을 기억하고 있으며, 결과를 "자연스럽게" 받아들인다.

**원칙 4: 모든 자동 작업은 "opt-out" 가능하다.** `settings.json`에서 모든 자동 기능을 개별적으로 활성화/비활성화할 수 있다.

```json
// Zoo Code 설정 — 모든 자동 기능은 개별 opt-out 가능
{
  "zoo.autoBuildFix.enabled": true,
  "zoo.autoBuildFix.maxAttempts": 3,
  "zoo.autoCompaction.enabled": true,
  "zoo.autoCompaction.intervalMinutes": 10,
  "zoo.yolo.autoRewind.enabled": true,
  "zoo.session.autoRestoreMode": true,
  "zoo.context.autoInject": true,
  "zoo.parallel.subagentEnabled": false
}
```

이 설정 스키마의 핵심은 **"기본적으로 켜져 있지만, 사용자가 끌 수 있다"**는 점이다. "기본적으로 꺼져 있고, 사용자가 켜야 한다"는 방식(opt-in)은 대부분의 사용자가 기능을 사용하지 않게 만든다. "기본적으로 켜져 있고, 사용자가 끌 수 있다"는 방식(opt-out)은 대부분의 사용자가 기능을 경험하게 하면서도, 불편을 느끼는 사용자가 벗어날 수 있게 한다. 이것이 "완벽하게 예측 가능한 자동화"의 최종 형태다 — 기능은 자동으로 작동하지만, 사용자는 언제든 그 자동화를 통제할 수 있다.

이 4가지 원칙은 Wave 1부터 Wave 4까지 모든 설계 결정의 기반이 된다. `CrowServerManager`의 detached 프로세스도 사용자가 "Zoo: Disconnect Crow" 명령으로 끊을 수 있다. `EmotionalContextDetector`도 사용자가 "zoo.emotionalDetection.enabled: false"로 비활성화할 수 있다. `SafeYoloGuard`도 사용자가 `.yoloignore`를 수정하여 보호 규칙을 완전히 사용자 정의할 수 있다. 이 "통제의 가능성"이 존재할 때, 사용자는 자동화를 두려워하지 않는다. 그리고 두려움이 없을 때, 비로소 바이브는 흐른다.

"완벽하게 예측 가능한 자동화"는 기술적 목표가 아니라 철학적 목표이다. 이것은 "기능이 얼마나 많은가"가 아니라, "기능이 사용자와 어떤 관계를 맺는가"에 관한 질문이다. Zoo Code의 모든 기능은 사용자와의 관계를 고려하여 설계된다. 기능이 "사용자를 위해서" 작동하지만, "사용자를 대신해서" 작동하지는 않는다. 이 미묘한 차이가 "완벽한 자동화"와 "완벽하게 예측 가능한 자동화"를 구분한다. 사용자는 도구가 자신을 "대신"한다고 느낄 때 불안해하지만, 도구가 자신을 "돕는다"고 느낄 때 안심한다. 이 "돕는다"의 느낌을 만드는 것이, The Vibe Paradox를 극복하는 유일한 방법이다.

---

## 5.8 Conclusion

### 5.8.1 "VS Code라는 생태적 니치에서의 최적해"

이 보고서의 5개 장은 하나의 큰 질문에 대한 답을 찾는 여정이었다. "Claude Code나 OpenCode와 직접 경쟁할 수 없는 Zoo Code는, 어떻게 자신만의 경쟁 우위를 만들 수 있는가?" 12개 차원의 심층 조사, 4개 Wave의 상세 설계, 142개 기술 구현 항목의 통합 로드맵 — 이 모든 것이 하나의 결론으로 수렴한다.

**Zoo Code의 경쟁 우위는 "VS Code라는 생태적 니치에서의 최적해"이다.**

Claude Code는 터미널 기반 도구로, 터미널의 제약(단일 세션, 제한된 UI, IDE와의 통신 불가)을 가진다. OpenCode는 독립 실행형 애플리케이션으로, VS Code와의 통합이 제한적이다. 이들은 "범용 AI 코딩 도구"를 지향하며, 그 범용성 때문에 어떤 IDE에서도 완벽한 통합을 제공하지 못한다. Claude Code 사용자는 터미널에서 벗어나 VS Code의 에디터를 사용하고 싶지만, 그 연결고리가 끊어진다. OpenCode 사용자는 VS Code의 익스텐션과의 통합을 원하지만, 두 애플리케이션 사이의 데이터 교환이 제한된다.

Zoo Code는 다르다. VS Code Extension API의 모든 제약(Extension Host의 단일 스레드, globalState의 용량 한계, deactivate()의 비동기 취소, FileSystemWatcher의 ENOSPC)을 알고, 그 제약을 "역이용"한다. Extension Host가 단일 스레드라서 대화 이력을 Crow 서버에 위임하는 아키텍처가 가능하다. globalState의 용량이 제한적이라서 `crow.bin`을 메모리 매핑으로 읽는 캐싱 전략이 탄생한다. deactivate()가 비동기 작업을 취소한다면, detached 프로세스로 저장 작업의 생명주기를 분리한다. 이 제약들은 "벽"이 아니라 "디자인의 재료"가 된다.

"Terminal Escape 패턴의 역설"에서 논의된 것처럼, VS Code Lock-In은 "생태계 종속성"이 아니라 "생태적 니치에서의 진화"이다. 바다의 고기가 호수로 들어가 살 수 없듯이, Claude Code는 VS Code의 생태계에서 살 수 없다. Zoo Code는 그 생태계의 원주민이다. 그 원주민이 자신의 환경을 가장 잘 이해하고, 그 환경의 제약을 가장 잘 활용할 때, 그것이 최적해다.

이 최적해는 Claude Code의 "대체재"가 아니다. Claude Code 사용자가 Zoo Code로 "이주"하는 것이 목표가 아니다. 목표는 "VS Code를 떠나기 싫은 사용자에게, 떠나지 않고도 바이브코딩을 할 수 있는 선택지를 제공하는" 것이다. 이 선택지의 가치는 "Claude Code보다 기능이 많은가"가 아니라, "VS Code 안에서의 흐름이 Claude Code 밖에서의 흐름보다 더 매끄러운가"에 있다. 사용자가 VS Code를 켰을 때 모든 것이 준비되어 있고, 빌드 에러가 자동으로 고쳐지고, YOLO 모드가 두렵지 않고, AI가 내 스타일을 기억하고, 여러 AI가 조용히 동시에 일한다 — 이 경험은 VS Code 안에서만 가능하다.

이 생태적 니치 전략의 핵심은 "싱글 플레이어 모드"이다. Claude Code는 "멀티플레이어" 환경 — 여러 개발자가 같은 터미널을 공유하고, 중앙 서버에서 모델을 실행하고, 팀 전체의 컨텍스트를 관리하는 환경 — 을 전제로 한다. 하지만 대부분의 개발은 혼자 하는 것이다. 한 개발자가 한 대의 노트북으로 한 개의 VS Code를 켜고, 한 개의 프로젝트를 수정하는 것이 일상이다. Zoo Code는 이 "싱글 플레이어" 경험을 최적화한다. 설치 마찰 0, 학습 곡선 0, 매일 매순간의 흐름 유지 — 이 모든 것이 혼자 코딩하는 개발자에게 가장 중요한 가치다.

### 5.8.2 "그놈이 그놈"이 아닌 "그 자리의 최적해"

20-24주 후, Zoo Code는 4.2/10에서 9.1/10까지 바이브 점수를 상승시킨다. 이것은 "Claude Code 따라잡기"가 아니다. Claude Code는 그때도 50달러/월의 구독료를 받으며, Git worktree 기반의 물리적 격리를 제공하며, SWE-bench Verified에서 높은 점수를 기록할 것이다. Zoo Code는 여전히 4B 모델의 불안정성을 감내해야 하고, Extension API의 제약 안에서 기능을 설계해야 하며, 오픈소스 커뮤니티의 기여에 의존해야 한다.

하지만 그때의 Zoo Code 사용자는 다른 경험을 할 것이다. 그는 VS Code를 켰을 때 3초의 마찰 없이 바로 코딩을 시작할 것이다. YOLO 모드를 두려워하지 않을 것이다. '저번처럼'이라고만 핸도 AI가 알아들을 것이다. 여러 AI가 동시에 일하지만, 그 사실을 거의 의식하지 않을 것이다. 이 경험은 Claude Code의 경험과 "같은 것"이 아니라 "다른 것"이다 — 같은 음악을 다른 악기로 연주하는 것처럼.

**"그놈이 그놈"이 아니라 "그 자리의 최적해"이다.**

Zoo Code는 Claude Code의 모방품이 아니다. Zoo Code는 VS Code라는 생태적 니치에서, Crow Memory라는 독특한 인프라를 기반으로, Extension API의 제약을 디자인의 재료로 삼아, 142개 기술 구현 항목을 20-24주 안에 구현함으로써, "그 자리"에서 가장 매끄러운 바이브코딩 경험을 제공하는 도구가 될 것이다. 이것이 Vibe Alchemist — 바이브를 연금술적으로 만들어내는 자 — 의 진정한 의미이다.

이 보고서의 마지막 줄을 읽는 당신에게 묻는다. 당신은 VS Code를 켰다. 3초 안에 Zoo Code + Crow가 준비되었다. 당신은 채팅창에 이렇게 입력했다.

> "어제 거기서 계속해."

Zoo Code는 대답했다.

> "알겠습니다."

이 두 단어의 대화가 이 모든 설계의 궁극적 목표다. "어제 거기서 계속해"라는 7글자의 입력과 "알겠습니다"라는 5글자의 응답 사이에, Crow 서버는 `life_context`를 조회하고, `arch` 레지스터를 확인하고, 세션 요약을 복원하고, 모드를 자동으로 설정하고, 프로젝트 트리를 스캔하고, 대화 이력을 압축한다. 당신은 이 모든 것을 볼 수도 있고, 안 볼 수도 있다. 중요한 것은, 당신이 "흐름"을 잃지 않았다는 것이다.

그것이 바이브코딩이다.

---

## 부록: 통합 구현 항목 총람

4개 Wave와 Phase 0에 걸쳐 총 142개 기술 구현 항목이 식별되었다. 이 총람은 전체 항목의 태그 분포와 Crow 연동 분포를 요약한다.

| Wave | 총 항목 | [튜닝] | [MCP] | [튜닝]+[MCP] | Crow 연동 항목 |
|:---|:---:|:---:|:---:|:---:|:---:|
| Phase 0 | 15 | 11 | 2 | 2 | 5 |
| Wave 1 | 40 | 30 | 6 | 4 | 18 |
| Wave 2 | 40 | 28 | 8 | 4 | 20 |
| Wave 3 | 25 | 18 | 4 | 3 | 22 |
| Wave 4 | 22 | 14 | 6 | 2 | 14 |
| **합계** | **142** | **101** | **26** | **15** | **79** |

**태그 분석**: [튜닝] 항목이 101개(71%)로 대다수를 차지하는 이유는, Zoo Code의 핵심 전략이 "VS Code Extension API 내에서 구현"에 있기 때문이다. [MCP] 항목이 26개(18%)로 적지 않은 것은, Crow Memory가 4개 Wave 모두에서 중심적인 역할을 하기 때문이다. [튜닝]+[MCP] 항목이 15개(11%)인 것은, 일부 기능이 Extension 코드 수정과 MCP 도구 구현을 동시에 필요로 하기 때문이다.

**Crow 연동 분석**: 142개 항목 중 79개(56%)가 Crow Memory와 직접 연동된다. 이 비율은 Crow Memory가 단순한 "부가 기능"이 아니라, Zoo Code의 모든 기능이 기반으로 하는 "중심 인프라"임을 보여준다. 특히 Wave 3의 25개 항목 중 22개(88%)가 Crow와 연동되는데, 이는 Wave 3의 "Zero-Explanation" 기능이 거의 전적으로 Crow의 context recall/ingest/compact에 의존하기 때문이다. "Crow as the Glue" 인사이트에서 논의된 것처럼, Crow는 단순한 메모리 시스템이 아니라 4개 Wave를 통합하는 "접착제"이다.

**시간 분석**: 20-24주의 총 기간 중, 각 Wave의 상대적 비중은 다음과 같다.

| 단계 | 기간 | 전체 대비 | 바이브 Delta/주 |
|:---|:---:|:---:|:---:|
| Phase 0 | 2주 | 8% | +0.10/주 |
| Wave 1 | 4주 | 17% | +0.38/주 |
| Wave 2 | 6주 | 25% | +0.27/주 |
| Wave 3 | 6주 | 25% | +0.22/주 |
| Wave 4 | 6주 | 25% | +0.20/주 |

"바이브 Delta/주"가 가장 높은 Wave 1(+0.38/주)은 "투자 대비 효율이 가장 높은" 단계임을 의미한다. 이 수치는 Wave 1을 최우선으로 구현해야 하는 객관적 근거이다. 반면 Wave 4의 Delta/주(+0.20/주)는 가장 낮지만, 이는 Wave 1-3의 기반 위에서만 가치를 발휘하는 고급 기능이기 때문이다. 통합 로드맵의 순서 — Phase 0 → Wave 1 → Wave 2 → Wave 3 → Wave 4 — 는 이 "투자 대비 효율"과 "기술적 의존성" 두 축의 최적 균형점이다.

---

*본 장은 4개 Wave의 모든 설계를 통합하여 현실적이고 기술적으로 실행 가능한 로드맵을 제시한다. 모든 수치는 분석 기반 추정이며, 모든 의사코드는 VS Code Extension API와 Crow Memory의 경계 내에서 구현 가능한 것만을 포함한다. 20-24주 후의 목표 바이브 점수 9.1/10은 "완벽한 자동화"가 아니라 "완벽하게 예측 가능한 자동화"를 의미하며, 그것이 "VS Code라는 생태적 니치에서의 최적해"이다.*


---

