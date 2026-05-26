// VibeZoo Wave 2: Git Stash Manager
// YOLO 진입/퇴장 시 Git stash를 자동으로 생성/복원한다.

import * as vscode from 'vscode';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

export class GitStashManager {
  private stashName: string | null = null;
  private workspaceRoot: string | null = null;

  constructor() {
    const folders = vscode.workspace.workspaceFolders;
    this.workspaceRoot = folders?.[0]?.uri.fsPath ?? null;
  }

  private get cwd(): string {
    return this.workspaceRoot || '.';
  }

  /** YOLO 모드 진입 — 현재 상태를 stash에 저장 */
  async enterYolo(): Promise<boolean> {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    this.stashName = `vibezoo-yolo-${timestamp}`;

    try {
      await execAsync(
        `git stash push -m "${this.stashName}" --include-untracked`,
        { cwd: this.cwd }
      );

      vscode.window.showInformationMessage(
        `VibeZoo: YOLO 모드 시작 — 현재 상태가 stash에 저장되었습니다.`
      );
      return true;
    } catch (err: any) {
      // Git 저장소가 아니거나 stash 실패 — yocto만으로도 작동
      console.warn('[VibeZoo] Git stash 실패 (yocto로만 진행):', err.message);
      return false;
    }
  }

  /** YOLO 모드 퇴장 — 성공 시 커밋, 실패 시 복구 */
  async exitYolo(success: boolean): Promise<void> {
    if (success) {
      try {
        // YOLO 성공: 변경사항을 자동 커밋
        await execAsync('git add -A', { cwd: this.cwd });
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        await execAsync(
          `git commit -m "vibezoo-yolo-complete-${timestamp}" --no-verify`,
          { cwd: this.cwd }
        );
        vscode.window.showInformationMessage(
          'VibeZoo: YOLO 완료 — 변경사항이 커밋되었습니다.'
        );
      } catch (err: any) {
        console.warn('[VibeZoo] Git 커밋 실패:', err.message);
      }
    } else {
      // YOLO 실패: 사용자에게 되돌릴지 묻기
      const choice = await vscode.window.showWarningMessage(
        'YOLO가 실패했습니다. 이전 상태로 되돌리시겠습니까?',
        'Instant Rewind',
        '수동으로 처리'
      );

      if (choice === 'Instant Rewind') {
        vscode.commands.executeCommand('vibezoo.instantRewind');
      }

      // Git stash 복원 시도
      if (this.stashName) {
        try {
          await execAsync(
            `git stash pop stash^{/${this.stashName}}`,
            { cwd: this.cwd }
          );
        } catch (err: any) {
          console.warn('[VibeZoo] Git stash pop 실패:', err.message);
        }
      }
    }

    this.stashName = null;
  }

  /** Git 저장소인지 확인 */
  isGitRepo(): boolean {
    try {
      const gitDir = require('path').join(this.workspaceRoot || '', '.git');
      return require('fs').existsSync(gitDir);
    } catch {
      return false;
    }
  }
}
