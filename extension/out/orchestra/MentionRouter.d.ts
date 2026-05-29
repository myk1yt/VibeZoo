import * as vscode from 'vscode';
import { SubagentManager } from './SubagentManager';
export declare class MentionRouter {
    private subagentManager;
    constructor(subagentManager: SubagentManager);
    /** 사용자 입력에서 @mention 패턴 파싱 */
    parse(input: string): {
        agent: string;
        prompt: string;
    } | null;
    /** Chat Participant 등록 (VS Code 공식 Chat API) */
    registerParticipants(context: vscode.ExtensionContext): void;
}
//# sourceMappingURL=MentionRouter.d.ts.map