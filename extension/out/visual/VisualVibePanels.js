"use strict";
// VibeZoo Wave 5: Visual Vibe 통합 패널
// Whiteboard, UI Preview, Diagram 등 Webview 패널 생성
// AI가 MCP 도구(draw_on_whiteboard, open_whiteboard)를 호출하면
// 파일 감시를 통해 자동으로 패널을 열고 그림을 렌더링한다.
//
// ★ 2026-06-01: P0-Critical 버그 수정
//   - BUG FIX: fs.watchFile(poll) → fs.watch(OS native) 교체
//   - BUG FIX: handleFileChange async 제거, readFileSync 사용
//   - BUG FIX: _fallbackWatchFile 폴백 메서드 추가
//   - fs.watch 실패 시 fs.watchFile로 fallback
// ★ 2026-05-27: 버그 수정 + 리팩토링
//   - BUG FIX: handleFileChange mtime 이중 검사로 파일 읽기 안 되던 버그 수정
//   - BUG FIX: acquireVsCodeApi() 중복 호출 → 1회로 통일
//   - BUG FIX: sendState 디바운스 처리 (연속 호출 병합)
//   - BUG FIX: 리사이즈 이벤트 디바운스 처리
//   - BUG FIX: Fabric.js CDN fallback 처리
//   - BUG FIX: (this as any) 타입 단언 → 정식 프로퍼티로 변경
//   - REFACTOR: 중복 이미지 로딩 코드 → addImageToCanvas() 유틸 함수
//   - REFACTOR: 상수 추출 (파일 경로, CDN URL, 타임아웃 값)
//   - REFACTOR: DrawCommand 타입 정의로 타입 안전성 개선
//   - REFACTOR: onDidReceiveMessage if 체인 → else if / switch 정리
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.VisualVibePanels = void 0;
const vscode = __importStar(require("vscode"));
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const os = __importStar(require("os"));
const child_process_1 = require("child_process");
// ── 상수 ──────────────────────────────────────────────────
const WB_FILE = () => path.join(os.homedir(), '.vibezoo-whiteboard.json');
const WB_ACTION_FILE = () => path.join(os.homedir(), '.vibezoo-whiteboard-action.json');
const UI_ACTION_FILE = () => path.join(os.homedir(), '.vibezoo-ui-action.json');
const FABRIC_CDN = 'https://cdnjs.cloudflare.com/ajax/libs/fabric.js/5.3.1/fabric.min.js';
const MERMAID_CDN = 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js';
const WATCH_INTERVAL_MS = 500;
const STATE_DEBOUNCE_MS = 300;
const RESIZE_DEBOUNCE_MS = 100;
const CAPTURE_READ_DELAY_MS = 500;
const CAPTURE_TIMEOUT_MS = 60000;
const UI_PREVIEW_FALLBACK_MS = 600;
const IMAGE_MAX_WIDTH = 600;
const IMAGE_SCALE_FACTOR = 0.8;
const log = (msg, ...args) => {
    if (process.env.VIBEZOO_DEBUG)
        console.log(`[VibeZoo::Visual] ${msg}`, ...args);
};
// ── 유틸 ──────────────────────────────────────────────────
function debounce(fn, delay) {
    let timer = null;
    const debounced = (...args) => {
        if (timer !== null)
            clearTimeout(timer);
        timer = setTimeout(() => {
            timer = null;
            fn(...args);
        }, delay);
    };
    return debounced;
}
// ── 메인 클래스 ────────────────────────────────────────────
class VisualVibePanels {
    whiteboardPanel = null;
    uiPreviewPanel = null;
    diagramPanel = null;
    homedir;
    _activated = false;
    _watching = false;
    _watchers = [];
    _lastCommandsHash = '';
    /** Whiteboard가 아직 열리지 않았을 때 대기 중인 드로잉 명령 */
    _pendingDrawCommands = null;
    constructor() {
        this.homedir = os.homedir();
    }
    // ── 수명주기 ──────────────────────────────────────────────
    activate() {
        if (this._activated)
            return;
        this._activated = true;
        this.startWatching();
        log('VisualVibePanels activated (watching started)');
    }
    dispose() {
        this.stopWatching();
        this.whiteboardPanel?.dispose();
        this.uiPreviewPanel?.dispose();
        this.diagramPanel?.dispose();
    }
    // ── 파일 감시 ─────────────────────────────────────────────
    /**
     * action 파일의 변경을 감지하여 콜백 실행.
     * @param filePath 감시할 파일 경로
     * @param _lastMtime 마지막 mtime 기록 (객체 참조로 유지) — fallback watchFile에서 사용
     * @param onChange 파일 내용이 변경되었을 때 실행할 콜백
     */
    handleFileChange(filePath, _lastMtime, onChange) {
        try {
            const contentStr = fs.readFileSync(filePath, 'utf-8');
            const content = JSON.parse(contentStr);
            onChange(content);
        }
        catch {
            // 파일이 아직 없거나 읽을 수 없음 — 무시
        }
    }
    /** 현재 파일의 mtime 반환 (없으면 0) */
    getCurrentMtime(filePath) {
        try {
            return fs.statSync(filePath).mtimeMs;
        }
        catch {
            return 0;
        }
    }
    /**
     * 파일 감시 시작 (fs.watch 기반).
     * activate()에서 최초 1회 호출.
     */
    startWatching() {
        if (this._watching)
            return;
        this._watching = true;
        const wbFile = WB_FILE();
        const wbAction = WB_ACTION_FILE();
        const uiAction = UI_ACTION_FILE();
        // 디바운스 타이머들
        let wbTimer = null;
        let actionTimer = null;
        let uiTimer = null;
        // 공통 감시 헬퍼
        const watchFile = (filePath, onChange, debounceMs = 300) => {
            try {
                const dir = path.dirname(filePath);
                const basename = path.basename(filePath);
                const watcher = fs.watch(dir, { persistent: false }, (eventType, filename) => {
                    if (filename !== basename)
                        return;
                    if (eventType !== 'change' && eventType !== 'rename')
                        return;
                    // 디바운스
                    if (filePath === wbFile && wbTimer)
                        clearTimeout(wbTimer);
                    if (filePath === wbAction && actionTimer)
                        clearTimeout(actionTimer);
                    if (filePath === uiAction && uiTimer)
                        clearTimeout(uiTimer);
                    const timer = setTimeout(() => {
                        this.handleFileChange(filePath, { current: 0 }, onChange);
                    }, debounceMs);
                    if (filePath === wbFile)
                        wbTimer = timer;
                    else if (filePath === wbAction)
                        actionTimer = timer;
                    else if (filePath === uiAction)
                        uiTimer = timer;
                });
                watcher.on('error', () => {
                    this._fallbackWatchFile(filePath, onChange);
                });
                this._watchers.push(watcher);
            }
            catch {
                this._fallbackWatchFile(filePath, onChange);
            }
        };
        // action 파일 감시
        watchFile(wbAction, (content) => {
            if (content.action === 'open') {
                this.openWhiteboard();
            }
        });
        // UI action 파일 감시
        watchFile(uiAction, (content) => {
            if (content.action === 'open_ui') {
                this.openUIPreview(content.code || '', content.framework || 'react');
            }
        });
        // whiteboard.json 감시
        watchFile(wbFile, (content) => {
            if (content._source === 'canvasState')
                return;
            if (!content.commands || content.commands.length === 0)
                return;
            const hash = JSON.stringify(content.commands);
            if (hash === this._lastCommandsHash)
                return;
            this._lastCommandsHash = hash;
            if (!this.whiteboardPanel) {
                this.openWhiteboard();
                this._pendingDrawCommands = content.commands;
            }
            else {
                this.sendToWhiteboard(content.commands);
            }
        });
        log('File watching started (fs.watch)');
    }
    /** 파일 감시 중단 */
    stopWatching() {
        if (!this._watching)
            return;
        for (const w of this._watchers) {
            try {
                w.close();
            }
            catch { /* ignore */ }
        }
        this._watchers = [];
        try {
            fs.unwatchFile(WB_FILE());
        }
        catch { /* ignore */ }
        try {
            fs.unwatchFile(WB_ACTION_FILE());
        }
        catch { /* ignore */ }
        try {
            fs.unwatchFile(UI_ACTION_FILE());
        }
        catch { /* ignore */ }
        this._watching = false;
        log('File watching stopped');
    }
    /** fs.watch 실패 시 fs.watchFile로 폴백 */
    _fallbackWatchFile(filePath, onChange) {
        const lastMtime = { current: this.getCurrentMtime(filePath) };
        fs.watchFile(filePath, { interval: WATCH_INTERVAL_MS }, (curr) => {
            if (curr.mtimeMs <= lastMtime.current)
                return;
            lastMtime.current = curr.mtimeMs;
            this.handleFileChange(filePath, lastMtime, onChange);
        });
    }
    // ── Whiteboard ───────────────────────────────────────────
    /** AI 드로잉 명령을 Whiteboard Webview로 전달 */
    sendToWhiteboard(commands) {
        if (this.whiteboardPanel) {
            this.whiteboardPanel.webview.postMessage({ type: 'draw', commands });
        }
    }
    /** Whiteboard 열기 — Fabric.js 기반 드로잉 캔버스 */
    openWhiteboard() {
        this.startWatching();
        if (this.whiteboardPanel) {
            this.whiteboardPanel.reveal(vscode.ViewColumn.Two);
            return this.whiteboardPanel;
        }
        this.whiteboardPanel = vscode.window.createWebviewPanel('vibezoo-whiteboard', '🎨 VibeZoo Whiteboard', vscode.ViewColumn.Two, { enableScripts: true, retainContextWhenHidden: true });
        this.whiteboardPanel.webview.html = this.whiteboardHtml();
        this.whiteboardPanel.webview.onDidReceiveMessage((message) => {
            switch (message.type) {
                case 'canvasState':
                    this.handleCanvasState(message.commands);
                    break;
                case 'captureScreenshot':
                    this.handleCaptureScreenshot();
                    break;
                case 'ready':
                    if (this._pendingDrawCommands) {
                        this.sendToWhiteboard(this._pendingDrawCommands);
                        this._pendingDrawCommands = null;
                    }
                    break;
            }
        });
        this.whiteboardPanel.onDidDispose(() => { this.whiteboardPanel = null; });
        return this.whiteboardPanel;
    }
    /** 사용자 캔버스 상태 저장 (무한 루프 방지를 위해 _source 마커 포함) */
    handleCanvasState(commands) {
        const data = {
            _source: 'canvasState',
            timestamp: Date.now(),
            commands,
        };
        try {
            fs.writeFileSync(WB_FILE(), JSON.stringify(data, null, 2), 'utf-8');
        }
        catch { /* ignore */ }
    }
    /** 캡처 도구 실행 → 클립보드 이미지를 Whiteboard에 자동 로드 */
    handleCaptureScreenshot() {
        const tmpFile = path.join(os.tmpdir(), `vibezoo-capture-${Date.now()}.png`);
        const openCaptureTool = process.platform === 'win32'
            ? `powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; Start-Process ms-screenclip: -Wait -WindowStyle Hidden; $img = [System.Windows.Forms.Clipboard]::GetImage(); if ($img) { $img.Save('${tmpFile}', [System.Drawing.Imaging.ImageFormat]::Png) }"`
            : process.platform === 'darwin'
                ? `screencapture -i -c "${tmpFile}" 2>/dev/null; osascript -e 'tell app "System Events" to set theImage to the clipboard as «class PNGf»' -e 'if theImage is not missing value then set imgFile to open for access "${tmpFile}" with write permission' -e 'write theImage to imgFile' -e 'close access imgFile'`
                : null;
        if (!openCaptureTool) {
            log('Capture not supported on this platform');
            return;
        }
        (0, child_process_1.exec)(openCaptureTool, { timeout: CAPTURE_TIMEOUT_MS }, (err) => {
            if (err) {
                log('Capture tool error:', err.message);
                this.cleanupTempFile(tmpFile);
                return;
            }
            setTimeout(() => {
                try {
                    if (fs.existsSync(tmpFile) && fs.statSync(tmpFile).size > 0) {
                        const imgData = fs.readFileSync(tmpFile, 'base64');
                        this.cleanupTempFile(tmpFile);
                        this.whiteboardPanel?.webview.postMessage({
                            type: 'loadLatestScreenshot',
                            dataUrl: `data:image/png;base64,${imgData}`,
                        });
                    }
                    else {
                        this.cleanupTempFile(tmpFile);
                    }
                }
                catch (e) {
                    log('Capture read error:', e.message);
                    this.cleanupTempFile(tmpFile);
                }
            }, CAPTURE_READ_DELAY_MS);
        });
    }
    cleanupTempFile(filePath) {
        try {
            if (fs.existsSync(filePath))
                fs.unlinkSync(filePath);
        }
        catch { /* ignore */ }
    }
    // ── UI Preview ───────────────────────────────────────────
    openUIPreview(initialCode, _framework) {
        if (this.uiPreviewPanel) {
            this.uiPreviewPanel.reveal(vscode.ViewColumn.Two);
            if (initialCode) {
                this.uiPreviewPanel.webview.postMessage({ type: 'render', code: initialCode });
            }
            return this.uiPreviewPanel;
        }
        this.uiPreviewPanel = vscode.window.createWebviewPanel('vibezoo-ui-preview', '🖼️ VibeZoo UI Preview', vscode.ViewColumn.Two, { enableScripts: true, retainContextWhenHidden: true });
        this.uiPreviewPanel.webview.html = this.uiPreviewHtml();
        this.uiPreviewPanel.onDidDispose(() => { this.uiPreviewPanel = null; });
        // Webview 로드 완료 후 초기 코드 전송 (중복 방지)
        if (initialCode) {
            const panel = this.uiPreviewPanel;
            let sent = false;
            const onReady = (msg) => {
                if (msg.type === 'ready' && !sent) {
                    sent = true;
                    panel.webview.postMessage({ type: 'render', code: initialCode });
                }
            };
            panel.webview.onDidReceiveMessage(onReady);
            // fallback: ready 신호가 없어도 600ms 후 전송
            setTimeout(() => {
                if (!sent) {
                    sent = true;
                    try {
                        panel.webview.postMessage({ type: 'render', code: initialCode });
                    }
                    catch { /* ignore */ }
                }
            }, UI_PREVIEW_FALLBACK_MS);
        }
        return this.uiPreviewPanel;
    }
    // ── Diagram ──────────────────────────────────────────────
    openDiagram(diagramType) {
        if (this.diagramPanel) {
            this.diagramPanel.reveal(vscode.ViewColumn.Two);
            return this.diagramPanel;
        }
        this.diagramPanel = vscode.window.createWebviewPanel('vibezoo-diagram', '📊 VibeZoo Diagram', vscode.ViewColumn.Two, { enableScripts: true, retainContextWhenHidden: true });
        this.diagramPanel.webview.html = this.diagramHtml(diagramType);
        this.diagramPanel.onDidDispose(() => { this.diagramPanel = null; });
        return this.diagramPanel;
    }
    // ── HTML 템플릿 ──────────────────────────────────────────
    whiteboardHtml() {
        return `<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { overflow: hidden; background: #1e1e1e; }
  #toolbar { position: fixed; top: 10px; left: 10px; z-index: 10; display: flex; gap: 6px; }
  #toolbar button { padding: 6px 12px; background: #3c3c3c; color: #ccc; border: 1px solid #555; border-radius: 4px; cursor: pointer; }
  #toolbar button:hover { background: #505050; }
  #error-overlay { display: none; position: fixed; inset: 0; z-index: 100; background: #1e1e1e; color: #f44747; justify-content: center; align-items: center; flex-direction: column; gap: 12px; font-family: sans-serif; }
  #error-overlay.show { display: flex; }
  canvas { display: block; }
</style>
<script src="${FABRIC_CDN}"
  onerror="document.getElementById('error-overlay').classList.add('show');">
</script>
</head><body>
<div id="error-overlay">
  <h2>⚠️ Fabric.js를 불러올 수 없습니다</h2>
  <p>인터넷 연결을 확인하거나 CDN이 차단되지 않았는지 확인하세요.</p>
</div>
<div id="toolbar">
  <button onclick="setMode('draw')">✏️ 그리기</button>
  <button onclick="setMode('rect')">⬜ 사각형</button>
  <button onclick="setMode('text')">📝 텍스트</button>
  <button onclick="setMode('select')">🖱️ 선택</button>
  <button onclick="captureScreenshot()">📸 캡처</button>
  <button onclick="document.getElementById('imgInput').click()">📷 이미지</button>
  <button onclick="deleteSelected()">🗑️ 선택 삭제</button>
  <button onclick="clearAll()">🧹 전체 삭제</button>
  <input type="file" id="imgInput" accept="image/*" style="display:none" onchange="addImage(this)">
</div>
<canvas id="c"></canvas>
<script>
  // acquireVsCodeApi는 최초 1회만 호출
  var vscode = typeof acquireVsCodeApi !== 'undefined' ? acquireVsCodeApi() : null;

  var canvas = new fabric.Canvas('c', {
    isDrawingMode: true,
    width: window.innerWidth,
    height: window.innerHeight,
    backgroundColor: '#1e1e1e',
  });
  canvas.freeDrawingBrush.color = '#ffffff';
  canvas.freeDrawingBrush.width = 3;

  // ── 디바운스 유틸 ──
  function debounce(fn, delay) {
    var timer = null;
    return function() {
      var args = arguments;
      var ctx = this;
      if (timer) clearTimeout(timer);
      timer = setTimeout(function() {
        timer = null;
        fn.apply(ctx, args);
      }, delay);
    };
  }

  // ── 상태 저장 (디바운스 적용) ──
  function sendState() {
    if (!vscode) return;
    var state = canvas.toJSON ? canvas.toJSON() : { objects: [] };
    vscode.postMessage({ type: 'canvasState', commands: state.objects || [] });
  }
  var sendStateDebounced = debounce(sendState, ${STATE_DEBOUNCE_MS});

  canvas.on('object:added', sendStateDebounced);
  canvas.on('object:modified', sendStateDebounced);
  canvas.on('object:removed', sendStateDebounced);
  // ── 공통 이미지 추가 함수 ──
  function addImageToCanvas(url) {
    fabric.Image.fromURL(url, function(img) {
      img.set({ left: 50, top: 50 });
      img.scaleToWidth(Math.min(canvas.width * ${IMAGE_SCALE_FACTOR}, ${IMAGE_MAX_WIDTH}));
      canvas.add(img);
      canvas.renderAll();
      sendStateDebounced();
    });
  }

  // ── 캡처 ──
  function captureScreenshot() {
    if (vscode) vscode.postMessage({ type: 'captureScreenshot' });
  }

  // ── AI Draw 명령 처리 ──
  function executeCommands(commands) {
    if (!commands || !Array.isArray(commands)) return;
    var needsRender = false;
    commands.forEach(function(cmd) {
      if (!cmd || !cmd.type) return;
      var props = cmd.props || {};
      switch (cmd.type) {
        case 'polygon': {
          var pts = (props.points || []).map(function(p) { return new fabric.Point(p.x, p.y); });
          if (pts.length < 3) break;
          canvas.add(new fabric.Polygon(pts, {
            fill: props.fill || 'transparent',
            stroke: props.stroke || '#ff6b6b',
            strokeWidth: props.strokeWidth || 2,
            left: props.left || 0,
            top: props.top || 0,
            objectCaching: false,
          }));
          needsRender = true;
          break;
        }
        case 'rect': {
          canvas.add(new fabric.Rect({
            left: props.left || 100,
            top: props.top || 100,
            width: props.width || 200,
            height: props.height || 150,
            fill: props.fill || 'transparent',
            stroke: props.stroke || '#4ec9ff',
            strokeWidth: props.strokeWidth || 2,
            rx: props.rx || 0,
            ry: props.ry || 0,
          }));
          needsRender = true;
          break;
        }
        case 'circle': {
          canvas.add(new fabric.Circle({
            left: props.left || 100,
            top: props.top || 100,
            radius: props.radius || 80,
            fill: props.fill || 'transparent',
            stroke: props.stroke || '#ffd700',
            strokeWidth: props.strokeWidth || 2,
          }));
          needsRender = true;
          break;
        }
        case 'line': {
          canvas.add(new fabric.Line(
            [props.x1 || 0, props.y1 || 0, props.x2 || 200, props.y2 || 200],
            {
              left: props.left || 0,
              top: props.top || 0,
              stroke: props.stroke || '#ffffff',
              strokeWidth: props.strokeWidth || 2,
            }
          ));
          needsRender = true;
          break;
        }
        case 'text': {
          canvas.add(new fabric.Textbox(props.text || '텍스트', {
            left: props.left || 100,
            top: props.top || 100,
            width: props.width || 300,
            fontSize: props.fontSize || 20,
            fill: props.fill || '#ffffff',
            fontFamily: props.fontFamily || 'sans-serif',
          }));
          needsRender = true;
          break;
        }
        case 'arrow': {
          var x1 = props.x1 || 0, y1 = props.y1 || 0;
          var x2 = props.x2 || 200, y2 = props.y2 || 200;
          var arrColor = props.stroke || '#ffffff';
          var arrWidth = props.strokeWidth || 2;
          canvas.add(new fabric.Line([x1, y1, x2, y2], {
            left: props.left || 0,
            top: props.top || 0,
            stroke: arrColor,
            strokeWidth: arrWidth,
          }));
          var angle = Math.atan2(y2 - y1, x2 - x1);
          var headLen = 15;
          var headPts = [
            { x: x2, y: y2 },
            { x: x2 - headLen * Math.cos(angle - Math.PI/6), y: y2 - headLen * Math.sin(angle - Math.PI/6) },
            { x: x2 - headLen * Math.cos(angle + Math.PI/6), y: y2 - headLen * Math.sin(angle + Math.PI/6) },
          ];
          canvas.add(new fabric.Polygon(headPts.map(function(p) { return new fabric.Point(p.x, p.y); }), {
            fill: arrColor,
            stroke: arrColor,
            strokeWidth: 1,
            objectCaching: false,
          }));
          needsRender = true;
          break;
        }
        case 'freehand': {
          if (props.path) {
            canvas.add(new fabric.Path(props.path, {
              left: props.left || 0,
              top: props.top || 0,
              stroke: props.stroke || '#ffffff',
              strokeWidth: props.strokeWidth || 3,
              fill: null,
            }));
            needsRender = true;
          }
          break;
        }
        case 'clear': {
          canvas.clear();
          canvas.backgroundColor = '#1e1e1e';
          needsRender = true;
          break;
        }
        case 'image': {
          if (props.url) {
            addImageToCanvas(props.url);
          }
          break;
        }
      }
    });
    if (needsRender) {
      canvas.renderAll();
      sendStateDebounced();
    }
  }

  // Webview 로드 완료 → Extension에 ready 신호 전송
  if (vscode) vscode.postMessage({ type: 'ready' });

  // ── Extension → Webview 메시지 처리 ──
  window.addEventListener('message', function(e) {
    if (e.data && e.data.type === 'draw' && e.data.commands) {
      executeCommands(e.data.commands);
      return;
    }
    if (e.data && e.data.type === 'loadLatestScreenshot' && e.data.dataUrl) {
      addImageToCanvas(e.data.dataUrl);
    }
  });

  // ── 파일 선택으로 이미지 추가 ──
  function addImage(input) {
    var file = input.files[0];
    if (!file) return;
    var reader = new FileReader();
    reader.onload = function(ev) {
      addImageToCanvas(ev.target.result);
    };
    reader.readAsDataURL(file);
    input.value = '';
  }

  // ── Ctrl+V 이미지 붙여넣기 ──
  document.addEventListener('paste', function(e) {
    var items = e.clipboardData && e.clipboardData.items;
    if (!items) return;
    for (var i = 0; i < items.length; i++) {
      var item = items[i];
      if (item.type.startsWith('image/')) {
        var blob = item.getAsFile();
        if (!blob) continue;
        var reader = new FileReader();
        reader.onload = function(ev) {
          addImageToCanvas(ev.target.result);
        };
        reader.readAsDataURL(blob);
        break;
      }
    }
  });

  // ── 모드 설정 ──
  function setMode(mode) {
    switch (mode) {
      case 'draw': canvas.isDrawingMode = true; break;
      case 'rect': canvas.isDrawingMode = false; addRect(); break;
      case 'text': canvas.isDrawingMode = false; addText(); break;
      case 'select': canvas.isDrawingMode = false; break;
    }
  }

  function addRect() {
    canvas.add(new fabric.Rect({ left: 100, top: 100, width: 200, height: 150, fill: 'transparent', stroke: '#4ec9ff', strokeWidth: 2 }));
  }

  function addText() {
    canvas.add(new fabric.Textbox('텍스트 입력', { left: 100, top: 100, width: 300, fontSize: 20, fill: '#ffffff', fontFamily: 'sans-serif' }));
  }

  function deleteSelected() {
    var active = canvas.getActiveObject();
    if (active) {
      canvas.remove(active);
      canvas.discardActiveObject();
      canvas.renderAll();
      sendStateDebounced();
    }
  }

  function clearAll() {
    canvas.clear();
    canvas.backgroundColor = '#1e1e1e';
    sendStateDebounced();
  }

  // Delete / Backspace 키
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Delete' || e.key === 'Backspace') {
      deleteSelected();
    }
  });

  // 리사이즈 (디바운스 적용)
  window.addEventListener('resize', debounce(function() {
    canvas.setWidth(window.innerWidth);
    canvas.setHeight(window.innerHeight);
  }, ${RESIZE_DEBOUNCE_MS}));
</script>
</body></html>`;
    }
    uiPreviewHtml() {
        return `<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: var(--vscode-editor-background, #1e1e1e); color: var(--vscode-foreground, #ccc); font-family: sans-serif; padding: 20px; }
  .placeholder { text-align: center; padding: 60px 20px; color: #888; }
  .placeholder h2 { margin-bottom: 12px; color: #ccc; }
  iframe { width: 100%; height: 90vh; border: 1px solid #444; border-radius: 8px; background: #fff; }
</style>
</head><body>
<div class="placeholder">
  <h2>🖼️ VibeZoo UI Preview</h2>
  <p>AI가 React/Vue 컴포넌트 코드를 생성하면 이곳에 실시간 렌더링됩니다.</p>
</div>
<script>
  var vscode = typeof acquireVsCodeApi !== 'undefined' ? acquireVsCodeApi() : null;
  if (vscode) vscode.postMessage({ type: 'ready' });

  window.addEventListener('message', function(event) {
    if (event.data.type === 'render' && event.data.code) {
      // HTML 엔티티 이스케이프 (srcdoc 속성용)
      var code = event.data.code;
      code = code.replace(/&/g, '&');
      code = code.replace(/"/g, '"');
      code = code.replace(/</g, '<');
      code = code.replace(/>/g, '>');
      document.body.innerHTML = '<iframe sandbox="allow-scripts" srcdoc="' + code + '"></iframe>';
    }
  });
</script>
</body></html>`;
    }
    diagramHtml(diagramType) {
        return `<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: #1e1e1e; color: #ccc; font-family: sans-serif; padding: 20px; }
  #diagram { width: 100%; min-height: 80vh; }
</style>
<script src="${MERMAID_CDN}"></script>
</head><body>
<div class="placeholder">
  <h2>📊 VibeZoo Diagram${diagramType ? ': ' + diagramType : ''}</h2>
  <div id="diagram"></div>
</div>
<script>
  mermaid.initialize({ startOnLoad: false, theme: 'dark' });
  var mermaidRenderId = 0;
  window.addEventListener('message', async function(event) {
    if (event.data.type === 'render' && event.data.mermaidCode) {
      var container = document.getElementById('diagram');
      container.innerHTML = '';
      var uniqueId = 'mermaid-diagram-' + (++mermaidRenderId);
      try {
        var result = await mermaid.render(uniqueId, event.data.mermaidCode);
        container.innerHTML = result.svg;
      } catch (err) {
        container.innerHTML = '<p style="color:#f44747">Mermaid 렌더링 오류: ' + (err.message || String(err)) + '</p>';
      }
    }
  });
</script>
</body></html>`;
    }
}
exports.VisualVibePanels = VisualVibePanels;
//# sourceMappingURL=VisualVibePanels.js.map