// VibeZoo: StatusBar 통합 관리자
// VibeZoo 상태, Crow 연결 상태, YOLO 모드, 권장 모드 제안 표시

import * as vscode from 'vscode';

export class StatusBarManager {
  private item: vscode.StatusBarItem;
  private modeSuggestionTimer: NodeJS.Timeout | null = null;
  private savedText: string = '';
  private savedTooltip: string = '';
  private savedCommand: string | vscode.Command | undefined = '';
  private _crowConnected: boolean = false;

  constructor() {
    this.item = vscode.window.createStatusBarItem(
      vscode.StatusBarAlignment.Right,
      100
    );
    this.item.command = 'vibezoo.verifyFoundation';
  }

  /** VibeZoo 활성 상태 표시 (VibeZoo 자체는 항상 active) */
  setActive(bridgeConnected: boolean, bridgePort?: number): void {
    if (bridgeConnected) {
      this.item.text = '$(pulse) VibeZoo';
      this.item.tooltip = `VibeZoo Bridge: 연결됨 (:${bridgePort || 9027})`;
      this.item.backgroundColor = undefined;
    } else {
      this.item.text = '$(check) VibeZoo';
      this.item.tooltip = 'VibeZoo: 활성화됨';
      this.item.backgroundColor = undefined;
    }
    this.item.show();
  }

  /** Crow 연결 상태 표시 (간결하게) */
  setCrowStatus(connected: boolean): void {
    this._crowConnected = connected;
    const current = String(this.item.tooltip || 'VibeZoo');
    const base = current.split(' | Crow')[0];
    if (connected) {
      this.item.tooltip = `${base} | Crow: 연결됨`;
    } else {
      this.item.tooltip = `${base} | Crow: 없음`;
    }
    this.item.show();
  }

  /** YOLO 모드 상태 표시 */
  setYoloStatus(active: boolean): void {
    if (active) {
      this.item.text = '$(flame) VibeZoo YOLO';
      this.item.backgroundColor = new vscode.ThemeColor(
        'statusBarItem.errorBackground'
      );
      this.item.tooltip = 'YOLO 모드 활성화 — 모든 파일 변경이 자동 백업됩니다.';
    }
  }

  /** 권장 모드 제안 (5초 후 자동 복구) */
  suggestMode(mode: string, reason: string): void {
    if (this.modeSuggestionTimer) clearTimeout(this.modeSuggestionTimer);

    // 직전 상태 저장
    this.savedText = this.item.text;
    this.savedTooltip = String(this.item.tooltip);
    this.savedCommand = this.item.command;

    this.item.text = `$(gear) 권장: ${mode}`;
    this.item.tooltip = `VibeZoo: ${reason}\n클릭하여 모드 변경`;
    this.item.command = undefined;

    this.modeSuggestionTimer = setTimeout(() => {
      this.modeSuggestionTimer = null;
      // 저장된 상태 복구
      this.item.text = this.savedText || '$(check) VibeZoo';
      this.item.tooltip = this.savedTooltip || 'VibeZoo: 활성화됨';
      this.item.command = this.savedCommand || 'vibezoo.verifyFoundation';
    }, 5000);
  }

  /** 진행 중인 작업 표시 */
  showProgress(message: string): void {
    this.item.text = `$(sync~spin) ${message}`;
  }

  dispose(): void {
    if (this.modeSuggestionTimer) clearTimeout(this.modeSuggestionTimer);
    this.item.dispose();
  }
}
