"use strict";
// VibeZoo Wave 5: Visual Vibe 통합 패널
// Whiteboard, UI Preview, Diagram 등 Webview 패널 생성
// AI가 MCP 도구(draw_on_whiteboard, open_whiteboard)를 호출하면
// 파일 감시를 통해 자동으로 패널을 열고 그림을 렌더링한다.
//
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
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
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
const DZ_ACTION_FILE = () => path.join(os.homedir(), '.vibezoo-dropzone-action.json');
const CHAT_PENDING_FILE = () => path.join(os.homedir(), '.vibezoo-chat-pending.json');
const getDateString = () => {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
};
const DROPZONE_CACHE_DIR = () => path.join(os.homedir(), '.vibezoo-uploads', getDateString());
const UPLOADED_IMAGE_PATH = () => path.join(DROPZONE_CACHE_DIR(), 'dropped_image.png');
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
    dropzonePanel = null;
    homedir;
    _activated = false;
    _watching = false;
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
        this.dropzonePanel?.dispose();
    }
    // ── 파일 감시 ─────────────────────────────────────────────
    /**
     * action 파일의 변경을 감지하여 콜백 실행.
     * @param filePath 감시할 파일 경로
     * @param lastMtime 마지막 mtime 기록 (객체 참조로 유지)
     * @param onChange 파일 내용이 변경되었을 때 실행할 콜백
     */
    async handleFileChange(filePath, lastMtime, onChange, retries = 5) {
        try {
            if (!fs.existsSync(filePath))
                return;
            const stat = fs.statSync(filePath);
            if (stat.mtimeMs <= lastMtime.current && retries === 5)
                return;
            const contentStr = await fs.promises.readFile(filePath, 'utf-8');
            const content = JSON.parse(contentStr);
            lastMtime.current = stat.mtimeMs;
            onChange(content);
        }
        catch (err) {
            if (retries > 0) {
                setTimeout(() => this.handleFileChange(filePath, lastMtime, onChange, retries - 1), 200);
            }
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
     * 파일 감시 시작 (fs.watchFile 기반).
     * activate()에서 최초 1회 호출.
     */
    startWatching() {
        if (this._watching)
            return;
        this._watching = true;
        const wbFile = WB_FILE();
        const wbAction = WB_ACTION_FILE();
        const uiAction = UI_ACTION_FILE();
        const dzAction = DZ_ACTION_FILE();
        const lastWbMtime = { current: this.getCurrentMtime(wbFile) };
        const lastActionMtime = { current: this.getCurrentMtime(wbAction) };
        const lastUiMtime = { current: this.getCurrentMtime(uiAction) };
        const lastDzMtime = { current: this.getCurrentMtime(dzAction) };
        // ── whiteboard-action.json 감시 (open_whiteboard MCP 도구) ──
        fs.watchFile(wbAction, { interval: WATCH_INTERVAL_MS }, () => {
            this.handleFileChange(wbAction, lastActionMtime, (content) => {
                if (content.action === 'open') {
                    this.openWhiteboard();
                    if (content.message) {
                        log(`Whiteboard action: ${content.message}`);
                    }
                }
            });
        });
        // ── ui-action.json 감시 (open_ui_preview MCP 도구) ──
        fs.watchFile(uiAction, { interval: WATCH_INTERVAL_MS }, () => {
            this.handleFileChange(uiAction, lastUiMtime, (content) => {
                if (content.action === 'open_ui') {
                    this.openUIPreview(content.code || '', content.framework || 'react');
                }
            });
        });
        // ── dropzone-action.json 감시 (open_dropzone MCP 도구) ──
        fs.watchFile(dzAction, { interval: WATCH_INTERVAL_MS }, () => {
            this.handleFileChange(dzAction, lastDzMtime, (content) => {
                if (content.action === 'open') {
                    this.openDropzone();
                    if (content.message) {
                        log(`Dropzone action: ${content.message}`);
                    }
                }
            });
        });
        // ── whiteboard.json 감시 (draw_on_whiteboard MCP 도구) ──
        fs.watchFile(wbFile, { interval: WATCH_INTERVAL_MS }, () => {
            this.handleFileChange(wbFile, lastWbMtime, (content) => {
                // canvasState에서 쓴 내용은 건너뜀 (무한 루프 방지)
                if (content._source === 'canvasState')
                    return;
                if (!content.commands || content.commands.length === 0)
                    return;
                // 중복 전송 방지
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
        });
        log('File watching started (fs.watchFile)');
    }
    /** 파일 감시 중단 */
    stopWatching() {
        if (!this._watching)
            return;
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
    // ── Dropzone ────────────────────────────────────────────
    /** 드랍존 열기 — 드래그앤드롭 / 파일 선택으로 이미지 업로드 */
    openDropzone() {
        if (this.dropzonePanel) {
            this.dropzonePanel.reveal(vscode.ViewColumn.Two);
            return this.dropzonePanel;
        }
        this.dropzonePanel = vscode.window.createWebviewPanel('vibezoo-dropzone', '📸 VibeZoo Drop Zone', vscode.ViewColumn.Two, { enableScripts: true, retainContextWhenHidden: true });
        this.dropzonePanel.webview.html = this.dropzoneHtml();
        this.dropzonePanel.webview.onDidReceiveMessage((message) => {
            switch (message.type) {
                case 'uploadFile':
                    this.handleDropzoneUpload(message.fileName, message.data, message.mimeType);
                    break;
                case 'uploadLocalFile':
                    this.handleLocalFileDrop(message.filePath, message.fileName);
                    break;
            }
        });
        this.dropzonePanel.onDidDispose(() => { this.dropzonePanel = null; });
        return this.dropzonePanel;
    }
    /** 드랍존 절대 경로 파일 복사 (VS Code 샌드박스 우회 근본 해결책) */
    async handleLocalFileDrop(sourcePath, fileName) {
        try {
            const cacheDir = DROPZONE_CACHE_DIR();
            fs.mkdirSync(cacheDir, { recursive: true });
            const safeName = `drop_${Date.now()}_${fileName}`;
            const destPath = path.join(cacheDir, safeName);
            fs.copyFileSync(sourcePath, destPath);
            const stat = fs.statSync(destPath);
            // 2. LLM(에이전트)에게 제어권 넘기기: 클립보드에 경로 복사 후 알림
            const isImage = /\.(jpg|jpeg|png|webp|gif|bmp)$/i.test(fileName);
            const fileTypeLabel = isImage ? "이미지 파일" : "문서 파일";
            const llmPrompt = `[Drop Zone 업로드 알림]\n제가 방금 ${fileTypeLabel}을(를) 업로드했습니다.\n파일 경로: ${destPath}\n\n이 파일을 읽고 무엇을 도와드릴까요? (원하시는 분석이나 코딩을 지시해 주세요)`;
            await vscode.env.clipboard.writeText(llmPrompt);
            vscode.window.showInformationMessage(vscode.l10n.t('✅ {0} uploaded. (Path copied to clipboard. Paste it in chat to instruct the LLM!)', fileTypeLabel));
            console.log(`[VibeZoo] Local Dropzone file copied: ${destPath} (${stat.size} bytes)`);
            const webviewUri = this.dropzonePanel?.webview.asWebviewUri(vscode.Uri.file(destPath)).toString();
            this.dropzonePanel?.webview.postMessage({
                type: 'uploadComplete',
                path: destPath,
                size: stat.size,
                fileName: safeName,
                webviewUri: webviewUri
            });
        }
        catch (e) {
            console.log(`[VibeZoo] Local Dropzone error: ${e.message}`);
            this.dropzonePanel?.webview.postMessage({
                type: 'uploadError',
                error: e.message,
            });
        }
    }
    /** 드랍존 파일 업로드 처리 — Temp 폴더에 저장 */
    async handleDropzoneUpload(fileName, dataBase64, mimeType) {
        try {
            const cacheDir = DROPZONE_CACHE_DIR();
            fs.mkdirSync(cacheDir, { recursive: true });
            let ext = path.extname(fileName);
            if (!ext) {
                const mimeMap = {
                    'image/png': '.png',
                    'image/jpeg': '.jpg',
                    'image/gif': '.gif',
                    'image/webp': '.webp',
                    'image/bmp': '.bmp',
                    'image/svg+xml': '.svg',
                    'text/plain': '.txt',
                    'application/pdf': '.pdf',
                };
                ext = mimeMap[mimeType] || '.bin';
            }
            const safeName = `upload_${Date.now()}${ext}`;
            const destPath = path.join(cacheDir, safeName);
            const raw = dataBase64.replace(/^data:[^;]+;base64,/, '');
            const buffer = Buffer.from(raw, 'base64');
            fs.writeFileSync(destPath, buffer);
            // 2. LLM(에이전트)에게 제어권 넘기기: 클립보드에 경로 복사 후 알림
            const isImage = /\.(jpg|jpeg|png|webp|gif|bmp)$/i.test(fileName);
            const fileTypeLabel = isImage ? "이미지 파일" : "문서 파일";
            const llmPrompt = `[Drop Zone 업로드 알림]\n제가 방금 ${fileTypeLabel}을(를) 업로드했습니다.\n파일 경로: ${destPath}\n\n이 파일을 읽고 무엇을 도와드릴까요? (원하시는 분석이나 코딩을 지시해 주세요)`;
            await vscode.env.clipboard.writeText(llmPrompt);
            vscode.window.showInformationMessage(vscode.l10n.t('✅ {0} uploaded. (Path copied to clipboard. Paste it in chat to instruct the LLM!)', fileTypeLabel));
            console.log(`[VibeZoo] Dropzone upload saved: ${destPath} (${buffer.length} bytes)`);
            this.dropzonePanel?.webview.postMessage({
                type: 'uploadComplete',
                path: destPath,
                size: buffer.length,
                fileName: safeName,
            });
            // 업로드 레지스트리 기록 (LLM이 파일 경로를 알 수 있도록)
            try {
                const registryPath = path.join(os.homedir(), '.vibezoo-uploads', 'latest.json');
                const registry = { path: destPath, fileName: safeName, size: buffer.length, mimeType, timestamp: Date.now() };
                let entries = [];
                if (fs.existsSync(registryPath)) {
                    entries = JSON.parse(fs.readFileSync(registryPath, 'utf-8'));
                }
                entries.unshift(registry);
                if (entries.length > 10)
                    entries = entries.slice(0, 10);
                fs.writeFileSync(registryPath, JSON.stringify(entries, null, 2));
                console.log(`[VibeZoo] Upload registry updated: ${destPath}`);
            }
            catch { }
        }
        catch (e) {
            console.log(`[VibeZoo] Dropzone upload error: ${e.message}`);
            this.dropzonePanel?.webview.postMessage({
                type: 'uploadError',
                error: e.message,
            });
        }
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
  <h2>${vscode.l10n.t('⚠️ Cannot load Fabric.js')}</h2>
  <p>${vscode.l10n.t('Please check your internet connection or if the CDN is blocked.')}</p>
</div>
<div id="toolbar">
  <button onclick="setMode('draw')">${vscode.l10n.t('✏️ Draw')}</button>
  <button onclick="setMode('rect')">${vscode.l10n.t('⬜ Rectangle')}</button>
  <button onclick="setMode('text')">${vscode.l10n.t('📝 Text')}</button>
  <button onclick="setMode('select')">${vscode.l10n.t('🖱️ Select')}</button>
  <button onclick="captureScreenshot()">${vscode.l10n.t('📸 Capture')}</button>
  <button onclick="document.getElementById('imgInput').click()">${vscode.l10n.t('📷 Image')}</button>
  <button onclick="deleteSelected()">${vscode.l10n.t('🗑️ Delete Selected')}</button>
  <button onclick="clearAll()">${vscode.l10n.t('🧹 Clear All')}</button>
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
          canvas.add(new fabric.Textbox(props.text || '${vscode.l10n.t('Text')}', {
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
    canvas.add(new fabric.Textbox('${vscode.l10n.t("Enter text")}', { left: 100, top: 100, width: 300, fontSize: 20, fill: '#ffffff', fontFamily: 'sans-serif' }));
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
  <p>${vscode.l10n.t('When AI generates React/Vue component code, it will be rendered here in real-time.')}</p>
</div>
<script>
  var vscode = typeof acquireVsCodeApi !== 'undefined' ? acquireVsCodeApi() : null;
  if (vscode) vscode.postMessage({ type: 'ready' });

  window.addEventListener('message', function(event) {
    if (event.data.type === 'render' && event.data.code) {
      // HTML 엔티티 이스케이프 (srcdoc 속성용)
      var code = event.data.code;
      code = code.replace(/&/g, '&amp;');
      code = code.replace(/"/g, '&quot;');
      code = code.replace(/</g, '&lt;');
      code = code.replace(/>/g, '&gt;');
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
        container.innerHTML = '';
        var errorEl = document.createElement('p');
        errorEl.style.color = '#f44747';
        errorEl.innerText = '${vscode.l10n.t('Mermaid render error')}: ' + (err.message || String(err));
        container.appendChild(errorEl);
      }
    }
  });
</script>
</body></html>`;
    }
    dropzoneHtml() {
        return `<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>VibeZoo Drop Zone</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: #1e1e1e; color: #ccc; font-family: -apple-system, sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; flex-direction: column; padding: 20px; }
  #dropzone { width: 100%; max-width: 600px; height: 350px; border: 3px dashed #555; border-radius: 16px; display: flex; flex-direction: column; justify-content: center; align-items: center; gap: 16px; cursor: pointer; transition: all 0.3s; text-align: center; padding: 20px; position: relative; }
  #dropzone * { pointer-events: none; }
  #dropzone:hover, #dropzone.dragover { border-color: #4ec9ff; background: rgba(78,201,255,0.1); }
  #dropzone.dragover { border-color: #6acb6a; background: rgba(106,203,106,0.1); }
  #dropzone img { max-width: 90%; max-height: 250px; border-radius: 8px; display: none; object-fit: contain; pointer-events: none; }
  #dropzone.has-image img { display: block; }
  #dropzone.has-image .placeholder { display: none; }
  .icon { font-size: 56px; opacity: 0.4; }
  .placeholder h2 { font-size: 20px; margin-bottom: 4px; }
  .hint { font-size: 13px; color: #888; margin-top: 4px; }
  .status { font-size: 15px; margin-top: 12px; padding: 8px 16px; border-radius: 8px; background: #2d2d2d; display: none; }
  .status.show { display: block; }
  .status.success { color: #6acb6a; border: 1px solid #6acb6a; }
  .status.error { color: #f44747; border: 1px solid #f44747; }
  .status.info { color: #4ec9ff; border: 1px solid #4ec9ff; }
  .file-info { font-size: 12px; color: #888; margin-top: 4px; }
  .actions { margin-top: 16px; display: flex; gap: 8px; position: relative; z-index: 20; }
  .actions button { padding: 8px 20px; background: #3c3c3c; color: #ccc; border: 1px solid #555; border-radius: 6px; cursor: pointer; font-size: 13px; }
  .actions button:hover { background: #505050; }
  .actions button.primary { background: #0e639c; border-color: #0e639c; color: #fff; }
  .actions button.primary:hover { background: #1177bb; }
  input[type=file] { display: none; }
</style>
</head><body>
<!-- 드래그 앤 드롭 이벤트를 방해하지 않도록 인라인 onclick 속성을 완전히 제거합니다 -->
<div id="dropzone">
  <div class="icon">📷</div>
  <div class="placeholder">
    <h2>VibeZoo Drop Zone</h2>
    <p>Drag & drop any file here</p>
    <p class="hint">or click to browse files</p>
  </div>
  <img id="preview">
</div>
<div class="status" id="status"></div>
<div class="file-info" id="fileInfo"></div>
<div class="actions">
  <button onclick="document.getElementById('fileInput').click()" class="primary">📂 Browse</button>
  <button onclick="clearDropzone()">🗑️ Clear</button>
</div>
<input type="file" id="fileInput" onchange="handleFiles(this.files)">
<script>
  var vscode = typeof acquireVsCodeApi !== 'undefined' ? acquireVsCodeApi() : null;

  function handleFiles(files) {
    if (!files || files.length === 0) return;
    var file = files[0];
    
    // VS Code 꼼수: file.path가 존재하면 (로컬 드래그 앤 드롭)
    if (file.path) {
      setStatus('Uploading local file...', 'info');
      if (vscode) {
        vscode.postMessage({
          type: 'uploadLocalFile',
          filePath: file.path,
          fileName: file.name
        });
      }
    } else {
      // 버튼으로 올렸거나 일반 웹 환경 (Base64 변환)
      uploadFile(file);
    }
  }

  function uploadFile(file) {
    if (!file) return;
    var reader = new FileReader();
    reader.onload = function(e) {
      var dataUrl = e.target.result;
      if (file.type && file.type.startsWith('image/')) {
        var img = document.getElementById('preview');
        img.src = dataUrl;
        img.style.display = 'block';
        document.getElementById('dropzone').classList.add('has-image');
      }
      setStatus('Uploading...', 'info');
      if (vscode) {
        vscode.postMessage({
          type: 'uploadFile',
          fileName: file.name,
          data: dataUrl,
          mimeType: file.type,
          size: file.size,
        });
      }
      document.getElementById('fileInfo').textContent = file.name + ' (' + formatSize(file.size) + ')';
    };
    reader.readAsDataURL(file);
  }

  function setStatus(msg, type) {
    var el = document.getElementById('status');
    el.textContent = msg;
    el.className = 'status show ' + (type || 'info');
  }

  function formatSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
  }

  function clearDropzone() {
    document.getElementById('preview').src = '';
    document.getElementById('preview').style.display = 'none';
    document.getElementById('dropzone').classList.remove('has-image');
    document.getElementById('dropzone').classList.remove('dragover');
    document.getElementById('status').className = 'status';
    document.getElementById('status').style.display = 'none';
    document.getElementById('fileInfo').textContent = '';
    document.getElementById('fileInput').value = '';
  }

  window.addEventListener('message', function(e) {
    var msg = e.data;
    if (!msg) return;
    switch (msg.type) {
      case 'uploadComplete':
        setStatus('✅ Uploaded! Path: ' + msg.path, 'success');
        if (msg.fileName) {
          document.getElementById('fileInfo').textContent = msg.fileName + ' (' + formatSize(msg.size) + ')';
        }
        if (msg.webviewUri) {
          var img = document.getElementById('preview');
          img.src = msg.webviewUri;
          img.style.display = 'block';
          document.getElementById('dropzone').classList.add('has-image');
        }
        break;
      case 'uploadError':
        setStatus('❌ Upload failed: ' + msg.error, 'error');
        break;
    }
  });

  var dz = document.getElementById('dropzone');
  
  dz.addEventListener('dragenter', function(e) {
    e.preventDefault(); e.stopPropagation();
    this.classList.add('dragover');
  }, false);

  dz.addEventListener('dragover', function(e) {
    e.preventDefault(); e.stopPropagation();
    e.dataTransfer.dropEffect = 'copy';
    this.classList.add('dragover');
  }, false);

  dz.addEventListener('dragleave', function(e) {
    e.preventDefault(); e.stopPropagation();
    this.classList.remove('dragover');
  }, false);

  dz.addEventListener('drop', function(e) {
    e.preventDefault(); e.stopPropagation();
    this.classList.remove('dragover');
    var files = e.dataTransfer.files;
    if (files && files.length > 0) {
      handleFiles(files);
    }
  }, false);

  document.addEventListener('dragover', function(e) { e.preventDefault(); e.stopPropagation(); }, false);
  document.addEventListener('drop', function(e) { e.preventDefault(); e.stopPropagation(); }, false);

  document.addEventListener('paste', function(e) {
    var items = e.clipboardData && e.clipboardData.items;
    if (!items) return;
    for (var i = 0; i < items.length; i++) {
      var item = items[i];
      if (item.kind === 'file') {
        var file = item.getAsFile();
        if (file) {
          uploadFile(file);
          break;
        }
      }
    }
  });

  if (vscode) vscode.postMessage({ type: 'ready' });
</script>
</body></html>`;
    }
}
exports.VisualVibePanels = VisualVibePanels;
//# sourceMappingURL=VisualVibePanels.js.map