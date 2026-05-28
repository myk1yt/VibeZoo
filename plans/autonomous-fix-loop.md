# VibeZoo Autonomous Fix Loop — Design Document

> **Written**: 2026-05-27
> **Version**: v1.0
> **Status**: Design Phase
> **Related Files**: `AutoBuildFix.ts`, `BuildFeedback.ts`, `SubagentManager.ts`, `vibezoo_mcp_bridge.py`

---

## 1. Problem Diagnosis

### 1.1 Current Status

VibeZoo's `AutoBuildFix` is currently the following **empty loop**:

```
BuildFeedback → build failure detected → AutoBuildFix.run()
                                      ├── check exitCode
                                      ├── check oscillation
                                      ├── rebuild() retry (just same build)
                                      └── No LLM call! No code modification!
```

The `run()` method in [`AutoBuildFix.ts`](../extension/src/safety/AutoBuildFix.ts:29) only repeats rebuilding up to `max_attempts=3`, with **zero logic to pass errors to LLM and receive fix code**. Therefore, if the build fails, it fails forever.

### 1.2 User Expectation vs Reality

| Expectation | Reality |
|:---|:---|
| "One order, continuous cycle, bug-free completion" | Toolbox (file search, lint, backup) |
| Build failure → AI analysis → fix → rebuild → success | Build failure → rebuild → failure → rebuild → failure |
| Autonomous self-healing loop | Must manually find and fix bugs one by one |

---

## 2. Core Design Principles

### 2.1 Architecture Constraints

VibeZoo is a **Companion Extension** that cannot modify Zoo Code source. Therefore:

- Extension **cannot directly call LLM** (no API key)
- Instead, communication flows in the direction of **LLM calling VibeZoo's tools**
- Communication channel between Extension and LLM: **File System** (pattern verified in Whiteboard)

### 2.2 Key Insight: One Message = Many Fix Attempts

LLM (Zoo Code) can sequentially call multiple MCP tools within a single response:

```
User: "Fix the build error" (1 message)
    │
    ▼
LLM: auto_fix_status() called → receive error list
LLM: search_codebase("error-related files") → collect context
LLM: review_code("failed file") → analyze problem
LLM: File edit (edit tool)
LLM: retry_build() called → receive new build result
    │
    ├── success → report completion
    └── failure → analyze again → fix → retry_build() (repeat within same response)
```

With this structure, **without user intervention**, a single message can auto-cycle up to `max_attempts` (default 3).

---

## 3. Overall Architecture

### 3.1 Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                        VS Code Window                              │
│                                                                   │
│  ┌─────────────────────────┐    ┌─────────────────────────────┐  │
│  │     Zoo Code (LLM)      │    │   VibeZoo Extension          │  │
│  │                         │    │                              │  │
│  │  ◄── MCP tool calls ────┼────┤  BuildFeedback              │  │
│  │      auto_fix_status()  │    │  (build failure detection)   │  │
│  │      retry_build()      │    │        │                     │  │
│  │      search_codebase()  │    │        ▼                     │  │
│  │      review_code()      │    │  FixLoopManager (new)        │  │
│  │      map_dependencies() │    │  ┌───────────────────────┐   │  │
│  │                         │    │  │ ~/.vibezoo-fix-       │   │  │
│  │  File edit (edit tool)  │    │  │   request.json        │   │  │
│  │      │                  │    │  │   (error data)         │   │  │
│  │      │                  │    │  ├───────────────────────┤   │  │
│  │      │                  │    │  │ Attempt counter      │   │  │
│  │      │                  │    │  │ Oscillation detector │   │  │
│  │      │                  │    │  │ Max attempt guard    │   │  │
│  │      │                  │    │  └───────────────────────┘   │  │
│  │      │                  │    │        │                     │  │
│  │      │                  │    │        ▼                     │  │
│  │      │                  │    │  StatusBar                   │  │
│  │      │                  │    │  "Auto-Fix: Attempt 2/3..."  │  │
│  └──────┼──────────────────┘    └─────────────────────────────┘  │
│         │                                                        │
└─────────┼────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────┐    ┌──────────────────────┐
│  Crow Memory (9020) │    │  VibeZoo MCP Bridge  │
│  • bug register     │    │  (9027/sse)          │
│  • past error pats  │    │  • auto_fix_status   │
│  • fix history learn│    │  • retry_build       │
└─────────────────────┘    │  • search_codebase   │
                           │  • review_code       │
                           │  • map_dependencies  │
                           └──────────────────────┘
```

### 3.2 Components

| Component | Location | Role |
|:---|:---|:---|
| **FixLoopManager** | `extension/src/orchestra/FixLoopManager.ts` (new) | State management, attempt counter, oscillation detection, fix request file read/write |
| **BuildFeedback** | `extension/src/flow/BuildFeedback.ts` (modified) | Build failure detection → pass errors to FixLoopManager |
| **AutoBuildFix** | `extension/src/safety/AutoBuildFix.ts` (replaced) | Removed. Replaced by FixLoopManager |
| **auto_fix_status** | `vibezoo_mcp_bridge.py` (new MCP tool) | LLM queries current fix request |
| **retry_build** | `vibezoo_mcp_bridge.py` (new MCP tool) | LLM requests build re-execution, returns result |
| **crow_ingest (bug)** | Crow Memory | Store past error patterns → learning |

---

## 4. Fix Request File Spec

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

### 4.2 State Machine

```
                    ┌──────────┐
                    │  idle    │ (build success state)
                    └────┬─────┘
                         │ build failure
                         ▼
                    ┌──────────┐
                    │ pending  │ (waiting for LLM)
                    └────┬─────┘
                         │ LLM calls auto_fix_status()
                         ▼
              ┌─────────────────────┐
              │   in_progress       │ (LLM analyzing/fixing)
              └────────┬────────────┘
                       │ LLM calls retry_build()
                       ▼
              ┌─────────────────────┐
              │   building          │ (build executing)
              └────────┬────────────┘
                       │
          ┌────────────┼────────────┐
          │ success    │            │ failure
          ▼            │            ▼
    ┌──────────┐       │    ┌──────────────┐
    │ resolved │       │    │ attempt < max│
    └──────────┘       │    └──┬───────┬───┘
                       │       │Yes    │No
                       │       ▼       ▼
                       │  pending  ┌──────────┐
                       │  (retry)  │ give_up  │
                       │           └──────────┘
                       │
                       │ oscillation detected
                       ▼
                 ┌───────────┐
                 │ abandoned │ (A→B→A pattern)
                 └───────────┘
```

---

## 5. New MCP Tools

### 5.1 `auto_fix_status()`

```python
@mcp.tool
def auto_fix_status() -> str:
    """Queries the status and error information of the current Auto-Fix session.
    Called by LLM to analyze build errors and start fixing.
    
    Returns:
        JSON: { status, attempt, maxAttempts, diagnostics, history }
    """
    fix_request_file = os.path.join(os.path.expanduser("~"), ".vibezoo-fix-request.json")
    if not os.path.exists(fix_request_file):
        return json.dumps({"status": "idle", "message": "No active fix request"})
    
    with open(fix_request_file) as f:
        data = json.load(f)
    
    # Change status to in_progress
    data["status"] = "in_progress"
    with open(fix_request_file, "w") as f:
        json.dump(data, f, indent=2)
    
    return json.dumps(data, indent=2)
```

### 5.2 `retry_build()`

```python
@mcp.tool
def retry_build() -> str:
    """Re-executes the build and returns the result.
    Called by LLM after applying fix code to verify build success.
    
    Returns:
        JSON: { exitCode, diagnostics, success }
    """
    import subprocess, sys
    
    root = os.getcwd()
    
    # Detect project type
    pkg_json = Path(root) / "package.json"
    if pkg_json.exists():
        cmd = ["npx.cmd" if sys.platform == "win32" else "npx", "tsc", "--noEmit"]
    else:
        return json.dumps({"exitCode": -1, "diagnostics": [], "success": False, "error": "No build command detected"})
    
    result = subprocess.run(cmd, cwd=root, capture_output=True, text=True, timeout=60)
    
    # Record result in fix-request file
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

## 6. FixLoopManager Class Design

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

  /** Called by BuildFeedback on build failure */
  onBuildFailure(diagnostics: Diagnostic[], stderr: string): void {
    // Start new fix session or add attempt to existing session
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

  /** Called when LLM reports build success via retry_build */
  onBuildSuccess(): void {
    if (this.currentSession) {
      this.currentSession.status = 'resolved';
      this.writeFixRequest();
      this.updateStatusBar(true);
    }
  }

  /** Oscillation detection */
  isOscillating(): boolean {
    // A→B→A pattern: compare even/odd error signatures in last 4 attempts
    const h = this.currentSession?.history ?? [];
    if (h.length < 4) return false;
    const recent = h.slice(-4);
    const sigs = recent.map(a => this.errorSignature(a.diagnostics));
    return sigs[0] === sigs[2] && sigs[1] === sigs[3];
  }

  /** Give up conditions */
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

  private writeFixRequest(): void { /* Write JSON file */ }
  private updateStatusBar(success = false): void { /* Update StatusBar */ }
  private createSession(diagnostics: Diagnostic[]): FixSession { /* Create new session */ }
}
```

---

## 7. Existing Files to Modify

### 7.1 `BuildFeedback.ts`

```diff
// Before: calling AutoBuildFix
- vscode.commands.executeCommand('vibezoo._autoBuildFix', result);

// After: pass errors to FixLoopManager + show StatusBar Fix action button
+ fixLoopManager.onBuildFailure(result.diagnostics, result.stderr);
+ vscode.window.setStatusBarMessage(
+   `$(warning) VibeZoo: Build Failed — [Auto Fix]`,
+   10000
+ );
```

### 7.2 `AutoBuildFix.ts`

**Full disposal** → replaced by `FixLoopManager.ts`. Remove `AutoBuildFix` import from `extension.ts`, replace with `FixLoopManager`.

### 7.3 `extension.ts`

```diff
- import { AutoBuildFix } from './safety/AutoBuildFix';
+ import { FixLoopManager } from './orchestra/FixLoopManager';

- autoBuildFix = new AutoBuildFix();
+ fixLoopManager = new FixLoopManager();
```

### 7.4 `vibezoo_mcp_bridge.py`

Add `auto_fix_status()` and `retry_build()` MCP tools.

---

## 8. User Experience (UX)

### 8.1 Manual Trigger (Default)

```
1. User writes code
2. Build executes → fails
3. StatusBar: "$(warning) Build Failed — [Auto Fix]" (clickable)
4. User clicks [Auto Fix] or sends "fix it" message
5. LLM will:
   - auto_fix_status() to check errors
   - search_codebase() to find related files
   - review_code() to analyze problem files
   - Fix files
   - retry_build() to verify
   - On failure, retry (within same response)
6. StatusBar: "$(check) Auto-Fix: Success after 2 attempts"
```

### 8.2 Automatic Trigger (Optional, `build.autoFix: true`)

```
1. Build fails
2. StatusBar immediately shows "$(sync~spin) Auto-Fix in progress..."
3. VS Code notification: "Build failed — Start auto fix? [Yes] [No]"
4. User clicks [Yes] → LLM session starts
5. Same flow as manual trigger from here
```

---

## 9. Crow Memory Integration

### 9.1 Error Pattern Storage

```python
# Inside retry_build()
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

### 9.2 Past Error Pattern Query

```python
# Inside auto_fix_status()
past_fixes = try_crow_recall(
    query=f"build error {error_code}",
    register="bug",
    limit=3
)
```

LLM references past fix history included in `auto_fix_status()` results to generate fixes faster.

---

## 10. Oscillation / Give-up Strategy

### 10.1 Oscillation Detection (A→B→A pattern)

```
Attempt 1: TS2322 at VisualVibePanels.ts:388 → fix applied
Attempt 2: TS2345 at VisualVibePanels.ts:442 → fix applied
Attempt 3: TS2322 at VisualVibePanels.ts:388 → SAME AS ATTEMPT 1 (oscillation!)
→ Stop. "A→B→A pattern detected. Manual inspection required."
```

### 10.2 Repeated Error Detection

Same file/line/code error occurs 2 consecutive times → fix ineffective. Stop.

### 10.3 Timeout

Entire fix loop limited to 120 seconds. Give up on timeout.

---

## 11. Implementation Priority

| Priority | Item | Description |
|:---:|:---|:---|
| 1 | `FixLoopManager` | Core state machine, attempt counter, oscillation detection |
| 2 | `auto_fix_status` MCP tool | Entry point for LLM to read error info |
| 3 | `retry_build` MCP tool | Tool for LLM to re-execute build and receive results |
| 4 | `BuildFeedback` integration | Build failure → FixLoopManager connection |
| 5 | StatusBar action button | Clickable "[Auto Fix]" UX |
| 6 | Crow Memory integration | Past error pattern learning/query |
| 7 | Remove existing `AutoBuildFix` | Dead code cleanup |

---

## 12. Verification Scenarios

### Scenario 1: Simple Type Error (1 fix)

```
1. TS2322 type error occurs
2. User says "fix it"
3. LLM: auto_fix_status() → check error
4. LLM: Fix file (type correction)
5. LLM: retry_build() → exitCode 0
6. Complete: "Build succeeded after 1 attempt"
```

### Scenario 2: Chain Errors (2 fixes)

```
1. 2 errors TS2322 + TS2345 occur
2. LLM: Fix only first error → retry_build()
3. Build fails (only TS2345 remains)
4. LLM: auto_fix_status() → check remaining error
5. LLM: Fix second error → retry_build()
6. Build succeeds
7. Complete: "Build succeeded after 2 attempts"
```

### Scenario 3: Oscillation (Early Abort)

```
1. TS2322 at A.ts:100
2. LLM fixes → new error TS2322 at B.ts:200
3. LLM fixes → TS2322 at A.ts:100 AGAIN
4. FixLoopManager: oscillation detected → abandoned
5. To user: "A→B→A pattern detected. Manual inspection required."
```

### Scenario 4: User Intervention — Whiteboard Guidance

```
1. Complex TS2322 + TS2345 errors, Auto-Fix in progress (attempt 1 failed)
2. User writes on Whiteboard: "Don't change API signature here"
3. LLM: check_intervention() → finds user note on Whiteboard
4. LLM: "Switch to fixing only internal logic while preserving API signature"
5. LLM: retry_build() → success
6. Complete: "2 attempts (user Whiteboard guidance applied)"
```

### Scenario 5: User Intervention — Chat Interruption

```
1. Auto-Fix in progress, attempt 2 failed
2. User chats: "Don't touch that file, solve it differently"
3. LLM: check_intervention() → detects chat message
4. LLM: "Understood. Will try a different approach excluding that file"
5. LLM: Fix other files → retry_build() → success
6. Complete: "3 attempts (user chat feedback applied)"
```

---

## 13. Human-in-the-Loop: Whiteboard + Chat Intervention

### 13.1 Design Principles

The autonomous fix loop should be **semi-automatic with human intervention, not fully automatic**. To implement VibeZoo's core philosophy of "user-controllable automation", the fix loop opens a **user intervention channel before each attempt**.

### 13.2 2 Intervention Channels

```
Inside Auto-Fix Loop:

  attempt N starts
      │
      ▼
  check_intervention() called
      │
      ├── Check Whiteboard (get_whiteboard_state)
      │   → Extract user drawings/memos/annotations
      │
      ├── Check Pending Message
      │   → ~/.vibezoo-chat-pending.json
      │   → StatusBar interaction results
      │
      └── Based on result:
          ├── No intervention → continue
          └── Intervention → incorporate user intent and proceed
```

### 13.3 Whiteboard Intervention

**User Scenarios**:
- While AI is modifying code, user marks scope on Whiteboard (circles, arrows)
- "Modify only up to here" area specification with text box
- Draw architecture diagram to convey intent to AI
- Visually explain similar bug patterns that occurred before

**Implementation**:
```python
@mcp.tool
def check_intervention() -> str:
    """Checks for user intervention before Auto-Fix Loop proceeds.
    Queries Whiteboard status and pending chat messages.
    
    Returns:
        JSON: { whiteboard_annotations, pending_messages, user_guidance, should_pause }
    """
    result = {
        "whiteboard_annotations": [],
        "pending_messages": [],
        "user_guidance": None,
        "should_pause": False
    }
    
    # 1. Check Whiteboard
    wb_file = os.path.join(os.path.expanduser("~"), ".vibezoo-whiteboard.json")
    if os.path.exists(wb_file):
        with open(wb_file) as f:
            wb_data = json.load(f)
        # Extract only text objects (user memos)
        for cmd in wb_data.get("commands", []):
            if cmd.get("type") == "text":
                result["whiteboard_annotations"].append({
                    "text": cmd.get("props", {}).get("text", ""),
                    "position": {"left": cmd.get("props", {}).get("left", 0)}
                })
    
    # 2. Check pending chat messages
    pending_file = os.path.join(os.path.expanduser("~"), ".vibezoo-chat-pending.json")
    if os.path.exists(pending_file):
        with open(pending_file) as f:
            pending = json.load(f)
        result["pending_messages"] = pending.get("messages", [])
        os.remove(pending_file)  # Prevent duplicate processing
    
    # 3. Synthesize user guidance
    if result["whiteboard_annotations"] or result["pending_messages"]:
        result["user_guidance"] = _synthesize_guidance(result)
    
    return json.dumps(result, indent=2, ensure_ascii=False)
```

**Whiteboard → Code Mapping Rules**:
- User writes filename/line number → LLM only modifies that scope
- "DO NOT TOUCH" + arrow → LLM excludes that file/function
- Architecture drawing → LLM interprets as structural constraint

### 13.4 Chat Intervention

**User Scenarios**:
- During Auto-Fix, user types "pause" in chat → loop pauses
- "That file is an API, don't touch it" → added to exclusion list
- "Try this instead: ..." → suggests new approach
- "Current fix is fine, continue" → resume loop

**StatusBar Action Buttons**:

| Button | Action |
|:---|:---|
| `[Pause]` | pause_fix_loop() → wait after current attempt completes |
| `[Resume]` | resume_fix_loop() → resume paused loop |
| `[Abort]` | abort_fix_loop() → immediate stop, keep changes |
| `[Rewind]` | rewind_fix_loop() → restore pre-fix state with yocto |
| `[Write Guide]` | Open Whiteboard → visualize user intent |

### 13.5 Fix Loop State Machine (With Intervention States)

```
idle → pending → in_progress → building → resolved
                    │                │
                    │                ├── fail → pending (retry)
                    │                └── oscillation/max → abandoned
                    │
                    └── check_intervention() detects should_pause
                              │
                              ▼
                       awaiting_user  ← waiting for user intervention
                              │
                              │ user message / Whiteboard update
                              ▼
                        user_override  ← user guidance applied
                              │
                              ▼
                         in_progress (resumed)
```

### 13.6 MCP Tools Added (For Intervention)

| Tool | Purpose |
|:---|:---|
| `check_intervention()` | Check Whiteboard + chat messages. Called by LLM before each attempt |
| `request_user_guidance(question)` | LLM asks user a question. Displayed on StatusBar + pending file written |
| `pause_fix_loop(reason)` | Pause loop after current attempt completes |
| `resume_fix_loop()` | User approves resume |

### 13.7 Intervention Priority

When user intervention is detected, follow these rules:

1. **"Abort" command** → immediate loop termination (highest priority)
2. **"Exclude file" directive** → skip that file modification
3. **"Change approach" directive** → apply new strategy in next attempt
4. **Whiteboard annotations** → text as commands, drawings as context
5. **General feedback** → reference for next fix

---

## 14. File Change Summary

| File | Action | Description |
|:---|:---|:---|
| `extension/src/orchestra/FixLoopManager.ts` | **New** | Core state machine, attempt management, oscillation detection, user intervention handling |
| `extension/src/flow/BuildFeedback.ts` | **Modify** | AutoBuildFix call → FixLoopManager integration |
| `extension/src/safety/AutoBuildFix.ts` | **Delete** | Replaced by FixLoopManager |
| `extension/src/extension.ts` | **Modify** | AutoBuildFix → FixLoopManager replacement, 4 intervention commands registered (pause/resume/abort/rewind) |
| `mcp-servers/vibezoo_mcp_bridge.py` | **Modify** | Add `auto_fix_status()`, `retry_build()`, `check_intervention()`, `request_user_guidance()`, `pause_fix_loop()`, `resume_fix_loop()` |
| `extension/src/types/index.ts` | **Modify** | Add `FixSession`, `FixLoopState`(awaiting_user, user_override added), `UserGuidance` types |
| `extension/src/visual/VisualVibePanels.ts` | **Modify** | Whiteboard text objects → `check_intervention()` integration (provides context to fix loop via ready signal) |
