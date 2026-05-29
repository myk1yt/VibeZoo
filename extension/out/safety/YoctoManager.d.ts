import * as vscode from 'vscode';
import { YoctoSnapshot } from '../types';
export declare class YoctoManager {
    private snapshotsDir;
    private watcher;
    private pendingFiles;
    private globalDebounceTimer;
    private readonly DEBOUNCE_MS;
    private currentSessionId;
    private activeSnapshots;
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
    /** 다중 파일 글로벌 백업 스케줄링 (debounce) */
    private scheduleBackup;
    /** 원자적 파일 복사: 임시 파일 → rename */
    private atomicCopyFile;
    /** 보류 중인 모든 파일을 단일 타임스탬프 디렉토리에 원자적으로 백업 */
    private executeGlobalBackup;
    /** 30일 이상 지난 백업 정리 */
    private cleanupOldSnapshots;
    dispose(): void;
}
//# sourceMappingURL=YoctoManager.d.ts.map