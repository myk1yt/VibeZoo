// VibeZoo: VS Code Extension — 통합 진입점
// Zoo Code 소스 코드를 전혀 수정하지 않는 독립 동반자 확장.
// Phase 0 + Wave 1~6의 모든 모듈을 연결한다.
// Crow Memory는 Zoo Code가 관리하므로, VibeZoo는 감지만 수행한다.

import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { spawn } from 'child_process';
import { CrowServerManager } from './crow/CrowServerManager';
import { StatusBarManager } from './ui/StatusBarManager';
import { ActiveSubagentsProvider, YoloHistoryProvider, SessionResumeProvider } from './ui/TreeViewProviders';
import { registerBuildTaskProvider } from './flow/BuildTaskProvider';
import { activateBuildFeedback } from './flow/BuildFeedback';
import { activateProjectDetector } from './flow/ProjectDetector';
import { ProjectTreeScanner } from './flow/ProjectTreeScanner';
import { YoctoManager } from './safety/YoctoManager';
import { ConfigService } from './config/ConfigService';
// FileGuard removed
import { AutoBuildFix } from './safety/AutoBuildFix';
import { GitStashManager } from './safety/GitStashManager';
import { ContextIndicator, ExplainLessSuggestor, SessionResume, EmotionalDetector } from './context/ContextIntelligence';
import { SubagentManager } from './orchestra/SubagentManager';
import { MentionRouter } from './orchestra/MentionRouter';
import { VisualVibePanels } from './visual/VisualVibePanels';
import { ConfigService } from './config/ConfigService';

// ── 조기 브릿지 Spawn (모듈 로드 시점) ─────────────────────
// activate()보다 먼저 실행되어 Python 브릿지를 미리 띄운다.
// 이렇게 하면 Zoo Code MCP 클라이언트가 SSE 연결을 시도할 때
// 브릿지가 준비되어 있을 시간을 확보한다.
(function trySpawnEarlyBridge(): void {
  try {
    const candidates = [
      // 설치된 확장: local.vibezoo-0.13.0/out/../mcp-servers/
      path.join(__dirname, '..', 'mcp-servers', 'vibezoo_mcp_bridge.py'),
      // 워크스페이스 개발: extension/out/../../mcp-servers/
      path.join(__dirname, '..', '..', 'mcp-servers', 'vibezoo_mcp_bridge.py'),
    ];
    let scriptPath: string | null = null;
    for (const c of candidates) {
      if (fs.existsSync(c)) { scriptPath = c; break; }
    }
    if (!scriptPath) {
      console.log('[VibeZoo] 조기 브릿지: 스크립트를 찾을 수 없음 (activate()에서 재시도)');
      return;
    }
    console.log(`[VibeZoo] 조기 브릿지 spawn: ${path.basename(scriptPath)}`);
    const port = ConfigService.getBridgePort();
    const child = spawn('python', [scriptPath, '--port', String(port)], {
      detached: true,
      stdio: ['ignore', 'pipe', 'pipe'],
      env: { ...process.env, CROW_SERVER_URL: ConfigService.getCrowUrl() },
    });
    child.unref();
    console.log('[VibeZoo] ✅ 조기 브릿지 백그라운드 실행 완료');
  } catch (e: any) {
    console.warn('[VibeZoo] 조기 브릿지 spawn 실패:', e.message);
    // activate()의 SubagentManager.spawnBridge()에서 재시도
  }
})();

// ── 중복 활성화 방지 ───────────────────────────────────────
const _activeExtensions = new Set<string>();

let crowServer: CrowServerManager;
let statusBar: StatusBarManager;
let yocto: YoctoManager;
// fileGuard removed
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

    // FileGuard removed
    autoBuildFix = new AutoBuildFix();
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
    statusBar.setActive(true, port);
    autoConfigureMCP(port);

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
    statusBar.setActive(true); // Bridge 실패해도 VibeZoo는 active
    statusBar.setCrowStatus(crowServer?.lastHealthy ?? false);
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

  // FileGuard removed

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

  // Open Drop Zone
  context.subscriptions.push(
    vscode.commands.registerCommand('vibezoo.openDropzone', () => {
      visualPanels.openDropzone();
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
        '# 🚀 VibeZoo v0.14.1',
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

  // FileGuard toggle removed

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

  // ── 누락된 명령어 핸들러 등록 (A–N) ──────────────────────

  // A. vibezoo.selfCheck — 시스템 자가진단
  context.subscriptions.push(
    vscode.commands.registerCommand('vibezoo.selfCheck', async () => {
      const lines = ['# 🔍 VibeZoo 자가진단', '', '## 시스템 상태'];
      // Bridge health check
      try {
        const resp = await fetch(ConfigService.getBridgeUrl('/health'), { signal: AbortSignal.timeout(3000) });
        lines.push(resp.ok ? '✅ MCP Bridge: 정상' : '⚠️ MCP Bridge: 비정상 응답');
      } catch {
        lines.push('❌ MCP Bridge: 연결 실패');
      }
      // Crow health check
      lines.push(crowServer?.lastHealthy ? '✅ Crow Memory: 연결됨' : '⚠️ Crow Memory: 연결 안 됨');
      // Extension status
      lines.push('✅ VibeZoo Extension: 활성화됨');
      // File system checks
      const yoctoDir = path.join(os.homedir(), '.zoo-code', 'yocto');
      lines.push(fs.existsSync(yoctoDir) ? '✅ yocto 디렉토리' : '⚠️ yocto 디렉토리 없음');
      // Bridge script check
      const scriptCandidates = [
        path.join(__dirname, '..', 'mcp-servers', 'vibezoo_mcp_bridge.py'),
        path.join(__dirname, '..', '..', 'mcp-servers', 'vibezoo_mcp_bridge.py'),
      ];
      let found = false;
      for (const c of scriptCandidates) { if (fs.existsSync(c)) { found = true; break; } }
      lines.push(found ? '✅ vibezoo_mcp_bridge.py' : '❌ vibezoo_mcp_bridge.py 없음');
      // Config
      lines.push('', '## 설정');
      const config = vscode.workspace.getConfiguration('vibezoo');
      lines.push(`- Crow 포트: ${config.get('crow.port')}`);
      lines.push(`- YOLO: ${config.get('yolo.enabled') ? 'ON' : 'OFF'}`);
      lines.push(`- Silent Build: ${config.get('build.silentMode') ? 'ON' : 'OFF'}`);
      lines.push(`- AutoBuildFix: ${config.get('build.autoFix') ? 'ON' : 'OFF'}`);
      lines.push(`- Whiteboard: ${config.get('visual.whiteboardEnabled') ? 'ON' : 'OFF'}`);
      lines.push(`- UI Preview: ${config.get('visual.uiPreviewEnabled') ? 'ON' : 'OFF'}`);
      const doc = await vscode.workspace.openTextDocument({ content: lines.join('\n'), language: 'markdown' });
      await vscode.window.showTextDocument(doc, { preview: true });
    })
  );

  // B. vibezoo.startWatching — CIM 파일 감시 시작
  context.subscriptions.push(
    vscode.commands.registerCommand('vibezoo.startWatching', async () => {
      vscode.window.showInformationMessage('VibeZoo: Continuous Improvement Mode 시작');
      statusBar.setCimStatus(true);
    })
  );

  // C. vibezoo.stopWatching — CIM 파일 감시 중지
  context.subscriptions.push(
    vscode.commands.registerCommand('vibezoo.stopWatching', async () => {
      vscode.window.showInformationMessage('VibeZoo: Continuous Improvement Mode 중지');
      statusBar.setCimStatus(false);
    })
  );

  // D. vibezoo.explainCode — 현재 커서 위치 코드 설명 (MCP 툴 안내)
  context.subscriptions.push(
    vscode.commands.registerCommand('vibezoo.explainCode', async () => {
      vscode.window.showInformationMessage('VibeZoo: Zoo Code 채팅에서 "코드 설명해줘" 라고 입력하세요. (explain_code MCP 도구)');
    })
  );

  // E. vibezoo.analyzeChanges — Git 변경 분석 (MCP 툴 안내)
  context.subscriptions.push(
    vscode.commands.registerCommand('vibezoo.analyzeChanges', async () => {
      vscode.window.showInformationMessage('VibeZoo: Zoo Code 채팅에서 "변경사항 분석해줘" 라고 입력하세요. (analyze_changes MCP 도구)');
    })
  );

  // F. vibezoo.reviewPR — PR 리뷰 (MCP 툴 안내)
  context.subscriptions.push(
    vscode.commands.registerCommand('vibezoo.reviewPR', async () => {
      vscode.window.showInformationMessage('VibeZoo: Zoo Code 채팅에서 "PR 리뷰해줘" 라고 입력하세요. (review_pr MCP 도구)');
    })
  );

  // G. vibezoo.refactorAcrossFiles — 멀티 파일 리팩토링 (MCP 툴 안내)
  context.subscriptions.push(
    vscode.commands.registerCommand('vibezoo.refactorAcrossFiles', async () => {
      vscode.window.showInformationMessage('VibeZoo: Zoo Code 채팅에서 "리팩토링해줘" 라고 입력하세요. (refactor_across_files MCP 도구)');
    })
  );

  // H. vibezoo.learnProject — 프로젝트 지식 학습 (MCP 툴 안내)
  context.subscriptions.push(
    vscode.commands.registerCommand('vibezoo.learnProject', async () => {
      vscode.window.showInformationMessage('VibeZoo: Zoo Code 채팅에서 "프로젝트 학습해줘" 라고 입력하세요. (learn_project MCP 도구)');
    })
  );

  // I. vibezoo.recallProject — 프로젝트 지식 회상 (MCP 툴 안내)
  context.subscriptions.push(
    vscode.commands.registerCommand('vibezoo.recallProject', async () => {
      vscode.window.showInformationMessage('VibeZoo: Zoo Code 채팅에서 "프로젝트 기억해줘" 라고 입력하세요. (recall_project MCP 도구)');
    })
  );

  // J. vibezoo.learnPreference — 코딩 선호도 학습 (MCP 툴 안내)
  context.subscriptions.push(
    vscode.commands.registerCommand('vibezoo.learnPreference', async () => {
      vscode.window.showInformationMessage('VibeZoo: Zoo Code 채팅에서 "선호도 학습해줘" 라고 입력하세요. (learn_preference MCP 도구)');
    })
  );

  // K. vibezoo.getPreferences — 선호도 조회 (MCP 툴 안내)
  context.subscriptions.push(
    vscode.commands.registerCommand('vibezoo.getPreferences', async () => {
      vscode.window.showInformationMessage('VibeZoo: Zoo Code 채팅에서 "선호도 보여줘" 라고 입력하세요. (get_preferences MCP 도구)');
    })
  );

  // L. vibezoo.pauseFixLoop — Auto-Fix 루프 일시 중지
  context.subscriptions.push(
    vscode.commands.registerCommand('vibezoo.pauseFixLoop', async () => {
      vscode.window.showInformationMessage('VibeZoo: Auto-Fix Loop 일시 중지됨');
    })
  );

  // M. vibezoo.resumeFixLoop — Auto-Fix 루프 재개
  context.subscriptions.push(
    vscode.commands.registerCommand('vibezoo.resumeFixLoop', async () => {
      vscode.window.showInformationMessage('VibeZoo: Auto-Fix Loop 재개됨');
    })
  );

  // N. vibezoo.abortFixLoop — Auto-Fix 루프 중단
  context.subscriptions.push(
    vscode.commands.registerCommand('vibezoo.abortFixLoop', async () => {
      vscode.window.showInformationMessage('VibeZoo: Auto-Fix Loop 중단됨');
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
  // fileGuard removed
  sessionResume?.dispose();
  visualPanels?.dispose();
  subagentManager?.terminate();
  statusBar?.dispose();
}

// ── Auto Configure Zoo Code MCP ──────────────────────────

function autoConfigureMCP(port: number): void {
  // 전역 MCP 설정에 이미 vibezoo가 등록되어 있으면 프로젝트 레벨 설정 불필요
  try {
    const globalMCPPath = path.join(os.homedir(), 'AppData', 'Roaming', 'Code', 'User', 'globalStorage',
      'zoocodeorganization.zoo-code', 'settings', 'mcp_settings.json');
    if (fs.existsSync(globalMCPPath)) {
      const globalSettings = JSON.parse(fs.readFileSync(globalMCPPath, 'utf-8'));
      if (globalSettings?.mcpServers?.vibezoo) {
        console.log('[VibeZoo] 전역 MCP에 vibezoo 이미 등록됨 — 프로젝트 레벨 설정 건너뜀');
        return;
      }
    }
  } catch { /* 전역 설정 확인 실패 — 기존 동작 유지 */ }

  const folders = vscode.workspace.workspaceFolders;
  if (!folders?.[0]) return;

  const root = folders[0].uri.fsPath;
  const zooMCPDir = path.join(root, '.roo');
  const zooMCPPath = path.join(zooMCPDir, 'mcp.json');

  const mcpConfig = {
    mcpServers: {
      vibezoo: {
        url: ConfigService.getBridgeUrl('/sse'),
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
  autoConfigureMCP(ConfigService.getBridgePort());

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
