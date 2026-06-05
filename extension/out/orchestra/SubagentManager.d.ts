import * as vscode from 'vscode';
import { SubagentNode } from '../types';
export declare class SubagentManager {
    private child;
    private node;
    private bridgeScript;
    private _onChange;
    readonly onChange: vscode.Event<SubagentNode>;
    constructor(context: vscode.ExtensionContext);
    private getBridgePort;
    /** 개별 에이전트 포트 목록 */
    private getAgentPorts;
    /** Bridge 서버 시작 (Python — FastMCP SSE) — 기존 healthy 브릿지 재사용 or 구버전 종료 후 재시작 */
    spawnBridge(): Promise<number>;
    /** 포트를 사용 중인 구버전 브릿지 프로세스 종료 */
    private killBridgeOnPort;
    /** 포트가 해제될 때까지 대기 */
    private waitForPortFree;
    /** 싱글톤 감지: 이미 실행 중인 브릿지 헬스체크 */
    private checkHealth;
    updateNodeStatus(status: SubagentNode['status'], task?: string): void;
    isRunning(): boolean;
    getPort(): number;
    terminate(): void;
    /** Python 의존성 자동 설치 */
    private installDependencies;
    private waitForReady;
}
//# sourceMappingURL=SubagentManager.d.ts.map