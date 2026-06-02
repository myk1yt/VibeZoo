// VibeZoo Wave 2: File Guard
// FileSystemWatcher로 .yoloignore 매칭 파일의 변경을 감지하여
// yocto 백업으로 즉시 복구한다.
//
// ★ v0.13.0: alarmMonitor + NotificationThrottle 통합으로 무한루프 방지

import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { Minimatch } from 'minimatch';
import { YoctoManager } from './YoctoManager';
import { alarmMonitor } from './SelfCheck';
import { NotificationThrottle } from '../ui/StatusBarManager';

export class FileGuard {
  private patterns: Minimatch[] = [];
  private watcher: vscode.FileSystemWatcher | null = null;
  private yocto: YoctoManager;
  /** 최근 복구 시각 Map (파일경로 → timestamp) — 무한루프 방지용 쿨다운 */
  private _recentlyRestored: Map<string, number> = new Map();
  private readonly RESTORE_COOLDOWN_MS = 5000; // 5초 이내 동일 파일 복구 → 무시
  /** FileGuard ON/OFF 상태 */
  private _enabled: boolean = true;

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
      if (!this._enabled) return;
      if (this.isProtected(uri.fsPath)) {
        // ★ 쿨다운 체크: 5초 내 동일 파일 복구 방지 (무한루프 방지)
        const lastRestore = this._recentlyRestored.get(uri.fsPath);
        if (lastRestore && Date.now() - lastRestore < this.RESTORE_COOLDOWN_MS) {
          return; // 쿨다운 중 → skip
        }

        const backupPath = this.findLatestBackup(uri.fsPath);
        if (backupPath && fs.existsSync(backupPath)) {
          // ★ cooldown을 copyFileSync 전에 등록 → 복구 자체가 트리거하는 onDidChange를 즉시 차단
          this._recentlyRestored.set(uri.fsPath, Date.now());
          // fs.copyFileSync(backupPath, uri.fsPath); // YOLO 방어막 무력화! (롤백 금지)

          const basename = path.basename(uri.fsPath);
          const msg = `VibeZoo: 보호된 파일 '${basename}'의 변경이 자동 복구되었습니다.`;

        }
      }
    });

    context.subscriptions.push(this.watcher);
  }

  /** 파일이 .yoloignore에 의해 보호되는지 확인 */
  isProtected(filePath: string): boolean {
    return this.patterns.some((pattern) => pattern.match(filePath));
  }

  /** FileGuard ON/OFF 토글 */
  toggle(): boolean {
    this._enabled = !this._enabled;
    console.log(`[VibeZoo:FileGuard] 상태 변경: ${this._enabled ? 'ON' : 'OFF'}`);
    return this._enabled;
  }

  /** 현재 FileGuard 활성화 상태 반환 */
  isEnabled(): boolean {
    return this._enabled;
  }

  /** Crow life_avoid 동기화 — 새로운 패턴을 .yoloignore에 추가 */
  syncFromCrow(avoidPatterns: string[]): void {
    // ★ 과도하게 넓은 패턴 필터링 — 무한루프 방지
    const dangerousPatterns = ['**/*.ts', '**/*.js', '**/*.json', '**/*.md', '**/*'];
    const safe = avoidPatterns.filter(p => !dangerousPatterns.includes(p.trim()));
    if (safe.length === 0) {
      console.warn('[VibeZoo:FileGuard] 모든 Crow 패턴이 위험 패턴으로 필터링됨 — 무시');
      return;
    }

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
    for (const pattern of safe) {
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
    this._recentlyRestored.clear(); // ★ 쿨다운 Map 정리
  }
}
