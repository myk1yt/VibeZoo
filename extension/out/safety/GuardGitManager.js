"use strict";
// VibeZoo v0.14.3: GuardGitManager — Guard.git 핵심 오케스트레이터
//
// C4: 멀티 루트 워크스페이스 지원
//   - gitDirPaths: string[] — 모든 .git 경로 관리
//   - stateMap: Map<string, GuardGitState> — 경로별 상태
//   - watchers: Map<string, vscode.FileSystemWatcher> — 경로별 watcher
//   - onDidChangeWorkspaceFolders 구독
//
// H1: Git Worktree 탐지 (resolveGitDir)
// H5: Rename 감시 (2초 delete+create window), 주기적 checkProtection (5분)
// H6: activate() 시 cleanupResidualACL() 호출
// M1: onChange() 콜백 해제 메커니즘 포함
// R2: startWatcher()에서 기존 watcher dispose
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
exports.GuardGitManager = void 0;
const vscode = __importStar(require("vscode"));
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const GuardGitACL_1 = require("./GuardGitACL");
const ConfigService_1 = require("../config/ConfigService");
// NotificationThrottle 참조 (fallback 처리 — 7.1 해결)
// StatusBarManager에서 export된 NotificationThrottle을 재사용
const StatusBarManager_1 = require("../ui/StatusBarManager");
class GuardGitManager {
    // ── 상태 ──
    stateMap = new Map();
    gitDirPaths = [];
    acl;
    watchers = new Map();
    yocto = null;
    statusBar = null;
    selfCheckInterval = null;
    yoctoBackupInterval = null;
    disposables = [];
    // ── H5: Rename 감지를 위한 pending deletions ──
    pendingDeletions = new Map();
    // ── M1: onChange 콜백 ──
    _onChangeCallbacks = [];
    constructor() {
        this.acl = (0, GuardGitACL_1.createGuardGitACL)();
    }
    // ── 생명주기 ──
    /**
     * GuardGitManager 초기화
     * H6: activate() 시작 시 cleanupResidualACL() 호출
     * Bug #4: yocto가 null이어도 Yocto 기능만 skip하고 ACL/Watcher는 정상 동작
     */
    async activate(context, yocto) {
        this.yocto = yocto;
        // C4: 워크스페이스 폴더 순회하여 .git 경로 탐색 (먼저 gitDirPaths 채움)
        this.rescanWorkspaceFolders();
        // H6: 잔여 ACL 정리 (gitDirPaths가 채워진 후 호출)
        await this.cleanupResidualACL();
        // C4: onDidChangeWorkspaceFolders 구독
        this.disposables.push(vscode.workspace.onDidChangeWorkspaceFolders((e) => {
            this.handleWorkspaceFoldersChanged(e);
        }));
        // context.subscriptions에 disposables 등록 (deactivate 시 정리)
        for (const d of this.disposables) {
            context.subscriptions.push(d);
        }
    }
    /**
     * GuardGitManager 정리 (deactivate 시)
     * ACL 원복 + watchers 해제 + interval 정리
     */
    async dispose() {
        await this.disable();
        this.stopPeriodicIntegrityCheck();
        this.stopYoctoBackup();
        this._onChangeCallbacks = [];
    }
    // ── C4: 워크스페이스 폴더 재스캔 ──
    rescanWorkspaceFolders() {
        const folders = vscode.workspace.workspaceFolders;
        if (!folders)
            return;
        for (const folder of folders) {
            const gitDir = this.resolveGitDir(folder.uri.fsPath);
            if (gitDir && !this.gitDirPaths.includes(gitDir)) {
                this.gitDirPaths.push(gitDir);
                this.stateMap.set(gitDir, 'inactive');
            }
        }
    }
    // ── H1: Git Worktree 탐지 ──
    /**
     * .git이 실제 디렉토리인지, worktree 참조 파일인지 확인
     *
     * Worktree 환경:
     *   $ cat .git
     *   gitdir: /path/to/main/.git/worktrees/feature-branch
     *
     * 일반 환경:
     *   .git/ — 디렉토리
     */
    resolveGitDir(workspaceRoot) {
        const dotGitPath = path.join(workspaceRoot, '.git');
        try {
            const stat = fs.statSync(dotGitPath);
            if (stat.isDirectory()) {
                return dotGitPath; // 일반 git 저장소
            }
            if (stat.isFile()) {
                // worktree: .git 파일 내용 파싱
                const content = fs.readFileSync(dotGitPath, 'utf-8').trim();
                const match = content.match(/^gitdir:\s*(.+)$/);
                if (match) {
                    const actualGitDir = match[1].trim();
                    // 상대 경로일 경우 workspaceRoot 기준 절대 경로로 변환
                    const resolved = path.isAbsolute(actualGitDir)
                        ? actualGitDir
                        : path.resolve(workspaceRoot, actualGitDir);
                    if (fs.existsSync(resolved) && fs.statSync(resolved).isDirectory()) {
                        console.log(`[Guard.git] Worktree 감지: ${dotGitPath} → ${resolved}`);
                        return resolved;
                    }
                }
            }
        }
        catch {
            // .git 없음
        }
        return null;
    }
    // ── H6: 잔여 ACL 정리 ──
    /**
     * activate() 시 호출: 기존 .git에 남아있는 Guard ACL 제거
     * Extension crash 후 재시작 시 잔여 ACL을 정리하고 정상 활성화
     */
    async cleanupResidualACL() {
        console.log('[Guard.git] 잔여 ACL 정리 시작...');
        for (const gitDir of this.gitDirPaths) {
            try {
                const isProtected = await this.acl.checkProtection(gitDir);
                if (isProtected) {
                    console.log(`[Guard.git] 잔여 ACL 감지: ${gitDir} → 정리`);
                    await this.acl.removeProtection(gitDir);
                }
            }
            catch (err) {
                console.warn(`[Guard.git] 잔여 ACL 정리 실패 (${gitDir}):`, err);
            }
        }
        console.log('[Guard.git] 잔여 ACL 정리 완료');
    }
    // ── Guard 토글 ──
    /**
     * Guard.git 활성화
     * 모든 workspace root에 대해 ACL 적용 + watcher 시작 + 스냅샷 + 주기 진단
     */
    async enable() {
        try {
            // 1. 워크스페이스 재스캔 (새 폴더 반영)
            this.rescanWorkspaceFolders();
            // Bug #2: gitDirPaths가 비어있으면 허위 성공 반환 방지
            if (this.gitDirPaths.length === 0) {
                console.warn('[Guard.git] 워크스페이스에 .git 디렉토리 없음 — enable 실패');
                return { success: false, error: 'No .git directory found in workspace' };
            }
            // 2. 모든 gitDir에 대해 ACL 적용
            let allSuccess = true;
            let lastResult = { success: true };
            for (const gitDir of this.gitDirPaths) {
                // 2a. checkProtection — 이미 적용됐으면 skip
                const alreadyProtected = await this.acl.checkProtection(gitDir);
                if (alreadyProtected) {
                    console.log(`[Guard.git] 이미 보호됨: ${gitDir} — skip`);
                    this.stateMap.set(gitDir, 'active');
                    this.startWatcher(gitDir);
                    continue;
                }
                // 2b. Linux: ConfigService.getGuardLinuxUseChattr() 확인
                if (process.platform === 'linux' && !ConfigService_1.ConfigService.getGuardLinuxUseChattr()) {
                    console.log(`[Guard.git] Linux chattr 비활성화 — Watcher+Yocto only: ${gitDir}`);
                    this.stateMap.set(gitDir, 'active'); // Watcher+Yocto 모드
                    this.startWatcher(gitDir);
                    continue;
                }
                // 2c. ACL 적용
                const result = await this.acl.applyProtection(gitDir);
                if (result.success) {
                    this.stateMap.set(gitDir, 'active');
                    this.startWatcher(gitDir);
                }
                else {
                    console.warn(`[Guard.git] ACL 적용 실패: ${gitDir}`, result.error);
                    this.stateMap.set(gitDir, 'error');
                    allSuccess = false;
                    lastResult = result;
                }
            }
            // 3. Yocto 스냅샷 (guard-enable)
            this.createGitSnapshot('guard-enable').catch(err => console.warn('[Guard.git] Yocto 스냅샷 실패:', err));
            // 4. 주기적 진단 시작 (H5)
            const intervalMin = ConfigService_1.ConfigService.getGuardIntegrityCheckIntervalMin();
            this.startPeriodicIntegrityCheck(intervalMin * 60 * 1000);
            // 5. Yocto 백업 시작
            if (ConfigService_1.ConfigService.getGuardYoctoBackupEnabled()) {
                const backupIntervalMin = ConfigService_1.ConfigService.getGuardYoctoBackupIntervalMin();
                this.startYoctoBackup(backupIntervalMin * 60 * 1000);
            }
            // 6. 상태바 업데이트
            this.statusBar?.setGuardMode(allSuccess ? 'active' : 'warning');
            // 7. onChange 알림
            this.notifyListeners();
            if (allSuccess) {
                return { success: true, command: 'enable()' };
            }
            return lastResult;
        }
        catch (err) {
            // 실패 시에도 TreeView 업데이트
            this.stateMap.forEach((_, key) => this.stateMap.set(key, 'error'));
            this.notifyListeners();
            return { success: false, error: err.message, command: 'enable()' };
        }
    }
    /**
     * Guard.git 비활성화
     * 모든 watcher 중지 + ACL 원복 + 주기 진단 중지
     */
    async disable() {
        let allSuccess = true;
        let lastResult = { success: true };
        // 1. 모든 watcher 중지
        this.stopAllWatchers();
        // 2. 모든 gitDir에 대해 ACL 제거
        for (const gitDir of this.gitDirPaths) {
            const isProtected = await this.acl.checkProtection(gitDir);
            if (!isProtected)
                continue;
            const result = await this.acl.removeProtection(gitDir);
            if (result.success) {
                this.stateMap.set(gitDir, 'inactive');
            }
            else {
                console.warn(`[Guard.git] ACL 해제 실패: ${gitDir}`, result.error);
                this.stateMap.set(gitDir, 'error');
                allSuccess = false;
                lastResult = result;
            }
        }
        // 3. 주기적 진단 중지
        this.stopPeriodicIntegrityCheck();
        this.stopYoctoBackup();
        // 4. 상태바 업데이트
        this.statusBar?.setGuardMode('safe');
        // 5. onChange 알림
        this.notifyListeners();
        if (allSuccess) {
            return { success: true, command: 'disable()' };
        }
        return lastResult;
    }
    /** Guard.git 활성화 여부 (any gitDirPath가 active인지) */
    isEnabled() {
        for (const state of this.stateMap.values()) {
            if (state === 'active' || state === 'warning')
                return true;
        }
        return false;
    }
    /** C4: 경로별 상태 조회 */
    getState(gitDir) {
        return this.stateMap.get(gitDir) ?? 'inactive';
    }
    /** 보호 중인 경로 수 */
    getProtectedPathCount() {
        let count = 0;
        for (const state of this.stateMap.values()) {
            if (state === 'active')
                count++;
        }
        return count;
    }
    // ── 무결성 ──
    /**
     * 모든 .git 경로의 무결성 검사
     * C4: 모든 경로 순회
     */
    async checkIntegrity() {
        const results = [];
        for (const gitDir of this.gitDirPaths) {
            const integrity = await this.checkSingleIntegrity(gitDir);
            results.push(integrity);
        }
        return results;
    }
    async checkSingleIntegrity(gitDir) {
        const base = {
            exists: false,
            protected: false,
            headRef: null,
            objectCount: 0,
            refCount: 0,
        };
        try {
            base.exists = fs.existsSync(gitDir) && fs.statSync(gitDir).isDirectory();
            if (!base.exists)
                return base;
            // HEAD 참조 값
            const headPath = path.join(gitDir, 'HEAD');
            if (fs.existsSync(headPath)) {
                base.headRef = fs.readFileSync(headPath, 'utf-8').trim().substring(0, 100);
            }
            // objects/ 내 파일 수
            const objectsPath = path.join(gitDir, 'objects');
            if (fs.existsSync(objectsPath)) {
                base.objectCount = this.countFilesRecursive(objectsPath);
            }
            // refs/ 내 파일 수
            const refsPath = path.join(gitDir, 'refs');
            if (fs.existsSync(refsPath)) {
                base.refCount = this.countFilesRecursive(refsPath);
            }
            // ACL 보호 상태
            base.protected = await this.acl.checkProtection(gitDir);
        }
        catch (err) {
            console.warn(`[Guard.git] 무결성 검사 실패: ${gitDir}`, err);
        }
        return base;
    }
    countFilesRecursive(dirPath) {
        let count = 0;
        try {
            const entries = fs.readdirSync(dirPath, { withFileTypes: true });
            for (const entry of entries) {
                const fullPath = path.join(dirPath, entry.name);
                if (entry.isDirectory()) {
                    count += this.countFilesRecursive(fullPath);
                }
                else {
                    count++;
                }
            }
        }
        catch {
            // 권한 문제 등 — 무시
        }
        return count;
    }
    // ── 주기적 진단 (H5) ──
    /**
     * H5: 주기적 무결성 진단 시작
     * checkProtection()을 주기적으로 호출하여 ACL bypass 감지
     */
    startPeriodicIntegrityCheck(intervalMs) {
        this.stopPeriodicIntegrityCheck();
        this.selfCheckInterval = setInterval(async () => {
            try {
                const integrities = await this.checkIntegrity();
                for (const integrity of integrities) {
                    if (integrity.exists && !integrity.protected && this.isEnabled()) {
                        console.warn(`[Guard.git] ⚠️ ACL bypass 감지! 재적용 시도...`);
                        // 재적용 시도
                        for (const gitDir of this.gitDirPaths) {
                            await this.acl.applyProtection(gitDir).catch(() => { });
                        }
                        this.statusBar?.setGuardMode('warning');
                        this.notifyListeners();
                        break;
                    }
                }
            }
            catch (err) {
                console.warn('[Guard.git] 주기적 진단 실패:', err);
            }
        }, intervalMs);
    }
    /** 주기적 진단 중지 */
    stopPeriodicIntegrityCheck() {
        if (this.selfCheckInterval) {
            clearInterval(this.selfCheckInterval);
            this.selfCheckInterval = null;
        }
    }
    // ── Yocto 백업 ──
    startYoctoBackup(intervalMs) {
        this.stopYoctoBackup();
        this.yoctoBackupInterval = setInterval(async () => {
            await this.createGitSnapshot('guard-periodic').catch(err => console.warn('[Guard.git] 주기적 Yocto 백업 실패:', err));
        }, intervalMs);
    }
    stopYoctoBackup() {
        if (this.yoctoBackupInterval) {
            clearInterval(this.yoctoBackupInterval);
            this.yoctoBackupInterval = null;
        }
    }
    // ── Yocto 연동 ──
    /**
     * Guard.git 전용 Yocto 스냅샷 생성
     * H3: 내부적으로 yocto.createSnapshot('auto') 호출 + metadata.guardTrigger 기록
     */
    async createGitSnapshot(trigger) {
        if (!this.yocto) {
            console.warn('[Guard.git] YoctoManager 없음 — 스냅샷 생략');
            return;
        }
        try {
            // H3: createSnapshot('auto') 호출
            const snapshot = await this.yocto.createSnapshot('auto');
            // snapshotGitCore 호출 (별도 메서드에서 처리)
            await this.yocto.snapshotGitCore({ guardTrigger: trigger });
            console.log(`[Guard.git] ✅ Yocto 스냅샷 완료 (trigger: ${trigger}, id: ${snapshot.id})`);
        }
        catch (err) {
            console.warn(`[Guard.git] Yocto 스냅샷 실패 (trigger: ${trigger}):`, err);
        }
    }
    // ── FileSystemWatcher (Layer 2) ──
    /**
     * H5: .git 디렉토리 감시 시작
     * R2: 기존 watcher가 있으면 dispose 후 새로 생성
     */
    startWatcher(gitDirPath) {
        // R2: 기존 watcher 정리
        this.stopWatcher(gitDirPath);
        const parentDir = path.dirname(gitDirPath);
        const pattern = new vscode.RelativePattern(parentDir, '.git');
        const watcher = vscode.workspace.createFileSystemWatcher(pattern, false, false, false);
        // H5: onDidDelete — rename 감지를 위해 pending 등록
        watcher.onDidDelete((uri) => {
            if (uri.fsPath === gitDirPath || uri.fsPath.endsWith('.git')) {
                this.pendingDeletions.set(gitDirPath, Date.now());
                setTimeout(() => {
                    if (this.pendingDeletions.has(gitDirPath)) {
                        // timeout 내에 create가 없었음 → 진짜 삭제
                        this.handleGitDeletion(gitDirPath);
                        this.pendingDeletions.delete(gitDirPath);
                    }
                }, 2000); // 2초 내 create 없으면 진짜 삭제
            }
        });
        // H5: onDidCreate — rename 감지 (delete + create 조합)
        watcher.onDidCreate((uri) => {
            if (uri.fsPath === gitDirPath || uri.fsPath.endsWith('.git')) {
                const pendingTime = this.pendingDeletions.get(gitDirPath);
                if (pendingTime && (Date.now() - pendingTime) < 2000) {
                    // 2초 내 delete → create: rename으로 판단
                    console.warn(`[Guard.git] ⚠️ .git 디렉토리 rename 감지! (ACL bypass 가능)`);
                    this.pendingDeletions.delete(gitDirPath);
                    this.stateMap.set(gitDirPath, 'warning');
                    this.statusBar?.setGuardMode('warning');
                    this.notifyListeners();
                    StatusBarManager_1.NotificationThrottle.showWarning('⚠️ .git 폴더가 이름 변경되었습니다! (ACL bypass 가능) Yocto에서 복구하시겠습니까?', '복구하기', '무시').then(choice => {
                        if (choice === '복구하기') {
                            vscode.commands.executeCommand('vibezoo.instantRewind');
                        }
                    });
                }
            }
        });
        this.watchers.set(gitDirPath, watcher);
    }
    /** .git 삭제 처리 */
    handleGitDeletion(gitDirPath) {
        console.error(`[Guard.git] ⚠️ .git 디렉토리 삭제 감지! (${gitDirPath})`);
        this.stateMap.set(gitDirPath, 'warning');
        this.statusBar?.setGuardMode('warning');
        this.notifyListeners();
        // Yocto pre-danger 스냅샷
        this.createGitSnapshot('guard-pre-danger').catch(() => { });
        StatusBarManager_1.NotificationThrottle.showWarning('⚠️ .git 폴더가 삭제되었습니다! Guard.git이 방어를 시도했지만 우회되었을 수 있습니다. Yocto에서 복구하시겠습니까?', '복구하기', '무시').then(choice => {
            if (choice === '복구하기') {
                vscode.commands.executeCommand('vibezoo.instantRewind');
            }
        });
    }
    stopWatcher(gitDirPath) {
        const watcher = this.watchers.get(gitDirPath);
        if (watcher) {
            watcher.dispose();
            this.watchers.delete(gitDirPath);
        }
    }
    stopAllWatchers() {
        for (const [path, watcher] of this.watchers) {
            watcher.dispose();
        }
        this.watchers.clear();
    }
    // ── C4: 워크스페이스 폴더 변경 처리 ──
    handleWorkspaceFoldersChanged(e) {
        // 추가된 폴더
        for (const added of e.added) {
            const gitDir = this.resolveGitDir(added.uri.fsPath);
            if (gitDir && !this.gitDirPaths.includes(gitDir)) {
                this.gitDirPaths.push(gitDir);
                this.stateMap.set(gitDir, 'inactive');
                if (this.isEnabled()) {
                    this.acl.applyProtection(gitDir).then(() => {
                        this.startWatcher(gitDir);
                        this.stateMap.set(gitDir, 'active');
                    }).catch(err => {
                        console.warn(`[Guard.git] 새 워크스페이스 ACL 적용 실패:`, err);
                        this.stateMap.set(gitDir, 'error');
                    });
                }
            }
        }
        // 제거된 폴더
        for (const removed of e.removed) {
            const toRemove = this.gitDirPaths.filter(p => p.startsWith(removed.uri.fsPath));
            for (const p of toRemove) {
                this.acl.removeProtection(p).catch(() => { });
                this.stopWatcher(p);
                this.gitDirPaths = this.gitDirPaths.filter(x => x !== p);
                this.stateMap.delete(p);
            }
        }
        this.notifyListeners();
    }
    // ── 상태바 연동 ──
    bindStatusBar(statusBar) {
        this.statusBar = statusBar;
    }
    // ── 이벤트 (M1: onChange 콜백 해제 가능) ──
    /**
     * M1: 상태 변경 콜백 등록
     * 반환된 함수를 호출하면 콜백이 해제된다.
     */
    onChange(cb) {
        this._onChangeCallbacks.push(cb);
        // M1: 해제 함수 반환
        return () => {
            const idx = this._onChangeCallbacks.indexOf(cb);
            if (idx !== -1) {
                this._onChangeCallbacks.splice(idx, 1);
            }
        };
    }
    notifyListeners() {
        const overall = this.computeOverallState();
        const summary = { overall, paths: new Map(this.stateMap) };
        for (const cb of this._onChangeCallbacks) {
            try {
                cb(summary);
            }
            catch (err) {
                console.warn('[Guard.git] onChange 콜백 오류:', err);
            }
        }
    }
    computeOverallState() {
        let hasActive = false;
        let hasWarning = false;
        let hasError = false;
        for (const state of this.stateMap.values()) {
            if (state === 'active')
                hasActive = true;
            if (state === 'warning')
                hasWarning = true;
            if (state === 'error')
                hasError = true;
        }
        if (hasError)
            return 'error';
        if (hasWarning)
            return 'warning';
        if (hasActive)
            return 'active';
        return 'inactive';
    }
    // ── 휴리스틱: 자동 활성화 판단 ──
    shouldAutoEnable() {
        if (!ConfigService_1.ConfigService.getGuardAutoEnable())
            return false;
        // YOLO 모드가 활성화되어 있으면 자동 활성화
        const yoloEnabled = vscode.workspace.getConfiguration('vibezoo').get('yolo.enabled', true);
        return yoloEnabled;
    }
}
exports.GuardGitManager = GuardGitManager;
//# sourceMappingURL=GuardGitManager.js.map