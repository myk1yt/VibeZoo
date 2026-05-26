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

  /** Crow 연결 상태 업데이트 */
  setCrowStatus(connected: boolean, freshness?: number): void {
    if (connected) {
      const fresh = freshness ?? 100;
      const icon = fresh > 70 ? '$(pulse)' : fresh > 30 ? '$(warning)' : '$(error)';
      this.item.text = `${icon} VibeZoo`;
      this.item.tooltip = `Crow Memory: 연결됨 | Context: ${fresh}% fresh`;
      this.item.backgroundColor = undefined;
    } else {
      this.item.text = '$(circle-slash) VibeZoo';
      this.item.tooltip = 'Crow Memory: 연결 끊김';
      this.item.backgroundColor = new vscode.ThemeColor(
        'statusBarItem.warningBackground'
      );
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
