// VibeZoo: Crow Memory SSE 서버 생명주기 관리자
// Crow는 VibeZoo에 포함되지 않는 외부 독립 시스템이다.
// VibeZoo는 child_process.spawn으로 Crow를 실행하고, SSE로 연동한다.

import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import * as os from 'os';
import { spawn, ChildProcess } from 'child_process';
import { CrowServerConfig } from '../types';

export class CrowServerManager {
  private config: CrowServerConfig;
  private child: ChildProcess | null = null;
  private healthCheckTimer: NodeJS.Timeout | null = null;
  private _onStatusChange = new vscode.EventEmitter<{
    connected: boolean;
    freshness?: number;
  }>();
  readonly onStatusChange = this._onStatusChange.event;

  constructor() {
    const crowHome = path.join(os.homedir(), '.zoo-code', 'crow');
    this.config = {
      port: vscode.workspace.getConfiguration('vibezoo').get('crow.port', 9020),
      crowBinPath: path.join(crowHome, 'crow.bin'),
      logPath: path.join(crowHome, 'server.log'),
      pidPath: path.join(crowHome, 'server.pid'),
      healthCheckIntervalMs: 30000,
      autoRestart: true,
      maxRestartAttempts: 3,
    };
  }

  /** PID 파일로 Crow 서버 실행 여부 확인 */
  isRunning(): boolean {
    try {
      const pidStr = fs.readFileSync(this.config.pidPath, 'utf-8').trim();
      const pid = parseInt(pidStr, 10);
      if (isNaN(pid)) return false;
      // kill(pid, 0): 시그널을 보내지 않고 프로세스 존재 여부만 확인
      process.kill(pid, 0);
      return true;
    } catch {
      return false;
    }
  }

  /** Crow SSE 서버 시작 (detached 모드 — VS Code 종료 후에도 생존) */
  async start(): Promise<number> {
    if (this.isRunning()) {
      const existingPid = fs.readFileSync(this.config.pidPath, 'utf-8').trim();
      console.log(`[VibeZoo] Crow 서버가 이미 실행 중: PID ${existingPid}`);
      return parseInt(existingPid, 10);
    }

    // Crow 서버 스크립트 경로 (Python — 외부 시스템)
    // Crow는 별도 설치된 독립 패키지라고 가정
    const crowScript = this.findCrowScript();
    if (!crowScript) {
      throw new Error(
        'Crow Memory 서버를 찾을 수 없습니다. Crow가 설치되어 있는지 확인하세요.\n' +
        'Crow는 VibeZoo와 독립된 외부 시스템입니다.'
      );
    }

    const out = fs.openSync(this.config.logPath, 'a');
    const err = fs.openSync(this.config.logPath, 'a');

    this.child = spawn('python', [crowScript, '--port', String(this.config.port)], {
      detached: true,
      stdio: ['ignore', out, err],
      env: { ...process.env, CROW_PORT: String(this.config.port) },
    });

    this.child.unref(); // 부모 이벤트 루프에서 제거

    if (this.child.pid) {
      fs.writeFileSync(this.config.pidPath, String(this.child.pid));
    }

    console.log(`[VibeZoo] Crow 서버 시작: PID ${this.child.pid}, 포트 ${this.config.port}`);

    // 서버 준비 대기 (최대 10초)
    await this.waitForReady(10000);

    this.startHealthCheck();
    this._onStatusChange.fire({ connected: true });

    return this.child.pid!;
  }

  /** Crow SSE 서버 재연결 (VS Code 재시작 시 호출) */
  async reconnect(): Promise<boolean> {
    if (!this.isRunning()) {
      console.log('[VibeZoo] Crow 서버가 실행 중이 아닙니다. 새로 시작합니다.');
      await this.start();
      return true;
    }

    // 기존 서버 헬스체크
    try {
      const healthy = await this.healthCheck();
      if (healthy) {
        const pid = fs.readFileSync(this.config.pidPath, 'utf-8').trim();
        console.log(`[VibeZoo] 기존 Crow 서버 재연결 성공: PID ${pid}`);
        this.startHealthCheck();
        this._onStatusChange.fire({ connected: true });
        return true;
      }
    } catch {
      console.log('[VibeZoo] Crow 서버 응답 없음. PID 파일 정리 후 재시작.');
    }

    // 응답 없으면 PID 파일 정리 후 새로 시작
    try { fs.unlinkSync(this.config.pidPath); } catch {}

    if (this.config.autoRestart) {
      await this.start();
      return true;
    }

    return false;
  }

  /** /health 엔드포인트 체크 */
  async healthCheck(): Promise<boolean> {
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 3000);
      const response = await fetch(`http://localhost:${this.config.port}/health`, {
        signal: controller.signal,
      });
      clearTimeout(timeout);
      return response.ok;
    } catch {
      return false;
    }
  }

  /** Crow 연결 해제 (의도적 — 서버는 종료하지 않음) */
  disconnect(): void {
    this.stopHealthCheck();
    this._onStatusChange.fire({ connected: false });
    console.log('[VibeZoo] Crow 연결 해제됨 (서버는 계속 실행 중)');
  }

  /** VibeZoo Extension 비활성화 시 정리 — 서버는 종료하지 않음 */
  onDeactivate(): void {
    this.stopHealthCheck();
    // 중요: detached 프로세스는 종료하지 않는다!
    // Crow는 VS Code 종료 후에도 생존해야 한다.
    if (this.child) {
      this.child.unref();
      this.child = null;
    }
  }

  /** Crow.bin freshness 추정 (최근 접근 시간 기반) */
  async getFreshness(): Promise<number> {
    try {
      const stat = fs.statSync(this.config.crowBinPath);
      const hoursSinceAccess = (Date.now() - stat.atimeMs) / 3600000;
      return Math.max(0, Math.round((1 - hoursSinceAccess / 168) * 100));
    } catch {
      return 0;
    }
  }

  private findCrowScript(): string | null {
    const candidates = [
      path.join(os.homedir(), '.zoo-code', 'crow', 'crow_mcp_server.py'),
      path.join(os.homedir(), 'crow', 'crow_mcp_server.py'),
      'crow_mcp_server.py', // PATH에 있는 경우
    ];
    for (const c of candidates) {
      if (fs.existsSync(c)) return c;
    }
    return null;
  }

  private async waitForReady(timeoutMs: number): Promise<void> {
    const deadline = Date.now() + timeoutMs;
    while (Date.now() < deadline) {
      if (await this.healthCheck()) return;
      await new Promise((r) => setTimeout(r, 200));
    }
    console.warn('[VibeZoo] Crow 서버가 준비되지 않았습니다. 계속 진행합니다.');
  }

  private startHealthCheck(): void {
    this.stopHealthCheck();
    this.healthCheckTimer = setInterval(async () => {
      const healthy = await this.healthCheck();
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
