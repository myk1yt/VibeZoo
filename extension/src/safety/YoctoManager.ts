// VibeZoo Wave 2: yocto — Lightweight Snapshot System
// FileSystemWatcher로 파일 변경을 감지하여 fs.copyFileSync로 즉시 백업.
// 200ms 글로벌 debounce로 다중 파일 변경 시 레이스 컨디션을 방지하여 한 타임스탬프(Atomic Directory)에 모아 백업.

import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import * as crypto from 'crypto';
import { YoctoSnapshot, YoctoFileEntry } from '../types';
import { NotificationThrottle } from '../ui/StatusBarManager';

export class YoctoManager {
  private snapshotsDir: string;
  private watcher: vscode.FileSystemWatcher | null = null;
  private pendingFiles: Set<string> = new Set();
  private globalDebounceTimer: NodeJS.Timeout | null = null;
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

    // activate 시 자동 스냅샷 생성 (Extension 재시작 후 첫 백업 대비)
    this.createSnapshot('auto');

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

  /** 디스크에서 최신 스냅샷 파일 목록을 로드 (인메모리 의존성 제거) */
  private loadSnapshotFromDisk(targetSession: string): { files: Array<{ originalPath: string; backupPath: string }> } {
    const sessionDir = path.join(this.snapshotsDir, targetSession);
    if (!fs.existsSync(sessionDir)) {
      return { files: [] };
    }

    // 세션 디렉토리 내의 타임스탬프 서브디렉토리들을 내림차순 정렬
    const entries = fs.readdirSync(sessionDir)
      .map((name) => ({ name, fullPath: path.join(sessionDir, name) }))
      .filter((e) => fs.statSync(e.fullPath).isDirectory())
      .sort((a, b) => b.name.localeCompare(a.name));

    if (entries.length === 0) return { files: [] };

    // 가장 최근 스냅샷 디렉토리에서 파일 목록 수집
    const latestSnapshotDir = entries[0].fullPath;
    const files: Array<{ originalPath: string; backupPath: string }> = [];

    const walkDir = (dir: string) => {
      let items;
      try {
        items = fs.readdirSync(dir);
      } catch {
        return;
      }
      for (const item of items) {
        const itemPath = path.join(dir, item);
        try {
          if (fs.statSync(itemPath).isDirectory()) {
            walkDir(itemPath);
          } else {
            // backupPath에서 originalPath를 역산:
            // backupPath = <snapshotsDir>/<sessionId>/<timestamp>/<relativePath>
            const rel = path.relative(latestSnapshotDir, itemPath);
            const workspaceFolders = vscode.workspace.workspaceFolders;
            if (workspaceFolders && workspaceFolders.length > 0) {
              const originalPath = path.join(workspaceFolders[0].uri.fsPath, rel);
              files.push({ originalPath, backupPath: itemPath });
            }
          }
        } catch {
          // 파일/디렉토리 읽기 실패 시 무시
        }
      }
    };

    walkDir(latestSnapshotDir);
    return { files };
  }

  /** ~/.zoo-code/yocto/ 디렉토리에서 세션 폴더 목록 반환 (최신순) */
  listSessions(): string[] {
    try {
      if (!fs.existsSync(this.snapshotsDir)) return [];
      const entries = fs.readdirSync(this.snapshotsDir, { withFileTypes: true });
      return entries
        .filter((e) => e.isDirectory())
        .map((e) => e.name)
        .sort((a, b) => b.localeCompare(a)) // 최신순
        .slice(0, 50);
    } catch {
      return [];
    }
  }

  /** Instant Rewind — 마지막 YOLO 스냅샷의 모든 파일 복구 */
  async instantRewind(sessionId?: string): Promise<{ restoredFiles: number; totalFiles: number; durationMs: number }> {
    const targetSession = sessionId || this.currentSessionId;

    // 1) 인메모리 스냅샷 우선 시도
    let snapshot = this.activeSnapshots
      .filter((s) => s.sessionId === targetSession)
      .sort((a, b) => b.timestamp - a.timestamp)[0];

    // 2) 인메모리에 없으면 디스크에서 직접 로드
    let diskFiles: Array<{ originalPath: string; backupPath: string }> = [];
    if (!snapshot || snapshot.files.length === 0) {
      const loaded = this.loadSnapshotFromDisk(targetSession);
      diskFiles = loaded.files;
      if (diskFiles.length === 0) {
        throw new Error('되돌릴 스냅샷이 없습니다.');
      }
    }

    const startTime = Date.now();
    let restored = 0;

    // snapshot.files (인메모리) 또는 diskFiles (디스크) 사용
    const fileList = snapshot && snapshot.files.length > 0
      ? snapshot.files.map((f) => ({ originalPath: f.originalPath, backupPath: f.backupPath }))
      : diskFiles;

    // 역순으로 복구
    const reversedFiles = [...fileList].reverse();
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

    NotificationThrottle.showInfo(
      `YOLO Rewind 완료: ${restored}/${reversedFiles.length} 파일 복구 (${durationMs}ms)`
    );

    return { restoredFiles: restored, totalFiles: reversedFiles.length, durationMs };
  }

  /** 다중 파일 글로벌 백업 스케줄링 (debounce) */
  private scheduleBackup(uri: vscode.Uri): void {
    this.pendingFiles.add(uri.fsPath);

    if (this.globalDebounceTimer) {
      clearTimeout(this.globalDebounceTimer);
    }

    this.globalDebounceTimer = setTimeout(() => {
      this.executeGlobalBackup();
    }, this.DEBOUNCE_MS);
  }

  /** 원자적 파일 복사: 임시 파일 → rename */
  private async atomicCopyFile(src: string, dest: string): Promise<void> {
    const tmpDir = path.dirname(dest);
    fs.mkdirSync(tmpDir, { recursive: true });
    const tmpFile = path.join(tmpDir, `.tmp-${crypto.randomUUID()}`);
    await fs.promises.copyFile(src, tmpFile);
    await fs.promises.rename(tmpFile, dest);
  }

  /** 보류 중인 모든 파일을 단일 타임스탬프 디렉토리에 원자적으로 백업 */
  private async executeGlobalBackup(): Promise<void> {
    if (this.pendingFiles.size === 0) return;
    
    const filesToBackup = Array.from(this.pendingFiles);
    this.pendingFiles.clear();
    this.globalDebounceTimer = null;

    const timestampStr = String(Date.now());
    const backupDir = path.join(this.snapshotsDir, this.currentSessionId, timestampStr);

    let latest = this.activeSnapshots[this.activeSnapshots.length - 1];
    if (!latest) {
      latest = await this.createSnapshot('auto');
    }

    for (const fsPath of filesToBackup) {
      try {
        const uri = vscode.Uri.file(fsPath);
        const relativePath = vscode.workspace.asRelativePath(uri);
        const backupPath = path.join(backupDir, relativePath);

        await this.atomicCopyFile(fsPath, backupPath);

        const stat = fs.statSync(fsPath);
        const entry: YoctoFileEntry = {
          originalPath: fsPath,
          backupPath,
          hash: crypto.createHash('sha256').update(relativePath).digest('hex').substring(0, 16),
          size: stat.size,
          mtime: stat.mtimeMs,
        };
        latest.files.push(entry);
      } catch (err) {
        console.error(`[Yocto] 백업 실패: ${fsPath}`, err);
      }
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
    if (this.globalDebounceTimer) {
      clearTimeout(this.globalDebounceTimer);
    }
    this.pendingFiles.clear();
  }
}
