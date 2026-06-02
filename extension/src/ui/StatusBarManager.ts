// VibeZoo: StatusBar 통합 관리자
// VibeZoo 상태, Crow 연결 상태, YOLO 모드, CIM 모드, 권장 모드 제안 표시
//
// ★ 중요: setActive()와 setCrowStatus()가 서로의 tooltip을 덮어쓰지 않도록
//   _baseTooltip(기본 메시지)과 _crowSuffix(Crow 상태)를 분리해서 관리한다.
// ★ M3-F: CIM 모드 on/off 표시 추가
//
// ★ v0.13.0: NotificationThrottle 통합 — 모든 showInformationMessage /
//   showWarningMessage 호출부에 throttle 적용

import * as vscode from 'vscode';

// ── NotificationThrottle ──────────────────────────────────────

export class NotificationThrottle {
  private static _history: Map<string, { lastShown: number; count: number }> = new Map();
  private static _minuteCount: number[] = [];
  private static readonly SAME_MSG_WINDOW_MS = 3000;   // 동일 메시지 3초 내 중복 → 무시
  private static readonly MAX_PER_MINUTE = 10;           // 분당 최대 10회

  /**
   * 메시지가 throttle 조건을 통과하면 true 반환.
   * @param message 표시할 메시지
   * @param useStatusBarFallapthrottle 초과 시 StatusBar로 대체 표시
   */
  static shouldAllow(message: string): boolean {
    const now = Date.now();
    const key = message.substring(0, 50); // 앞 50자 기준

    // 1. 동일 메시지 3초 내 중복 체크
    const existing = this._history.get(key);
    if (existing && (now - existing.lastShown) < this.SAME_MSG_WINDOW_MS) {
      existing.count++;
      return false;
    }

    // 2. 분당 최대 10회 제한
    this._minuteCount = this._minuteCount.filter(t => now - t < 60000);
    if (this._minuteCount.length >= this.MAX_PER_MINUTE) {
      console.warn(`[NotificationThrottle] 분당 ${this.MAX_PER_MINUTE}회 초과 — 메시지 무시: "${message.substring(0, 50)}..."`);
      return false;
    }

    // 통과 — 기록
    this._history.set(key, { lastShown: now, count: 1 });
    this._minuteCount.push(now);

    // 오래된 기록 정리 (5분)
    if (this._history.size > 100) {
      const cutoff = now - 300000;
      for (const [k, v] of this._history) {
        if (v.lastShown < cutoff) this._history.delete(k);
      }
    }

    return true;
  }

  /** 정보 메시지 표시 (throttle 적용) */
  static showInfo(message: string, ...items: string[]): Thenable<string | undefined> {
    if (!this.shouldAllow(message)) {
      // 초과 시 StatusBar 텍스트로 대체
      vscode.window.setStatusBarMessage(`$(warning) ${message.substring(0, 60)}`, 5000);
      return Promise.resolve(undefined);
    }
    return vscode.window.showInformationMessage(message, ...items);
  }

  /** 경고 메시지 표시 (throttle 적용) */
  static showWarning(message: string, ...items: string[]): Thenable<string | undefined> {
    if (!this.shouldAllow(message)) {
      vscode.window.setStatusBarMessage(`$(error) ${message.substring(0, 60)}`, 5000);
      return Promise.resolve(undefined);
    }
    return vscode.window.showWarningMessage(message, ...items);
  }

  /** 에러 메시지 표시 (throttle 적용) */
  static showError(message: string, ...items: string[]): Thenable<string | undefined> {
    if (!this.shouldAllow(message)) {
      vscode.window.setStatusBarMessage(`$(error) ${message.substring(0, 60)}`, 5000);
      return Promise.resolve(undefined);
    }
    return vscode.window.showErrorMessage(message, ...items);
  }

  /** throttle 상태 리셋 (테스트 및 재시작용) */
  static reset(): void {
    this._history.clear();
    this._minuteCount = [];
  }
}

// ── Guard Mode (I_instability) ───────────────────────────────

export type GuardMode = 'active' | 'warning' | 'safe';

// ── StatusBarManager ─────────────────────────────────────────

export class StatusBarManager {
  private item: vscode.StatusBarItem;
  private modeSuggestionTimer: NodeJS.Timeout | null = null;
  private savedText: string = '';
  private savedTooltip: string = '';
  private savedCommand: string | vscode.Command | undefined = '';
  private _crowConnected: boolean = false;
  private _cimActive: boolean = false;
  private _yoloActive: boolean = false;
  private _guardMode: GuardMode = 'safe';

  /** setActive()로 설정된 base tooltip (Crow 접미사 제외) */
  private _baseTooltip: string = vscode.l10n.t('VibeZoo: Active');

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
      tooltip += vscode.l10n.t(' | Crow: Connected');
    } else {
      tooltip += vscode.l10n.t(' | Crow: Disconnected');
    }
    if (this._cimActive) {
      tooltip += ' | CIM: ON';
    }
    if (this._yoloActive) {
      tooltip += ' | YOLO: ON';
    }
    const guardLabel = this._guardMode === 'active' ? '🛡️ Guard: Active' :
      this._guardMode === 'warning' ? '⚠️ Guard: Warning' : '';
    if (guardLabel) tooltip += ` | ${guardLabel}`;
    return tooltip;
  }

  /** 내부: CIM/YOLO/GUARD 상태를 텍스트에 반영 */
  private _composeText(): string {
    if (this._guardMode === 'active') return '$(zap) VibeZoo Guard';
    if (this._guardMode === 'warning') return '$(warning) VibeZoo';
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
      this._baseTooltip = vscode.l10n.t('VibeZoo Bridge: Connected (:{0})', bridgePort || 9027);
      this.item.backgroundColor = undefined;
    } else {
      this._baseTooltip = vscode.l10n.t('VibeZoo: Active');
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

  /** Guard Mode 설정 (I_instability) */
  setGuardMode(mode: GuardMode): void {
    this._guardMode = mode;
    this.item.text = this._composeText();
    this.item.tooltip = this._composeTooltip();
    // Guard active 시 배경색 변경
    if (mode === 'active') {
      this.item.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
    } else if (mode === 'warning') {
      this.item.backgroundColor = undefined;
    } else {
      this.item.backgroundColor = undefined;
    }
    this.item.show();
  }

  /** 현재 Guard Mode 반환 */
  get guardMode(): GuardMode {
    return this._guardMode;
  }

  /** 권장 모드 제안 (5초 후 자동 복구) */
  suggestMode(mode: string, reason: string): void {
    if (this.modeSuggestionTimer) clearTimeout(this.modeSuggestionTimer);

    this.savedText = this.item.text;
    this.savedTooltip = String(this.item.tooltip);
    this.savedCommand = this.item.command;
    const savedCrowConnected = this._crowConnected;

    this.item.text = vscode.l10n.t('$(gear) Suggested: {0}', mode);
    this.item.tooltip = vscode.l10n.t('VibeZoo: {0}\nClick to change mode', reason);
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
