// VibeZoo: Tree View Providers
// Active Subagents, YOLO History, Session Resume 트리 뷰 제공

import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import * as os from 'os';
import { SubagentNode, SessionSummary } from '../types';

// ── Active Subagents Tree ────────────────────────────────────

export class ActiveSubagentsProvider implements vscode.TreeDataProvider<SubagentTreeItem> {
  private _onDidChangeTreeData = new vscode.EventEmitter<SubagentTreeItem | undefined>();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

  private nodes: Map<string, SubagentNode> = new Map();

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

  /** MCP 브릿지 시작 시 개별 에이전트 노드들을 초기화 */
  initializeAgentNodes(bridgePort: number): void {
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
        currentTask: `${agent.name} ready via Bridge (:${bridgePort})`,
        port: agent.port,
        startTime: Date.now(),
      });
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
      placeholder.tooltip = 'VibeZoo MCP Bridge가 연결되면 Scout·Reviewer·Tester·DeepAnalyzer가 여기에 표시됩니다.';
      return Promise.resolve([placeholder as any]);
    }
    const items = nodes.map((node) => new SubagentTreeItem(node));
    return Promise.resolve(items);
  }
}

class SubagentTreeItem extends vscode.TreeItem {
  constructor(node: SubagentNode) {
    super(node.name, vscode.TreeItemCollapsibleState.None);

    this.id = node.id;
    this.description = node.currentTask || node.status;

    const iconMap: Record<string, string> = {
      idle: '$(debug-pause)',
      running: '$(sync~spin)',
      completed: '$(check)',
      error: '$(error)',
    };
    this.iconPath = undefined;
    this.label = `${iconMap[node.status] || '$(question)'} ${node.name}`;

    this.tooltip = new vscode.MarkdownString(
      `**${node.name}**\n\nStatus: ${node.status}${node.currentTask ? `\nTask: ${node.currentTask}` : ''}${node.port ? `\nPort: ${node.port}` : ''}${node.progress !== undefined ? `\nProgress: ${node.progress}%` : ''}${node.elapsedMs ? `\nElapsed: ${(node.elapsedMs / 1000).toFixed(1)}s` : ''}`
    );

    this.contextValue = node.status;

    // 클릭 시 해당 에이전트의 MCP 도구 안내 표시
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
