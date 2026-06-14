# VibeZoo 프로젝트 컨텍스트

> **VibeZoo = [Crow Memory](#crow-memory-개요) (Synaptic Memory) + [VibeZoo MCP Bridge](#mcp-도구-카탈로그) (37+ Tools)**
>
> Zoo Code를 위한 동반자 확장(Companion Extension)으로, LLM이 코드를 더욱 지능적으로 검색·분석·리뷰·문서화할 수 있도록 돕습니다.

- **마지막 업데이트**: 2026-06-13
- **버전**: v0.15.0 (extension), v0.15.0 (bridge config)
- **라이선스**: MIT
- **저장소**: <https://github.com/vibezoo/VibeZoo_forZoocode>

---

## 목차

1. [프로젝트 개요](#1-프로젝트-개요)
2. [기술 스택](#2-기술-스택)
3. [시스템 아키텍처](#3-시스템-아키텍처)
4. [진입점](#4-진입점)
5. [데이터 흐름](#5-데이터-흐름)
6. [모듈 맵](#6-모듈-맵)
7. [통신 구조](#7-통신-구조)
8. [MCP 도구 카탈로그](#8-mcp-도구-카탈로그)
9. [주요 패턴 및 컨벤션](#9-주요-패턴-및-컨벤션)
10. [알려진 이슈 및 병목](#10-알려진-이슈-및-병목)
11. [빠른 시작](#11-빠른-시작)
12. [주요 의존성](#12-주요-의존성)

---

## 1. 프로젝트 개요

| 항목 | 상세 |
|------|------|
| **이름** | VibeZoo |
| **표시 이름** | `%vibezoo.displayName%` (i18n) |
| **버전** | `0.15.0` |
| **타입** | VS Code Extension + Python MCP Server (듀얼 프로젝트) |
| **목적** | Zoo Code(AI 코딩 어시스턴트)를 위한 동반자 확장. 코드 검색, 리뷰, 시각 협업, 자율 빌드 픽스, 메모리 기반 개인화 제공 |
| **타겟 플랫폼** | VS Code `^1.90.0` |
| **주요 기능** | Guard.git(`.git` 보호), YOLO 스냅샷, Whiteboard/Dropzone, Crow Memory 연동, 37+ MCP 도구 |
| **라이선스** | MIT |
| **저장소** | <https://github.com/vibezoo/vibezoo> |

VibeZoo는 Zoo Code의 소스 코드를 한 줄도 수정하지 않고, MCP/SSE와 VS Code Extension API를 통해 기능을 확장합니다. 핵심 철학은 **"Crow remembers not the code, but the hand that wrote it."** — 즉, 코드 자체가 아니라 사용자의 습관과 맥락을 기억하는 것입니다.

> **Crow Memory의 핵심 개념**: Transformer 기반 LLM은 학습 시점에서 고정됩니다. Crow은 고정 크기 가중치 행렬과 λ(decay rate)를 통해 **"Creative Forgetting"**을 구현하여, 100% 정확한 회상을 포기하는 대신 **현재의 사용자**에게 편향된 응답을 만듭니다.
>
> Hebbian EMA 업데이트 규칙: `W_new = λ · W_old + (1 − λ) · (key ⊗ value)`

---

## 2. 기술 스택

### 2.1 VS Code Extension (TypeScript)

| 기술 | 버전 / 용도 |
|------|------------|
| TypeScript | `^5.3.0` — 확장 로직 구현 |
| VS Code API | `^1.90.0` — Extension, TreeView, Webview, StatusBar |
| CommonJS | `extension/tsconfig.json` 기준 모듈 시스템 |
| ES2022 | 대상 런타임 |
| `minimatch` | Glob 패턴 매칭 |
| `eslint` | 린팅 |
| `@vscode/vsce` | VSIX 패키징 |
| `@vscode/l10n-dev` | 다국어(i18n/l10n) 지원 — 영어 기반 + 한국어(`ko`) 번역 팩 |

### 2.2 MCP Bridge Server (Python)

| 기술 | 용도 |
|------|------|
| Python | `3.10+` |
| `fastmcp` | FastMCP SSE 서버 프레임워크 |
| `starlette` | HTTP 라우팅 (`/health`, `/tools/list_subagents`) |
| `tree_sitter_languages` | 멀티랭귀지 AST 파싱 |
| `llama-cpp-python` | MiniCPM-V GGUF 추론 |
| `pytesseract` / `PaddleOCR` | OCR 엔진 |
| `opencv-python` | 이미지 전처리, SSA |
| `curl_cffi` + `selectolax` + `httpx` | 웹 검색/파싱 |
| `requests` | Crow Memory REST API 클라이언트 |

---

## 3. 시스템 아키텍처

VibeZoo는 **3-Layer Hybrid Architecture**로 구성됩니다. v0.15.0부터는 확장 자체가 Python MCP Bridge(9027)와 Crow Memory fallback(9020)을 자동으로 시작하며, Zoo Code는 `.roo/mcp.json`을 통해 자동으로 Bridge에 SSE 연결합니다.

```text
┌───────────────────────────────────────────────────────────────────────┐
│                         VS Code Window                                 │
│  ┌───────────────────────┐    ┌────────────────────────────────────┐  │
│  │   Zoo Code (LLM)      │    │  VibeZoo Extension                  │  │
│  │  • LLM Reasoning      │    │  ┌──────────────────────────────┐  │  │
│  │  • Built-in Crow      │    │  │ Phase 0: Foundation           │  │  │
│  │    (localhost:9020)   │    │  │ Wave 1: Flow Keepers          │  │  │
│  │  • MCP Client         │    │  │ Wave 2: Safety Net            │  │  │
│  │  • @mention Chat      │    │  │ Wave 3: Context Intel         │  │  │
│  └───────────┬───────────┘    │  │ Wave 4: Orchestra             │  │  │
│              │ MCP/SSE        │  │ Wave 5: Visual Vibe           │  │  │
│              │                │  │ Wave 7: Error Collect         │  │  │
│              │                │  └──────────────────────────────┘  │  │
│              │                │  • Guard.git (Safety)               │  │
│              │                │  • StatusBar / TreeView             │  │
│              │                │  • Visual Panels (Webview)          │  │
│              │                │  • PythonResolver / McpConfigService│  │
│              │                │  • SelfCheck + Auto-Recovery        │  │
│  └───────────┼────────────────┴────────────────────────────────────┘  │
└──────────────┼───────────────────────────────────────────────────────┘
               │  MCP/SSE — `.roo/mcp.json` (always synced)
               ▼
┌───────────────────────────────────────────────────────────────────────┐
│                         VibeZoo Extension Host                         │
│  ┌──────────────────────────────┐    ┌──────────────────────────────┐ │
│  │   PythonResolver             │    │   McpConfigService            │ │
│  │   (6-step discovery chain)   │    │   (project-level MCP config)  │ │
│  └──────────────┬───────────────┘    └──────────────┬───────────────┘ │
│                 │                                    │                 │
│  ┌──────────────▼───────────────┐    ┌──────────────▼───────────────┐ │
│  │   SubagentManager            │    │   VscodePaths                 │ │
│  │   spawnBridge()              │    │   (cross-platform paths)      │ │
│  │   /health polling            │    └──────────────────────────────┘ │
│  └──────────────┬───────────────┘                                     │
└─────────────────┼─────────────────────────────────────────────────────┘
                  │ child_process.spawn
                  ▼
┌─────────────────────────────┐  ┌─────────────────────────────────┐
│ Crow Memory (9020)          │  │ VibeZoo MCP Bridge (9027)       │
│ • Real Crow (proxy mode)    │  │ • 37+ MCP Tools                │
│ • Local in-memory fallback  │  │ • AST Engine (tree-sitter)     │
│ • /health, /ingest, /recall │  │ • Search Engine (rg→git→walk)  │
│                             │  │ • OCR Engine (Tesseract/Paddle)│
│                             │  │ • Vision AI (MiniCPM-V GGUF)   │
│                             │  │ • Error Registry               │
│                             │  │ • Intent Detector (Crow-Aware)  │
│                             │  │ • Fix Loop 상태 머신            │
└─────────────────────────────┘  └─────────────────────────────────┘
```

### 3.0 Auto-Connect Flow (v0.15.0)

확장이 활성화되면 다음 순서로 자동 연결이 진행됩니다:

1. **[`extension/src/extension.ts`](extension/src/extension.ts:55)** [`activate()`](extension/src/extension.ts:55) 시작
2. **[`CrowServerManager.reconnect()`](extension/src/crow/CrowServerManager.ts:130)** — 9020번 포트로 health check 후 실패 시 [`PythonResolver`](extension/src/python/PythonResolver.ts:27)로 [`crow_memory_server.py`](extension/mcp-servers/crow_memory_server.py:208) spawn
3. **[`SubagentManager.spawnBridge()`](extension/src/orchestra/SubagentManager.ts)** — PythonResolver로 Python interpreter를 탐색해 [`extension/mcp-servers/vibezoo_mcp_bridge.py`](extension/mcp-servers/vibezoo_mcp_bridge.py) 실행
4. **[`McpConfigService.writeProjectMcp()`](extension/src/mcp/McpConfigService.ts:47)** — Bridge 성공/실패와 무관하게 `.roo/mcp.json`에 `mcpServers.vibezoo` 강제 기록
5. **[`SelfChecker.runAll()`](extension/src/safety/SelfCheck.ts:132)** — 5초 후 백그라운드로 진단 실행, 실패 시 [`autoRecover()`](extension/src/safety/SelfCheck.ts:486)로 Bridge/MCP 자동 복구

> **핵심 원칙**: global MCP 설정은 **읽기 전용 참고**일 뿐이며, 프로젝트 레벨 `.roo/mcp.json`이 항상 최신 상태를 유지합니다.

### 3.1 레이어 구성

| 레이어 | 디렉토리 | 책임 |
|--------|---------|------|
| **Layer 1** | [`extension/src/`](extension/src/) | VS Code Extension — UI, Safety, Flow, Orchestra, Visual |
| **Layer 2** | [`mcp-servers/bridge/`](mcp-servers/bridge/) | Python MCP Bridge — 37+ 도구, AST, 검색, OCR, 비전, 에러 핸들링 |
| **Layer 3** | Crow Memory (외부) | 시냅틱 메모리 서버 — Hebbian EMA, 8 Registers, `crow.bin` |

### 3.2 Crow Memory의 8 Registers

| 도메인 | 레지스터 |
|--------|---------|
| Code Domain | `style`, `bug`, `arch`, `context` |
| Life Domain | `life_pref`, `life_avoid`, `life_phil`, `life_context` |

---

## 4. 진입점

### 4.1 VS Code Extension

| 파일 | 역할 | 핵심 심볼 |
|------|------|----------|
| [`extension/src/extension.ts`](extension/src/extension.ts:1) | 확장 메인 진입점 | [`activate()`](extension/src/extension.ts:55), [`deactivate()`](extension/src/extension.ts:638), [`autoConfigureMCP()`](extension/src/extension.ts:718), [`ensureTemplates()`](extension/src/extension.ts:725), `setRestartBridgeFn` |
| [`extension/src/python/PythonResolver.ts`](extension/src/python/PythonResolver.ts:1) | Python interpreter 탐색/검증 | [`PythonResolver.resolve()`](extension/src/python/PythonResolver.ts:61) (6-step chain) |
| [`extension/src/platform/VscodePaths.ts`](extension/src/platform/VscodePaths.ts:1) | 크로스 플랫폼 VS Code 경로 | [`getCodeUserPath()`](extension/src/platform/VscodePaths.ts:51), [`getGlobalMcpSettingsPath()`](extension/src/platform/VscodePaths.ts:102) |
| [`extension/src/mcp/McpConfigService.ts`](extension/src/mcp/McpConfigService.ts:1) | 프로젝트/글로벌 MCP 설정 동기화 | [`writeProjectMcp()`](extension/src/mcp/McpConfigService.ts:47), [`readGlobalMcp()`](extension/src/mcp/McpConfigService.ts:24) |
| [`extension/package.json`](extension/package.json:1) | 확장 매니페스트 | 29개 명령어, 27개 설정, 3개 TreeView, 3개 키바인딩 |
| [`extension/tsconfig.json`](extension/tsconfig.json:1) | TypeScript 설정 | `strict`, ES2022, CommonJS |

### 4.2 MCP Bridge Server

| 파일 | 역할 | 핵심 심볼 |
|------|------|----------|
| [`extension/mcp-servers/vibezoo_mcp_bridge.py`](extension/mcp-servers/vibezoo_mcp_bridge.py:1) | FastMCP SSE 서버 (port 9027) | `/health` GET, `/tools/list_subagents` POST, `bridge/tools/` 모듈 등록 |
| [`extension/mcp-servers/crow_memory_server.py`](extension/mcp-servers/crow_memory_server.py:1) | REAL HTTP Crow Memory fallback 서버 (port 9020) | [`run_server()`](extension/mcp-servers/crow_memory_server.py:208), Proxy/Local 모드 |

### 4.3 부트스트랩 / 실행 스크립트

| 파일 | OS | 설명 |
|------|----|------|
| [`init_vibezoo.bat`](init_vibezoo.bat:1) | Windows | venv 생성 → pip install → npm install → tsc |
| [`init_vibezoo.sh`](init_vibezoo.sh:1) | Linux/macOS | 위와 동일한 Linux/macOS 부트스트래퍼 |
| [`start_vibezoo_servers.bat`](start_vibezoo_servers.bat:1) | Windows | Crow Memory(9020) + VibeZoo Bridge(9027) 자동 실행 + Health Check |
| [`start_vibezoo_bridge.bat`](start_vibezoo_bridge.bat:1) | Windows | VibeZoo Bridge 단독 실행 (`%USERPROFILE%\mcp-servers\vibezoo\`에서 실행) |
| [`watch_vibezoo_bridge.bat`](watch_vibezoo_bridge.bat:1) | Windows | 30초 간격 watchdog — bridge 헬스체크 및 자동 재시작 |

---

## 5. 데이터 흐름

### 5.1 흐름 1: LLM ↔ MCP Bridge (사용자 액션)

```text
사용자(LM Studio/Zoo Code)
  │
  ├─ @mention 파싱 ──→ MentionRouter (extension/src/orchestra/MentionRouter.ts:21)
  │
  ├─ MCP/SSE ──→ VibeZoo MCP Bridge (port 9027)
  │                  │
  │                  ├─ tools/__init__.py (자동 에러 캡처 데코레이터)
  │                  ├─ error_handler.py → ErrorRegistry (~/.vibezoo-errors/registry.json)
  │                  ├─ ast_engine.py (tree-sitter AST 파싱)
  │                  ├─ search_engine.py (rg→git grep→walk)
  │                  ├─ intent_detector.py (키워드 + Crow 바이어스)
  │                  └─ crow_client.py → Crow Memory REST API (port 9020)
  │
  └─ VS Code Extension ──→ SubagentManager (extension/src/orchestra/SubagentManager.ts:15)
                              │
                              ├─ spawnBridge() → Python 프로세스 spawn
                              ├─ killBridgeOnPort() → 구버전 종료
                              └─ waitForReady() → health check 폴링
```

### 5.2 흐름 2: Build Feedback

```text
사용자가 파일 저장
  → YoctoManager.executeDirectBackup() (extension/src/safety/YoctoManager.ts:222)
    → onWillSaveTextDocument 이벤트
      → createSnapshot('pre-edit') + atomicCopyFile
        → ~/.zoo-code/yocto/{sessionId}/{snapshotId}/ 에 백업
  → BuildFeedback (extension/src/flow/BuildFeedback.ts:9)
    → onDidEndTaskProcess 이벤트
      → collectDiagnostics() (LSP)
        → FixLoopManager.onBuildFailure() (extension/src/orchestra/FixLoopManager.ts:116)
          → writeFixRequest() (~/.vibezoo-fix-request.json)
            → LLM이 MCP 도구(auto_fix_status, retry_build)로 응답
              → I_instability 계산 → GuardMode 결정
```

### 5.3 흐름 3: Dropzone File Upload

```text
사용자 드래그앤드롭 / Ctrl+V
  → Dropzone Webview (VisualVibePanels.ts:963, Fabric.js)
    → postMessage({ type: 'uploadFile' | 'uploadLocalFile' })
      → handleDropzoneUpload() / handleLocalFileDrop()
        → ~/.vibezoo-uploads/{date}/ 파일 저장
          → 클립보드에 LLM 프롬프트 복사
            → 사용자가 LLM 채팅에 붙여넣기
              → LLM이 MCP 도구(analyze_uploaded_file) 호출
                → file_analyzer.py → SSA/OCR/MiniCPM-V 파이프라인
```

---

## 6. 모듈 맵

### 6.1 Layer 1 — VS Code Extension (`extension/src/`)

| 모듈 | 파일 | 책임 |
|------|------|------|
| **Config** | [`config/ConfigService.ts`](extension/src/config/ConfigService.ts:3) | 중앙 설정 조회 (Host, Port, Guard, 각종 토글) |
| **MCP Config** | [`mcp/McpConfigService.ts`](extension/src/mcp/McpConfigService.ts:1) | 프로젝트 `.roo/mcp.json` 강제 동기화, global MCP 설정 읽기 전용 참고 |
| **Python** | [`python/PythonResolver.ts`](extension/src/python/PythonResolver.ts:1) | 6단계 Python interpreter discovery chain (`setting` → `venv` → `pyenv` → `python3` → `python` → `py -3`) |
| **Platform** | [`platform/VscodePaths.ts`](extension/src/platform/VscodePaths.ts:1) | 크로스 플랫폼 VS Code 사용자/글로벌 설정 경로 계산 |
| **Context** | [`context/ContextIntelligence.ts`](extension/src/context/ContextIntelligence.ts:1) | ContextIndicator, ExplainLessSuggestor, SessionResume, EmotionalDetector |
| **Crow** | [`crow/CrowServerManager.ts`](extension/src/crow/CrowServerManager.ts:11) | Crow Memory 연결 감지, healthCheck, 자동 spawn |
| **Flow** | [`flow/BuildFeedback.ts`](extension/src/flow/BuildFeedback.ts:9) | `onDidEndTaskProcess` 구독 → 자동 빌드 피드백 |
| | [`flow/BuildTaskProvider.ts`](extension/src/flow/BuildTaskProvider.ts:31) | Silent Build Task Provider (Node/Rust/Go 등) |
| | [`flow/ErrorCollection.ts`](extension/src/flow/ErrorCollection.ts:30) | `registry.json` 폴링 (5초), Critical 알림 |
| | [`flow/ProjectDetector.ts`](extension/src/flow/ProjectDetector.ts:22) | 워크스페이스 타입 감지 + 모드 제안 |
| | [`flow/ProjectTreeScanner.ts`](extension/src/flow/ProjectTreeScanner.ts:8) | Async Generator 기반 트리 스캔 + 30초 TTL 캐시 |
| **Orchestra** | [`orchestra/SubagentManager.ts`](extension/src/orchestra/SubagentManager.ts:15) | MCP Bridge spawn/terminate + health check |
| | [`orchestra/MentionRouter.ts`](extension/src/orchestra/MentionRouter.ts:13) | @mention 파싱 + Chat Participant 등록 |
| | [`orchestra/FixLoopManager.ts`](extension/src/orchestra/FixLoopManager.ts:92) | 상태 머신 (idle→pending→in_progress→building→resolved), `I_instability` 계산, CIM 감시 |
| **Safety** | [`safety/GuardGitManager.ts`](extension/src/safety/GuardGitManager.ts:28) | `.git` 디렉토리 OS ACL 보호 (멀티루트, Worktree, Rename 탐지) |
| | [`safety/GuardGitACL.ts`](extension/src/safety/GuardGitACL.ts:107) | OS 추상화 계층 (icacls/chattr/chmod +a), `execFileSafe()` |
| | [`safety/GitStashManager.ts`](extension/src/safety/GitStashManager.ts:13) | YOLO 진입/퇴장 시 Git stash 자동 관리 |
| | [`safety/YoctoManager.ts`](extension/src/safety/YoctoManager.ts:13) | 경량 스냅샷 시스템 (`onWillSaveTextDocument`, 200ms debounce, Instant Rewind) |
| | [`safety/SelfCheck.ts`](extension/src/safety/SelfCheck.ts:106) | 시스템 자가진단 (8개 체크 항목, AlarmMonitor) |
| | [`safety/AutoBuildFix.ts`](extension/src/safety/AutoBuildFix.ts:23) | STUB — LLM-driven MCP 도구로 대체 |
| **UI** | [`ui/StatusBarManager.ts`](extension/src/ui/StatusBarManager.ts:100) | StatusBar 통합 (VibeZoo/Crow/YOLO/CIM/Guard/에러 카운트) |
| | [`ui/TreeViewProviders.ts`](extension/src/ui/TreeViewProviders.ts:29) | 3개 TreeView (ActiveSubagents, YOLO History, Session Resume) |
| **Visual** | [`visual/VisualVibePanels.ts`](extension/src/visual/VisualVibePanels.ts:86) | Whiteboard(Fabric.js) + UI Preview + Diagram(Mermaid) + Dropzone Webview |
| | [`visual/ErrorDashboard.ts`](extension/src/visual/ErrorDashboard.ts:12) | `registry.json` 감시 → Webview 대시보드 |
| **Types** | [`types/index.ts`](extension/src/types/index.ts:1) | 공통 타입 정의 (CrowServerConfig, BuildResult, SubagentNode, GuardGit 등) |

### 6.2 Layer 2 — Python MCP Bridge (`mcp-servers/bridge/`)

| 모듈 | 파일 | 책임 |
|------|------|------|
| **Config** | [`config.py`](mcp-servers/bridge/config.py:1) | 버전, URL, 파일 경로, 확장자 필터, 캐시 설정 |
| **Crow Client** | [`crow_client.py`](mcp-servers/bridge/crow_client.py:1) | REST API 클라이언트 (`try_crow_ingest`, `try_crow_recall`, `crow_health_check`) |
| **AST Engine** | [`ast_engine.py`](mcp-servers/bridge/ast_engine.py:16) | 멀티랭귀지 tree-sitter 파서 (TS/JS/Python/Go/Rust/C/C++), regex 폴백 |
| **Search Engine** | [`search_engine.py`](mcp-servers/bridge/search_engine.py:21) | 3단계 검색 (rg → git grep → os.walk) |
| **OCR Engine** | [`ocr_engine.py`](mcp-servers/bridge/ocr_engine.py:70) | Tesseract 우선, PaddleOCR 폴백, AdaptiveThresholding 전처리 |
| **Intent Detector** | [`intent_detector.py`](mcp-servers/bridge/intent_detector.py:1) | 키워드 기반 의도 분류 + Crow Memory 바이어스 + Dropzone 시간 바인딩 |
| **Error Handler** | [`error_handler.py`](mcp-servers/bridge/error_handler.py:1) | 전역 에러 캡처 데코레이터, ErrorRegistry (JSON+DCLP 싱글톤) |
| **Auto Fixer** | [`auto_fixer.py`](mcp-servers/bridge/auto_fixer.py) | 알려진 에러 패턴 DB + fix 제안 생성 |
| **File Cache** | [`file_cache.py`](mcp-servers/bridge/file_cache.py) | L1 메모리 캐시 |
| **LLM Pipeline** | [`llm_pipeline.py`](mcp-servers/bridge/llm_pipeline.py) | LLM 호출 파이프라인 |
| **Result Ranker** | [`result_ranker.py`](mcp-servers/bridge/result_ranker.py) | 검색 결과 랭킹 |
| **Tool Context** | [`tool_context.py`](mcp-servers/bridge/tool_context.py) | 도구 실행 컨텍스트 관리 |
| **Utils** | [`utils.py`](mcp-servers/bridge/utils.py) | 공통 유틸리티 |
| **Vision** | [`vision/minicpm.py`](mcp-servers/bridge/vision/minicpm.py:1) | MiniCPM-V GGUF 래퍼 (`llama-cpp-python`) |
| **Tools** | [`tools/`](mcp-servers/bridge/tools/__init__.py:1) | 16개 파일, 37+ MCP 도구 등록 |

### 6.3 디렉토리 트리

```text
extension/src/
├── extension.ts
├── config/
│   └── ConfigService.ts
├── context/
│   └── ContextIntelligence.ts
├── crow/
│   └── CrowServerManager.ts
├── flow/
│   ├── BuildFeedback.ts
│   ├── BuildTaskProvider.ts
│   ├── ErrorCollection.ts
│   ├── ProjectDetector.ts
│   └── ProjectTreeScanner.ts
├── mcp/
│   └── McpConfigService.ts
├── orchestra/
│   ├── FixLoopManager.ts
│   ├── MentionRouter.ts
│   └── SubagentManager.ts
├── platform/
│   └── VscodePaths.ts
├── python/
│   └── PythonResolver.ts
├── safety/
│   ├── AutoBuildFix.ts
│   ├── GitStashManager.ts
│   ├── GuardGitACL.ts
│   ├── GuardGitManager.ts
│   ├── SelfCheck.ts
│   └── YoctoManager.ts
├── types/
│   └── index.ts
├── ui/
│   ├── StatusBarManager.ts
│   └── TreeViewProviders.ts
└── visual/
    ├── ErrorDashboard.ts
    └── VisualVibePanels.ts

extension/mcp-servers/
├── crow_memory_server.py
├── vibezoo_mcp_bridge.py
└── bridge/

mcp-servers/bridge/ (legacy mirror)
├── __init__.py
├── config.py
├── crow_client.py
├── ast_engine.py
├── auto_fixer.py
├── error_handler.py
├── file_cache.py
├── intent_detector.py
├── llm_pipeline.py
├── ocr_engine.py
├── result_ranker.py
├── search_engine.py
├── tool_context.py
├── utils.py
├── tools/
│   ├── __init__.py
│   ├── _base.py
│   ├── analysis.py
│   ├── deep_analyzer.py
│   ├── editor.py
│   ├── feedback.py
│   ├── file_analyzer.py
│   ├── fix_loop.py
│   ├── github_diver.py
│   ├── integrated.py
│   ├── knowledge.py
│   ├── reviewer.py
│   ├── scout.py
│   ├── setup.py
│   ├── ssa.py
│   ├── tester.py
│   ├── ux_coordinator.py
│   ├── web.py
│   └── whiteboard.py
└── vision/
    └── minicpm.py
```

---

## 7. 통신 구조

### 7.1 VS Code Extension ↔ Python MCP Bridge

| 방식 | 포트 | 프로토콜/용도 |
|------|------|--------------|
| `child_process.spawn` | — | 프로세스 생명주기 관리 (시작/종료/health check) |
| JSON 파일 IPC | — | 비동기 명령 전달 (whiteboard, dropzone, fix request) |
| HTTP fetch | 9027 | `/health` 헬스체크 [`SubagentManager.ts:199`](extension/src/orchestra/SubagentManager.ts:199) |
| HTTP fetch | 9027 | `/tools/list_subagents` 에이전트 상태 폴링 [`TreeViewProviders.ts:91`](extension/src/ui/TreeViewProviders.ts:91) |

### 7.2 Zoo Code (LLM) ↔ VibeZoo MCP Bridge

| 방식 | 포트 | 프로토콜/용도 |
|------|------|--------------|
| MCP/SSE | 9027 | `http://{host}:{port}/sse` — 모든 MCP 도구 호출 |
| `.roo/mcp.json` | — | Zoo Code 자동 설정 ([`McpConfigService.writeProjectMcp()`](extension/src/mcp/McpConfigService.ts:47)) |
| Global MCP (`mcp_settings.json`) | — | 읽기 전용 참고; 절대 수정하지 않음 |

### 7.3 VibeZoo Bridge ↔ Crow Memory

| 방식 | 포트 | 엔드포인트 | 설명 |
|------|------|-----------|------|
| HTTP REST | 9020 | `GET /health` | 헬스체크 |
| HTTP REST | 9020 | `POST /ingest` | 메모리 저장 (에러, 컨텍스트) |
| HTTP REST | 9020 | `GET /recall` | 메모리 검색 (유사 패턴, 컨텍스트) |

Crow Memory URL은 환경 변수 `CROW_SERVER_URL` (기본: `http://localhost:9020`)로 설정됩니다 ([`config.py:13`](mcp-servers/bridge/config.py:13)).

### 7.4 JSON 파일 IPC 경로

VibeZoo Extension과 Python Bridge/MCP 도구 간의 비동기 통신은 **파일 기반 IPC**를 사용합니다.

| 파일 경로 | 용도 |
|-----------|------|
| `~/.vibezoo-whiteboard.json` | AI 드로잉 명령 |
| `~/.vibezoo-whiteboard-action.json` | Whiteboard open/close |
| `~/.vibezoo-ui-action.json` | UI Preview 렌더링 명령 |
| `~/.vibezoo-dropzone-action.json` | Dropzone open |
| `~/.vibezoo-fix-request.json` | Fix Loop 상태 (LLM 읽음) |
| `~/.vibezoo-errors/registry.json` | 에러 레지스트리 (Dashboard 읽음) |
| `~/.vibezoo-chat-pending.json` | 채팅 펜딩 메시지 |

---

## 8. MCP 도구 카탈로그

VibeZoo MCP Bridge는 37개 이상의 MCP 도구를 16개 파일로 모듈화하여 제공합니다.

| 카테고리 | 파일 | 도구 | 설명 |
|----------|------|------|------|
| Setup | [`tools/setup.py`](mcp-servers/bridge/tools/setup.py) | `vibezoo_setup` | 의존성 설치 및 MCP/Zoo 설정 자동화 |
| Scout | [`tools/scout.py`](mcp-servers/bridge/tools/scout.py) | `search_codebase`, `find_references`, `summarize_architecture` | 코드 검색 및 탐색 |
| Reviewer | [`tools/reviewer.py`](mcp-servers/bridge/tools/reviewer.py) | `review_code` | 코드 품질 검사 (ESLint, go vet 연동) |
| Tester | [`tools/tester.py`](mcp-servers/bridge/tools/tester.py) | `generate_tests`, `analyze_coverage` | 테스트 생성 및 커버리지 분석 |
| Deep Analyzer | [`tools/deep_analyzer.py`](mcp-servers/bridge/tools/deep_analyzer.py) | `analyze_call_graph`, `map_dependencies`, `extract_patterns`, `reverse_engineer` | 깊은 AST 분석 |
| File Analyzer | [`tools/file_analyzer.py`](mcp-servers/bridge/tools/file_analyzer.py) | `analyze_uploaded_file` | 업로드 파일 분석 (목록 확인 및 SSA/OCR/Vision 지원) |
| Whiteboard | [`tools/whiteboard.py`](mcp-servers/bridge/tools/whiteboard.py) | `draw_on_whiteboard`, `get_whiteboard_state`, `capture_screen` | AI-Human 시각 협업 |
| Fix Loop | [`tools/fix_loop.py`](mcp-servers/bridge/tools/fix_loop.py) | `auto_fix_status`, `retry_build`, `check_intervention` | 자율 빌드 픽스 루프 |
| Integrated | [`tools/integrated.py`](mcp-servers/bridge/tools/integrated.py) | `review_project`, `find_bugs`, `suggest_refactor`, `generate_docs` | 통합 시나리오 도구 |
| Analysis | [`tools/analysis.py`](mcp-servers/bridge/tools/analysis.py) | `explain_code`, `analyze_changes`, `review_pr`, `refactor_across_files` | 코드 설명 및 diff 분석 |
| Knowledge | [`tools/knowledge.py`](mcp-servers/bridge/tools/knowledge.py) | `learn_project`, `recall_project`, `learn_preference`, `get_preferences` | 프로젝트/사용자 지식 메모리 |
| Web | [`tools/web.py`](mcp-servers/bridge/tools/web.py) | `fetch_page`, `web_search` | 웹 검색 및 페이지 분석 |
| SSA | [`tools/ssa.py`](mcp-servers/bridge/tools/ssa.py) | `aggregate_spatial_pixels` | 공간 통계 분석 |
| Editor | [`tools/editor.py`](mcp-servers/bridge/tools/editor.py) | `apply_patch`, `read_project_file` | AI-안전 파일 편집 |
| UX Coordinator | [`tools/ux_coordinator.py`](mcp-servers/bridge/tools/ux_coordinator.py) | `ux_coordinator`, `auto_analyze_after_drop`, `auto_analyze_whiteboard` | 의도 감지 및 자동 도구 체인 |
| Feedback | [`tools/feedback.py`](mcp-servers/bridge/tools/feedback.py) | `vibezoo_feedback` | 피드백/텔레메트리 기록 |

### 8.1 주요 도구 하이라이트

- **[`apply_patch`](mcp-servers/bridge/tools/editor.py)**
  - `path` optional — diff 내용에서 타겟 파일 자동 감지
  - Fuzzy matching — 최대 85% 유사도 자동 보정
  - AST-Guided Smart Ellipsis — `// ...` 등의 placeholder 처리
  - Transactional Apply — dry-run 후 atomic commit, 실패 시 롤백
  - Auto backup — `~/.vibezoo-backup/`에 사전 백업

- **`ux_coordinator`**
  - Crow Memory-aware 의도 분석
  - 의도: `file_share`, `drawing_request`, `code_analysis`, `project_setup`, `fix_loop`

- **`search_codebase`**
  - `target_path` 파라미터로 특정 디렉토리 검색 가능
  - ripgrep 기반, invalid regex 시 substring 폴백

---

## 9. 주요 패턴 및 컨벤션

### 9.1 Extension → Python Bridge via `child_process.spawn`

[`SubagentManager.ts:95`](extension/src/orchestra/SubagentManager.ts:95)에서 Python MCP Bridge를 `spawn('python', [bridgeScript, '--port', port])`로 실행합니다. `detached: true` + `unref()`로 백그라운드 실행되며, VS Code 재시작 시 포트 충돌을 방지하기 위해 [`killBridgeOnPort()`](extension/src/orchestra/SubagentManager.ts:146)로 구버전 프로세스를 먼저 종료합니다.

### 9.2 JSON 파일 IPC (Inter-Process Communication)

Extension과 Python Bridge/MCP 도구 간의 비동기 통신은 **파일 기반 IPC**를 사용합니다. 주요 파일은 [7.4 JSON 파일 IPC 경로](#74-json-파일-ipc-경로)를 참조하세요.

### 9.3 Selection-Over-Fallback (계층적 폴백)

| 영역 | 폴백 체인 |
|------|----------|
| 검색 | ripgrep → git grep → os.walk ([`search_engine.py:73-78`](mcp-servers/bridge/search_engine.py:73)) |
| AST | tree_sitter_languages → 개별 tree-sitter 패키지 → regex ([`ast_engine.py:127-166`](mcp-servers/bridge/ast_engine.py:127)) |
| OCR | Tesseract → PaddleOCR → 비활성화 ([`ocr_engine.py:203-218`](mcp-servers/bridge/ocr_engine.py:203)) |
| 세션 복원 | Crow Memory → 로컬 파일 → YOLO yocto 디렉토리 ([`ContextIntelligence.ts:80-140`](extension/src/context/ContextIntelligence.ts:80)) |

### 9.4 Event-Driven Architecture (VS Code Events)

| 이벤트 | 핸들러 | 결과 |
|--------|--------|------|
| `onDidEndTaskProcess` | [`BuildFeedback.ts:10`](extension/src/flow/BuildFeedback.ts:10) | 빌드 결과 → FixLoopManager |
| `onWillSaveTextDocument` | [`YoctoManager.ts:33`](extension/src/safety/YoctoManager.ts:33) | 저장 직전 스냅샷 백업 |
| `onDidChangeWorkspaceFolders` | [`GuardGitManager.ts:70`](extension/src/safety/GuardGitManager.ts:70) | 멀티루트 Guard 설정 |
| `fs.watchFile` | [`VisualVibePanels.ts:167`](extension/src/visual/VisualVibePanels.ts:167) | action file 감시 |

### 9.5 Debounce + Stale-While-Revalidate (SWR)

| 대상 | 동작 | 위치 |
|------|------|------|
| 파일 변경 감시 | 1000ms debounce | [`ProjectTreeScanner.ts:28`](extension/src/flow/ProjectTreeScanner.ts:28) |
| Whiteboard canvasState | 300ms debounce | [`VisualVibePanels.ts:637`](extension/src/visual/VisualVibePanels.ts:637) |
| Tree scan | 30초 TTL + stale-while-revalidate | [`ProjectTreeScanner.ts:39-43`](extension/src/flow/ProjectTreeScanner.ts:39) |
| Notification | 3초 동일 메시지 방지 + 분당 10회 제한 | [`StatusBarManager.ts:18-19`](extension/src/ui/StatusBarManager.ts:18) |

### 9.6 Graceful Degradation (Best-Effort Architecture)

- Crow Memory 연결 실패 → 확장 정상 동작 (Crow 없이도 모든 기능 사용 가능)
- MCP Bridge 실패 → VibeZoo는 active 상태 유지 ([`extension.ts:178-179`](extension/src/extension.ts:178))
- 알림 throttle → StatusBar fallback ([`StatusBarManager.ts:62-64`](extension/src/ui/StatusBarManager.ts:62))
- `capture_tool_errors` 데코레이터 → 성공 시 zero-overhead ([`error_handler.py:227`](mcp-servers/bridge/error_handler.py:227))

### 9.7 Thread Safety (Python Bridge)

- `ErrorRegistry`: DCLP 싱글톤 + `threading.Lock` ([`error_handler.py:51-68`](mcp-servers/bridge/error_handler.py:51))
- `ThreadPoolExecutor` (max_workers=4) for 비동기 에러 기록 ([`error_handler.py:29`](mcp-servers/bridge/error_handler.py:29))
- `AstEngine`: `threading.Lock` + DCLP 패턴 ([`ast_engine.py:89`](mcp-servers/bridge/ast_engine.py:89))

### 9.8 Naming Convention

| 언어 | 규칙 |
|------|------|
| TypeScript | 클래스: `PascalCase` (`CrowServerManager`, `GuardGitManager`), 메서드/함수: `camelCase` |
| Python | 함수/변수: `snake_case` (`crow_health_check`, `detect_intent_v2`), 클래스: `PascalCase` |
| 파일/디렉토리 | `kebab-case` (`mcp-servers`, `crow-memory-server.py`) 및 `PascalCase` (`ConfigService.ts`) |
| i18n | `%vibezoo.commandName.title%` 패턴의 localization 키 |

### 9.9 Error Handling Pattern

- **TypeScript**: `try/catch` with `console.warn` + graceful fallback (비치명적 실패는 조용히 넘김)
- **Python**: `try/except Exception` + `logger.debug` (silent failure philosophy)
- 모든 MCP 도구: [`@capture_tool_errors`](mcp-servers/bridge/error_handler.py)로 자동 래핑 → ErrorRegistry 기록 + Crow ingest → 예외 재발생 (LLM으로 전파)
- `I_instability` (불안정성 지수): 동일 에러 반복률 + 편집 횟수 + 빌드 실패로 조기 차단 ([`FixLoopManager.ts:75-78`](extension/src/orchestra/FixLoopManager.ts:75))

### 9.10 Security Patterns

- **Guard.git ACL**: `execFile()` only (no shell), 경로 검증 정규식, timeout 10초 ([`GuardGitACL.ts:55-73`](extension/src/safety/GuardGitACL.ts:55))
- **C1/C2**: sudo 절대 사용 금지, shell injection 방지, 모든 OS 명령어 `execFileSafe()`
- **익명화**: 사용자 홈 경로 → `~`로 마스킹 ([`error_handler.py:34-38`](mcp-servers/bridge/error_handler.py:34))
- **중복 활성화 방지**: `_activeExtensions` Set으로 2회 activate 차단 ([`extension.ts:67`](extension/src/extension.ts:67))

---

## 10. 알려진 이슈 및 병목

| # | 이슈 | 설명 | 위치/근거 |
|---|------|------|----------|
| 1 | **JSON 파일 IPC의 신뢰성 문제** | Extension과 Bridge 간 비동기 통신이 JSON 파일에 전적으로 의존. 파일 락(locking) 메커니즘 부재로 레이스 컨디션 가능성. `fs.watchFile` + mtime 비교로 보완 중이지만 완벽하지 않음. | `~/.vibezoo-*.json` |
| 2 | **Python Bridge 단일 장애점(SPOF)** | 37개 MCP 도구가 단일 Python 프로세스(`vibezoo_mcp_bridge.py`)에서 실행. 장애 시 모든 MCP 기능 마비. | [`mcp-servers/vibezoo_mcp_bridge.py`](mcp-servers/vibezoo_mcp_bridge.py:1) |
| 3 | **Crow Memory FAKE 서버** | [`crow_memory_server.py`](mcp-servers/crow_memory_server.py:1)는 단순 DEPRECATED 출력 후 종료. 실제 Crow 서버는 별도 저장소([vibezoo/crowmemory](https://github.com/vibezoo/crowmemory))에 있으며 의존성 추적이 어려움. | [`mcp-servers/crow_memory_server.py`](mcp-servers/crow_memory_server.py:1) |
| 3-fix | **(해결됨) Crow Memory fallback 서버** | v0.15.0에서 [`extension/mcp-servers/crow_memory_server.py`](extension/mcp-servers/crow_memory_server.py:1)를 실제 HTTP 서버로 교체. 외부 Crow이 있으면 Proxy 모드, 없으면 Local in-memory 모드로 동작하며 `sys.exit(0)` 제거. | [`extension/mcp-servers/crow_memory_server.py`](extension/mcp-servers/crow_memory_server.py:1) |
| 6-fix | **(해결됨) 프로젝트 레벨 MCP 설정 누락** | `autoConfigureMCP()`가 global MCP에 vibezoo가 등록돼 있으면 `.roo/mcp.json` 작성을 생략했던 버그 수정. [`McpConfigService`](extension/src/mcp/McpConfigService.ts:1)로 분리해 global 설정과 무관하게 항상 프로젝트 설정 강제 기록. | [`extension/src/mcp/McpConfigService.ts`](extension/src/mcp/McpConfigService.ts:1) |
| 7-fix | **(해결됨) Python interpreter 탐색 실패** | 다양한 환경(`python`/`python3`/venv/Microsoft Store)에서 Bridge/Crow spawn 실패. [`PythonResolver`](extension/src/python/PythonResolver.ts:1) 도입으로 6단계 체인으로 deterministic하게 결정. | [`extension/src/python/PythonResolver.ts`](extension/src/python/PythonResolver.ts:1) |
| 8-fix | **(해결됨) VSIX에서 Python 브릿지 누락** | `mcp-servers/`가 VSIX에 포함되지 않아 설치된 확장에서 Bridge를 찾지 못함. `mcp-servers/`를 `extension/mcp-servers/`로 이동하고 `.vscodeignore`에서 제외. | [`extension/mcp-servers/`](extension/mcp-servers/) |
| 9-fix | **(해결됨) Cross-platform global MCP 경로 오류** | Windows 외 플랫폼에서 Zoo Code global MCP 설정 경로를 하드코딩했던 문제. [`VscodePaths`](extension/src/platform/VscodePaths.ts:1)로 Stable/Insiders 구분 및 OS별 경로 계산. | [`extension/src/platform/VscodePaths.ts`](extension/src/platform/VscodePaths.ts:1) |
| 4 | **`try/except Exception` 과다 사용** | Python Bridge 전반에 걸친 광범위한 예외 캐치로 디버깅 곤란. `capture_tool_errors`가 완화하지만, `_try_crow_ingest`, `_try_auto_fix` 등에서 무성 실패(silent failure) 발생. | `mcp-servers/bridge/*.py` |
| 5 | **설정 중복** | [`extension/package.json`](extension/package.json:180)의 `contributes.configuration`과 [`ConfigService.ts`](extension/src/config/ConfigService.ts:3)가 동일한 설정을 중복 참조. 새 설정 추가 시 누락 가능성. | [`extension/package.json`](extension/package.json:180), [`ConfigService.ts`](extension/src/config/ConfigService.ts:3) |
| 6 | **문서화 부족** | `mcp-servers/bridge/tools/_base.py`의 인터페이스 설계 문서 불명확. 각 도구별 특수 파라미터에 대한 JSDoc/Google-style docstring 부족. | [`mcp-servers/bridge/tools/_base.py`](mcp-servers/bridge/tools/_base.py) |

---

## 11. 빠른 시작

### 11.1 요구사항

- Python `3.10+`
- Zoo Code (또는 MCP 호환 AI 코딩 에이전트)
- Git
- VS Code `^1.90.0`

### 11.2 초기화

**Windows:**

```powershell
git clone https://github.com/vibezoo/VibeZoo_forZoocode.git
cd VibeZoo_forZoocode
.\init_vibezoo.bat
```

**macOS / Linux:**

```bash
git clone https://github.com/vibezoo/VibeZoo_forZoocode.git
cd VibeZoo_forZoocode
bash init_vibezoo.sh
```

> `init_vibezoo` 스크립트는 venv 생성 → pip install → npm install → `tsc` 컴파일까지 한 번에 수행합니다.

### 11.3 서버 실행

**수동 실행:**

```bash
# VibeZoo MCP Bridge (from standard runtime directory)
cd %USERPROFILE%\mcp-servers\vibezoo
python vibezoo_mcp_bridge.py --port 9027
```

**Windows 자동 실행 (Crow Memory + Bridge):**

```powershell
%USERPROFILE%\mcp-servers\vibezoo\start_vibezoo_servers.bat
```

**Watchdog 실행 (Bridge 모니터링):**

```powershell
%USERPROFILE%\mcp-servers\vibezoo\watch_vibezoo_bridge.bat
```

### 11.4 Zoo Code 연동

`vibezoo_setup` 도구를 실행하면 `.roo/mcp.json`과 `.zoo/config.json`이 자동 구성됩니다.

```text
vibezoo_setup(target="minimal", configure_custom_modes=True)
```

수동 구성 시:

```json
// .roo/mcp.json
{
  "mcpServers": {
    "vibezoo": {
      "url": "http://localhost:9027/sse"
    }
  }
}
```

### 11.5 확장 빌드/패키징

| 스크립트 | 명령 | 설명 |
|----------|------|------|
| `vscode:prepublish` | `npm run compile` | 배포 전 컴파일 |
| `compile` | `tsc -p ./` | TypeScript 컴파일 |
| `watch` | `tsc -watch -p ./` | 개발 watch 모드 |
| `package` | `vsce package` | VSIX 패키징 |
| `lint` | `eslint src --ext ts` | 린팅 |
| `l10n:export` | `npx @vscode/l10n-dev export --outDir ./l10n ./src` | 다국어 추출 |

> 루트 [`package.json`](package.json:1)은 `@vscode/l10n-dev` 개발 의존성만 포함합니다. 실제 확장 스크립트는 [`extension/package.json`](extension/package.json:378)에 정의되어 있습니다.

---

## 12. 주요 의존성

### 12.1 TypeScript (VS Code Extension)

| 패키지 | 버전 | 용도 |
|--------|------|------|
| `@types/vscode` | `^1.90.0` | VS Code Extension API 타입 |
| `typescript` | `^5.3.0` | TypeScript 컴파일러 |
| `@vscode/vsce` | `^2.22.0` | VSIX 패키징 |
| `@vscode/l10n-dev` | `^0.0.35` | 로컬라이제이션 도구 |
| `minimatch` | `^10.2.5` | Glob 패턴 매칭 |
| `eslint` | `^8.0.0` | 린팅 |
| `@types/node` | `^20.0.0` | Node.js API 타입 |

### 12.2 Python (MCP Bridge)

| 패키지 | 용도 |
|--------|------|
| `fastmcp` | FastMCP SSE 서버 프레임워크 |
| `starlette` | HTTP 라우팅 (custom_route) |
| `requests` | Crow Memory REST API 클라이언트 |
| `tree_sitter_languages` | 멀티랭귀지 AST 파싱 |
| `llama-cpp-python` | MiniCPM-V GGUF 추론 |
| `pytesseract` | Tesseract OCR |
| `PaddleOCR` | OCR 폴백 |
| `opencv-python` | 이미지 전처리, SSA |
| `curl_cffi` | 웹 검색 엔진 |
| `selectolax` + `httpx` | HTML 파싱 |

---

## 부록: 참고 리소스

- **VibeZoo 저장소**: <https://github.com/vibezoo/VibeZoo_forZoocode>
- **Crow Memory 저장소**: <https://github.com/vibezoo/crowmemory>
- **후원**: <https://teamsunplaza.gumroad.com/l/vibezoo>
- **문의**: <myk1yt@gmail.com>

---

*VibeZoo v0.15.0 — June 2026*  
*Co-designed by Stefano, Kim & AI*
