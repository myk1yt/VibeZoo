// VibeZoo: VS Code Extension — 통합 진입점
// Zoo Code 소스 코드를 전혀 수정하지 않는 독립 동반자 확장.
// Phase 0 + Wave 1~6의 모든 모듈을 연결한다.

import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { CrowServerManager } from './crow/CrowServerManager';
import { StatusBarManager } from './ui/StatusBarManager';
import { ActiveSubagentsProvider, YoloHistoryProvider } from './ui/TreeViewProviders';
import { registerBuildTaskProvider } from './flow/BuildTaskProvider';
import { activateBuildFeedback } from './flow/BuildFeedback';
import { activateProjectDetector } from './flow/ProjectDetector';
import { ProjectTreeScanner } from './flow/ProjectTreeScanner';
import { YoctoManager } from './safety/YoctoManager';
import { FileGuard } from './safety/FileGuard';
import { AutoBuildFix } from './safety/AutoBuildFix';
import { GitStashManager } from './safety/GitStashManager';
import { ContextIndicator, ExplainLessSuggestor, SessionResume, EmotionalDetector } from './context/ContextIntelligence';
import { SubagentManager } from './orchestra/SubagentManager';
import { MentionRouter } from './orchestra/MentionRouter';
import { VisualVibePanels } from './visual/VisualVibePanels';

let crowServer: CrowServerManager;
let statusBar: StatusBarManager;
let yocto: YoctoManager;
let fileGuard: FileGuard;
let autoBuildFix: AutoBuildFix;
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
  console.log('[VibeZoo] 🚀 활성화 시작...');

  // ── Phase 0: Foundation ──────────────────────────────────
  ensureDirectories();
  ensureTemplates();

  crowServer = new CrowServerManager();
  statusBar = new StatusBarManager();

  // Crow 연결 상태 → StatusBar
  crowServer.onStatusChange(({ connected, freshness }) => {
    statusBar.setCrowStatus(connected, freshness);
  });

  const autoReconnect = vscode.workspace.getConfiguration('vibezoo').get('crow.autoReconnect', true);
  if (autoReconnect) {
    crowServer.reconnect().catch((err) =>
      console.warn('[VibeZoo] Crow 연결 실패:', err.message)
    );
  }

  // 초기 상태
  const connected = crowServer.isRunning() && (await crowServer.healthCheck());
  const freshness = connected ? await crowServer.getFreshness() : undefined;
  statusBar.setCrowStatus(connected, freshness);

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

    autoBuildFix = new AutoBuildFix();
    gitStash = new GitStashManager();
  }

  // ── Wave 3: Context Intelligence ─────────────────────────
  contextIndicator = new ContextIndicator();
  explainLess = new ExplainLessSuggestor();
  sessionResume = new SessionResume();
  emotionalDetector = new EmotionalDetector();

  if (vscode.workspace.getConfiguration('vibezoo').get('context.showFreshness', true)) {
    const status = await contextIndicator.getFreshnessStatus();
    statusBar.setCrowStatus(connected, status.percentage);
  }

  if (vscode.workspace.getConfiguration('vibezoo').get('session.autoResume', true)) {
    sessionResume.show(context).catch(() => {});
  }

  // ── TreeView Providers ──────────────────────────────────
  const subagentsProvider = new ActiveSubagentsProvider();
  const yoloHistoryProvider = new YoloHistoryProvider();

  context.subscriptions.push(
    vscode.window.registerTreeDataProvider('vibezoo.activeSubagents', subagentsProvider)
  );
  context.subscriptions.push(
    vscode.window.registerTreeDataProvider('vibezoo.yoloHistory', yoloHistoryProvider)
  );

  // SubagentManager 상태 변경 → TreeView 업데이트
  subagentManager.onChange((node) => {
    subagentsProvider.updateNode(node);
  });

  // ── Wave 4: Orchestra ────────────────────────────────────
  subagentManager = new SubagentManager(context);
  mentionRouter = new MentionRouter(subagentManager);
  mentionRouter.registerParticipants(context);

  // ── Wave 5: Visual Vibe ──────────────────────────────────
  visualPanels = new VisualVibePanels();

  // ── Commands ─────────────────────────────────────────────

  // Instant Rewind
  context.subscriptions.push(
    vscode.commands.registerCommand('vibezoo.instantRewind', async () => {
      if (!yocto) {
        vscode.window.showWarningMessage('VibeZoo: YOLO 안전망이 비활성화되어 있습니다.');
        return;
      }
      try {
        const result = await yocto.instantRewind();
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
      const crowRunning = crowServer.isRunning();
      const crowHealthy = crowRunning ? await crowServer.healthCheck() : false;
      lines.push(crowHealthy ? '✅ Crow Memory: 연결됨' : '❌ Crow Memory: 연결 실패');
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

  // Reconnect Crow
  context.subscriptions.push(
    vscode.commands.registerCommand('vibezoo.reconnectCrow', async () => {
      try {
        await crowServer.reconnect();
        vscode.window.showInformationMessage('✅ VibeZoo: Crow Memory 재연결 성공!');
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

  // Show Session Resume
  context.subscriptions.push(
    vscode.commands.registerCommand('vibezoo.showSessionResume', () => {
      sessionResume.show(context);
    })
  );

  // AutoBuildFix 내부 커맨드
  context.subscriptions.push(
    vscode.commands.registerCommand('vibezoo._autoBuildFix', async (result: any) => {
      if (autoBuildFix) {
        const outcome = await autoBuildFix.run(result);
        if (outcome.status === 'success') {
          vscode.window.showInformationMessage(
            `VibeZoo: AutoBuildFix 성공 (${outcome.attempt}회 시도)`
          );
        }
      }
    })
  );

  console.log('[VibeZoo] ✅ 활성화 완료');
}

// ── Deactivate ───────────────────────────────────────────────

export function deactivate(): void {
  console.log('[VibeZoo] 비활성화 — Crow 서버는 계속 실행됩니다.');

  crowServer?.onDeactivate();
  treeScanner?.dispose();
  yocto?.dispose();
  fileGuard?.dispose();
  sessionResume?.dispose();
  visualPanels?.dispose();
  subagentManager?.terminate();
  statusBar?.dispose();
}

// ── Helpers ─────────────────────────────────────────────────

function ensureDirectories(): void {
  const dirs = [
    path.join(os.homedir(), '.zoo-code', 'yocto'),
    path.join(os.homedir(), '.zoo-code', 'crow'),
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
