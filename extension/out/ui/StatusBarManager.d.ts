export declare class NotificationThrottle {
    private static _history;
    private static _minuteCount;
    private static readonly SAME_MSG_WINDOW_MS;
    private static readonly MAX_PER_MINUTE;
    /**
     * 메시지가 throttle 조건을 통과하면 true 반환.
     * @param message 표시할 메시지
     * @param useStatusBarFallapthrottle 초과 시 StatusBar로 대체 표시
     */
    static shouldAllow(message: string): boolean;
    /** 정보 메시지 표시 (throttle 적용) */
    static showInfo(message: string, ...items: string[]): Thenable<string | undefined>;
    /** 경고 메시지 표시 (throttle 적용) */
    static showWarning(message: string, ...items: string[]): Thenable<string | undefined>;
    /** 에러 메시지 표시 (throttle 적용) */
    static showError(message: string, ...items: string[]): Thenable<string | undefined>;
    /** throttle 상태 리셋 (테스트 및 재시작용) */
    static reset(): void;
}
export type GuardMode = 'active' | 'warning' | 'safe';
export declare class StatusBarManager {
    private item;
    private modeSuggestionTimer;
    private savedText;
    private savedTooltip;
    private savedCommand;
    private _crowConnected;
    private _cimActive;
    private _yoloActive;
    private _guardMode;
    /** setActive()로 설정된 base tooltip (Crow 접미사 제외) */
    private _baseTooltip;
    constructor();
    /** 내부: _baseTooltip + Crow 접미사 + CIM/YOLO 상태로 tooltip 재구성 */
    private _composeTooltip;
    /** 내부: CIM/YOLO/GUARD 상태를 텍스트에 반영 */
    private _composeText;
    /** VibeZoo 활성 상태 표시 */
    setActive(bridgeConnected: boolean, bridgePort?: number, crowConnected?: boolean): void;
    /** Crow 연결 상태 표시 */
    setCrowStatus(connected: boolean): void;
    /** YOLO 모드 상태 표시 */
    setYoloStatus(active: boolean): void;
    /** CIM (Continuous Improvement Mode) 상태 표시 */
    setCimStatus(active: boolean): void;
    /** Guard Mode 설정 (I_instability) */
    setGuardMode(mode: GuardMode): void;
    /** 현재 Guard Mode 반환 */
    get guardMode(): GuardMode;
    /** 권장 모드 제안 (5초 후 자동 복구) */
    suggestMode(mode: string, reason: string): void;
    /** 진행 중인 작업 표시 */
    showProgress(message: string): void;
    dispose(): void;
}
//# sourceMappingURL=StatusBarManager.d.ts.map