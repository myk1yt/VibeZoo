"use strict";
// VibeZoo M1-A: FixLoopManager
// Autonomous Fix Loop 상태 머신
// 상태: idle → pending → in_progress → building → resolved/abandoned
// LLM과 ~/.vibezoo-fix-request.json 파일로 통신
// oscillation 감지 (A→B→A 패턴) + maxAttempts 초과 시 give up
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
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.FixLoopManager = exports.getGuardMode = exports.calculateInstability = void 0;
const vscode = __importStar(require("vscode"));
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const os = __importStar(require("os"));
const StatusBarManager_1 = require("../ui/StatusBarManager");
const ConfigService_1 = require("../config/ConfigService");
/**
 * 불안정성 계산: I = α·nedits + β·autocorr + γ·buildFails
 * α=0.35, β=0.45, γ=0.20
 */
function calculateInstability(m) {
    const α = 0.35, β = 0.45, γ = 0.20;
    return α * Math.min(m.nedits / 10, 1) + β * m.autocorr + γ * Math.min(m.buildFails / 5, 1);
}
exports.calculateInstability = calculateInstability;
/**
 * 불안정성 → GuardMode 변환
 * <0.3=active, <0.7=warning, ≥0.7=safe
 */
function getGuardMode(instability) {
    if (instability < 0.3)
        return 'active';
    if (instability < 0.7)
        return 'warning';
    return 'safe';
}
exports.getGuardMode = getGuardMode;
// ── FixLoopManager ───────────────────────────────────────────
class FixLoopManager {
    state = 'idle';
    currentSession = null;
    fixRequestPath;
    maxAttempts;
    SESSION_TIMEOUT_MS = 120000; // 2분
    statusBarMessage = null;
    constructor() {
        this.fixRequestPath = path.join(os.homedir(), '.vibezoo-fix-request.json');
        this.maxAttempts = vscode.workspace
            .getConfiguration('vibezoo')
            .get('build.autoFixMaxAttempts', 3);
    }
    get stateValue() {
        return this.state;
    }
    get currentSessionValue() {
        return this.currentSession;
    }
    /** BuildFeedback이 빌드 실패 시 호출 */
    onBuildFailure(diagnostics, stderr, taskName = 'vibezoo: build') {
        const projectRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath ?? '';
        // 기존 세션이 없거나 resolved 상태면 새 세션 생성
        if (!this.currentSession || this.currentSession.status === 'resolved' || this.currentSession.status === 'abandoned') {
            this.currentSession = this.createSession(projectRoot, taskName);
        }
        // 새 attempt 추가
        const attemptNum = this.currentSession.history.length + 1;
        const attempt = {
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
    markInProgress() {
        if (this.currentSession) {
            this.currentSession.status = 'in_progress';
            this.state = 'in_progress';
            this.writeFixRequest();
            console.log('[VibeZoo] FixLoopManager: → in_progress (LLM 분석 중)');
        }
    }
    /** retry_build() 호출 전 → 상태를 building으로 변경 */
    markBuilding() {
        if (this.currentSession) {
            this.currentSession.status = 'building';
            this.state = 'building';
            this.writeFixRequest();
            console.log('[VibeZoo] FixLoopManager: → building (빌드 실행 중)');
        }
    }
    /** 빌드 성공 시 */
    markResolved() {
        if (this.currentSession) {
            this.currentSession.status = 'resolved';
            this.state = 'resolved';
            this.clearSessionTimeout();
            this.writeFixRequest();
            this.updateStatusBar(true);
            // 성공 메시지
            const attemptCount = this.currentSession.history.length;
            StatusBarManager_1.NotificationThrottle.showInfo(`✅ VibeZoo: ${attemptCount}회 시도 후 빌드 성공!`);
            // fix request 파일 정리 (성공 시)
            this.cleanupFixRequest();
            console.log(`[VibeZoo] FixLoopManager: → resolved (${attemptCount}회 시도 후 성공)`);
        }
    }
    /** 빌드 실패 시 (LLM이 retry_build()로 실패 보고) */
    markBuildFailed(diagnostics, stderr) {
        if (!this.currentSession)
            return;
        // 새 attempt 추가
        const attemptNum = this.currentSession.history.length + 1;
        const attempt = {
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
        const THRESHOLD = 0.5;
        if (instability >= THRESHOLD) {
            // 불안정성 높음 → 즉시 중단 (Recovery/Halt)
            this.currentSession.status = 'abandoned';
            this.state = 'abandoned';
            this.clearSessionTimeout();
            this.writeFixRequest();
            this.updateStatusBar();
            StatusBarManager_1.NotificationThrottle.showWarning(`⚠️ VibeZoo: I_instability=${instability.toFixed(2)} (Guard: Safe/Halt). Auto-Fix를 중단합니다. 수동 확인이 필요합니다.`);
            console.log(`[VibeZoo] FixLoopManager: → abandoned (I_instability=${instability.toFixed(2)} >= ${THRESHOLD})`);
            return;
        }
        // Max attempts 초과
        if (this.shouldGiveUp()) {
            this.currentSession.status = 'abandoned';
            this.state = 'abandoned';
            this.clearSessionTimeout();
            this.writeFixRequest();
            this.updateStatusBar();
            StatusBarManager_1.NotificationThrottle.showWarning(`⚠️ VibeZoo: 최대 ${this.maxAttempts}회 시도 초과. Auto-Fix를 중단합니다.`);
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
    calculateInstability() {
        const h = this.currentSession?.history ?? [];
        if (h.length === 0)
            return 0;
        // nedits: 누적 편집 횟수 (attempt 수)
        const nedits = h.length;
        // autocorr: 자기상관계수 — 동일 에러 시그니처 반복률
        let sameSigCount = 0;
        let totalPairs = 0;
        for (let i = 1; i < h.length; i++) {
            const sig1 = this.errorSignature(h[i - 1].diagnostics);
            const sig2 = this.errorSignature(h[i].diagnostics);
            totalPairs++;
            if (sig1 === sig2)
                sameSigCount++;
        }
        const autocorr = totalPairs > 0 ? sameSigCount / totalPairs : 0;
        // buildFails: 연속 빌드 실패 횟수
        let buildFails = 0;
        for (let i = h.length - 1; i >= 0; i--) {
            if (h[i].exitCode !== 0)
                buildFails++;
            else
                break;
        }
        return calculateInstability({ nedits, autocorr, buildFails });
    }
    // isOscillating()은 calculateInstability()로 대체됨
    _oscillationCompat() {
        // 이전 호환성: calculateInstability()가 active를 반환하면 oscillation
        return this.calculateInstability() >= 0.3;
    }
    /** Give up 조건 */
    shouldGiveUp() {
        if (!this.currentSession)
            return false;
        if (this.currentSession.history.length >= this.maxAttempts)
            return true;
        if (this.calculateInstability() >= 0.5)
            return true;
        return false;
    }
    /** 에러 시그니처 생성 (파일+코드 기준) */
    errorSignature(diagnostics) {
        return diagnostics
            .map(d => `${d.file}:${d.code}`)
            .sort()
            .join('|');
    }
    /** 세션 생성 */
    createSession(projectRoot, taskName) {
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
    writeFixRequest() {
        if (!this.currentSession)
            return;
        try {
            // Crow recall 결과도 포함 (있으면)
            const pastFixes = this.currentSession.history
                .filter(a => a.fixApplied)
                .map(a => ({
                attempt: a.attempt,
                fixApplied: a.fixApplied,
                timestamp: a.timestamp,
            }));
            const data = {
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
        }
        catch (err) {
            console.error('[VibeZoo] Failed to write fix request:', err);
        }
    }
    /** Fix request 파일 정리 */
    cleanupFixRequest() {
        try {
            if (fs.existsSync(this.fixRequestPath)) {
                fs.unlinkSync(this.fixRequestPath);
            }
        }
        catch { /* ignore */ }
    }
    /** StatusBar 업데이트 */
    updateStatusBar(success = false) {
        // 기존 메시지 제거
        this.statusBarMessage?.dispose();
        if (!this.currentSession)
            return;
        const attempt = this.currentSession.attempt;
        const max = this.currentSession.maxAttempts;
        if (success) {
            this.statusBarMessage = vscode.window.setStatusBarMessage(`$(check) VibeZoo: Auto-Fix 성공 (${attempt}회 시도)`, 8000);
        }
        else if (this.currentSession.status === 'abandoned') {
            this.statusBarMessage = vscode.window.setStatusBarMessage(`$(error) VibeZoo: Auto-Fix 중단됨`, 8000);
        }
        else if (this.currentSession.status === 'pending') {
            this.statusBarMessage = vscode.window.setStatusBarMessage(`$(warning) VibeZoo: 빌드 실패 — [자동 수정]`, 10000);
        }
        else if (this.currentSession.status === 'in_progress') {
            this.statusBarMessage = vscode.window.setStatusBarMessage(`$(sync~spin) VibeZoo: Auto-Fix ${attempt}/${max} 분석 중...`, 5000);
        }
        else if (this.currentSession.status === 'building') {
            this.statusBarMessage = vscode.window.setStatusBarMessage(`$(sync~spin) VibeZoo: Auto-Fix ${attempt}/${max} 빌드 중...`, 5000);
        }
    }
    /** 세션 타임아웃 리셋 */
    resetSessionTimeout() {
        this.clearSessionTimeout();
        if (!this.currentSession)
            return;
        this.currentSession.timeoutId = setTimeout(() => {
            if (this.currentSession && this.currentSession.status !== 'resolved' && this.currentSession.status !== 'abandoned') {
                this.currentSession.status = 'abandoned';
                this.state = 'abandoned';
                this.writeFixRequest();
                this.updateStatusBar();
                console.log('[VibeZoo] FixLoopManager: → abandoned (timeout)');
                StatusBarManager_1.NotificationThrottle.showWarning('⏰ VibeZoo: Auto-Fix 시간 초과 (120초). 수동 확인이 필요합니다.');
            }
        }, this.SESSION_TIMEOUT_MS);
    }
    /** 세션 타임아웃 제거 */
    clearSessionTimeout() {
        if (this.currentSession?.timeoutId) {
            clearTimeout(this.currentSession.timeoutId);
            this.currentSession.timeoutId = undefined;
        }
    }
    /** 사용자 개입 — 일시정지 */
    pause() {
        if (this.currentSession && (this.state === 'in_progress' || this.state === 'pending')) {
            this.currentSession.status = 'awaiting_user';
            this.state = 'awaiting_user';
            this.writeFixRequest();
            this.updateStatusBar();
            StatusBarManager_1.NotificationThrottle.showInfo('⏸️ VibeZoo: Auto-Fix가 일시정지되었습니다.');
        }
    }
    /** 사용자 개입 — 재개 */
    async resume() {
        if (this.currentSession && this.state === 'awaiting_user') {
            // Context Hydration: freeze 상태와 현재 파일 비교
            await this.hydrateContext();
            this.currentSession.status = 'in_progress';
            this.state = 'in_progress';
            this.writeFixRequest();
            this.updateStatusBar();
            StatusBarManager_1.NotificationThrottle.showInfo('▶️ VibeZoo: Auto-Fix가 재개되었습니다.');
        }
    }
    /**
     * Context Hydration: freeze 시점과 현재 파일 상태를 비교하여
     * 변경 감지 시 Crow context 레지스터에 저장.
     * resume 시 자동 호출되어 AST Delta 추적.
     */
    async hydrateContext() {
        if (!this.currentSession)
            return;
        const projectRoot = this.currentSession.projectRoot;
        if (!projectRoot)
            return;
        try {
            // freeze 시점의 fix request 기록과 현재 파일 상태 비교
            const freezeSnapshot = this.currentSession.history[this.currentSession.history.length - 1];
            if (!freezeSnapshot)
                return;
            // 간소화: 수정된 파일 목록 diff → Crow ingest
            const touchedFiles = new Set();
            for (const attempt of this.currentSession.history) {
                for (const diag of attempt.diagnostics) {
                    if (diag.file)
                        touchedFiles.add(diag.file);
                }
            }
            if (touchedFiles.size > 0) {
                const fileList = Array.from(touchedFiles).slice(0, 20);
                console.log(`[FixLoopManager] HydrateContext: ${fileList.length} 파일 변경 감지됨`);
                // Crow ingest를 시도 (실패해도 무관)
                try {
                    // 로컬 HTTP 요청으로 Crow에 저장
                    const http = await Promise.resolve().then(() => __importStar(require('http')));
                    const payload = JSON.stringify({
                        content: `FixLoop resume detected changes in ${fileList.length} files: ${fileList.join(', ')}`,
                        register: 'context'
                    });
                    const req = http.request({
                        hostname: ConfigService_1.ConfigService.getHost(),
                        port: ConfigService_1.ConfigService.getCrowPort(),
                        path: '/ingest',
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json', 'Content-Length': payload.length }
                    });
                    req.write(payload);
                    req.end();
                }
                catch {
                    // Crow 없어도 정상 동작
                }
            }
        }
        catch (err) {
            console.warn('[FixLoopManager] HydrateContext 실패 (비치명적):', err);
        }
    }
    /** 사용자 개입 — 중단 */
    abort() {
        if (this.currentSession) {
            this.currentSession.status = 'abandoned';
            this.state = 'abandoned';
            this.clearSessionTimeout();
            this.writeFixRequest();
            this.updateStatusBar();
            StatusBarManager_1.NotificationThrottle.showInfo('🛑 VibeZoo: Auto-Fix가 사용자에 의해 중단되었습니다.');
        }
    }
    // ── M3-B: Continuous Improvement Mode (지속적 감시) ──────
    _watcher = null;
    _isWatching = false;
    _watchDisposables = [];
    _buildInProgress = false;
    /** 파일 저장 감시 시작 — tsc 자동 실행 → 에러 시 auto-fix */
    startWatching() {
        if (this._isWatching) {
            StatusBarManager_1.NotificationThrottle.showInfo('VibeZoo: 이미 감시 중입니다.');
            return;
        }
        const folders = vscode.workspace.workspaceFolders;
        if (!folders?.[0]) {
            StatusBarManager_1.NotificationThrottle.showWarning('VibeZoo: 열려있는 프로젝트가 없어 감시를 시작할 수 없습니다.');
            return;
        }
        const workspaceRoot = folders[0].uri.fsPath;
        // 문서 저장 이벤트 감시 (tsc 자동 실행)
        const onSave = vscode.workspace.onDidSaveTextDocument(async (doc) => {
            // TS/JS 파일만 처리
            if (!/\.(ts|tsx|js|jsx)$/.test(doc.fileName))
                return;
            if (doc.fileName.includes('node_modules'))
                return;
            if (this._buildInProgress)
                return;
            this._buildInProgress = true;
            console.log(`[VibeZoo:CIM] File saved: ${doc.fileName}`);
            try {
                const success = await this.runAutoBuild(workspaceRoot);
                if (!success) {
                    console.log('[VibeZoo:CIM] Build failed → auto-fix triggered');
                }
            }
            finally {
                this._buildInProgress = false;
            }
        });
        // 상태바 표시
        const statusItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
        statusItem.text = '$(eye) VibeZoo: Watching';
        statusItem.tooltip = vscode.l10n.t('Auto tsc check on file save');
        statusItem.command = 'vibezoo.stopWatching';
        statusItem.show();
        this._watchDisposables.push(onSave, statusItem);
        this._isWatching = true;
        StatusBarManager_1.NotificationThrottle.showInfo('👁️ VibeZoo: Continuous Improvement Mode 시작됨 — 파일 저장 시 자동 tsc 검사');
        console.log('[VibeZoo:CIM] Watching started for', workspaceRoot);
    }
    /** tsc --noEmit 실행 후 결과 반환 */
    async runAutoBuild(workspaceRoot) {
        try {
            const { exec } = await Promise.resolve().then(() => __importStar(require('child_process')));
            return new Promise((resolve) => {
                const tscPath = /^win/.test(process.platform) ? 'npx.cmd' : 'npx';
                const child = exec(`${tscPath} tsc --noEmit`, { cwd: workspaceRoot, timeout: 60000 }, (error, stdout, stderr) => {
                    const exitCode = error ? error.code || 1 : 0;
                    if (exitCode === 0) {
                        console.log('[VibeZoo:CIM] tsc passed');
                        resolve(true);
                    }
                    else {
                        console.log('[VibeZoo:CIM] tsc failed');
                        // 진단 정보 수집
                        const diagnostics = this.parseTscDiagnostics(stderr || stdout);
                        // auto-fix loop 트리거
                        this.onBuildFailure(diagnostics, stderr || stdout, 'vibezoo:cim:autobuild');
                        StatusBarManager_1.NotificationThrottle.showWarning(`⚠️ VibeZoo: tsc 에러 감지 (${diagnostics.length}개) — 자동 수정 시도 중...`);
                        resolve(false);
                    }
                });
                child?.stdout?.on('data', (data) => {
                    console.log(`[VibeZoo:CIM] tsc: ${data.trim()}`);
                });
                child?.stderr?.on('data', (data) => {
                    console.log(`[VibeZoo:CIM] tsc err: ${data.trim()}`);
                });
            });
        }
        catch (err) {
            console.error('[VibeZoo:CIM] Build error:', err);
            return false;
        }
    }
    /** tsc stderr/stdout → Diagnostic[] 파싱 */
    parseTscDiagnostics(output) {
        const diagnostics = [];
        // TS 에러 패턴: file(line,col): error TS1234: message
        const pattern = /(.+)\((\d+),(\d+)\):\s+(error|warning)\s+(TS\d+):\s+(.+)/g;
        let match;
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
    stopWatching() {
        if (!this._isWatching) {
            StatusBarManager_1.NotificationThrottle.showInfo('VibeZoo: 현재 감시 중이 아닙니다.');
            return;
        }
        for (const d of this._watchDisposables) {
            d.dispose();
        }
        this._watchDisposables = [];
        this._watcher = null;
        this._isWatching = false;
        StatusBarManager_1.NotificationThrottle.showInfo('⏹️ VibeZoo: Continuous Improvement Mode 중지됨');
        console.log('[VibeZoo:CIM] Watching stopped');
    }
    /** 감시 상태 확인 */
    isWatching() {
        return this._isWatching;
    }
    /** dispose */
    dispose() {
        this.clearSessionTimeout();
        this.statusBarMessage?.dispose();
        this.stopWatching();
    }
}
exports.FixLoopManager = FixLoopManager;
//# sourceMappingURL=FixLoopManager.js.map