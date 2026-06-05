export interface AutoBuildFixResult {
    status: 'success' | 'failed' | 'abandoned';
    attempt: number;
    error?: string;
}
export interface AutoBuildFixInput {
    errorSignature?: string;
    errorCount?: number;
    consecutiveFailures?: number;
    instability?: number;
}
export declare class AutoBuildFix {
    /**
     * 빌드 실패 자동 수정을 실행합니다.
     *
     * @param input - FixLoopManager로부터 전달된 빌드 실패 컨텍스트
     * @returns AutoBuildFixResult - 수정 결과
     *
     * @note STUB 구현: Phase 2에서 vscode.commands.executeCommand("vibezoo.triggerLlmFix") 연동 예정
     * @note 현재는 LLM이 MCP 도구를 통해 직접 Fix Loop을 제어하므로, 이 모듈은 확장 포인트로 유지
     */
    run(input?: AutoBuildFixInput): Promise<AutoBuildFixResult>;
}
//# sourceMappingURL=AutoBuildFix.d.ts.map