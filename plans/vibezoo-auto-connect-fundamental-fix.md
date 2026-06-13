# VibeZoo 자동 연결 실패 — 근본적 해결책 설계

> 작성 기준: VibeZoo v0.15.0 (extension/ + mcp-servers/)
> 목표: Windows 부팅 → VS Code 실행 → VibeZoo 확장 자동으로 Python MCP Bridge(9027) + Crow Memory(9020) 시작 → Zoo Code가 `.roo/mcp.json`을 통해 자동 SSE 연결

---

## 1. Technical Specification

### 1.1 Goals and core constraints

| ID | Goal | Constraint |
|----|------|------------|
| G1 | VS Code 시작만으로 MCP Bridge가 spawn 됨 | 사용자가 batch/shell 스크립트를 실행하지 않아야 함 |
| G2 | Zoo Code가 자동으로 Bridge에 SSE 연결 | `.roo/mcp.json`이 항상 최신/유효 상태를 유지 |
| G3 | Crow Memory(또는 graceful fallback)가 동작 | `crow_memory_server.py` stub 즉시 종료 금지 |
| G4 | 설치된 VSIX에서도 Python 브릿지를 찾음 | Python 파일이 VSIX 번들에 포함되어야 함 |
| G5 | 다양한 Python 실행 환경 대응 | `python`/`python3`/venv/conda/pyenv/Microsoft Store |
| G6 | Windows 외 macOS/Linux 지원 | MCP 설정 경로가 OS별로 올바르게 결정 |
| G7 | 누락된 설정 키 보완 | `vibezoo.bridge.port`, `vibezoo.network.host`가 `configuration.properties`에 존재 |

### 1.2 Frontend ↔ Backend communication data flow

```
[VS Code Window]
   │ activationEvents: onStartupFinished
   ▼
[extension/src/extension.ts:activate()]
   │ 1. ensureDirectories / ensureTemplates
   │ 2. CrowServerManager 생성
   │ 3. (비동기) crowServer.reconnect() — Crow 연결 선시도
   ▼
[extension/src/orchestra/SubagentManager.ts]
   │ 4. spawnBridge()
   │    ├─ Python resolver로 python command 탐색
   │    ├─ 확장 디렉토리 내 mcp-servers/vibezoo_mcp_bridge.py spawn
   │    ├─ port 점유/구버전 정리
   │    └─ /health 폴링
   ▼
[extension/src/extension.ts]
   │ 5. autoConfigureMCP(port) — .roo/mcp.json 강제 동기화
   │    ├─ global mcp_settings.json은 참고만, 절대 early-return 금지
   │    ├─ OS별 global 경로에서 vibezoo 정의 여부 확인
   │    └─ 프로젝트 .roo/mcp.json에 vibezoo 서버 정의 병합/갱신
   ▼
[.roo/mcp.json]
   │ Zoo Code file watcher가 변경 감지
   ▼
[Zoo Code MCP Client]
   │ SSE transport로 http://{host}:{port}/sse 연결
   ▼
[vibezoo_mcp_bridge.py : FastMCP SSE Server]
   │ 필요 시 Crow Memory(9020)로 proxy/tool 호출
   ▼
[crow_memory_server.py (또는 외부 Crow)]
```

### 1.3 Type definitions

아래 타입들은 `extension/src/types/index.ts`에 추가/확장하여, Frontend(TypeScript) ↔ Backend(Python) 간 계약을 명시합니다.

```ts
// extension/src/types/index.ts (추가)

export interface McpServerDefinition {
  url: string;
  transport: 'sse';
  /** optional: Zoo Code 향후 호환 */
  disabled?: boolean;
  /** optional: autoApprove */
  autoApprove?: string[];
}

export interface McpSettings {
  mcpServers: Record<string, McpServerDefinition>;
}

export interface CrowServerConfig {
  port: number;
  healthCheckIntervalMs: number;
  /** spawn 실패 시 graceful로만 동작할 수 있음 */
  spawnOnFailure?: boolean;
}

export interface PythonCommandCandidate {
  command: string;
  source: 'setting' | 'venv' | 'pyenv' | 'conda' | 'path' | 'fallback';
  /** 검증 결과 */
  version?: string;
}

export interface SpawnResult {
  success: boolean;
  pid?: number;
  port: number;
  error?: string;
  /** 'spawned' | 'reused' | 'failed' */
  status: string;
}
```

### 1.4 Error handling contract

- 모든 spawn/async 경계에서 `try/catch` + `Promise.allSettled` 사용
- 실패는 OutputChannel + `console.warn`/`console.error` 기록
- 사용자에게는 치명적 오류 1회만 알림 (AlarmMonitor throttle 적용)
- `autoConfigureMCP` 실패 시 `SelfChecker.checkMcpConfig()`가 `autoRecoverable=true`로 후속 복구

---

## 2. Architecture Decisions

### 2.1 Design patterns and tech stack

| 영역 | 채택 패턴 | 근거 |
|------|----------|------|
| Bridge spawn | **Singleton lifecycle manager** (`SubagentManager`) | Reload 시 중복 프로세스 방지, 기존 healthy bridge 재사용 |
| Python 탐색 | **Resolver chain + caching** | 다양한 환경에서 deterministic하게 python command 결정 |
| MCP 설정 동기화 | **Project-level single source of truth** | global 설정은 참고만, `.roo/mcp.json`을 항상 overwrite/merge |
| Crow 통합 | **Optional external dependency + graceful degradation** | `crow_memory_server.py` stub 제거, 외부 Crow 서버 연결 시도 + 실패 시 bridge 단독 동작 |
| VSIX 번들링 | ** extension/mcp-servers 이동 + .vscodeignore 수정** | VS Code 확장 표준 구조 준수, `context.extensionPath`로 탐색 단순화 |
| 설정 키 | **package.json `configuration.properties` 보완** | `ConfigService`가 참조하는 키가 모두 UI/설정에 노출 |
| 크로스 플랫폼 | **vscode.env.appRoot + process.platform 분기** | VS Code API 우선, fallback으로 `os.homedir()` + OS별 경로 |

### 2.2 Tech stack / references

- VS Code Extension API: `vscode.ExtensionContext.extensionPath`, `vscode.workspace.getConfiguration`
- VS Code 설정 위치: [Visual Studio Code User and Workspace Settings](https://code.visualstudio.com/docs/getstarted/settings)
  - Windows: `%APPDATA%\Code\User\globalStorage\zoocodeorganization.zoo-code\settings\mcp_settings.json`
  - macOS: `~/Library/Application Support/Code/User/globalStorage/zoocodeorganization.zoo-code/settings/mcp_settings.json`
  - Linux: `~/.config/Code/User/globalStorage/zoocodeorganization.zoo-code/settings/mcp_settings.json`
- Zoo Code MCP: SSE transport over `http://host:port/sse`
- Python: FastMCP + starlette (`fastmcp`, `uvicorn`, `requests`)

### 2.3 Potential risks and edge case handling

| Risk | Edge case | Handling |
|------|-----------|----------|
| R1 | Global MCP에 vibezoo가 등록돼 있으나 포트/URL이 다름 | `.roo/mcp.json`도 강제 동기화; global은 참고만 |
| R2 | `.roo/mcp.json`이 Git tracked이거나 수동 수정 중 | merge 방식으로 `vibezoo` 키만 덮어쓰고 나머지는 보존 |
| R3 | Bridge는 떴지만 Zoo Code file watcher가 놓침 | 설정 변경 시 mtime touch + Zoo Code reload 권장 (문서화) |
| R4 | Python이 PATH에 없음 | 사용자 설정 `vibezoo.advanced.pythonPath` fallback 제공 |
| R5 | Microsoft Store `python`로 spawn 실패 | `python3`, `py`, `python.exe` 순차 시도 |
| R6 | Crow 서버가 외부에 없고 stub만 있음 | stub 제거, bridge 내부에서 `/health` proxy 실패 시에도 bridge tool 응답 유지 |
| R7 | VSIX 패키징 시 mcp-servers 누락 | `.vscodeignore`에서 `mcp-servers/**` 제거, `extension/mcp-servers`로 이동 |
| R8 | Extension reload 시 orphan python 프로세스 | `killBridgeOnPort` + `taskkill`/`kill` 정리 로직 재사용 |
| R9 | 멀티 루트 워크스페이스 | 첫 번째 폴더(root)에만 `.roo/mcp.json` 작성, 추후 확장 가능 |

---

## 3. Implementation Plan (Sub-tasks)

아래 6개 task는 순서에 따라 진행하되, **파일/인터페이스 경계가 명확히 분리**되어 병렬 개발 가능합니다.

---

### Task 1: Python resolver 및 spawn 엔진 분리

**목표**: `python`/`python3`/venv/conda/Microsoft Store 등 다양한 환경에서 deterministic하게 Python interpreter를 찾고, Bridge/Crow spawn 로직을 한 곳에서 관리한다.

**Exact files to create/modify**:
- **Create** `extension/src/python/PythonResolver.ts`
- **Modify** `extension/src/orchestra/SubagentManager.ts`
- **Modify** `extension/src/crow/CrowServerManager.ts`
- **Modify** `extension/src/types/index.ts`

**Implementation prerequisites**:
- `ConfigService.getAdvancedPythonPath()` (Task 6에서 추가)가 필요
- `extension/mcp-servers` 이동 완료 (Task 3) 후 경로 후보 단순화

**Details**:
- `PythonResolver.resolve()`가 아래 우선순위로 command 결정:
  1. `vibezoo.advanced.pythonPath` 설정
  2. 가상환경 탐색: `.venv/Scripts/python.exe`(Win), `.venv/bin/python`(nix), `venv/...`
  3. `pyenv`/`conda`에서 `python`/`python3`
  4. `python3` (macOS/Linux)
  5. `python` (Windows, Microsoft Store 포함)
  6. `py -3` (Windows launcher)
- 각 candidate에 대해 `execSync('${cmd} --version')`으로 검증, 성공한 첫 번째 반환
- 실패 시 `OutputChannel`에 상세 로그

---

### Task 2: Crow Memory 통합 및 graceful degradation

**목표**: `mcp-servers/crow_memory_server.py`의 즉시 종료 stub을 제거하고, 실제 Crow Memory 서버가 있으면 시작하고 없으면 bridge가 단독으로 동작하도록 한다.

**Exact files to create/modify**:
- **Modify** `mcp-servers/crow_memory_server.py` (또는 **Replace**)
- **Modify** `extension/src/crow/CrowServerManager.ts`
- **Modify** `extension/src/config/ConfigService.ts`
- **Modify** `mcp-servers/bridge/crow_client.py`

**Implementation prerequisites**:
- Task 1의 `PythonResolver` 완료
- Task 3의 `extension/mcp-servers` 이동 완료

**Details**:
- `crow_memory_server.py`를 최소한의 in-memory Crow Memory 서버로 교체:
  - FastAPI 또는 Flask 기반 `/health`, `/memories`, `/store` 엔드포인트
  - 또는 기존 외부 Crow 서버(`..\Crow Memory\crow_mcp_server.py`)가 있다면 그것을 spawn
  - **절대 `sys.exit(0)` 금지**
- `CrowServerManager`의 `spawnCrowServer()`가 `PythonResolver` 사용
- Crow 연결 실패 시:
  - `statusBar.setCrowStatus(false)`
  - Bridge의 tool 응답에서 Crow 의존 기능은 빈 결과 또는 적절한 메시지 반환
  - `bridge/crow_client.py`의 `crow_health_check()`가 예외를 삼키고 `False` 반환

---

### Task 3: Python 브릿지 VSIX 번들링

**목표**: `mcp-servers/` 디렉토리를 `extension/mcp-servers/`로 이동시켜 VSIX 패키지에 포함되도록 한다.

**Exact files to create/modify**:
- **Move** `mcp-servers/` → `extension/mcp-servers/`
- **Modify** `extension/.vscodeignore`
- **Modify** `extension/src/orchestra/SubagentManager.ts` (경로 후보 단순화)
- **Modify** `extension/src/crow/CrowServerManager.ts` (경로 후보 단순화)
- **Modify** `extension/src/extension.ts` (조기 spawn 경로)
- **Modify** `extension/package.json` (필요 시 files 배열)

**Implementation prerequisites**:
- 파일 이동 후 `npm run compile` 통과

**Details**:
- `extension/.vscodeignore`에서 `mcp-servers/**` 제외 확인; 현재 `.vscodeignore`는 `src/**`만 무시하므로 이동하면 자동 포함됨
- 기존 후보 경로(../../../mcp-servers) 제거; 단일 신뢰 경로만 사용:
  - `path.join(context.extensionPath, 'mcp-servers', 'vibezoo_mcp_bridge.py')`
- `extension.ts` 상단의 즉시 실행 함수(`trySpawnEarlyBridge`)도 동일 경로 사용
- `mcp-servers/bridge/` 내부 `__init__.py`, `tools/`, `vision/` 등 모두 이동

---

### Task 4: MCP 자동 구성 근본 수정

**목표**: global MCP 설정과 무관하게, 프로젝트 레벨 `.roo/mcp.json`을 항상 최신 상태로 유지한다.

**Exact files to create/modify**:
- **Modify** `extension/src/extension.ts` (`autoConfigureMCP`)
- **Modify** `extension/src/safety/SelfCheck.ts` (`autoConfigureMCP`, `checkMcpConfig`)
- **Create** `extension/src/mcp/McpConfigService.ts`

**Implementation prerequisites**:
- Task 3의 `extension/mcp-servers` 이동 완료
- Task 5의 OS별 경로 유틸 완료

**Details**:
- `autoConfigureMCP(port)`에서 글로벌 설정 존재 여부에 관계없이 **항상** `.roo/mcp.json` 작성
- global 설정은 **읽기 전용**으로 참고하여 사용자가 이미 설정했는지 로깅만 수행
- `McpConfigService`로 분리:
  - `getGlobalMcpPath(): string | null` — OS별
  - `readGlobalMcp(): McpSettings | null`
  - `writeProjectMcp(root: string, definition: McpServerDefinition): void`
  - `mergeProjectMcp(root: string, serverKey: string, definition: McpServerDefinition): void`
- `.roo/mcp.json`은 `mcpServers` 키만 병합; 다른 사용자 정의 서버 보존
- 파일 쓰기 후 `fs.utimesSync`로 mtime 갱신 (Zoo Code watcher 강제 트리거)

---

### Task 5: 크로스 플랫폼 MCP 경로 및 설정 키 보완

**목표**: Windows/macOS/Linux에서 Zoo Code global MCP 설정 경로를 올바르게 찾고, `vibezoo.bridge.port`/`vibezoo.network.host` 설정 키를 package.json에 추가한다.

**Exact files to create/modify**:
- **Create** `extension/src/platform/VscodePaths.ts`
- **Modify** `extension/src/extension.ts` (globalMCPPath 하드코딩 제거)
- **Modify** `extension/src/safety/SelfCheck.ts` (globalMCPPath 사용 부분)
- **Modify** `extension/package.json` (`configuration.properties`)
- **Modify** `extension/l10n/bundle.l10n.json`, `bundle.l10n.ko.json`
- **Modify** `extension/package.nls.json`, `package.nls.ko.json`

**Implementation prerequisites**:
- 없음

**Details**:
- `VscodePaths.ts`:
  - `getCodeUserPath(): string` — `process.platform`별 분기
  - Windows: `%APPDATA%\Code\User`
  - macOS: `~/Library/Application Support/Code/User`
  - Linux: `~/.config/Code/User`
  - `getGlobalMcpSettingsPath(): string` — 위 경로 + `globalStorage/zoocodeorganization.zoo-code/settings/mcp_settings.json`
- `extension/package.json`에 추가:
  ```json
  "vibezoo.bridge.port": { "type": "number", "default": 9027, "description": "%vibezoo.bridge.port.description%" },
  "vibezoo.network.host": { "type": "string", "default": "127.0.0.1", "description": "%vibezoo.network.host.description%" },
  "vibezoo.advanced.pythonPath": { "type": "string", "default": "", "description": "%vibezoo.advanced.pythonPath.description%" }
  ```
- l10n/nls 파일에对应 description 추가

---

### Task 6: 통합 활성화 시퀀스 및 테스트/검증

**목표**: 위 수정사항을 활성화 흐름에 통합하고, SelfCheck/StatusBar에서 올바르게 진단/표시되도록 한다.

**Exact files to create/modify**:
- **Modify** `extension/src/extension.ts` (activate/deactivate 흐름)
- **Modify** `extension/src/ui/StatusBarManager.ts` (Crow/Bridge 상태 표시 강화)
- **Modify** `extension/src/safety/SelfCheck.ts` (Bridge/Crow/MCP 설정 진단 강화)
- **Create** `extension/src/python/__tests__/PythonResolver.test.ts` (선택)

**Implementation prerequisites**:
- Task 1~5 완료

**Details**:
- `activate()` 시퀀스:
  1. `ensureDirectories()` / `ensureTemplates()`
  2. `CrowServerManager` 생성 + 비동기 `reconnect()`
  3. `SubagentManager` 생성 + `spawnBridge()`
  4. Bridge 성공 시 `McpConfigService.writeProjectMcp(...)`
  5. Bridge 실패 시에도 `McpConfigService`는 이전 값으로 write 시도 (시간차 재연결 유도)
  6. 활성화 완료 후 `SelfChecker.runAll()` 백그라운드 실행
- `deactivate()`:
  - Bridge process terminate (기존 로직 유지)
  - Crow server는 외부 관리 가정, VibeZoo가 spawn한 프로세스만 정리
- `StatusBarManager`:
  - Bridge 연결 port 표시
  - Crow 연결 상태 표시
  - 실패 시 tooltip에 마지막 에러 요약
- SelfCheck:
  - `checkMcpConfig()`가 `vibezoo` URL까지 검증
  - `autoRecover()`에서 Bridge 재시작 명령어(`vibezoo.verifyFoundation`) 트리거 또는 `SubagentManager.spawnBridge()` 호출

---

## 4. File change summary

| File | Action | Summary |
|------|--------|---------|
| `extension/mcp-servers/**` | Move from root | VSIX 번들링 및 단일 경로 탐색 |
| `extension/.vscodeignore` | Modify | 이동한 `mcp-servers`가 포함되도록 확인 |
| `extension/src/python/PythonResolver.ts` | Create | Python interpreter 탐색/검증 |
| `extension/src/platform/VscodePaths.ts` | Create | OS별 VS Code 설정 경로 |
| `extension/src/mcp/McpConfigService.ts` | Create | project/global MCP 설정 읽기/쓰기 |
| `extension/src/types/index.ts` | Modify | `McpSettings`, `PythonCommandCandidate`, `SpawnResult` 등 추가 |
| `extension/src/config/ConfigService.ts` | Modify | `getAdvancedPythonPath()` 추가 |
| `extension/src/orchestra/SubagentManager.ts` | Modify | PythonResolver 사용, 경로 단순화 |
| `extension/src/crow/CrowServerManager.ts` | Modify | PythonResolver 사용, graceful degradation |
| `extension/src/extension.ts` | Modify | 활성화 시퀀스, autoConfigureMCP 개선 |
| `extension/src/safety/SelfCheck.ts` | Modify | MCP 복구/진단 강화, global 경로 제거 |
| `extension/src/ui/StatusBarManager.ts` | Modify | 실패 상태 tooltip |
| `extension/package.json` | Modify | `bridge.port`, `network.host`, `advanced.pythonPath` 설정 추가 |
| `extension/package.nls*.json`, `extension/l10n/bundle.l10n*.json` | Modify | 설정 설명 번역 추가 |
| `mcp-servers/crow_memory_server.py` | Replace | stub 제거, 실제 Crow Memory 서버 또는 외부 Crow 시작 |
| `mcp-servers/bridge/crow_client.py` | Modify | Crow 연결 실패 시 graceful fallback |

---

## 5. Verification checklist (for `ask` mode audit)

- [ ] `extension:activate()` 이후 `.roo/mcp.json`에 `mcpServers.vibezoo.url === http://127.0.0.1:9027/sse` 존재
- [ ] global MCP에 vibezoo가 등록돼 있어도 `.roo/mcp.json`이 갱신됨
- [ ] VSIX 패키지(`vsce package`) 내부에 `extension/mcp-servers/vibezoo_mcp_bridge.py` 존재
- [ ] Python이 `python3`로만 존재하는 macOS/Linux에서도 Bridge spawn 성공
- [ ] Crow 서버가 없는 환경에서도 Bridge `/health`가 `200 OK` 반환 (crow=false)
- [ ] `vibezoo.bridge.port`/`vibezoo.network.host` 설정 변경 시 `.roo/mcp.json` URL이 반영됨
- [ ] Windows 외 플랫폼에서 global MCP 경로가 올바르게 계산됨
