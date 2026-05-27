# VibeZoo Autonomous Fix Loop — 설계 문서

> **작성일**: 2026-05-27
> **버전**: v1.0
> **상태**: 설계 단계
> **관련 파일**: `AutoBuildFix.ts`, `BuildFeedback.ts`, `SubagentManager.ts`, `vibezoo_mcp_bridge.py`

---

## 1. 문제 진단

### 1.1 현재 상태

현재 VibeZoo의 `AutoBuildFix`는 다음과 같은 **빈 루프**다:

```
BuildFeedback → 빌드 실패 감지 → AutoBuildFix.run()
                                      ├── exitCode 확인
                                      ├── oscillation 체크
                                      ├── rebuild() 재시도 (그냥 같은 빌드)
                                      └── LLM 호출 없음! 코드 수정 없음!
```

[`AutoBuildFix.ts`](../extension/src/safety/AutoBuildFix.ts:29)의 `run()` 메서드는 `max_attempts=3`까지 rebuild만 반복할 뿐, **에러를 LLM에 전달해서 수정 코드를 받아오는 로직이 전무**하다. 따라서 빌드가 실패하면 영원히 실패한다.

### 1.2 사용자 기대 vs 현실

| 기대 | 현실 |
|:---|:---|
| "한 번 주문하면 계속 순환하면서 버그없이 완전하게" | 도구 상자 (파일 검색, 린트, 백업) |
| 빌드 실패 → AI 분석 → 수정 → 재빌드 → 성공 | 빌드 실패 → 재빌드 → 실패 → 재빌드 → 실패 |
| 자율적인 자기 치유 루프 | 수동으로 하나하나 버그 찾아서 고쳐야 함 |

---

## 2. 핵심 설계 원칙

### 2.1 아키텍처 제약

VibeZoo는 Zoo Code 소스를 수정할 수 없는 **Companion Extension**이다. 따라서:

- Extension은 **LLM을 직접 호출할 수 없다** (API 키 없음)
- 대신 **LLM이 VibeZoo의 도구를 호출**하는 방향으로 통신
- Extension과 LLM 사이의 통신 채널: **파일 시스템** (Whiteboard에서 검증된 패턴)

### 2.2 핵심 인사이트: One Message = Many Fix Attempts

LLM(Zoo Code)은 한 번의 응답 안에서 여러 MCP 도구를 순차적으로 호출할 수 있다:

```
사용자: "빌드 에러 고쳐줘" (1회 메시지)
    │
    ▼
LLM: auto_fix_status() 호출 → 에러 목록 수신
LLM: search_codebase("에러 관련 파일") → 컨텍스트 수집
LLM: review_code("실패한 파일") → 문제 분석
LLM: 파일 수정 (edit tool)
LLM: retry_build() 호출 → 새 빌드 결과 수신
    │
    ├── 성공 → 완료 보고
    └── 실패 → 다시 분석 → 수정 → retry_build() (같은 응답 내에서 반복)
```

이 구조면 **사용자 개입 없이** 한 번의 메시지로 최대 `max_attempts`(기본 3회)까지 자동 순환 가능하다.

---

## 3. 전체 아키텍처

### 3.1 데이터 흐름도

```
┌──────────────────────────────────────────────────────────────────┐
│                        VS Code 창                                  │
│                                                                   │
│  ┌─────────────────────────┐    ┌─────────────────────────────┐  │
│  │     Zoo Code (LLM)      │    │   VibeZoo Extension          │  │
│  │                         │    │                              │  │
│  │  ◄── MCP tool calls ────┼────┤  BuildFeedback              │  │
│  │      auto_fix_status()  │    │  (빌드 실패 감지)            │  │
│  │      retry_build()      │    │        │                     │  │
│  │      search_codebase()  │    │        ▼                     │  │
│  │      review_code()      │    │  FixLoopManager (신규)       │  │
│  │      map_dependencies() │    │  ┌───────────────────────┐   │  │
│  │                         │    │  │ ~/.vibezoo-fix-       │   │  │
│  │  파일 수정 (edit tool)  │    │  │   request.json        │   │  │
│  │      │                  │    │  │   (에러 데이터)        │   │  │
│  │      │                  │    │  ├───────────────────────┤   │  │
│  │      │                  │    │  │ Attempt counter      │   │  │
│  │      │                  │    │  │ Oscillation detector │   │  │
│  │      │                  │    │  │ Max attempt guard    │   │  │
│  │      │                  │    │  └───────────────────────┘   │  │
│  │      │                  │    │        │                     │  │
│  │      │                  │    │        ▼                     │  │
│  │      │                  │    │  StatusBar                   │  │
│  │      │                  │    │  "Auto-Fix: 2/3 시도 중..." │  │
│  └──────┼──────────────────┘    └─────────────────────────────┘  │
│         │                                                        │
└─────────┼────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────┐    ┌──────────────────────┐
│  Crow Memory (9020) │    │  VibeZoo MCP Bridge  │
│  • bug 레지스터     │    │  (9027/sse)          │
│  • 과거 에러 패턴   │    │  • auto_fix_status   │
│  • 수정 이력 학습   │    │  • retry_build       │
└─────────────────────┘    │  • search_codebase   │
                           │  • review_code       │
                           │  • map_dependencies  │
                           └──────────────────────┘
```

### 3.2 구성 요소

| 구성 요소 | 위치 | 역할 |
|:---|:---|:---|
| **FixLoopManager** | `extension/src/orchestra/FixLoopManager.ts` (신규) | 상태 관리, attempt 카운터, oscillation 감지, fix request 파일 읽기/쓰기 |
| **BuildFeedback** | `extension/src/flow/BuildFeedback.ts` (수정) | 빌드 실패 감지 → FixLoopManager에 에러 전달 |
| **AutoBuildFix** | `extension/src/safety/AutoBuildFix.ts` (대체) | 제거. FixLoopManager로 대체 |
| **auto_fix_status** | `vibezoo_mcp_bridge.py` (MCP 도구 추가) | LLM이 현재 fix request 조회 |
| **retry_build** | `vibezoo_mcp_bridge.py` (MCP 도구 추가) | LLM이 빌드 재실행 요청, 결과 반환 |
| **crow_ingest (bug)** | Crow Memory | 과거 에러 패턴 저장 → 학습 |

---

## 4. Fix Request 파일 스펙

### 4.1 `~/.vibezoo-fix-request.json`

```json
{
  "sessionId": "fix_20260527_150300",
  "status": "pending",
  "attempt": 2,
  "maxAttempts": 3,
  "createdAt": 1716796980000,
  "history": [
    {
      "attempt": 1,
      "exitCode": 1,
      "diagnostics": [
        {
          "file": "extension/src/visual/VisualVibePanels.ts",
          "line": 388,
          "column": 30,
          "severity": "error",
          "message": "Type 'string' is not assignable to type 'number'",
          "code": "TS2322",
          "source": "ts"
        }
      ],
      "stderr": "...",
      "fixApplied": null,
      "timestamp": 1716796980000
    }
  ],
  "projectRoot": "/path/to/project"
}
```

### 4.2 상태 머신

```
                    ┌──────────┐
                    │  idle    │ (빌드 성공 상태)
                    └────┬─────┘
                         │ 빌드 실패
                         ▼
                    ┌──────────┐
                    │ pending  │ (LLM 대기 중)
                    └────┬─────┘
                         │ LLM이 auto_fix_status() 호출
                         ▼
              ┌─────────────────────┐
              │   in_progress       │ (LLM이 분석/수정 중)
              └────────┬────────────┘
                       │ LLM이 retry_build() 호출
                       ▼
              ┌─────────────────────┐
              │   building          │ (빌드 실행 중)
              └────────┬────────────┘
                       │
          ┌────────────┼────────────┐
          │ 빌드 성공  │            │ 빌드 실패
          ▼            │            ▼
    ┌──────────┐       │    ┌──────────────┐
    │ resolved │       │    │ attempt < max?│
    └──────────┘       │    └──┬───────┬───┘
                       │       │Yes    │No
                       │       ▼       ▼
                       │  pending  ┌──────────┐
                       │  (재시도) │ give_up  │
                       │           └──────────┘
                       │
                       │ oscillation 감지
                       ▼
                 ┌───────────┐
                 │ abandoned │ (A→B→A 패턴)
                 └───────────┘
```

---

## 5. 신규 MCP 도구

### 5.1 `auto_fix_status()`

```python
@mcp.tool
def auto_fix_status() -> str:
    """현재 진행 중인 Auto-Fix 세션의 상태와 에러 정보를 조회합니다.
    LLM이 빌드 에러를 분석하고 수정을 시작할 때 호출합니다.
    
    Returns:
        JSON: { status, attempt, maxAttempts, diagnostics, history }
    """
    fix_request_file = os.path.join(os.path.expanduser("~"), ".vibezoo-fix-request.json")
    if not os.path.exists(fix_request_file):
        return json.dumps({"status": "idle", "message": "No active fix request"})
    
    with open(fix_request_file) as f:
        data = json.load(f)
    
    # 상태를 in_progress로 변경
    data["status"] = "in_progress"
    with open(fix_request_file, "w") as f:
        json.dump(data, f, indent=2)
    
    return json.dumps(data, indent=2)
```

### 5.2 `retry_build()`

```python
@mcp.tool
def retry_build() -> str:
    """빌드를 재실행하고 결과를 반환합니다.
    LLM이 수정 코드를 적용한 후 빌드 성공 여부를 확인할 때 호출합니다.
    
    Returns:
        JSON: { exitCode, diagnostics, success }
    """
    import subprocess, sys
    
    root = os.getcwd()
    
    # 프로젝트 타입 감지
    pkg_json = Path(root) / "package.json"
    if pkg_json.exists():
        cmd = ["npx.cmd" if sys.platform == "win32" else "npx", "tsc", "--noEmit"]
    else:
        return json.dumps({"exitCode": -1, "diagnostics": [], "success": False, "error": "No build command detected"})
    
    result = subprocess.run(cmd, cwd=root, capture_output=True, text=True, timeout=60)
    
    # 결과를 fix-request 파일에 기록
    fix_request_file = os.path.join(os.path.expanduser("~"), ".vibezoo-fix-request.json")
    # ... update file with new attempt data
    
    return json.dumps({
        "exitCode": result.returncode,
        "stdout": result.stdout[-2000:],
        "stderr": result.stderr[-2000:],
        "success": result.returncode == 0
    }, indent=2)
```

---

## 6. FixLoopManager 클래스 설계

```typescript
// extension/src/orchestra/FixLoopManager.ts

export class FixLoopManager {
  private state: FixLoopState = 'idle';
  private currentSession: FixSession | null = null;
  private fixRequestPath: string;
  private maxAttempts: number;

  constructor() {
    this.fixRequestPath = path.join(os.homedir(), '.vibezoo-fix-request.json');
    this.maxAttempts = vscode.workspace
      .getConfiguration('vibezoo')
      .get('build.autoFixMaxAttempts', 3);
  }

  /** BuildFeedback이 빌드 실패 시 호출 */
  onBuildFailure(diagnostics: Diagnostic[], stderr: string): void {
    // 새 fix 세션 시작 또는 기존 세션에 attempt 추가
    if (!this.currentSession || this.currentSession.status === 'resolved') {
      this.currentSession = this.createSession(diagnostics);
    }
    
    this.currentSession.history.push({
      attempt: this.currentSession.history.length + 1,
      exitCode: 1,
      diagnostics,
      stderr,
      fixApplied: null,
      timestamp: Date.now(),
    });

    this.currentSession.status = 'pending';
    this.writeFixRequest();
    this.updateStatusBar();
  }

  /** LLM이 retry_build로 빌드 성공 보고 시 호출 */
  onBuildSuccess(): void {
    if (this.currentSession) {
      this.currentSession.status = 'resolved';
      this.writeFixRequest();
      this.updateStatusBar(true);
    }
  }

  /** Oscillation 감지 */
  isOscillating(): boolean {
    // A→B→A 패턴: 최근 4회 attempt에서 짝수/홀수 에러 시그니처 비교
    const h = this.currentSession?.history ?? [];
    if (h.length < 4) return false;
    const recent = h.slice(-4);
    const sigs = recent.map(a => this.errorSignature(a.diagnostics));
    return sigs[0] === sigs[2] && sigs[1] === sigs[3];
  }

  /** Give up 조건 */
  shouldGiveUp(): boolean {
    if (!this.currentSession) return false;
    if (this.currentSession.history.length >= this.maxAttempts) return true;
    if (this.isOscillating()) return true;
    return false;
  }

  private errorSignature(diagnostics: Diagnostic[]): string {
    return diagnostics
      .map(d => `${d.file}:${d.code}`)
      .sort()
      .join('|');
  }

  private writeFixRequest(): void { /* JSON 파일 쓰기 */ }
  private updateStatusBar(success = false): void { /* StatusBar 업데이트 */ }
  private createSession(diagnostics: Diagnostic[]): FixSession { /* 새 세션 생성 */ }
}
```

---

## 7. 수정할 기존 파일

### 7.1 `BuildFeedback.ts`

```diff
// 기존: AutoBuildFix 호출
- vscode.commands.executeCommand('vibezoo._autoBuildFix', result);

// 변경: FixLoopManager에 에러 전달 + StatusBar에 Fix 액션 버튼
+ fixLoopManager.onBuildFailure(result.diagnostics, result.stderr);
+ vscode.window.setStatusBarMessage(
+   `$(warning) VibeZoo: 빌드 실패 — [자동 수정]`,
+   10000
+ );
```

### 7.2 `AutoBuildFix.ts`

**전면 폐기** → `FixLoopManager.ts`로 대체. `extension.ts`에서 `AutoBuildFix` import 제거, `FixLoopManager`로 교체.

### 7.3 `extension.ts`

```diff
- import { AutoBuildFix } from './safety/AutoBuildFix';
+ import { FixLoopManager } from './orchestra/FixLoopManager';

- autoBuildFix = new AutoBuildFix();
+ fixLoopManager = new FixLoopManager();
```

### 7.4 `vibezoo_mcp_bridge.py`

`auto_fix_status()`와 `retry_build()` MCP 도구 추가.

---

## 8. 사용자 경험 (UX)

### 8.1 수동 트리거 (기본)

```
1. 사용자가 코드 작성
2. 빌드 실행 → 실패
3. StatusBar: "$(warning) 빌드 실패 — [자동 수정]" (클릭 가능)
4. 사용자가 [자동 수정] 클릭 또는 "고쳐줘" 메시지 전송
5. LLM이:
   - auto_fix_status()로 에러 확인
   - search_codebase()로 관련 파일 검색
   - review_code()로 문제 파일 분석
   - 파일 수정
   - retry_build()로 확인
   - 실패 시 재시도 (같은 응답 내에서)
6. StatusBar: "$(check) Auto-Fix: 2회 시도 후 성공"
```

### 8.2 자동 트리거 (옵션, `build.autoFix: true`)

```
1. 빌드 실패
2. StatusBar에 즉시 "$(sync~spin) Auto-Fix 진행 중..."
3. VS Code notification: "빌드 실패 — 자동 수정을 시작할까요? [예] [아니오]"
4. 사용자가 [예] 클릭 → LLM 세션 시작
5. 이후 동일한 수동 트리거 흐름
```

---

## 9. Crow Memory 연동

### 9.1 에러 패턴 저장

```python
# retry_build() 내에서
if result.returncode != 0:
    try_crow_ingest(
        content=json.dumps({
            "error": result.stderr[-500:],
            "diagnostics": diagnostics_summary,
            "files_modified": modified_files,
        }),
        register="bug"
    )
```

### 9.2 과거 에러 패턴 조회

```python
# auto_fix_status() 내에서
past_fixes = try_crow_recall(
    query=f"build error {error_code}",
    register="bug",
    limit=3
)
```

LLM이 `auto_fix_status()` 결과에 포함된 과거 수정 이력을 참고하여 더 빠르게 fix 생성.

---

## 10. Oscillation / Give-up 전략

### 10.1 Oscillation 감지 (A→B→A 패턴)

```
Attempt 1: TS2322 at VisualVibePanels.ts:388 → fix applied
Attempt 2: TS2345 at VisualVibePanels.ts:442 → fix applied
Attempt 3: TS2322 at VisualVibePanels.ts:388 → SAME AS ATTEMPT 1 (oscillation!)
→ Stop. "A→B→A 패턴 감지. 수동 확인 필요."
```

### 10.2 Repeated Error 감지

동일한 파일/라인/코드의 에러가 2회 연속 발생 → 수정이 효과 없음. Stop.

### 10.3 Timeout

전체 fix loop 120초 제한. 초과 시 give up.

---

## 11. 구현 우선순위

| 순위 | 항목 | 설명 |
|:---:|:---|:---|
| 1 | `FixLoopManager` | 핵심 상태 머신, attempt 카운터, oscillation 감지 |
| 2 | `auto_fix_status` MCP 도구 | LLM이 에러 정보를 읽는 진입점 |
| 3 | `retry_build` MCP 도구 | LLM이 빌드를 재실행하고 결과를 받는 도구 |
| 4 | `BuildFeedback` 연동 | 빌드 실패 → FixLoopManager 연결 |
| 5 | StatusBar 액션 버튼 | "[자동 수정]" 클릭 가능한 UX |
| 6 | Crow Memory 연동 | 과거 에러 패턴 학습/조회 |
| 7 | 기존 `AutoBuildFix` 제거 | dead code cleanup |

---

## 12. 검증 시나리오

### 시나리오 1: 단순 타입 에러 (1회 수정)

```
1. TS2322 타입 에러 발생
2. 사용자 "고쳐줘"
3. LLM: auto_fix_status() → 에러 확인
4. LLM: 파일 수정 (타입 교정)
5. LLM: retry_build() → exitCode 0
6. 완료: "1회 시도 후 빌드 성공"
```

### 시나리오 2: 연쇄 에러 (2회 수정)

```
1. TS2322 + TS2345 2개 에러 발생
2. LLM: 첫 번째 에러만 수정 → retry_build()
3. 빌드 실패 (TS2345만 남음)
4. LLM: auto_fix_status() → 남은 에러 확인
5. LLM: 두 번째 에러 수정 → retry_build()
6. 빌드 성공
7. 완료: "2회 시도 후 빌드 성공"
```

### 시나리오 3: Oscillation (조기 중단)

```
1. TS2322 at A.ts:100
2. LLM fixes → new error TS2322 at B.ts:200
3. LLM fixes → TS2322 at A.ts:100 AGAIN
4. FixLoopManager: oscillation 감지 → abandoned
5. 사용자에게: "A→B→A 패턴 감지. 수동 확인이 필요합니다."
```

### 시나리오 4: 사용자 개입 — Whiteboard 유도

```
1. TS2322 + TS2345 복합 에러 발생, Auto-Fix 진행 중 (attempt 1 실패)
2. 사용자가 Whiteboard에 "여기 API 시그니처 바꾸지 마" 라고 텍스트 작성
3. LLM: check_intervention() → Whiteboard에서 사용자 메모 발견
4. LLM: "API 시그니처를 유지하면서 내부 로직만 수정하는 방식으로 전환"
5. LLM: retry_build() → 성공
6. 완료: "2회 시도 (사용자 Whiteboard 가이드 반영)"
```

### 시나리오 5: 사용자 개입 — 채팅 중단

```
1. Auto-Fix 진행 중, attempt 2까지 실패
2. 사용자가 채팅: "그 파일은 건드리지 말고 다른 방식으로 해결해줘"
3. LLM: check_intervention() → 채팅 메시지 감지
4. LLM: "알겠습니다. 해당 파일을 제외한 다른 접근법을 시도합니다"
5. LLM: 다른 파일 수정 → retry_build() → 성공
6. 완료: "3회 시도 (사용자 채팅 피드백 반영)"
```

---

## 13. Human-in-the-Loop: Whiteboard + Chat 개입

### 13.1 설계 원칙

자율 수정 루프는 **완전 자동이 아니라 인간이 개입할 수 있는 반자동**이어야 한다. VibeZoo의 핵심 철학인 "사용자가 통제 가능한 자동화"를 구현하기 위해, 수정 루프의 **매 attempt 전에 사용자 개입 창구**를 연다.

### 13.2 개입 채널 2종

```
Auto-Fix Loop 내부:

  attempt N 시작
      │
      ▼
  check_intervention() 호출
      │
      ├── Whiteboard 확인 (get_whiteboard_state)
      │   → 사용자 그림/메모/주석 추출
      │
      ├── Pending Message 확인
      │   → ~/.vibezoo-chat-pending.json
      │   → StatusBar 인터랙션 결과
      │
      └── 결과에 따라:
          ├── 개입 없음 → 계속 진행
          └── 개입 있음 → 사용자 의도 반영 후 진행
```

### 13.3 Whiteboard 개입

**사용 시나리오**:
- AI가 코드를 수정하는 동안, 사용자는 Whiteboard에 영향 범위 표시 (원, 화살표)
- "여기까지만 수정해" 라고 텍스트 박스로 영역 지정
- 아키텍처 다이어그램을 그려서 AI에게 의도 전달
- 이전에 발생했던 유사 버그 패턴을 그림으로 설명

**구현**:
```python
@mcp.tool
def check_intervention() -> str:
    """Auto-Fix Loop 진행 전 사용자 개입 여부를 확인합니다.
    Whiteboard 상태와 대기 중인 채팅 메시지를 조회합니다.
    
    Returns:
        JSON: { whiteboard_annotations, pending_messages, user_guidance, should_pause }
    """
    result = {
        "whiteboard_annotations": [],
        "pending_messages": [],
        "user_guidance": None,
        "should_pause": False
    }
    
    # 1. Whiteboard 확인
    wb_file = os.path.join(os.path.expanduser("~"), ".vibezoo-whiteboard.json")
    if os.path.exists(wb_file):
        with open(wb_file) as f:
            wb_data = json.load(f)
        # 텍스트 객체만 추출 (사용자 메모)
        for cmd in wb_data.get("commands", []):
            if cmd.get("type") == "text":
                result["whiteboard_annotations"].append({
                    "text": cmd.get("props", {}).get("text", ""),
                    "position": {"left": cmd.get("props", {}).get("left", 0)}
                })
    
    # 2. Pending chat messages 확인
    pending_file = os.path.join(os.path.expanduser("~"), ".vibezoo-chat-pending.json")
    if os.path.exists(pending_file):
        with open(pending_file) as f:
            pending = json.load(f)
        result["pending_messages"] = pending.get("messages", [])
        os.remove(pending_file)  # 중복 처리 방지
    
    # 3. 사용자 가이드라인 종합
    if result["whiteboard_annotations"] or result["pending_messages"]:
        result["user_guidance"] = _synthesize_guidance(result)
    
    return json.dumps(result, indent=2, ensure_ascii=False)
```

**Whiteboard → 코드 매핑 규칙**:
- 사용자가 파일명/라인번호 적으면 → LLM이 해당 범위만 수정
- "DO NOT TOUCH" + 화살표 → LLM이 해당 파일/함수 제외
- 아키텍처 그림 → LLM이 구조적 제약으로 해석

### 13.4 Chat 개입

**사용 시나리오**:
- Auto-Fix 진행 중 사용자가 채팅창에 "잠깐 멈춰" → 루프 일시정지
- "저 파일은 API라서 건드리면 안 돼" → 제외 목록에 추가
- "대신 이렇게 해봐: ..." → 새로운 접근법 제시
- "지금 수정 괜찮아, 계속 진행해" → 루프 재개

**StatusBar 액션 버튼**:

| 버튼 | 동작 |
|:---|:---|
| `[일시정지]` | pause_fix_loop() → 현재 attempt 완료 후 대기 |
| `[계속 진행]` | resume_fix_loop() → 중단된 루프 재개 |
| `[중단]` | abort_fix_loop() → 즉시 종료, 변경사항 유지 |
| `[되돌리기]` | rewind_fix_loop() → yocto로 수정 전 상태 복구 |
| `[가이드 작성]` | Whiteboard 열기 → 사용자 의도 시각화 |

### 13.5 Fix Loop 상태 머신 (개입 상태 추가)

```
idle → pending → in_progress → building → resolved
                    │                │
                    │                ├── 실패 → pending (재시도)
                    │                └── oscillation/max → abandoned
                    │
                    └── check_intervention() 에서 should_pause
                              │
                              ▼
                       awaiting_user  ← 사용자 개입 대기
                              │
                              │ 사용자 메시지 / Whiteboard 업데이트
                              ▼
                       user_override  ← 사용자 가이드 반영
                              │
                              ▼
                        in_progress (재개)
```

### 13.6 MCP 도구 추가 (개입용)

| 도구 | 용도 |
|:---|:---|
| `check_intervention()` | Whiteboard + 채팅 메시지 확인. 매 attempt 전에 LLM이 호출 |
| `request_user_guidance(question)` | LLM이 사용자에게 질문. StatusBar에 표시 + pending 파일 기록 |
| `pause_fix_loop(reason)` | 현재 attempt 완료 후 루프 일시정지 |
| `resume_fix_loop()` | 사용자가 재개 승인 |

### 13.7 개입 우선순위

사용자 개입이 감지되면 다음 규칙을 따른다:

1. **"중단" 명령** → 즉시 루프 종료 (최우선)
2. **"파일 제외" 지시** → 해당 파일 수정 건너뛰기
3. **"접근법 변경" 지시** → 다음 attempt에 새 전략 적용
4. **Whiteboard 주석** → 텍스트는 명령으로, 그림은 컨텍스트로 해석
5. **일반 피드백** → 다음 수정에 참고

---

## 14. 파일 변경 요약

| 파일 | 액션 | 설명 |
|:---|:---|:---|
| `extension/src/orchestra/FixLoopManager.ts` | **신규** | 핵심 상태 머신, attempt 관리, oscillation 감지, 사용자 개입 처리 |
| `extension/src/flow/BuildFeedback.ts` | **수정** | AutoBuildFix 호출 → FixLoopManager 연동 |
| `extension/src/safety/AutoBuildFix.ts` | **삭제** | FixLoopManager로 대체 |
| `extension/src/extension.ts` | **수정** | AutoBuildFix → FixLoopManager 교체, 개입용 커맨드 4종 등록 (pause/resume/abort/rewind) |
| `mcp-servers/vibezoo_mcp_bridge.py` | **수정** | `auto_fix_status()`, `retry_build()`, `check_intervention()`, `request_user_guidance()`, `pause_fix_loop()`, `resume_fix_loop()` 추가 |
| `extension/src/types/index.ts` | **수정** | `FixSession`, `FixLoopState`(awaiting_user, user_override 추가), `UserGuidance` 타입 추가 |
| `extension/src/visual/VisualVibePanels.ts` | **수정** | Whiteboard 텍스트 객체 → `check_intervention()` 연동 (ready 신호로 fix loop에 컨텍스트 제공) |
