// VibeZoo: Tree View Providers
// Active Subagents, YOLO History, Session Resume 트리 뷰 제공
// ★ M3-F: Active Subagents에 실제 Bridge health check 연동,
//   Session Resume에 Crow/로컬 데이터 표시, CIM 상태 표시

import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import * as os from 'os';
import { SubagentNode, SessionSummary } from '../types';

// ── Bridge Health Check ──────────────────────────────────────

const BRIDGE_HEALTH_URL = 'http://localhost:9027/health';

async function checkBridgeHealth(): Promise<{ ok: boolean; crow: boolean; version: string }> {
  try {
    const resp = await fetch(BRIDGE_HEALTH_URL, { signal: AbortSignal.timeout(3000) });
    if (resp.ok) {
      const data: any = await resp.json();
      return { ok: true, crow: !!data.crow, version: data.version || '?' };
    }
  } catch {}
  return { ok: false, crow: false, version: '?' };
}

// ── Active Subagents Tree ────────────────────────────────────

export class ActiveSubagentsProvider implements vscode.TreeDataProvider<SubagentTreeItem> {
  private _onDidChangeTreeData = new vscode.EventEmitter<SubagentTreeItem | undefined>();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

  private nodes: Map<string, SubagentNode> = new Map();
  private _bridgePort: number = 9027;
  private _bridgeOk: boolean = false;
  private _crowOk: boolean = false;
  private _healthCheckInterval: NodeJS.Timeout | null = null;

  refresh(node?: SubagentNode): void {
    if (node) {
      const item = this.nodes.get(node.id);
      if (item) {
        this.nodes.set(node.id, node);
      }
    }
    this._onDidChangeTreeData.fire(undefined);
  }

  updateNode(node: SubagentNode): void {
    this.nodes.set(node.id, node);
    this._onDidChangeTreeData.fire(undefined);
  }

  removeNode(id: string): void {
    this.nodes.delete(id);
    this._onDidChangeTreeData.fire(undefined);
  }

  /** Bridge health를 주기적으로 확인 (30초 간격) */
  startHealthCheck(): void {
    this.stopHealthCheck();
    this._healthCheckInterval = setInterval(async () => {
      const health = await checkBridgeHealth();
      this._bridgeOk = health.ok;
      this._crowOk = health.crow;
      // 모든 노드 상태 업데이트
      for (const [id, node] of this.nodes) {
        if (id === '_bridge') continue;
        if (!this._bridgeOk) {
          node.status = 'error';
          node.currentTask = 'Bridge disconnected';
        }
      }
      // Subagent 작업 목록 polling
      await this.pollSubagentTasks();
      this._onDidChangeTreeData.fire(undefined);
    }, 30000);
    // Immediate first check
    checkBridgeHealth().then(health => {
      this._bridgeOk = health.ok;
      this._crowOk = health.crow;
      this._onDidChangeTreeData.fire(undefined);
    });
    // Immediate subagent poll
    this.pollSubagentTasks();
  }

  /** SubagentPool의 작업 목록을 30초 간격 polling하여 TreeView에 표시 */
  private async pollSubagentTasks(): Promise<void> {
    try {
      const resp = await fetch('http://localhost:9027/tools/list_subagents', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
        signal: AbortSignal.timeout(5000),
      });
      if (!resp.ok) return;
      const data: any = await resp.json();
      const tasks: any[] = data?.tasks || [];
      // 기존 subagent_* 노드 제거 (리스폰스 기반으로 갱신)
      for (const [id] of this.nodes) {
        if (id.startsWith('subagent_')) {
          this.nodes.delete(id);
        }
      }
      // 새 작업 노드 추가
      for (const task of tasks) {
        const age = task.created_at ? Math.floor((Date.now() / 1000 - task.created_at) / 60) : 0;
        this.nodes.set(`subagent_${task.id}`, {
          id: `subagent_${task.id}`,
          name: `[${task.role}] ${task.description.substring(0, 30)}`,
          status: task.status === 'completed' ? 'completed' :
                  task.status === 'failed' ? 'error' :
                  task.status === 'running' ? 'running' : 'idle',
          currentTask: `${task.status} (${age}m)`,
          port: 0,
          startTime: task.created_at ? task.created_at * 1000 : undefined,
        });
      }
    } catch {
      // Bridge가 아직 준비되지 않음 — 무시
    }
  }

  stopHealthCheck(): void {
    if (this._healthCheckInterval) {
      clearInterval(this._healthCheckInterval);
      this._healthCheckInterval = null;
    }
  }

  /** MCP 브릿지 시작 시 개별 에이전트 노드들을 초기화 + Bridge 상태 노드 추가 */
  initializeAgentNodes(bridgePort: number): void {
    this._bridgePort = bridgePort;
    const agents = [
      { id: 'scout', name: 'Scout', port: vscode.workspace.getConfiguration('vibezoo').get('scout.port', 9022) },
      { id: 'reviewer', name: 'Reviewer', port: vscode.workspace.getConfiguration('vibezoo').get('reviewer.port', 9023) },
      { id: 'tester', name: 'Tester', port: vscode.workspace.getConfiguration('vibezoo').get('tester.port', 9024) },
      { id: 'deepAnalyzer', name: 'Deep Analyzer', port: vscode.workspace.getConfiguration('vibezoo').get('deepAnalyzer.port', 9026) },
    ];
    for (const agent of agents) {
      this.nodes.set(agent.id, {
        id: agent.id,
        name: agent.name,
        status: 'running',
        currentTask: 'Connected via Bridge',
        port: agent.port,
        startTime: Date.now(),
      });
    }
    // 가상 Bridge Health 노드 추가 (최상단에 표시)
    this.nodes.set('_bridge', {
      id: '_bridge',
      name: 'Bridge',
      status: 'running',
      currentTask: `Port ${bridgePort}`,
      port: bridgePort,
      startTime: Date.now(),
    });
    this._onDidChangeTreeData.fire(undefined);
    // Health check 시작
    this.startHealthCheck();
  }

  /** FileGuard 토글 상태 업데이트 */
  setFileGuardStatus(enabled: boolean): void {
    if (enabled) {
      this.nodes.set('_fileguard', {
        id: '_fileguard',
        name: 'FileGuard',
        status: 'running',
        currentTask: 'Protecting files',
        port: 0,
        startTime: Date.now(),
      });
    } else {
      this.nodes.delete('_fileguard');
    }
    this._onDidChangeTreeData.fire(undefined);
  }

  /** CIM 감시 상태 업데이트 */
  setCimStatus(watching: boolean): void {
    const existing = this.nodes.get('_cim');
    if (watching) {
      this.nodes.set('_cim', {
        id: '_cim',
        name: 'CIM Monitor',
        status: 'running',
        currentTask: 'Watching file changes',
        port: 0,
        startTime: Date.now(),
      });
    } else {
      this.nodes.delete('_cim');
    }
    this._onDidChangeTreeData.fire(undefined);
  }

  getTreeItem(element: SubagentTreeItem): vscode.TreeItem {
    return element;
  }

  getChildren(_element?: SubagentTreeItem): Thenable<SubagentTreeItem[]> {
    const nodes = Array.from(this.nodes.values());
    if (nodes.length === 0) {
      const placeholder = new vscode.TreeItem('VibeZoo 대기 중...', vscode.TreeItemCollapsibleState.None);
      placeholder.description = '브릿지 연결 시 자동 표시됩니다';
      placeholder.iconPath = undefined;
      placeholder.label = '$(sync~spin) VibeZoo 대기 중...';
      placeholder.tooltip = 'VibeZoo MCP Bridge가 연결되면 Agent 상태가 표시됩니다.';
      return Promise.resolve([placeholder as any]);
    }
    const items = nodes.map((node) => new SubagentTreeItem(node, this._bridgeOk, this._crowOk));
    // Bridge -> FileGuard -> 이름순 정렬
    items.sort((a, b) => {
      if (a.node.id === '_bridge') return -1;
      if (b.node.id === '_bridge') return 1;
      if (a.node.id === '_fileguard') return -1;
      if (b.node.id === '_fileguard') return 1;
      return a.node.name.localeCompare(b.node.name);
    });
    return Promise.resolve(items);
  }

  dispose(): void {
    this.stopHealthCheck();
  }
}

class SubagentTreeItem extends vscode.TreeItem {
  node: SubagentNode;

  constructor(node: SubagentNode, bridgeOk: boolean = false, crowOk: boolean = false) {
    super(node.name, vscode.TreeItemCollapsibleState.None);

    this.node = node;
    this.id = node.id;
    this.description = node.currentTask || node.status;

    // Special styling for bridge health node
    if (node.id === '_bridge') {
      const statusIcon = bridgeOk ? '$(check)' : '$(error)';
      const statusText = bridgeOk ? 'Connected' : 'Disconnected';
      this.label = `${statusIcon} Bridge (:${node.port})`;
      this.description = statusText;
      this.tooltip = new vscode.MarkdownString(
        `**MCP Bridge**\n\nStatus: ${bridgeOk ? '✅ Connected' : '❌ Disconnected'}\nPort: ${node.port}\nCrow: ${crowOk ? '✅ Connected' : '❌ Disconnected'}\n\nClick to check foundation status.`
      );
      this.contextValue = bridgeOk ? 'connected' : 'disconnected';
      this.command = {
        command: 'vibezoo.verifyFoundation',
        title: 'Check Foundation',
      };
      return;
    }

    // CIM monitor special node
    if (node.id === '_cim') {
      this.label = `$(eye) CIM Monitor`;
      this.description = node.currentTask;
      this.tooltip = new vscode.MarkdownString(
        `**Continuous Improvement Mode**\n\nStatus: Watching file changes\nAuto-build on save: Enabled\n\nClick to stop watching.`
      );
      this.contextValue = 'cim';
      this.command = {
        command: 'vibezoo.stopWatching',
        title: 'Stop CIM',
      };
      return;
    }

    // FileGuard toggle special node
    if (node.id === '_fileguard') {
      const enabled = node.status === 'running';
      this.label = enabled ? '$(shield) FileGuard' : '$(unlock) FileGuard';
      this.description = enabled ? 'ON' : 'OFF';
      this.contextValue = enabled ? 'fileguard-on' : 'fileguard-off';
      this.command = {
        command: 'vibezoo.toggleFileGuard',
        title: 'Toggle FileGuard',
      };
      return;
    }

    // Regular agent nodes
    const iconMap: Record<string, string> = {
      idle: '$(debug-pause)',
      running: '$(sync~spin)',
      completed: '$(check)',
      error: '$(error)',
    };
    this.label = `${iconMap[node.status] || '$(question)'} ${node.name}`;

    const bridgeStatus = bridgeOk ? 'Bridge: Connected' : 'Bridge: Disconnected';
    this.tooltip = new vscode.MarkdownString(
      `**${node.name}**\n\nStatus: ${node.status}\n${bridgeStatus}${node.currentTask ? `\nTask: ${node.currentTask}` : ''}${node.port ? `\nPort: ${node.port}` : ''}${node.progress !== undefined ? `\nProgress: ${node.progress}%` : ''}${node.elapsedMs ? `\nElapsed: ${(node.elapsedMs / 1000).toFixed(1)}s` : ''}`
    );

    this.contextValue = node.status;

    this.command = {
      command: 'vibezoo.showAgentInfo',
      title: '에이전트 정보',
      arguments: [node],
    };
  }
}

// ── YOLO History Tree ───────────────────────────────────────

export class YoloHistoryProvider implements vscode.TreeDataProvider<YoloHistoryItem> {
  private _onDidChangeTreeData = new vscode.EventEmitter<YoloHistoryItem | undefined>();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

  private snapshots: string[] = [];

  refresh(): void {
    this.loadFromDisk();
    this._onDidChangeTreeData.fire(undefined);
  }

  addSnapshot(name: string): void {
    this.snapshots.unshift(name);
    if (this.snapshots.length > 50) this.snapshots.pop();
    this._onDidChangeTreeData.fire(undefined);
  }

  /** ~/.zoo-code/yocto/ 디렉토리에서 실제 세션 폴더 목록을 읽어온다 */
  private loadFromDisk(): void {
    try {
      const yoctoDir = path.join(os.homedir(), '.zoo-code', 'yocto');
      if (!fs.existsSync(yoctoDir)) {
        this.snapshots = [];
        return;
      }
      const entries = fs.readdirSync(yoctoDir, { withFileTypes: true });
      const dirs = entries
        .filter((e) => e.isDirectory())
        .map((e) => e.name)
        .sort((a, b) => b.localeCompare(a)) // 최신순
        .slice(0, 50);
      this.snapshots = dirs;
    } catch {
      this.snapshots = [];
    }
  }

  getTreeItem(element: YoloHistoryItem): vscode.TreeItem {
    return element;
  }

  getChildren(_element?: YoloHistoryItem): Thenable<YoloHistoryItem[]> {
    // 항상 디스크에서 다시 읽어 최신 상태 유지
    this.loadFromDisk();

    if (this.snapshots.length === 0) {
      const placeholder = new vscode.TreeItem('YOLO 기록 없음', vscode.TreeItemCollapsibleState.None);
      placeholder.description = 'YOLO 모드로 작업 시 자동 기록됩니다';
      placeholder.iconPath = undefined;
      placeholder.label = '$(history) YOLO 기록 없음';
      placeholder.tooltip = 'YOLO(Yocto OnLine Offline) 모드로 YOCTO 스냅샷을 생성하면 여기에 기록이 표시됩니다.';
      return Promise.resolve([placeholder as any]);
    }
    return Promise.resolve(
      this.snapshots.map((s) => new YoloHistoryItem(s))
    );
  }
}

class YoloHistoryItem extends vscode.TreeItem {
  constructor(name: string) {
    super(name, vscode.TreeItemCollapsibleState.None);
    this.id = name;
    this.description = this.formatDescription(name);
    this.iconPath = undefined;
    this.label = `$(history) ${name}`;
    this.contextValue = 'yoloSnapshot';
    this.tooltip = `YOLO 세션: ${name}\n우클릭 → Rewind 실행`;
  }

  private formatDescription(name: string): string {
    // 이름에서 타임스탬프 추출하여 날짜 표시
    const match = name.match(/(\d{13})/);
    if (match) {
      const ts = parseInt(match[1], 10);
      const d = new Date(ts);
      return d.toLocaleString('ko-KR', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    }
    const match2 = name.match(/session[-_]?(\d+)/);
    if (match2) {
      const ts = parseInt(match2[1], 10);
      if (!isNaN(ts) && ts > 1e12) {
        const d = new Date(ts);
        return d.toLocaleString('ko-KR', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
      }
    }
    return 'YOLO snapshot';
  }
}

// ── Session Resume Tree ──────────────────────────────────────

export class SessionResumeProvider implements vscode.TreeDataProvider<SessionResumeItem> {
  private _onDidChangeTreeData = new vscode.EventEmitter<SessionResumeItem | undefined>();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

  private sessions: SessionSummary[] = [];
  private refreshFn: (() => Promise<SessionSummary[]>) | null = null;

  /** SessionResume.refresh()를 외부에서 주입 */
  setRefreshFn(fn: () => Promise<SessionSummary[]>): void {
    this.refreshFn = fn;
  }

  async refresh(): Promise<void> {
    if (this.refreshFn) {
      this.sessions = await this.refreshFn();
    }
    this._onDidChangeTreeData.fire(undefined);
  }

  getTreeItem(element: SessionResumeItem): vscode.TreeItem {
    return element;
  }

  getChildren(element?: SessionResumeItem): Thenable<SessionResumeItem[]> {
    if (!element) {
      // 최상위: 세션 목록
      if (this.sessions.length === 0) {
        const placeholder = new vscode.TreeItem('이전 세션 없음', vscode.TreeItemCollapsibleState.None);
        placeholder.description = 'Crow Memory에서 세션 정보를 불러오는 중...';
        placeholder.iconPath = undefined;
        placeholder.label = '$(empty) 불러온 세션 없음';
        placeholder.tooltip = 'Crow Memory 또는 로컬 파일에서 세션 요약을 불러올 수 없습니다.';
        return Promise.resolve([placeholder as any]);
      }
      return Promise.resolve(
        this.sessions.map((s) => new SessionResumeItem(s))
      );
    }

    // 하위: 세션 상세 정보
    const session = element.session;
    const children: SessionResumeItem[] = [];

    children.push(new SessionResumeItem(session, 'summary', `📋 ${session.summary || '요약 없음'}`));
    children.push(new SessionResumeItem(session, 'project', `📁 ${session.projectPath || '프로젝트 경로 없음'}`));
    children.push(new SessionResumeItem(session, 'mode', `⚙️ Mode: ${session.mode}`));
    children.push(new SessionResumeItem(session, 'time', `🕐 ${new Date(session.startedAt).toLocaleString('ko-KR')}`));

    if (session.keyDecisions.length > 0) {
      const decisionLabel = `📌 주요 결정 (${session.keyDecisions.length})`;
      const decisionItem = new SessionResumeItem(session, 'decisions', decisionLabel);
      decisionItem.collapsibleState = vscode.TreeItemCollapsibleState.Expanded;
      decisionItem.children = session.keyDecisions.map((d, i) =>
        new SessionResumeItem(session, `decision-${i}`, `  • ${d}`, vscode.TreeItemCollapsibleState.None)
      );
      children.push(decisionItem);
    }

    if (session.touchedFiles.length > 0) {
      const filesLabel = `📄 수정 파일 (${session.touchedFiles.length})`;
      const filesItem = new SessionResumeItem(session, 'files', filesLabel);
      filesItem.collapsibleState = vscode.TreeItemCollapsibleState.Collapsed;
      filesItem.children = session.touchedFiles.map((f, i) =>
        new SessionResumeItem(session, `file-${i}`, `  ${f}`, vscode.TreeItemCollapsibleState.None)
      );
      children.push(filesItem);
    }

    if (session.pendingTasks.length > 0) {
      const tasksLabel = `⏳ 미완료 작업 (${session.pendingTasks.length})`;
      const tasksItem = new SessionResumeItem(session, 'tasks', tasksLabel);
      tasksItem.collapsibleState = vscode.TreeItemCollapsibleState.Collapsed;
      tasksItem.children = session.pendingTasks.map((t, i) =>
        new SessionResumeItem(session, `task-${i}`, `  ☐ ${t}`, vscode.TreeItemCollapsibleState.None)
      );
      children.push(tasksItem);
    }

    return Promise.resolve(children);
  }
}

class SessionResumeItem extends vscode.TreeItem {
  session: SessionSummary;
  children: SessionResumeItem[] = [];

  constructor(session: SessionSummary, type?: string, labelOverride?: string, collapsibleState?: vscode.TreeItemCollapsibleState) {
    if (type && labelOverride) {
      // 하위 아이템
      super(labelOverride, collapsibleState ?? vscode.TreeItemCollapsibleState.None);
      this.session = session;
      this.id = `${session.sessionId}-${type}`;
      this.description = '';
      this.iconPath = undefined;
      this.tooltip = labelOverride;
    } else {
      // 최상위 세션 아이템
      const displayName = session.summary
        ? session.summary.substring(0, 60) + (session.summary.length > 60 ? '…' : '')
        : session.sessionId;
      super(displayName, vscode.TreeItemCollapsibleState.Collapsed);
      this.session = session;
      this.id = session.sessionId;
      this.description = `${session.mode || '?'} • ${new Date(session.startedAt).toLocaleDateString('ko-KR')}`;
      this.iconPath = undefined;
      this.label = `$(calendar) ${displayName}`;
      this.tooltip = new vscode.MarkdownString(
        `**세션 요약**\n\n${session.summary || '요약 없음'}\n\n**프로젝트**: ${session.projectPath || 'N/A'}\n**모드**: ${session.mode}\n**시작**: ${new Date(session.startedAt).toLocaleString('ko-KR')}${session.keyDecisions.length ? `\n**주요 결정**: ${session.keyDecisions.length}개` : ''}${session.touchedFiles.length ? `\n**수정 파일**: ${session.touchedFiles.length}개` : ''}${session.pendingTasks.length ? `\n**미완료 작업**: ${session.pendingTasks.length}개` : ''}`
      );
      this.contextValue = 'session';
    }
  }
}
