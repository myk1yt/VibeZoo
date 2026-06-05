export declare class GitStashManager {
    private stashName;
    private workspaceRoot;
    constructor();
    private get cwd();
    /** YOLO 모드 진입 — 현재 상태를 stash에 저장 */
    enterYolo(): Promise<boolean>;
    /** YOLO 모드 퇴장 — 성공 시 커밋, 실패 시 복구 */
    exitYolo(success: boolean): Promise<void>;
    /** Git 저장소인지 확인 */
    isGitRepo(): boolean;
}
//# sourceMappingURL=GitStashManager.d.ts.map