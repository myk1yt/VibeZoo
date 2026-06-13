// VibeZoo: Python Interpreter Resolver
// Task 1 — python/python3/venv/pyenv/Microsoft Store 등 다양한 환경에서
// deterministic하게 Python interpreter를 찾는다.
//
// 사용법:
//   const resolver = PythonResolver.getInstance();
//   const py = resolver.resolve(workspaceRoot);  // 동기
//   // 또는
//   const py = await resolver.resolveAsync(workspaceRoot);
//
//   // spawn 인자 구성:
//   const { command, args } = PythonResolver.buildSpawnArgs(py, [scriptPath, '--port', '9027']);

import { execSync } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';
import * as vscode from 'vscode';
import type { PythonCommandCandidate } from '../types';

export interface SpawnArgs {
  /** spawn() 첫 번째 인자 (executable) */
  command: string;
  /** spawn() 두 번째 인자 (args) — candidate의 내장 args + caller args */
  args: string[];
}

export class PythonResolver {
  private static instance: PythonResolver;
  private cachedResult: PythonCommandCandidate | null = null;
  /** OutputChannel 로깅 (선택) */
  private outputChannel: vscode.OutputChannel | null = null;

  private constructor() {}

  // ── Singleton ────────────────────────────────────────────

  static getInstance(): PythonResolver {
    if (!PythonResolver.instance) {
      PythonResolver.instance = new PythonResolver();
    }
    return PythonResolver.instance;
  }

  /**
   * OutputChannel 연결 (디버그 로깅용).
   * 설정하지 않으면 console.log로 대체.
   */
  setOutputChannel(channel: vscode.OutputChannel): void {
    this.outputChannel = channel;
  }

  // ── Public API ───────────────────────────────────────────

  /**
   * 6단계 체인으로 Python interpreter를 동기 탐색.
   * 첫 번째 검증된 candidate 반환.
   * 결과는 인스턴스 수명 동안 캐싱됨 (clearCache()로 초기화).
   *
   * @param workspaceRoot - 현재 프로젝트 루트 (venv 탐색 기준)
   */
  resolve(workspaceRoot: string): PythonCommandCandidate {
    if (this.cachedResult) {
      this.log(`[PythonResolver] 캐시 반환: ${this.cachedResult.command} (source=${this.cachedResult.source})`);
      return this.cachedResult;
    }

    const chain = this.buildChain(workspaceRoot);
    this.log(`[PythonResolver] 탐색 시작 (${chain.length}개 candidate) — workspaceRoot=${workspaceRoot}`);

    for (const candidate of chain) {
      this.log(`  검증: command="${candidate.command}" source=${candidate.source}`);
      const valid = this.validateCandidate(candidate);
      if (valid) {
        this.log(`  ✅ 통과: version=${candidate.version}`);
        this.cachedResult = candidate;
        return candidate;
      }
      this.log(`  ❌ 실패: command="${candidate.command}"`);
    }

    // 모든 단계 실패 → 최후의 fallback (검증 없이 반환)
    const fallback: PythonCommandCandidate = {
      command: 'python',
      source: 'fallback',
    };
    this.log(`[PythonResolver] ⚠️ 모든 candidate 실패 — fallback: python`);
    this.cachedResult = fallback;
    return fallback;
  }

  /**
   * resolve()의 Promise 래퍼.
   */
  resolveAsync(workspaceRoot: string): Promise<PythonCommandCandidate> {
    return Promise.resolve(this.resolve(workspaceRoot));
  }

  /**
   * 캐시 초기화 (환경 변화 시 재탐색 트리거).
   */
  clearCache(): void {
    this.cachedResult = null;
    this.log('[PythonResolver] 캐시 초기화됨');
  }

  /**
   * PythonCommandCandidate에 포함된 명령어를 spawn(command, args) 형태로 분할.
   *
   * @example
   *   // command="python" → { command: "python", args: [...] }
   *   // command="py -3"  → { command: "py", args: ["-3", ...] }
   */
  static buildSpawnArgs(
    candidate: PythonCommandCandidate,
    extraArgs: string[],
  ): SpawnArgs {
    const parts = candidate.command.split(/\s+/);
    const command = parts[0];
    const args = [...parts.slice(1), ...extraArgs];
    return { command, args };
  }

  // ── Resolution Chain ─────────────────────────────────────

  private buildChain(workspaceRoot: string): PythonCommandCandidate[] {
    const chain: PythonCommandCandidate[] = [];
    const isWin = process.platform === 'win32';

    // 1. 사용자 설정 vibezoo.advanced.pythonPath
    const settingPath = this.getPythonPathSetting();
    if (settingPath) {
      chain.push({ command: settingPath, source: 'setting' });
    }

    // 2. 가상환경 탐색 (.venv → venv 순)
    const venvCandidates = this.findVenvPython(workspaceRoot);
    chain.push(...venvCandidates);

    // 3. pyenv (conda는 MVP에서 생략 — 복잡도 감소)
    if (this.isPyenvAvailable()) {
      // pyenv가 활성화되어 있으면 PATH의 python이 이미 pyenv 관리 하에 있음
      chain.push({ command: 'python', source: 'pyenv' });
    }

    // 4. python3 (macOS/Linux 기본)
    if (!isWin) {
      chain.push({ command: 'python3', source: 'path' });
    }

    // 5. python (Windows/Mac/Linux — Microsoft Store python 포함)
    chain.push({ command: 'python', source: 'path' });

    // 6. py -3 (Windows launcher — 최후 시도)
    if (isWin) {
      chain.push({ command: 'py -3', source: 'fallback' });
    }

    return chain;
  }

  // ── Candidate Sources ────────────────────────────────────

  private getPythonPathSetting(): string | undefined {
    try {
      const val = vscode.workspace
        .getConfiguration('vibezoo')
        .get<string>('advanced.pythonPath', '');
      const trimmed = val.trim();
      return trimmed.length > 0 ? trimmed : undefined;
    } catch {
      return undefined;
    }
  }

  private findVenvPython(workspaceRoot: string): PythonCommandCandidate[] {
    const candidates: PythonCommandCandidate[] = [];
    const isWin = process.platform === 'win32';
    const venvDirs = ['.venv', 'venv'];

    for (const venvDir of venvDirs) {
      const pythonPath = isWin
        ? path.join(venvDir, 'Scripts', 'python.exe')
        : path.join(venvDir, 'bin', 'python');
      const fullPath = path.join(workspaceRoot, pythonPath);
      if (fs.existsSync(fullPath)) {
        candidates.push({ command: fullPath, source: 'venv' });
      }
    }

    return candidates;
  }

  private isPyenvAvailable(): boolean {
    try {
      execSync('pyenv --version', {
        encoding: 'utf-8',
        timeout: 3000,
        stdio: ['ignore', 'pipe', 'pipe'],
      });
      return true;
    } catch {
      return false;
    }
  }

  // ── Validation ───────────────────────────────────────────

  private validateCandidate(candidate: PythonCommandCandidate): boolean {
    try {
      const stdout = execSync(`"${candidate.command}" --version`, {
        encoding: 'utf-8',
        timeout: 5000,
        stdio: ['ignore', 'pipe', 'pipe'],
      });
      const versionMatch = stdout.match(/Python (\d+\.\d+\.\d+)/);
      if (versionMatch) {
        candidate.version = versionMatch[1];
        return true;
      }
      return false;
    } catch {
      return false;
    }
  }

  // ── Logging ──────────────────────────────────────────────

  private log(message: string): void {
    if (this.outputChannel) {
      this.outputChannel.appendLine(message);
    } else {
      console.log(message);
    }
  }
}
