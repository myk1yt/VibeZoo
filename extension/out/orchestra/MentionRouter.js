"use strict";
// VibeZoo Wave 4: Mention Router
// @mention prefix 파싱 및 VS Code Chat Participant 등록
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.MentionRouter = void 0;
const vscode = __importStar(require("vscode"));
const ROUTE_TABLE = {
    scout: { name: 'Scout', description: '코드 탐색 및 아키텍처 분석' },
    reviewer: { name: 'Reviewer', description: '코드 리뷰 및 품질 검사' },
    tester: { name: 'Tester', description: '테스트 생성 및 커버리지 분석' },
};
class MentionRouter {
    subagentManager;
    constructor(subagentManager) {
        this.subagentManager = subagentManager;
    }
    /** 사용자 입력에서 @mention 패턴 파싱 */
    parse(input) {
        const match = input.match(/^@(\w+)\s+(.*)$/);
        if (!match)
            return null;
        const [, agent, prompt] = match;
        if (!ROUTE_TABLE[agent])
            return null;
        return { agent, prompt };
    }
    /** Chat Participant 등록 (VS Code 공식 Chat API) */
    registerParticipants(context) {
        // createChatParticipant가 사용 가능한지 런타임 체크
        const chatApi = vscode.chat;
        if (typeof chatApi?.createChatParticipant !== 'function') {
            console.log('[VibeZoo] Chat Participant API 사용 불가 — 레거시 모드');
            return;
        }
        for (const [agent, info] of Object.entries(ROUTE_TABLE)) {
            try {
                const participant = chatApi.createChatParticipant(`vibezoo.${agent}`, async (request, _ctx, stream, _token) => {
                    stream.markdown(`> 🔍 Routing to **${info.name}**: ${info.description}...\n\n`);
                    try {
                        await this.subagentManager.spawnBridge();
                        this.subagentManager.updateNodeStatus('running', request.prompt);
                        stream.markdown(`${info.name}가 작업을 시작했습니다. 결과는 Crow Memory를 통해 공유됩니다.\n`);
                        this.subagentManager.updateNodeStatus('completed');
                    }
                    catch (err) {
                        stream.markdown(`> ⚠️ ${info.name} 오류: ${err.message}\n`);
                        this.subagentManager.updateNodeStatus('error');
                    }
                });
                context.subscriptions.push(participant);
                console.log(`[VibeZoo] Chat Participant 등록: @${agent}`);
            }
            catch (err) {
                console.warn(`[VibeZoo] @${agent} Participant 등록 실패:`, err);
            }
        }
    }
}
exports.MentionRouter = MentionRouter;
//# sourceMappingURL=MentionRouter.js.map