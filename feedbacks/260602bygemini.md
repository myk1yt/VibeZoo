# VibeZoo Dropzone 호출 오류 분석 및 수정 제안 (MCP 도구)

## 📌 문제 현상
LLM이 MCP(Model Context Protocol) 도구를 통해 `open_dropzone` (또는 `open_image_dropzone`)을 호출하면, VS Code 안에 드롭존 웹뷰가 떠야 하지만 뜨지 않는 버그가 발생하고 있습니다.
사용자가 VS Code의 명령 팔레트(Ctrl+Shift+P)를 통해 수동으로 `VibeZoo : 드롭존 띄우는 명령어` (`vibezoo.openDropzone`)를 실행하면 정상적으로 웹뷰가 나타나는 것으로 보아, **VS Code 확장 내의 드롭존 UI 생성 기능은 정상적으로 작동하지만, MCP 서버(Python)와 VS Code 확장(TypeScript) 간의 통신 과정(이벤트 트리거)에 연결이 끊겨 있음**을 시사합니다.

## 🔍 원인 분석 (코드 레벨)

VibeZoo의 MCP 서버(Python)와 VS Code 확장(TypeScript)은 특정 `.json` 파일의 변경(File Watcher)을 통해 이벤트를 주고받는 구조로 설계되어 있습니다.

### 1. VS Code 확장 측 (TypeScript) 수신부 정상
`extension/src/visual/VisualVibePanels.ts` 코드를 살펴보면, 드롭존 이벤트를 수신하기 위해 다음과 같이 `.vibezoo-dropzone-action.json`(`DZ_ACTION_FILE`) 파일을 감시하고 있습니다.

```typescript
// VisualVibePanels.ts (Line 28)
const DZ_ACTION_FILE = () => path.join(os.homedir(), '.vibezoo-dropzone-action.json');

// VisualVibePanels.ts (Line 192~198)
    // ── dropzone-action.json 감시 (open_dropzone MCP 도구) ──
    const dzWatcher = vscode.workspace.createFileSystemWatcher(
      new vscode.RelativePattern(path.dirname(DZ_ACTION_FILE()), path.basename(DZ_ACTION_FILE()))
    );
    
    dzWatcher.onDidChange(async (uri) => {
        // ... (파일을 읽어 action이 'open_dropzone'일 경우) ...
        this.openDropzone(); // <-- 여기서 드롭존 웹뷰를 띄움
    });
```
위 코드를 통해 확장은 `DZ_ACTION_FILE` 파일에 변경이 생기면 이벤트를 트리거하여 `openDropzone()`을 정상 호출할 준비가 되어 있습니다.

### 2. MCP 서버 측 (Python) 송신부 오류
문제는 `mcp-servers/bridge/tools/whiteboard.py` 파일의 `_open_dropzone_in_webview()` 함수에 있었습니다.

```python
# whiteboard.py (Line 815 ~ 827)
def _open_dropzone_in_webview() -> str:
    """VS Code Webview 내장 드롭존 열기 (open_image_dropzone 통합)"""
    from base64 import b64encode
    # ... 중략 ...
    data = {
        "action": "open_dropzone",
        "html_b64": html_b64,
        "title": "VibeZoo Image Drop Zone",
        "timestamp": time.time(),
    }
    
    # ❌ [버그 발생 지점]
    _atomic_write_json(WHITEBOARD_ACTION_FILE, data, indent=2)
```
위 코드를 보면 MCP 도구가 호출되어 데이터를 작성할 때, `DZ_ACTION_FILE`(`.vibezoo-dropzone-action.json`)에 써야 하는데 엉뚱하게도 **`WHITEBOARD_ACTION_FILE`(`.vibezoo-whiteboard-action.json`)에 데이터를 작성**하고 있습니다.

즉, **송신부(Python)는 화이트보드 액션 파일에 편지를 넣었는데, 수신부(TypeScript)는 드롭존 액션 파일의 우체통만 쳐다보고 있어서** 이벤트가 전달되지 않는 상황입니다.

## 🛠 수정 가이드 (코더에게 전달할 내용)

이 문제를 해결하려면 Python 서버 측의 코드 단 한 줄만 수정하면 됩니다.

### 대상 파일
`mcp-servers/bridge/tools/whiteboard.py`

### 변경 내용
`_open_dropzone_in_webview()` 함수 내부 (약 827번째 줄 주변)

**수정 전 (Before):**
```python
    _atomic_write_json(WHITEBOARD_ACTION_FILE, data, indent=2)
```

**수정 후 (After):**
```python
    _atomic_write_json(DZ_ACTION_FILE, data, indent=2)
```
*(참고: 파일 최상단 `import` 영역에서 이미 `bridge.config`로부터 `DZ_ACTION_FILE`이 `import` 되어 있으므로 추가적인 import 작업은 필요 없습니다.)*

이 부분을 변경하신 후 MCP 서버를 재시작하시면, LLM이 드롭존 도구를 호출할 때 `DZ_ACTION_FILE`이 올바르게 갱신되며, VS Code가 이를 정상적으로 감지하여 웹뷰를 성공적으로 띄우게 됩니다.
