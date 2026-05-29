"use strict";
// VibeZoo Wave 1: Project Tree Scanner
// 프로젝트 파일 구조를 스캔하여 30초 TTL 캐시로 유지한다.
// FileSystemWatcher로 파일 생성/삭제 시 증분 갱신.
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.ProjectTreeScanner = void 0;
const vscode = __importStar(require("vscode"));
class ProjectTreeScanner {
    treeCache = null;
    cacheTimestamp = 0;
    CACHE_TTL_MS = 30000; // 30초
    watcher = null;
    async initialize(context) {
        await this.rescan();
        const folders = vscode.workspace.workspaceFolders;
        if (!folders || folders.length === 0)
            return;
        // 파일 변경 감시 → 트리 증분 갱신
        this.watcher = vscode.workspace.createFileSystemWatcher(new vscode.RelativePattern(folders[0], '**/*'));
        let debounceTimer = null;
        const refreshTree = () => {
            if (debounceTimer)
                clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => this.invalidateAndRescan(), 1000);
        };
        this.watcher.onDidCreate(refreshTree);
        this.watcher.onDidDelete(refreshTree);
        // 내용 변경은 무시 (성능)
        context.subscriptions.push(this.watcher);
    }
    /** 현재 트리 정보 반환 (캐시 TTL 만료 시 비동기 갱신) */
    getTreeForPrompt() {
        if (!this.treeCache)
            return '';
        if (Date.now() - this.cacheTimestamp > this.CACHE_TTL_MS) {
            this.rescan().catch(console.error);
        }
        return this.treeCache;
    }
    /** 전체 재스캔 */
    async rescan() {
        const folders = vscode.workspace.workspaceFolders;
        if (!folders || folders.length === 0)
            return;
        const includePatterns = [
            '{package.json,Cargo.toml,go.mod,pyproject.toml,pom.xml,README.md,AGENTS.md,.zoo.md}',
            'src/**/*',
            'lib/**/*',
            'app/**/*',
            'pages/**/*',
            'components/**/*',
        ];
        const excludePattern = '{**/node_modules/**,**/.git/**,**/dist/**,**/build/**,**/.next/**,**/coverage/**,**/target/**}';
        const treeLines = ['## Project Structure (VibeZoo)'];
        for (const pattern of includePatterns) {
            try {
                const files = await vscode.workspace.findFiles(pattern, excludePattern, 100);
                for (const f of files) {
                    const rel = vscode.workspace.asRelativePath(f);
                    treeLines.push(`  ${rel}`);
                }
            }
            catch {
                // 패턴 매칭 실패 — 무시
            }
        }
        this.treeCache = treeLines.join('\n');
        this.cacheTimestamp = Date.now();
    }
    dispose() {
        this.watcher?.dispose();
    }
    async invalidateAndRescan() {
        this.treeCache = null;
        await this.rescan();
    }
}
exports.ProjectTreeScanner = ProjectTreeScanner;
//# sourceMappingURL=ProjectTreeScanner.js.map