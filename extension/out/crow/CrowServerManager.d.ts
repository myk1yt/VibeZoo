import * as vscode from 'vscode';
export declare class CrowServerManager {
    private config;
    private healthCheckTimer;
    private _onStatusChange;
    readonly onStatusChange: vscode.Event<{
        connected: boolean;
    }>;
    /** 마지막 healthCheck 결과 캐시 (외부에서 재사용 가능) */
    private _lastHealthy;
    /** Bridge 통합 모드에서 직접 healthy 상태 설정 */
    markHealthy(): void;
    constructor();
    /** 마지막 healthCheck 결과 */
    get lastHealthy(): boolean;
    /** Crow 서버 헬스체크 (HTTP GET /health) */
    healthCheck(): Promise<boolean>;
    /** Zoo Code의 Crow 서버 연결 확인 (기존 서버 재시작 없이 감지만) */
    reconnect(maxRetries?: number): Promise<boolean>;
    /** 연결 해제 (구독 정리만) */
    disconnect(): void;
    /** Extension 비활성화 시 정리 */
    onDeactivate(): void;
    private startHealthCheck;
    private stopHealthCheck;
}
//# sourceMappingURL=CrowServerManager.d.ts.map