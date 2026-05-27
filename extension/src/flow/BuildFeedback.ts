// VibeZoo Wave 1: Build Feedback Watcher
// onDidEndTaskProcess 이벤트를 구독하여 빌드 결과를 자동 수집한다.
// 실패 시 FixLoopManager에 에러를 전달하여 Auto-Fix 루프 시작.
// Crow Memory의 bug 레지스터에 에러 패턴 저장은 LLM이 MCP 도구로 수행.

import * as vscode from 'vscode';
import { BuildResult, Diagnostic } from '../types';

export function activateBuildFeedback(context: vscode.ExtensionContext): void {
  const disposable = vscode.tasks.onDidEndTaskProcess(async (event) => {
    const task = event.execution.task;

    // VibeZoo 태스크만 처리
    if (task.source !== 'VibeZoo') return;

    const exitCode = event.exitCode ?? -1;

    if (exitCode !== 0) {
      // 0.5초 대기 — LSP diagnostics 업데이트 시간
      await new Promise((resolve) => setTimeout(resolve, 500));
      const diagnostics = collectDiagnostics();

      const result: BuildResult = {
        taskName: task.name,
        exitCode,
        stderr: '',
        stdout: '',
        timestamp: Date.now(),
        diagnostics,
        projectRoot: vscode.workspace.workspaceFolders?.[0]?.uri.fsPath ?? '',
      };

      const errorSummary = diagnostics
        .slice(0, 10)
        .map((d) => `[${d.severity}] ${d.file}:${d.line} — ${d.message}`)
        .join('\n');

      console.log(`[VibeZoo] 빌드 실패 감지: exitCode=${exitCode}`);
      console.log(`[VibeZoo] 진단 결과:\n${errorSummary}`);

      // FixLoopManager에 에러 전달 (커맨드 기반)
      vscode.commands.executeCommand('vibezoo._autoBuildFix', result);

      // 사용자에게 알림 — StatusBar에 Fix 액션 표시
      vscode.window.setStatusBarMessage(
        `$(warning) VibeZoo: 빌드 실패 — [자동 수정]`,
        10000
      );
    } else {
      console.log(`[VibeZoo] 빌드 성공: ${task.name}`);

      // FixLoopManager에 성공 알림
      vscode.commands.executeCommand('vibezoo._buildSuccess');
    }
  });

  context.subscriptions.push(disposable);
}

function collectDiagnostics(): Diagnostic[] {
  const result: Diagnostic[] = [];
  const allDiagnostics = vscode.languages.getDiagnostics();

  for (const [uri, diagnostics] of allDiagnostics) {
    const relativePath = vscode.workspace.asRelativePath(uri);
    for (const d of diagnostics) {
      result.push({
        file: relativePath,
        line: d.range.start.line + 1,
        column: d.range.start.character + 1,
        severity:
          d.severity === vscode.DiagnosticSeverity.Error
            ? 'error'
            : d.severity === vscode.DiagnosticSeverity.Warning
            ? 'warning'
            : 'info',
        message: d.message,
        code: String(d.code ?? ''),
        source: d.source ?? '',
      });
    }
  }
  return result;
}
