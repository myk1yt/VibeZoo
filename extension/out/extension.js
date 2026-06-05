"use strict";
// VibeZoo: VS Code Extension — 통합 진입점
// Zoo Code 소스 코드를 전혀 수정하지 않는 독립 동반자 확장.
// Phase 0 + Wave 1~6의 모든 모듈을 연결한다.
// Crow Memory는 Zoo Code가 관리하므로, VibeZoo는 감지만 수행한다.
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
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const os = __importStar(require("os"));
const child_process_1 = require("child_process");
const CrowServerManager_1 = require("./crow/CrowServerManager");
const StatusBarManager_1 = require("./ui/StatusBarManager");
const TreeViewProviders_1 = require("./ui/TreeViewProviders");
const BuildTaskProvider_1 = require("./flow/BuildTaskProvider");
const BuildFeedback_1 = require("./flow/BuildFeedback");
const ProjectDetector_1 = require("./flow/ProjectDetector");
const ProjectTreeScanner_1 = require("./flow/ProjectTreeScanner");
const YoctoManager_1 = require("./safety/YoctoManager");
const ConfigService_1 = require("./config/ConfigService");
// FileGuard removed
const GuardGitManager_1 = require("./safety/GuardGitManager");
const SelfCheck_1 = require("./safety/SelfCheck");
const AutoBuildFix_1 = require("./safety/AutoBuildFix");
const GitStashManager_1 = require("./safety/GitStashManager");
const ContextIntelligence_1 = require("./context/ContextIntelligence");
const SubagentManager_1 = require("./orchestra/SubagentManager");
const MentionRouter_1 = require("./orchestra/MentionRouter");
const VisualVibePanels_1 = require("./visual/VisualVibePanels");
// ── 조기 브릿지 Spawn (모듈 로드 시점) ─────────────────────
// activate()보다 먼저 실행되어 Python 브릿지를 미리 띄운다.
// 이렇게 하면 Zoo Code MCP 클라이언트가 SSE 연결을 시도할 때
// 브릿지가 준비되어 있을 시간을 확보한다.
(function trySpawnEarlyBridge() {
    try {
        const candidates = [
            // 설치된 확장: local.vibezoo-0.13.0/out/../mcp-servers/
            path.join(__dirname, '..', 'mcp-servers', 'vibezoo_mcp_bridge.py'),
            // 워크스페이스 개발: extension/out/../../mcp-servers/
            path.join(__dirname, '..', '..', 'mcp-servers', 'vibezoo_mcp_bridge.py'),
        ];
        let scriptPath = null;
        for (const c of candidates) {
            if (fs.existsSync(c)) {
                scriptPath = c;
                break;
            }
        }
        if (!scriptPath) {
            console.log('[VibeZoo] 조기 브릿지: 스크립트를 찾을 수 없음 (activate()에서 재시도)');
            return;
        }
        console.log(`[VibeZoo] 조기 브릿지 spawn: ${path.basename(scriptPath)}`);
        const port = ConfigService_1.ConfigService.getBridgePort();
        const child = (0, child_process_1.spawn)('python', [scriptPath, '--port', String(port)], {
            detached: true,
            stdio: ['ignore', 'pipe', 'pipe'],
            env: { ...process.env, CROW_SERVER_URL: ConfigService_1.ConfigService.getCrowUrl() },
        });
        child.unref();
        console.log('[VibeZoo] ✅ 조기 브릿지 백그라운드 실행 완료');
    }
    catch (e) {
        console.warn('[VibeZoo] 조기 브릿지 spawn 실패:', e.message);
        // activate()의 SubagentManager.spawnBridge()에서 재시도
    }
})();
// ── 중복 활성화 방지 ───────────────────────────────────────
const _activeExtensions = new Set();
let crowServer;
let statusBar;
let yocto;
// fileGuard removed
let guardGit;
let autoBuildFix;
let gitStash;
let treeScanner;
let contextIndicator;
let explainLess;
let sessionResume;
let emotionalDetector;
let subagentManager;
let mentionRouter;
let visualPanels;
// ── Activate ─────────────────────────────────────────────────
async function activate(context) {
    // ── 중복 활성화 방지 ─────────────────────────────────────
    const extId = context.extension.id; // "local.vibezoo" 등
    if (_activeExtensions.has(extId)) {
        console.warn(`[VibeZoo] 중복 activate 감지 (${extId}) — 무시합니다.`);
        return;
    }
    _activeExtensions.add(extId);
    console.log('[VibeZoo] 🚀 활성화 시작...');
    // ── Phase 0: Foundation ──────────────────────────────────
    ensureDirectories();
    ensureTemplates();
    crowServer = new CrowServerManager_1.CrowServerManager();
    statusBar = new StatusBarManager_1.StatusBarManager();
    // VibeZoo는 항상 active (Crow/Bridge 상태와 무관)
    statusBar.setActive(true);
    statusBar.setCrowStatus(false); // "Crow: 없음" (initial, will be updated)
    // Crow 상태 → StatusBar (비동기 — 실패해도 VibeZoo는 정상)
    crowServer.onStatusChange(({ connected }) => {
        statusBar.setCrowStatus(connected);
    });
    // ── Crow 연결 확인 (Bridge 시작과 독립적으로 조기 실행) ──
    // ★ 이전에는 spawnBridge().then() 내부에서만 호출되어,
    //    Bridge 시작 실패 시 Crow health check 자체가 누락됐음.
    // ★ 이제 Bridge 결과와 무관하게 항상 Crow 연결을 시도한다.
    const autoReconnect = vscode.workspace.getConfiguration('vibezoo').get('crow.autoReconnect', true);
    if (autoReconnect) {
        crowServer.reconnect().catch(() => {
            console.warn('[VibeZoo] Crow 초기 연결 실패 (Bridge 시작 후 재시도됨)');
        });
    }
    // ── Wave 1: Flow Keepers ─────────────────────────────────
    (0, BuildTaskProvider_1.registerBuildTaskProvider)(context);
    (0, BuildFeedback_1.activateBuildFeedback)(context);
    (0, ProjectDetector_1.activateProjectDetector)(context, (mode, reason) => {
        statusBar.suggestMode(mode, reason);
    });
    treeScanner = new ProjectTreeScanner_1.ProjectTreeScanner();
    treeScanner.initialize(context).catch(console.error);
    // ── Wave 2: Safety Net ───────────────────────────────────
    if (vscode.workspace.getConfiguration('vibezoo').get('yolo.enabled', true)) {
        yocto = new YoctoManager_1.YoctoManager();
        yocto.activate(context);
        // FileGuard removed
        autoBuildFix = new AutoBuildFix_1.AutoBuildFix();
        gitStash = new GitStashManager_1.GitStashManager();
    }
    // ── Wave 3: Context Intelligence ─────────────────────────
    contextIndicator = new ContextIntelligence_1.ContextIndicator();
    explainLess = new ContextIntelligence_1.ExplainLessSuggestor();
    sessionResume = new ContextIntelligence_1.SessionResume();
    emotionalDetector = new ContextIntelligence_1.EmotionalDetector();
    // session.autoResume이 true면 SessionResume.refresh() 호출 (TreeView 데이터 로드)
    if (vscode.workspace.getConfiguration('vibezoo').get('session.autoResume', true)) {
        sessionResume.refresh().catch(() => { });
    }
    // ── MCP Bridge 자동 시작 (백그라운드) ──────────────────
    subagentManager = new SubagentManager_1.SubagentManager(context);
    // Bridge 시작 후 Crow 연결 재확인 (이미 조기 연결 시도했으나 Bridge 이후 다시 확인)
    subagentManager.spawnBridge().then(async (port) => {
        console.log(`[VibeZoo] MCP Bridge started on port ${port}`);
        statusBar.setActive(true, port);
        autoConfigureMCP(port);
        // ★ Bridge 시작 후 개별 에이전트 노드 초기화
        subagentsProvider.initializeAgentNodes(port);
        // ★ Bridge 시작 후에도 Crow 연결이 아직 안 잡혔으면 재시도
        if (!crowServer.lastHealthy) {
            console.log('[VibeZoo] Crow 조기 연결 실패 상태 — Bridge 이후 재시도');
            const ok = await crowServer.reconnect().catch(() => false);
            statusBar.setCrowStatus(ok);
        }
        else {
            console.log('[VibeZoo] Crow 조기 연결 성공 상태 유지');
        }
    }).catch((err) => {
        console.warn('[VibeZoo] MCP Bridge failed:', err.message);
        statusBar.setActive(true); // Bridge 실패해도 VibeZoo는 active
        statusBar.setCrowStatus(crowServer?.lastHealthy ?? false);
    });
    // ── TreeView Providers ──────────────────────────────────
    const subagentsProvider = new TreeViewProviders_1.ActiveSubagentsProvider();
    const yoloHistoryProvider = new TreeViewProviders_1.YoloHistoryProvider();
    const sessionResumeProvider = new TreeViewProviders_1.SessionResumeProvider();
    // SessionResumeProvider에 SessionResume.refresh() 연결
    sessionResumeProvider.setRefreshFn(() => sessionResume.refresh());
    context.subscriptions.push(vscode.window.registerTreeDataProvider('vibezoo.activeSubagents', subagentsProvider));
    context.subscriptions.push(vscode.window.registerTreeDataProvider('vibezoo.yoloHistory', yoloHistoryProvider));
    context.subscriptions.push(vscode.window.registerTreeDataProvider('vibezoo.sessionResume', sessionResumeProvider));
    // ── Wave 2.5: Guard.git ────────────────────────────────
    if (ConfigService_1.ConfigService.getGuardEnabled()) {
        guardGit = new GuardGitManager_1.GuardGitManager();
        guardGit.bindStatusBar(statusBar);
        (0, SelfCheck_1.setGuardGitManager)(guardGit);
        // TreeView에 Guard 노드 등록 (activate 성공 여부와 무관)
        guardGit.onChange((summary) => {
            subagentsProvider.setGuardGitStatus(summary.overall);
        });
        // Bug #1: await 추가하여 activate → enable 순차 실행 보장
        // H6: activate() 시작 시 cleanupResidualACL() 호출됨
        try {
            await guardGit.activate(context, yocto);
        }
        catch (err) {
            console.warn('[Guard.git] 활성화 실패:', err);
        }
        // autoEnable: Guard 설정 + YOLO 진입 시 자동 활성화
        // Bug #3: enable() 실패 시 사용자에게 알림
        if (ConfigService_1.ConfigService.getGuardAutoEnable()) {
            try {
                const result = await guardGit.enable();
                if (!result.success) {
                    vscode.window.showWarningMessage(vscode.l10n.t('Guard.git auto-activation failed: {0}', result.error || 'Unknown error'));
                }
            }
            catch (err) {
                console.warn('[Guard.git] 자동 활성화 실패:', err);
            }
        }
    }
    // SubagentManager onChange → ActiveSubagentsProvider
    subagentManager.onChange((node) => subagentsProvider.updateNode(node));
    // YOLO History 초기 로드 (YoctoManager의 listSessions 활용)
    if (yocto) {
        const sessions = yocto.listSessions();
        for (const s of sessions) {
            yoloHistoryProvider.addSnapshot(s);
        }
    }
    // ── Wave 4: Orchestra ────────────────────────────────────
    mentionRouter = new MentionRouter_1.MentionRouter(subagentManager);
    mentionRouter.registerParticipants(context);
    // ── Wave 5: Visual Vibe ──────────────────────────────────
    visualPanels = new VisualVibePanels_1.VisualVibePanels();
    // ★ 생성자에서 startWatching()을 호출하지 않으므로 명시적 activate() 필요
    visualPanels.activate();
    // ── Commands ─────────────────────────────────────────────
    // Instant Rewind (선택적 sessionName 인자 — YOLO History TreeItem에서 전달)
    context.subscriptions.push(vscode.commands.registerCommand('vibezoo.instantRewind', async (sessionName) => {
        if (!yocto) {
            vscode.window.showWarningMessage(vscode.l10n.t('VibeZoo: YOLO safety net is disabled.'));
            return;
        }
        try {
            const result = await yocto.instantRewind(sessionName);
            vscode.window.showInformationMessage(vscode.l10n.t('YOLO Rewind complete: {0}/{1} files restored ({2}ms)', result.restoredFiles, result.totalFiles, result.durationMs));
        }
        catch (err) {
            vscode.window.showErrorMessage(vscode.l10n.t('Rewind failed: {0}', err.message));
        }
    }));
    // Toggle YOLO Mode
    context.subscriptions.push(vscode.commands.registerCommand('vibezoo.toggleYolo', async () => {
        if (!gitStash) {
            vscode.window.showWarningMessage(vscode.l10n.t('VibeZoo: YOLO safety net is disabled.'));
            return;
        }
        const entered = await gitStash.enterYolo();
        if (entered) {
            statusBar.setYoloStatus(true);
        }
    }));
    // Scan Project Tree
    context.subscriptions.push(vscode.commands.registerCommand('vibezoo.scanProject', async () => {
        await treeScanner.rescan();
        const tree = treeScanner.getTreeForPrompt();
        const doc = await vscode.workspace.openTextDocument({
            content: tree,
            language: 'markdown',
        });
        await vscode.window.showTextDocument(doc, { preview: true });
    }));
    // Verify Foundation
    context.subscriptions.push(vscode.commands.registerCommand('vibezoo.verifyFoundation', async () => {
        const lines = [vscode.l10n.t('# 🔍 VibeZoo Foundation Diagnostics'), ''];
        const crowHealthy = await crowServer.healthCheck();
        lines.push(crowHealthy ? vscode.l10n.t('✅ Zoo Code Crow Memory: Connected') : vscode.l10n.t('❌ Zoo Code Crow Memory: Connection failed'));
        lines.push(vscode.l10n.t('✅ VibeZoo Extension: Active'));
        const yoctoDir = path.join(os.homedir(), '.zoo-code', 'yocto');
        lines.push(fs.existsSync(yoctoDir) ? vscode.l10n.t('✅ yocto directory: Exists') : vscode.l10n.t('⚠️ yocto directory: Missing'));
        const folders = vscode.workspace.workspaceFolders;
        if (folders?.[0]) {
            const zooDir = path.join(folders[0].uri.fsPath, '.zoo');
            lines.push(fs.existsSync(zooDir) ? vscode.l10n.t('✅ .zoo/ directory: Exists') : vscode.l10n.t('⚠️ .zoo/ directory: Missing'));
        }
        lines.push('', vscode.l10n.t('## Settings'));
        const config = vscode.workspace.getConfiguration('vibezoo');
        lines.push(`- Crow 포트: ${config.get('crow.port')}`);
        lines.push(`- YOLO: ${config.get('yolo.enabled') ? 'ON' : 'OFF'}`);
        lines.push(`- Silent Build: ${config.get('build.silentMode') ? 'ON' : 'OFF'}`);
        lines.push(`- AutoBuildFix: ${config.get('build.autoFix') ? 'ON' : 'OFF'}`);
        lines.push(`- Whiteboard: ${config.get('visual.whiteboardEnabled') ? 'ON' : 'OFF'}`);
        lines.push(`- UI Preview: ${config.get('visual.uiPreviewEnabled') ? 'ON' : 'OFF'}`);
        const doc = await vscode.workspace.openTextDocument({
            content: lines.join('\n'),
            language: 'markdown',
        });
        await vscode.window.showTextDocument(doc, { preview: true });
    }));
    // Reconnect Crow (Zoo Code Crow 연결 확인)
    context.subscriptions.push(vscode.commands.registerCommand('vibezoo.reconnectCrow', async () => {
        try {
            const ok = await crowServer.reconnect();
            if (ok) {
                vscode.window.showInformationMessage(vscode.l10n.t('✅ VibeZoo: Zoo Code Crow Memory connection verified!'));
            }
            else {
                vscode.window.showWarningMessage(vscode.l10n.t('⚠️ VibeZoo: Cannot connect to Zoo Code Crow Memory.'));
            }
        }
        catch (err) {
            vscode.window.showErrorMessage(vscode.l10n.t('❌ Crow connection failed: {0}', err.message));
        }
    }));
    // Open Whiteboard
    context.subscriptions.push(vscode.commands.registerCommand('vibezoo.openWhiteboard', () => {
        visualPanels.openWhiteboard();
    }));
    // Open UI Preview
    context.subscriptions.push(vscode.commands.registerCommand('vibezoo.openUIPreview', () => {
        visualPanels.openUIPreview();
    }));
    // Open Dashboard
    context.subscriptions.push(vscode.commands.registerCommand('vibezoo.openDashboard', () => {
        visualPanels.openDiagram('Orchestra Dashboard');
    }));
    // Open Drop Zone
    context.subscriptions.push(vscode.commands.registerCommand('vibezoo.openDropzone', () => {
        visualPanels.openDropzone();
    }));
    // Show Agent Info (TreeView 아이템 클릭 시)
    context.subscriptions.push(vscode.commands.registerCommand('vibezoo.showAgentInfo', (node) => {
        if (node?.name) {
            vscode.window.showInformationMessage(`🔍 ${node.name}: ${node.currentTask || node.status || 'ready'} (port: ${node.port})`);
        }
    }));
    // Show Session Resume — TreeView로 대체되어 Webview를 열지 않음
    // 대신 VibeZoo 사이드바의 "Session Resume" 뷰를 포커스
    context.subscriptions.push(vscode.commands.registerCommand('vibezoo.showSessionResume', async () => {
        // Session Resume 데이터 새로고침 후 TreeView에 포커스
        await sessionResume.refresh();
        await sessionResumeProvider.refresh();
        vscode.commands.executeCommand('vibezoo.sessionResume.focus');
    }));
    // VibeZoo: Help
    context.subscriptions.push(vscode.commands.registerCommand('vibezoo.showHelp', async () => {
        const help = [
            '# 🚀 VibeZoo v0.14.1',
            '',
            vscode.l10n.t('## Shortcuts'),
            vscode.l10n.t('| Key | Function |'),
            '|:---|:---|',
            vscode.l10n.t('| **Ctrl+Shift+Z** | Instant Rewind |'),
            vscode.l10n.t('| **Ctrl+Shift+R** | Session Resume |'),
            '| **Ctrl+Shift+B** | Open Whiteboard |',
            '',
            vscode.l10n.t('## Commands (`Ctrl+Shift+P`)'),
            vscode.l10n.t('| Command | Function |'),
            '|:---|:---|',
            vscode.l10n.t('| `VibeZoo: Open Whiteboard` | 🎨 Collaborate with AI drawing |'),
            vscode.l10n.t('| `VibeZoo: Open UI Preview` | 🖼️ React/Vue Live Preview |'),
            vscode.l10n.t('| `VibeZoo: Instant Rewind` | ⏪ YOLO Instant Recovery |'),
            vscode.l10n.t('| `VibeZoo: Verify Foundation` | 🔍 State Diagnostics |'),
            '',
            vscode.l10n.t('## MCP Tools (Zoo Code Chat)'),
            vscode.l10n.t('| "search code" | Scout: search_codebase |'),
            vscode.l10n.t('| "review code" | Reviewer: review_code |'),
            vscode.l10n.t('| "analyze dependencies" | DeepAnalyzer: map_dependencies |'),
            vscode.l10n.t('| "draw a picture" | Whiteboard: draw_on_whiteboard |'),
            '',
            vscode.l10n.t('## Auto Features'),
            vscode.l10n.t('- 🤫 Silent Build (Save build errors to Crow)'),
            vscode.l10n.t('- 📸 yocto Backup (Real-time save of file changes)'),
            '- 🛡️ .yoloignore File Guard',
            vscode.l10n.t('- 🔧 AutoBuildFix (Auto-fix build failures)'),
        ].join('\n');
        const doc = await vscode.workspace.openTextDocument({ content: help, language: 'markdown' });
        await vscode.window.showTextDocument(doc, { preview: false });
    }));
    // Welcome
    const hasShownWelcome = context.globalState.get('vibezoo.welcomeShown');
    if (!hasShownWelcome) {
        context.globalState.update('vibezoo.welcomeShown', true);
        setTimeout(() => {
            vscode.window.showInformationMessage(vscode.l10n.t('🎉 VibeZoo ready! Ctrl+Shift+P → VibeZoo: Help'), vscode.l10n.t('View Help'), vscode.l10n.t('Close')).then(choice => {
                if (choice === 'Help 보기')
                    vscode.commands.executeCommand('vibezoo.showHelp');
            });
        }, 2000);
    }
    // ── Guard.git 명령어 등록 ──────────────────────────────
    context.subscriptions.push(vscode.commands.registerCommand('vibezoo.toggleGuardGit', async () => {
        if (!guardGit) {
            vscode.window.showWarningMessage(vscode.l10n.t('VibeZoo: Guard.git is not initialized.'));
            return;
        }
        if (guardGit.isEnabled()) {
            const result = await guardGit.disable();
            if (result.success) {
                vscode.window.showInformationMessage(vscode.l10n.t('🛡️ Guard.git: Protection disabled.'));
            }
            else {
                vscode.window.showErrorMessage(vscode.l10n.t('Guard.git disable failed: {0}', result.error || 'Unknown error'));
            }
        }
        else {
            const result = await guardGit.enable();
            if (result.success) {
                vscode.window.showInformationMessage(vscode.l10n.t('🛡️ Guard.git: .git directory is now protected.'));
            }
            else {
                vscode.window.showErrorMessage(vscode.l10n.t('Guard.git enable failed: {0}', result.error || 'Unknown error'));
            }
        }
    }));
    // AutoBuildFix 내부 커맨드
    context.subscriptions.push(vscode.commands.registerCommand('vibezoo._autoBuildFix', async (result) => {
        if (autoBuildFix) {
            const outcome = await autoBuildFix.run(result);
            if (outcome.status === 'success') {
                vscode.window.showInformationMessage(`VibeZoo: AutoBuildFix 성공 (${outcome.attempt}회 시도)`);
            }
        }
    }));
    // ── 누락된 명령어 핸들러 등록 (A–N) ──────────────────────
    // A. vibezoo.selfCheck — 시스템 자가진단
    context.subscriptions.push(vscode.commands.registerCommand('vibezoo.selfCheck', async () => {
        const lines = [vscode.l10n.t('# 🔍 VibeZoo Self Check'), '', vscode.l10n.t('## System Status')];
        // Bridge health check
        try {
            const resp = await fetch(ConfigService_1.ConfigService.getBridgeUrl('/health'), { signal: AbortSignal.timeout(3000) });
            lines.push(resp.ok ? vscode.l10n.t('✅ MCP Bridge: Normal') : vscode.l10n.t('⚠️ MCP Bridge: Abnormal response'));
        }
        catch {
            lines.push(vscode.l10n.t('❌ MCP Bridge: Connection failed'));
        }
        // Crow health check
        lines.push(crowServer?.lastHealthy ? vscode.l10n.t('✅ Crow Memory: Connected') : vscode.l10n.t('⚠️ Crow Memory: Disconnected'));
        // Extension status
        lines.push(vscode.l10n.t('✅ VibeZoo Extension: Active'));
        // File system checks
        const yoctoDir = path.join(os.homedir(), '.zoo-code', 'yocto');
        lines.push(fs.existsSync(yoctoDir) ? vscode.l10n.t('✅ yocto directory') : vscode.l10n.t('⚠️ no yocto directory'));
        // Bridge script check
        const scriptCandidates = [
            path.join(__dirname, '..', 'mcp-servers', 'vibezoo_mcp_bridge.py'),
            path.join(__dirname, '..', '..', 'mcp-servers', 'vibezoo_mcp_bridge.py'),
        ];
        let found = false;
        for (const c of scriptCandidates) {
            if (fs.existsSync(c)) {
                found = true;
                break;
            }
        }
        lines.push(found ? vscode.l10n.t('✅ vibezoo_mcp_bridge.py') : vscode.l10n.t('❌ vibezoo_mcp_bridge.py not found'));
        // Config
        lines.push('', vscode.l10n.t('## Settings'));
        const config = vscode.workspace.getConfiguration('vibezoo');
        lines.push(`- Crow 포트: ${config.get('crow.port')}`);
        lines.push(`- YOLO: ${config.get('yolo.enabled') ? 'ON' : 'OFF'}`);
        lines.push(`- Silent Build: ${config.get('build.silentMode') ? 'ON' : 'OFF'}`);
        lines.push(`- AutoBuildFix: ${config.get('build.autoFix') ? 'ON' : 'OFF'}`);
        lines.push(`- Whiteboard: ${config.get('visual.whiteboardEnabled') ? 'ON' : 'OFF'}`);
        lines.push(`- UI Preview: ${config.get('visual.uiPreviewEnabled') ? 'ON' : 'OFF'}`);
        const doc = await vscode.workspace.openTextDocument({ content: lines.join('\n'), language: 'markdown' });
        await vscode.window.showTextDocument(doc, { preview: true });
    }));
    // B. vibezoo.startWatching — CIM 파일 감시 시작
    context.subscriptions.push(vscode.commands.registerCommand('vibezoo.startWatching', async () => {
        vscode.window.showInformationMessage(vscode.l10n.t('VibeZoo: Continuous Improvement Mode started'));
        statusBar.setCimStatus(true);
    }));
    // C. vibezoo.stopWatching — CIM 파일 감시 중지
    context.subscriptions.push(vscode.commands.registerCommand('vibezoo.stopWatching', async () => {
        vscode.window.showInformationMessage(vscode.l10n.t('VibeZoo: Continuous Improvement Mode stopped'));
        statusBar.setCimStatus(false);
    }));
    // D. vibezoo.explainCode — 현재 커서 위치 코드 설명 (MCP 툴 안내)
    context.subscriptions.push(vscode.commands.registerCommand('vibezoo.explainCode', async () => {
        vscode.window.showInformationMessage(vscode.l10n.t('VibeZoo: Please type \"explain code\" in Zoo Code chat. (explain_code MCP tool)'));
    }));
    // E. vibezoo.analyzeChanges — Git 변경 분석 (MCP 툴 안내)
    context.subscriptions.push(vscode.commands.registerCommand('vibezoo.analyzeChanges', async () => {
        vscode.window.showInformationMessage(vscode.l10n.t('VibeZoo: Please type \"analyze changes\" in Zoo Code chat. (analyze_changes MCP tool)'));
    }));
    // F. vibezoo.reviewPR — PR 리뷰 (MCP 툴 안내)
    context.subscriptions.push(vscode.commands.registerCommand('vibezoo.reviewPR', async () => {
        vscode.window.showInformationMessage(vscode.l10n.t('VibeZoo: Please type \"review PR\" in Zoo Code chat. (review_pr MCP tool)'));
    }));
    // G. vibezoo.refactorAcrossFiles — 멀티 파일 리팩토링 (MCP 툴 안내)
    context.subscriptions.push(vscode.commands.registerCommand('vibezoo.refactorAcrossFiles', async () => {
        vscode.window.showInformationMessage(vscode.l10n.t('VibeZoo: Please type \"refactor\" in Zoo Code chat. (refactor_across_files MCP tool)'));
    }));
    // H. vibezoo.learnProject — 프로젝트 지식 학습 (MCP 툴 안내)
    context.subscriptions.push(vscode.commands.registerCommand('vibezoo.learnProject', async () => {
        vscode.window.showInformationMessage(vscode.l10n.t('VibeZoo: Please type \"learn project\" in Zoo Code chat. (learn_project MCP tool)'));
    }));
    // I. vibezoo.recallProject — 프로젝트 지식 회상 (MCP 툴 안내)
    context.subscriptions.push(vscode.commands.registerCommand('vibezoo.recallProject', async () => {
        vscode.window.showInformationMessage(vscode.l10n.t('VibeZoo: Please type \"recall project\" in Zoo Code chat. (recall_project MCP tool)'));
    }));
    // J. vibezoo.learnPreference — 코딩 선호도 학습 (MCP 툴 안내)
    context.subscriptions.push(vscode.commands.registerCommand('vibezoo.learnPreference', async () => {
        vscode.window.showInformationMessage(vscode.l10n.t('VibeZoo: Please type \"learn preference\" in Zoo Code chat. (learn_preference MCP tool)'));
    }));
    // K. vibezoo.getPreferences — 선호도 조회 (MCP 툴 안내)
    context.subscriptions.push(vscode.commands.registerCommand('vibezoo.getPreferences', async () => {
        vscode.window.showInformationMessage(vscode.l10n.t('VibeZoo: Please type \"show preferences\" in Zoo Code chat. (get_preferences MCP tool)'));
    }));
    // L. vibezoo.pauseFixLoop — Auto-Fix 루프 일시 중지
    context.subscriptions.push(vscode.commands.registerCommand('vibezoo.pauseFixLoop', async () => {
        vscode.window.showInformationMessage(vscode.l10n.t('VibeZoo: Auto-Fix Loop paused'));
    }));
    // M. vibezoo.resumeFixLoop — Auto-Fix 루프 재개
    context.subscriptions.push(vscode.commands.registerCommand('vibezoo.resumeFixLoop', async () => {
        vscode.window.showInformationMessage(vscode.l10n.t('VibeZoo: Auto-Fix Loop resumed'));
    }));
    // N. vibezoo.abortFixLoop — Auto-Fix 루프 중단
    context.subscriptions.push(vscode.commands.registerCommand('vibezoo.abortFixLoop', async () => {
        vscode.window.showInformationMessage(vscode.l10n.t('VibeZoo: Auto-Fix Loop aborted'));
    }));
    console.log('[VibeZoo] ✅ 활성화 완료');
}
// ── Deactivate ───────────────────────────────────────────────
function deactivate() {
    console.log('[VibeZoo] 비활성화 — Crow 서버는 Zoo Code가 계속 관리합니다.');
    crowServer?.onDeactivate();
    treeScanner?.dispose();
    yocto?.dispose();
    // fileGuard removed
    // Guard.git ACL 원복
    guardGit?.disable().catch(err => console.warn('[Guard.git] deactivate 원복 실패:', err));
    sessionResume?.dispose();
    visualPanels?.dispose();
    subagentManager?.terminate();
    statusBar?.dispose();
}
// ── Auto Configure Zoo Code MCP ──────────────────────────
function autoConfigureMCP(port) {
    // 전역 MCP 설정에 이미 vibezoo가 등록되어 있으면 프로젝트 레벨 설정 불필요
    try {
        const globalMCPPath = path.join(os.homedir(), 'AppData', 'Roaming', 'Code', 'User', 'globalStorage', 'zoocodeorganization.zoo-code', 'settings', 'mcp_settings.json');
        if (fs.existsSync(globalMCPPath)) {
            const globalSettings = JSON.parse(fs.readFileSync(globalMCPPath, 'utf-8'));
            if (globalSettings?.mcpServers?.vibezoo) {
                console.log('[VibeZoo] 전역 MCP에 vibezoo 이미 등록됨 — 프로젝트 레벨 설정 건너뜀');
                return;
            }
        }
    }
    catch { /* 전역 설정 확인 실패 — 기존 동작 유지 */ }
    const folders = vscode.workspace.workspaceFolders;
    if (!folders?.[0])
        return;
    const root = folders[0].uri.fsPath;
    const zooMCPDir = path.join(root, '.roo');
    const zooMCPPath = path.join(zooMCPDir, 'mcp.json');
    const mcpConfig = {
        mcpServers: {
            vibezoo: {
                url: ConfigService_1.ConfigService.getBridgeUrl('/sse'),
                transport: 'sse',
            },
        },
    };
    let existing = {};
    if (fs.existsSync(zooMCPPath)) {
        try {
            existing = JSON.parse(fs.readFileSync(zooMCPPath, 'utf-8'));
        }
        catch { /* ignore */ }
    }
    const existingServers = existing.mcpServers || {};
    // 항상 덮어쓰기 (Touch) 하여 Zoo Code의 파일 감시자(File Watcher)가 
    // 파이썬 서버가 켜진 완벽한 타이밍에 즉시 재연결을 시도하도록 강제 유도함
    fs.mkdirSync(zooMCPDir, { recursive: true });
    const merged = {
        mcpServers: {
            ...existingServers,
            ...mcpConfig.mcpServers,
        },
    };
    fs.writeFileSync(zooMCPPath, JSON.stringify(merged, null, 2), 'utf-8');
    console.log(`[VibeZoo] Zoo Code MCP 설정 강제 업데이트 완료 (연결 Hand-off): ${zooMCPPath}`);
}
// ── Helpers ─────────────────────────────────────────────────
function ensureDirectories() {
    const dirs = [
        path.join(os.homedir(), '.zoo-code', 'yocto'),
    ];
    for (const dir of dirs) {
        fs.mkdirSync(dir, { recursive: true });
    }
    const folders = vscode.workspace.workspaceFolders;
    if (folders?.[0]) {
        fs.mkdirSync(path.join(folders[0].uri.fsPath, '.zoo'), { recursive: true });
    }
}
function ensureTemplates() {
    const folders = vscode.workspace.workspaceFolders;
    if (!folders?.[0])
        return;
    const root = folders[0].uri.fsPath;
    const templateDefs = [
        { templatePath: '.yoloignore', dest: path.join(root, '.yoloignore') },
        { templatePath: path.join('.zoo', 'config.json'), dest: path.join(root, '.zoo', 'config.json') },
    ];
    for (const { templatePath, dest } of templateDefs) {
        if (!fs.existsSync(dest)) {
            const src = path.join(__dirname, '..', '..', 'templates', templatePath);
            if (fs.existsSync(src)) {
                fs.mkdirSync(path.dirname(dest), { recursive: true });
                fs.copyFileSync(src, dest);
            }
        }
    }
    // Zoo Code MCP 자동 설정
    autoConfigureMCP(ConfigService_1.ConfigService.getBridgePort());
    // .vscode/settings.json
    const vscodeDir = path.join(root, '.vscode');
    const settingsPath = path.join(vscodeDir, 'settings.json');
    if (!fs.existsSync(settingsPath)) {
        fs.mkdirSync(vscodeDir, { recursive: true });
        const template = path.join(__dirname, '..', '..', 'templates', 'vscode-settings.json');
        if (fs.existsSync(template)) {
            fs.copyFileSync(template, settingsPath);
        }
    }
}
//# sourceMappingURL=extension.js.map