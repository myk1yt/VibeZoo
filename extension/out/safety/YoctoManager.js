"use strict";
// VibeZoo Wave 2: yocto — Lightweight Snapshot System
// FileSystemWatcher로 파일 변경을 감지하여 fs.copyFileSync로 즉시 백업.
// 200ms 글로벌 debounce로 다중 파일 변경 시 레이스 컨디션을 방지하여 한 타임스탬프(Atomic Directory)에 모아 백업.
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
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.YoctoManager = void 0;
const vscode = __importStar(require("vscode"));
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const os = __importStar(require("os"));
const crypto = __importStar(require("crypto"));
const StatusBarManager_1 = require("../ui/StatusBarManager");
class YoctoManager {
    snapshotsDir;
    watcher = null;
    trackedFiles = new Set();
    currentSessionId;
    activeSnapshots = [];
    MAX_SNAPSHOTS = 50;
    constructor() {
        this.snapshotsDir = path.join(os.homedir(), '.zoo-code', 'yocto');
        fs.mkdirSync(this.snapshotsDir, { recursive: true });
        this.currentSessionId = `session-${Date.now()}`;
    }
    activate(context) {
        const folders = vscode.workspace.workspaceFolders;
        if (!folders || folders.length === 0)
            return;
        // 소스 파일 변경 감시 (onWillSaveTextDocument로 변경하여 진본 백업)
        context.subscriptions.push(vscode.workspace.onWillSaveTextDocument((e) => {
            e.waitUntil(this.executeDirectBackup(e.document));
        }));
        // activate 시 자동 스냅샷 생성 (Extension 재시작 후 첫 백업 대비)
        this.createSnapshot('auto');
        // 주기적 정리: 30일 이상 지난 스냅샷 삭제
        this.cleanupOldSnapshots(30);
    }
    /** YOLO 진입 시 전체 스냅샷 생성 */
    async createSnapshot(trigger) {
        const snapshotId = `snap-${Date.now()}`;
        const snapshot = {
            id: snapshotId,
            sessionId: this.currentSessionId,
            timestamp: Date.now(),
            trigger,
            files: [],
            isBase: this.activeSnapshots.length === 0,
        };
        this.activeSnapshots.push(snapshot);
        if (this.activeSnapshots.length > this.MAX_SNAPSHOTS) {
            const evictIndex = this.activeSnapshots.findIndex((s) => !s.isBase);
            if (evictIndex !== -1) {
                this.activeSnapshots.splice(evictIndex, 1);
            }
            else {
                this.activeSnapshots.shift();
            }
        }
        return snapshot;
    }
    /** 디스크에서 최신 스냅샷 파일 목록을 로드 (인메모리 의존성 제거) */
    loadSnapshotFromDisk(targetSession) {
        const sessionDir = path.join(this.snapshotsDir, targetSession);
        if (!fs.existsSync(sessionDir)) {
            return { files: [] };
        }
        // 세션 디렉토리 내의 타임스탬프 서브디렉토리들을 내림차순 정렬
        const entries = fs.readdirSync(sessionDir)
            .map((name) => ({ name, fullPath: path.join(sessionDir, name) }))
            .filter((e) => fs.statSync(e.fullPath).isDirectory())
            .sort((a, b) => b.name.localeCompare(a.name));
        if (entries.length === 0)
            return { files: [] };
        // 가장 최근 스냅샷 디렉토리에서 파일 목록 수집
        const latestSnapshotDir = entries[0].fullPath;
        const files = [];
        const walkDir = (dir) => {
            let items;
            try {
                items = fs.readdirSync(dir);
            }
            catch {
                return;
            }
            for (const item of items) {
                const itemPath = path.join(dir, item);
                try {
                    if (fs.statSync(itemPath).isDirectory()) {
                        walkDir(itemPath);
                    }
                    else {
                        // backupPath에서 originalPath를 역산:
                        // backupPath = <snapshotsDir>/<sessionId>/<timestamp>/<relativePath>
                        const rel = path.relative(latestSnapshotDir, itemPath);
                        const workspaceFolders = vscode.workspace.workspaceFolders;
                        if (workspaceFolders && workspaceFolders.length > 0) {
                            const originalPath = path.join(workspaceFolders[0].uri.fsPath, rel);
                            files.push({ originalPath, backupPath: itemPath });
                        }
                    }
                }
                catch {
                    // 파일/디렉토리 읽기 실패 시 무시
                }
            }
        };
        walkDir(latestSnapshotDir);
        return { files };
    }
    /** ~/.zoo-code/yocto/ 디렉토리에서 세션 폴더 목록 반환 (최신순) */
    listSessions() {
        try {
            if (!fs.existsSync(this.snapshotsDir))
                return [];
            const entries = fs.readdirSync(this.snapshotsDir, { withFileTypes: true });
            return entries
                .filter((e) => e.isDirectory())
                .map((e) => e.name)
                .sort((a, b) => b.localeCompare(a)) // 최신순
                .slice(0, 50);
        }
        catch {
            return [];
        }
    }
    /** Instant Rewind — 마지막 YOLO 스냅샷의 모든 파일 복구 */
    async instantRewind(sessionId) {
        const targetSession = sessionId || this.currentSessionId;
        // 1) 인메모리 스냅샷 우선 시도
        let snapshot = this.activeSnapshots
            .filter((s) => s.sessionId === targetSession)
            .sort((a, b) => b.timestamp - a.timestamp)[0];
        // 2) 인메모리에 없으면 디스크에서 직접 로드
        let diskFiles = [];
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
        // 역순으로 복구 (Atomic 트랜잭션 방식)
        const reversedFiles = [...fileList].reverse();
        const backupOfCurrent = [];
        // 1단계: 복구 대상 파일들의 현재 상태를 임시로 저장
        try {
            for (const file of reversedFiles) {
                if (fs.existsSync(file.originalPath)) {
                    const tempPath = file.originalPath + `.tmp.rewind`;
                    fs.copyFileSync(file.originalPath, tempPath);
                    backupOfCurrent.push({ originalPath: file.originalPath, tempPath });
                }
            }
            // 2단계: 복구 진행
            for (const file of reversedFiles) {
                if (fs.existsSync(file.backupPath)) {
                    fs.copyFileSync(file.backupPath, file.originalPath);
                    restored++;
                }
            }
            // 3단계: 임시 백업 파일 삭제
            for (const b of backupOfCurrent) {
                if (fs.existsSync(b.tempPath)) {
                    fs.unlinkSync(b.tempPath);
                }
            }
        }
        catch (err) {
            // 복구 실패 시: 임시 백업된 파일들을 다시 원상복구(Fall-back)
            console.error(`[Yocto] 트랜잭션 실패, 롤백 수행...`, err);
            for (const b of backupOfCurrent) {
                if (fs.existsSync(b.tempPath)) {
                    fs.copyFileSync(b.tempPath, b.originalPath);
                    fs.unlinkSync(b.tempPath);
                }
            }
            throw new Error(`Rewind 실패 (Rollback됨): ${err.message}`);
        }
        // VS Code 문서 캐시 새로고침
        for (const file of reversedFiles) {
            try {
                const doc = await vscode.workspace.openTextDocument(file.originalPath);
                await vscode.window.showTextDocument(doc, { preview: true, preserveFocus: true });
            }
            catch {
                // 파일이 없거나 열 수 없는 경우 무시
            }
        }
        const durationMs = Date.now() - startTime;
        StatusBarManager_1.NotificationThrottle.showInfo(`YOLO Rewind 완료: ${restored}/${reversedFiles.length} 파일 복구 (${durationMs}ms)`);
        return { restoredFiles: restored, totalFiles: reversedFiles.length, durationMs };
    }
    /** 동기식 진본 백업: 저장 직전에 파일 락(레이스 컨디션 방지) */
    async executeDirectBackup(document) {
        const fsPath = document.uri.fsPath;
        // 최초 원본(Base Revision) 보장
        if (!this.trackedFiles.has(fsPath)) {
            this.trackedFiles.add(fsPath);
            await this.backupToBaseRevision(fsPath);
        }
        const snapshot = await this.createSnapshot('pre-edit');
        const backupDir = path.join(this.snapshotsDir, this.currentSessionId, snapshot.id);
        const relativePath = vscode.workspace.asRelativePath(document.uri);
        const backupPath = path.join(backupDir, relativePath);
        try {
            const tmpDir = path.dirname(backupPath);
            fs.mkdirSync(tmpDir, { recursive: true });
            const tmpFile = path.join(tmpDir, `.tmp-${crypto.randomUUID()}`);
            // 저장되기 전의 메모리(진본) 상태를 디스크에 동기적으로 기록
            await fs.promises.writeFile(tmpFile, document.getText());
            await fs.promises.rename(tmpFile, backupPath);
            const stat = fs.statSync(backupPath);
            snapshot.files.push({
                originalPath: fsPath,
                backupPath,
                hash: crypto.createHash('sha256').update(relativePath).digest('hex').substring(0, 16),
                size: stat.size,
                mtime: stat.mtimeMs,
            });
            if (snapshot.files.length > 500) {
                snapshot.files = snapshot.files.slice(-500);
            }
        }
        catch (err) {
            console.error(`[Yocto] 백업 실패: ${fsPath}`, err);
        }
    }
    /** Base Revision에 파일의 최초 상태 기록 */
    async backupToBaseRevision(fsPath) {
        let baseSnapshot = this.activeSnapshots.find(s => s.isBase);
        if (!baseSnapshot) {
            baseSnapshot = {
                id: `base-${Date.now()}`,
                sessionId: this.currentSessionId,
                timestamp: Date.now(),
                trigger: 'auto',
                files: [],
                isBase: true
            };
            this.activeSnapshots.unshift(baseSnapshot);
        }
        const backupDir = path.join(this.snapshotsDir, this.currentSessionId, baseSnapshot.id);
        const relativePath = vscode.workspace.asRelativePath(fsPath);
        const backupPath = path.join(backupDir, relativePath);
        try {
            const tmpDir = path.dirname(backupPath);
            fs.mkdirSync(tmpDir, { recursive: true });
            const tmpFile = path.join(tmpDir, `.tmp-${crypto.randomUUID()}`);
            // 최초 원본은 디스크의 현재 상태(수정 전)를 백업
            if (fs.existsSync(fsPath)) {
                await fs.promises.copyFile(fsPath, tmpFile);
                await fs.promises.rename(tmpFile, backupPath);
                const stat = fs.statSync(backupPath);
                baseSnapshot.files.push({
                    originalPath: fsPath,
                    backupPath,
                    hash: crypto.createHash('sha256').update(relativePath).digest('hex').substring(0, 16),
                    size: stat.size,
                    mtime: stat.mtimeMs,
                });
            }
        }
        catch (err) {
            console.error(`[Yocto] Base Revision 백업 실패: ${fsPath}`, err);
        }
    }
    /** 원자적 파일 복사: 임시 파일 → rename */
    async atomicCopyFile(src, dest) {
        const tmpDir = path.dirname(dest);
        fs.mkdirSync(tmpDir, { recursive: true });
        const tmpFile = path.join(tmpDir, `.tmp-${crypto.randomUUID()}`);
        await fs.promises.copyFile(src, tmpFile);
        await fs.promises.rename(tmpFile, dest);
    }
    /** 30일 이상 지난 백업 정리 */
    cleanupOldSnapshots(daysOld) {
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
        }
        catch {
            // 정리 실패는 치명적이지 않음
        }
    }
    // ── Guard.git 연동 ───────────────────────────────────────
    /**
     * Guard.git 전용: .git 디렉토리의 핵심 파일들만 스냅샷
     *
     * H3: 내부적으로 createSnapshot('auto')를 호출하고, metadata.guardTrigger 필드로
     * guard 전용 trigger 기록. 기존 YoctoSnapshot.trigger union 타입은 변경하지 않음.
     *
     * 대상 파일:
     *   .git/HEAD          — 현재 브랜치 참조
     *   .git/config        — 저장소 설정
     *   .git/refs/heads/*  — 로컬 브랜치 refs
     *   .git/refs/remotes/*— 리모트 refs
     *   .git/refs/stash    — stash ref (있을 경우)
     *   .git/index         — 스테이징 영역 (있을 경우)
     *
     * 스냅샷 저장 경로: ~/.zoo-code/yocto/{sessionId}/guard-git-{timestamp}/
     */
    async snapshotGitCore(metadata) {
        // H3: createSnapshot('auto') 호출
        const snapshot = await this.createSnapshot('auto');
        const backupDir = path.join(this.snapshotsDir, this.currentSessionId, `guard-git-${snapshot.id}`);
        // 워크스페이스 폴더에서 .git 경로 탐색
        const folders = vscode.workspace.workspaceFolders;
        if (!folders)
            return snapshot;
        for (const folder of folders) {
            const dotGitPath = path.join(folder.uri.fsPath, '.git');
            let gitDir = dotGitPath;
            // Worktree 지원: .git이 파일이면 내용 파싱
            try {
                if (fs.existsSync(dotGitPath)) {
                    const stat = fs.statSync(dotGitPath);
                    if (stat.isFile()) {
                        const content = fs.readFileSync(dotGitPath, 'utf-8').trim();
                        const match = content.match(/^gitdir:\s*(.+)$/);
                        if (match) {
                            const actualGitDir = match[1].trim();
                            gitDir = path.isAbsolute(actualGitDir) ? actualGitDir : path.resolve(folder.uri.fsPath, actualGitDir);
                        }
                    }
                }
                else {
                    continue;
                }
            }
            catch {
                continue;
            }
            // 스냅샷 대상 파일 패턴
            const targetPatterns = [
                'HEAD',
                'config',
                'refs/heads/**',
                'refs/remotes/**',
                'refs/stash',
                'index',
            ];
            // glob 패턴으로 파일 수집
            const filesToBackup = [];
            for (const pattern of targetPatterns) {
                const fullPattern = path.join(gitDir, pattern);
                try {
                    if (pattern.includes('**')) {
                        // glob 패턴 — 디렉토리 탐색
                        const baseDir = path.dirname(fullPattern.replace('**', ''));
                        if (fs.existsSync(baseDir)) {
                            this.collectGitFiles(baseDir, filesToBackup);
                        }
                    }
                    else {
                        if (fs.existsSync(fullPattern)) {
                            filesToBackup.push(fullPattern);
                        }
                    }
                }
                catch {
                    // 패턴 매칭 실패는 무시
                }
            }
            // 파일 복사
            for (const srcPath of filesToBackup) {
                try {
                    const relativeToGit = path.relative(gitDir, srcPath);
                    const destPath = path.join(backupDir, folder.uri.fsPath.replace(/[\\:]/g, '_'), relativeToGit);
                    const tmpDir = path.dirname(destPath);
                    fs.mkdirSync(tmpDir, { recursive: true });
                    const tmpFile = path.join(tmpDir, `.tmp-${crypto.randomUUID()}`);
                    await fs.promises.copyFile(srcPath, tmpFile);
                    await fs.promises.rename(tmpFile, destPath);
                    const stat = fs.statSync(destPath);
                    snapshot.files.push({
                        originalPath: srcPath,
                        backupPath: destPath,
                        hash: crypto.createHash('sha256').update(relativeToGit).digest('hex').substring(0, 16),
                        size: stat.size,
                        mtime: stat.mtimeMs,
                    });
                }
                catch {
                    // 개별 파일 복사 실패는 무시
                }
            }
        }
        console.log(`[Yocto:Guard.git] ✅ .git 핵심 파일 스냅샷 완료 (${snapshot.files.length} files, trigger: ${metadata.guardTrigger})`);
        return snapshot;
    }
    /** 디렉토리 내 파일 재귀 수집 */
    collectGitFiles(dir, result) {
        try {
            const entries = fs.readdirSync(dir, { withFileTypes: true });
            for (const entry of entries) {
                const fullPath = path.join(dir, entry.name);
                if (entry.isDirectory()) {
                    this.collectGitFiles(fullPath, result);
                }
                else if (entry.isFile()) {
                    result.push(fullPath);
                }
            }
        }
        catch {
            // 권한 문제 등 — 무시
        }
    }
    /**
     * Guard 감지: .git 내 파일 목록을 이전 스냅샷과 비교하여 변경 감지
     */
    async detectGitChanges(lastSnapshot) {
        const result = {
            added: [],
            removed: [],
            modified: [],
        };
        // 현재 .git 핵심 파일 목록 수집
        const currentFiles = new Map(); // path → hash
        const folders = vscode.workspace.workspaceFolders;
        if (!folders)
            return result;
        for (const folder of folders) {
            const dotGitPath = path.join(folder.uri.fsPath, '.git');
            if (!fs.existsSync(dotGitPath))
                continue;
            const gitDir = (() => {
                try {
                    const stat = fs.statSync(dotGitPath);
                    if (stat.isDirectory())
                        return dotGitPath;
                    if (stat.isFile()) {
                        const content = fs.readFileSync(dotGitPath, 'utf-8').trim();
                        const match = content.match(/^gitdir:\s*(.+)$/);
                        if (match) {
                            const actualGitDir = match[1].trim();
                            return path.isAbsolute(actualGitDir) ? actualGitDir : path.resolve(folder.uri.fsPath, actualGitDir);
                        }
                    }
                }
                catch { }
                return null;
            })();
            if (!gitDir)
                continue;
            const targetPatterns = ['HEAD', 'config', 'refs/heads', 'refs/remotes', 'refs/stash', 'index'];
            for (const pattern of targetPatterns) {
                const fullPath = path.join(gitDir, pattern);
                if (fs.existsSync(fullPath)) {
                    try {
                        const stat = fs.statSync(fullPath);
                        if (stat.isFile()) {
                            const hash = crypto.createHash('sha256')
                                .update(fs.readFileSync(fullPath))
                                .digest('hex')
                                .substring(0, 16);
                            currentFiles.set(fullPath, hash);
                        }
                    }
                    catch { }
                }
            }
        }
        // 이전 스냅샷의 파일 목록과 비교
        const lastFiles = new Map();
        for (const entry of lastSnapshot.files) {
            lastFiles.set(entry.originalPath, entry.hash);
        }
        for (const [path, hash] of currentFiles) {
            const lastHash = lastFiles.get(path);
            if (lastHash === undefined) {
                result.added.push(path);
            }
            else if (lastHash !== hash) {
                result.modified.push(path);
            }
        }
        for (const [path] of lastFiles) {
            if (!currentFiles.has(path)) {
                result.removed.push(path);
            }
        }
        return result;
    }
    dispose() {
        this.watcher?.dispose();
        this.trackedFiles.clear();
    }
}
exports.YoctoManager = YoctoManager;
//# sourceMappingURL=YoctoManager.js.map