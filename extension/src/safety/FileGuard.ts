// VibeZoo Wave 2: File Guard
// FileSystemWatcher로 .yoloignore 매칭 파일의 변경을 감지하여
// yocto 백업으로 즉시 복구한다.

import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { Minimatch } from 'minimatch';
import { YoctoManager } from './YoctoManager';

export class FileGuard {
  private patterns: Minimatch[] = [];
  private watcher: vscode.FileSystemWatcher | null = null;
  private yocto: YoctoManager;

  constructor(yocto: YoctoManager) {
    this.yocto = yocto;
    this.loadPatterns();
  }

  activate(context: vscode.ExtensionContext): void {
    const folders = vscode.workspace.workspaceFolders;
    if (!folders || folders.length === 0) return;

    // .yoloignore 파일 감시 (변경 시 재로드)
    const ignoreWatcher = vscode.workspace.createFileSystemWatcher(
      new vscode.RelativePattern(folders[0], '.yoloignore')
    );
    ignoreWatcher.onDidChange(() => this.loadPatterns());
    ignoreWatcher.onDidCreate(() => this.loadPatterns());
    context.subscriptions.push(ignoreWatcher);

    // 모든 파일 변경 감시
    this.watcher = vscode.workspace.createFileSystemWatcher(
      new vscode.RelativePattern(folders[0], '**/*'),
      false, false, false
    );

    this.watcher.onDidChange(async (uri) => {
      if (this.isProtected(uri.fsPath)) {
        // 보호된 파일이 변경됨 → yocto에서 최신 백업 찾아 복구
        const backupPath = this.findLatestBackup(uri.fsPath);
        if (backupPath && fs.existsSync(backupPath)) {
          fs.copyFileSync(backupPath, uri.fsPath);
          vscode.window.showWarningMessage(
            `VibeZoo: 보호된 파일 '${path.basename(uri.fsPath)}'의 변경이 자동 복구되었습니다.`
          );
        }
      }
    });

    context.subscriptions.push(this.watcher);
  }

  /** 파일이 .yoloignore에 의해 보호되는지 확인 */
  isProtected(filePath: string): boolean {
    return this.patterns.some((pattern) => pattern.match(filePath));
  }

  /** Crow life_avoid 동기화 — 새로운 패턴을 .yoloignore에 추가 */
  syncFromCrow(avoidPatterns: string[]): void {
    const folders = vscode.workspace.workspaceFolders;
    if (!folders || folders.length === 0) return;

    const ignorePath = path.join(folders[0].uri.fsPath, '.yoloignore');
    let content = '';
    try {
      content = fs.readFileSync(ignorePath, 'utf-8');
    } catch {
      // 파일 없음 — 새로 생성
    }

    let updated = false;
    for (const pattern of avoidPatterns) {
      if (!content.includes(pattern)) {
        content += `\n${pattern}`;
        updated = true;
      }
    }

    if (updated) {
      fs.writeFileSync(ignorePath, content, 'utf-8');
      this.loadPatterns();
    }
  }

  /** .yoloignore 파일 로드 */
  private loadPatterns(): void {
    this.patterns = [];

    const sources: string[] = [];

    // 프로젝트 루트 .yoloignore
    const folders = vscode.workspace.workspaceFolders;
    if (folders && folders.length > 0) {
      const projectIgnore = path.join(folders[0].uri.fsPath, '.yoloignore');
      sources.push(projectIgnore);
    }

    // 사용자 홈 .yoloignore
    const homeIgnore = path.join(os.homedir(), '.yoloignore');
    sources.push(homeIgnore);

    for (const source of sources) {
      try {
        const content = fs.readFileSync(source, 'utf-8');
        const lines = content.split('\n').filter(
          (line) => line.trim() && !line.startsWith('#')
        );
        for (const line of lines) {
          this.patterns.push(new Minimatch(line.trim(), { dot: true }));
        }
      } catch {
        // 파일 없음
      }
    }

    console.log(`[VibeZoo] FileGuard: ${this.patterns.length}개 보호 패턴 로드됨`);
  }

  private findLatestBackup(originalPath: string): string | null {
    const yoctoDir = path.join(os.homedir(), '.zoo-code', 'yocto');
    if (!fs.existsSync(yoctoDir)) return null;

    const relativePath = path.relative(
      vscode.workspace.workspaceFolders?.[0]?.uri.fsPath ?? '',
      originalPath
    );

    // 세션 디렉토리 목록 (역순 정렬로 최신 세션 우선)
    const sessions = fs.readdirSync(yoctoDir)
      .filter((s) => {
        try { return fs.statSync(path.join(yoctoDir, s)).isDirectory(); }
        catch { return false; }
      })
      .sort()
      .reverse();

    for (const session of sessions) {
      const sessionDir = path.join(yoctoDir, session);
      // 각 세션에서 가장 최근 타임스탬프 디렉토리만 확인 (이전 타임스탬프는 덮어쓰여졌을 가능성 낮음)
      const timestamps = fs.readdirSync(sessionDir)
        .filter((t) => {
          try { return fs.statSync(path.join(sessionDir, t)).isDirectory(); }
          catch { return false; }
        })
        .sort()
        .reverse();

      if (timestamps.length > 0) {
        const backupPath = path.join(sessionDir, timestamps[0], relativePath);
        if (fs.existsSync(backupPath)) return backupPath;
      }
    }

    return null;
  }

  dispose(): void {
    this.watcher?.dispose();
  }
}
