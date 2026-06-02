# VibeZoo 코드베이스 버그 및 취약점 진단 리포트

**작성자**: AGY-CLI Orchestrator (feat. `debugger` Agent)
**진단 대상**: VibeZoo Extension 핵심 코어 로직

---

## 🔍 진단 요약
디버그 전문 에이전트가 VibeZoo의 전반적인 구조(Orchestration, Yolo Safety Net, Crow Memory 연동 등)를 스캔한 결과, 설정 파일 무시로 인한 통신 단절, 치명적 메모리 누수, 그리고 대규모 프로젝트 컨텍스트 잘림 등 **총 4건의 심각한(Critical) 논리적/구조적 버그**가 발견되었습니다.

---

## 🐛 주요 버그 상세 분석

### 1. 포트 설정 하드코딩으로 인한 MCP 연결 실패 (Logical Bug)
- **발생 위치**: `extension/src/extension.ts` 내 `autoConfigureMCP()` 함수
- **문제점**: `SubagentManager`는 사용자 설정(`vibezoo.bridge.port`)에 맞춰 브릿지 프로세스를 시작하지만, 실제 VS Code 설정(`.roo/mcp.json`)을 조작하는 `autoConfigureMCP()` 함수 내부에서는 인자를 무시하고 `http://localhost:9027/sse` 경로를 하드코딩해버립니다.
- **영향도 (High)**: 사용자가 브릿지 포트를 다른 번호로 변경할 경우, MCP 도구 호출 시 무조건 9027 포트로 접근하려 하므로 서버 응답 거부(Connection Refused)가 발생하여 도구 연동이 완전히 마비됩니다.

### 2. Crow Memory 환경변수 하드코딩 (Configuration Bug)
- **발생 위치**: `extension/src/orchestra/SubagentManager.ts` 내 `spawnBridge()` 함수
- **문제점**: Python 브릿지를 `spawn`할 때 환경 변수 `CROW_SERVER_URL` 값을 `http://127.0.0.1:9020`으로 강제 고정하여 주입하고 있습니다.
- **영향도 (Medium)**: 상태바 모니터링 모듈(`CrowServerManager`)은 사용자 설정(`vibezoo.crow.port`)을 올바르게 읽어오지만, 정작 코어 브릿지는 항상 9020으로만 통신하려 하므로 설정 변경 시 기억 모듈(Crow Memory)과의 단절이 발생합니다.

### 3. 심각한 메모리 누수 및 Yolo Rewind 논리 결함 (Data/Memory Bug)
- **발생 위치**: `extension/src/safety/YoctoManager.ts`
- **문제점 1 (메모리 누수)**: 파일 저장 시마다 `executeGlobalBackup()`가 호출되는데, 내부 로직이 단일 스냅샷 배열(`latest.files.push(entry)`)에 무한정 메타데이터를 밀어 넣고 있습니다. 세션 장기화 시 심각한 램(RAM) 누수를 유발합니다.
- **문제점 2 (복구 실패)**: 백업 타이밍이 파일 변경(`onDidChange`) **이후**로 잡혀 있어, `instantRewind` 실행 시 파일이 "편집 전"이 아닌 "편집 직후" 상태로 롤백됩니다. 덧붙여, 역순 복원(`reverse()`) 로직의 결함으로 동일 파일 중복 I/O 발생 및 정확한 상태(Undo) 복구가 불가능합니다.
- **영향도 (Critical)**: 안전망을 표방하는 Yocto 기능이 오히려 메모리를 갉아먹고, 가장 중요한 "YOLO 복구" 기능을 수행하지 못해 신뢰성을 크게 떨어뜨립니다.

### 4. 대형 프로젝트 컨텍스트 누락 및 트리 잘림 (Context Bug)
- **발생 위치**: `extension/src/flow/ProjectTreeScanner.ts` 내 `rescan()` 함수
- **문제점**: 프로젝트 트리를 구성하는 `vscode.workspace.findFiles(pattern, excludePattern, 100)` 구문에서 최대 결과값(`maxResults`)이 단 `100`으로 고정되어 있습니다.
- **영향도 (High)**: 파일이 100개가 넘어가는 실제 현업 프로젝트에서는 트리가 중간에 잘려버립니다. LLM이 프로젝트의 전체 파일 구조를 100% 온전하게 파악하지 못하게 만들어, 심각한 컨텍스트 누락(할루시네이션)을 초래합니다.

---

## 🛠 권고 조치 (Next Step)
위 버그들은 VibeZoo의 핵심 철학인 **안정성(YOLO)**과 **유연성(Configuration)**을 직접적으로 훼손하고 있습니다.
`architect` 에이전트를 통해 리팩터링 계획을 수립하고, `coder` 에이전트를 투입하여 순차적으로 코드를 교정(Hotfix)하는 것을 강력히 권장합니다.
