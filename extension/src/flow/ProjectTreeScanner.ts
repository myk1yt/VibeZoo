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

  /** 비동기 제너레이터를 이용한 재귀적 디렉토리 스캔 (메모리 최적화) */
  private async *walkDirectory(dirUri: vscode.Uri, depth: number = 0, excludeNames: Set<string>): AsyncGenerator<{ uri: vscode.Uri; relPath: string; isDir: boolean; depth: number }> {
    try {
      const entries = await vscode.workspace.fs.readDirectory(dirUri);
      for (const [name, type] of entries) {
        if (excludeNames.has(name) || name === '.git') continue;

        const isDir = (type & vscode.FileType.Directory) !== 0;
        const childUri = vscode.Uri.joinPath(dirUri, name);
        const relPath = vscode.workspace.asRelativePath(childUri);

        yield { uri: childUri, relPath, isDir, depth };

        if (isDir) {
          if (depth < 3) { // 3단계 깊이까지만 즉시 전개, 나머지는 Lazy Loading 힌트 제공
            yield* this.walkDirectory(childUri, depth + 1, excludeNames);
          } else {
            yield { uri: childUri, relPath: relPath + '/... (접힘: 필요시 탐색 요망)', isDir: true, depth: depth + 1 };
          }
        }
      }
    } catch {
      // 접근 불가 폴더 무시
    }
  }

  /** 전체 재스캔 */
  async rescan(): Promise<void> {
    const folders = vscode.workspace.workspaceFolders;
    if (!folders || folders.length === 0) return;

    const excludeNames = new Set(['node_modules', 'dist', 'build', '.next', 'coverage', 'target']);
    const treeLines: string[] = ['## Project Structure (VibeZoo - Async Streaming)'];
    const rootUri = folders[0].uri;

    for await (const node of this.walkDirectory(rootUri, 0, excludeNames)) {
      const indent = '  '.repeat(node.depth);
      const name = node.relPath.split(/[/\\]/).pop();
      if (node.isDir) {
        treeLines.push(`${indent}- 📁 ${name}`);
      } else {
        treeLines.push(`${indent}- 📄 ${name}`);
      }
    }

    this.treeCache = treeLines.join('\n');
    this.cacheTimestamp = Date.now();
  }

  dispose(): void {
    this.watcher?.dispose();
  }

  private async invalidateAndRescan(): Promise<void> {
    // SWR (Stale-while-revalidate): 기존 캐시를 유지한 상태로 백그라운드 스캔 수행
    await this.rescan();
  }
}
