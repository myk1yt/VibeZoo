"use strict";
// VibeZoo: Tree View Providers
// Active Subagents, YOLO History, Session Resume 트리 뷰 제공
// ★ M3-F: Active Subagents에 실제 Bridge health check 연동,
//   Session Resume에 Crow/로컬 데이터 표시, CIM 상태 표시
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
exports.SessionResumeProvider = exports.YoloHistoryProvider = exports.ActiveSubagentsProvider = void 0;
const vscode = __importStar(require("vscode"));
const path = __importStar(require("path"));
const fs = __importStar(require("fs"));
const os = __importStar(require("os"));
const ConfigService_1 = require("../config/ConfigService");
const SelfCheck_1 = require("../safety/SelfCheck");
// ── Bridge Health Check ──────────────────────────────────────
async function checkBridgeHealth() {
    try {
        const resp = await fetch(ConfigService_1.ConfigService.getBridgeUrl('/health'), { signal: AbortSignal.timeout(3000) });
        if (resp.ok) {
            const data = await resp.json();
            return { ok: true, crow: !!data.crow, version: data.version || '?' };
        }
    }
    catch { }
    return { ok: false, crow: false, version: '?' };
}
// ── Active Subagents Tree ────────────────────────────────────
class ActiveSubagentsProvider {
    _onDidChangeTreeData = new vscode.EventEmitter();
    onDidChangeTreeData = this._onDidChangeTreeData.event;
    nodes = new Map();
    _bridgePort = 9027;
    _bridgeOk = false;
    _crowOk = false;
    _healthCheckInterval = null;
    refresh(node) {
        if (node) {
            const item = this.nodes.get(node.id);
            if (item) {
                this.nodes.set(node.id, node);
            }
        }
        this._onDidChangeTreeData.fire(undefined);
    }
    updateNode(node) {
        this.nodes.set(node.id, node);
        this._onDidChangeTreeData.fire(undefined);
    }
    removeNode(id) {
        this.nodes.delete(id);
        this._onDidChangeTreeData.fire(undefined);
    }
    /** Bridge health를 주기적으로 확인 (30초 간격) */
    startHealthCheck() {
        this.stopHealthCheck();
        this._healthCheckInterval = setInterval(async () => {
            const health = await checkBridgeHealth();
            this._bridgeOk = health.ok;
            this._crowOk = health.crow;
            // 모든 노드 상태 업데이트
            for (const [id, node] of this.nodes) {
                if (id === '_bridge')
                    continue;
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
    async pollSubagentTasks() {
        try {
            const resp = await fetch(ConfigService_1.ConfigService.getBridgeUrl('/tools/list_subagents'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({}),
                signal: AbortSignal.timeout(5000),
            });
            if (!resp.ok)
                return;
            const data = await resp.json();
            const tasks = data?.tasks || [];
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
        }
        catch {
            // Bridge가 아직 준비되지 않음 — 무시
        }
    }
    stopHealthCheck() {
        if (this._healthCheckInterval) {
            clearInterval(this._healthCheckInterval);
            this._healthCheckInterval = null;
        }
    }
    /** MCP 브릿지 시작 시 개별 에이전트 노드들을 초기화 + Bridge 상태 노드 추가 */
    initializeAgentNodes(bridgePort) {
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
    /** Guard.git 상태 업데이트 */
    setGuardGitStatus(state) {
        const nodeId = '_guard_git';
        // 항상 노드 표시 (inactive여도 유지)
        const guardManager = (0, SelfCheck_1.getGuardGitManager)();
        const pathCount = guardManager?.getProtectedPathCount() ?? 1;
        this.nodes.set(nodeId, {
            id: nodeId,
            name: 'Guard.git',
            status: state === 'active' ? 'running' : state === 'warning' ? 'error' : 'idle',
            currentTask: state === 'active' ? `.git Protected (${pathCount} roots)`
                : state === 'warning' ? '⚠️ .git Compromised'
                    : state === 'error' ? 'Error'
                        : 'Off — Click to enable',
            port: 0,
            startTime: Date.now(),
        });
        this._onDidChangeTreeData.fire(undefined);
    }
    /** CIM 감시 상태 업데이트 */
    setCimStatus(watching) {
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
        }
        else {
            this.nodes.delete('_cim');
        }
        this._onDidChangeTreeData.fire(undefined);
    }
    getTreeItem(element) {
        return element;
    }
    getChildren(_element) {
        const nodes = Array.from(this.nodes.values());
        if (nodes.length === 0) {
            const placeholder = new vscode.TreeItem(vscode.l10n.t('Waiting for VibeZoo...'), vscode.TreeItemCollapsibleState.None);
            placeholder.description = vscode.l10n.t('Automatically shown when Bridge connects');
            placeholder.iconPath = undefined;
            placeholder.label = vscode.l10n.t('$(sync~spin) Waiting for VibeZoo...');
            placeholder.tooltip = vscode.l10n.t('Agent status will be displayed when VibeZoo MCP Bridge is connected.');
            return Promise.resolve([placeholder]);
        }
        const items = nodes.map((node) => new SubagentTreeItem(node, this._bridgeOk, this._crowOk));
        // Bridge -> 이름순 정렬
        items.sort((a, b) => {
            if (a.node.id === '_bridge')
                return -1;
            if (b.node.id === '_bridge')
                return 1;
            return a.node.name.localeCompare(b.node.name);
        });
        return Promise.resolve(items);
    }
    dispose() {
        this.stopHealthCheck();
    }
}
exports.ActiveSubagentsProvider = ActiveSubagentsProvider;
class SubagentTreeItem extends vscode.TreeItem {
    node;
    constructor(node, bridgeOk = false, crowOk = false) {
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
            this.tooltip = new vscode.MarkdownString(`**MCP Bridge**\n\nStatus: ${bridgeOk ? '✅ Connected' : '❌ Disconnected'}\nPort: ${node.port}\nCrow: ${crowOk ? '✅ Connected' : '❌ Disconnected'}\n\nClick to check foundation status.`);
            this.contextValue = bridgeOk ? 'connected' : 'disconnected';
            this.command = {
                command: 'vibezoo.verifyFoundation',
                title: 'Check Foundation',
            };
            return;
        }
        // Guard.git special node
        if (node.id === '_guard_git') {
            const stateLabel = node.status === 'running' ? 'Active'
                : node.status === 'error' ? 'Warning'
                    : 'Inactive';
            const statusIcon = node.status === 'running' ? '$(shield)'
                : node.status === 'error' ? '$(error)'
                    : '$(circle-slash)';
            this.label = `${statusIcon} Guard.git`;
            this.description = node.currentTask;
            this.tooltip = new vscode.MarkdownString(`**Guard.git**\n\nStatus: ${stateLabel}\n.git directory: Protected\n\nClick to toggle Guard.git on/off.`);
            this.contextValue = 'guardGit';
            this.command = {
                command: 'vibezoo.toggleGuardGit',
                title: 'Toggle Guard.git',
            };
            return;
        }
        // CIM monitor special node
        if (node.id === '_cim') {
            this.label = `$(eye) CIM Monitor`;
            this.description = node.currentTask;
            this.tooltip = new vscode.MarkdownString(`**Continuous Improvement Mode**\n\nStatus: Watching file changes\nAuto-build on save: Enabled\n\nClick to stop watching.`);
            this.contextValue = 'cim';
            this.command = {
                command: 'vibezoo.stopWatching',
                title: 'Stop CIM',
            };
            return;
        }
        // FileGuard node removed
        // Regular agent nodes
        const iconMap = {
            idle: '$(debug-pause)',
            running: '$(sync~spin)',
            completed: '$(check)',
            error: '$(error)',
        };
        this.label = `${iconMap[node.status] || '$(question)'} ${node.name}`;
        const bridgeStatus = bridgeOk ? 'Bridge: Connected' : 'Bridge: Disconnected';
        this.tooltip = new vscode.MarkdownString(`**${node.name}**\n\nStatus: ${node.status}\n${bridgeStatus}${node.currentTask ? `\nTask: ${node.currentTask}` : ''}${node.port ? `\nPort: ${node.port}` : ''}${node.progress !== undefined ? `\nProgress: ${node.progress}%` : ''}${node.elapsedMs ? `\nElapsed: ${(node.elapsedMs / 1000).toFixed(1)}s` : ''}`);
        this.contextValue = node.status;
        this.command = {
            command: 'vibezoo.showAgentInfo',
            title: vscode.l10n.t('Agent Info'),
            arguments: [node],
        };
    }
}
// ── YOLO History Tree ───────────────────────────────────────
class YoloHistoryProvider {
    _onDidChangeTreeData = new vscode.EventEmitter();
    onDidChangeTreeData = this._onDidChangeTreeData.event;
    snapshots = [];
    refresh() {
        this.loadFromDisk();
        this._onDidChangeTreeData.fire(undefined);
    }
    addSnapshot(name) {
        this.snapshots.unshift(name);
        if (this.snapshots.length > 50)
            this.snapshots.pop();
        this._onDidChangeTreeData.fire(undefined);
    }
    /** ~/.zoo-code/yocto/ 디렉토리에서 실제 세션 폴더 목록을 읽어온다 */
    loadFromDisk() {
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
        }
        catch {
            this.snapshots = [];
        }
    }
    getTreeItem(element) {
        return element;
    }
    getChildren(_element) {
        // 항상 디스크에서 다시 읽어 최신 상태 유지
        this.loadFromDisk();
        if (this.snapshots.length === 0) {
            const placeholder = new vscode.TreeItem(vscode.l10n.t('No YOLO history'), vscode.TreeItemCollapsibleState.None);
            placeholder.description = vscode.l10n.t('Automatically recorded when working in YOLO mode');
            placeholder.iconPath = undefined;
            placeholder.label = vscode.l10n.t('$(history) No YOLO history');
            placeholder.tooltip = vscode.l10n.t('YOLO session history will be displayed here when YOLO snapshots are created.');
            return Promise.resolve([placeholder]);
        }
        return Promise.resolve(this.snapshots.map((s) => new YoloHistoryItem(s)));
    }
}
exports.YoloHistoryProvider = YoloHistoryProvider;
class YoloHistoryItem extends vscode.TreeItem {
    constructor(name) {
        super(name, vscode.TreeItemCollapsibleState.None);
        this.id = name;
        this.description = this.formatDescription(name);
        this.iconPath = undefined;
        this.label = `$(history) ${name}`;
        this.contextValue = 'yoloSnapshot';
        this.tooltip = vscode.l10n.t('YOLO Session: {0}\nRight-click → Run Rewind', name);
    }
    formatDescription(name) {
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
class SessionResumeProvider {
    _onDidChangeTreeData = new vscode.EventEmitter();
    onDidChangeTreeData = this._onDidChangeTreeData.event;
    sessions = [];
    refreshFn = null;
    /** SessionResume.refresh()를 외부에서 주입 */
    setRefreshFn(fn) {
        this.refreshFn = fn;
    }
    async refresh() {
        if (this.refreshFn) {
            this.sessions = await this.refreshFn();
        }
        this._onDidChangeTreeData.fire(undefined);
    }
    getTreeItem(element) {
        return element;
    }
    getChildren(element) {
        if (!element) {
            // 최상위: 세션 목록
            if (this.sessions.length === 0) {
                const placeholder = new vscode.TreeItem(vscode.l10n.t('No previous session'), vscode.TreeItemCollapsibleState.None);
                placeholder.description = vscode.l10n.t('Loading session info from Crow Memory...');
                placeholder.iconPath = undefined;
                placeholder.label = vscode.l10n.t('$(empty) No loaded session');
                placeholder.tooltip = vscode.l10n.t('Cannot load session resume from Crow Memory or local file.');
                return Promise.resolve([placeholder]);
            }
            return Promise.resolve(this.sessions.map((s) => new SessionResumeItem(s)));
        }
        // 하위: 세션 상세 정보
        const session = element.session;
        const children = [];
        children.push(new SessionResumeItem(session, 'summary', vscode.l10n.t('📋 {0}', session.summary || vscode.l10n.t('No summary'))));
        children.push(new SessionResumeItem(session, 'project', vscode.l10n.t('📁 {0}', session.projectPath || vscode.l10n.t('No project path'))));
        children.push(new SessionResumeItem(session, 'mode', `⚙️ Mode: ${session.mode}`));
        children.push(new SessionResumeItem(session, 'time', `🕐 ${new Date(session.startedAt).toLocaleString('ko-KR')}`));
        if (session.keyDecisions.length > 0) {
            const decisionLabel = vscode.l10n.t('📌 Key Decisions ({0})', session.keyDecisions.length);
            const decisionItem = new SessionResumeItem(session, 'decisions', decisionLabel);
            decisionItem.collapsibleState = vscode.TreeItemCollapsibleState.Expanded;
            decisionItem.children = session.keyDecisions.map((d, i) => new SessionResumeItem(session, `decision-${i}`, `  • ${d}`, vscode.TreeItemCollapsibleState.None));
            children.push(decisionItem);
        }
        if (session.touchedFiles.length > 0) {
            const filesLabel = vscode.l10n.t('📄 Modified Files ({0})', session.touchedFiles.length);
            const filesItem = new SessionResumeItem(session, 'files', filesLabel);
            filesItem.collapsibleState = vscode.TreeItemCollapsibleState.Collapsed;
            filesItem.children = session.touchedFiles.map((f, i) => new SessionResumeItem(session, `file-${i}`, `  ${f}`, vscode.TreeItemCollapsibleState.None));
            children.push(filesItem);
        }
        if (session.pendingTasks.length > 0) {
            const tasksLabel = vscode.l10n.t('⏳ Pending Tasks ({0})', session.pendingTasks.length);
            const tasksItem = new SessionResumeItem(session, 'tasks', tasksLabel);
            tasksItem.collapsibleState = vscode.TreeItemCollapsibleState.Collapsed;
            tasksItem.children = session.pendingTasks.map((t, i) => new SessionResumeItem(session, `task-${i}`, `  ☐ ${t}`, vscode.TreeItemCollapsibleState.None));
            children.push(tasksItem);
        }
        return Promise.resolve(children);
    }
}
exports.SessionResumeProvider = SessionResumeProvider;
class SessionResumeItem extends vscode.TreeItem {
    session;
    children;
    constructor(session, type, labelOverride, collapsibleState) {
        if (type && labelOverride) {
            // 하위 아이템
            super(labelOverride, collapsibleState ?? vscode.TreeItemCollapsibleState.None);
            this.session = session;
            this.children = [];
            this.id = `${session.sessionId}-${type}`;
            this.description = '';
            this.iconPath = undefined;
            this.tooltip = labelOverride;
        }
        else {
            // 최상위 세션 아이템
            const displayName = session.summary
                ? session.summary.substring(0, 60) + (session.summary.length > 60 ? '…' : '')
                : session.sessionId;
            super(displayName, vscode.TreeItemCollapsibleState.Collapsed);
            this.session = session;
            this.children = [];
            this.id = session.sessionId;
            this.description = `${session.mode || '?'} • ${new Date(session.startedAt).toLocaleDateString('ko-KR')}`;
            this.iconPath = undefined;
            this.label = `$(calendar) ${displayName}`;
            this.tooltip = new vscode.MarkdownString(vscode.l10n.t('**Session Summary**\n\n{0}\n\n**Project**: {1}\n**Mode**: {2}\n**Started**: {3}{4}{5}{6}', session.summary || vscode.l10n.t('No summary'), session.projectPath || 'N/A', session.mode, new Date(session.startedAt).toLocaleString(), session.keyDecisions.length ? vscode.l10n.t('\n**Key Decisions**: {0}', session.keyDecisions.length) : '', session.touchedFiles.length ? vscode.l10n.t('\n**Modified Files**: {0}', session.touchedFiles.length) : '', session.pendingTasks.length ? vscode.l10n.t('\n**Pending Tasks**: {0}', session.pendingTasks.length) : ''));
            this.contextValue = 'session';
        }
    }
}
//# sourceMappingURL=TreeViewProviders.js.map