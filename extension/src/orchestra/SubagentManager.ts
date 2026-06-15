// VibeZoo Wave 4: Subagent Manager
// vibezoo_mcp_bridge.py (Python, 단일 파일)를 spawn하고 생명주기를 관리한다.
// 이 브릿지 하나로 Scout + Reviewer + Tester + DeepAnalyzer 기능을 모두 제공.
// Crow Memory(외부, 9020)와 함께 Zoo Code에 MCP 도구를 제공한다.

import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { spawn, execSync, ChildProcess } from 'child_process';
import { SubagentNode } from '../types';
import { ConfigService } from '../config/ConfigService';
import { PythonResolver } from '../python/PythonResolver';

const BRIDGE_NAME = 'vibezoo-bridge';

export class SubagentManager {
  private child: ChildProcess | null = null;
  private node: SubagentNode | null = null;
  private bridgeScript: string | null = null;
  private context: vscode.ExtensionContext;

  private _onChange = new vscode.EventEmitter<SubagentNode>();
  readonly onChange = this._onChange.event;

  constructor(context: vscode.ExtensionContext) {
    this.context = context;
    // VSIX 번들링 후 확장 디렉토리 내부 mcp-servers/ (extension/mcp-servers/vibezoo_mcp_bridge.py)
    const scriptPath = path.join(context.extensionPath, 'mcp-servers', 'vibezoo_mcp_bridge.py');
    if (fs.existsSync(scriptPath)) {
      this.bridgeScript = scriptPath;
    }
  }

  private getBridgePort(): number {
    return ConfigService.getBridgePort();
  }

  /** 개별 에이전트 포트 목록 */
  private getAgentPorts(): Array<{ id: string; name: string; port: number }> {
    return ConfigService.getAgentPorts();
  }

  /** Bridge 서버 시작 (Python — FastMCP SSE) — 기존 healthy 브릿지 재사용 or 구버전 종료 후 재시작 */
  async spawnBridge(): Promise<number> {
    const port = this.getBridgePort();
    if (this.child) {
      return port;
    }

    // 글로벌 브릿지 스크립트 복사 (항상 최신 버전을 유지)
    this.syncGlobalBridgeFiles();

    // ★ 기존에 healthy한 브릿지가 이미 실행 중이면 버전을 확인
    const runningVersion = await this.checkHealthAndVersion(port);
    const currentVersion = vscode.extensions.getExtension('local.vibezoo')?.packageJSON.version || 'unknown';

    if (runningVersion) {
      if (runningVersion === currentVersion || currentVersion === 'unknown') {
        console.log(`[VibeZoo] 기존 Bridge 재사용 (port ${port}, v${runningVersion}) — kill 없이 즉시 반환`);
        this.node = {
          id: BRIDGE_NAME,
          name: 'VibeZoo Bridge',
          status: 'running',
          currentTask: 'Scout + Reviewer + Tester + DeepAnalyzer + Crow',
          port: port,
          startTime: Date.now(),
        };
        this._onChange.fire(this.node);
        return port;
      } else {
        console.log(`[VibeZoo] Bridge 버전 불일치 감지 (실행중: v${runningVersion}, 확장: v${currentVersion}) — 재시작 진행`);
      }
    }

    // ★ 구버전 브릿지 강제 종료: detached + unref로 인해 Reload 후에도 프로세스가 살아있을 수 있음
    await this.killBridgeOnPort(port);
    // 포트가 해제될 때까지 대기 (최대 5초)
    await this.waitForPortFree(port, 5000);

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

    // PythonResolver로 인터프리터 탐색
    const resolver = PythonResolver.getInstance();
    const workspaceRoot = path.dirname(this.bridgeScript);
    // workspaceRoot로는 extensionPath를 사용 (venv 탐색 기준)
    const extensionRoot = path.dirname(path.dirname(this.bridgeScript)); // mcp-servers의 부모 = extension/
    const pyCandidate = resolver.resolve(extensionRoot);

    console.log(`[VibeZoo] Python resolved: "${pyCandidate.command}" (source=${pyCandidate.source}, version=${pyCandidate.version ?? '?'})`);

    // 브릿지 spawn (이제 Crow URL을 스스로 가리키도록)
    const { command: pyCmd, args: pyArgs } = PythonResolver.buildSpawnArgs(pyCandidate, [
      this.bridgeScript,
      '--port',
      String(port),
    ]);
    this.child = spawn(pyCmd, pyArgs, {
      detached: true,
      cwd: path.dirname(this.bridgeScript),
      stdio: ['ignore', 'pipe', 'pipe'],
      env: {
        ...process.env,
        CROW_SERVER_URL: ConfigService.getCrowUrl(),
      },
    });

    // stdout/stderr → OutputChannel
    const channel = vscode.window.createOutputChannel('VibeZoo MCP Bridge');
    this.child.stdout?.on('data', (data: Buffer) => channel.append(data.toString()));
    this.child.stderr?.on('data', (data: Buffer) => channel.append(data.toString()));

    // 프로세스가 즉시 종료될 경우 감지하여 로그 출력
    this.child.on('exit', (code, signal) => {
      if (code !== null && code !== 0) {
        const msg = `[VibeZoo] Bridge 프로세스가 종료 코드 ${code}로 종료됨 (signal: ${signal ?? 'none'})`;
        console.error(msg);
        channel.appendLine(`[ERROR] ${msg}`);
      }
    });

    this.child.unref();

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

  /** 포트를 사용 중인 구버전 브릿지 프로세스 종료 */
  private async killBridgeOnPort(port: number): Promise<void> {
    try {
      const runningVersion = await this.checkHealthAndVersion(port);
      if (!runningVersion && !this.child) return;

      console.log(`[VibeZoo] 구버전 Bridge 감지됨 (port ${port}) — 강제 종료 시도`);
      try {
        // Windows: netstat으로 PID 찾기
        const isWin = process.platform === 'win32';
        const cmd = isWin
          ? `netstat -ano | findstr :${port} | findstr LISTENING`
          : `lsof -ti:${port}`;
        const pidOutput = execSync(cmd, { encoding: 'utf-8', timeout: 5000 });
        const pidMatch = pidOutput.match(/(\d+)\s*$/m);
        if (pidMatch) {
          const pid = pidMatch[1].trim();
          const killCmd = isWin ? `taskkill /F /PID ${pid} /T` : `kill -9 ${pid}`;
          execSync(killCmd, { timeout: 3000 });
          console.log(`[VibeZoo] 구버전 Bridge(PID ${pid}) 종료 완료`);
        }
      } catch (e: any) {
        // netstat/findstr 실패 시 휴리스틱 fallback
        console.warn(`[VibeZoo] PID 탐색 실패, 강제 종료 생략(고립 대기): ${e.message}`);
        if (this.child && this.child.pid) {
          try {
            console.log(`[VibeZoo] 캐싱된 ChildProcess(PID: ${this.child.pid})를 통해 종료 시도`);
            if (process.platform === 'win32') {
              execSync(`taskkill /F /PID ${this.child.pid} /T`, { timeout: 3000 });
            } else {
              this.child.kill('SIGKILL');
            }
          } catch (err) {
            console.warn(`[VibeZoo] 캐싱된 ChildProcess 종료 실패:`, err);
          }
        }
      }
    } catch {
      // 조용히 실패 — spawn 단계에서 새 프로세스가 시작됨
    }
  }

  /** 포트가 해제될 때까지 대기 */
  private async waitForPortFree(port: number, timeoutMs: number): Promise<void> {
    const deadline = Date.now() + timeoutMs;
    while (Date.now() < deadline) {
      const runningVersion = await this.checkHealthAndVersion(port);
      if (!runningVersion) return;
      await new Promise((r) => setTimeout(r, 300));
    }
    console.warn(`[VibeZoo] Port ${port} 해제 대기 시간 초과 — 새 브릿지 spawn 시도`);
  }

  /** 싱글톤 감지: 이미 실행 중인 브릿지 헬스체크 및 버전 반환 */
  private async checkHealthAndVersion(port: number): Promise<string | null> {
    try {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 2000);
      const response = await fetch(ConfigService.getAgentUrl(port, '/health'), {
        signal: controller.signal,
      });
      clearTimeout(timer);
      if (response.ok) {
        try {
          const data = await response.json() as { version?: string };
          return data.version || 'legacy';
        } catch {
          return 'legacy';
        }
      }
      return null;
    } catch {
      return null;
    }
  }

  /** 글로벌 디렉토리에 브릿지 파일 강제 동기화 (Zoo Code autoStartCommand 용) */
  private syncGlobalBridgeFiles(): void {
    try {
      const userProfile = process.env.USERPROFILE || process.env.HOME;
      if (!userProfile) return;
      
      const destDir = path.join(userProfile, 'mcp-servers', 'vibezoo');
      if (!fs.existsSync(destDir)) {
        fs.mkdirSync(destDir, { recursive: true });
      }

      const srcDir = path.join(this.context.extensionPath, 'mcp-servers');
      const filesToSync = ['vibezoo_mcp_bridge.py', 'start_vibezoo_bridge.bat'];

      for (const file of filesToSync) {
        const srcPath = path.join(srcDir, file);
        const destPath = path.join(destDir, file);
        if (fs.existsSync(srcPath)) {
          fs.copyFileSync(srcPath, destPath);
        }
      }
      console.log(`[VibeZoo] 글로벌 브릿지 파일 동기화 완료 (${destDir})`);
    } catch (err: any) {
      console.warn(`[VibeZoo] 글로벌 브릿지 파일 동기화 실패: ${err.message}`);
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
      const pid = child.pid;
      
      try {
        if (process.platform === 'win32' && pid) {
           execSync(`taskkill /F /PID ${pid} /T`, { timeout: 3000 });
        } else {
           child.kill('SIGTERM');
           setTimeout(() => {
             if (this.child) {
               this.child.kill('SIGKILL');
             }
           }, 5000);
        }
      } catch (err) {
         console.warn('[VibeZoo] Process termination failed', err);
      }
      
      this.child = null;
      this.node = null;
    }
  }

  /** Python 의존성 자동 설치 (PythonResolver로 탐색한 Python 사용) */
  private async installDependencies(): Promise<void> {
    const requirements = ['fastmcp', 'uvicorn', 'requests'];
    const missing: string[] = [];

    const resolver = PythonResolver.getInstance();
    // workspaceRoot가 없으면 resolve() 기본 동작 (venv 제외)
    const py = resolver.resolve('');

    for (const pkg of requirements) {
      try {
        execSync(`"${py.command}" -c "import ${pkg.replace('-', '_')}"`, { stdio: 'ignore' });
      } catch {
        missing.push(pkg);
      }
    }

    if (missing.length > 0) {
      console.log(`[VibeZoo] Installing missing Python packages: ${missing.join(' ')} using ${py.command}`);
      execSync(`"${py.command}" -m pip install ${missing.join(' ')}`, { stdio: 'pipe', timeout: 60000 });
      console.log('[VibeZoo] Python packages installed successfully');
    }
  }

  private async waitForReady(port: number, timeoutMs: number): Promise<void> {
    const deadline = Date.now() + timeoutMs;
    let delay = 100;
    while (Date.now() < deadline) {
      try {
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), 1500);
        const response = await fetch(ConfigService.getAgentUrl(port, '/health'), {
          signal: controller.signal,
        });
        clearTimeout(timer);
        // Any HTTP response (including 404) means the server is running
        return;
      } catch {
        // Connection refused or timeout — not ready yet
      }
      await new Promise((r) => setTimeout(r, delay));
      delay = Math.min(delay * 1.5, 1000);
    }
  }
}
