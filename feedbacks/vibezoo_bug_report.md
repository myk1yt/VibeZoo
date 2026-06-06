# VibeZoo Codebase Bug and Vulnerability Diagnostic Report

**Author**: AGY-CLI Orchestrator (feat. `debugger` Agent)
**Diagnosis Target**: VibeZoo Extension Core Logic

---

## 🔍 Diagnosis Summary
The debug specialist agent scanned VibeZoo's overall structure (Orchestration, Yolo Safety Net, Crow Memory integration, etc.) and discovered a total of **4 critical logical/structural bugs**, including communication breakdown due to configuration file neglect, critical memory leaks, and large project context truncation.

---

## 🐛 Major Bug Detailed Analysis

### 1. MCP Connection Failure Due to Hardcoded Port Settings (Logical Bug)
- **Location**: `autoConfigureMCP()` function in `extension/src/extension.ts`
- **Problem**: `SubagentManager` starts the bridge process according to user settings (`vibezoo.bridge.port`), but the `autoConfigureMCP()` function that manipulates the actual VS Code settings (`.roo/mcp.json`) ignores arguments and hardcodes the `http://localhost:9027/sse` path.
- **Impact (High)**: If the user changes the bridge port, MCP tool calls will always attempt to access port 9027, resulting in Connection Refused and complete tool integration paralysis.

### 2. Hardcoded Crow Memory Environment Variable (Configuration Bug)
- **Location**: `spawnBridge()` function in `extension/src/orchestra/SubagentManager.ts`
- **Problem**: When spawning the Python bridge, the environment variable `CROW_SERVER_URL` is forced to `http://127.0.0.1:9020`.
- **Impact (Medium)**: The status bar monitoring module (`CrowServerManager`) correctly reads user settings (`vibezoo.crow.port`), but the core bridge always communicates on port 9020, causing disconnection from the memory module (Crow Memory) when settings change.

### 3. Critical Memory Leak and Yolo Rewind Logic Defect (Data/Memory Bug)
- **Location**: `extension/src/safety/YoctoManager.ts`
- **Problem 1 (Memory Leak)**: `executeGlobalBackup()` is called on every file save, but the internal logic indefinitely pushes metadata into a single snapshot array (`latest.files.push(entry)`). This causes severe RAM leaks in long sessions.
- **Problem 2 (Restore Failure)**: The backup timing is set **after** file change (`onDidChange`), so `instantRewind` rolls back files to "immediately after editing" rather than "before editing." Additionally, the reverse order restoration (`reverse()`) logic defect causes duplicate I/O for the same file and prevents accurate state (Undo) restoration.
- **Impact (Critical)**: The Yocto feature, intended as a safety net, actually consumes memory and fails to perform the most important "YOLO recovery" function, severely degrading reliability.

### 4. Large Project Context Omission and Tree Truncation (Context Bug)
- **Location**: `rescan()` function in `extension/src/flow/ProjectTreeScanner.ts`
- **Problem**: The `vscode.workspace.findFiles(pattern, excludePattern, 100)` statement in project tree construction has a fixed maximum result (`maxResults`) of only `100`.
- **Impact (High)**: In real-world projects with over 100 files, the tree is truncated midway. This prevents the LLM from fully understanding the complete file structure, causing severe context omission (hallucination).

---

## 🛠 Recommended Actions (Next Step)
The above bugs directly undermine VibeZoo's core philosophy of **Stability (YOLO)** and **Flexibility (Configuration)**.
It is strongly recommended to establish a refactoring plan through the `architect` agent, then deploy the `coder` agent to sequentially correct (Hotfix) the code.
