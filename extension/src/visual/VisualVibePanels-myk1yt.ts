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

import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { exec } from 'child_process';
import { ErrorDashboard } from './ErrorDashboard';

// ── 상수 ──────────────────────────────────────────────────
const WB_FILE = () => path.join(os.homedir(), '.vibezoo-whiteboard.json');
const WB_ACTION_FILE = () => path.join(os.homedir(), '.vibezoo-whiteboard-action.json');
const UI_ACTION_FILE = () => path.join(os.homedir(), '.vibezoo-ui-action.json');
const DZ_ACTION_FILE = () => path.join(os.homedir(), '.vibezoo-dropzone-action.json');
const CHAT_PENDING_FILE = () => path.join(os.homedir(), '.vibezoo-chat-pending.json');
const getDateString = (): string => {
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

const log = (msg: string, ...args: any[]) => {
  if (process.env.VIBEZOO_DEBUG) console.log(`[VibeZoo::Visual] ${msg}`, ...args);
};

// ── 타입 정의 ──────────────────────────────────────────────
interface Point2D { x: number; y: number; }

interface DrawCommand {
  type: 'polygon' | 'rect' | 'circle' | 'line' | 'text' | 'arrow' | 'freehand' | 'clear' | 'image';
  props?: Record<string, any>;
}

export interface DropzoneUploadEntry {
  path: string;
  fileName: string;
  size: number;
  mimeType: string;
  timestamp: number;
  width?: number;
  height?: number;
  autoAnalyze?: boolean;
  analysisStatus?: 'pending' | 'done' | 'failed';
}

interface WatchFileContent {
  _source?: string;
  commands?: DrawCommand[];
  action?: string;
  message?: string;
  code?: string;
  framework?: string;
  timestamp?: number;
}

// ── 유틸 ──────────────────────────────────────────────────
function debounce<T extends (...args: any[]) => void>(fn: T, delay: number): T {
  let timer: ReturnType<typeof setTimeout> | null = null;
  const debounced = (...args: any[]) => {
    if (timer !== null) clearTimeout(timer);
    timer = setTimeout(() => {
      timer = null;
      fn(...args);
    }, delay);
  };
  return debounced as unknown as T;
}

// ── 메인 클래스 ────────────────────────────────────────────
export class VisualVibePanels {
  private whiteboardPanel: vscode.WebviewPanel | null = null;
  private uiPreviewPanel: vscode.WebviewPanel | null = null;
  private diagramPanel: vscode.WebviewPanel | null = null;
  private dropzonePanel: vscode.WebviewPanel | null = null;
  private readonly homedir: string;
  private _activated = false;
  private _watching = false;
  private _lastCommandsHash = '';
  /** Whiteboard가 아직 열리지 않았을 때 대기 중인 드로잉 명령 */
  private _pendingDrawCommands: DrawCommand[] | null = null;

  /** P3: Error Dashboard 인스턴스 */
  private errorDashboard: ErrorDashboard;

  constructor() {
    this.homedir = os.homedir();
    this.errorDashboard = new ErrorDashboard();
  }

  // ── 수명주기 ──────────────────────────────────────────────

  activate(): void {
    if (this._activated) return;
    this._activated = true;
    this.startWatching();
    log('VisualVibePanels activated (watching started)');
  }

  dispose(): void {
    this.stopWatching();
    this.whiteboardPanel?.dispose();
    this.uiPreviewPanel?.dispose();
    this.diagramPanel?.dispose();
    this.dropzonePanel?.dispose();
    this.errorDashboard?.dispose();
  }

  // ── 파일 감시 ─────────────────────────────────────────────

  /**
   * action 파일의 변경을 감지하여 콜백 실행.
   * @param filePath 감시할 파일 경로
   * @param lastMtime 마지막 mtime 기록 (객체 참조로 유지)
   * @param onChange 파일 내용이 변경되었을 때 실행할 콜백
   */
  private async handleFileChange(
    filePath: string,
    lastMtime: { current: number },
    onChange: (content: WatchFileContent) => void,
    retries = 5
  ): Promise<void> {
    try {
      if (!fs.existsSync(filePath)) return;
      const stat = fs.statSync(filePath);
      if (stat.mtimeMs <= lastMtime.current && retries === 5) return;

      const contentStr = await fs.promises.readFile(filePath, 'utf-8');
      const content: WatchFileContent = JSON.parse(contentStr);
      lastMtime.current = stat.mtimeMs;
      onChange(content);
    } catch (err) {
      if (retries > 0) {
        setTimeout(() => this.handleFileChange(filePath, lastMtime, onChange, retries - 1), 200);
      }
    }
  }

  /** 현재 파일의 mtime 반환 (없으면 0) */
  private getCurrentMtime(filePath: string): number {
    try {
      return fs.statSync(filePath).mtimeMs;
    } catch {
      return 0;
    }
  }

  /**
   * 파일 감시 시작 (fs.watchFile 기반).
   * activate()에서 최초 1회 호출.
   */
  private startWatching(): void {
    if (this._watching) return;
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
        if (content._source === 'canvasState') return;
        if (!content.commands || content.commands.length === 0) return;

        // 중복 전송 방지
        const hash = JSON.stringify(content.commands);
        if (hash === this._lastCommandsHash) return;
        this._lastCommandsHash = hash;

        if (!this.whiteboardPanel) {
          this.openWhiteboard();
          this._pendingDrawCommands = content.commands;
        } else {
          this.sendToWhiteboard(content.commands);
        }
      });
    });

    log('File watching started (fs.watchFile)');
  }

  /** 파일 감시 중단 */
  private stopWatching(): void {
    if (!this._watching) return;
    try { fs.unwatchFile(WB_FILE()); } catch { /* ignore */ }
    try { fs.unwatchFile(WB_ACTION_FILE()); } catch { /* ignore */ }
    try { fs.unwatchFile(UI_ACTION_FILE()); } catch { /* ignore */ }
    try { fs.unwatchFile(DZ_ACTION_FILE()); } catch { /* ignore */ } // ★ BUG FIX: dropzone unwatch 누락
    this._watching = false;
    log('File watching stopped');
  }

  // ── Whiteboard ───────────────────────────────────────────

  /** AI 드로잉 명령을 Whiteboard Webview로 전달 */
  private sendToWhiteboard(commands: DrawCommand[]): void {
    if (this.whiteboardPanel) {
      this.whiteboardPanel.webview.postMessage({ type: 'draw', commands });
    }
  }

  /** Whiteboard 열기 — Fabric.js 기반 드로잉 캔버스 */
  openWhiteboard(): vscode.WebviewPanel {
    this.startWatching();

    if (this.whiteboardPanel) {
      this.whiteboardPanel.reveal(vscode.ViewColumn.Two);
      return this.whiteboardPanel;
    }

    this.whiteboardPanel = vscode.window.createWebviewPanel(
      'vibezoo-whiteboard',
      '🎨 VibeZoo Whiteboard',
      vscode.ViewColumn.Two,
      { enableScripts: true, retainContextWhenHidden: true },
    );

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
            this.sendToWhiteboard(this._pendingDrawCommands!);
            this._pendingDrawCommands = null;
          }
          break;
      }
    });

    this.whiteboardPanel.onDidDispose(() => { this.whiteboardPanel = null; });
    return this.whiteboardPanel;
  }

  /** 사용자 캔버스 상태 저장 (무한 루프 방지를 위해 _source 마커 포함) */
  private handleCanvasState(commands: DrawCommand[]): void {
    const data: WatchFileContent = {
      _source: 'canvasState',
      timestamp: Date.now(),
      commands,
    };
    try {
      fs.writeFileSync(WB_FILE(), JSON.stringify(data, null, 2), 'utf-8');
    } catch { /* ignore */ }
  }

  /** 캡처 도구 실행 → 클립보드 이미지를 Whiteboard에 자동 로드 */
  private handleCaptureScreenshot(): void {
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

    exec(openCaptureTool, { timeout: CAPTURE_TIMEOUT_MS }, (err) => {
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
          } else {
            this.cleanupTempFile(tmpFile);
          }
        } catch (e: any) {
          log('Capture read error:', e.message);
          this.cleanupTempFile(tmpFile);
        }
      }, CAPTURE_READ_DELAY_MS);
    });
  }

  private cleanupTempFile(filePath: string): void {
    try { if (fs.existsSync(filePath)) fs.unlinkSync(filePath); } catch { /* ignore */ }
  }

  // ── UI Preview ───────────────────────────────────────────

  openUIPreview(initialCode?: string, _framework?: string): vscode.WebviewPanel {
    if (this.uiPreviewPanel) {
      this.uiPreviewPanel.reveal(vscode.ViewColumn.Two);
      if (initialCode) {
        this.uiPreviewPanel.webview.postMessage({ type: 'render', code: initialCode });
      }
      return this.uiPreviewPanel;
    }

    this.uiPreviewPanel = vscode.window.createWebviewPanel(
      'vibezoo-ui-preview',
      '🖼️ VibeZoo UI Preview',
      vscode.ViewColumn.Two,
      { enableScripts: true, retainContextWhenHidden: true },
    );

    this.uiPreviewPanel.webview.html = this.uiPreviewHtml();
    this.uiPreviewPanel.onDidDispose(() => { this.uiPreviewPanel = null; });

    // Webview 로드 완료 후 초기 코드 전송 (중복 방지)
    if (initialCode) {
      const panel = this.uiPreviewPanel;
      let sent = false;
      const onReady = (msg: any) => {
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
          try { panel.webview.postMessage({ type: 'render', code: initialCode }); } catch { /* ignore */ }
        }
      }, UI_PREVIEW_FALLBACK_MS);
    }

    return this.uiPreviewPanel;
  }

  // ── Diagram ──────────────────────────────────────────────

  openDiagram(diagramType?: string): vscode.WebviewPanel {
    if (this.diagramPanel) {
      this.diagramPanel.reveal(vscode.ViewColumn.Two);
      return this.diagramPanel;
    }

    this.diagramPanel = vscode.window.createWebviewPanel(
      'vibezoo-diagram',
      '📊 VibeZoo Diagram',
      vscode.ViewColumn.Two,
      { enableScripts: true, retainContextWhenHidden: true },
    );

    this.diagramPanel.webview.html = this.diagramHtml(diagramType);
    this.diagramPanel.onDidDispose(() => { this.diagramPanel = null; });
    return this.diagramPanel;
  }

  // ── Error Dashboard ───────────────────────────────────

  /** Error Dashboard 열기 (P3) */
  openErrorDashboard(): vscode.WebviewPanel {
    return this.errorDashboard.open();
  }

  // ── Dropzone ────────────────────────────────────────────

  /** 업로드 히스토리 (최대 10개) 조회 */
  private getUploadHistory(): DropzoneUploadEntry[] {
    try {
      const registryPath = path.join(os.homedir(), '.vibezoo-uploads', 'latest.json');
      if (fs.existsSync(registryPath)) {
        const raw = fs.readFileSync(registryPath, 'utf-8');
        const entries = JSON.parse(raw);
        if (Array.isArray(entries)) {
          return entries.slice(0, 10);
        }
      }
    } catch {
      // ignore
    }
    return [];
  }

  /** 업로드 히스토리 저장 */
  private saveUploadHistory(entries: DropzoneUploadEntry[]): void {
    try {
      const uploadsDir = path.join(os.homedir(), '.vibezoo-uploads');
      fs.mkdirSync(uploadsDir, { recursive: true });
      const registryPath = path.join(uploadsDir, 'latest.json');
      fs.writeFileSync(registryPath, JSON.stringify(entries.slice(0, 10), null, 2), 'utf-8');
    } catch {
      // ignore
    }
  }

  /** 드랍존 열기 — 드래그앤드롭 / 클립보드 붙여넣기(Ctrl+V) / 파일 선택으로 이미지 업로드 */
  openDropzone(): vscode.WebviewPanel {
    if (this.dropzonePanel) {
      this.dropzonePanel.reveal(vscode.ViewColumn.Two);
      this.dropzonePanel.webview.postMessage({
        type: 'historyLoaded',
        history: this.getUploadHistory(),
      });
      return this.dropzonePanel;
    }

    this.dropzonePanel = vscode.window.createWebviewPanel(
      'vibezoo-dropzone',
      '📸 VibeZoo Drop Zone',
      vscode.ViewColumn.Two,
      { enableScripts: true, retainContextWhenHidden: true },
    );

    this.dropzonePanel.webview.html = this.dropzoneHtml();

    this.dropzonePanel.webview.onDidReceiveMessage(async (message) => {
      switch (message.type) {
        case 'ready':
          this.dropzonePanel?.webview.postMessage({
            type: 'historyLoaded',
            history: this.getUploadHistory(),
          });
          break;
        case 'uploadFile':
          await this.handleDropzoneUpload(
            message.fileName,
            message.data,
            message.mimeType,
            message.width,
            message.height
          );
          break;
        case 'uploadLocalFile':
          await this.handleLocalFileDrop(
            message.filePath,
            message.fileName,
            message.width,
            message.height
          );
          break;
        case 'copyToClipboard':
          if (message.text) {
            await vscode.env.clipboard.writeText(message.text);
            const label = message.label || vscode.l10n.t('Content');
            vscode.window.showInformationMessage(vscode.l10n.t('📋 {0} copied to clipboard!', label));
            this.dropzonePanel?.webview.postMessage({
              type: 'copied',
              label: label,
              text: message.text,
            });
          }
          break;
        case 'openFile':
          if (message.filePath && fs.existsSync(message.filePath)) {
            vscode.commands.executeCommand('vscode.open', vscode.Uri.file(message.filePath));
          }
          break;
        case 'clearHistory':
          this.saveUploadHistory([]);
          this.dropzonePanel?.webview.postMessage({
            type: 'historyLoaded',
            history: [],
          });
          vscode.window.showInformationMessage(vscode.l10n.t('🗑️ Upload history cleared.'));
          break;
      }
    });

    this.dropzonePanel.onDidDispose(() => { this.dropzonePanel = null; });
    return this.dropzonePanel;
  }

  /** 드랍존 절대 경로 파일 복사 (VS Code 샌드박스 우회 근본 해결책) */
  private async handleLocalFileDrop(
    sourcePath: string,
    fileName: string,
    width?: number,
    height?: number
  ): Promise<void> {
    try {
      const cacheDir = DROPZONE_CACHE_DIR();
      fs.mkdirSync(cacheDir, { recursive: true });

      const safeName = `drop_${Date.now()}_${fileName}`;
      const destPath = path.join(cacheDir, safeName);

      fs.copyFileSync(sourcePath, destPath);
      const stat = fs.statSync(destPath);

      const isImage = /\.(jpg|jpeg|png|webp|gif|bmp|svg)$/i.test(fileName);
      const fileTypeLabel = isImage ? vscode.l10n.t('Image file') : vscode.l10n.t('Document file');

      // 1. 설정 확인 (기본값 true)
      const autoAnalyze = vscode.workspace.getConfiguration('vibezoo.image').get<boolean>('autoAnalyze', true);

      // 2. 클립보드에 AI 프롬프트 + 마크다운 참조 자동 복사
      const markdownRef = isImage
        ? `![${fileName}](${destPath})\n\n[Image File Path: ${destPath}]`
        : `[File: ${fileName}](${destPath})\n\n[File Path: ${destPath}]`;

      await vscode.env.clipboard.writeText(markdownRef);
      vscode.window.showInformationMessage(
        vscode.l10n.t('✅ {0} saved & Markdown copied to clipboard! Paste it in AI chat.', fileTypeLabel)
      );

      console.log(`[VibeZoo] Local Dropzone file copied: ${destPath} (${stat.size} bytes)`);

      const entry: DropzoneUploadEntry = {
        path: destPath,
        fileName: safeName,
        size: stat.size,
        mimeType: isImage ? `image/${path.extname(fileName).slice(1) || 'png'}` : 'application/octet-stream',
        timestamp: Date.now(),
        width: width || undefined,
        height: height || undefined,
        autoAnalyze: autoAnalyze,
        analysisStatus: 'pending',
      };

      const history = this.getUploadHistory();
      const updatedHistory = [entry, ...history.filter(h => h.path !== destPath)].slice(0, 10);
      this.saveUploadHistory(updatedHistory);

      const webviewUri = this.dropzonePanel?.webview.asWebviewUri(vscode.Uri.file(destPath)).toString();

      this.dropzonePanel?.webview.postMessage({
        type: 'uploadComplete',
        entry,
        history: updatedHistory,
        webviewUri: webviewUri,
        markdownRef: markdownRef,
      });
    } catch (e: any) {
      console.log(`[VibeZoo] Local Dropzone error: ${e.message}`);
      this.dropzonePanel?.webview.postMessage({
        type: 'uploadError',
        error: e.message,
      });
    }
  }

  /** 드랍존 파일 업로드 처리 — Temp 폴더에 저장 */
  private async handleDropzoneUpload(
    fileName: string,
    dataBase64: string,
    mimeType: string,
    width?: number,
    height?: number
  ): Promise<void> {
    try {
      const cacheDir = DROPZONE_CACHE_DIR();
      fs.mkdirSync(cacheDir, { recursive: true });

      let ext = path.extname(fileName);
      if (!ext) {
        const mimeMap: Record<string, string> = {
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

      const isImage = /\.(jpg|jpeg|png|webp|gif|bmp|svg)$/i.test(fileName) || (mimeType && mimeType.startsWith('image/'));
      const fileTypeLabel = isImage ? vscode.l10n.t('Image file') : vscode.l10n.t('Document file');

      // 1. 설정 확인 (기본값 true)
      const autoAnalyze = vscode.workspace.getConfiguration('vibezoo.image').get<boolean>('autoAnalyze', true);

      // 2. 클립보드에 AI 프롬프트 + 마크다운 참조 자동 복사
      const markdownRef = isImage
        ? `![${fileName}](${destPath})\n\n[Image File Path: ${destPath}]`
        : `[File: ${fileName}](${destPath})\n\n[File Path: ${destPath}]`;

      await vscode.env.clipboard.writeText(markdownRef);
      vscode.window.showInformationMessage(
        vscode.l10n.t('✅ {0} saved & Markdown copied to clipboard! Paste it in AI chat.', fileTypeLabel)
      );

      console.log(`[VibeZoo] Dropzone upload saved: ${destPath} (${buffer.length} bytes)`);

      const entry: DropzoneUploadEntry = {
        path: destPath,
        fileName: safeName,
        size: buffer.length,
        mimeType: mimeType || 'image/png',
        timestamp: Date.now(),
        width: width || undefined,
        height: height || undefined,
        autoAnalyze: autoAnalyze,
        analysisStatus: 'pending',
      };

      const history = this.getUploadHistory();
      const updatedHistory = [entry, ...history.filter(h => h.path !== destPath)].slice(0, 10);
      this.saveUploadHistory(updatedHistory);

      const webviewUri = this.dropzonePanel?.webview.asWebviewUri(vscode.Uri.file(destPath)).toString();

      this.dropzonePanel?.webview.postMessage({
        type: 'uploadComplete',
        entry,
        history: updatedHistory,
        webviewUri: webviewUri,
        markdownRef: markdownRef,
      });
    } catch (e: any) {
      console.log(`[VibeZoo] Dropzone upload error: ${e.message}`);
      this.dropzonePanel?.webview.postMessage({
        type: 'uploadError',
        error: e.message,
      });
    }
  }

  // ── HTML 템플릿 ──────────────────────────────────────────

  private whiteboardHtml(): string {
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

  private uiPreviewHtml(): string {
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

  private diagramHtml(diagramType?: string): string {
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


  private dropzoneHtml(): string {
    return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>${vscode.l10n.t('VibeZoo Drop Zone')}</title>
<style>
  :root {
    --ease-out: cubic-bezier(0.23, 1, 0.32, 1);
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    background: var(--vscode-editor-background, #1e1e1e);
    color: var(--vscode-editor-foreground, #cccccc);
    font-family: var(--vscode-font-family, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif);
    min-height: 100vh;
    padding: 16px;
    display: flex;
    justify-content: flex-start;
    align-items: center;
    flex-direction: column;
  }
  #app {
    width: 100%;
    max-width: 680px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
  header {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  header h1 {
    font-size: 18px;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  header p {
    font-size: 12px;
    opacity: 0.8;
  }
  #dropzone {
    width: 100%;
    min-height: 220px;
    border: 2px dashed var(--vscode-input-border, #454545);
    border-radius: 12px;
    background: rgba(128, 128, 128, 0.04);
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    gap: 12px;
    cursor: pointer;
    text-align: center;
    padding: 20px;
    position: relative;
    transition: transform 150ms var(--ease-out), border-color 150ms var(--ease-out), background 150ms var(--ease-out);
    outline: none;
  }
  #dropzone:hover, #dropzone:focus-visible {
    border-color: var(--vscode-focusBorder, #007fd4);
    background: rgba(0, 122, 204, 0.06);
  }
  #dropzone.dragover {
    border-color: #4ec9b0;
    background: rgba(78, 201, 176, 0.12);
    transform: scale(1.01);
  }
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    pointer-events: none;
  }
  .empty-state .icon {
    font-size: 40px;
    opacity: 0.6;
    line-height: 1;
  }
  .empty-state h3 {
    font-size: 14px;
    font-weight: 500;
  }
  .empty-state .hint {
    font-size: 12px;
    opacity: 0.7;
  }
  .empty-state .kbd-hint {
    margin-top: 6px;
    font-size: 11px;
    padding: 3px 8px;
    background: var(--vscode-badge-background, #333333);
    color: var(--vscode-badge-foreground, #ffffff);
    border-radius: 4px;
    border: 1px solid var(--vscode-widget-border, #454545);
  }
  .preview-state {
    display: none;
    width: 100%;
    flex-direction: column;
    align-items: center;
    gap: 12px;
  }
  #dropzone.has-image .empty-state { display: none; }
  #dropzone.has-image .preview-state { display: flex; }
  #preview-img {
    max-width: 100%;
    max-height: 240px;
    border-radius: 6px;
    object-fit: contain;
    box-shadow: 0 4px 12px rgba(0,0,0,0.25);
    background: rgba(0,0,0,0.1);
  }
  .meta-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    justify-content: center;
  }
  .chip {
    font-size: 11px;
    padding: 3px 8px;
    background: var(--vscode-badge-background, #3c3c3c);
    color: var(--vscode-badge-foreground, #ffffff);
    border-radius: 4px;
    display: inline-flex;
    align-items: center;
    gap: 4px;
  }
  .btn-bar {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: center;
  }
  button {
    font-family: inherit;
    font-size: 12px;
    padding: 6px 14px;
    border-radius: 4px;
    cursor: pointer;
    border: 1px solid transparent;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    transition: background 120ms var(--ease-out), transform 80ms var(--ease-out);
  }
  button:active {
    transform: scale(0.97);
  }
  button.primary {
    background: var(--vscode-button-background, #0e639c);
    color: var(--vscode-button-foreground, #ffffff);
  }
  button.primary:hover {
    background: var(--vscode-button-hoverBackground, #1177bb);
  }
  button.secondary {
    background: var(--vscode-button-secondaryBackground, #3a3d41);
    color: var(--vscode-button-secondaryForeground, #ffffff);
  }
  button.secondary:hover {
    background: var(--vscode-button-secondaryHoverBackground, #45494e);
  }
  button.ghost {
    background: transparent;
    border: 1px solid var(--vscode-widget-border, #454545);
    color: var(--vscode-editor-foreground, #cccccc);
  }
  button.ghost:hover {
    background: rgba(255, 255, 255, 0.06);
  }
  .history-section {
    display: flex;
    flex-direction: column;
    gap: 10px;
    border-top: 1px solid var(--vscode-widget-border, #333333);
    padding-top: 16px;
  }
  .history-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .history-header h2 {
    font-size: 13px;
    font-weight: 600;
    opacity: 0.9;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .history-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 10px;
  }
  .history-empty {
    grid-column: 1 / -1;
    text-align: center;
    padding: 20px;
    font-size: 12px;
    opacity: 0.6;
    border: 1px dashed var(--vscode-widget-border, #333333);
    border-radius: 8px;
  }
  .history-card {
    border: 1px solid var(--vscode-widget-border, #333333);
    border-radius: 8px;
    padding: 6px;
    background: rgba(128, 128, 128, 0.02);
    cursor: pointer;
    display: flex;
    flex-direction: column;
    gap: 4px;
    transition: transform 120ms var(--ease-out), border-color 120ms var(--ease-out);
    outline: none;
    text-align: left;
  }
  .history-card:hover, .history-card:focus-visible {
    border-color: var(--vscode-focusBorder, #007fd4);
    transform: translateY(-2px);
    background: rgba(0, 122, 204, 0.05);
  }
  .history-card.active {
    border-color: var(--vscode-focusBorder, #007fd4);
    box-shadow: 0 0 0 1px var(--vscode-focusBorder, #007fd4);
  }
  .history-thumb {
    width: 100%;
    height: 70px;
    object-fit: contain;
    border-radius: 4px;
    background: rgba(0,0,0,0.15);
  }
  .history-name {
    font-size: 11px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    font-weight: 500;
  }
  .history-meta {
    font-size: 10px;
    opacity: 0.65;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  #toast {
    position: fixed;
    bottom: 24px;
    left: 50%;
    transform: translateX(-50%) translateY(20px);
    opacity: 0;
    background: var(--vscode-notifications-background, #252526);
    color: var(--vscode-notifications-foreground, #cccccc);
    border: 1px solid var(--vscode-focusBorder, #007fd4);
    padding: 8px 16px;
    border-radius: 6px;
    font-size: 12px;
    z-index: 1000;
    box-shadow: 0 4px 14px rgba(0,0,0,0.3);
    transition: transform 200ms var(--ease-out), opacity 200ms var(--ease-out);
    pointer-events: none;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  #toast.show {
    transform: translateX(-50%) translateY(0);
    opacity: 1;
  }
  input[type=file] { display: none; }
</style>
</head>
<body>
<div id="app">
  <header>
    <h1>📸 ${vscode.l10n.t('VibeZoo Drop Zone')}</h1>
    <p>${vscode.l10n.t('Paste image (Ctrl+V) or drag & drop files here')}</p>
  </header>

  <div id="dropzone" tabindex="0" role="button" aria-label="${vscode.l10n.t('Drop Zone')}">
    <div class="empty-state">
      <div class="icon">📷</div>
      <h3>${vscode.l10n.t('Paste image (Ctrl+V) or drag & drop files here')}</h3>
      <p class="hint">${vscode.l10n.t('Click to browse files')}</p>
      <div class="kbd-hint">Ctrl + V / ⌘ + V</div>
    </div>

    <div class="preview-state">
      <img id="preview-img" alt="Preview">
      <div class="meta-chips" id="meta-chips"></div>
      <div class="btn-bar" style="margin-top: 6px;">
        <button type="button" class="primary" id="btnCopyMarkdown">📋 ${vscode.l10n.t('Copy Markdown')}</button>
        <button type="button" class="secondary" id="btnCopyPath">📁 ${vscode.l10n.t('Copy Path')}</button>
        <button type="button" class="ghost" id="btnOpenFile">🔍 ${vscode.l10n.t('Open in VS Code')}</button>
      </div>
    </div>
  </div>

  <div class="btn-bar" style="justify-content: space-between;">
    <button type="button" class="secondary" onclick="document.getElementById('fileInput').click()">📂 ${vscode.l10n.t('Browse Files')}</button>
    <button type="button" class="ghost" onclick="clearCurrentPreview()">🧹 ${vscode.l10n.t('Clear')}</button>
  </div>

  <div class="history-section">
    <div class="history-header">
      <h2>🕒 ${vscode.l10n.t('Recent Uploads')}</h2>
      <button type="button" class="ghost" style="padding: 3px 8px; font-size: 11px;" onclick="clearHistory()">🗑️ ${vscode.l10n.t('Clear History')}</button>
    </div>
    <div class="history-grid" id="history-grid">
      <div class="history-empty">${vscode.l10n.t('No recent uploads')}</div>
    </div>
  </div>
</div>

<div id="toast"></div>
<input type="file" id="fileInput" accept="image/*,.pdf,.doc,.docx,.txt,.md" onchange="handleFiles(this.files)">

<script>
  var vscode = typeof acquireVsCodeApi !== 'undefined' ? acquireVsCodeApi() : null;
  var currentEntry = null;
  var historyList = [];
  var toastTimer = null;

  function showToast(msg) {
    var toast = document.getElementById('toast');
    toast.textContent = msg;
    toast.classList.add('show');
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(function() {
      toast.classList.remove('show');
    }, 2800);
  }

  function formatSize(bytes) {
    if (!bytes || bytes < 1024) return (bytes || 0) + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
  }

  function formatTime(ts) {
    if (!ts) return '';
    var d = new Date(ts);
    var h = String(d.getHours()).padStart(2, '0');
    var m = String(d.getMinutes()).padStart(2, '0');
    return h + ':' + m;
  }

  function updatePreview(entry, webviewUri) {
    currentEntry = entry;
    var dz = document.getElementById('dropzone');
    var img = document.getElementById('preview-img');
    var chips = document.getElementById('meta-chips');

    if (!entry) {
      dz.classList.remove('has-image');
      img.src = '';
      chips.innerHTML = '';
      return;
    }

    dz.classList.add('has-image');
    if (webviewUri) {
      img.src = webviewUri;
    } else if (entry.dataUrl) {
      img.src = entry.dataUrl;
    } else if (entry.path) {
      img.src = entry.path;
    }

    var ext = (entry.fileName || '').split('.').pop().toUpperCase() || 'FILE';
    var sizeStr = formatSize(entry.size);
    var resStr = (entry.width && entry.height) ? (entry.width + ' × ' + entry.height) : '';

    var html = '';
    if (resStr) {
      html += '<span class="chip">📐 ' + resStr + '</span>';
    }
    html += '<span class="chip">💾 ' + sizeStr + '</span>';
    html += '<span class="chip">📄 ' + ext + '</span>';
    if (entry.fileName) {
      html += '<span class="chip" title="' + entry.fileName + '">📁 ' + entry.fileName + '</span>';
    }
    chips.innerHTML = html;
  }

  function renderHistory(list) {
    historyList = list || [];
    var grid = document.getElementById('history-grid');
    if (!historyList || historyList.length === 0) {
      grid.innerHTML = '<div class="history-empty">${vscode.l10n.t('No recent uploads')}</div>';
      return;
    }

    grid.innerHTML = '';
    historyList.forEach(function(item, idx) {
      var card = document.createElement('div');
      card.className = 'history-card' + (currentEntry && currentEntry.path === item.path ? ' active' : '');
      card.tabIndex = 0;
      card.setAttribute('role', 'button');
      card.setAttribute('aria-label', item.fileName);

      var isImg = /\\.(jpg|jpeg|png|webp|gif|bmp|svg)$/i.test(item.fileName) || (item.mimeType && item.mimeType.startsWith('image/'));
      var iconOrImg = isImg
        ? '<img class="history-thumb" src="' + (item.webviewUri || item.path) + '" alt="" onerror="this.style.display=\\'none\\'">'
        : '<div class="history-thumb" style="display:flex;align-items:center;justify-content:center;font-size:24px;">📄</div>';

      var res = (item.width && item.height) ? (item.width + '×' + item.height + ' • ') : '';
      card.innerHTML = iconOrImg +
        '<div class="history-name" title="' + item.fileName + '">' + item.fileName + '</div>' +
        '<div class="history-meta">' + res + formatSize(item.size) + ' • ' + formatTime(item.timestamp) + '</div>';

      function selectCard() {
        document.querySelectorAll('.history-card').forEach(function(c) { c.classList.remove('active'); });
        card.classList.add('active');
        updatePreview(item, item.webviewUri);
        var isImg = /\\.(jpg|jpeg|png|webp|gif|bmp|svg)$/i.test(item.fileName);
        var md = isImg ? '![' + item.fileName + '](' + item.path + ')' : '[' + item.fileName + '](' + item.path + ')';
        if (vscode) {
          vscode.postMessage({
            type: 'copyToClipboard',
            text: md,
            label: '${vscode.l10n.t('Markdown')}'
          });
        }
      }

      card.onclick = selectCard;
      card.onkeydown = function(e) {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          selectCard();
        }
      };

      grid.appendChild(card);
    });
  }

  function handleFiles(files) {
    if (!files || files.length === 0) return;
    var file = files[0];

    showToast('${vscode.l10n.t('Uploading...')}');

    if (file.path) {
      // 로컬 파일 경로가 있는 경우 (VS Code 데스크톱 드래그앤드롭)
      var img = new Image();
      var u = URL.createObjectURL(file);
      img.onload = function() {
        var w = img.naturalWidth;
        var h = img.naturalHeight;
        URL.revokeObjectURL(u);
        if (vscode) {
          vscode.postMessage({
            type: 'uploadLocalFile',
            filePath: file.path,
            fileName: file.name,
            width: w,
            height: h
          });
        }
      };
      img.onerror = function() {
        URL.revokeObjectURL(u);
        if (vscode) {
          vscode.postMessage({
            type: 'uploadLocalFile',
            filePath: file.path,
            fileName: file.name
          });
        }
      };
      img.src = u;
    } else {
      // 일반 클립보드 또는 파일 인풋 (Base64)
      var reader = new FileReader();
      reader.onload = function(e) {
        var dataUrl = e.target.result;
        var isImg = file.type && file.type.startsWith('image/');
        if (isImg) {
          var img = new Image();
          img.onload = function() {
            var w = img.naturalWidth;
            var h = img.naturalHeight;
            if (vscode) {
              vscode.postMessage({
                type: 'uploadFile',
                fileName: file.name,
                data: dataUrl,
                mimeType: file.type,
                width: w,
                height: h
              });
            }
          };
          img.src = dataUrl;
        } else {
          if (vscode) {
            vscode.postMessage({
              type: 'uploadFile',
              fileName: file.name,
              data: dataUrl,
              mimeType: file.type
            });
          }
        }
      };
      reader.readAsDataURL(file);
    }
  }

  function clearCurrentPreview() {
    updatePreview(null);
    document.getElementById('fileInput').value = '';
  }

  function clearHistory() {
    if (vscode) {
      vscode.postMessage({ type: 'clearHistory' });
    }
  }

  // 버튼 이벤트 연결
  document.getElementById('btnCopyMarkdown').onclick = function(e) {
    e.stopPropagation();
    if (!currentEntry) return;
    var isImg = /\\.(jpg|jpeg|png|webp|gif|bmp|svg)$/i.test(currentEntry.fileName);
    var md = isImg ? '![' + currentEntry.fileName + '](' + currentEntry.path + ')' : '[' + currentEntry.fileName + '](' + currentEntry.path + ')';
    if (vscode) {
      vscode.postMessage({
        type: 'copyToClipboard',
        text: md,
        label: '${vscode.l10n.t('Markdown')}'
      });
    }
  };

  document.getElementById('btnCopyPath').onclick = function(e) {
    e.stopPropagation();
    if (!currentEntry) return;
    if (vscode) {
      vscode.postMessage({
        type: 'copyToClipboard',
        text: currentEntry.path,
        label: '${vscode.l10n.t('Path')}'
      });
    }
  };

  document.getElementById('btnOpenFile').onclick = function(e) {
    e.stopPropagation();
    if (!currentEntry) return;
    if (vscode) {
      vscode.postMessage({
        type: 'openFile',
        filePath: currentEntry.path
      });
    }
  };

  var dz = document.getElementById('dropzone');

  dz.onclick = function(e) {
    if (e.target.tagName === 'BUTTON') return;
    document.getElementById('fileInput').click();
  };

  dz.onkeydown = function(e) {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      document.getElementById('fileInput').click();
    }
  };

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

  // Ctrl+V 이미지 붙여넣기
  document.addEventListener('paste', function(e) {
    var items = e.clipboardData && e.clipboardData.items;
    if (!items) return;
    for (var i = 0; i < items.length; i++) {
      var item = items[i];
      if (item.kind === 'file') {
        var file = item.getAsFile();
        if (file) {
          handleFiles([file]);
          break;
        }
      }
    }
  });

  // 메시지 수신
  window.addEventListener('message', function(e) {
    var msg = e.data;
    if (!msg) return;
    switch (msg.type) {
      case 'historyLoaded':
        renderHistory(msg.history);
        if (msg.history && msg.history.length > 0 && !currentEntry) {
          updatePreview(msg.history[0], msg.history[0].webviewUri);
        }
        break;
      case 'uploadComplete':
        updatePreview(msg.entry, msg.webviewUri);
        renderHistory(msg.history);
        showToast('${vscode.l10n.t('Saved & Markdown copied to clipboard!')}');
        break;
      case 'uploadError':
        showToast('${vscode.l10n.t('Upload failed: {0}', '{0}')}'.replace('{0}', msg.error || ''));
        break;
      case 'copied':
        showToast('📋 ' + (msg.label || '') + ' ${vscode.l10n.t('copied to clipboard!')}');
        break;
    }
  });

  if (vscode) vscode.postMessage({ type: 'ready' });
</script>
</body>
</html>`;
  }
}

