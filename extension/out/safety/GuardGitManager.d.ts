import * as vscode from 'vscode';
import { GuardGitState, GuardGitACLResult, GuardGitIntegrity } from '../types';
import { YoctoManager } from './YoctoManager';
import { StatusBarManager } from '../ui/StatusBarManager';
export declare class GuardGitManager {
    private stateMap;
    private gitDirPaths;
    private acl;
    private watchers;
    private yocto;
    private statusBar;
    private selfCheckInterval;
    private yoctoBackupInterval;
    private disposables;
    private pendingDeletions;
    private _onChangeCallbacks;
    constructor();
    /**
     * GuardGitManager 초기화
     * H6: activate() 시작 시 cleanupResidualACL() 호출
     * Bug #4: yocto가 null이어도 Yocto 기능만 skip하고 ACL/Watcher는 정상 동작
     */
    activate(context: vscode.ExtensionContext, yocto: YoctoManager | null): Promise<void>;
    /**
     * GuardGitManager 정리 (deactivate 시)
     * ACL 원복 + watchers 해제 + interval 정리
     */
    dispose(): Promise<void>;
    private rescanWorkspaceFolders;
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
    private resolveGitDir;
    /**
     * activate() 시 호출: 기존 .git에 남아있는 Guard ACL 제거
     * Extension crash 후 재시작 시 잔여 ACL을 정리하고 정상 활성화
     */
    private cleanupResidualACL;
    /**
     * Guard.git 활성화
     * 모든 workspace root에 대해 ACL 적용 + watcher 시작 + 스냅샷 + 주기 진단
     */
    enable(): Promise<GuardGitACLResult>;
    /**
     * Guard.git 비활성화
     * 모든 watcher 중지 + ACL 원복 + 주기 진단 중지
     */
    disable(): Promise<GuardGitACLResult>;
    /** Guard.git 활성화 여부 (any gitDirPath가 active인지) */
    isEnabled(): boolean;
    /** C4: 경로별 상태 조회 */
    getState(gitDir: string): GuardGitState;
    /** 보호 중인 경로 수 */
    getProtectedPathCount(): number;
    /**
     * 모든 .git 경로의 무결성 검사
     * C4: 모든 경로 순회
     */
    checkIntegrity(): Promise<GuardGitIntegrity[]>;
    private checkSingleIntegrity;
    private countFilesRecursive;
    /**
     * H5: 주기적 무결성 진단 시작
     * checkProtection()을 주기적으로 호출하여 ACL bypass 감지
     */
    startPeriodicIntegrityCheck(intervalMs: number): void;
    /** 주기적 진단 중지 */
    stopPeriodicIntegrityCheck(): void;
    private startYoctoBackup;
    private stopYoctoBackup;
    /**
     * Guard.git 전용 Yocto 스냅샷 생성
     * H3: 내부적으로 yocto.createSnapshot('auto') 호출 + metadata.guardTrigger 기록
     */
    createGitSnapshot(trigger: 'guard-enable' | 'guard-periodic' | 'guard-pre-danger'): Promise<void>;
    /**
     * H5: .git 디렉토리 감시 시작
     * R2: 기존 watcher가 있으면 dispose 후 새로 생성
     */
    private startWatcher;
    /** .git 삭제 처리 */
    private handleGitDeletion;
    private stopWatcher;
    private stopAllWatchers;
    private handleWorkspaceFoldersChanged;
    bindStatusBar(statusBar: StatusBarManager): void;
    /**
     * M1: 상태 변경 콜백 등록
     * 반환된 함수를 호출하면 콜백이 해제된다.
     */
    onChange(cb: (summary: {
        overall: GuardGitState;
        paths: Map<string, GuardGitState>;
    }) => void): () => void;
    private notifyListeners;
    private computeOverallState;
    shouldAutoEnable(): boolean;
}
//# sourceMappingURL=GuardGitManager.d.ts.map