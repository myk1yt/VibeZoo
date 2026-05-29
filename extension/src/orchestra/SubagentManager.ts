// VibeZoo Wave 4: Subagent Manager
// vibezoo_mcp_bridge.py (Python, 단일 파일)를 spawn하고 생명주기를 관리한다.
// 이 브릿지 하나로 Scout + Reviewer + Tester + DeepAnalyzer 기능을 모두 제공.
// Crow Memory(외부, 9020)와 함께 Zoo Code에 MCP 도구를 제공한다.

import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { spawn, execSync, ChildProcess } from 'child_process';
import { SubagentNode } from '../types';

const BRIDGE_NAME = 'vibezoo-bridge';

export class SubagentManager {
  private child: ChildProcess | null = null;
  private node: SubagentNode | null = null;
  private bridgeScript: string | null = null;

  private _onChange = new vscode.EventEmitter<SubagentNode>();
  readonly onChange = this._onChange.event;

  constructor(context: vscode.ExtensionContext) {
    const candidates = [
      path.join(context.extensionPath, '..', 'mcp-servers', 'vibezoo_mcp_bridge.py'),
      path.join(context.extensionPath, '..', '..', 'mcp-servers', 'vibezoo_mcp_bridge.py'),
      'vibezoo_mcp_bridge.py',
    ];
    for (const c of candidates) {
      if (fs.existsSync(c)) {
        this.bridgeScript = c;
        break;
      }
    }
  }

  private getBridgePort(): number {
    return vscode.workspace.getConfiguration('vibezoo').get('bridge.port', 9027);
  }

  /** 개별 에이전트 포트 목록 */
  private getAgentPorts(): Array<{ id: string; name: string; port: number }> {
    const config = vscode.workspace.getConfiguration('vibezoo');
    return [
      { id: 'scout', name: 'Scout', port: config.get('scout.port', 9022) },
      { id: 'reviewer', name: 'Reviewer', port: config.get('reviewer.port', 9023) },
      { id: 'tester', name: 'Tester', port: config.get('tester.port', 9024) },
      { id: 'deepAnalyzer', name: 'Deep Analyzer', port: config.get('deepAnalyzer.port', 9026) },
    ];
  }

  /** Bridge 서버 시작 (Python — FastMCP SSE) — 싱글톤 감지 포함 */
  async spawnBridge(): Promise<number> {
    const port = this.getBridgePort();
    if (this.child) {
      return port;
    }

    // ★ 싱글톤 감지: 이미 실행 중인 브릿지가 있으면 spawn 생략
    const alive = await this.checkHealth(port);
    if (alive) {
      console.log(`[VibeZoo] 기존 MCP Bridge 감지됨 (port ${port}) — spawn 생략, 공유 사용`);
      this.node = {
        id: BRIDGE_NAME,
        name: 'VibeZoo Bridge',
        status: 'running',
        currentTask: 'Scout + Reviewer + Tester + DeepAnalyzer (shared)',
        port: port,
        startTime: Date.now(),
      };
      this._onChange.fire(this.node);

      // 개별 에이전트 노드 발행
      const agentPorts = this.getAgentPorts();
      for (const agent of agentPorts) {
        this._onChange.fire({
          id: agent.id,
          name: agent.name,
          status: 'running',
          currentTask: `${agent.name} ready via Bridge (:${port})`,
          port: agent.port,
          startTime: Date.now(),
        });
      }
      return port;
    }

    if (!this.bridgeScript) {
      throw new Error(
        'vibezoo_mcp_bridge.py를 찾을 수 없습니다.\n' +
        'VibeZoo 설치 디렉토리의 mcp-servers/ 폴더를 확인하세요.'
      );
    }

    // Python 의존성 자동 설치
    try {
      await this.installDependencies();
    } catch (err: any) {
      console.warn('[VibeZoo] Python deps install failed:', err.message);
      // 실패해도 진행 — 이미 설치되어 있을 수 있음
    }

    // 브릿지 spawn (이제 Crow URL을 스스로 가리키도록)
    this.child = spawn('python', [this.bridgeScript, '--port', String(port)], {
      detached: true,
      stdio: ['ignore', 'pipe', 'pipe'],
      env: {
        ...process.env,
        CROW_SERVER_URL: `http://127.0.0.1:${port}`,  // 로컬 Crow를 스스로 참조
      },
    });

    this.child.unref();

    // stdout/stderr → OutputChannel
    const channel = vscode.window.createOutputChannel('VibeZoo MCP Bridge');
    this.child.stdout?.on('data', (data: Buffer) => channel.append(data.toString()));
    this.child.stderr?.on('data', (data: Buffer) => channel.append(data.toString()));

    this.node = {
      id: BRIDGE_NAME,
      name: 'VibeZoo Bridge',
      status: 'running',
      currentTask: 'Scout + Reviewer + Tester + DeepAnalyzer + Crow',
      port: port,
      startTime: Date.now(),
    };

    // 준비 대기 (최대 15초 — Crow Memory 로딩 포함)
    await this.waitForReady(port, 15000);

    if (this.node && this.node.startTime) {
      this.node.elapsedMs = Date.now() - this.node.startTime;
    }
    this._onChange.fire(this.node);

    // 개별 에이전트 노드들도 함께 발행
    const agentPorts = this.getAgentPorts();
    for (const agent of agentPorts) {
      this._onChange.fire({
        id: agent.id,
        name: agent.name,
        status: 'running',
        currentTask: `${agent.name} ready via Bridge (:${port})`,
        port: agent.port,
        startTime: Date.now(),
      });
    }

    console.log(`[VibeZoo] MCP Bridge started on port ${port} (Crow+VibeZoo 통합)`);
    return port;
  }

  /** 싱글톤 감지: 이미 실행 중인 브릿지 헬스체크 */
  private async checkHealth(port: number): Promise<boolean> {
    try {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 2000);
      const response = await fetch(`http://127.0.0.1:${port}/health`, {
        signal: controller.signal,
      });
      clearTimeout(timer);
      return response.ok;
    } catch {
      return false;
    }
  }

  updateNodeStatus(status: SubagentNode['status'], task?: string): void {
    if (this.node) {
      this.node.status = status;
      if (task) this.node.currentTask = task;
      if (status === 'completed' || status === 'error') {
        this.node.elapsedMs = this.node.startTime ? Date.now() - this.node.startTime : 0;
      }
      this._onChange.fire(this.node);
    }
  }

  isRunning(): boolean {
    return this.child !== null;
  }

  getPort(): number {
    return this.getBridgePort();
  }

  terminate(): void {
    if (this.child) {
      const child = this.child;
      child.kill('SIGTERM');

      child.on('exit', () => {
        console.log('[VibeZoo] Bridge process exited');
      });

      setTimeout(() => {
        if (this.child) {
          this.child.kill('SIGKILL');
        }
        this.child = null;
        this.node = null;
      }, 5000);
    }
  }

  /** Python 의존성 자동 설치 */
  private async installDependencies(): Promise<void> {
    const requirements = ['fastmcp', 'uvicorn', 'requests'];
    const missing: string[] = [];

    for (const pkg of requirements) {
      try {
        execSync(`python -c "import ${pkg.replace('-', '_')}"`, { stdio: 'ignore' });
      } catch {
        missing.push(pkg);
      }
    }

    if (missing.length > 0) {
      console.log(`[VibeZoo] Installing missing Python packages: ${missing.join(', ')}`);
      execSync(`pip install ${missing.join(' ')}`, { stdio: 'pipe', timeout: 60000 });
      console.log('[VibeZoo] Python packages installed successfully');
    }
  }

  private async waitForReady(port: number, timeoutMs: number): Promise<void> {
    const deadline = Date.now() + timeoutMs;
    while (Date.now() < deadline) {
      try {
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), 1500);
        // 127.0.0.1 사용 (localhost는 IPv6로 resolve될 수 있음)
        const response = await fetch(`http://127.0.0.1:${port}/health`, {
          signal: controller.signal,
        });
        clearTimeout(timer);
        // Any HTTP response (including 404) means the server is running
        return;
      } catch {
        // Connection refused or timeout — not ready yet
      }
      await new Promise((r) => setTimeout(r, 300));
    }
  }
}
