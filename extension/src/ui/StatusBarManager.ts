// VibeZoo: StatusBar 통합 관리자
// VibeZoo 상태, Crow 연결 상태, YOLO 모드, 권장 모드 제안 표시
//
// ★ 중요: setActive()와 setCrowStatus()가 서로의 tooltip을 덮어쓰지 않도록
//   _baseTooltip(기본 메시지)과 _crowSuffix(Crow 상태)를 분리해서 관리한다.

import * as vscode from 'vscode';

export class StatusBarManager {
  private item: vscode.StatusBarItem;
  private modeSuggestionTimer: NodeJS.Timeout | null = null;
  private savedText: string = '';
  private savedTooltip: string = '';
  private savedCommand: string | vscode.Command | undefined = '';
  private _crowConnected: boolean = false;

  /** setActive()로 설정된 base tooltip (Crow 접미사 제외) */
  private _baseTooltip: string = 'VibeZoo: 활성화됨';

  constructor() {
    this.item = vscode.window.createStatusBarItem(
      vscode.StatusBarAlignment.Right,
      100
    );
    this.item.command = 'vibezoo.verifyFoundation';
  }

  /** 내부: _baseTooltip + Crow 접미사로 tooltip 재구성 */
  private _composeTooltip(): string {
    if (this._crowConnected) {
      return `${this._baseTooltip} | Crow: 연결됨`;
    }
    return `${this._baseTooltip} | Crow: 없음`;
  }

  /** VibeZoo 활성 상태 표시 (VibeZoo 자체는 항상 active) */
  setActive(bridgeConnected: boolean, bridgePort?: number): void {
    if (bridgeConnected) {
      this.item.text = '$(pulse) VibeZoo';
      this._baseTooltip = `VibeZoo Bridge: 연결됨 (:${bridgePort || 9027})`;
      this.item.backgroundColor = undefined;
    } else {
      this.item.text = '$(check) VibeZoo';
      this._baseTooltip = 'VibeZoo: 활성화됨';
      this.item.backgroundColor = undefined;
    }
    // Crow 상태를 보존하여 tooltip 재구성
    this.item.tooltip = this._composeTooltip();
    this.item.show();
  }

  /** Crow 연결 상태 표시 (간결하게) */
  setCrowStatus(connected: boolean): void {
    this._crowConnected = connected;
    this.item.tooltip = this._composeTooltip();
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

    // 직전 상태 저장 (Crow 상태 유지를 위해 _crowConnected도 캡처)
    this.savedText = this.item.text;
    this.savedTooltip = String(this.item.tooltip);
    this.savedCommand = this.item.command;
    const savedCrowConnected = this._crowConnected;

    this.item.text = `$(gear) 권장: ${mode}`;
    this.item.tooltip = `VibeZoo: ${reason}\n클릭하여 모드 변경`;
    this.item.command = undefined;

    this.modeSuggestionTimer = setTimeout(() => {
      this.modeSuggestionTimer = null;
      // 저장된 상태 복구 (Crow 상태는 현재 _crowConnected로 재반영)
      this.item.text = this.savedText || '$(check) VibeZoo';
      // _crowConnected가 true면 tooltip에 Crow 상태를 다시 붙임
      this.item.tooltip = this.savedTooltip || this._composeTooltip();
      this.item.command = this.savedCommand || 'vibezoo.verifyFoundation';
      // 저장 시점과 다른 Crow 상태였다면 tooltip 재구성
      if (this._crowConnected !== savedCrowConnected) {
        this.item.tooltip = this._composeTooltip();
      }
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
