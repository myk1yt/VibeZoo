# VibeZoo Development Journal

## 2026-06-16: Global Auto-Connect Conflict Fix (v0.15.1 Enhancement & Hotfix)

### Summary
- **Root cause**: Removing `autoStart` and `autoStartCommand` caused connection drops on VS Code restarts or opening new workspaces. However, keeping them caused duplicate process spawns and port binding conflicts (`winerror 10048`) because Zoo Code spawned the process while the extension also attempted to spawn/reuse it.
- **Fix strategy**: Keep `autoStart` and `autoStartCommand` templates to let Zoo Code auto-start the bridge. In the extension, implement physical port-level check (`netstat` on Windows and `lsof` on Unix) to identify if the port is physically occupied, and aggressively terminate any duplicate/zombie processes holding port 9027 during health checks and setup phases.

### Tasks Completed

| Task | File | Description |
|------|------|-------------|
| Config Preserve | [`extension/src/mcp/McpConfigService.ts`](extension/src/mcp/McpConfigService.ts) | Restored `autoStart` and `autoStartCommand` keys to default server definitions and stopped deleting them in configuration merging. |
| Spawn cwd & Port Check | [`extension/src/orchestra/SubagentManager.ts`](extension/src/orchestra/SubagentManager.ts) | Set explicit `cwd` parameter on spawn. Added `isPortOccupied()` using `netstat` and `lsof` to physically inspect port 9027, and updated `killBridgeOnPort()` to terminate zombie processes regardless of HTTP health check timeouts. |

### Key Decisions
- **Port-Level Lifetime Guard**: Instead of disabling Zoo Code's autostart mechanism, VibeZoo now safely detects duplicate/zombie runs at the socket port level. This preserves seamless autostart functionality without risking port conflicts.
- **Config Preservation**: Keep `mcp_settings.json` and `.roo/mcp.json` in sync with autostart enabled, allowing the extension to be robust across restarts.

### Files Changed
- **Modified**: [`extension/src/mcp/McpConfigService.ts`](extension/src/mcp/McpConfigService.ts), [`extension/src/orchestra/SubagentManager.ts`](extension/src/orchestra/SubagentManager.ts)

---

## 2026-06-13: Auto-Connect Fundamental Fix (v0.15.0)

### Summary
- **Root cause**: `autoConfigureMCP()` in `extension/src/extension.ts` skipped writing project-level `.roo/mcp.json` when the global Zoo Code MCP config (`mcp_settings.json`) already contained a `vibezoo` entry. On fresh workspaces this prevented Zoo Code from discovering the local VibeZoo Bridge SSE endpoint.
- **Fix strategy**: separate project-level MCP synchronization from global config inspection; global settings are now read-only reference.

### Tasks Completed

| Task | File | Description |
|------|------|-------------|
| Task 4 | [`extension/src/mcp/McpConfigService.ts`](extension/src/mcp/McpConfigService.ts) | New service that always writes `.roo/mcp.json`, preserving other user-defined servers; global MCP config is only read for logging. |
| Task 1 | [`extension/src/python/PythonResolver.ts`](extension/src/python/PythonResolver.ts) | 6-step Python interpreter discovery chain: user setting → `.venv`/`venv` → `pyenv` → `python3` → `python` → `py -3` (Windows). |
| Task 3 | `mcp-servers/` → [`extension/mcp-servers/`](extension/mcp-servers/) | Moved Python bridge and Crow server into the extension directory so they are bundled inside the VSIX. |
| Task 5 | [`extension/src/platform/VscodePaths.ts`](extension/src/platform/VscodePaths.ts) | Cross-platform VS Code config path resolver that distinguishes Stable vs Insiders and handles Windows, macOS, and Linux. |
| Task 2 | [`extension/mcp-servers/crow_memory_server.py`](extension/mcp-servers/crow_memory_server.py) | Replaced the `sys.exit(0)` stub with a real HTTP server that proxies to an external Crow or runs an in-memory fallback. |
| Task 6 | [`extension/src/extension.ts`](extension/src/extension.ts), [`extension/src/safety/SelfCheck.ts`](extension/src/safety/SelfCheck.ts), [`extension/src/ui/StatusBarManager.ts`](extension/src/ui/StatusBarManager.ts) | Removed `trySpawnEarlyBridge()`; added SelfCheck auto-recovery callback that can restart the Bridge and rewrite `.roo/mcp.json`; enhanced status bar with port/error tooltips. |

### Key Decisions
- **Project-level source of truth**: `.roo/mcp.json` is always kept in sync; global `mcp_settings.json` is never modified by VibeZoo.
- **Graceful degradation**: Crow Memory is optional. If the real Crow server is unavailable, the bundled fallback server provides `/health`, `/ingest`, and `/recall` so the Bridge keeps working.
- **Deterministic Python resolution**: No hardcoded `python` assumption; discovery chain covers venv, pyenv, Microsoft Store, and platform differences.
- **VSIX self-contained**: Python assets are now part of the packaged extension, removing the runtime dependency on the workspace root `mcp-servers/` directory.

### Files Changed
- **New**: [`extension/src/mcp/McpConfigService.ts`](extension/src/mcp/McpConfigService.ts)
- **New**: [`extension/src/python/PythonResolver.ts`](extension/src/python/PythonResolver.ts)
- **New**: [`extension/src/platform/VscodePaths.ts`](extension/src/platform/VscodePaths.ts)
- **Moved**: `mcp-servers/**` → [`extension/mcp-servers/**`](extension/mcp-servers/)
- **Modified**: [`extension/src/extension.ts`](extension/src/extension.ts), [`extension/src/orchestra/SubagentManager.ts`](extension/src/orchestra/SubagentManager.ts), [`extension/src/crow/CrowServerManager.ts`](extension/src/crow/CrowServerManager.ts), [`extension/src/safety/SelfCheck.ts`](extension/src/safety/SelfCheck.ts), [`extension/src/ui/StatusBarManager.ts`](extension/src/ui/StatusBarManager.ts), [`extension/.vscodeignore`](extension/.vscodeignore)
- **Replaced**: [`extension/mcp-servers/crow_memory_server.py`](extension/mcp-servers/crow_memory_server.py)

### Documentation Updated
- [`docs/PROJECT_CONTEXT.md`](docs/PROJECT_CONTEXT.md) — architecture diagram, module map, resolved issues, date
- [`fromscratch/CHANGELOG.md`](fromscratch/CHANGELOG.md) — v0.15.0 entry
- [`fromscratch/RELEASENOTES.md`](fromscratch/RELEASENOTES.md) — v0.15.0 release notes
- [`README.md`](README.md) — auto-connect description and history

---

## 2026-06-03: 3-Engine Parallel Web Search

### Summary
- **Architecture Redesign**: Completely replaced the faulty SearxNG dependency with a new robust 3-Engine Parallel Search architecture.
- **Engines**: Integrated duckduckgo-search (AsyncDDGS), googlesearch-python (Threaded), and Yahoo Search (aiohttp + BeautifulSoup).
- **Concurrency**: Utilized syncio.gather() for parallel execution and aggregated, deduplicated results into clean Markdown.
- **Files Modified**: mcp-servers/web_search.py, README.md, mcp-servers/bridge/tools/web.py.
- **Cleanup**: Removed all SearxNG references.

---


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

---

## 2026-06-02: Dropzone 세션 인식 + PDF SSA 분석 제거

### Summary
- **버그 발견**: `check_uploaded_files()`가 이전 세션의 모든 업로드를 보여주고, PDF 문서에 SSA(이미지 공간 분석)가 실행됨
- **Bug 1 수정 — 세션 인식 드롭존**:
  - [`config.py`](mcp-servers/bridge/config.py): `DZ_SESSION_FILE` 상수 추가
  - [`whiteboard.py`](mcp-servers/bridge/tools/whiteboard.py): `_open_dropzone_in_webview()`에서 드롭존 오픈 시 `dz_session.json`에 `started_at` 타임스탬프 기록
  - [`whiteboard.py`](mcp-servers/bridge/tools/whiteboard.py): `check_uploaded_files()`에서 세션 이후 업로드만 필터링 (JS ms → Python s 변환)
- **Bug 2 수정 — PDF SSA 제거**:
  - [`file_analyzer.py`](mcp-servers/bridge/tools/file_analyzer.py): `_analyze_pdf_as_image()`에서 SSA 블록 19줄 완전 제거, OCR + MiniCPM-V는 유지
- **Bug 3 수정 — MCP 브릿지 데드락 해결**:
  - [`SubagentManager.ts`](extension/src/orchestra/SubagentManager.ts): 파이프 버퍼가 가득 차 서버가 멈추는 데드락을 방지하기 위해 `stdio` 설정을 `['ignore', 'pipe', 'pipe']`에서 `'ignore'`로 변경하여 VSCode Reload 시 VibeZoo 무한 대기 문제 영구 해결
- **Feature 추가**:
  - [`vibezoo_mcp_bridge.py`](mcp-servers/vibezoo_mcp_bridge.py): Dropzone 웹 UI에 클립보드 이미지 복사/붙여넣기(Ctrl+V) 기능 추가
  - [`.zoo/subagents_config.json`](.zoo/subagents_config.json): 분업화된 서브에이전트(Architect, Code, Debugger, MCP_Expert) 설정 영구 저장 파일 추가
- **워크플로우**: Research → Architect → Code → Debug → Git commit/push → VSIX rebuild → Local reinstall
- **GitHub**: 3 files changed, 41 insertions, 25 deletions, commit `90016d8`, tag `v0.14.2`

## 2026-06-03: VibeZoo Autonomous Master Plan

### Summary
- **Feature 추가 — SearxNG WebSearch**:
  - [web_search.py](mcp-servers/web_search.py): SearxNG 연동 및 에러 시 자동 Fallback 로직 추가 (MCP 도구로 등록)
- **Feature 추가 — LLM 자가 피드백 루프**:
  - [eedback.py](mcp-servers/bridge/tools/feedback.py): 반복 작업이나 불편 사항을 utonomous_agent_suggestions.jsonl에 스스로 기록하는 텔레메트리 도구 추가
- **Feature 추가 — Agent.md (자율 행동 프로토콜)**:
  - [.zoo/Agent.md](.zoo/Agent.md): LLM이 하드코딩 없이 VibeZoo 도구를 최우선 사용하고, 실패 시 자율 디버깅을 수행하도록 강제하는 핵심 프롬프트 규칙 제정
- **Feature 추가 — Universal UX Bootstrapper**:
  - init_vibezoo.bat, init_vibezoo.sh, README.md 가이드라인을 통해 GitHub 클론 시 즉각 환경 구성 지원
- **GitHub**: Tag 0.14.2 release.

# #   2 0 2 6 - 0 6 - 0 3 :   Q u a d - C o r e   A s y n c   S e a r c h   E n g i n e   A r c h i t e c t u r e  
  
 # # #   S u m m a r y  
 -   * * F e a t u r e   � �     W e b S e a r c h   Ѽ,�  ����  �ĳT�* * :  
     -   ` w e b _ s e a r c h . p y ` :   0�t�  3 - E n g i n e   )���D�  ` c u r l _ c f f i ` ( �ƌ�  1���  ����)   �  ` s e l e c t o l a x ` + ` h t t p x ` ( ଍�  ���)   0��X�  * * Q u a d - C o r e   A s y n c   S e a r c h   E n g i n e * *   DŤ�Mј�\�  ��)Ӡ���.  
     -   ` n o d r i v e r `   �  ` t w s c r a p e ` ��  H��1�/ Ĭ�  �ȍ�1�  8��\�  D�0���  �Ĭ���  �p�.  
     -   ` a s y n c i o . g a t h e r ` |�  ����\�  Ѽ,�  �̬�\�  Q���  ��ĳ  �  ����  ���  �p�  \���  �T�.  
 -   * * X�t�1�  ��p�tǸ�* * :   ` c u r l _ c f f i ` ,   ` s e l e c t o l a x ` ,   ` h t t p x `   \���  Xֽ�  $�X�  D�̸.  
 -   * * 8��T�* * :   ` R E A D M E . m d ` X�  1 . 0   9�X�D�  ��  DŤ�Mј�  ����<�\�  \���T�.  
 