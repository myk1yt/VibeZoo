// VibeZoo Wave 5: Visual Vibe 통합 패널
// Whiteboard, UI Preview, Diagram 등 Webview 패널 생성
// AI가 MCP 도구(draw_on_whiteboard, open_whiteboard)를 호출하면
// 파일 감시를 통해 자동으로 패널을 열고 그림을 렌더링한다.
//
// ★ 2026-05-27: 무한 알람 수정
//   - setInterval 폴링 → fs.watchFile() 이벤트 기반 감시
//   - showInformationMessage → log() (사용자 알람 제거)
//   - startWatching()은 Whiteboard가 실제로 열릴 때만 시작

import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { exec } from 'child_process';

const log = (msg: string, ...args: any[]) => {
  if (process.env.VIBEZOO_DEBUG) console.log(`[VibeZoo::Visual] ${msg}`, ...args);
};

export class VisualVibePanels {
  private whiteboardPanel: vscode.WebviewPanel | null = null;
  private uiPreviewPanel: vscode.WebviewPanel | null = null;
  private diagramPanel: vscode.WebviewPanel | null = null;
  private homedir: string;
  private _activated = false;
  /** Watcher가 이미 시작되었는지 플래그 (중복 시작 방지) */
  private _watching = false;

  /** 마지막으로 보낸 명령어의 해시 (중복 전송 방지) */
  private _lastCommandsHash: string = '';

  constructor() {
    this.homedir = os.homedir();
    // NOTE: startWatching()은 openWhiteboard()에서 호출 — 생성자/activate()에서 즉시 시작하지 않음
  }

  /** Visual 감시 준비 (activate()에서 조건부 호출) */
  activate(): void {
    if (this._activated) return;
    this._activated = true;
    // ★ startWatching() 제거 — Whiteboard가 실제로 열릴 때만 감시 시작
    log('VisualVibePanels activated (watching deferred until whiteboard opens)');
  }

  /** 파일의 현재 mtime을 반환 (없으면 0) */
  private getCurrentMtime(filePath: string): number {
    try {
      const stat = fs.statSync(filePath);
      return stat.mtimeMs;
    } catch {
      return 0;
    }
  }

  /**
   * Whiteboard / UI action 파일 감시 시작 (fs.watchFile 기반)
   * setInterval 폴링 대신 fs.watchFile을 사용하여 OS 이벤트에 반응.
   * startWatching()은 openWhiteboard()에서 최초 1회 호출됨.
   */
  private startWatching(): void {
    if (this._watching) return;
    this._watching = true;

    const wbFile = path.join(this.homedir, '.vibezoo-whiteboard.json');
    const wbAction = path.join(this.homedir, '.vibezoo-whiteboard-action.json');
    const uiAction = path.join(this.homedir, '.vibezoo-ui-action.json');

    // ★ 중요: lastMtime을 객체로 유지해야 콜백 내부에서 .current 업데이트가 반영됨
    const lastWbMtime = { current: this.getCurrentMtime(wbFile) };
    const lastActionMtime = { current: this.getCurrentMtime(wbAction) };
    const lastUiMtime = { current: this.getCurrentMtime(uiAction) };

    /** 공통 파일 변경 핸들러: 변경 시 파일을 읽고 onChange 콜백 실행 */
    const handleFileChange = async (
      filePath: string,
      lastMtime: { current: number },
      onChange: (content: any) => void,
    ): Promise<void> => {
      try {
        const stat = await fs.promises.stat(filePath);
        if (stat.mtimeMs > lastMtime.current) {
          lastMtime.current = stat.mtimeMs;
          const contentStr = await fs.promises.readFile(filePath, 'utf-8');
          const content = JSON.parse(contentStr);
          onChange(content);
        }
      } catch {
        // 파일이 아직 없거나 읽을 수 없음 — 무시
      }
    };

    // ── whiteboard-action.json 감시 (open_whiteboard MCP 도구) ──
    fs.watchFile(wbAction, { interval: 500 }, (curr) => {
      if (curr.mtimeMs > lastActionMtime.current) {
        lastActionMtime.current = curr.mtimeMs;
        handleFileChange(wbAction, lastActionMtime, (content) => {
          if (content.action === 'open') {
            this.openWhiteboard();
            if (content.message) {
              // ★ showInformationMessage 제거 — log()로 대체 (무한 알람 방지)
              log(`Whiteboard action: ${content.message}`);
            }
          }
        });
      }
    });

    // ── ui-action.json 감시 (open_ui_preview MCP 도구) ──
    fs.watchFile(uiAction, { interval: 500 }, (curr) => {
      if (curr.mtimeMs > lastUiMtime.current) {
        lastUiMtime.current = curr.mtimeMs;
        handleFileChange(uiAction, lastUiMtime, (content) => {
          if (content.action === 'open_ui') {
            this.openUIPreview(content.code || '', content.framework || 'react');
          }
        });
      }
    });

    // ── whiteboard.json 감시 (draw_on_whiteboard MCP 도구) ──
    fs.watchFile(wbFile, { interval: 500 }, (curr) => {
      if (curr.mtimeMs > lastWbMtime.current) {
        lastWbMtime.current = curr.mtimeMs;
        handleFileChange(wbFile, lastWbMtime, (content) => {
          // ★ canvasState에서 쓴 내용은 건너뜀 (무한 루프 방지)
          if (content._source === 'canvasState') return;
          if (content.commands && content.commands.length > 0) {
            // 중복 전송 방지: JSON 문자열이 동일하면 스킵
            const hash = JSON.stringify(content.commands);
            if (hash === this._lastCommandsHash) return;
            this._lastCommandsHash = hash;

            // Whiteboard가 아직 안 열렸으면 자동 열기
            if (!this.whiteboardPanel) {
              this.openWhiteboard();
              // Webview HTML 로드 대기 → ready 메시지에서 pending commands 전송
              (this as any)._pendingDrawCommands = content.commands;
            } else {
              // 드로잉 명령 Webview에 전달
              this.sendToWhiteboard(content.commands);
            }
          }
        });
      }
    });

    log('File watching started (fs.watchFile)');
  }

  /** AI의 드로잉 명령을 Whiteboard Webview로 전달 */
  private sendToWhiteboard(commands: any[]): void {
    if (this.whiteboardPanel) {
      this.whiteboardPanel.webview.postMessage({ type: 'draw', commands });
    }
  }

  /** Whiteboard 열기 — Fabric.js 기반 드로잉 캔버스 */
  openWhiteboard(): vscode.WebviewPanel {
    // ★ Whiteboard가 열릴 때 watcher 시작 (최초 1회)
    this.startWatching();

    if (this.whiteboardPanel) {
      this.whiteboardPanel.reveal(vscode.ViewColumn.Two);
      return this.whiteboardPanel;
    }

    this.whiteboardPanel = vscode.window.createWebviewPanel(
      'vibezoo-whiteboard',
      '🎨 VibeZoo Whiteboard',
      vscode.ViewColumn.Two,
      {
        enableScripts: true,
        retainContextWhenHidden: true,
      }
    );

    this.whiteboardPanel.webview.html = this.whiteboardHtml();

    // Webview → Extension: 사용자가 그린 내용 자동 저장 + 캡처
    this.whiteboardPanel.webview.onDidReceiveMessage(async (message) => {
      if (message.type === 'canvasState') {
        const wbFile = path.join(os.homedir(), '.vibezoo-whiteboard.json');
        // ★ _source: "canvasState" 마커를 추가하여 watcher가 이 변경을 무시하게 함
        //    (AI의 draw_on_whiteboard 명령과 구분하여 무한 루프 방지)
        const data = { _source: 'canvasState', timestamp: Date.now(), commands: message.commands };
        try {
          fs.writeFileSync(wbFile, JSON.stringify(data, null, 2), 'utf-8');
        } catch {}
      }
      if (message.type === 'captureScreenshot') {
        // 캡처 도구 실행 → 클립보드 이미지 자동 로드
        this.handleCaptureScreenshot();
      }
      if (message.type === 'ready') {
        // Webview HTML 로드 완료 → 대기 중인 드로잉 명령 전송
        if ((this as any)._pendingDrawCommands) {
          this.sendToWhiteboard((this as any)._pendingDrawCommands);
          delete (this as any)._pendingDrawCommands;
        }
      }
    });

    this.whiteboardPanel.onDidDispose(() => { this.whiteboardPanel = null; });
    return this.whiteboardPanel;
  }

  /** 캡처 도구 실행 → 클립보드 이미지를 Whiteboard에 자동 로드 */
  private handleCaptureScreenshot(): void {
    const tmpFile = path.join(os.tmpdir(), `vibezoo-capture-${Date.now()}.png`);

    // Step 1: 캡처 도구 실행 (Windows: Snipping Tool, macOS: screencapture)
    const openCaptureTool = process.platform === 'win32'
      ? `powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; Start-Process ms-screenclip: -Wait -WindowStyle Hidden; $img = [System.Windows.Forms.Clipboard]::GetImage(); if ($img) { $img.Save('${tmpFile}', [System.Drawing.Imaging.ImageFormat]::Png) }"`
      : process.platform === 'darwin'
        ? `screencapture -i -c "${tmpFile}" 2>/dev/null; osascript -e 'tell app "System Events" to set theImage to the clipboard as «class PNGf»' -e 'if theImage is not missing value then set imgFile to open for access "${tmpFile}" with write permission' -e 'write theImage to imgFile' -e 'close access imgFile'`
        : null;

    if (!openCaptureTool) {
      log('Capture not supported on this platform');
      return;
    }

    exec(openCaptureTool, { timeout: 60000 }, (err) => {
      if (err) {
        log('Capture tool error:', err.message);
        // 클립보드에 이미지가 없으면 조용히 무시
        try { if (fs.existsSync(tmpFile)) fs.unlinkSync(tmpFile); } catch {}
        return;
      }
      // Step 2: 임시 파일 읽어서 Webview로 전송
      setTimeout(() => {
        try {
          if (fs.existsSync(tmpFile) && fs.statSync(tmpFile).size > 0) {
            const imgData = fs.readFileSync(tmpFile, 'base64');
            fs.unlinkSync(tmpFile);
            this.whiteboardPanel?.webview.postMessage({
              type: 'loadLatestScreenshot',
              dataUrl: `data:image/png;base64,${imgData}`
            });
          } else {
            try { if (fs.existsSync(tmpFile)) fs.unlinkSync(tmpFile); } catch {}
          }
        } catch (e: any) {
          log('Capture read error:', e.message);
          try { if (fs.existsSync(tmpFile)) fs.unlinkSync(tmpFile); } catch {}
        }
      }, 500);
    });
  }

  /** UI Preview 열기 — React/Vue 컴포넌트 실시간 렌더링 */
  openUIPreview(initialCode?: string, _framework?: string): vscode.WebviewPanel {
    if (this.uiPreviewPanel) {
      this.uiPreviewPanel.reveal(vscode.ViewColumn.Two);
      // 기존 패널에 새 코드 전송
      if (initialCode) {
        this.uiPreviewPanel.webview.postMessage({ type: 'render', code: initialCode });
      }
      return this.uiPreviewPanel;
    }

    this.uiPreviewPanel = vscode.window.createWebviewPanel(
      'vibezoo-ui-preview',
      '🖼️ VibeZoo UI Preview',
      vscode.ViewColumn.Two,
      {
        enableScripts: true,
        retainContextWhenHidden: true,
      }
    );

    this.uiPreviewPanel.webview.html = this.uiPreviewHtml();
    this.uiPreviewPanel.onDidDispose(() => { this.uiPreviewPanel = null; });

    // Webview 로드 완료 후 초기 코드 전송 (중복 방지)
    if (initialCode) {
      const panel = this.uiPreviewPanel;
      let sent = false;
      const checkReady = (msg: any) => {
        if (msg.type === 'ready' && !sent) {
          sent = true;
          panel.webview.postMessage({ type: 'render', code: initialCode });
        }
      };
      panel.webview.onDidReceiveMessage(checkReady);
      // fallback: ready 신호가 없어도 600ms 후 전송 (단, ready에서 이미 보냈으면 skip)
      setTimeout(() => {
        if (!sent) {
          sent = true;
          try { panel.webview.postMessage({ type: 'render', code: initialCode }); } catch {}
        }
      }, 600);
    }

    return this.uiPreviewPanel;
  }

  /** Diagram 열기 — Mermaid.js + D3.js */
  openDiagram(diagramType?: string): vscode.WebviewPanel {
    if (this.diagramPanel) {
      this.diagramPanel.reveal(vscode.ViewColumn.Two);
      return this.diagramPanel;
    }

    this.diagramPanel = vscode.window.createWebviewPanel(
      'vibezoo-diagram',
      '📊 VibeZoo Diagram',
      vscode.ViewColumn.Two,
      {
        enableScripts: true,
        retainContextWhenHidden: true,
      }
    );

    this.diagramPanel.webview.html = this.diagramHtml(diagramType);
    this.diagramPanel.onDidDispose(() => { this.diagramPanel = null; });
    return this.diagramPanel;
  }

  /** 모든 패널 정리 + 파일 감시 중단 */
  dispose(): void {
    // ★ fs.watchFile 해제
    if (this._watching) {
      const wbFile = path.join(this.homedir, '.vibezoo-whiteboard.json');
      const wbAction = path.join(this.homedir, '.vibezoo-whiteboard-action.json');
      const uiAction = path.join(this.homedir, '.vibezoo-ui-action.json');
      try { fs.unwatchFile(wbFile); } catch {}
      try { fs.unwatchFile(wbAction); } catch {}
      try { fs.unwatchFile(uiAction); } catch {}
      this._watching = false;
      log('File watching stopped');
    }
    this.whiteboardPanel?.dispose();
    this.uiPreviewPanel?.dispose();
    this.diagramPanel?.dispose();
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
  canvas { display: block; }
</style>
<script src="https://cdnjs.cloudflare.com/ajax/libs/fabric.js/5.3.1/fabric.min.js"></script>
</head><body>
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
  const canvas = new fabric.Canvas('c', {
    isDrawingMode: true,
    width: window.innerWidth,
    height: window.innerHeight,
    backgroundColor: '#1e1e1e',
  });
  canvas.freeDrawingBrush.color = '#ffffff';
  canvas.freeDrawingBrush.width = 3;

  // Webview 로드 완료 → Extension에 ready 신호 전송 (pending draw commands flush)
  const vscodeApi = typeof acquireVsCodeApi !== 'undefined' ? acquireVsCodeApi() : null;
  if (vscodeApi) vscodeApi.postMessage({ type: 'ready' });

  // Auto-save on every change → sends to extension via postMessage
  function sendState() {
    const vscode = typeof acquireVsCodeApi !== 'undefined' ? acquireVsCodeApi() : null;
    if (vscode) {
      const state = canvas.toJSON ? canvas.toJSON() : {};
      vscode.postMessage({ type: 'canvasState', commands: state.objects || [] });
    }
  }
  canvas.on('object:added', () => setTimeout(sendState, 150));
  canvas.on('object:modified', () => setTimeout(sendState, 150));
  canvas.on('object:removed', () => setTimeout(sendState, 150));

  // 캡처 → Windows Snipping Tool → 자동 로드
  function captureScreenshot() {
    const vscode = typeof acquireVsCodeApi !== 'undefined' ? acquireVsCodeApi() : null;
    if (vscode) {
      vscode.postMessage({ type: 'captureScreenshot' });
    }
  }
  // ============================================================
  // AI Draw 명령 처리기 — Extension에서 보낸 type:'draw' 메시지
  // ============================================================
  function executeCommands(commands) {
    if (!commands || !Array.isArray(commands)) return;
    commands.forEach(function(cmd) {
      if (!cmd || !cmd.type) return;
      var props = cmd.props || {};
      switch (cmd.type) {
        case 'polygon': {
          // points: [{x:0,y:0}, {x:100,y:0}, ...]
          var pts = (props.points || []).map(function(p) { return new fabric.Point(p.x, p.y); });
          if (pts.length < 3) break;
          var poly = new fabric.Polygon(pts, {
            fill: props.fill || 'transparent',
            stroke: props.stroke || '#ff6b6b',
            strokeWidth: props.strokeWidth || 2,
            left: props.left || 0,
            top: props.top || 0,
            objectCaching: false
          });
          canvas.add(poly);
          break;
        }
        case 'rect': {
          var rect = new fabric.Rect({
            left: props.left || 100,
            top: props.top || 100,
            width: props.width || 200,
            height: props.height || 150,
            fill: props.fill || 'transparent',
            stroke: props.stroke || '#4ec9ff',
            strokeWidth: props.strokeWidth || 2,
            rx: props.rx || 0,
            ry: props.ry || 0
          });
          canvas.add(rect);
          break;
        }
        case 'circle': {
          var circle = new fabric.Circle({
            left: props.left || 100,
            top: props.top || 100,
            radius: props.radius || 80,
            fill: props.fill || 'transparent',
            stroke: props.stroke || '#ffd700',
            strokeWidth: props.strokeWidth || 2
          });
          canvas.add(circle);
          break;
        }
        case 'line': {
          var line = new fabric.Line(
            [props.x1 || 0, props.y1 || 0, props.x2 || 200, props.y2 || 200],
            {
              left: props.left || 0,
              top: props.top || 0,
              stroke: props.stroke || '#ffffff',
              strokeWidth: props.strokeWidth || 2
            }
          );
          canvas.add(line);
          break;
        }
        case 'text': {
          var text = new fabric.Textbox(props.text || '텍스트', {
            left: props.left || 100,
            top: props.top || 100,
            width: props.width || 300,
            fontSize: props.fontSize || 20,
            fill: props.fill || '#ffffff',
            fontFamily: props.fontFamily || 'sans-serif'
          });
          canvas.add(text);
          break;
        }
        case 'arrow': {
          // 화살표는 선 + 삼각형 헤드로 구현
          var x1 = props.x1 || 0, y1 = props.y1 || 0;
          var x2 = props.x2 || 200, y2 = props.y2 || 200;
          var arrColor = props.stroke || '#ffffff';
          var arrWidth = props.strokeWidth || 2;
          var line = new fabric.Line([x1, y1, x2, y2], {
            left: props.left || 0,
            top: props.top || 0,
            stroke: arrColor,
            strokeWidth: arrWidth
          });
          canvas.add(line);
          // 화살촉 삼각형
          var angle = Math.atan2(y2 - y1, x2 - x1);
          var headLen = 15;
          var headPts = [
            { x: x2, y: y2 },
            { x: x2 - headLen * Math.cos(angle - Math.PI/6), y: y2 - headLen * Math.sin(angle - Math.PI/6) },
            { x: x2 - headLen * Math.cos(angle + Math.PI/6), y: y2 - headLen * Math.sin(angle + Math.PI/6) }
          ];
          var head = new fabric.Polygon(headPts.map(function(p) { return new fabric.Point(p.x, p.y); }), {
            fill: arrColor,
            stroke: arrColor,
            strokeWidth: 1,
            objectCaching: false
          });
          canvas.add(head);
          break;
        }
        case 'freehand': {
          // freehand path: props.path (array of fabric point arrays)
          if (props.path) {
            var path = new fabric.Path(props.path, {
              left: props.left || 0,
              top: props.top || 0,
              stroke: props.stroke || '#ffffff',
              strokeWidth: props.strokeWidth || 3,
              fill: null
            });
            canvas.add(path);
          }
          break;
        }
        case 'clear': {
          canvas.clear();
          canvas.backgroundColor = '#1e1e1e';
          break;
        }
      }
    });
    canvas.renderAll();
    setTimeout(sendState, 200);
  }

  window.addEventListener('message', (e) => {
    // 🔥 draw 명령 처리 (AI가 draw_on_whiteboard로 보낸 polygon, rect 등)
    if (e.data?.type === 'draw' && e.data?.commands) {
      executeCommands(e.data.commands);
      return;
    }
    if (e.data?.type === 'loadLatestScreenshot' && e.data?.dataUrl) {
      fabric.Image.fromURL(e.data.dataUrl, (img) => {
        img.set({ left: 50, top: 50 });
        img.scaleToWidth(Math.min(canvas.width * 0.8, 600));
        canvas.add(img);
        canvas.renderAll();
        setTimeout(sendState, 150);
      });
    }
  });

  // 파일 선택으로 이미지 추가
  function addImage(input) {
    const file = input.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      fabric.Image.fromURL(ev.target.result, (img) => {
        img.set({ left: 50, top: 50 });
        img.scaleToWidth(Math.min(canvas.width * 0.8, 600));
        canvas.add(img);
        canvas.renderAll();
        setTimeout(sendState, 150);
      });
    };
    reader.readAsDataURL(file);
    input.value = '';
  }

  // Ctrl+V 이미지 붙여넣기 (Webview가 허용하는 경우만)
  document.addEventListener('paste', (e) => {
    const items = e.clipboardData?.items;
    if (!items) return;
    for (let item of items) {
      if (item.type.startsWith('image/')) {
        const blob = item.getAsFile();
        if (!blob) continue;
        const reader = new FileReader();
        reader.onload = (ev) => {
          fabric.Image.fromURL(ev.target.result, (img) => {
            img.set({ left: 50, top: 50 });
            img.scaleToWidth(Math.min(canvas.width * 0.8, 600));
            canvas.add(img);
            canvas.renderAll();
            setTimeout(sendState, 150);
          });
        };
        reader.readAsDataURL(blob);
        break;
      }
    }
  });

  function setMode(mode) {
    switch(mode) {
      case 'draw': canvas.isDrawingMode = true; break;
      case 'rect': canvas.isDrawingMode = false; addRect(); break;
      case 'text': canvas.isDrawingMode = false; addText(); break;
      case 'select': canvas.isDrawingMode = false; break;
    }
  }

  function addRect() {
    const rect = new fabric.Rect({ left: 100, top: 100, width: 200, height: 150, fill: 'transparent', stroke: '#4ec9ff', strokeWidth: 2 });
    canvas.add(rect);
  }

  function addText() {
    const text = new fabric.Textbox('텍스트 입력', { left: 100, top: 100, width: 300, fontSize: 20, fill: '#ffffff', fontFamily: 'sans-serif' });
    canvas.add(text);
  }

  function deleteSelected() {
    const active = canvas.getActiveObject();
    if (active) {
      canvas.remove(active);
      canvas.discardActiveObject();
      canvas.renderAll();
      setTimeout(sendState, 150);
    }
  }
  function clearAll() { canvas.clear(); canvas.backgroundColor = '#1e1e1e'; setTimeout(sendState, 150); }

  // Delete key로 선택 객체 삭제
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Delete' || e.key === 'Backspace') {
      deleteSelected();
    }
  });

  window.addEventListener('resize', () => { canvas.setWidth(window.innerWidth); canvas.setHeight(window.innerHeight); });
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
  <p>AI가 React/Vue 컴포넌트 코드를 생성하면 이곳에 실시간 렌더링됩니다.</p>
</div>
<script>
  const vscode = typeof acquireVsCodeApi !== 'undefined' ? acquireVsCodeApi() : null;
  if (vscode) vscode.postMessage({ type: 'ready' });

  window.addEventListener('message', (event) => {
    if (event.data.type === 'render' && event.data.code) {
      // HTML 엔티티 이스케이프 (srcdoc 속성용)
      const escaped = event.data.code
        .replace(/&/g, '&' + 'amp;')
        .replace(/"/g, '&' + 'quot;')
        .replace(/</g, '&' + 'lt;')
        .replace(/>/g, '&' + 'gt;');
      document.body.innerHTML = '<iframe sandbox="allow-scripts" srcdoc="' + escaped + '"></iframe>';
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
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
</head><body>
<div class="placeholder">
  <h2>📊 VibeZoo Diagram${diagramType ? ': ' + diagramType : ''}</h2>
  <div id="diagram"></div>
</div>
<script>
  mermaid.initialize({ startOnLoad: false, theme: 'dark' });
  let mermaidRenderId = 0;
  window.addEventListener('message', async (event) => {
    if (event.data.type === 'render' && event.data.mermaidCode) {
      const container = document.getElementById('diagram');
      container.innerHTML = '';
      const uniqueId = 'mermaid-diagram-' + (++mermaidRenderId);
      try {
        const { svg } = await mermaid.render(uniqueId, event.data.mermaidCode);
        container.innerHTML = svg;
      } catch (err) {
        container.innerHTML = '<p style="color:#f44747">Mermaid 렌더링 오류: ' + err.message + '</p>';
      }
    }
  });
</script>
</body></html>`;
  }
}
