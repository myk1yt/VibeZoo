# VibeZoo: Companion-First Architecture — 실행 가능한 통합 설계서

> **작성일**: 2026-05-27
> **기반 문서**: `reportfromgemini.md`, `zoo_code_upgrade.agent.final.md`
> **버전**: v2.2 — API-First Edition
> **프로젝트명**: VibeZoo — Zoo Code를 위한 독립형 동반자 확장
> **외부 의존성**: Crow Memory (독립 시스템, SSE 연동)
> **LLM 환경**: API 기반 (로컬 모델 미사용). Zoo Code의 API 설정을 그대로 활용.
> **핵심 제약**: Zoo Code 소스 코드를 수정하지 않는다. 모든 기능은 VibeZoo Extension + MCP 서버 + 설정 파일 변경으로 구현한다.
> **대상 바이브 점수**: 9.2/10 (API 환경에서 실현 가능 최대치)

---

## 0. Constraint Analysis: 무엇이 가능하고 무엇이 불가능한가

### 0.1 구현 수단 3종 + 외부 시스템

| 수단 | 태그 | 설명 | 예시 |
|:---|:---|:---|:---|
| **VibeZoo Extension** | `[VibeZoo]` | Zoo Code와 별개인 새 VS Code Extension. VS Code Extension API 전체 사용 가능. | StatusBar, TreeView, Webview, FileSystemWatcher, Task Provider, Command Palette |
| **MCP Server/Tool** | `[MCP]` | VibeZoo가 spawn하는 독립 프로세스(Python/Node). FastMCP + SSE transport. Zoo Code가 tool call로 호출. | Scout/Reviewer/Tester Subagent, Deep Analyzer |
| **Config Only** | `[Config]` | Zoo Code의 설정 파일만 수정. 소스 코드 변경 없음. | `custom_modes.yaml`, `.zoo/config.json`, `.vscode/settings.json` |
| **Crow Memory (외부)** | `[Crow]` | VibeZoo에 포함되지 않는 **독립 시스템**. SSE 서버(9020) + crow.bin. VibeZoo는 SSE로 Crow와 연동. | `crow_recall`, `crow_ingest`, `crow_compact`, Lock Manager |

### 0.2 Zoo Code 소스 없이 절대 불가능한 것들 (그리고 우회 전략)

| 불가능한 것 | 이유 | 우회 전략 | 손실 |
|:---|:---|:---|:---|
| **LLM 메시지 파이프라인 가로채기** | 다른 Extension의 내부 메시지 흐름에 접근 불가 | `[Config]` custom_modes.yaml 강화 + `[Crow]` crow_recall tool call + `[VibeZoo]` StatusBar 맥락 알림 | Zero-Explanation 100%→80% |
| **Custom Mode 자동 전환** | Zoo Code 내부 모드 상태를 외부에서 변경 불가 | `[VibeZoo]` StatusBar에 "권장 모드: X [적용]" 버튼으로 1클릭 제안 | 3클릭→1클릭 |
| **파일 쓰기 사전 차단** | Zoo Code의 WorkspaceEdit을 intercept 불가 | `[VibeZoo]` FileSystemWatcher로 사후 감지 + yocto 즉시 복구 (0.3초) | 예방→치료 (Layer 1→Layer 2) |
| **Zoo Code 채팅 내 @mention** | Zoo Code의 채팅 UI를 외부에서 확장 불가 | `[VibeZoo]` VS Code 공식 Chat Participant API로 `@scout` 등 별도 제공 + `[Crow]` tool call 기반 라우팅 | 채팅 통합→별도 채널 |

### 0.3 전체 태그 분포 (Companion-First)

| 태그 | 비율 | 설명 |
|:---|:---:|:---|
| `[VibeZoo]` | **52%** | VibeZoo Extension에서 구현 |
| `[MCP]` | **30%** | VibeZoo가 spawn하는 MCP 서버/도구 (Subagent, Deep Analyzer) |
| `[Config]` | **7%** | Zoo Code 설정 파일 변경만으로 구현 |
| `[Crow]` | **8%** | Crow Memory 외부 시스템 — VibeZoo가 SSE로 연동 |
| `[ZooCode]` | **3%** | Zoo Code 소스 수정이 불가피한 극소수 (Phase 0에서 우회 전략 확정) |

---

## 1. Executive Summary

### 1.1 이 문서의 목적

Zoo Code를 **소스 코드 수정 없이**, 오직 VibeZoo Extension + MCP 서버 + Crow Memory(외부) + 설정 변경만으로 "세상에서 가장 흐름이 끊기지 않는 바이브코딩 툴"로 진화시키는 설계서.

### 1.2 핵심 철학

```
Vibe = f(Usefulness, Predictability, Control_perceived)
```

- **"VS Code Lock-In"**: VS Code를 벗어나지 않는다.
- **"완벽하게 예측 가능한 자동화"**: Claude Code #46444의 교훈. 사용자가 통제 가능한 자동화.
- **"VibeZoo, Not Fork"**: Zoo Code를 포크하지 않는다. 곁에서 돕는 동반자 확장(VibeZoo)을 만든다.
- **"Crow is the Memory, VibeZoo is the Body"**: Crow Memory는 VibeZoo에 포함되지 않는 외부 독립 시스템. VibeZoo가 몸통이 되어 SSE로 Crow와 유기적으로 연동된다.

### 1.3 시스템 구성

```
┌──────────────────────────────────────────────────────────────┐
│                       VS Code 창                               │
│  ┌────────────┐  ┌──────────────────────────────────────┐    │
│  │ Zoo Code   │  │ VibeZoo Extension                     │    │
│  │ (기존)     │  │  • StatusBar (Crow, Mode, Fresh)      │    │
│  │            │  │  • TreeView (Subagents, YOLO)         │    │
│  │ MCP Client │  │  • Webview (Whiteboard, UI Preview)   │    │
│  │ ─────────  │  │  • FileSystemWatcher (yocto)          │    │
│  │ tool call  │  │  • Task Provider (silent build)       │    │
│  └─────┬──────┘  │  • Chat Participant (@scout 등)        │    │
│        │         └──────────────┬─────────────────────────┘    │
└────────┼────────────────────────┼──────────────────────────────┘
         │ MCP/SSE                │ child_process.spawn
         │ (외부 시스템)           │ (VibeZoo가 spawn)
         ▼                        ▼
┌──────────────────┐  ┌──────────────────────────────────┐
│ Crow Memory      │  │ VibeZoo MCP Servers               │
│ (외부 독립 시스템) │  │ Scout:9022  Reviewer:9023        │
│ localhost:9020   │  │ Tester:9024 Deep:9026             │
│ • crow.bin       │  │ (Python FastMCP)                  │
│ • Lock Manager   │  └──────────────────────────────────┘
│ • Visual Store   │
└──────────────────┘
```

### 1.4 전체 Wave 구성

| Wave | 기간 | 핵심 목표 | 바이브 |
|:---|:---|:---|:---:|
| **Phase 0: Foundation** | Week 0-2 | VibeZoo Extension 골격, Crow(외부) 연결, 상태바 | 4.2→5.0 |
| **Wave 1: Unbreakable Flow** | Week 2-6 | 빌드 자동화, 프로젝트 감지, 트리 스캔, 검색 | 5.0→7.0 |
| **Wave 2: Fearless YOLO** | Week 6-12 | yocto 백업/복구, 사후 파일 보호, AutoBuildFix | 7.0→8.0 |
| **Wave 3: Explain-Less** | Week 12-18 | MCP 컨텍스트 주입, 세션 메모리, 감정 감지 | 8.0→8.7 |
| **Wave 4: Orchestra of One** | Week 18-24 | Scout Subagent, @mentions, Dashboard, 충돌 해결 | 8.7→9.0 |
| **Wave 5: Visual Vibe** | Week 16-24 | Whiteboard, UI Preview, Screenshot, Diagram | (병렬) |
| **Wave 6: Deep Analysis** | Week 20-26 | Call Graph, Dependency Map, Pattern, Reverse Eng | (병렬) |

> **참고**: Wave 3은 "Zero-Explanation"이 아닌 "Explain-Less"로 명명. 메시지 파이프라인 주입이 불가능하므로 완전한 Zero-Explanation은 달성할 수 없으나, Crow Memory 도구 + Config 강화 + VibeZoo 사이드채널로 설명 부담을 80% 이상 감소시킬 수 있다.

---

## 2. Phase 0: VibeZoo Extension Foundation (Week 0-2)

### 2.1 목표

VibeZoo Extension의 기본 골격을 구축하고, 외부 Crow Memory와의 연결을 확립한다. 이 Extension은 Zoo Code와 **동일한 VS Code 창에서 독립적으로 실행**되며, 자체 StatusBar, TreeView, Webview, Command를 가진다. Crow Memory는 VibeZoo에 포함되지 않는 **외부 독립 시스템**임을 전제한다.

### 2.2 구현 항목

| # | 항목 | 태그 | 설명 |
|:---|:---|:---|:---|
| P0-1 | **VibeZoo Extension 프로젝트 생성** | `[VibeZoo]` | `yo code`로 새 VS Code Extension 스캐폴딩. `package.json`에 `activationEvents`, `contributes` 설정. 네임스페이스: `vibezoo` |
| P0-2 | **`CrowServerManager`** | `[VibeZoo]` | `child_process.spawn({ detached: true })`로 Crow SSE 서버(외부) 관리. PID 파일 기반 재탐색. `/health` 엔드포인트 확인. VS Code 종료 후에도 서버 생존 (`child.unref()`). Crow는 VibeZoo와 독립된 시스템. |
| P0-3 | **`ConnectionStatusBar`** | `[VibeZoo]` | 오른쪽 StatusBar에 `"$(pulse) VibeZoo"` 아이콘. Crow 연결 상태에 따라 색상 변경(초록=connected, 노랑=degraded, 빨강=disconnected). 툴팁에 상세 정보. |
| P0-4 | **디렉토리 구조 생성** | `[VibeZoo]` | `~/.zoo-code/yocto/`, 프로젝트 루트 `.zoo/` 자동 생성 (Crow 디렉토리는 Crow가 관리) |
| P0-5 | **`.vscode/settings.json` 주입** | `[VibeZoo]` | `files.watcherExclude` (node_modules, .git, dist), `workbench.localHistory.enabled: true` |
| P0-6 | **`.yoloignore` 템플릿** | `[VibeZoo]` | `.env`, `*.pem`, `secrets/`, `package-lock.json` 등 기본 보호 패턴 파일 생성 |
| P0-7 | **`crow_diagnostics` MCP 도구** | `[Crow]` | Crow Memory 서버 상태 진단. `crow.bin` 무결성 확인. 메모리 사용량 보고. |
| P0-8 | **Foundation 검증 명령** | `[VibeZoo]` | `VibeZoo: Verify Foundation` 커맨드. SSE 서버, 디렉토리, 설정, Crow(외부) 연결 일괄 진단. |

### 2.3 검증 기준

- [ ] VibeZoo Extension 설치 후 VS Code 5회 재시작 시 Crow(외부) SSE 서버 100% 생존
- [ ] StatusBar에 Crow 연결 상태 실시간 표시 (Crow는 외부 시스템이므로 연결 끊김 시에도 VibeZoo 자체는 정상 작동)
- [ ] `.zoo/`, `~/.zoo-code/` 디렉토리 자동 생성
- [ ] `VibeZoo: Verify Foundation` 명령으로 모든 구성요소 + Crow 연결 상태 확인 가능

### 2.4 package.json contributions (Phase 0)

```json
{
  "name": "vibezoo",
  "displayName": "VibeZoo",
  "activationEvents": ["onStartupFinished"],
  "contributes": {
    "commands": [
      { "command": "vibezoo.verifyFoundation", "title": "VibeZoo: Verify Foundation" },
      { "command": "vibezoo.reconnectCrow", "title": "VibeZoo: Reconnect to Crow" }
    ]
  }
}
```

---

## 3. Wave 1: Unbreakable Flow (Week 2-6)

### 3.1 목표

사용자가 **매일 겪는** 6대 흐름 단절을 VibeZoo + MCP + Crow(외부) + Config로 제거한다. 바이브 점수 5.0 → 7.0.

### 3.2 6대 흐름 차원 (Companion-First 구현)

| 차원 | 현재 | 목표 | 구현 방식 |
|:---|:---:|:---:|:---|
| **D1: 세션 지속성** | 3/10 | 7/10 | `[Config]` custom_modes.yaml에 모드 고정 + `[VibeZoo]` Crow(외부) 재연결 + StatusBar 표시 |
| **D2: 모드 전환 마찰** | 4/10 | 7/10 | `[VibeZoo]` 프로젝트 감지 → StatusBar에 "권장 모드" 제안 (1클릭) |
| **D3: 빌드-피드백 루프** | 4/10 | 8/10 | `[VibeZoo]` Task Provider(silent) + `onDidEndTaskProcess` → `[Crow]` crow_ingest→bug |
| **D4: 컨텍스트 로트** | 4/10 | 7/10 | `[Crow]` crow_compact 10분 간격 + `[VibeZoo]` 트리거 (파일 저장 시) |
| **D5: 파일 탐색 마찰** | 5/10 | 8/10 | `[VibeZoo]` ProjectTreeScanner + `[Crow]` arch 레지스터 연동. 트리 정보를 MCP tool로 제공 |
| **D6: 외부 리소스 탐색** | 3/10 | 8/10 | `[MCP]` crow_research MCP 도구 (Brave/Tavily API) + `[VibeZoo]` 검색 트리거 |

### 3.3 핵심 구현 항목

| # | 항목 | 태그 | 설명 |
|:---|:---|:---|:---|
| W1-1 | **Silent Build Task Provider** | `[VibeZoo]` | `registerTaskProvider`로 `crow: build` 태스크 제공. `presentation.reveal: silent` — 에러 시에만 터미널 표시. 프로젝트 타입 자동 감지(package.json→npm, Cargo.toml→cargo 등) |
| W1-2 | **`onDidEndTaskProcess` 구독** | `[VibeZoo]` | exitCode ≠ 0 → stderr 수집 → `[Crow]` crow_ingest(register="bug") 호출 → LSP diagnostics 0.5초 후 수집 |
| W1-3 | **Project Auto-Detector** | `[VibeZoo]` | `onDidChangeWorkspaceFolders` → `.zoo/config.json`, `package.json` 등 스캔 → StatusBar에 `"$(gear) 권장 모드: Code + Crow [적용]"` 버튼. 1클릭으로 모드 변경 제안. |
| W1-4 | **`AGENTS.md` / `.zoo.md` 감시** | `[VibeZoo]` | `FileSystemWatcher`로 프로젝트 룰 파일 변경 감지. 내용을 `[Crow]` crow_ingest(register="arch")로 저장. |
| W1-5 | **`ProjectTreeScanner`** | `[VibeZoo]` | `findFiles()`로 프로젝트 트리 스캔 + 30초 TTL 캐시 + `FileSystemWatcher` 증분 갱신. 결과를 `[Crow]` 도구로 LLM에 제공. |
| W1-6 | **`crow_compact` 자동화** | `[VibeZoo]` + `[Crow]` | `onWillSaveTextDocument` 이벤트 → 10분 간격 `crow_compact` 호출. 요약 결과를 `life_context`에 저장. |
| W1-7 | **`crow_research` MCP 도구** | `[MCP]` | Brave Search / Tavily API 호출. 검색 결과를 Markdown으로 정리. `[VibeZoo]`이 채팅 입력에서 검색 키워드("~찾아줘", "~문서") 감지 시 MCP 도구 호출 제안. |
| W1-8 | **LSP Diagnostics 피드백** | `[VibeZoo]` | `onDidChangeDiagnostics` 1초 debounce → 진단 요약 → `[Crow]` crow_ingest |

### 3.4 Crow 연동

| 차원 | MCP 도구 | 레지스터 |
|:---|:---|:---|
| 빌드 피드백 | `crow_ingest` | `bug` (빌드 에러 패턴) |
| 컨텍스트 로트 | `crow_compact` | `context` → `arch` |
| 파일 탐색 | `crow_ingest`, `crow_recall` | `arch` (프로젝트 구조) |
| 외부 리소스 | `crow_ingest` | `life_context` (검색 이력) |
| 모드/규칙 | `crow_ingest` | `arch` (AGENTS.md 내용) |

---

## 4. Wave 2: Fearless YOLO (Week 6-12)

### 4.1 목표

YOLO 모드의 심리적 불안을 제거한다. "되돌려줘" 한 마디(또는 `Ctrl+Shift+Z`)에 0.3초 내 복구. 바이브 점수 7.0 → 8.0.

### 4.2 VibeZoo 안전망 (수정된 3계층)

Zoo Code 소스 없이는 **Layer 1(사전 차단)**을 구현할 수 없다. 따라서 Layer 2(실시간 감지+복구)와 Layer 3(사후 복구)를 중심으로 설계하고, Layer 1의 역할은 `[Config]`로 Zoo Code의 MCP 도구 권한 설정으로 대체한다.

```
LAYER 1: Prevention (우회 — Config 기반)
├── Zoo Code MCP 도구 권한 설정으로 위험한 도구 제한
└── .yoloignore 파일 → Companion이 주기적으로 Crow와 동기화

LAYER 2: Real-time Detection & Recovery (Companion)
├── yocto: FileSystemWatcher + fs.copyFileSync (200ms debounce)
├── 보호 파일 감지: .yoloignore 매칭 파일 변경 → 즉시 yocto 복구
└── crow_manage_backup 자동 호출

LAYER 3: Post-hoc Recovery (Companion)
├── localHistory 버전 복원 (VS Code 내장)
├── Git stash 자동화 (YOLO 진입/퇴장)
└── AutoBuildFix: 빌드 실패 → LLM 수정 → 재빌드 (max_attempts=3)
```

### 4.3 핵심 구현 항목

| # | 항목 | 태그 | 설명 |
|:---|:---|:---|:---|
| W2-1 | **`YoctoSnapshotManager`** | `[VibeZoo]` | `FileSystemWatcher`로 `**/*.{ts,tsx,js,jsx,py}` 감시. 파일 변경 시 `fs.copyFileSync`로 `~/.zoo-code/yocto/{sessionId}/{timestamp}/`에 백업. 200ms debounce. |
| W2-2 | **`instantRewind()`** | `[VibeZoo]` | Command Palette에 `VibeZoo: Instant Rewind` 등록. 단축키 `Ctrl+Shift+Z`. 마지막 YOLO 세션의 모든 백업 파일을 원위치로 복사. VS Code 문서 캐시 새로고침. |
| W2-3 | **`.yoloignore` File Guard** | `[VibeZoo]` | FileSystemWatcher로 `.yoloignore` 매칭 파일 변경 감지 → 즉시 yocto 백업으로 복구 → 사용자에게 알림: `"보호된 파일 ${name}의 변경이 자동 복구되었습니다."` |
| W2-4 | **Git Stash 자동화** | `[VibeZoo]` | `VibeZoo: Toggle YOLO Mode` 커맨드. 실행 시: (1) `git stash push -m "yolo-before-{timestamp}"`, (2) `[Crow]` crow_manage_backup create, (3) StatusBar에 "YOLO: ON" 표시. 종료 시: 성공→커밋, 실패→Rewind 제안. |
| W2-5 | **`AutoBuildFix`** | `[VibeZoo]` + `[Crow]` | `onDidEndTaskProcess`로 빌드 실패 감지 → stderr 파싱 → `[Crow]` crow_recall(register="bug")로 과거 유사 에러 조회 → LLM에 수정 요청 (Zoo Code를 통해) → 재빌드. max_attempts=3 + oscillation 감지. |
| W2-6 | **`.yoloignore` ↔ Crow 동기화** | `[VibeZoo]` + `[Crow]` | 주기적으로 `crow_recall(register="life_avoid")` → 새로운 회피 패턴 발견 시 `.yoloignore`에 자동 추가. |
| W2-7 | **YOLO History TreeView** | `[VibeZoo]` | Explorer에 "YOLO Sessions" 트리. 각 세션의 파일 목록, 타임스탬프, 상태(active/rewound/committed) 표시. |
| W2-8 | **`crow_manage_backup`** | `[Crow]` | YOLO 진입/퇴장 시 Crow 메모리 스냅샷 생성/복원. Crow Memory의 기본 도구. |

### 4.4 성능 목표

| 시나리오 | 메커니즘 | 목표 시간 |
|:---|:---|:---|
| 단일 파일 복구 | yocto `fs.copyFileSync` | **< 100ms** |
| 10개 파일 복구 | yocto 순차 복사 | **< 500ms** |
| 보호 파일 변경 감지→복구 | FileSystemWatcher + yocto | **< 500ms** |
| 빌드 실패→자동 수정 (1회) | AutoBuildFix | **< 15s** |

---

## 5. Wave 3: Explain-Less (Week 12-18)

### 5.1 목표

사용자의 반복 설명 부담을 80% 이상 감소시킨다. Zoo Code 메시지 파이프라인을 가로챌 수 없는 제약 속에서, **Crow Memory 도구 + Config 강화 + VibeZoo 사이드채널**의 3중 전략으로 접근. 바이브 점수 8.0 → 8.7.

> **이름 변경**: "Zero-Explanation" → "Explain-Less". 완전한 무설명은 불가능하지만, 설명 부담을 극적으로 줄인다.

### 5.2 3중 Context 전략

```
전략 A: Config 기반 (custom_modes.yaml 강화)
  ├── crow_recall 호출 지시를 더 강력하게 작성
  ├── .zoo.md / AGENTS.md를 읽어들이는 지시 포함
  └── 프로젝트별 규칙을 system prompt에 명시

전략 B: Crow Memory 도구 기반 (LLM이 MCP tool call로 호출)
  ├── crow_recall(domain="all") → 사용자 편향, 프로젝트 규칙, 과거 패턴 회상
  ├── crow_compact → 세션 요약 → life_context 저장
  └── LLM이 자율적으로 필요할 때 호출 (이상적 시나리오)

전략 C: VibeZoo 사이드채널 (비침투적 알림)
  ├── 사용자 입력 감지 → StatusBar에 "💡 Crow 맥락 로드됨" 표시
  ├── 세션 시작 시 "지난 세션 요약"을 Webview로 표시 (읽기 전용)
  └── crow_recall 누락 감지 → StatusBar에 경고
```

### 5.3 핵심 구현 항목

| # | 항목 | 태그 | 설명 |
|:---|:---|:---|:---|
| W3-1 | **`custom_modes.yaml` 강화** | `[Config]` | 시스템 프롬프트에 "매 응답 전 `crow_recall(domain='all')`을 호출하라"는 지시를 최우선 순위로 배치. `.zoo.md` 파일을 읽어들이는 지시 포함. |
| W3-2 | **`crow_recall` 도구 개선** | `[Crow]` | 도메인별 필터링(`coding`, `style`, `architecture`), 관련도 점수, 최신 항목 우선(recency bias) 기능 강화. Crow Memory 기본 도구. |
| W3-3 | **`crow_compact` 도구 개선** | `[Crow]` | Claude Code 3-tier compaction 방식 적용. 요약 구조: Goal → Standing Instructions → Key Discoveries → Accomplished → Relevant Files → Next Steps. |
| W3-4 | **`SessionResume` Webview** | `[VibeZoo]` | VS Code 시작 시(`onStartupFinished`) 직전 세션의 요약을 Webview 패널로 표시. "지난 세션: JWT 인증 리팩토링 중이었음. 3개 파일 수정됨. [이어서 작업]" |
| W3-5 | **`ContextStatusIndicator`** | `[VibeZoo]` | StatusBar에 `"Crow Context: 87% fresh"` 표시. 복합 지표(recently + relevance + coverage + confidence). |
| W3-6 | **`ExplainLessSuggestor`** | `[VibeZoo]` | 사용자 입력에서 반복 설명 패턴 감지 (예: "또 Zustand라고 말해야 하나?"). StatusBar에 `"💡 이 프로젝트의 상태관리는 Zustand입니다. system_prompt.md에 추가할까요?"` 제안. |
| W3-7 | **`system_prompt.md` HITL 파이프라인** | `[VibeZoo]` + `[Crow]` | `crow_evolve_propose`가 규칙 후보 제안 → QuickPick으로 승인/거부/수정 → `.zoo/system_prompt.md`에 추가 → Git 커밋/푸시. |
| W3-8 | **`EmotionalContextDetector`** | `[VibeZoo]` | 자체 Chat Participant에서 사용자 메시지 분석. 3회 연속 거절("아니", "다시 해", "그렇게 하지 마") 감지 → `[Crow]` crow_ingest(register="life_avoid", polarity=-2.0). |
| W3-9 | **Global + Project `.crow.bin` 계층화** | `[Crow]` | `~/.zoo-code/crow/crow.bin` (전역) + `{project}/.crow.bin` (프로젝트). 프로젝트 특화 지식은 프로젝트에, 개인 편향은 전역에. Crow Memory의 저장소 계층 구조. |

### 5.4 손실 분석: Zero-Explanation vs Explain-Less

| 기능 | Full Architecture (Zoo Code 수정) | VibeZoo (API 기반) | 손실 |
|:---|:---|:---|:---|
| 매 턴 자동 Context Injection | ContextInjector가 system prompt prepend | `[Config]` 지시 + `[Crow]` tool call + `[VibeZoo]` StatusBar 알림. API 모델은 tool call 신뢰도가 높아 실질적 손실 적음. | ~10% |
| Context Injection 안전망 | FallbackInjector | 불필요 — API 모델은 시스템 프롬프트 지시를 안정적으로 수행 | 0% |
| Cross-Session Memory | globalState 세션 요약 + 자동 복원 | SessionResume Webview + crow_compact | ~10% |
| Emotional Context | 모든 채널에서 사용자 메시지 분석 | VibeZoo Chat Participant에서 분석 + `[Crow]` life_avoid 저장 | ~10% |
| **종합** | **100%** | **~90%** | **~10%** |

> **API 환경의 이점**: 로컬 4B 모델의 tool call 불안정성(30-60% 실패율)이 완전히 제거된다. API 모델(GPT-4, Claude, DeepSeek 등)은 시스템 프롬프트 지시를 안정적으로 따르므로, FallbackInjector 같은 복잡한 우회 메커니즘이 불필요하다. "완전한 Zero-Explanation"은 아니지만, 설명 부담의 90%는 제거 가능하다.

---

## 6. Wave 4: Orchestra of One (Week 18-24)

### 6.1 목표

Scout Subagent를 시작으로 병렬 AI 작업을 구현한다. Zoo Code 채팅과 별개인 VS Code Chat Participant를 활용해 `@scout` 라우팅을 제공. 바이브 점수 8.7 → 9.0.

### 6.2 Scout-First 점진적 확장

```
Phase A (Week 18-20): Scout 단독
  └── Scout MCP 서버 + Chat Participant @scout
  └── BackgroundTaskManager + TreeView
  └── 2주간 안정화

Phase B (Week 20-22): Reviewer + Tester 추가
  └── 안정화 확인 후 확장

Phase C (Week 22-24): Fleet Dashboard 완성
  └── Webview 대시보드 + Lock Manager + 충돌 해결
```

### 6.3 핵심 구현 항목

| # | 항목 | 태그 | 설명 |
|:---|:---|:---|:---|
| W4-1 | **`SubagentManager`** | `[VibeZoo]` | `child_process.spawn`로 MCP 서버 프로세스 관리. idle 5분 후 auto-terminate. health check. |
| W4-2 | **Scout MCP 서버** | `[MCP]` | Python FastMCP. `search_codebase`, `find_references`, `summarize_architecture`. 포트 9022. VibeZoo가 spawn. |
| W4-3 | **Reviewer MCP 서버** | `[MCP]` | Python FastMCP. `review_code`, `check_quality`, `suggest_improvements`. 포트 9023. (Phase B) |
| W4-4 | **Tester MCP 서버** | `[MCP]` | Python FastMCP. `generate_tests`, `analyze_coverage`. 포트 9024. (Phase B) |
| W4-5 | **Chat Participant `@scout`, `@reviewer`, `@tester`** | `[VibeZoo]` | `vscode.chat.createChatParticipant`로 VS Code 공식 Chat에 등록. `@scout 이거 찾아줘` → Scout MCP 서버로 라우팅. Zoo Code 채팅과 별개 채널. |
| W4-6 | **`BackgroundTaskManager`** | `[VibeZoo]` | `vscode.window.withProgress`로 진행률 표시. 완료 시 Opt-In 알림("Scout 완료: 15개 결과 [보기] [무시]"). 취소 가능. |
| W4-7 | **`ActiveSubagentsProvider` TreeView** | `[VibeZoo]` | Explorer에 "Active Subagents" 트리. idle/running/completed/error 상태별 아이콘. 현재 작업 설명. |
| W4-8 | **`OrchestraDashboard` Webview** | `[VibeZoo]` | 작업 목록, 진행률(ProgressBar), ETA, 충돌 상태. SSE 실시간 업데이트. `retainContextWhenHidden: true`. |
| W4-9 | **Crow Lock Manager** | `[Crow]` | `lock_acquire`/`lock_release`/`lock_check` 도구. 대기 큐, 데드락 감지 및 선점. Crow Memory 서버 내 구현. |
| W4-10 | **충돌 해결** | `[VibeZoo]` | FileSystemWatcher 무단 쓰기 감지 + VS Code Merge Conflict UI + AI 자동 3-way merge. |

### 6.4 Subagent 결과 → Crow 자동 저장

| Subagent | 레지스터 | 예시 |
|:---|:---|:---|
| Scout | `arch` | "이 프로젝트는 Result<T,E> 패턴 사용" |
| Reviewer | `style` | "함수명 camelCase, 파일명 kebab-case" |
| Tester | `bug` | "auth.ts:45 경계값 테스트 누락" |

---

## 7. Wave 5: Visual Vibe (Week 16-24) [신규 — 병렬 개발]

### 7.1 목표

AI와 사용자가 **시각적으로 협업**할 수 있는 채널. 모든 UI는 VibeZoo Extension의 Webview로 구현. 바이브 점수 9.0 → 9.3.

### 7.2 4대 Visual Vibe 차원

| 차원 | 현재 | 목표 | 구현 |
|:---|:---:|:---:|:---|
| **D1: Shared Whiteboard** | 1/10 | 8/10 | `[VibeZoo]` Fabric.js Webview + `[Crow]` SSE 드로잉 동기화 |
| **D2: UI Mockup Preview** | 1/10 | 9/10 | `[VibeZoo]` iframe 샌드박스 + 실시간 코드 렌더링 |
| **D3: Screenshot Context** | 1/10 | 8/10 | `[VibeZoo]` 이미지 입력 → 멀티모달 API 분석 |
| **D4: Diagram Visualization** | 2/10 | 9/10 | `[VibeZoo]` Mermaid.js + D3.js Webview |

### 7.3 핵심 구현 항목

| # | 항목 | 태그 | 설명 |
|:---|:---|:---|:---|
| W5-1 | **`WhiteboardWebview`** | `[VibeZoo]` | Fabric.js 캔버스. 펜, 도형, 텍스트, 이미지 도구. AI가 다이어그램/레이아웃을 그리고, 사용자가 주석 추가. |
| W5-2 | **Whiteboard SSE Sync** | `[VibeZoo]` + `[Crow]` | 드로잉 이벤트를 Crow Visual Context Store를 통해 실시간 동기화. 세션 저장/복원. |
| W5-3 | **`UIPreviewWebview`** | `[VibeZoo]` | iframe sandbox + Babel standalone + Tailwind CDN. React/Vue 컴포넌트 코드를 받아 실시간 렌더링. 뷰포트 전환(모바일/데스크탑). |
| W5-4 | **`ScreenshotAnalyzer`** | `[VibeZoo]` + `[Crow]` | 클립보드 이미지 감지 → 멀티모달 LLM API 호출 → 디자인 요소 추출 → `[Crow]` crow_ingest(register="life_context"). |
| W5-5 | **`DiagramEngine`** | `[VibeZoo]` + `[MCP]` | Mermaid.js 렌더링 + D3.js Force Graph. 다이어그램 노드 클릭 → VS Code 파일 열기(`vscode.open`). |
| W5-6 | **Visual Context Store** | `[Crow]` | Crow Memory에 화이트보드 세션, 다이어그램 데이터, UI 선호도 저장. Crow의 확장 저장소. |
| W5-7 | **UI Preview - Code Sync** | `[VibeZoo]` | AI가 코드 생성 → VibeZoo가 Webview에 `postMessage({ type: 'render', code })` 전송 → 즉시 미리보기 업데이트. |

### 7.4 Visual Vibe 데이터 흐름

```
AI 코드 생성
    │
    ▼
[VibeZoo: UIPreviewWebview]
    │ postMessage({ type: 'render', code })
    ▼
[iframe sandbox] → 실시간 렌더링
    │
    │ 사용자가 "버튼 색상 진하게"
    ▼
[VibeZoo: 채팅 입력] → Zoo Code → AI 코드 수정
    │
    └── 수정된 코드 → 다시 Webview로 → 즉시 반영
```

---

## 8. Wave 6: Deep Analysis (Week 20-26) [신규 — 병렬 개발]

### 8.1 목표

코드베이스를 외과적으로 분석하고 역설계한다. 모든 분석 로직은 MCP 서버에서, 시각화는 VibeZoo Webview에서. 바이브 점수 9.3 → 9.5.

### 8.2 4대 Deep Analysis 차원

| 차원 | 현재 | 목표 | 구현 |
|:---|:---:|:---:|:---|
| **D1: Call Graph Generator** | 2/10 | 9/10 | `[MCP]` Tree-sitter AST → 함수 호출 그래프 → `[VibeZoo]` D3.js 시각화 |
| **D2: Dependency Mapper** | 2/10 | 9/10 | `[MCP]` import 분석 + Tarjan's SCC 순환 참조 탐지 → `[VibeZoo]` 히트맵 |
| **D3: Code Pattern Extractor** | 2/10 | 9/10 | `[MCP]` AST 기반 빈도 패턴 마이닝 → `[Crow]` style/bug 레지스터 자동 등록 |
| **D4: Reverse Engineering** | 1/10 | 8/10 | `[MCP]` LSP + AST → OpenAPI/ERD/UML 자동 생성 → `[Crow]` arch 저장 |

### 8.3 핵심 구현 항목

| # | 항목 | 태그 | 설명 |
|:---|:---|:---|:---|
| W6-1 | **Deep Analyzer MCP 서버** | `[MCP]` | Python FastMCP + Tree-sitter. `analyze_call_graph`, `map_dependencies`, `extract_patterns`, `reverse_engineer`. 포트 9026. VibeZoo가 spawn. |
| W6-2 | **`CallGraphVisualizer`** | `[VibeZoo]` | D3.js Force-Directed Graph. 노드 클릭 → 해당 함수로 이동. 방향 엣지로 호출 관계 표시. |
| W6-3 | **`DependencyHeatmap`** | `[VibeZoo]` | Webview로 파일 간 의존성 히트맵. 순환 참조 빨간색 강조. 과도한 결합(import 20회+) 경고. |
| W6-4 | **`PatternReport`** | `[VibeZoo]` | 추출된 코드 패턴을 Markdown 리포트로 표시. QuickPick으로 "이 패턴을 system_prompt.md에 추가할까요?" 승인. |
| W6-5 | **역설계 문서 생성기** | `[MCP]` + `[VibeZoo]` | 분석 결과 → OpenAPI 3.0 YAML, Mermaid ERD, Markdown 문서 자동 생성. `.zoo/docs/`에 저장. |
| W6-6 | **Pattern → Crow 자동 등록** | `[Crow]` | `PatternExtractor` 결과 → `crow_ingest(register="style")` + `crow_evolve_propose`로 `system_prompt.md` 추가 제안. Crow Memory 연동. |
| W6-7 | **Deep Analysis Chat Participant** | `[VibeZoo]` | `@analyze call-graph src/services/auth.ts` → Deep Analyzer MCP 호출 → Webview로 시각화. |

### 8.4 Deep Analysis Crow 연동

| 기능 | 레지스터 | 저장 내용 |
|:---|:---|:---|
| Call Graph | `arch` | 함수 호출 관계, 변경 영향도 데이터 |
| Dependency Map | `bug` | 순환 참조, 과도한 결합 → 사전 경고 |
| Pattern Extract | `style` | 코드 패턴 규칙 → `crow_evolve_propose` |
| Reverse Eng | `arch` | API 명세, 데이터 모델, 아키텍처 문서 |

---

## 9. Priority Matrix (VibeZoo-First)

### 9.1 핵심 원칙

- `x`(구현 난이도): 1(쉬움) ~ 10(신규 아키텍처 필요)
- `y`(사용자 피로도 감소): 1(미미함) ~ 10(매일 여러 번 겪는 마찰 제거)
- `z`(VibeZoo 구현 적합성): 1(MCP/Config로만 가능) ~ 10(VibeZoo Extension API 완벽 지원)
- **3D Score = y×0.4 + z×0.3 + (11-x)×0.3**

### 9.2 상위 20개 우선순위

| 순위 | 항목 | Wave | 태그 | x | y | z | 3D |
|:---:|:---|:---|:---|:---:|:---:|:---:|:---:|
| 1 | Silent Build Task Provider | W1 | `[VibeZoo]` | 3 | 9 | 10 | **8.1** |
| 2 | `onDidEndTaskProcess` 빌드 수집 | W1 | `[VibeZoo]` | 3 | 9 | 10 | **8.1** |
| 3 | Crow 연결 StatusBar | P0 | `[VibeZoo]` | 2 | 7 | 10 | **7.9** |
| 4 | yocto 자동 백업 | W2 | `[VibeZoo]` | 4 | 9 | 9 | **7.8** |
| 5 | `instantRewind()` | W2 | `[VibeZoo]` | 4 | 9 | 9 | **7.8** |
| 6 | UI Mockup Preview | W5 | `[VibeZoo]` | 4 | 9 | 8 | **7.5** |
| 7 | 프로젝트 자동 감지 + 모드 제안 | W1 | `[VibeZoo]` | 3 | 7 | 10 | **7.3** |
| 8 | `.yoloignore` File Guard | W2 | `[VibeZoo]` | 4 | 8 | 9 | **7.2** |
| 9 | `ProjectTreeScanner` | W1 | `[VibeZoo]` | 5 | 7 | 9 | **6.7** |
| 10 | `custom_modes.yaml` 강화 | W3 | `[Config]` | 2 | 8 | 6 | **6.8** |
| 11 | `crow_compact` 자동화 | W1 | `[VibeZoo]`+`[Crow]` | 5 | 6 | 9 | **6.3** |
| 12 | AutoBuildFix | W2 | `[VibeZoo]`+`[Crow]` | 6 | 9 | 8 | **7.2** |
| 13 | Diagram Visualization | W5 | `[VibeZoo]` | 5 | 8 | 7 | **6.8** |
| 14 | `SessionResume` Webview | W3 | `[VibeZoo]` | 4 | 7 | 8 | **6.7** |
| 15 | `.zoo.md` / `AGENTS.md` 감시 | W1 | `[VibeZoo]` | 3 | 5 | 9 | **6.5** |
| 16 | Call Graph Generator | W6 | `[MCP]`+`[VibeZoo]` | 5 | 8 | 7 | **6.8** |
| 17 | Scout MCP 서버 | W4 | `[MCP]` | 6 | 7 | 7 | **6.4** |
| 18 | Chat Participant `@scout` | W4 | `[VibeZoo]` | 5 | 7 | 8 | **6.7** |
| 19 | Pattern Extractor | W6 | `[MCP]` | 5 | 8 | 6 | **6.5** |
| 20 | `EmotionalContextDetector` | W3 | `[VibeZoo]`+`[Crow]` | 6 | 6 | 8 | **5.9** |

---

## 10. Implementation Roadmap

### 10.1 전체 타임라인

```
Week  0    2    4    6    8    10   12   14   16   18   20   22   24   26
├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
│ P0  │                                                                  │
├─────┤                                                                  │
│     │ W1: Unbreakable Flow                                            │
│     ├──────────────────┤                                              │
│     │                  │ W2: Fearless YOLO                            │
│     │                  ├─────────────────────┤                        │
│     │                  │                     │ W3: Explain-Less       │
│     │                  │                     ├──────────────────┤    │
│     │                  │  W5: Visual Vibe (8주, 병렬)                │
│     │                  │  ├────────────────────────────────────┤     │
│     │                  │  │ W6: Deep Analysis (6주, 병렬)      │     │
│     │                  │  │      ├──────────────────────────────┤    │
│     │                  │  │      │ W4: Orchestra of One         │    │
│     │                  │  │      │  ├───────────────────────────┤    │
└─────┴──────────────────┴──┴──────┴──┴───────────────────────────┴────┘
```

### 10.2 마일스톤

| 마일스톤 | 시점 | 바이브 | 핵심 성과 |
|:---|:---|:---:|:---|
| **M0: Foundation** | Week 2 | 5.0 | VibeZoo Extension 작동, Crow(외부) 연결, 상태바 |
| **M1: Flow** | Week 6 | 7.0 | Silent 빌드, 프로젝트 감지, 트리 스캔, 검색 |
| **M2: Fearless** | Week 12 | 8.0 | yocto 백업/복구, File Guard, AutoBuildFix |
| **M3: Visual Alpha** | Week 20 | 8.5 | Whiteboard + UI Preview + Diagram 기본 |
| **M4: Explain-Less** | Week 18 | 8.7 | Config 강화, SessionResume, EmotionalDetector |
| **M5: Analyze Alpha** | Week 22 | 8.9 | Call Graph + Pattern Extract 기본 |
| **M6: Orchestra Alpha** | Week 24 | 9.0 | Scout + @mentions + Dashboard |
| **M7: Full Integration** | Week 26 | 9.0 | 전 Wave 통합 안정화 |

### 10.3 병렬 트랙

| 트랙 | 담당 | 시작 | 종료 | 핵심 기술 |
|:---|:---|:---|:---|:---|
| **트랙 A: Core** | W1→W2→W3→W4 | Week 2 | Week 24 | VS Code Extension API, MCP |
| **트랙 B: Visual** | W5 | Week 16 | Week 24 | Webview, Canvas, D3.js |
| **트랙 C: Analysis** | W6 | Week 20 | Week 26 | Tree-sitter, LSP, AST |

---

## 11. Risk Management

| # | 리스크 | 확률 | 대응책 |
|:---|:---|:---:|:---|
| R1 | Crow SSE 서버(외부) 응답 불가 | 25% | 모든 `[Crow]` 호출 3초 타임아웃. 실패 시 `[VibeZoo]` 단독 동작 + StatusBar 경고. Crow는 외부 시스템이므로 VibeZoo 자체는 정상 작동. |
| R2 | API LLM 서비스 장애 | 10% | Zoo Code의 API 설정에 따른 장애. VibeZoo가 통제할 수 없는 영역이므로, 핵심 기능은 Crow 로컬 캐시 + StatusBar 알림으로 gracefully degrade. |
| R3 | FileSystemWatcher ENOSPC | 15% | `watcherExclude` 자동 설정 + 폴링(30초) 폴백. |
| R4 | Webview 성능 저하 (W5) | 20% | `retainContextWhenHidden` + requestAnimationFrame 배칭 + 가상 DOM. |
| R5 | Subagent orphan 프로세스 | 20% | `deactivate()`에서 SIGTERM → 5초 후 SIGKILL + PID 파일 정리. |
| R6 | Chat Participant API 변경 | 30% | `createChatParticipant` 가용성 런타임 체크 + 커스텀 Command 폴백. |

---

## 12. Success Metrics

### 12.1 10개 평가 축 (VibeZoo-First 목표)

| 축 | 현재 | P0 | W1 | W2 | W3 | W4 | W5 | W6 | 목표 |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| A1: 세션 연속성 | 3 | 4 | 6 | 6 | 7 | 7 | 7 | 7 | 7 |
| A2: 모드 전환 마찰 | 4 | 4 | 7 | 7 | 7 | 7 | 7 | 7 | 7 |
| A3: 빌드 피드백 | 4 | 4 | 8 | 8 | 8 | 8 | 8 | 8 | 8 |
| A4: 컨텍스트 지속성 | 4 | 4 | 6 | 7 | 8 | 8 | 8 | 8 | 8 |
| A5: YOLO 안전성 | 3 | 3 | 4 | 8 | 8 | 8 | 8 | 8 | 8 |
| A6: 설명 부담 감소 | 3 | 3 | 4 | 5 | 8 | 8 | 8 | 8 | 8 |
| A7: 병렬 작업 | 2 | 2 | 2 | 3 | 5 | 8 | 8 | 8 | 8 |
| A8: 시각 협업 | 1 | 1 | 1 | 1 | 2 | 3 | 8 | 8 | 8 |
| A9: 분석 깊이 | 2 | 2 | 2 | 3 | 4 | 5 | 6 | 9 | 9 |
| A10: 통제감 | 5 | 6 | 7 | 8 | 9 | 9 | 9 | 9 | 9 |
| **가중 평균** | **4.2** | **4.8** | **6.7** | **7.7** | **8.5** | **8.8** | **9.0** | **9.2** | **9.2** |

> **참고**: Full Architecture(소스 수정 허용)의 목표가 9.5인 것과 비교해 VibeZoo-First는 9.2가 현실적 상한이다. 0.3점 차이는 "LLM 메시지 파이프라인 접근 불가"에서 오는 Explain-Less의 한계다. API 모델 사용으로 로컬 모델 이슈가 제거되어 이전 추정(9.0)보다 0.2점 상향 조정되었다.

---

## 13. Conclusion

Zoo Code 소스 코드를 **단 한 줄도 수정하지 않고**, 우리는:

- **VibeZoo Extension**으로 StatusBar, TreeView, Webview, FileSystemWatcher, Task Provider, Chat Participant를 제공하고
- **VibeZoo MCP 서버**로 Subagent(Scout/Reviewer/Tester), Deep Analyzer를 운영하며
- **Crow Memory(외부)**와 SSE로 유기적으로 연동하여 기억·편향·컨텍스트를 관리하고
- **Config 파일**로 Zoo Code의 시스템 프롬프트와 프로젝트 설정을 강화한다

이 4중 구조로 **바이브 점수 4.2 → 9.2**의 도약이 가능하다.

잃는 것은 0.3점. 얻는 것은:
- Zoo Code 릴리스 주기로부터의 **완전한 독립성**
- Zoo Code뿐 아니라 모든 MCP 호환 도구에서의 **범용성**
- Crow Memory의 **독립적 진화 가능성** (VibeZoo와 무관하게 업그레이드)
- 포크 유지보수 부담의 **제로화**

> **다음 단계**: Phase 0 + Wave 1 Phase A의 상세 구현 명세서(`fromscratch/implementation-wave1-phaseA.md`) 작성.
