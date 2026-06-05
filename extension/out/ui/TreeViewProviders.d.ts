import * as vscode from 'vscode';
import { SubagentNode, SessionSummary, GuardGitState } from '../types';
export declare class ActiveSubagentsProvider implements vscode.TreeDataProvider<SubagentTreeItem> {
    private _onDidChangeTreeData;
    readonly onDidChangeTreeData: vscode.Event<SubagentTreeItem | undefined>;
    private nodes;
    private _bridgePort;
    private _bridgeOk;
    private _crowOk;
    private _healthCheckInterval;
    refresh(node?: SubagentNode): void;
    updateNode(node: SubagentNode): void;
    removeNode(id: string): void;
    /** Bridge health를 주기적으로 확인 (30초 간격) */
    startHealthCheck(): void;
    /** SubagentPool의 작업 목록을 30초 간격 polling하여 TreeView에 표시 */
    private pollSubagentTasks;
    stopHealthCheck(): void;
    /** MCP 브릿지 시작 시 개별 에이전트 노드들을 초기화 + Bridge 상태 노드 추가 */
    initializeAgentNodes(bridgePort: number): void;
    /** Guard.git 상태 업데이트 */
    setGuardGitStatus(state: GuardGitState): void;
    /** CIM 감시 상태 업데이트 */
    setCimStatus(watching: boolean): void;
    getTreeItem(element: SubagentTreeItem): vscode.TreeItem;
    getChildren(_element?: SubagentTreeItem): Thenable<SubagentTreeItem[]>;
    dispose(): void;
}
declare class SubagentTreeItem extends vscode.TreeItem {
    node: SubagentNode;
    constructor(node: SubagentNode, bridgeOk?: boolean, crowOk?: boolean);
}
export declare class YoloHistoryProvider implements vscode.TreeDataProvider<YoloHistoryItem> {
    private _onDidChangeTreeData;
    readonly onDidChangeTreeData: vscode.Event<YoloHistoryItem | undefined>;
    private snapshots;
    refresh(): void;
    addSnapshot(name: string): void;
    /** ~/.zoo-code/yocto/ 디렉토리에서 실제 세션 폴더 목록을 읽어온다 */
    private loadFromDisk;
    getTreeItem(element: YoloHistoryItem): vscode.TreeItem;
    getChildren(_element?: YoloHistoryItem): Thenable<YoloHistoryItem[]>;
}
declare class YoloHistoryItem extends vscode.TreeItem {
    constructor(name: string);
    private formatDescription;
}
export declare class SessionResumeProvider implements vscode.TreeDataProvider<SessionResumeItem> {
    private _onDidChangeTreeData;
    readonly onDidChangeTreeData: vscode.Event<SessionResumeItem | undefined>;
    private sessions;
    private refreshFn;
    /** SessionResume.refresh()를 외부에서 주입 */
    setRefreshFn(fn: () => Promise<SessionSummary[]>): void;
    refresh(): Promise<void>;
    getTreeItem(element: SessionResumeItem): vscode.TreeItem;
    getChildren(element?: SessionResumeItem): Thenable<SessionResumeItem[]>;
}
declare class SessionResumeItem extends vscode.TreeItem {
    session: SessionSummary;
    children: SessionResumeItem[];
    constructor(session: SessionSummary, type?: string, labelOverride?: string, collapsibleState?: vscode.TreeItemCollapsibleState);
}
export {};
//# sourceMappingURL=TreeViewProviders.d.ts.map