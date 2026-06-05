import * as vscode from 'vscode';
import { YoctoManager } from './YoctoManager';
export declare class FileGuard {
    private patterns;
    private watcher;
    private yocto;
    /** 최근 복구 시각 Map (파일경로 → timestamp) — 무한루프 방지용 쿨다운 */
    private _recentlyRestored;
    private readonly RESTORE_COOLDOWN_MS;
    /** FileGuard ON/OFF 상태 */
    private _enabled;
    constructor(yocto: YoctoManager);
    activate(context: vscode.ExtensionContext): void;
    /** 파일이 .yoloignore에 의해 보호되는지 확인 */
    isProtected(filePath: string): boolean;
    /** FileGuard ON/OFF 토글 */
    toggle(): boolean;
    /** 현재 FileGuard 활성화 상태 반환 */
    isEnabled(): boolean;
    /** Crow life_avoid 동기화 — 새로운 패턴을 .yoloignore에 추가 */
    syncFromCrow(avoidPatterns: string[]): void;
    /** .yoloignore 파일 로드 */
    private loadPatterns;
    private findLatestBackup;
    dispose(): void;
}
//# sourceMappingURL=FileGuard.d.ts.map