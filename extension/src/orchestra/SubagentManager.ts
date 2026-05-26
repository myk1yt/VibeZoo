// VibeZoo Wave 4: Subagent Manager
// vibezoo_mcp_bridge.py (Python, 단일 파일)를 spawn하고 생명주기를 관리한다.
// 이 브릿지 하나로 Scout + Reviewer + Tester + DeepAnalyzer 기능을 모두 제공.
// Crow Memory(외부, 9020)와 함께 Zoo Code에 MCP 도구를 제공한다.

import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { spawn, ChildProcess } from 'child_process';
import { SubagentNode } from '../types';

const BRIDGE_NAME = 'vibezoo-bridge';
const BRIDGE_PORT = 9027;

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

  /** Bridge 서버 시작 (Python — FastMCP SSE) */
  async spawnBridge(): Promise<number> {
    if (this.child) {
      return BRIDGE_PORT;
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

    const crowPort = vscode.workspace.getConfiguration('vibezoo').get('crow.port', 9020);

    this.child = spawn('python', [this.bridgeScript, '--port', String(BRIDGE_PORT)], {
      detached: true,
      stdio: ['ignore', 'pipe', 'pipe'],
      env: {
        ...process.env,
        CROW_SERVER_URL: `http://localhost:${crowPort}`,
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
      currentTask: 'Scout + Reviewer + Tester + DeepAnalyzer',
      port: BRIDGE_PORT,
      startTime: Date.now(),
    };

    // 준비 대기 (최대 10초)
    await this.waitForReady(BRIDGE_PORT, 10000);

    if (this.node && this.node.startTime) {
      this.node.elapsedMs = Date.now() - this.node.startTime;
    }
    this._onChange.fire(this.node);
    console.log(`[VibeZoo] MCP Bridge started on port ${BRIDGE_PORT}`);
    return BRIDGE_PORT;
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
    return BRIDGE_PORT;
  }

  terminate(): void {
    if (this.child) {
      this.child.kill('SIGTERM');
      setTimeout(() => {
        if (this.child) {
          this.child.kill('SIGKILL');
          this.child = null;
        }
      }, 5000);
      this.child = null;
      this.node = null;
    }
  }

  /** Python 의존성 자동 설치 */
  private async installDependencies(): Promise<void> {
    const requirements = ['fastmcp', 'uvicorn', 'requests'];
    const missing: string[] = [];

    for (const pkg of requirements) {
      try {
        const { execSync } = require('child_process');
        execSync(`python -c "import ${pkg.replace('-', '_')}"`, { stdio: 'ignore' });
      } catch {
        missing.push(pkg);
      }
    }

    if (missing.length > 0) {
      console.log(`[VibeZoo] Installing missing Python packages: ${missing.join(', ')}`);
      const { execSync } = require('child_process');
      execSync(`pip install ${missing.join(' ')}`, { stdio: 'pipe', timeout: 60000 });
      console.log('[VibeZoo] Python packages installed successfully');
    }
  }

  private async waitForReady(port: number, timeoutMs: number): Promise<void> {
    const deadline = Date.now() + timeoutMs;
    while (Date.now() < deadline) {
      try {
        const response = await fetch(`http://localhost:${port}/health`);
        if (response.ok) return;
      } catch { /* not ready */ }
      await new Promise((r) => setTimeout(r, 200));
    }
  }
}
