// VibeZoo: Tree View Providers
// YOLO History와 Active Subagents 트리 뷰 제공

import * as vscode from 'vscode';
import { SubagentNode } from '../types';

// ── Active Subagents Tree ────────────────────────────────────

export class ActiveSubagentsProvider implements vscode.TreeDataProvider<SubagentTreeItem> {
  private _onDidChangeTreeData = new vscode.EventEmitter<SubagentTreeItem | undefined>();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

  private nodes: Map<string, SubagentNode> = new Map();

  refresh(node?: SubagentNode): void {
    if (node) {
      const item = this.nodes.get(node.id);
      if (item) {
        this.nodes.set(node.id, node);
      }
    }
    this._onDidChangeTreeData.fire(undefined);
  }

  updateNode(node: SubagentNode): void {
    this.nodes.set(node.id, node);
    this._onDidChangeTreeData.fire(undefined);
  }

  removeNode(id: string): void {
    this.nodes.delete(id);
    this._onDidChangeTreeData.fire(undefined);
  }

  getTreeItem(element: SubagentTreeItem): vscode.TreeItem {
    return element;
  }

  getChildren(_element?: SubagentTreeItem): Thenable<SubagentTreeItem[]> {
    const nodes = Array.from(this.nodes.values());
    if (nodes.length === 0) {
      const placeholder = new vscode.TreeItem('브릿지 연결 시 자동 표시됩니다', vscode.TreeItemCollapsibleState.None);
      placeholder.description = '현재 대기 중';
      placeholder.iconPath = undefined;
      placeholder.label = '$(sync~spin) VibeZoo 대기 중...';
      placeholder.tooltip = 'VibeZoo MCP Bridge가 연결되면 Scout·Reviewer·Tester가 여기에 표시됩니다.';
      return Promise.resolve([placeholder as any]);
    }
    const items = nodes.map((node) => new SubagentTreeItem(node));
    return Promise.resolve(items);
  }
}

class SubagentTreeItem extends vscode.TreeItem {
  constructor(node: SubagentNode) {
    super(node.name, vscode.TreeItemCollapsibleState.None);

    this.id = node.id;
    this.description = node.currentTask || node.status;

    const iconMap: Record<string, string> = {
      idle: '$(debug-pause)',
      running: '$(sync~spin)',
      completed: '$(check)',
      error: '$(error)',
    };
    this.iconPath = undefined;
    this.label = `${iconMap[node.status] || '$(question)'} ${node.name}`;

    this.tooltip = new vscode.MarkdownString(
      `**${node.name}**\n\nStatus: ${node.status}${
        node.currentTask ? `\nTask: ${node.currentTask}` : ''
      }${node.progress !== undefined ? `\nProgress: ${node.progress}%` : ''}${
        node.elapsedMs ? `\nElapsed: ${(node.elapsedMs / 1000).toFixed(1)}s` : ''
      }`
    );

    this.contextValue = node.status;
  }
}

// ── YOLO History Tree ───────────────────────────────────────

export class YoloHistoryProvider implements vscode.TreeDataProvider<YoloHistoryItem> {
  private _onDidChangeTreeData = new vscode.EventEmitter<YoloHistoryItem | undefined>();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

  private snapshots: string[] = [];

  refresh(): void {
    this._onDidChangeTreeData.fire(undefined);
  }

  addSnapshot(name: string): void {
    this.snapshots.unshift(name);
    if (this.snapshots.length > 50) this.snapshots.pop();
    this._onDidChangeTreeData.fire(undefined);
  }

  getTreeItem(element: YoloHistoryItem): vscode.TreeItem {
    return element;
  }

  getChildren(_element?: YoloHistoryItem): Thenable<YoloHistoryItem[]> {
    if (this.snapshots.length === 0) {
      const placeholder = new vscode.TreeItem('아직 YOLO 세션 기록이 없습니다', vscode.TreeItemCollapsibleState.None);
      placeholder.description = 'YOLO 모드로 작업 시 자동 기록됩니다';
      placeholder.iconPath = undefined;
      placeholder.label = '$(history) YOLO 기록 없음';
      placeholder.tooltip = 'YOLO(Yocto OnLine Offline) 모드로 YOCTO 스냅샷을 생성하면 여기에 기록이 표시됩니다.';
      return Promise.resolve([placeholder as any]);
    }
    return Promise.resolve(
      this.snapshots.map((s) => new YoloHistoryItem(s))
    );
  }
}

class YoloHistoryItem extends vscode.TreeItem {
  constructor(name: string) {
    super(name, vscode.TreeItemCollapsibleState.None);
    this.id = name;
    this.description = 'YOLO snapshot';
    this.iconPath = undefined;
    this.label = `$(history) ${name}`;
    this.contextValue = 'yoloSnapshot';
  }
}
