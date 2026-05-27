// VibeZoo: StatusBar 통합 관리자
// Crow 연결, 모드 제안, Context freshness, YOLO 상태 표시

import * as vscode from 'vscode';

export class StatusBarManager {
  private item: vscode.StatusBarItem;
  private modeSuggestionTimer: NodeJS.Timeout | null = null;

  constructor() {
    this.item = vscode.window.createStatusBarItem(
      vscode.StatusBarAlignment.Right,
      100
    );
    this.item.command = 'vibezoo.verifyFoundation';
  }

  /** VibeZoo 활성 상태 표시 (Bridge 연결 기준) */
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

  /** Crow 연결 상태 (툴팁에만) */
  setCrowStatus(connected: boolean, freshness?: number): void {
    const current = String(this.item.tooltip || 'VibeZoo');
    const base = current.split(' | Crow')[0];
    this.item.tooltip = connected
      ? `${base} | Crow: 연결됨 (${freshness || 100}% fresh)`
      : `${base} | Crow: 연결 안 됨`;
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

  /** 권장 모드 제안 (3초 후 자동 사라짐) */
  suggestMode(mode: string, reason: string): void {
    if (this.modeSuggestionTimer) clearTimeout(this.modeSuggestionTimer);

    this.item.text = `$(gear) 권장: ${mode}`;
    this.item.tooltip = `VibeZoo: ${reason}\n클릭하여 모드 변경`;
    this.item.command = undefined; // 모드 제안일 뿐, Zoo Code 모드를 직접 변경할 수 없음

    this.modeSuggestionTimer = setTimeout(() => {
      this.modeSuggestionTimer = null;
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
