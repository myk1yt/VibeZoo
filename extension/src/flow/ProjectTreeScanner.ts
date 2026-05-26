// VibeZoo Wave 1: Project Tree Scanner
// 프로젝트 파일 구조를 스캔하여 30초 TTL 캐시로 유지한다.
// FileSystemWatcher로 파일 생성/삭제 시 증분 갱신.

import * as vscode from 'vscode';
import * as path from 'path';

export class ProjectTreeScanner {
  private treeCache: string | null = null;
  private cacheTimestamp: number = 0;
  private readonly CACHE_TTL_MS = 30000; // 30초
  private watcher: vscode.FileSystemWatcher | null = null;

  async initialize(context: vscode.ExtensionContext): Promise<void> {
    await this.rescan();

    const folders = vscode.workspace.workspaceFolders;
    if (!folders || folders.length === 0) return;

    // 파일 변경 감시 → 트리 증분 갱신
    this.watcher = vscode.workspace.createFileSystemWatcher(
      new vscode.RelativePattern(folders[0], '**/*')
    );

    let debounceTimer: NodeJS.Timeout | null = null;
    const refreshTree = () => {
      if (debounceTimer) clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => this.invalidateAndRescan(), 1000);
    };

    this.watcher.onDidCreate(refreshTree);
    this.watcher.onDidDelete(refreshTree);
    // 내용 변경은 무시 (성능)

    context.subscriptions.push(this.watcher);
  }

  /** 현재 트리 정보 반환 (캐시 TTL 만료 시 비동기 갱신) */
  getTreeForPrompt(): string {
    if (!this.treeCache) return '';
    if (Date.now() - this.cacheTimestamp > this.CACHE_TTL_MS) {
      this.rescan().catch(console.error);
    }
    return this.treeCache;
  }

  /** 전체 재스캔 */
  async rescan(): Promise<void> {
    const folders = vscode.workspace.workspaceFolders;
    if (!folders || folders.length === 0) return;

    const includePatterns = [
      '{package.json,Cargo.toml,go.mod,pyproject.toml,pom.xml,README.md,AGENTS.md,.zoo.md}',
      'src/**/*',
      'lib/**/*',
      'app/**/*',
      'pages/**/*',
      'components/**/*',
    ];

    const excludePattern = '{**/node_modules/**,**/.git/**,**/dist/**,**/build/**,**/.next/**,**/coverage/**,**/target/**}';

    const treeLines: string[] = ['## Project Structure (VibeZoo)'];

    for (const pattern of includePatterns) {
      try {
        const files = await vscode.workspace.findFiles(pattern, excludePattern, 100);
        for (const f of files) {
          const rel = vscode.workspace.asRelativePath(f);
          treeLines.push(`  ${rel}`);
        }
      } catch {
        // 패턴 매칭 실패 — 무시
      }
    }

    this.treeCache = treeLines.join('\n');
    this.cacheTimestamp = Date.now();
  }

  dispose(): void {
    this.watcher?.dispose();
  }

  private async invalidateAndRescan(): Promise<void> {
    this.treeCache = null;
    await this.rescan();
  }
}
