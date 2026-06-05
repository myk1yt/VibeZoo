import * as vscode from 'vscode';
import { YoctoSnapshot } from '../types';
export declare class YoctoManager {
    private snapshotsDir;
    private watcher;
    private trackedFiles;
    private currentSessionId;
    private activeSnapshots;
    private readonly MAX_SNAPSHOTS;
    constructor();
    activate(context: vscode.ExtensionContext): void;
    /** YOLO 진입 시 전체 스냅샷 생성 */
    createSnapshot(trigger: 'manual' | 'auto' | 'yolo-enter' | 'pre-edit'): Promise<YoctoSnapshot>;
    /** 디스크에서 최신 스냅샷 파일 목록을 로드 (인메모리 의존성 제거) */
    private loadSnapshotFromDisk;
    /** ~/.zoo-code/yocto/ 디렉토리에서 세션 폴더 목록 반환 (최신순) */
    listSessions(): string[];
    /** Instant Rewind — 마지막 YOLO 스냅샷의 모든 파일 복구 */
    instantRewind(sessionId?: string): Promise<{
        restoredFiles: number;
        totalFiles: number;
        durationMs: number;
    }>;
    /** 동기식 진본 백업: 저장 직전에 파일 락(레이스 컨디션 방지) */
    private executeDirectBackup;
    /** Base Revision에 파일의 최초 상태 기록 */
    private backupToBaseRevision;
    /** 원자적 파일 복사: 임시 파일 → rename */
    private atomicCopyFile;
    /** 30일 이상 지난 백업 정리 */
    private cleanupOldSnapshots;
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
    snapshotGitCore(metadata: {
        guardTrigger: 'guard-enable' | 'guard-periodic' | 'guard-pre-danger';
    }): Promise<YoctoSnapshot>;
    /** 디렉토리 내 파일 재귀 수집 */
    private collectGitFiles;
    /**
     * Guard 감지: .git 내 파일 목록을 이전 스냅샷과 비교하여 변경 감지
     */
    detectGitChanges(lastSnapshot: YoctoSnapshot): Promise<{
        added: string[];
        removed: string[];
        modified: string[];
    }>;
    dispose(): void;
}
//# sourceMappingURL=YoctoManager.d.ts.map