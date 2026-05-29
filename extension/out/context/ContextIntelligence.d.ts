import { SessionSummary } from '../types';
export declare class ContextIndicator {
    /** Crow Context 복합 지표 계산 및 StatusBar 표시 */
    getFreshnessStatus(): Promise<{
        percentage: number;
        icon: string;
    }>;
    private tryStatCrowBin;
}
export declare class ExplainLessSuggestor {
    private recentMessages;
    private readonly MAX_HISTORY;
    /** 사용자 입력에서 반복 설명 패턴 감지 */
    analyze(message: string): string | null;
}
/**
 * SessionResume — WebviewPanel 대신 TreeView 데이터 제공을 위한 클래스
 * Crow Memory 또는 로컬 파일에서 이전 세션 요약 정보를 가져온다.
 */
export declare class SessionResume {
    private sessions;
    /** 세션 요약을 불러온다 (Crow recall 또는 로컬 파일에서) */
    refresh(): Promise<SessionSummary[]>;
    getSessions(): SessionSummary[];
    private toSessionSummary;
    private parseTimestampFromName;
    dispose(): void;
}
export declare class EmotionalDetector {
    private rejectionPatterns;
    private consecutiveRejections;
    /** 사용자 메시지의 감정 신호 분석 */
    analyze(message: string): {
        tone: 'neutral' | 'frustrated' | 'satisfied' | 'urgent';
        rejectionStreak: number;
    };
    private isPositive;
}
//# sourceMappingURL=ContextIntelligence.d.ts.map