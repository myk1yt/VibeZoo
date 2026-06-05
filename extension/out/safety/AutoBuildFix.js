"use strict";
// VibeZoo — AutoBuildFix (stub → Phase 2)
//
// 현재: LLM이 MCP 도구(auto_fix_status, retry_build)를 통해 직접 Fix Loop을 수행.
// 향후: FixLoopManager가 실패를 감지하면 AutoBuildFix가 내부적으로
//       vscode.commands.executeCommand("vibezoo.triggerLlmFix")를 호출하여
//       LLM 세션을 프로그래밍적으로 개시하는 브릿지 역할.
//
// 상태: STUB — interface만 정의되어 있으며, 실제 구현은 Phase 2에서 진행.
Object.defineProperty(exports, "__esModule", { value: true });
exports.AutoBuildFix = void 0;
class AutoBuildFix {
    /**
     * 빌드 실패 자동 수정을 실행합니다.
     *
     * @param input - FixLoopManager로부터 전달된 빌드 실패 컨텍스트
     * @returns AutoBuildFixResult - 수정 결과
     *
     * @note STUB 구현: Phase 2에서 vscode.commands.executeCommand("vibezoo.triggerLlmFix") 연동 예정
     * @note 현재는 LLM이 MCP 도구를 통해 직접 Fix Loop을 제어하므로, 이 모듈은 확장 포인트로 유지
     */
    async run(input) {
        // stub: 실제 구현은 다음 Phase에서
        // 향후 FixLoopManager.calculateInstability() 결과를 받아
        // 자율적으로 LLM 세션을 트리거하는 로직으로 대체
        const reason = input?.instability !== undefined && input.instability > 0.7
            ? 'abandoned (instability too high)'
            : 'stub — bypassed (LLM-driven MCP tools handle the fix loop)';
        console.debug(`[AutoBuildFix] ${reason}`);
        return {
            status: 'success',
            attempt: 0,
            error: reason,
        };
    }
}
exports.AutoBuildFix = AutoBuildFix;
//# sourceMappingURL=AutoBuildFix.js.map