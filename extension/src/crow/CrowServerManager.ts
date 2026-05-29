// VibeZoo: Crow Memory 연결 감지 관리자
// VibeZoo는 Crow 서버를 직접 실행하지 않는다.
// Crow는 Zoo Code가 관리하는 외부 독립 시스템이다.
// VibeZoo는 Zoo Code의 Crow 서버 연결 상태를 감지만 한다.

import * as vscode from 'vscode';
import { CrowServerConfig } from '../types';

export class CrowServerManager {
  private config: CrowServerConfig;
  private healthCheckTimer: NodeJS.Timeout | null = null;
  private _onStatusChange = new vscode.EventEmitter<{
    connected: boolean;
  }>();
  readonly onStatusChange = this._onStatusChange.event;
  /** 마지막 healthCheck 결과 캐시 (외부에서 재사용 가능) */
  private _lastHealthy: boolean = false;

  /** Bridge 통합 모드에서 직접 healthy 상태 설정 */
  markHealthy(): void {
    this._lastHealthy = true;
    this._onStatusChange.fire({ connected: true });
    this.startHealthCheck();
  }

  constructor() {
    this.config = {
      port: vscode.workspace.getConfiguration('vibezoo').get('crow.port', 9020),
      healthCheckIntervalMs: 30000,
    };
  }

  /** 마지막 healthCheck 결과 */
  get lastHealthy(): boolean {
    return this._lastHealthy;
  }

  /** Crow 서버 헬스체크 (HTTP GET /health)
   *  ★ 127.0.0.1 사용 (localhost는 IPv6로 resolve될 수 있음) */
  async healthCheck(): Promise<boolean> {
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 3000);
      const url = `http://127.0.0.1:${this.config.port}/health`;
      const response = await fetch(url, {
        signal: controller.signal,
      });
      clearTimeout(timeout);
      const ok = response.ok;
      console.log(`[VibeZoo] Crow healthCheck → ${url} → ${ok ? '✅ 성공' : '❌ 실패'} (status=${response.status})`);
      return ok;
    } catch (err: any) {
      console.log(`[VibeZoo] Crow healthCheck → http://127.0.0.1:${this.config.port}/health → 💥 예외: ${err.message}`);
      return false;
    }
  }

  /** Zoo Code의 Crow 서버 연결 확인 (기존 서버 재시작 없이 감지만) */
  async reconnect(maxRetries: number = 3): Promise<boolean> {
    for (let attempt = 0; attempt < maxRetries; attempt++) {
      this._onStatusChange.fire({ connected: false });

      const healthy = await this.healthCheck();
      if (healthy) {
        this._lastHealthy = true;
        console.log(`[VibeZoo] ✅ Zoo Code Crow 서버 연결 확인: 포트 ${this.config.port}`);
        this.startHealthCheck();
        this._onStatusChange.fire({ connected: true });
        return true;
      }

      console.log(`[VibeZoo] ⏳ Zoo Code Crow 서버 응답 없음 (${attempt + 1}/${maxRetries}). 5초 후 재시도…`);
      if (attempt < maxRetries - 1) {
        await new Promise((r) => setTimeout(r, 5000));
      }
    }

    this._lastHealthy = false;
    console.warn(`[VibeZoo] ❌ Zoo Code Crow 서버 연결 최종 실패 (${maxRetries}회 시도).`);
    this._onStatusChange.fire({ connected: false });
    return false;
  }

  /** 연결 해제 (구독 정리만) */
  disconnect(): void {
    this.stopHealthCheck();
    this._lastHealthy = false;
    this._onStatusChange.fire({ connected: false });
    console.log('[VibeZoo] Crow 연결 해제됨 (Zoo Code 서버는 계속 실행 중)');
  }

  /** Extension 비활성화 시 정리 */
  onDeactivate(): void {
    this.stopHealthCheck();
  }

  private startHealthCheck(): void {
    this.stopHealthCheck();
    this.healthCheckTimer = setInterval(async () => {
      const healthy = await this.healthCheck();
      this._lastHealthy = healthy;
      if (!healthy) {
        this._onStatusChange.fire({ connected: false });
      }
    }, this.config.healthCheckIntervalMs);
  }

  private stopHealthCheck(): void {
    if (this.healthCheckTimer) {
      clearInterval(this.healthCheckTimer);
      this.healthCheckTimer = null;
    }
  }
}
