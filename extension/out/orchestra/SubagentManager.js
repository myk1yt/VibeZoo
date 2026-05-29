"use strict";
// VibeZoo Wave 4: Subagent Manager
// vibezoo_mcp_bridge.py (Python, 단일 파일)를 spawn하고 생명주기를 관리한다.
// 이 브릿지 하나로 Scout + Reviewer + Tester + DeepAnalyzer 기능을 모두 제공.
// Crow Memory(외부, 9020)와 함께 Zoo Code에 MCP 도구를 제공한다.
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.SubagentManager = void 0;
const vscode = __importStar(require("vscode"));
const path = __importStar(require("path"));
const fs = __importStar(require("fs"));
const child_process_1 = require("child_process");
const BRIDGE_NAME = 'vibezoo-bridge';
class SubagentManager {
    child = null;
    node = null;
    bridgeScript = null;
    _onChange = new vscode.EventEmitter();
    onChange = this._onChange.event;
    constructor(context) {
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
    getBridgePort() {
        return vscode.workspace.getConfiguration('vibezoo').get('bridge.port', 9027);
    }
    /** 개별 에이전트 포트 목록 */
    getAgentPorts() {
        const config = vscode.workspace.getConfiguration('vibezoo');
        return [
            { id: 'scout', name: 'Scout', port: config.get('scout.port', 9022) },
            { id: 'reviewer', name: 'Reviewer', port: config.get('reviewer.port', 9023) },
            { id: 'tester', name: 'Tester', port: config.get('tester.port', 9024) },
            { id: 'deepAnalyzer', name: 'Deep Analyzer', port: config.get('deepAnalyzer.port', 9026) },
        ];
    }
    /** Bridge 서버 시작 (Python — FastMCP SSE) — 구버전 종료 후 재시작 */
    async spawnBridge() {
        const port = this.getBridgePort();
        if (this.child) {
            return port;
        }
        // ★ 구버전 브릿지 강제 종료: detached + unref로 인해 Reload 후에도 프로세스가 살아있을 수 있음
        await this.killBridgeOnPort(port);
        // 포트가 해제될 때까지 대기 (최대 5초)
        await this.waitForPortFree(port, 5000);
        if (!this.bridgeScript) {
            throw new Error('vibezoo_mcp_bridge.py를 찾을 수 없습니다.\n' +
                'VibeZoo 설치 디렉토리의 mcp-servers/ 폴더를 확인하세요.');
        }
        // Python 의존성 자동 설치
        try {
            await this.installDependencies();
        }
        catch (err) {
            console.warn('[VibeZoo] Python deps install failed:', err.message);
            // 실패해도 진행 — 이미 설치되어 있을 수 있음
        }
        // 브릿지 spawn (이제 Crow URL을 스스로 가리키도록)
        this.child = (0, child_process_1.spawn)('python', [this.bridgeScript, '--port', String(port)], {
            detached: true,
            stdio: ['ignore', 'pipe', 'pipe'],
            env: {
                ...process.env,
                CROW_SERVER_URL: `http://127.0.0.1:9020`, // Crow Memory 기본 포트 (port 변수는 bridge 포트, Crow는 9020 고정)
            },
        });
        this.child.unref();
        // stdout/stderr → OutputChannel
        const channel = vscode.window.createOutputChannel('VibeZoo MCP Bridge');
        this.child.stdout?.on('data', (data) => channel.append(data.toString()));
        this.child.stderr?.on('data', (data) => channel.append(data.toString()));
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
    async killBridgeOnPort(port) {
        try {
            const alive = await this.checkHealth(port);
            if (!alive)
                return;
            console.log(`[VibeZoo] 구버전 Bridge 감지됨 (port ${port}) — 강제 종료 시도`);
            try {
                // Windows: netstat으로 PID 찾기
                const isWin = process.platform === 'win32';
                const cmd = isWin
                    ? `netstat -ano | findstr :${port} | findstr LISTENING`
                    : `lsof -ti:${port}`;
                const pidOutput = (0, child_process_1.execSync)(cmd, { encoding: 'utf-8', timeout: 5000 });
                const pidMatch = pidOutput.match(/(\d+)\s*$/m);
                if (pidMatch) {
                    const pid = pidMatch[1].trim();
                    const killCmd = isWin ? `taskkill /F /PID ${pid}` : `kill -9 ${pid}`;
                    (0, child_process_1.execSync)(killCmd, { timeout: 3000 });
                    console.log(`[VibeZoo] 구버전 Bridge(PID ${pid}) 종료 완료`);
                }
            }
            catch (e) {
                // netstat/findstr 실패 시 휴리스틱 fallback
                console.warn(`[VibeZoo] PID 탐색 실패, fallback kill: ${e.message}`);
                try {
                    if (process.platform === 'win32') {
                        (0, child_process_1.execSync)(`taskkill /F /FI "IMAGENAME eq python.exe"`, { timeout: 3000 });
                    }
                }
                catch {
                    // 이미 종료되었거나 접근 권한 없음 — 무시
                }
            }
        }
        catch {
            // 조용히 실패 — spawn 단계에서 새 프로세스가 시작됨
        }
    }
    /** 포트가 해제될 때까지 대기 */
    async waitForPortFree(port, timeoutMs) {
        const deadline = Date.now() + timeoutMs;
        while (Date.now() < deadline) {
            const alive = await this.checkHealth(port);
            if (!alive)
                return;
            await new Promise((r) => setTimeout(r, 300));
        }
        console.warn(`[VibeZoo] Port ${port} 해제 대기 시간 초과 — 새 브릿지 spawn 시도`);
    }
    /** 싱글톤 감지: 이미 실행 중인 브릿지 헬스체크 */
    async checkHealth(port) {
        try {
            const controller = new AbortController();
            const timer = setTimeout(() => controller.abort(), 2000);
            const response = await fetch(`http://127.0.0.1:${port}/health`, {
                signal: controller.signal,
            });
            clearTimeout(timer);
            return response.ok;
        }
        catch {
            return false;
        }
    }
    updateNodeStatus(status, task) {
        if (this.node) {
            this.node.status = status;
            if (task)
                this.node.currentTask = task;
            if (status === 'completed' || status === 'error') {
                this.node.elapsedMs = this.node.startTime ? Date.now() - this.node.startTime : 0;
            }
            this._onChange.fire(this.node);
        }
    }
    isRunning() {
        return this.child !== null;
    }
    getPort() {
        return this.getBridgePort();
    }
    terminate() {
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
    async installDependencies() {
        const requirements = ['fastmcp', 'uvicorn', 'requests'];
        const missing = [];
        for (const pkg of requirements) {
            try {
                (0, child_process_1.execSync)(`python -c "import ${pkg.replace('-', '_')}"`, { stdio: 'ignore' });
            }
            catch {
                missing.push(pkg);
            }
        }
        if (missing.length > 0) {
            console.log(`[VibeZoo] Installing missing Python packages: ${missing.join(', ')}`);
            (0, child_process_1.execSync)(`pip install ${missing.join(' ')}`, { stdio: 'pipe', timeout: 60000 });
            console.log('[VibeZoo] Python packages installed successfully');
        }
    }
    async waitForReady(port, timeoutMs) {
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
            }
            catch {
                // Connection refused or timeout — not ready yet
            }
            await new Promise((r) => setTimeout(r, 300));
        }
    }
}
exports.SubagentManager = SubagentManager;
//# sourceMappingURL=SubagentManager.js.map