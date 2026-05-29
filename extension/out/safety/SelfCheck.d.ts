import { SelfCheckReport, SelfCheckItem } from '../types';
export declare class AlarmMonitor {
    private alarmLog;
    private readonly WINDOW_MS;
    private readonly MAX_ALARMS;
    private _throttled;
    private _throttleUntil;
    /** 알람 등록. true 반환 = 제한 초과로 무시됨 */
    record(message: string): boolean;
    get throttled(): boolean;
    get recentAlarmCount(): number;
    reset(): void;
}
export declare const alarmMonitor: AlarmMonitor;
export declare class SelfChecker {
    private version;
    constructor(version?: string);
    /** 모든 진단 실행 */
    runAll(): Promise<SelfCheckReport>;
    /** Bridge :9027/health 확인 */
    checkBridgeConnectivity(): Promise<SelfCheckItem>;
    /** Crow :9020/health 확인 */
    checkCrowHealth(): Promise<SelfCheckItem>;
    /** .roo/mcp.json 무결성 확인 */
    checkMcpConfig(): Promise<SelfCheckItem>;
    /** 화이트보드 JSON 파일 무결성 */
    checkWhiteboardFiles(): Promise<SelfCheckItem>;
    /** 백업 디렉토리 권한/공간 확인 */
    checkYoctoDirectory(): Promise<SelfCheckItem>;
    /** Zoo Code 확장 호환성 확인 */
    checkZooCodeCompatibility(): Promise<SelfCheckItem>;
    /** 알람 카운터 헬스 체크 */
    checkNotificationHealth(): Promise<SelfCheckItem>;
    /** 감지된 문제 자동 복구 시도 */
    autoRecover(failure: SelfCheckItem): Promise<boolean>;
    /** MCP 설정 자동 복구 */
    private autoConfigureMCP;
    /** 자가진단 결과를 마크다운으로 포맷팅 */
    formatReport(report: SelfCheckReport): string;
}
//# sourceMappingURL=SelfCheck.d.ts.map