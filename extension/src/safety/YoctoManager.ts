// VibeZoo Wave 2: yocto — Lightweight Snapshot System
// FileSystemWatcher로 파일 변경을 감지하여 fs.copyFileSync로 즉시 백업.
// 200ms debounce로 이벤트 폭주 방지.

import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import * as crypto from 'crypto';
import { YoctoSnapshot, YoctoFileEntry } from '../types';

export class YoctoManager {
  private snapshotsDir: string;
  private watcher: vscode.FileSystemWatcher | null = null;
  private pendingBackup: Map<string, NodeJS.Timeout> = new Map();
  private readonly DEBOUNCE_MS = 200;
  private currentSessionId: string;
  private activeSnapshots: YoctoSnapshot[] = [];

  constructor() {
    this.snapshotsDir = path.join(os.homedir(), '.zoo-code', 'yocto');
    fs.mkdirSync(this.snapshotsDir, { recursive: true });
    this.currentSessionId = `session-${Date.now()}`;
  }

  activate(context: vscode.ExtensionContext): void {
    const folders = vscode.workspace.workspaceFolders;
    if (!folders || folders.length === 0) return;

    // 소스 파일 변경 감시
    this.watcher = vscode.workspace.createFileSystemWatcher(
      new vscode.RelativePattern(folders[0], '**/*.{ts,tsx,js,jsx,py,go,rs,java,json,yaml,yml,md,css,html}'),
      false, // 생성
      false, // 변경
      false  // 삭제
    );

    this.watcher.onDidChange((uri) => this.scheduleBackup(uri));
    this.watcher.onDidCreate((uri) => this.scheduleBackup(uri));

    context.subscriptions.push(this.watcher);

    // 주기적 정리: 30일 이상 지난 스냅샷 삭제
    this.cleanupOldSnapshots(30);
  }

  /** YOLO 진입 시 전체 스냅샷 생성 */
  async createSnapshot(trigger: 'manual' | 'auto' | 'yolo-enter' | 'pre-edit'): Promise<YoctoSnapshot> {
    const snapshot: YoctoSnapshot = {
      id: `snap-${Date.now()}`,
      sessionId: this.currentSessionId,
      timestamp: Date.now(),
      trigger,
      files: [],
    };

    this.activeSnapshots.push(snapshot);
    return snapshot;
  }

  /** Instant Rewind — 마지막 YOLO 스냅샷의 모든 파일 복구 */
  async instantRewind(sessionId?: string): Promise<{ restoredFiles: number; totalFiles: number; durationMs: number }> {
    const targetSession = sessionId || this.currentSessionId;
    const snapshot = this.activeSnapshots
      .filter((s) => s.sessionId === targetSession)
      .sort((a, b) => b.timestamp - a.timestamp)[0];

    if (!snapshot || snapshot.files.length === 0) {
      throw new Error('되돌릴 스냅샷이 없습니다.');
    }

    const startTime = Date.now();
    let restored = 0;

    // 역순으로 복구
    const reversedFiles = [...snapshot.files].reverse();
    for (const file of reversedFiles) {
      try {
        if (fs.existsSync(file.backupPath)) {
          fs.copyFileSync(file.backupPath, file.originalPath);
          restored++;
        }
      } catch (err) {
        console.error(`[Yocto] 복구 실패: ${file.originalPath}`, err);
      }
    }

    // VS Code 문서 캐시 새로고침
    for (const file of reversedFiles) {
      try {
        const doc = await vscode.workspace.openTextDocument(file.originalPath);
        await vscode.window.showTextDocument(doc, { preview: true, preserveFocus: true });
      } catch {
        // 파일이 없거나 열 수 없는 경우 무시
      }
    }

    const durationMs = Date.now() - startTime;

    vscode.window.showInformationMessage(
      `YOLO Rewind 완료: ${restored}/${reversedFiles.length} 파일 복구 (${durationMs}ms)`
    );

    return { restoredFiles: restored, totalFiles: reversedFiles.length, durationMs };
  }

  /** 파일 단위 백업 스케줄링 (debounce) */
  private scheduleBackup(uri: vscode.Uri): void {
    const existing = this.pendingBackup.get(uri.fsPath);
    if (existing) clearTimeout(existing);

    const timeout = setTimeout(() => {
      this.pendingBackup.delete(uri.fsPath);
      this.backupFile(uri);
    }, this.DEBOUNCE_MS);

    this.pendingBackup.set(uri.fsPath, timeout);
  }

  /** 단일 파일 백업 */
  private async backupFile(uri: vscode.Uri): Promise<void> {
    try {
      const relativePath = vscode.workspace.asRelativePath(uri);
      const backupDir = path.join(this.snapshotsDir, this.currentSessionId, String(Date.now()));
      const backupPath = path.join(backupDir, relativePath);

      fs.mkdirSync(path.dirname(backupPath), { recursive: true });
      fs.copyFileSync(uri.fsPath, backupPath);

      const stat = fs.statSync(uri.fsPath);
      const entry: YoctoFileEntry = {
        originalPath: uri.fsPath,
        backupPath,
        hash: crypto.createHash('sha256').update(relativePath).digest('hex').substring(0, 16),
        size: stat.size,
        mtime: stat.mtimeMs,
      };

      // 가장 최근 스냅샷에 추가
      const latest = this.activeSnapshots[this.activeSnapshots.length - 1];
      if (latest) {
        latest.files.push(entry);
      }
    } catch (err) {
      console.error(`[Yocto] 백업 실패: ${uri.fsPath}`, err);
    }
  }

  /** 30일 이상 지난 백업 정리 */
  private cleanupOldSnapshots(daysOld: number): void {
    const cutoff = Date.now() - daysOld * 86400000;
    try {
      const entries = fs.readdirSync(this.snapshotsDir);
      for (const entry of entries) {
        const entryPath = path.join(this.snapshotsDir, entry);
        const stat = fs.statSync(entryPath);
        if (stat.mtimeMs < cutoff) {
          fs.rmSync(entryPath, { recursive: true, force: true });
        }
      }
    } catch {
      // 정리 실패는 치명적이지 않음
    }
  }

  dispose(): void {
    this.watcher?.dispose();
    for (const timer of this.pendingBackup.values()) {
      clearTimeout(timer);
    }
    this.pendingBackup.clear();
  }
}
