// VibeZoo Wave 5: Visual Vibe 통합 패널
// Whiteboard, UI Preview, Diagram 등 Webview 패널 생성
// AI가 MCP 도구(draw_on_whiteboard, open_whiteboard)를 호출하면
// 파일 감시를 통해 자동으로 패널을 열고 그림을 렌더링한다.

import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';

export class VisualVibePanels {
  private whiteboardPanel: vscode.WebviewPanel | null = null;
  private uiPreviewPanel: vscode.WebviewPanel | null = null;
  private diagramPanel: vscode.WebviewPanel | null = null;
  private watchTimer: NodeJS.Timeout | null = null;
  private homedir: string;

  constructor() {
    this.homedir = os.homedir();
    this.startWatching();
  }

  /** AI가 MCP 도구로 호출한 Whiteboard/UI 명령 파일 감시 */
  private startWatching(): void {
    const wbFile = path.join(this.homedir, '.vibezoo-whiteboard.json');
    const wbAction = path.join(this.homedir, '.vibezoo-whiteboard-action.json');
    const uiAction = path.join(this.homedir, '.vibezoo-ui-action.json');

    let lastWbMtime = 0;
    let lastActionMtime = 0;
    let lastUiMtime = 0;

    this.watchTimer = setInterval(() => {
      // Whiteboard action 감지 (open_whiteboard 호출)
      try {
        const wbStat = fs.statSync(wbAction);
        if (wbStat.mtimeMs > lastActionMtime) {
          lastActionMtime = wbStat.mtimeMs;
          const content = JSON.parse(fs.readFileSync(wbAction, 'utf-8'));
          if (content.action === 'open') {
            this.openWhiteboard();
            if (content.message) {
              vscode.window.showInformationMessage(`🎨 VibeZoo: ${content.message}`);
            }
          }
        }
      } catch {}

      // UI Preview action 감지 (open_ui_preview 호출)
      try {
        const uiStat = fs.statSync(uiAction);
        if (uiStat.mtimeMs > lastUiMtime) {
          lastUiMtime = uiStat.mtimeMs;
          const content = JSON.parse(fs.readFileSync(uiAction, 'utf-8'));
          if (content.action === 'open_ui') {
            this.openUIPreview(content.code || '', content.framework || 'react');
          }
        }
      } catch {}

      // Whiteboard drawing 명령 감지 (draw_on_whiteboard 호출)
      try {
        const wbStat = fs.statSync(wbFile);
        if (wbStat.mtimeMs > lastWbMtime) {
          lastWbMtime = wbStat.mtimeMs;
          const content = JSON.parse(fs.readFileSync(wbFile, 'utf-8'));
          if (content.commands && content.commands.length > 0) {
            // Whiteboard가 아직 안 열렸으면 자동 열기
            if (!this.whiteboardPanel) {
              this.openWhiteboard();
            }
            // 드로잉 명령 Webview에 전달
            this.sendToWhiteboard(content.commands);
          }
        }
      } catch {}
    }, 1000); // 1초 폴링
  }

  /** AI의 드로잉 명령을 Whiteboard Webview로 전달 */
  private sendToWhiteboard(commands: any[]): void {
    if (this.whiteboardPanel) {
      this.whiteboardPanel.webview.postMessage({ type: 'draw', commands });
    }
  }

  /** Whiteboard 열기 — Fabric.js 기반 드로잉 캔버스 */
  openWhiteboard(): vscode.WebviewPanel {
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
    this.whiteboardPanel.onDidDispose(() => { this.whiteboardPanel = null; });
    return this.whiteboardPanel;
  }

  /** UI Preview 열기 — React/Vue 컴포넌트 실시간 렌더링 */
  openUIPreview(initialCode?: string, _framework?: string): vscode.WebviewPanel {
    if (this.uiPreviewPanel) {
      this.uiPreviewPanel.reveal(vscode.ViewColumn.Two);
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

    // AI 코드 생성 시 postMessage로 코드 전달
    this.uiPreviewPanel.webview.onDidReceiveMessage((message) => {
      if (message.type === 'render') {
        this.uiPreviewPanel?.webview.postMessage({
          type: 'render',
          code: message.code,
        });
      }
    });

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

  /** 모든 패널 정리 */
  dispose(): void {
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
  <button onclick="clearAll()">🗑️ 전체 삭제</button>
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

  function clearAll() { canvas.clear(); canvas.backgroundColor = '#1e1e1e'; }

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
  window.addEventListener('message', (event) => {
    if (event.data.type === 'render' && event.data.code) {
      document.body.innerHTML = '<iframe sandbox="allow-scripts" srcdoc="' +
        event.data.code.replace(/"/g, '"') + '"></iframe>';
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
  window.addEventListener('message', async (event) => {
    if (event.data.type === 'render' && event.data.mermaidCode) {
      const { svg } = await mermaid.render('diagram', event.data.mermaidCode);
      document.getElementById('diagram').innerHTML = svg;
    }
  });
</script>
</body></html>`;
  }
}
