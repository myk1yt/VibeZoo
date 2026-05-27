// VibeZoo: StatusBar 통합 관리자
// VibeZoo 상태, Crow 연결 상태, YOLO 모드, CIM 모드, 권장 모드 제안 표시
//
// ★ 중요: setActive()와 setCrowStatus()가 서로의 tooltip을 덮어쓰지 않도록
//   _baseTooltip(기본 메시지)과 _crowSuffix(Crow 상태)를 분리해서 관리한다.
// ★ M3-F: CIM 모드 on/off 표시 추가

import * as vscode from 'vscode';

export class StatusBarManager {
  private item: vscode.StatusBarItem;
  private modeSuggestionTimer: NodeJS.Timeout | null = null;
  private savedText: string = '';
  private savedTooltip: string = '';
  private savedCommand: string | vscode.Command | undefined = '';
  private _crowConnected: boolean = false;
  private _cimActive: boolean = false;
  private _yoloActive: boolean = false;

  /** setActive()로 설정된 base tooltip (Crow 접미사 제외) */
  private _baseTooltip: string = 'VibeZoo: 활성화됨';

  constructor() {
    this.item = vscode.window.createStatusBarItem(
      vscode.StatusBarAlignment.Right,
      100
    );
    this.item.command = 'vibezoo.verifyFoundation';
  }

  /** 내부: _baseTooltip + Crow 접미사 + CIM/YOLO 상태로 tooltip 재구성 */
  private _composeTooltip(): string {
    let tooltip = this._baseTooltip;
    if (this._crowConnected) {
      tooltip += ' | Crow: 연결됨';
    } else {
      tooltip += ' | Crow: 없음';
    }
    if (this._cimActive) {
      tooltip += ' | CIM: ON';
    }
    if (this._yoloActive) {
      tooltip += ' | YOLO: ON';
    }
    return tooltip;
  }

  /** 내부: CIM/YOLO 상태를 텍스트에 반영 */
  private _composeText(): string {
    let text = '$(zap) VibeZoo';
    if (this._cimActive) {
      text = '$(eye) VibeZoo';
    }
    if (this._yoloActive) {
      text = '$(flame) VibeZoo YOLO';
    }
    return text;
  }

  /** VibeZoo 활성 상태 표시 */
  setActive(bridgeConnected: boolean, bridgePort?: number, crowConnected?: boolean): void {
    if (crowConnected !== undefined) {
      this._crowConnected = crowConnected;
    }
    if (bridgeConnected) {
      this._baseTooltip = `VibeZoo Bridge: 연결됨 (:${bridgePort || 9027})`;
      this.item.backgroundColor = undefined;
    } else {
      this._baseTooltip = 'VibeZoo: 활성화됨';
      this.item.backgroundColor = undefined;
    }
    this.item.text = this._composeText();
    this.item.tooltip = this._composeTooltip();
    this.item.show();
  }

  /** Crow 연결 상태 표시 */
  setCrowStatus(connected: boolean): void {
    this._crowConnected = connected;
    this.item.tooltip = this._composeTooltip();
    this.item.show();
  }

  /** YOLO 모드 상태 표시 */
  setYoloStatus(active: boolean): void {
    this._yoloActive = active;
    this.item.text = this._composeText();
    this.item.tooltip = this._composeTooltip();
    if (active) {
      this.item.backgroundColor = new vscode.ThemeColor('statusBarItem.errorBackground');
    } else {
      this.item.backgroundColor = undefined;
    }
    this.item.show();
  }

  /** CIM (Continuous Improvement Mode) 상태 표시 */
  setCimStatus(active: boolean): void {
    this._cimActive = active;
    this.item.text = this._composeText();
    this.item.tooltip = this._composeTooltip();
    if (active) {
      // CIM 활성화 시 반짝이는 효과
      this.item.text = '$(eye) VibeZoo CIM';
    }
    this.item.show();
  }

  /** 권장 모드 제안 (5초 후 자동 복구) */
  suggestMode(mode: string, reason: string): void {
    if (this.modeSuggestionTimer) clearTimeout(this.modeSuggestionTimer);

    this.savedText = this.item.text;
    this.savedTooltip = String(this.item.tooltip);
    this.savedCommand = this.item.command;
    const savedCrowConnected = this._crowConnected;

    this.item.text = `$(gear) 권장: ${mode}`;
    this.item.tooltip = `VibeZoo: ${reason}\n클릭하여 모드 변경`;
    this.item.command = undefined;

    this.modeSuggestionTimer = setTimeout(() => {
      this.modeSuggestionTimer = null;
      this.item.text = this.savedText || this._composeText();
      this.item.tooltip = this.savedTooltip || this._composeTooltip();
      this.item.command = this.savedCommand || 'vibezoo.verifyFoundation';
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
