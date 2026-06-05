import * as vscode from 'vscode';
export declare class ProjectTreeScanner {
    private treeCache;
    private cacheTimestamp;
    private readonly CACHE_TTL_MS;
    private watcher;
    initialize(context: vscode.ExtensionContext): Promise<void>;
    /** 현재 트리 정보 반환 (캐시 TTL 만료 시 비동기 갱신) */
    getTreeForPrompt(): string;
    /** 비동기 제너레이터를 이용한 재귀적 디렉토리 스캔 (메모리 최적화) */
    private walkDirectory;
    /** 전체 재스캔 */
    rescan(): Promise<void>;
    dispose(): void;
    private invalidateAndRescan;
}
//# sourceMappingURL=ProjectTreeScanner.d.ts.map