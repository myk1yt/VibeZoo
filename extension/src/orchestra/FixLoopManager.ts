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
      vscode.window.showInformationMessage(
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

    // Oscillation 체크
    if (this.isOscillating()) {
      this.currentSession.status = 'abandoned';
      this.state = 'abandoned';
      this.clearSessionTimeout();
      this.writeFixRequest();
      this.updateStatusBar();
      vscode.window.showWarningMessage(
        '⚠️ VibeZoo: A→B→A 패턴 감지. Auto-Fix를 중단합니다. 수동 확인이 필요합니다.'
      );
      console.log('[VibeZoo] FixLoopManager: → abandoned (oscillation 감지)');
      return;
    }

    // Max attempts 초과
    if (this.shouldGiveUp()) {
      this.currentSession.status = 'abandoned';
      this.state = 'abandoned';
      this.clearSessionTimeout();
      this.writeFixRequest();
      this.updateStatusBar();
      vscode.window.showWarningMessage(
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

  /** Oscillation 감지: A→B→A 패턴 */
  isOscillating(): boolean {
    const h = this.currentSession?.history ?? [];
    if (h.length < 4) return false;

    // 최근 4회의 에러 시그니처 추출
    const recent = h.slice(-4);
    const sigs = recent.map(a => this.errorSignature(a.diagnostics));

    // A→B→A→B 또는 A→B→C→A 패턴 체크
    // sigs[0] === sigs[2] (첫 번째와 세 번째가 동일)
    // 또는 sigs[1] === sigs[3] (두 번째와 네 번째가 동일)
    if (sigs[0] === sigs[2] || sigs[1] === sigs[3]) {
      return true;
    }

    // 반복 에러: 동일한 파일/코드 에러가 2회 연속
    if (h.length >= 2) {
      const lastTwo = h.slice(-2);
      const sig1 = this.errorSignature(lastTwo[0].diagnostics);
      const sig2 = this.errorSignature(lastTwo[1].diagnostics);
      if (sig1 === sig2) {
        return true;
      }
    }

    return false;
  }

  /** Give up 조건 */
  shouldGiveUp(): boolean {
    if (!this.currentSession) return false;
    if (this.currentSession.history.length >= this.maxAttempts) return true;
    if (this.isOscillating()) return true;
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
        vscode.window.showWarningMessage(
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
      vscode.window.showInformationMessage('⏸️ VibeZoo: Auto-Fix가 일시정지되었습니다.');
    }
  }

  /** 사용자 개입 — 재개 */
  resume(): void {
    if (this.currentSession && this.state === 'awaiting_user') {
      this.currentSession.status = 'in_progress';
      this.state = 'in_progress';
      this.writeFixRequest();
      this.updateStatusBar();
      vscode.window.showInformationMessage('▶️ VibeZoo: Auto-Fix가 재개되었습니다.');
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
      vscode.window.showInformationMessage('🛑 VibeZoo: Auto-Fix가 사용자에 의해 중단되었습니다.');
    }
  }

  /** dispose */
  dispose(): void {
    this.clearSessionTimeout();
    this.statusBarMessage?.dispose();
  }
}
