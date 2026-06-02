# VibeZoo Development Journal

## 2026-06-02: Dropzone & Vision AI Pipeline Refactoring

### Issue 1: Drag & Drop Failure in VS Code Webview
* **Symptom**: Dragging files onto the Dropzone UI worked in a normal browser but failed inside the VS Code Webview sandbox.
* **Root Cause Analysis**: The initial attempt to fix this involved layering an `opacity: 0` `<input type="file">` over the drop area. While theoretically sound, VS Code's Webview (specifically on Windows Webview2) blocks or swallows drag-and-drop events over file inputs. The earlier JS-based interception was also failing because `window.addEventListener('drop')` was aggressively swallowing events before they reached the dropzone.
* **Resolution**: Reverted to pure Vanilla JS drag events (`dragenter`, `dragover`, `drop`) attached strictly to the `#dropzone` div. Removed aggressive `window` level interception. The file payload is now successfully intercepted and passed to `vscode.postMessage` to bypass sandbox restrictions.

### Issue 2: "Selection Menu" (QuickPick) Missing
* **Symptom**: The user noted that upon adding a file, the UI immediately launched the analyzer without presenting a "selection" (choice of actions).
* **Root Cause Analysis**: The backend handler (`handleLocalFileDrop` / `handleDropzoneUpload`) was hardcoded to immediately invoke `child_process.spawn` without consulting the user.
* **Resolution**: Introduced a `vscode.window.showQuickPick` dialog in `VisualVibePanels.ts`. After a file is uploaded, VS Code now prompts the user to select an action (e.g., "🔍 Analyze Image with MiniCPM-V (llama.cpp)"). The terminal only spawns if the user confirms this action.

### Issue 3: Analyzer Script Execution & Pathing
* **Symptom**: Spawning the terminal failed because `analyzer.py` could not be found.
* **Root Cause Analysis**: The script path was resolving relative to the Extension's installation folder (`__dirname` inside `.vscode/extensions/local.vibezoo...`), not the user's workspace.
* **Resolution**: Updated the path resolver to prioritize `vscode.workspace.workspaceFolders[0].uri.fsPath`, ensuring it correctly targets the `mcp-servers/tools/analyzer.py` script living inside the Zoo Code project workspace.

### Final Verification Status
- [x] Vanilla JS Drag and Drop working.
- [x] Browse (Open File) button working.
- [x] Action Selection (QuickPick) appears after successful upload.
- [x] Selecting "Analyze Image" spawns the terminal securely using `child_process.spawn`.
- [x] `analyzer.py` connects correctly to the local `llama.cpp` OpenAI-compatible API on port 8080 and streams Vision output.

### Issue 4: Clear Button Bug & AI Pipeline UX Overhaul
* **Symptom 1**: Clicking the "Clear" button broke subsequent drag-and-drop actions.
* **Root Cause 1**: The `clearDropzone()` function failed to remove the `dragover` class and neglected to reset the newly introduced result UI components, leaving the dropzone in an invalid state.
* **Resolution 1**: Updated `clearDropzone()` to comprehensively reset all CSS classes (including `dragover`) and hide/empty the result box.
* **Symptom 2**: The user correctly pointed out that showing a programming-style "Terminal Command" or QuickPick menu is poor UX for a companion tool. The system should automatically detect the file type and act naturally, reporting results back to the LLM/UI rather than popping up a raw CMD window.
* **Root Cause 2**: The implementation relied on `child_process.spawn` launching a visible CMD window, which breaks immersion and prevents Node.js from capturing the output natively.
* **Resolution 2**: Overhauled the architecture:
  1. Replaced `showQuickPick` with a natural `showInformationMessage` dialog: *"이 파일은 [이미지]입니다. VibeZoo AI를 활용해 분석을 시작할까요?"* based on dynamic regex file extension checking.
  2. Replaced intrusive `child_process.spawn(cmd.exe...)` with silent, background `child_process.exec`.
  3. The Webview UI now dynamically displays a loading spinner ("분석 중...").
  4. Once `analyzer.py` completes, the stdout (result text) is sent directly to the Webview and rendered natively inside a beautiful result box, achieving a seamless "report-back" experience.

*Note: Version bumped to 0.14.2 for cache breaking, but locked per user request.*
