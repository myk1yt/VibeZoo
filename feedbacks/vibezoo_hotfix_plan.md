# VibeZoo Hotfix Master Plan

## 1. Overview
The `debugger` agent's diagnosis has identified 3 critical defects in recently added code that seriously threaten project stability and user system safety. This master plan provides architecture and logic modification guidelines to fundamentally and safely resolve these defects.

## 2. Issue Analysis & Solutions

### 2.1. `FixLoopManager.ts`: Control Logic Inversion Problem
* **Problem**: Logical error where the loop proceeds when instability is high and stops when low. This can cause work to continue in unstable states, leading to cascading errors.
* **Solution (Action Item)**:
  * Invert the loop control condition: Change so that work **continues** when `instability < THRESHOLD` (stable state), and **halts/breaks** and calls recovery logic when `instability >= THRESHOLD` (unstable state).
  * *Design Guideline*: Clearly handle edge cases when changing conditions, and design to return appropriate error logs and status codes on halt.

### 2.2. `SubagentManager.ts`: System Violation (Process Force Termination) Problem
* **Problem**: When PID discovery fails, the last resort command `taskkill /F /FI "IMAGENAME eq python.exe"` forcefully terminates **all Python processes** on the user's system, a severe system infringement.
* **Solution (Action Item)**:
  * Completely delete the indiscriminate `taskkill` command line execution code.
  * Safely cache ChildProcess objects returned when spawning sub-agent processes in internal state (Memory/State).
  * When terminating processes, improve the architecture to use the `kill()` method of cached ChildProcess objects (e.g., `process.kill()`, `tree-kill` library) to **specifically and safely terminate only that sub-agent and its child processes**.
  * *Design Guideline*: Even if PID discovery fails completely, perform Graceful Fallback (output warning log and isolate) without interfering with other system processes.

### 2.3. `SelfCheck.ts`: User Data Loss Problem
* **Problem**: The automatic recovery process of `.roo/mcp.json` ignores existing settings (other MCP server information, etc.) and completely overwrites the entire file, causing complete loss of user's existing data.
* **Solution (Action Item)**:
  * Change logic from Overwrite method to **Safe Merge method**.
  * Implementation Steps:
    1. **Read**: Use `fs.promises.readFile` to read the existing `.roo/mcp.json` file. (Initialize as empty object if file doesn't exist)
    2. **Parse**: Parse via `JSON.parse()`.
    3. **Merge**: Merge only essential configuration nodes required for VibeZoo operation into the existing JSON object (Deep merge or Object.assign). Do not touch other existing MCP configuration values.
    4. **Write**: Safely save in a neat format using `JSON.stringify(..., null, 2)`.
  * *Design Guideline*: Must include `try-catch` exception handling for potential Syntax Errors during JSON parsing to ensure integrity.

## 3. Task Sequence
This hotfix directly affects system stability, so it must be executed quickly and accurately in the following order.

1. **Phase 1: `SubagentManager.ts` Hotfix (Critical & Urgent)**
   - Immediately remove Python process killer logic that affects the entire system and apply process object-based termination logic.
2. **Phase 2: `SelfCheck.ts` Hotfix (High)**
   - Implement file read/merge logic and add exception handling to prevent user configuration data loss.
3. **Phase 3: `FixLoopManager.ts` Hotfix (High)**
   - Normalize loop control flow (fix conditional statement).
4. **Phase 4: Integration Test and Verification (QA)**
   - Verify each modification works as intended without side effects. (Especially `mcp.json` merge test and subprocess isolated termination test)

## 4. Expected Outcomes
* Elimination of system-level risk factors (terminating all Python processes), ensuring user development environment safety.
* Safe preservation of user custom settings (other MCP).
* Maximization of VibeZoo self-healing and operational stability through normalization of instability control logic.
