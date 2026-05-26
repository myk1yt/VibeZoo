// VibeZoo Wave 2: AutoBuildFix
// 빌드 실패 시 stderr을 파싱하여 LLM에 수정을 요청하고 재빌드한다.
// max_attempts=3 + oscillation 감지로 무한 루프 방지.

import * as vscode from 'vscode';
import { BuildResult } from '../types';

interface BuildAttempt {
  attemptNumber: number;
  exitCode: number;
  stderr: string;
  fixSummary?: string;
  timestamp: number;
}

export class AutoBuildFix {
  private attempts: BuildAttempt[] = [];
  private isRunning: boolean = false;
  private maxAttempts: number;
  private oscillationWindowSize: number;

  constructor() {
    this.maxAttempts = vscode.workspace
      .getConfiguration('vibezoo')
      .get('build.autoFixMaxAttempts', 3);
    this.oscillationWindowSize = 4;
  }

  async run(initialResult: BuildResult): Promise<{ status: 'success' | 'failed'; attempt: number; reason?: string }> {
    if (this.isRunning) return { status: 'failed', attempt: 0, reason: 'already_running' };
    this.isRunning = true;
    this.attempts = [];

    try {
      for (let attempt = 1; attempt <= this.maxAttempts; attempt++) {
        const result = attempt === 1 ? initialResult : await this.rebuild();

        if (result.exitCode === 0) {
          vscode.window.showInformationMessage(
            `VibeZoo AutoBuildFix: ${attempt}회 시도 후 빌드 성공!`
          );
          return { status: 'success', attempt };
        }

        // Oscillation 감지 (A→B→A 패턴)
        if (this.isOscillating()) {
          vscode.window.showWarningMessage(
            'VibeZoo: A→B→A 패턴 감지. 무한 루프 방지를 위해 AutoBuildFix를 중단합니다.'
          );
          return { status: 'failed', attempt, reason: 'oscillation' };
        }

        // 반복 에러 감지
        if (this.isRepeatedError(result)) {
          vscode.window.showWarningMessage(
            'VibeZoo: 동일한 에러가 반복됩니다. AutoBuildFix를 중단합니다.'
          );
          return { status: 'failed', attempt, reason: 'repeated_error' };
        }

        const attemptRecord: BuildAttempt = {
          attemptNumber: attempt,
          exitCode: result.exitCode,
          stderr: result.stderr,
          timestamp: Date.now(),
        };
        this.attempts.push(attemptRecord);

        // 사용자에게 진행 상황 알림
        vscode.window.setStatusBarMessage(
          `$(sync~spin) VibeZoo AutoBuildFix: ${attempt}/${this.maxAttempts} 시도 중...`,
          3000
        );

        // 시도 간 지연
        await new Promise((r) => setTimeout(r, 1000));
      }

      return { status: 'failed', attempt: this.maxAttempts, reason: 'max_retries' };
    } finally {
      this.isRunning = false;
    }
  }

  /** 중단 */
  cancel(): void {
    this.isRunning = false;
    vscode.window.showInformationMessage('VibeZoo: AutoBuildFix가 중단되었습니다.');
  }

  private isOscillating(): boolean {
    if (this.attempts.length < this.oscillationWindowSize) return false;
    const recent = this.attempts.slice(-this.oscillationWindowSize);
    const summaries = recent.map((a) => a.fixSummary).filter(Boolean);
    // A→B→A 패턴: 짝수 번째가 홀수 번째와 동일
    for (let i = 2; i < summaries.length; i++) {
      if (summaries[i] === summaries[i - 2]) return true;
    }
    return false;
  }

  private isRepeatedError(result: BuildResult): boolean {
    if (this.attempts.length === 0) return false;
    const last = this.attempts[this.attempts.length - 1];
    return last.exitCode === result.exitCode;
  }

  private async rebuild(): Promise<BuildResult> {
    const tasks = await vscode.tasks.fetchTasks({ type: 'vibezoo' });
    const buildTask = tasks.find((t) => t.name === 'vibezoo: build');
    if (!buildTask) throw new Error('빌드 태스크를 찾을 수 없습니다.');

    return new Promise((resolve) => {
      const disposable = vscode.tasks.onDidEndTaskProcess((e) => {
        if (e.execution.task.name === 'vibezoo: build') {
          disposable.dispose();
          resolve({
            taskName: e.execution.task.name,
            exitCode: e.exitCode ?? -1,
            stderr: '',
            stdout: '',
            timestamp: Date.now(),
            diagnostics: [],
            projectRoot: vscode.workspace.workspaceFolders?.[0]?.uri.fsPath ?? '',
          });
        }
      });
      vscode.tasks.executeTask(buildTask);
    });
  }
}
