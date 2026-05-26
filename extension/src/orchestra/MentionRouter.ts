// VibeZoo Wave 4: Mention Router
// @mention prefix 파싱 및 VS Code Chat Participant 등록

import * as vscode from 'vscode';
import { SubagentManager } from './SubagentManager';

const ROUTE_TABLE: Record<string, { name: string; description: string }> = {
  scout: { name: 'Scout', description: '코드 탐색 및 아키텍처 분석' },
  reviewer: { name: 'Reviewer', description: '코드 리뷰 및 품질 검사' },
  tester: { name: 'Tester', description: '테스트 생성 및 커버리지 분석' },
};

export class MentionRouter {
  private subagentManager: SubagentManager;

  constructor(subagentManager: SubagentManager) {
    this.subagentManager = subagentManager;
  }

  /** 사용자 입력에서 @mention 패턴 파싱 */
  parse(input: string): { agent: string; prompt: string } | null {
    const match = input.match(/^@(\w+)\s+(.*)$/);
    if (!match) return null;
    const [, agent, prompt] = match;
    if (!ROUTE_TABLE[agent]) return null;
    return { agent, prompt };
  }

  /** Chat Participant 등록 (VS Code 공식 Chat API) */
  registerParticipants(context: vscode.ExtensionContext): void {
    // createChatParticipant가 사용 가능한지 런타임 체크
    const chatApi = (vscode as any).chat;
    if (typeof chatApi?.createChatParticipant !== 'function') {
      console.log('[VibeZoo] Chat Participant API 사용 불가 — 레거시 모드');
      return;
    }

    for (const [agent, info] of Object.entries(ROUTE_TABLE)) {
      try {
        const participant = chatApi.createChatParticipant(
          `vibezoo.${agent}`,
          async (request: any, _ctx: any, stream: any, _token: any) => {
            stream.markdown(`> 🔍 Routing to **${info.name}**: ${info.description}...\n\n`);

            try {
              await this.subagentManager.spawnBridge();
              this.subagentManager.updateNodeStatus('running', request.prompt);

              stream.markdown(`${info.name}가 작업을 시작했습니다. 결과는 Crow Memory를 통해 공유됩니다.\n`);

              this.subagentManager.updateNodeStatus('completed');
            } catch (err: any) {
              stream.markdown(`> ⚠️ ${info.name} 오류: ${err.message}\n`);
              this.subagentManager.updateNodeStatus('error');
            }
          }
        );
        context.subscriptions.push(participant);
        console.log(`[VibeZoo] Chat Participant 등록: @${agent}`);
      } catch (err) {
        console.warn(`[VibeZoo] @${agent} Participant 등록 실패:`, err);
      }
    }
  }
}
