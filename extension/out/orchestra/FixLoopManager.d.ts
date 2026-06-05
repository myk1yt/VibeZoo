/// <reference types="node" />
import { Diagnostic } from '../types';
import { GuardMode } from '../ui/StatusBarManager';
export type FixLoopState = 'idle' | 'pending' | 'in_progress' | 'building' | 'resolved' | 'abandoned' | 'awaiting_user' | 'user_override';
export interface FixAttempt {
    attempt: number;
    exitCode: number;
    diagnostics: Diagnostic[];
    stderr: string;
    fixApplied: string | null;
    timestamp: number;
}
export interface FixSession {
    sessionId: string;
    status: FixLoopState;
    attempt: number;
    maxAttempts: number;
    createdAt: number;
    history: FixAttempt[];
    projectRoot: string;
    taskName: string;
    timeoutId?: NodeJS.Timeout;
}
export interface FixRequestFile {
    sessionId: string;
    status: FixLoopState;
    attempt: number;
    maxAttempts: number;
    createdAt: number;
    history: FixAttempt[];
    projectRoot: string;
    pastFixes?: any[];
}
export interface InstabilityMetrics {
    /** 누적 편집 횟수 (attempt 수) */
    nedits: number;
    /** 자기상관계수: 동일 에러 반복률 [0, 1] */
    autocorr: number;
    /** 연속 빌드 실패 횟수 */
    buildFails: number;
}
/**
 * 불안정성 계산: I = α·nedits + β·autocorr + γ·buildFails
 * α=0.35, β=0.45, γ=0.20
 */
export declare function calculateInstability(m: InstabilityMetrics): number;
/**
 * 불안정성 → GuardMode 변환
 * <0.3=active, <0.7=warning, ≥0.7=safe
 */
export declare function getGuardMode(instability: number): GuardMode;
export declare class FixLoopManager {
    private state;
    private currentSession;
    private fixRequestPath;
    private maxAttempts;
    private readonly SESSION_TIMEOUT_MS;
    private statusBarMessage;
    constructor();
    get stateValue(): FixLoopState;
    get currentSessionValue(): FixSession | null;
    /** BuildFeedback이 빌드 실패 시 호출 */
    onBuildFailure(diagnostics: Diagnostic[], stderr: string, taskName?: string): void;
    /** LLM이 auto_fix_status() 호출 → 상태를 in_progress로 변경 */
    markInProgress(): void;
    /** retry_build() 호출 전 → 상태를 building으로 변경 */
    markBuilding(): void;
    /** 빌드 성공 시 */
    markResolved(): void;
    /** 빌드 실패 시 (LLM이 retry_build()로 실패 보고) */
    markBuildFailed(diagnostics: Diagnostic[], stderr: string): void;
    /**
     * I_instability 계산: 불안정성 연속값 반환
     * 기존 isOscillating() boolean을 대체
     */
    calculateInstability(): number;
    private _oscillationCompat;
    /** Give up 조건 */
    shouldGiveUp(): boolean;
    /** 에러 시그니처 생성 (파일+코드 기준) */
    private errorSignature;
    /** 세션 생성 */
    private createSession;
    /** Fix request JSON 파일 쓰기 */
    private writeFixRequest;
    /** Fix request 파일 정리 */
    private cleanupFixRequest;
    /** StatusBar 업데이트 */
    private updateStatusBar;
    /** 세션 타임아웃 리셋 */
    private resetSessionTimeout;
    /** 세션 타임아웃 제거 */
    private clearSessionTimeout;
    /** 사용자 개입 — 일시정지 */
    pause(): void;
    /** 사용자 개입 — 재개 */
    resume(): Promise<void>;
    /**
     * Context Hydration: freeze 시점과 현재 파일 상태를 비교하여
     * 변경 감지 시 Crow context 레지스터에 저장.
     * resume 시 자동 호출되어 AST Delta 추적.
     */
    private hydrateContext;
    /** 사용자 개입 — 중단 */
    abort(): void;
    private _watcher;
    private _isWatching;
    private _watchDisposables;
    private _buildInProgress;
    /** 파일 저장 감시 시작 — tsc 자동 실행 → 에러 시 auto-fix */
    startWatching(): void;
    /** tsc --noEmit 실행 후 결과 반환 */
    private runAutoBuild;
    /** tsc stderr/stdout → Diagnostic[] 파싱 */
    private parseTscDiagnostics;
    /** 감시 중지 */
    stopWatching(): void;
    /** 감시 상태 확인 */
    isWatching(): boolean;
    /** dispose */
    dispose(): void;
}
//# sourceMappingURL=FixLoopManager.d.ts.map