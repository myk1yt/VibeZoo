// VibeZoo: Crow Memory 연결 감지 및 자동 시작 관리자
// Bridge(port 9027)와 동일한 패턴으로 Crow Memory 서버(port 9020)를 자동 spawn한다.

import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { spawn, ChildProcess } from 'child_process';
import { CrowServerConfig } from '../types';
import { ConfigService } from '../config/ConfigService';
import { PythonResolver } from '../python/PythonResolver';

export class CrowServerManager {
  private config: CrowServerConfig;
  private healthCheckTimer: NodeJS.Timeout | null = null;
  private _onStatusChange = new vscode.EventEmitter<{
    connected: boolean;
  }>();
  readonly onStatusChange = this._onStatusChange.event;
  /** 마지막 healthCheck 결과 캐시 (외부에서 재사용 가능) */
  private _lastHealthy: boolean = false;
  /** spawn한 child process (중복 실행 방지) */
  private child: ChildProcess | null = null;

  /** Bridge 통합 모드에서 직접 healthy 상태 설정 */
  markHealthy(): void {
    this._lastHealthy = true;
    this._onStatusChange.fire({ connected: true });
    this.startHealthCheck();
  }

  constructor(private extensionPath?: string) {
    this.config = {
      port: vscode.workspace.getConfiguration('vibezoo').get('crow.port', 9020),
      healthCheckIntervalMs: 30000,
    };
  }

  /** 마지막 healthCheck 결과 */
  get lastHealthy(): boolean {
    return this._lastHealthy;
  }

  /** Crow 서버 헬스체크 (HTTP GET /health) */
  async healthCheck(): Promise<boolean> {
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 3000);
      const url = ConfigService.getCrowUrl('/health');
      const response = await fetch(url, {
        signal: controller.signal,
      });
      clearTimeout(timeout);
      const ok = response.ok;
      console.log(`[VibeZoo] Crow healthCheck → ${url} → ${ok ? '✅ 성공' : '❌ 실패'} (status=${response.status})`);
      return ok;
    } catch (err: any) {
      console.log(`[VibeZoo] Crow healthCheck → ${ConfigService.getCrowUrl('/health')} → 💥 예외: ${err.message}`);
      return false;
    }
  }

  /** Crow Memory 서버 spawn (Bridge와 동일한 패턴) */
  async spawnCrowServer(): Promise<boolean> {
    // 이미 실행 중이거나 spawn한 프로세스가 있으면 중복 방지
    if (this.child) {
      console.log('[VibeZoo] Crow 서버가 이미 spawn됨 — 중복 실행 방지');
      return true;
    }

    if (!this.extensionPath) {
      console.warn('[VibeZoo] extensionPath 없음 — Crow 서버 spawn 불가');
      return false;
    }

    // Python 스크립트 경로 (VSIX 번들링 후 확장 디렉토리 내부 mcp-servers/)
    const scriptPath = path.join(this.extensionPath, 'mcp-servers', 'crow_memory_server.py');

    if (!fs.existsSync(scriptPath)) {
      console.warn('[VibeZoo] crow_memory_server.py를 찾을 수 없음:', scriptPath);
      return false;
    }

    console.log(`[VibeZoo] Crow 서버 spawn: ${path.basename(scriptPath)} on port ${this.config.port}`);

    try {
      // PythonResolver로 인터프리터 탐색 (extensionPath를 workspaceRoot로 사용)
      const workspaceRoot = this.extensionPath ? path.dirname(this.extensionPath) : '';
      const pyCandidate = PythonResolver.getInstance().resolve(workspaceRoot);

      console.log(`[VibeZoo] Python resolved for Crow: "${pyCandidate.command}" (source=${pyCandidate.source}, version=${pyCandidate.version ?? '?'})`);

      const { command: pyCmd, args: pyArgs } = PythonResolver.buildSpawnArgs(pyCandidate, [
        scriptPath,
        '--port',
        String(this.config.port),
      ]);

      this.child = spawn(pyCmd, pyArgs, {
        detached: true,
        stdio: 'ignore',
      });
      this.child.unref();
      console.log(`[VibeZoo] ✅ Crow 서버 백그라운드 실행 중 (port ${this.config.port})`);
      return true;
    } catch (err: any) {
      console.error(`[VibeZoo] Crow 서버 spawn 실패: ${err.message}`);
      this.child = null;
      return false;
    }
  }

  /** 서버 준비 대기 (health check 폴링) */
  private async waitForReady(timeoutMs: number = 15000): Promise<boolean> {
    const deadline = Date.now() + timeoutMs;
    let delay = 200;
    while (Date.now() < deadline) {
      const healthy = await this.healthCheck();
      if (healthy) {
        console.log(`[VibeZoo] Crow 서버 준비 완료 (port ${this.config.port})`);
        return true;
      }
      await new Promise((r) => setTimeout(r, delay));
      delay = Math.min(delay * 1.5, 1000);
    }
    console.warn(`[VibeZoo] Crow 서버 준비 대기 시간 초과 (${timeoutMs}ms)`);
    return false;
  }

  /** Crow 서버 연결 확인 (서버가 없으면 자동 spawn) */
  async reconnect(maxRetries: number = 3): Promise<boolean> {
    for (let attempt = 0; attempt < maxRetries; attempt++) {
      this._onStatusChange.fire({ connected: false });

      const healthy = await this.healthCheck();
      if (healthy) {
        this._lastHealthy = true;
        console.log(`[VibeZoo] ✅ Crow 서버 연결 확인: 포트 ${this.config.port}`);
        this.startHealthCheck();
        this._onStatusChange.fire({ connected: true });
        return true;
      }

      // health check 실패 시 Crow 서버 spawn 시도 (첫 번째 시도에서만)
      if (attempt === 0) {
        console.log('[VibeZoo] Crow 서버 없음 — 자동 spawn 시도');
        const spawned = await this.spawnCrowServer();
        if (spawned) {
          console.log('[VibeZoo] Crow 서버 spawn 완료 — 준비 대기 중...');
          const ready = await this.waitForReady(15000);
          if (ready) {
            this._lastHealthy = true;
            console.log(`[VibeZoo] ✅ Crow 서버 자동 시작 성공: 포트 ${this.config.port}`);
            this.startHealthCheck();
            this._onStatusChange.fire({ connected: true });
            return true;
          }
        }
      }

      console.log(`[VibeZoo] ⏳ Crow 서버 응답 없음 (${attempt + 1}/${maxRetries}). 5초 후 재시도…`);
      if (attempt < maxRetries - 1) {
        await new Promise((r) => setTimeout(r, 5000));
      }
    }

    this._lastHealthy = false;
    console.warn(`[VibeZoo] ❌ Crow 서버 연결 최종 실패 (${maxRetries}회 시도).`);
    this._onStatusChange.fire({ connected: false });
    return false;
  }

  /** 연결 해제 (구독 정리만) */
  disconnect(): void {
    this.stopHealthCheck();
    this._lastHealthy = false;
    this._onStatusChange.fire({ connected: false });
    console.log('[VibeZoo] Crow 연결 해제됨 (서버는 계속 실행 중)');
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
