# VibeZoo Development Journal

## 2026-06-02: VibeZoo v2 업그레이드 (드랍존 범용화 + PDF 파이프라인 + OCR 전처리)

### Summary
- **실제 사용 피드백 기반 개선** — KOICA CTS PDF 업로드→분석 워크플로우에서 발견된 문제 해결
- **드랍존 범용화** — 이미지+PDF+DOCX+TXT+코드 모든 파일 지원, 확장자 보존 저장 ([`config.py`](mcp-servers/bridge/config.py))
- **PDF 스캔문서 파이프라인** — `_analyze_pdf_as_image()` 신규: fitz→SSA→OCR→MiniCPM 자동 연계 ([`file_analyzer.py`](mcp-servers/bridge/tools/file_analyzer.py))
- **auto_analyze_after_drop 강화** — PDF 파일 `analyze_file()` 직접 호출 ([`ux_coordinator.py`](mcp-servers/bridge/tools/ux_coordinator.py))
- **OCR 전처리** — AdaptiveThresholding + 노이즈 제거로 한글 인식률 향상 ([`ocr_engine.py`](mcp-servers/bridge/ocr_engine.py))
- **설계 문서**: [`plans/vibezoo-v2-upgrade.md`](plans/vibezoo-v2-upgrade.md)
- **GitHub**: 6 files changed, 481 insertions, push 완료 (commit `20b8943`)
- **Cleanup**: `_extract_pdf.py`, `_extract_pdf_v2.py` 삭제

---

## 2026-06-02: UX Workflow 구현 (의도 감지 + 자동 도구 체인)

### Summary
- **신규**: [`intent_detector.py`](../mcp-servers/bridge/intent_detector.py) — 키워드 기반 자연어 의도 감지 모듈 (`file_share`, `drawing_request`, `whiteboard_input`, `code_analysis`, `general_question`)
- **신규**: [`ux_coordinator.py`](../mcp-servers/bridge/tools/ux_coordinator.py) — UX 코디네이터 (3개 도구: `ux_coordinator`, `auto_analyze_after_drop`, `auto_analyze_whiteboard`)
- **수정**: [`tools/__init__.py`](../mcp-servers/bridge/tools/__init__.py), [`whiteboard.py`](../mcp-servers/bridge/tools/whiteboard.py), [`file_analyzer.py`](../mcp-servers/bridge/tools/file_analyzer.py), (v2는 _archive/로 이동)
- **설계 문서**: [`plans/ux-workflow-design.md`](../plans/ux-workflow-design.md)
- **결정 사항**: MiniCPM 우선 사용 (GGUF, llama-cpp-python)
- **GitHub**: 7 files changed, 918 insertions, push 완료
- **도구 수**: 31 → 34

---

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

### Issue 5: Paradigm Shift - Dropzone as a Pure LLM Gateway
* **Symptom**: The extension was autonomously launching analysis tools (`analyzer.py`) and displaying results in a webview. This isolated the LLM (Zoo Code/agy-cli) from the context, violating the core philosophy of VibeZoo where the LLM is the autonomous agent holding the tools.
* **Resolution**: Completely stripped out all hardcoded `child_process.exec`, `showInformationMessage`, and webview `Result Box` logic. The Dropzone now acts strictly as an ingestion gateway. When a file is uploaded, the extension simply saves it and writes a structured prompt (including the file path) to the user's clipboard, instructing them to paste it into the LLM chat. This restores agency to the LLM, allowing it to dynamically ask the user what they want to do with the file (e.g., "This is an image, shall I extract text or build a UI?") and then execute the necessary tools on its own.

*Note: Version bumped to 0.14.1 for cache breaking, but locked per user request.*
