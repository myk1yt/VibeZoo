// VibeZoo Wave 2: AutoBuildFix
// 빌드 실패 시 stderr을 파싱하여 LLM에 수정을 요청하고 재빌드한다.
// max_attempts=3 + oscillation 감지로 무한 루프 방지.

import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { BuildResult } from '../types';

interface BuildAttempt {
  attemptNumber: number;
  exitCode: number;
  stderr: string;
  fixSummary?: string;
  timestamp: number;
}

const FIX_REQUEST_FILE = path.join(os.homedir(), '.vibezoo-fix-request.json');

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
          // 성공 시 fix request 파일 정리
          this.cleanupFixRequest();
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

        // LLM fix request 파일에 에러 데이터 기록
        this.writeFixRequest(result, attempt);

        // 사용자에게 진행 상황 알림
        vscode.window.setStatusBarMessage(
          `$(sync~spin) VibeZoo AutoBuildFix: ${attempt}/${this.maxAttempts} 시도 중...`,
          3000
        );

        // 시도 간 지연 (LLM이 fix request를 읽고 수정할 시간 확보)
        await new Promise((r) => setTimeout(r, 3000));
      }

      return { status: 'failed', attempt: this.maxAttempts, reason: 'max_retries' };
    } finally {
      this.isRunning = false;
    }
  }

  /** 중단 */
  cancel(): void {
    this.isRunning = false;
    this.cleanupFixRequest();
    vscode.window.showInformationMessage('VibeZoo: AutoBuildFix가 중단되었습니다.');
  }

  /** Fix request 파일에 빌드 에러 기록 → LLM이 읽고 수정 */
  private writeFixRequest(result: BuildResult, attempt: number): void {
    try {
      const data = {
        version: 1,
        timestamp: Date.now(),
        attempt,
        maxAttempts: this.maxAttempts,
        error: {
          exitCode: result.exitCode,
          stderr: result.stderr,
          stdout: result.stdout,
          diagnostics: result.diagnostics,
        },
        projectRoot: result.projectRoot,
        taskName: result.taskName,
        // LLM이 수정할 파일 목록 (diagnostics에서 추출)
        filesToFix: [...new Set(result.diagnostics.map((d) => d.file))],
      };
      fs.mkdirSync(path.dirname(FIX_REQUEST_FILE), { recursive: true });
      fs.writeFileSync(FIX_REQUEST_FILE, JSON.stringify(data, null, 2), 'utf-8');
      console.log(`[VibeZoo] Fix request written to ${FIX_REQUEST_FILE}`);
    } catch (err) {
      console.error('[VibeZoo] Failed to write fix request:', err);
    }
  }

  /** Fix request 파일 정리 */
  private cleanupFixRequest(): void {
    try {
      if (fs.existsSync(FIX_REQUEST_FILE)) {
        fs.unlinkSync(FIX_REQUEST_FILE);
      }
    } catch {
      // 무시
    }
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

    return new Promise((resolve, reject) => {
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

      // 120초 타임아웃
      const timeout = setTimeout(() => {
        disposable.dispose();
        reject(new Error('Build timed out after 120s'));
      }, 120000);

      // 타임아웃이 resolve보다 먼저 실행되지 않도록, resolve 시 clearTimeout
      const originalResolve = resolve;
      const wrappedDisposable = vscode.tasks.onDidEndTaskProcess((e) => {
        if (e.execution.task.name === 'vibezoo: build') {
          clearTimeout(timeout);
          wrappedDisposable.dispose();
          originalResolve({
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
