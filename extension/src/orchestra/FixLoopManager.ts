// VibeZoo M1-A: FixLoopManager
// Autonomous Fix Loop 상태 머신
// 상태: idle → pending → in_progress → building → resolved/abandoned
// LLM과 ~/.vibezoo-fix-request.json 파일로 통신
// oscillation 감지 (A→B→A 패턴) + maxAttempts 초과 시 give up

import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { Diagnostic, BuildResult } from '../types';
import { StatusBarManager, GuardMode, NotificationThrottle } from '../ui/StatusBarManager';
import { ConfigService } from '../config/ConfigService';
// NotificationThrottle is used for all user-facing notifications

// ── 타입 정의 ────────────────────────────────────────────────

export type FixLoopState =
  | 'idle'
  | 'pending'
  | 'in_progress'
  | 'building'
  | 'resolved'
  | 'abandoned'
  | 'awaiting_user'
  | 'user_override';

export interface FixAttempt {
  attempt: number;
  exitCode: number;
  diagnostics: Diagnostic[];
  stderr: string;
  fixApplied: string | null;  // LLM이 적용한 수정 요약
  timestamp: number;
}

export interface FixSession {
  sessionId: string;
  status: FixLoopState;
  attempt: number;
  maxAttempts: number;
  createdAt: number;
  history: FixAttempt[];
  projectRoot: string;
  taskName: string;
  timeoutId?: NodeJS.Timeout;
}

export interface FixRequestFile {
  sessionId: string;
  status: FixLoopState;
  attempt: number;
  maxAttempts: number;
  createdAt: number;
  history: FixAttempt[];
  projectRoot: string;
  pastFixes?: any[];  // Crow recall 결과
}

// ── I_instability: 예측형 가드레일 ────────────────────────────

export interface InstabilityMetrics {
  /** 누적 편집 횟수 (attempt 수) */
  nedits: number;
  /** 자기상관계수: 동일 에러 반복률 [0, 1] */
  autocorr: number;
  /** 연속 빌드 실패 횟수 */
  buildFails: number;
}

/**
 * 불안정성 계산: I = α·nedits + β·autocorr + γ·buildFails
 * α=0.35, β=0.45, γ=0.20
 */
export function calculateInstability(m: InstabilityMetrics): number {
  const α = 0.35, β = 0.45, γ = 0.20;
  return α * Math.min(m.nedits / 10, 1) + β * m.autocorr + γ * Math.min(m.buildFails / 5, 1);
}

/**
 * 불안정성 → GuardMode 변환
 * <0.3=active, <0.7=warning, ≥0.7=safe
 */
export function getGuardMode(instability: number): GuardMode {
  if (instability < 0.3) return 'active';
  if (instability < 0.7) return 'warning';
  return 'safe';
}

// ── FixLoopManager ───────────────────────────────────────────

export class FixLoopManager {
  private state: FixLoopState = 'idle';
  private currentSession: FixSession | null = null;
  private fixRequestPath: string;
  private maxAttempts: number;
  private readonly SESSION_TIMEOUT_MS = 120_000; // 2분
  private statusBarMessage: vscode.Disposable | null = null;

  constructor() {
    this.fixRequestPath = path.join(os.homedir(), '.vibezoo-fix-request.json');
    this.maxAttempts = vscode.workspace
      .getConfiguration('vibezoo')
      .get('build.autoFixMaxAttempts', 3);
  }

  get stateValue(): FixLoopState {
    return this.state;
  }

  get currentSessionValue(): FixSession | null {
    return this.currentSession;
  }

  /** BuildFeedback이 빌드 실패 시 호출 */
  onBuildFailure(diagnostics: Diagnostic[], stderr: string, taskName = 'vibezoo: build'): void {
    const projectRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath ?? '';

    // 기존 세션이 없거나 resolved 상태면 새 세션 생성
    if (!this.currentSession || this.currentSession.status === 'resolved' || this.currentSession.status === 'abandoned') {
      this.currentSession = this.createSession(projectRoot, taskName);
    }

    // 새 attempt 추가
    const attemptNum = this.currentSession.history.length + 1;
    const attempt: FixAttempt = {
      attempt: attemptNum,
      exitCode: 1,
      diagnostics,
      stderr,
      fixApplied: null,
      timestamp: Date.now(),
    };
    this.currentSession.history.push(attempt);
    this.currentSession.attempt = attemptNum;
    this.currentSession.status = 'pending';
    this.state = 'pending';

    // Fix request 파일 쓰기
    this.writeFixRequest();
    this.updateStatusBar();

    // 세션 타임아웃 설정 (LLM이 2분 내에 응답 없으면 abandon)
    this.resetSessionTimeout();

    console.log(`[VibeZoo] FixLoopManager: 빌드 실패 → pending (attempt ${attemptNum}/${this.maxAttempts})`);
  }

  /** LLM이 auto_fix_status() 호출 → 상태를 in_progress로 변경 */
  markInProgress(): void {
    if (this.currentSession) {
      this.currentSession.status = 'in_progress';
      this.state = 'in_progress';
      this.writeFixRequest();
      console.log('[VibeZoo] FixLoopManager: → in_progress (LLM 분석 중)');
    }
  }

  /** retry_build() 호출 전 → 상태를 building으로 변경 */
  markBuilding(): void {
    if (this.currentSession) {
      this.currentSession.status = 'building';
      this.state = 'building';
      this.writeFixRequest();
      console.log('[VibeZoo] FixLoopManager: → building (빌드 실행 중)');
    }
  }

  /** 빌드 성공 시 */
  markResolved(): void {
    if (this.currentSession) {
      this.currentSession.status = 'resolved';
      this.state = 'resolved';
      this.clearSessionTimeout();
      this.writeFixRequest();
      this.updateStatusBar(true);

      // 성공 메시지
      const attemptCount = this.currentSession.history.length;
      NotificationThrottle.showInfo(
        `✅ VibeZoo: ${attemptCount}회 시도 후 빌드 성공!`
      );

      // fix request 파일 정리 (성공 시)
      this.cleanupFixRequest();

      console.log(`[VibeZoo] FixLoopManager: → resolved (${attemptCount}회 시도 후 성공)`);
    }
  }

  /** 빌드 실패 시 (LLM이 retry_build()로 실패 보고) */
  markBuildFailed(diagnostics: Diagnostic[], stderr: string): void {
    if (!this.currentSession) return;

    // 새 attempt 추가
    const attemptNum = this.currentSession.history.length + 1;
    const attempt: FixAttempt = {
      attempt: attemptNum,
      exitCode: 1,
      diagnostics,
      stderr,
      fixApplied: null,
      timestamp: Date.now(),
    };
    this.currentSession.history.push(attempt);
    this.currentSession.attempt = attemptNum;

    // I_instability 계산 (가드레일)
    const instability = this.calculateInstability();
    const guardMode = getGuardMode(instability);

    if (guardMode === 'active') {
      // 불안정성 높음 → 즉시 중단
      this.currentSession.status = 'abandoned';
      this.state = 'abandoned';
      this.clearSessionTimeout();
      this.writeFixRequest();
      this.updateStatusBar();
      NotificationThrottle.showWarning(
        `⚠️ VibeZoo: I_instability=${instability.toFixed(2)} (Guard: Active). Auto-Fix를 중단합니다. 수동 확인이 필요합니다.`
      );
      console.log(`[VibeZoo] FixLoopManager: → abandoned (I_instability=${instability.toFixed(2)}, Guard=${guardMode})`);
      return;
    }

    // Max attempts 초과
    if (this.shouldGiveUp()) {
      this.currentSession.status = 'abandoned';
      this.state = 'abandoned';
      this.clearSessionTimeout();
      this.writeFixRequest();
      this.updateStatusBar();
      NotificationThrottle.showWarning(
        `⚠️ VibeZoo: 최대 ${this.maxAttempts}회 시도 초과. Auto-Fix를 중단합니다.`
      );
      console.log('[VibeZoo] FixLoopManager: → abandoned (max attempts 초과)');
      return;
    }

    // 재시도 가능 → pending 상태로
    this.currentSession.status = 'pending';
    this.state = 'pending';
    this.resetSessionTimeout();
    this.writeFixRequest();
    this.updateStatusBar();

    console.log(`[VibeZoo] FixLoopManager: 빌드 실패 → pending (attempt ${attemptNum}/${this.maxAttempts})`);
  }

  /**
   * I_instability 계산: 불안정성 연속값 반환
   * 기존 isOscillating() boolean을 대체
   */
  calculateInstability(): number {
    const h = this.currentSession?.history ?? [];
    if (h.length === 0) return 0;

    // nedits: 누적 편집 횟수 (attempt 수)
    const nedits = h.length;

    // autocorr: 자기상관계수 — 동일 에러 시그니처 반복률
    let sameSigCount = 0;
    let totalPairs = 0;
    for (let i = 1; i < h.length; i++) {
      const sig1 = this.errorSignature(h[i - 1].diagnostics);
      const sig2 = this.errorSignature(h[i].diagnostics);
      totalPairs++;
      if (sig1 === sig2) sameSigCount++;
    }
    const autocorr = totalPairs > 0 ? sameSigCount / totalPairs : 0;

    // buildFails: 연속 빌드 실패 횟수
    let buildFails = 0;
    for (let i = h.length - 1; i >= 0; i--) {
      if (h[i].exitCode !== 0) buildFails++;
      else break;
    }

    return calculateInstability({ nedits, autocorr, buildFails });
  }

  // isOscillating()은 calculateInstability()로 대체됨
  private _oscillationCompat(): boolean {
    // 이전 호환성: calculateInstability()가 active를 반환하면 oscillation
    return this.calculateInstability() >= 0.3;
  }

  /** Give up 조건 */
  shouldGiveUp(): boolean {
    if (!this.currentSession) return false;
    if (this.currentSession.history.length >= this.maxAttempts) return true;
    if (this.calculateInstability() >= 0.5) return true;
    return false;
  }

  /** 에러 시그니처 생성 (파일+코드 기준) */
  private errorSignature(diagnostics: Diagnostic[]): string {
    return diagnostics
      .map(d => `${d.file}:${d.code}`)
      .sort()
      .join('|');
  }

  /** 세션 생성 */
  private createSession(projectRoot: string, taskName: string): FixSession {
    return {
      sessionId: `fix_${Date.now()}`,
      status: 'pending',
      attempt: 0,
      maxAttempts: this.maxAttempts,
      createdAt: Date.now(),
      history: [],
      projectRoot,
      taskName,
    };
  }

  /** Fix request JSON 파일 쓰기 */
  private writeFixRequest(): void {
    if (!this.currentSession) return;

    try {
      // Crow recall 결과도 포함 (있으면)
      const pastFixes = this.currentSession.history
        .filter(a => a.fixApplied)
        .map(a => ({
          attempt: a.attempt,
          fixApplied: a.fixApplied,
          timestamp: a.timestamp,
        }));

      const data: FixRequestFile = {
        sessionId: this.currentSession.sessionId,
        status: this.currentSession.status,
        attempt: this.currentSession.attempt,
        maxAttempts: this.currentSession.maxAttempts,
        createdAt: this.currentSession.createdAt,
        history: this.currentSession.history,
        projectRoot: this.currentSession.projectRoot,
        pastFixes: pastFixes.length > 0 ? pastFixes : undefined,
      };

      fs.mkdirSync(path.dirname(this.fixRequestPath), { recursive: true });
      fs.writeFileSync(this.fixRequestPath, JSON.stringify(data, null, 2), 'utf-8');
      console.log(`[VibeZoo] Fix request written to ${this.fixRequestPath}`);
    } catch (err) {
      console.error('[VibeZoo] Failed to write fix request:', err);
    }
  }

  /** Fix request 파일 정리 */
  private cleanupFixRequest(): void {
    try {
      if (fs.existsSync(this.fixRequestPath)) {
        fs.unlinkSync(this.fixRequestPath);
      }
    } catch { /* ignore */ }
  }

  /** StatusBar 업데이트 */
  private updateStatusBar(success = false): void {
    // 기존 메시지 제거
    this.statusBarMessage?.dispose();

    if (!this.currentSession) return;

    const attempt = this.currentSession.attempt;
    const max = this.currentSession.maxAttempts;

    if (success) {
      this.statusBarMessage = vscode.window.setStatusBarMessage(
        `$(check) VibeZoo: Auto-Fix 성공 (${attempt}회 시도)`,
        8000
      );
    } else if (this.currentSession.status === 'abandoned') {
      this.statusBarMessage = vscode.window.setStatusBarMessage(
        `$(error) VibeZoo: Auto-Fix 중단됨`,
        8000
      );
    } else if (this.currentSession.status === 'pending') {
      this.statusBarMessage = vscode.window.setStatusBarMessage(
        `$(warning) VibeZoo: 빌드 실패 — [자동 수정]`,
        10000
      );
    } else if (this.currentSession.status === 'in_progress') {
      this.statusBarMessage = vscode.window.setStatusBarMessage(
        `$(sync~spin) VibeZoo: Auto-Fix ${attempt}/${max} 분석 중...`,
        5000
      );
    } else if (this.currentSession.status === 'building') {
      this.statusBarMessage = vscode.window.setStatusBarMessage(
        `$(sync~spin) VibeZoo: Auto-Fix ${attempt}/${max} 빌드 중...`,
        5000
      );
    }
  }

  /** 세션 타임아웃 리셋 */
  private resetSessionTimeout(): void {
    this.clearSessionTimeout();
    if (!this.currentSession) return;

    this.currentSession.timeoutId = setTimeout(() => {
      if (this.currentSession && this.currentSession.status !== 'resolved' && this.currentSession.status !== 'abandoned') {
        this.currentSession.status = 'abandoned';
        this.state = 'abandoned';
        this.writeFixRequest();
        this.updateStatusBar();
        console.log('[VibeZoo] FixLoopManager: → abandoned (timeout)');
        NotificationThrottle.showWarning(
          '⏰ VibeZoo: Auto-Fix 시간 초과 (120초). 수동 확인이 필요합니다.'
        );
      }
    }, this.SESSION_TIMEOUT_MS);
  }

  /** 세션 타임아웃 제거 */
  private clearSessionTimeout(): void {
    if (this.currentSession?.timeoutId) {
      clearTimeout(this.currentSession.timeoutId);
      this.currentSession.timeoutId = undefined;
    }
  }

  /** 사용자 개입 — 일시정지 */
  pause(): void {
    if (this.currentSession && (this.state === 'in_progress' || this.state === 'pending')) {
      this.currentSession.status = 'awaiting_user';
      this.state = 'awaiting_user';
      this.writeFixRequest();
      this.updateStatusBar();
      NotificationThrottle.showInfo('⏸️ VibeZoo: Auto-Fix가 일시정지되었습니다.');
    }
  }

  /** 사용자 개입 — 재개 */
  async resume(): Promise<void> {
    if (this.currentSession && this.state === 'awaiting_user') {
      // Context Hydration: freeze 상태와 현재 파일 비교
      await this.hydrateContext();

      this.currentSession.status = 'in_progress';
      this.state = 'in_progress';
      this.writeFixRequest();
      this.updateStatusBar();
      NotificationThrottle.showInfo('▶️ VibeZoo: Auto-Fix가 재개되었습니다.');
    }
  }

  /**
   * Context Hydration: freeze 시점과 현재 파일 상태를 비교하여
   * 변경 감지 시 Crow context 레지스터에 저장.
   * resume 시 자동 호출되어 AST Delta 추적.
   */
  private async hydrateContext(): Promise<void> {
    if (!this.currentSession) return;

    const projectRoot = this.currentSession.projectRoot;
    if (!projectRoot) return;

    try {
      // freeze 시점의 fix request 기록과 현재 파일 상태 비교
      const freezeSnapshot = this.currentSession.history[this.currentSession.history.length - 1];
      if (!freezeSnapshot) return;

      // 간소화: 수정된 파일 목록 diff → Crow ingest
      const touchedFiles = new Set<string>();
      for (const attempt of this.currentSession.history) {
        for (const diag of attempt.diagnostics) {
          if (diag.file) touchedFiles.add(diag.file);
        }
      }

      if (touchedFiles.size > 0) {
        const fileList = Array.from(touchedFiles).slice(0, 20);
        console.log(`[FixLoopManager] HydrateContext: ${fileList.length} 파일 변경 감지됨`);
        // Crow ingest를 시도 (실패해도 무관)
        try {
          // 로컬 HTTP 요청으로 Crow에 저장
          const http = await import('http');
          const payload = JSON.stringify({
            content: `FixLoop resume detected changes in ${fileList.length} files: ${fileList.join(', ')}`,
            register: 'context'
          });
          const req = http.request({
            hostname: ConfigService.getHost(),
            port: ConfigService.getCrowPort(),
            path: '/ingest',
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Content-Length': payload.length }
          });
          req.write(payload);
          req.end();
        } catch {
          // Crow 없어도 정상 동작
        }
      }
    } catch (err) {
      console.warn('[FixLoopManager] HydrateContext 실패 (비치명적):', err);
    }
  }

  /** 사용자 개입 — 중단 */
  abort(): void {
    if (this.currentSession) {
      this.currentSession.status = 'abandoned';
      this.state = 'abandoned';
      this.clearSessionTimeout();
      this.writeFixRequest();
      this.updateStatusBar();
      NotificationThrottle.showInfo('🛑 VibeZoo: Auto-Fix가 사용자에 의해 중단되었습니다.');
    }
  }

  // ── M3-B: Continuous Improvement Mode (지속적 감시) ──────

  private _watcher: vscode.FileSystemWatcher | null = null;
  private _isWatching = false;
  private _watchDisposables: vscode.Disposable[] = [];
  private _buildInProgress = false;

  /** 파일 저장 감시 시작 — tsc 자동 실행 → 에러 시 auto-fix */
  startWatching(): void {
    if (this._isWatching) {
      NotificationThrottle.showInfo('VibeZoo: 이미 감시 중입니다.');
      return;
    }

    const folders = vscode.workspace.workspaceFolders;
    if (!folders?.[0]) {
      NotificationThrottle.showWarning('VibeZoo: 열려있는 프로젝트가 없어 감시를 시작할 수 없습니다.');
      return;
    }

    const workspaceRoot = folders[0].uri.fsPath;

    // 문서 저장 이벤트 감시 (tsc 자동 실행)
    const onSave = vscode.workspace.onDidSaveTextDocument(async (doc: vscode.TextDocument) => {
      // TS/JS 파일만 처리
      if (!/\.(ts|tsx|js|jsx)$/.test(doc.fileName)) return;
      if (doc.fileName.includes('node_modules')) return;
      if (this._buildInProgress) return;
      this._buildInProgress = true;

      console.log(`[VibeZoo:CIM] File saved: ${doc.fileName}`);
      try {
        const success = await this.runAutoBuild(workspaceRoot);
        if (!success) {
          console.log('[VibeZoo:CIM] Build failed → auto-fix triggered');
        }
      } finally {
        this._buildInProgress = false;
      }
    });

    // 상태바 표시
    const statusItem = vscode.window.createStatusBarItem(
      vscode.StatusBarAlignment.Right,
      100
    );
    statusItem.text = '$(eye) VibeZoo: Watching';
    statusItem.tooltip = '파일 저장 시 자동 tsc 검사';
    statusItem.command = 'vibezoo.stopWatching';
    statusItem.show();

    this._watchDisposables.push(onSave, statusItem);
    this._isWatching = true;

    NotificationThrottle.showInfo(
      '👁️ VibeZoo: Continuous Improvement Mode 시작됨 — 파일 저장 시 자동 tsc 검사'
    );
    console.log('[VibeZoo:CIM] Watching started for', workspaceRoot);
  }

  /** tsc --noEmit 실행 후 결과 반환 */
  private async runAutoBuild(workspaceRoot: string): Promise<boolean> {
    try {
      const { exec } = await import('child_process');
      return new Promise<boolean>((resolve) => {
        const tscPath = /^win/.test(process.platform) ? 'npx.cmd' : 'npx';
        const child = exec(
          `${tscPath} tsc --noEmit`,
          { cwd: workspaceRoot, timeout: 60000 },
          (error, stdout, stderr) => {
            const exitCode = error ? (error as any).code || 1 : 0;
            if (exitCode === 0) {
              console.log('[VibeZoo:CIM] tsc passed');
              resolve(true);
            } else {
              console.log('[VibeZoo:CIM] tsc failed');
              // 진단 정보 수집
              const diagnostics = this.parseTscDiagnostics(stderr || stdout);
              // auto-fix loop 트리거
              this.onBuildFailure(
                diagnostics,
                stderr || stdout,
                'vibezoo:cim:autobuild'
              );
              NotificationThrottle.showWarning(
                `⚠️ VibeZoo: tsc 에러 감지 (${diagnostics.length}개) — 자동 수정 시도 중...`
              );
              resolve(false);
            }
          }
        );
        child?.stdout?.on('data', (data: string) => {
          console.log(`[VibeZoo:CIM] tsc: ${data.trim()}`);
        });
        child?.stderr?.on('data', (data: string) => {
          console.log(`[VibeZoo:CIM] tsc err: ${data.trim()}`);
        });
      });
    } catch (err) {
      console.error('[VibeZoo:CIM] Build error:', err);
      return false;
    }
  }

  /** tsc stderr/stdout → Diagnostic[] 파싱 */
  private parseTscDiagnostics(output: string): import('../types').Diagnostic[] {
    const diagnostics: import('../types').Diagnostic[] = [];
    // TS 에러 패턴: file(line,col): error TS1234: message
    const pattern = /(.+)\((\d+),(\d+)\):\s+(error|warning)\s+(TS\d+):\s+(.+)/g;
    let match: RegExpExecArray | null;
    while ((match = pattern.exec(output)) !== null) {
      diagnostics.push({
        file: match[1].trim(),
        line: parseInt(match[2], 10),
        column: parseInt(match[3], 10),
        severity: match[4] === 'error' ? 'error' : 'warning',
        code: match[5],
        message: match[6].trim(),
        source: 'typescript',
      });
    }
    return diagnostics;
  }

  /** 감시 중지 */
  stopWatching(): void {
    if (!this._isWatching) {
      NotificationThrottle.showInfo('VibeZoo: 현재 감시 중이 아닙니다.');
      return;
    }

    for (const d of this._watchDisposables) {
      d.dispose();
    }
    this._watchDisposables = [];
    this._watcher = null;
    this._isWatching = false;

    NotificationThrottle.showInfo('⏹️ VibeZoo: Continuous Improvement Mode 중지됨');
    console.log('[VibeZoo:CIM] Watching stopped');
  }

  /** 감시 상태 확인 */
  isWatching(): boolean {
    return this._isWatching;
  }

  /** dispose */
  dispose(): void {
    this.clearSessionTimeout();
    this.statusBarMessage?.dispose();
    this.stopWatching();
  }
}
