// VibeZoo: VS Code Extension — 통합 진입점
// Zoo Code 소스 코드를 전혀 수정하지 않는 독립 동반자 확장.
// Phase 0 + Wave 1~6의 모든 모듈을 연결한다.
// Crow Memory는 Zoo Code가 관리하므로, VibeZoo는 감지만 수행한다.

import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { CrowServerManager } from './crow/CrowServerManager';
import { StatusBarManager } from './ui/StatusBarManager';
import { ActiveSubagentsProvider, YoloHistoryProvider, SessionResumeProvider } from './ui/TreeViewProviders';
import { registerBuildTaskProvider } from './flow/BuildTaskProvider';
import { activateBuildFeedback } from './flow/BuildFeedback';
import { activateProjectDetector } from './flow/ProjectDetector';
import { ProjectTreeScanner } from './flow/ProjectTreeScanner';
import { YoctoManager } from './safety/YoctoManager';
import { FileGuard } from './safety/FileGuard';
import { FixLoopManager } from './orchestra/FixLoopManager';
import { GitStashManager } from './safety/GitStashManager';
import { ContextIndicator, ExplainLessSuggestor, SessionResume, EmotionalDetector } from './context/ContextIntelligence';
import { SubagentManager } from './orchestra/SubagentManager';
import { MentionRouter } from './orchestra/MentionRouter';
import { VisualVibePanels } from './visual/VisualVibePanels';

// ── 중복 활성화 방지 ───────────────────────────────────────
const _activeExtensions = new Set<string>();

let crowServer: CrowServerManager;
let statusBar: StatusBarManager;
let yocto: YoctoManager;
let fileGuard: FileGuard;
let fixLoopManager: FixLoopManager;
let gitStash: GitStashManager;
let treeScanner: ProjectTreeScanner;
let contextIndicator: ContextIndicator;
let explainLess: ExplainLessSuggestor;
let sessionResume: SessionResume;
let emotionalDetector: EmotionalDetector;
let subagentManager: SubagentManager;
let mentionRouter: MentionRouter;
let visualPanels: VisualVibePanels;

// ── Activate ─────────────────────────────────────────────────

export async function activate(context: vscode.ExtensionContext): Promise<void> {
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

  crowServer = new CrowServerManager();
  statusBar = new StatusBarManager();

  // VibeZoo는 항상 active (Crow/Bridge 상태와 무관) — 통합 setActive에 crowConnected 포함
  statusBar.setActive(true, undefined, false); // "Crow: 없음" (initial, will be updated)

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
  registerBuildTaskProvider(context);
  activateBuildFeedback(context);
  activateProjectDetector(context, (mode, reason) => {
    statusBar.suggestMode(mode, reason);
  });

  treeScanner = new ProjectTreeScanner();
  treeScanner.initialize(context).catch(console.error);

  // ── Wave 2: Safety Net ───────────────────────────────────
  if (vscode.workspace.getConfiguration('vibezoo').get('yolo.enabled', true)) {
    yocto = new YoctoManager();
    yocto.activate(context);

    fileGuard = new FileGuard(yocto);
    fileGuard.activate(context);

    fixLoopManager = new FixLoopManager();
    gitStash = new GitStashManager();
  }

  // ── Wave 3: Context Intelligence ─────────────────────────
  contextIndicator = new ContextIndicator();
  explainLess = new ExplainLessSuggestor();
  sessionResume = new SessionResume();
  emotionalDetector = new EmotionalDetector();

  // session.autoResume이 true면 SessionResume.refresh() 호출 (TreeView 데이터 로드)
  if (vscode.workspace.getConfiguration('vibezoo').get('session.autoResume', true)) {
    sessionResume.refresh().catch(() => {});
  }

  // ── MCP Bridge 자동 시작 (백그라운드) ──────────────────
  subagentManager = new SubagentManager(context);

  // Bridge 시작 후 Crow 연결 재확인 (이미 조기 연결 시도했으나 Bridge 이후 다시 확인)
  subagentManager.spawnBridge().then(async (port) => {
    console.log(`[VibeZoo] MCP Bridge started on port ${port}`);
    statusBar.setActive(true, port, crowServer.lastHealthy);
    autoConfigureMCP();

    // ★ Bridge 시작 후 개별 에이전트 노드 초기화
    subagentsProvider.initializeAgentNodes(port);

    // ★ Bridge 시작 후에도 Crow 연결이 아직 안 잡혔으면 재시도
    if (!crowServer.lastHealthy) {
      console.log('[VibeZoo] Crow 조기 연결 실패 상태 — Bridge 이후 재시도');
      const ok = await crowServer.reconnect().catch(() => false);
      statusBar.setCrowStatus(ok);
    } else {
      console.log('[VibeZoo] Crow 조기 연결 성공 상태 유지');
    }
  }).catch((err: any) => {
    console.warn('[VibeZoo] MCP Bridge failed:', err.message);
    statusBar.setActive(true, undefined, crowServer?.lastHealthy ?? false);
  });

  // ── TreeView Providers ──────────────────────────────────
  const subagentsProvider = new ActiveSubagentsProvider();
  const yoloHistoryProvider = new YoloHistoryProvider();
  const sessionResumeProvider = new SessionResumeProvider();

  // SessionResumeProvider에 SessionResume.refresh() 연결
  sessionResumeProvider.setRefreshFn(() => sessionResume.refresh());

  context.subscriptions.push(
    vscode.window.registerTreeDataProvider('vibezoo.activeSubagents', subagentsProvider)
  );
  context.subscriptions.push(
    vscode.window.registerTreeDataProvider('vibezoo.yoloHistory', yoloHistoryProvider)
  );
  context.subscriptions.push(
    vscode.window.registerTreeDataProvider('vibezoo.sessionResume', sessionResumeProvider)
  );

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
  mentionRouter = new MentionRouter(subagentManager);
  mentionRouter.registerParticipants(context);

  // ── Wave 5: Visual Vibe ──────────────────────────────────
  visualPanels = new VisualVibePanels();
  // ★ 생성자에서 startWatching()을 호출하지 않으므로 명시적 activate() 필요
  visualPanels.activate();

  // ── Commands ─────────────────────────────────────────────

  // Instant Rewind (선택적 sessionName 인자 — YOLO History TreeItem에서 전달)
  context.subscriptions.push(
    vscode.commands.registerCommand('vibezoo.instantRewind', async (sessionName?: string) => {
      if (!yocto) {
        vscode.window.showWarningMessage('VibeZoo: YOLO 안전망이 비활성화되어 있습니다.');
        return;
      }
      const confirm = await vscode.window.showWarningMessage(
        '정말로 모든 파일을 이 시점으로 되돌리시겠습니까?',
        { modal: true },
        '예, 복구합니다',
        '취소'
      );
      if (confirm !== '예, 복구합니다') return;
      try {
        const result = await yocto.instantRewind(sessionName);
        vscode.window.showInformationMessage(
          `YOLO Rewind 완료: ${result.restoredFiles}/${result.totalFiles} 파일 복구 (${result.durationMs}ms)`
        );
      } catch (err: any) {
        vscode.window.showErrorMessage(`Rewind 실패: ${err.message}`);
      }
    })
  );

  // Toggle YOLO Mode
  context.subscriptions.push(
    vscode.commands.registerCommand('vibezoo.toggleYolo', async () => {
      if (!gitStash) {
        vscode.window.showWarningMessage('VibeZoo: YOLO 안전망이 비활성화되어 있습니다.');
        return;
      }
      const entered = await gitStash.enterYolo();
      if (entered) {
        statusBar.setYoloStatus(true);
      }
    })
  );

  // Scan Project Tree
  context.subscriptions.push(
    vscode.commands.registerCommand('vibezoo.scanProject', async () => {
      await treeScanner.rescan();
      const tree = treeScanner.getTreeForPrompt();
      const doc = await vscode.workspace.openTextDocument({
        content: tree,
        language: 'markdown',
      });
      await vscode.window.showTextDocument(doc, { preview: true });
    })
  );

  // Verify Foundation
  context.subscriptions.push(
    vscode.commands.registerCommand('vibezoo.verifyFoundation', async () => {
      const lines = ['# 🔍 VibeZoo Foundation 진단', ''];
      const crowHealthy = await crowServer.healthCheck();
      lines.push(crowHealthy ? '✅ Zoo Code Crow Memory: 연결됨' : '❌ Zoo Code Crow Memory: 연결 실패');
      lines.push('✅ VibeZoo Extension: 활성화됨');

      const yoctoDir = path.join(os.homedir(), '.zoo-code', 'yocto');
      lines.push(fs.existsSync(yoctoDir) ? '✅ yocto 디렉토리: 존재함' : '⚠️ yocto 디렉토리: 없음');

      const folders = vscode.workspace.workspaceFolders;
      if (folders?.[0]) {
        const zooDir = path.join(folders[0].uri.fsPath, '.zoo');
        lines.push(fs.existsSync(zooDir) ? '✅ .zoo/ 디렉토리: 존재함' : '⚠️ .zoo/ 디렉토리: 없음');
      }

      lines.push('', '## 설정');
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
    })
  );

  // Reconnect Crow (Zoo Code Crow 연결 확인)
  context.subscriptions.push(
    vscode.commands.registerCommand('vibezoo.reconnectCrow', async () => {
      try {
        const ok = await crowServer.reconnect();
        if (ok) {
          vscode.window.showInformationMessage('✅ VibeZoo: Zoo Code Crow Memory 연결 확인 성공!');
        } else {
          vscode.window.showWarningMessage('⚠️ VibeZoo: Zoo Code Crow Memory에 연결할 수 없습니다.');
        }
      } catch (err: any) {
        vscode.window.showErrorMessage(`❌ Crow 연결 실패: ${err.message}`);
      }
    })
  );

  // Open Whiteboard
  context.subscriptions.push(
    vscode.commands.registerCommand('vibezoo.openWhiteboard', () => {
      visualPanels.openWhiteboard();
    })
  );

  // Open UI Preview
  context.subscriptions.push(
    vscode.commands.registerCommand('vibezoo.openUIPreview', () => {
      visualPanels.openUIPreview();
    })
  );

  // Open Dashboard
  context.subscriptions.push(
    vscode.commands.registerCommand('vibezoo.openDashboard', () => {
      visualPanels.openDiagram('Orchestra Dashboard');
    })
  );

  // Show Agent Info (TreeView 아이템 클릭 시)
  context.subscriptions.push(
    vscode.commands.registerCommand('vibezoo.showAgentInfo', (node: any) => {
      if (node?.name) {
        vscode.window.showInformationMessage(
          `🔍 ${node.name}: ${node.currentTask || node.status || 'ready'} (port: ${node.port})`
        );
      }
    })
  );

  // Show Session Resume — TreeView로 대체되어 Webview를 열지 않음
  // 대신 VibeZoo 사이드바의 "Session Resume" 뷰를 포커스
  context.subscriptions.push(
    vscode.commands.registerCommand('vibezoo.showSessionResume', async () => {
      // Session Resume 데이터 새로고침 후 TreeView에 포커스
      await sessionResume.refresh();
      await sessionResumeProvider.refresh();
      vscode.commands.executeCommand('vibezoo.sessionResume.focus');
    })
  );

  // VibeZoo: Help
  context.subscriptions.push(
    vscode.commands.registerCommand('vibezoo.showHelp', async () => {
      const help = [
        '# 🚀 VibeZoo v0.11.1',
        '',
        '## 단축키',
        '| 키 | 기능 |',
        '|:---|:---|',
        '| **Ctrl+Shift+Z** | Instant Rewind (YOLO 복구) |',
        '| **Ctrl+Shift+R** | Session Resume (이전 세션) |',
        '| **Ctrl+Shift+B** | Open Whiteboard |',
        '',
        '## 명령어 (`Ctrl+Shift+P`)',
        '| 명령어 | 기능 |',
        '|:---|:---|',
        '| `VibeZoo: Open Whiteboard` | 🎨 AI와 그림 그리며 협업 |',
        '| `VibeZoo: Open UI Preview` | 🖼️ React/Vue 실시간 미리보기 |',
        '| `VibeZoo: Instant Rewind` | ⏪ YOLO 즉시 복구 |',
        '| `VibeZoo: Verify Foundation` | 🔍 상태 진단 |',
        '',
        '## MCP 도구 (Zoo Code 채팅)',
        '| "코드 검색해줘" | Scout: search_codebase |',
        '| "코드 리뷰해줘" | Reviewer: review_code |',
        '| "의존성 분석해줘" | DeepAnalyzer: map_dependencies |',
        '| "그림 그려줘" | Whiteboard: draw_on_whiteboard |',
        '',
        '## 자동 기능',
        '- 🤫 Silent Build (빌드 에러 Crow 저장)',
        '- 📸 yocto 백업 (모든 파일 변경 실시간 저장)',
        '- 🛡️ .yoloignore File Guard',
        '- 🔧 AutoBuildFix (빌드 실패 자동 수정)',
      ].join('\n');
      const doc = await vscode.workspace.openTextDocument({ content: help, language: 'markdown' });
      await vscode.window.showTextDocument(doc, { preview: false });
    })
  );

  // Welcome
  const hasShownWelcome = context.globalState.get('vibezoo.welcomeShown');
  if (!hasShownWelcome) {
    context.globalState.update('vibezoo.welcomeShown', true);
    setTimeout(() => {
      vscode.window.showInformationMessage(
        '🎉 VibeZoo 준비 완료! Ctrl+Shift+P → VibeZoo: Help',
        'Help 보기', '닫기'
      ).then(choice => {
        if (choice === 'Help 보기') vscode.commands.executeCommand('vibezoo.showHelp');
      });
    }, 2000);
  }

  // FixLoopManager 내부 커맨드 — 빌드 실패 시 FixLoopManager에 전달
  context.subscriptions.push(
    vscode.commands.registerCommand('vibezoo._autoBuildFix', async (result: any) => {
      if (fixLoopManager && result?.diagnostics) {
        fixLoopManager.onBuildFailure(result.diagnostics, result.stderr || '', result.taskName);
      }
    })
  );

  // FixLoopManager 내부 커맨드 — 빌드 성공 시 FixLoopManager에 알림
  context.subscriptions.push(
    vscode.commands.registerCommand('vibezoo._buildSuccess', () => {
      fixLoopManager?.markResolved();
    })
  );

  // FixLoop: pause / resume / abort 커맨드
  context.subscriptions.push(
    vscode.commands.registerCommand('vibezoo.pauseFixLoop', () => {
      fixLoopManager?.pause();
    })
  );
  context.subscriptions.push(
    vscode.commands.registerCommand('vibezoo.resumeFixLoop', () => {
      fixLoopManager?.resume();
    })
  );
  context.subscriptions.push(
    vscode.commands.registerCommand('vibezoo.abortFixLoop', () => {
      fixLoopManager?.abort();
    })
  );

  // ── Q4: Quick Win — 시나리오 통합 MCP 도구 VS Code 명령어 ──
  const BRIDGE_URL = 'http://localhost:9027';

  /** MCP Bridge 호출 헬퍼 */
  async function callMCPTool(toolName: string, args: Record<string, any>): Promise<string> {
    try {
      const resp = await fetch(`${BRIDGE_URL}/tools/call`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: toolName, arguments: args }),
        signal: AbortSignal.timeout(30000),
      });
      if (!resp.ok) {
        return `❌ Bridge error: ${resp.status} ${resp.statusText}`;
      }
      const data: any = await resp.json();
      return data?.content?.[0]?.text || JSON.stringify(data, null, 2);
    } catch (err: any) {
      return `❌ Bridge 호출 실패: ${err.message}\n\nBridge가 http://localhost:9027 에서 실행 중인지 확인하세요.`;
    }
  }

  /** 결과를 새 편집기 탭으로 열기 */
  function showResultInEditor(title: string, content: string): void {
    vscode.workspace.openTextDocument({ content, language: 'markdown' }).then(doc => {
      vscode.window.showTextDocument(doc, { preview: false });
    });
  }

  // ── review_project ──
  context.subscriptions.push(
    vscode.commands.registerCommand('vibezoo.reviewProject', async () => {
      const folders = vscode.workspace.workspaceFolders;
      if (!folders?.[0]) {
        vscode.window.showWarningMessage('VibeZoo: 열려있는 프로젝트가 없습니다.');
        return;
      }
      const targetPath = folders[0].uri.fsPath;
      statusBar.showProgress('리뷰 분석 중...');
      const result = await callMCPTool('review_project', { target_path: targetPath });
      showResultInEditor('VibeZoo Project Review', result);
    })
  );

  // ── find_bugs ──
  context.subscriptions.push(
    vscode.commands.registerCommand('vibezoo.findBugs', async () => {
      const folders = vscode.workspace.workspaceFolders;
      if (!folders?.[0]) {
        vscode.window.showWarningMessage('VibeZoo: 열려있는 프로젝트가 없습니다.');
        return;
      }
      const targetPath = folders[0].uri.fsPath;
      statusBar.showProgress('버그 검색 중...');
      const result = await callMCPTool('find_bugs', { target_path: targetPath });
      showResultInEditor('VibeZoo Bug Finder', result);
    })
  );

  // ── suggest_refactor ──
  context.subscriptions.push(
    vscode.commands.registerCommand('vibezoo.suggestRefactor', async () => {
      const folders = vscode.workspace.workspaceFolders;
      if (!folders?.[0]) {
        vscode.window.showWarningMessage('VibeZoo: 열려있는 프로젝트가 없습니다.');
        return;
      }
      const targetPath = folders[0].uri.fsPath;
      statusBar.showProgress('리팩터링 분석 중...');
      const result = await callMCPTool('suggest_refactor', { target_path: targetPath });
      showResultInEditor('VibeZoo Refactoring Suggestions', result);
    })
  );

  // ── generate_docs ──
  context.subscriptions.push(
    vscode.commands.registerCommand('vibezoo.generateDocs', async () => {
      const folders = vscode.workspace.workspaceFolders;
      if (!folders?.[0]) {
        vscode.window.showWarningMessage('VibeZoo: 열려있는 프로젝트가 없습니다.');
        return;
      }
      const targetPath = folders[0].uri.fsPath;
      statusBar.showProgress('문서 생성 중...');
      const result = await callMCPTool('generate_docs', { target_path: targetPath, format: 'markdown' });
      showResultInEditor('VibeZoo Generated Documentation', result);
    })
  );

  console.log('[VibeZoo] ✅ 활성화 완료');
}

// ── Deactivate ───────────────────────────────────────────────

export function deactivate(): void {
  console.log('[VibeZoo] 비활성화 — Crow 서버는 Zoo Code가 계속 관리합니다.');

  crowServer?.onDeactivate();
  treeScanner?.dispose();
  yocto?.dispose();
  fileGuard?.dispose();
  fixLoopManager?.dispose();
  sessionResume?.dispose();
  visualPanels?.dispose();
  subagentManager?.terminate();
  statusBar?.dispose();
}

// ── Auto Configure Zoo Code MCP ──────────────────────────

function autoConfigureMCP(): void {
  const folders = vscode.workspace.workspaceFolders;
  if (!folders?.[0]) return;

  const root = folders[0].uri.fsPath;
  const zooMCPDir = path.join(root, '.roo');
  const zooMCPPath = path.join(zooMCPDir, 'mcp.json');

  const mcpConfig = {
    mcpServers: {
      vibezoo: {
        url: 'http://localhost:9027/sse',
        transport: 'sse',
      },
    },
  };

  let existing: any = {};
  if (fs.existsSync(zooMCPPath)) {
    try {
      existing = JSON.parse(fs.readFileSync(zooMCPPath, 'utf-8'));
    } catch { /* ignore */ }
  }

  const existingServers = existing.mcpServers || {};

  // 이미 vibezoo가 등록되어 있으면 덮어쓰지 않음
  if (!existingServers.vibezoo) {
    fs.mkdirSync(zooMCPDir, { recursive: true });
    const merged = {
      mcpServers: {
        ...existingServers,
        ...mcpConfig.mcpServers,
      },
    };
    fs.writeFileSync(zooMCPPath, JSON.stringify(merged, null, 2), 'utf-8');
    console.log(`[VibeZoo] Zoo Code MCP 설정 완료: ${zooMCPPath}`);
  } else {
    console.log('[VibeZoo] Zoo Code MCP 설정이 이미 존재합니다. 건드리지 않습니다.');
  }
}

// ── Helpers ─────────────────────────────────────────────────

function ensureDirectories(): void {
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

function ensureTemplates(): void {
  const folders = vscode.workspace.workspaceFolders;
  if (!folders?.[0]) return;
  const root = folders[0].uri.fsPath;

  const templateDefs: { templatePath: string; dest: string }[] = [
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
  autoConfigureMCP();

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
