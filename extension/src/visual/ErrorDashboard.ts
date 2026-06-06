// VibeZoo Wave 7: Error Dashboard
// registry.json을 감시하여 실시간 에러 현황판 표시
// VisualVibePanels의 fs.watchFile 패턴 재사용

import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';

const REGISTRY_PATH = path.join(os.homedir(), '.vibezoo-errors', 'registry.json');

export class ErrorDashboard {
  private panel: vscode.WebviewPanel | null = null;
  private _watching = false;
  private lastMtime = { current: 0 };
  /** fs.watchFile()이 반환하는 StatWatcher 참조 (dispose 체인용) */
  private _watcherRef: fs.StatWatcher | null = null;

  open(): vscode.WebviewPanel {
    if (this.panel) {
      this.panel.reveal(vscode.ViewColumn.Two);
      return this.panel;
    }

    this.panel = vscode.window.createWebviewPanel(
      'vibezoo-error-dashboard',
      '🐞 VibeZoo Error Dashboard',
      vscode.ViewColumn.Two,
      { enableScripts: true, retainContextWhenHidden: true }
    );

    this.panel.webview.html = this.getHtml();
    this.startWatching();

    this.panel.onDidDispose(() => {
      this.panel = null;
      this.stopWatching();
    });

    // 초기 데이터 로드
    this.sendData();

    return this.panel;
  }

  private startWatching(): void {
    if (this._watching) return;
    this._watching = true;
    this.lastMtime.current = this.getCurrentMtime();

    this._watcherRef = fs.watchFile(REGISTRY_PATH, { interval: 500 }, () => {
      const newMtime = this.getCurrentMtime();
      if (newMtime > this.lastMtime.current) {
        this.lastMtime.current = newMtime;
        this.sendData();
      }
    });
  }

  private stopWatching(): void {
    if (!this._watching) return;
    try {
      if (this._watcherRef) {
        fs.unwatchFile(REGISTRY_PATH);
        this._watcherRef = null;
      }
    } catch { /* ignore */ }
    this._watching = false;
  }

  private getCurrentMtime(): number {
    try { return fs.statSync(REGISTRY_PATH).mtimeMs; }
    catch { return 0; }
  }

  private sendData(): void {
    try {
      if (!fs.existsSync(REGISTRY_PATH)) return;
      const raw = fs.readFileSync(REGISTRY_PATH, 'utf-8');
      const data = JSON.parse(raw);
      this.panel?.webview.postMessage({ type: 'update', data });
    } catch { /* ignore */ }
  }

  private getHtml(): string {
    return `<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: var(--vscode-editor-background, #1e1e1e); color: var(--vscode-foreground, #ccc); font-family: var(--vscode-font-family, sans-serif); padding: 20px; overflow-y: auto; }
  h1 { font-size: 1.5em; margin-bottom: 20px; color: #f44747; }
  .section { margin-bottom: 24px; }
  .section h2 { font-size: 1.1em; margin-bottom: 8px; border-bottom: 1px solid #444; padding-bottom: 4px; }
  .stat-row { display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 12px; }
  .stat { background: #2d2d2d; padding: 10px 16px; border-radius: 8px; min-width: 120px; }
  .stat .label { font-size: 0.75em; color: #888; }
  .stat .value { font-size: 1.5em; font-weight: bold; }
  .stat .value.success { color: #6acb6a; }
  .stat .value.warning { color: #ffd700; }
  .stat .value.error { color: #f44747; }
  table { width: 100%; border-collapse: collapse; font-size: 0.85em; }
  th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid #333; }
  th { color: #888; font-weight: normal; }
  .critical { color: #f44747; font-weight: bold; }
  .error-row:hover { background: #2a2a2a; }
  .badge { display: inline-block; padding: 2px 6px; border-radius: 4px; font-size: 0.7em; }
  .badge.critical { background: #f44747; color: #fff; }
  .badge.warning { background: #ffd700; color: #000; }
  .empty { color: #888; text-align: center; padding: 40px; }
  .auto-refresh { font-size: 0.7em; color: #666; margin-top: 20px; text-align: right; }
  .bar-chart { display: flex; gap: 8px; align-items: flex-end; height: 100px; padding: 8px 0; }
  .bar-item { display: flex; flex-direction: column; align-items: center; flex: 1; }
  .bar { width: 100%; min-height: 4px; border-radius: 4px 4px 0 0; transition: height 0.3s; position: relative; }
  .bar .bar-count { position: absolute; top: -18px; left: 50%; transform: translateX(-50%); font-size: 0.75em; color: #ccc; }
  .bar-label { font-size: 0.65em; color: #888; margin-top: 4px; text-align: center; word-break: break-all; max-width: 120px; }
</style>
</head><body>
<h1>🐞 Error Dashboard</h1>

<div class="section">
  <h2>📊 요약</h2>
  <div class="stat-row" id="summary"></div>
</div>

<div class="section">
  <h2>🔥 빈도 Top 5</h2>
  <div class="bar-chart" id="top-freq-bars"></div>
  <div id="top-freq-table"></div>
</div>

<div class="section">
  <h2>📋 최근 에러 (20개)</h2>
  <div id="recent-errors"></div>
</div>

<div class="auto-refresh">🔄 auto-refresh via FileSystemWatcher</div>

<script>
  const vscode = acquireVsCodeApi();

  function escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/&/g,'&').replace(/</g,'<').replace(/>/g,'>').replace(/"/g,'"');
  }

  function render(data) {
    if (!data || data.length === 0) {
      document.getElementById('recent-errors').innerHTML = '<div class="empty">✅ No errors recorded</div>';
      document.getElementById('summary').innerHTML = '<div class="stat"><div class="label">Total Errors</div><div class="value success">0</div></div>';
      document.getElementById('top-freq-bars').innerHTML = '';
      document.getElementById('top-freq-table').innerHTML = '';
      return;
    }

    // 빈도 집계
    const freq = {};
    let autoFixTotal = 0, autoFixSuccess = 0;
    data.forEach(function(e) {
      const sig = (e.tool || '?') + ':' + (e.exception_type || '?');
      freq[sig] = (freq[sig] || 0) + 1;
      if (e.auto_fix_attempted) {
        autoFixTotal++;
        if (e.auto_fix_success) autoFixSuccess++;
      }
    });

    // Top 5 정렬
    const sorted = Object.entries(freq).sort(function(a, b) { return b[1] - a[1]; }).slice(0, 5);
    const maxCount = sorted.length > 0 ? sorted[0][1] : 1;

    // 막대 그래프
    const barsHtml = sorted.length > 0
      ? sorted.map(function(_a) {
          var sig = _a[0], cnt = _a[1];
          var pct = Math.max(8, (cnt / maxCount) * 100);
          var isCrit = cnt >= 5;
          var color = isCrit ? '#f44747' : '#ffd700';
          var shortLabel = sig.length > 25 ? sig.substring(0, 22) + '...' : sig;
          return '<div class="bar-item"><div class="bar" style="height:' + pct + 'px;background:' + color + '"><span class="bar-count">' + cnt + '</span></div><div class="bar-label" title="' + escapeHtml(sig) + '">' + escapeHtml(shortLabel) + '</div></div>';
        }).join('')
      : '<div class="empty">-</div>';
    document.getElementById('top-freq-bars').innerHTML = barsHtml;

    // Top 5 테이블
    const topHtml = sorted.length > 0
      ? '<table><tr><th>Signature</th><th>Count</th><th>Status</th></tr>' +
        sorted.map(function(_a) {
          var sig = _a[0], cnt = _a[1];
          var isCrit = cnt >= 5;
          return '<tr class="' + (isCrit ? 'critical' : '') + '"><td>' + escapeHtml(sig) + '</td><td>' + cnt + '</td><td>' + (isCrit ? '<span class="badge critical">⚠️ CRITICAL</span>' : '<span class="badge warning">⚠️</span>') + '</td></tr>';
        }).join('') + '</table>'
      : '<div class="empty">-</div>';
    document.getElementById('top-freq-table').innerHTML = topHtml;

    // 요약
    const successRate = autoFixTotal > 0 ? Math.round(autoFixSuccess / autoFixTotal * 100) : 0;
    document.getElementById('summary').innerHTML =
      '<div class="stat"><div class="label">Total Errors</div><div class="value error">' + data.length + '</div></div>' +
      '<div class="stat"><div class="label">Unique Types</div><div class="value warning">' + Object.keys(freq).length + '</div></div>' +
      '<div class="stat"><div class="label">Auto-Fix Rate</div><div class="value ' + (successRate >= 50 ? 'success' : 'warning') + '">' + successRate + '%</div></div>' +
      '<div class="stat"><div class="label">Auto-Fix Total</div><div class="value">' + autoFixTotal + '</div></div>';

    // 최근 에러
    const recent = data.slice(0, 20);
    const recentHtml = recent.length > 0
      ? '<table><tr><th>Time</th><th>Tool</th><th>Exception</th><th>File</th></tr>' +
        recent.map(function(e) {
          var time = e.timestamp ? new Date(e.timestamp).toLocaleTimeString() : '?';
          var sig = (e.tool || '?') + ':' + (e.exception_type || '?');
          var isCrit = (freq[sig] || 0) >= 5;
          var msgPreview = (e.exception_message || '').substring(0, 60);
          return '<tr class="error-row ' + (isCrit ? 'critical' : '') + '"><td>' + escapeHtml(time) + '</td><td>' + escapeHtml(e.tool || '') + '</td><td>' + escapeHtml(e.exception_type || '') + ': ' + escapeHtml(msgPreview) + '</td><td>' + escapeHtml(e.file_line || '') + '</td></tr>';
        }).join('') + '</table>'
      : '<div class="empty">-</div>';
    document.getElementById('recent-errors').innerHTML = recentHtml;
  }

  window.addEventListener('message', function(event) {
    if (event.data && event.data.type === 'update') {
      render(event.data.data);
    }
  });
</script>
</body></html>`;
  }

  dispose(): void {
    this.stopWatching();
    this.panel?.dispose();
  }
}
