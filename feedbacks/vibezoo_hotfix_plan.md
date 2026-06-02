# VibeZoo 긴급 핫픽스 마스터 플랜 (VibeZoo Hotfix Master Plan)

## 1. 개요 (Overview)
`debugger` 요원의 진단 결과, 최근 추가된 코드에서 프로젝트의 안정성과 사용자 시스템 안전을 심각하게 위협하는 3가지 치명적 결함이 발견되었습니다. 본 마스터 플랜은 이 결함들을 근본적이고 안전하게 해결하기 위한 아키텍처 및 로직 수정 지침을 제공합니다. 

## 2. 결함 분석 및 해결 방안 (Issue Analysis & Solutions)

### 2.1. `FixLoopManager.ts`: 제어 로직 역전 문제
* **문제점**: 불안정성(Instability) 수치가 높을 때 루프를 진행하고, 낮을 때 중단하는 논리적 오류. 이로 인해 불안정한 상태에서 작업이 계속 진행되어 연쇄적인 오류를 유발할 수 있습니다.
* **해결 방안 (Action Item)**: 
  * 루프 제어 조건문 역전 수정: `instability < THRESHOLD` (안정 상태)일 때 작업을 **진행(Continue)**하고, `instability >= THRESHOLD` (불안정 상태)일 때 작업을 **중단(Halt/Break)** 및 복구(Recovery) 로직을 호출하도록 변경합니다.
  * *설계 지침*: 조건 변경 시 경계값(Edge case) 처리를 명확히 하고, 중단 시 적절한 에러 로그와 상태 코드를 반환하도록 설계합니다.

### 2.2. `SubagentManager.ts`: 시스템 위반 (프로세스 강제 종료) 문제
* **문제점**: PID 탐색 실패 시 최후의 수단으로 `taskkill /F /FI "IMAGENAME eq python.exe"` 명령을 실행하여 사용자의 **모든 파이썬 프로세스를 강제 종료**하는 심각한 시스템 침해 행위가 발생합니다.
* **해결 방안 (Action Item)**:
  * 무차별적인 `taskkill` 커맨드라인 실행 코드 전면 삭제.
  * 서브에이전트 프로세스 생성(Spawn) 시 반환되는 ChildProcess 객체를 내부 상태(Memory/State)에 안전하게 캐싱하여 관리합니다.
  * 프로세스 종료 시, 캐싱된 ChildProcess 객체의 `kill()` 메서드(예: `process.kill()`, `tree-kill` 라이브러리 등)를 활용하여 **해당 서브에이전트 및 그 하위 프로세스만 특정하여 안전하게 종료**하도록 아키텍처를 개선합니다.
  * *설계 지침*: PID 탐색이 완전히 실패하더라도 시스템의 다른 프로세스에 간섭하지 않고 Graceful Fallback(경고 로그 출력 및 고립)을 수행해야 합니다.

### 2.3. `SelfCheck.ts`: 사용자 데이터 유실 문제
* **문제점**: `.roo/mcp.json` 파일의 자동 복구 과정에서 기존 설정(타 MCP 서버 정보 등)을 무시하고 전체 파일을 통째로 덮어써서 사용자의 기존 데이터가 완전히 유실됩니다.
* **해결 방안 (Action Item)**:
  * 덮어쓰기(Overwrite) 방식에서 **안전한 병합(Safe Merge) 방식**으로 로직 변경.
  * 구현 단계:
    1. **Read**: `fs.promises.readFile`을 사용해 기존 `.roo/mcp.json` 파일을 읽어옵니다. (파일이 없으면 빈 객체로 초기화)
    2. **Parse**: `JSON.parse()`를 통해 파싱합니다.
    3. **Merge**: 기존 JSON 객체에 VibeZoo 운영에 필요한 필수 설정 노드만 병합(Deep merge 또는 Object.assign)합니다. 기존에 존재하는 다른 MCP 설정값은 건드리지 않습니다.
    4. **Write**: `JSON.stringify(..., null, 2)`를 사용하여 정돈된 포맷으로 안전하게 다시 저장합니다.
  * *설계 지침*: JSON 파싱 중 발생할 수 있는 Syntax Error에 대한 `try-catch` 예외 처리를 반드시 포함하여 무결성을 보장해야 합니다.

## 3. 작업 순서 (Task Sequence)
본 핫픽스는 시스템 안정성에 직결되므로 다음 순서대로 신속하고 정확하게 진행되어야 합니다.

1. **Phase 1: `SubagentManager.ts` 핫픽스 (Critical & Urgent)**
   - 시스템 전체에 영향을 미치는 파이썬 프로세스 킬러 로직 즉시 제거 및 프로세스 객체 기반 종료 로직 적용.
2. **Phase 2: `SelfCheck.ts` 핫픽스 (High)**
   - 사용자 설정 데이터 유실 방지를 위한 파일 읽기/병합 로직 구현 및 예외 처리 추가.
3. **Phase 3: `FixLoopManager.ts` 핫픽스 (High)**
   - 루프 제어 흐름 정상화 (조건문 수정).
4. **Phase 4: 통합 테스트 및 검증 (QA)**
   - 각 수정 사항이 사이드 이펙트 없이 의도대로 동작하는지 확인. (특히 `mcp.json` 병합 테스트 및 서브 프로세스 고립 종료 테스트)

## 4. 기대 효과 (Expected Outcomes)
* 시스템 레벨의 위험 요소(모든 파이썬 프로세스 종료)가 제거되어 사용자의 개발 환경 안전 보장.
* 사용자 커스텀 설정(타 MCP)의 안전한 보존.
* 불안정성 제어 로직 정상화를 통한 VibeZoo 자가 치유 및 구동 안정성 극대화.
