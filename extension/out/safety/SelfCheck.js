"use strict";
// VibeZoo v0.13.0: SelfCheck — 시스템 자가진단 + AlarmMonitor
// Phase 0 최우선 구축: NotificationThrottle보다 먼저 사용 가능해야 함
//
// SelfChecker:
//   - runAll(): 모든 진단 실행 → SelfCheckReport 반환
//   - checkBridgeConnectivity(): Bridge :9027/health 확인
//   - checkCrowHealth(): Crow :9020/health 확인
//   - checkMcpConfig(): .roo/mcp.json 무결성 확인
//   - checkWhiteboardFiles(): 화이트보드 JSON 파일 무결성
//   - checkYoctoDirectory(): 백업 디렉토리 권한/공간 확인
//   - autoRecover(failure): 감지된 문제 자동 복구 시도
//
// AlarmMonitor:
//   60초 슬라이딩 윈도우로 알람 횟수 추적
//   30회/분 초과 → 강제 throttle + 로그 경고
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
exports.SelfChecker = exports.getGuardGitManager = exports.setGuardGitManager = exports.alarmMonitor = exports.AlarmMonitor = void 0;
const vscode = __importStar(require("vscode"));
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const os = __importStar(require("os"));
const ConfigService_1 = require("../config/ConfigService");
// ── AlarmMonitor ──────────────────────────────────────────────
class AlarmMonitor {
    alarmLog = [];
    WINDOW_MS = 60000; // 60초 슬라이딩 윈도우
    MAX_ALARMS = 30; // 분당 30회
    _throttled = false;
    _throttleUntil = 0;
    /** 알람 등록. true 반환 = 제한 초과로 무시됨 */
    record(message) {
        const now = Date.now();
        // throttle 상태 체크
        if (this._throttled) {
            if (now < this._throttleUntil) {
                console.warn(`[AlarmMonitor] THROTTLED: ${message}`);
                return true; // 무시됨
            }
            this._throttled = false;
        }
        // 슬라이딩 윈도우 정리
        this.alarmLog = this.alarmLog.filter(e => now - e.timestamp < this.WINDOW_MS);
        this.alarmLog.push({ timestamp: now, message });
        // 임계값 초과 체크
        if (this.alarmLog.length > this.MAX_ALARMS) {
            this._throttled = true;
            this._throttleUntil = now + 30000; // 30초 강제 throttle
            console.error(`[AlarmMonitor] CRITICAL: 분당 ${this.alarmLog.length}회 알람 발생! 30초간 throttle. 마지막 메시지: ${message}`);
            return true; // 무시됨
        }
        return false; // 정상 등록
    }
    get throttled() {
        if (this._throttled && Date.now() >= this._throttleUntil) {
            this._throttled = false;
        }
        return this._throttled;
    }
    get recentAlarmCount() {
        const now = Date.now();
        this.alarmLog = this.alarmLog.filter(e => now - e.timestamp < this.WINDOW_MS);
        return this.alarmLog.length;
    }
    reset() {
        this.alarmLog = [];
        this._throttled = false;
        this._throttleUntil = 0;
    }
}
exports.AlarmMonitor = AlarmMonitor;
// ── 전역 싱글톤 인스턴스 ──────────────────────────────────────
exports.alarmMonitor = new AlarmMonitor();
// ── GuardGitManager 싱글톤 접근자 ──────────────────────────
let _guardGitManager = null;
/** GuardGitManager 인스턴스 등록 (extension.ts에서 호출) */
function setGuardGitManager(mgr) {
    _guardGitManager = mgr;
}
exports.setGuardGitManager = setGuardGitManager;
/** GuardGitManager 인스턴스 조회 */
function getGuardGitManager() {
    return _guardGitManager;
}
exports.getGuardGitManager = getGuardGitManager;
// ── SelfChecker ───────────────────────────────────────────────
class SelfChecker {
    version;
    constructor(version = '0.13.0') {
        this.version = version;
    }
    /** 모든 진단 실행 */
    async runAll() {
        const checks = [];
        // 병렬 실행 가능한 체크
        const results = await Promise.allSettled([
            this.checkBridgeConnectivity(),
            this.checkCrowHealth(),
            this.checkMcpConfig(),
            this.checkWhiteboardFiles(),
            this.checkYoctoDirectory(),
            this.checkZooCodeCompatibility(),
            this.checkNotificationHealth(),
            this.checkGitGuardIntegrity(),
        ]);
        for (const result of results) {
            if (result.status === 'fulfilled') {
                checks.push(result.value);
            }
            else {
                checks.push({
                    name: 'Unknown Check',
                    status: 'failed',
                    message: `체크 중 예외 발생: ${result.reason}`,
                });
            }
        }
        // 종합 상태 판정
        const failures = checks.filter(c => c.status === 'failed').length;
        const warnings = checks.filter(c => c.status === 'warning').length;
        let overall = 'healthy';
        if (failures > 0)
            overall = 'critical';
        else if (warnings > 0)
            overall = 'degraded';
        const report = {
            overall,
            checks,
            timestamp: Date.now(),
            version: this.version,
        };
        console.log(`[SelfCheck] ✅ 진단 완료: overall=${overall}, checks=${checks.length}, failures=${failures}, warnings=${warnings}`);
        return report;
    }
    /** Bridge :9027/health 확인 */
    async checkBridgeConnectivity() {
        const base = {
            name: 'Bridge Connectivity',
            status: 'passed',
            message: 'MCP Bridge 연결됨',
        };
        try {
            const controller = new AbortController();
            const timeout = setTimeout(() => controller.abort(), 5000);
            const resp = await fetch(ConfigService_1.ConfigService.getBridgeUrl('/health'), {
                signal: controller.signal,
            });
            clearTimeout(timeout);
            if (resp.ok) {
                const data = await resp.json();
                base.detail = `version=${data.version || '?'}, crow=${data.crow ? 'connected' : 'disconnected'}`;
                return base;
            }
            base.status = 'failed';
            base.message = `Bridge 응답 오류: HTTP ${resp.status}`;
            base.autoRecoverable = true;
            return base;
        }
        catch (err) {
            base.status = 'failed';
            base.message = `Bridge 연결 실패: ${err.name === 'AbortError' ? '5초 타임아웃' : err.message}`;
            base.autoRecoverable = true;
            return base;
        }
    }
    /** Crow :9020/health 확인 */
    async checkCrowHealth() {
        const base = {
            name: 'Crow Memory Health',
            status: 'passed',
            message: 'Crow Memory 연결됨',
        };
        try {
            const controller = new AbortController();
            const timeout = setTimeout(() => controller.abort(), 3000);
            const resp = await fetch(ConfigService_1.ConfigService.getCrowUrl('/health'), {
                signal: controller.signal,
            });
            clearTimeout(timeout);
            if (resp.ok) {
                return base;
            }
            base.status = 'warning';
            base.message = `Crow 응답 오류: HTTP ${resp.status}`;
            return base;
        }
        catch (err) {
            base.status = 'warning';
            base.message = `Crow 연결 실패: ${err.name === 'AbortError' ? '3초 타임아웃' : err.message}`;
            return base;
        }
    }
    /** .roo/mcp.json 무결성 확인 */
    async checkMcpConfig() {
        const base = {
            name: 'MCP Configuration',
            status: 'passed',
            message: '.roo/mcp.json 정상',
        };
        try {
            const folders = vscode.workspace.workspaceFolders;
            if (!folders?.[0]) {
                base.status = 'warning';
                base.message = '열린 워크스페이스 없음 — MCP 설정 확인 불가';
                return base;
            }
            const mcpPath = path.join(folders[0].uri.fsPath, '.roo', 'mcp.json');
            if (!fs.existsSync(mcpPath)) {
                base.status = 'warning';
                base.message = '.roo/mcp.json 파일이 존재하지 않음';
                base.autoRecoverable = true;
                return base;
            }
            const raw = fs.readFileSync(mcpPath, 'utf-8');
            const config = JSON.parse(raw);
            if (!config.mcpServers) {
                base.status = 'failed';
                base.message = '.roo/mcp.json에 mcpServers 키가 없음';
                base.autoRecoverable = true;
                return base;
            }
            if (!config.mcpServers.vibezoo) {
                base.status = 'failed';
                base.message = '.roo/mcp.json에 vibezoo 서버 정의가 없음';
                base.autoRecoverable = true;
                return base;
            }
            const vibezooConfig = config.mcpServers.vibezoo;
            const expectedUrl = ConfigService_1.ConfigService.getBridgeUrl('/sse');
            if (vibezooConfig.url !== expectedUrl) {
                base.status = 'warning';
                base.message = `vibezoo 서버 URL이 예상과 다름: ${vibezooConfig.url} (expected: ${expectedUrl})`;
                return base;
            }
            // 중복 서버 정의 검사
            const serverKeys = Object.keys(config.mcpServers);
            if (serverKeys.filter(k => k === 'vibezoo').length > 1) {
                base.status = 'warning';
                base.message = 'vibezoo 서버가 중복 정의됨';
                return base;
            }
            base.detail = `서버: ${serverKeys.join(', ')}`;
            return base;
        }
        catch (err) {
            base.status = 'failed';
            base.message = `.roo/mcp.json 파싱 오류: ${err.message}`;
            base.autoRecoverable = true;
            return base;
        }
    }
    /** 화이트보드 JSON 파일 무결성 */
    async checkWhiteboardFiles() {
        const base = {
            name: 'Whiteboard Files',
            status: 'passed',
            message: '화이트보드 파일 정상',
        };
        try {
            const wbFile = path.join(os.homedir(), '.vibezoo-whiteboard.json');
            if (!fs.existsSync(wbFile)) {
                base.status = 'passed';
                base.message = '화이트보드 파일 없음 (신규 상태)';
                return base;
            }
            const raw = fs.readFileSync(wbFile, 'utf-8');
            JSON.parse(raw); // 유효성 검사만
            return base;
        }
        catch (err) {
            base.status = 'warning';
            base.message = `화이트보드 JSON 파싱 오류: ${err.message}`;
            return base;
        }
    }
    /** 백업 디렉토리 권한/공간 확인 */
    async checkYoctoDirectory() {
        const base = {
            name: 'Yocto Backup Directory',
            status: 'passed',
            message: '백업 디렉토리 정상',
        };
        try {
            const yoctoDir = path.join(os.homedir(), '.zoo-code', 'yocto');
            if (!fs.existsSync(yoctoDir)) {
                base.status = 'warning';
                base.message = 'yocto 디렉토리가 존재하지 않음 (생성 필요)';
                base.autoRecoverable = true;
                return base;
            }
            // 쓰기 권한 확인
            const testFile = path.join(yoctoDir, '.selfcheck-tmp');
            fs.writeFileSync(testFile, 'test', 'utf-8');
            fs.unlinkSync(testFile);
            // 디스크 공간 확인 (Windows: root 디렉토리 사용)
            let freeBytes = 0;
            try {
                const rootDir = path.parse(yoctoDir).root;
                // Windows에서 디스크 공간 확인은 native addon 필요 — 간략 체크
                const stats = fs.statSync(rootDir);
                freeBytes = stats.size > 0 ? stats.size : 1073741824; // fallback 1GB
            }
            catch {
                freeBytes = 1073741824; // fallback
            }
            if (freeBytes < 104857600) { // 100MB 미만
                base.status = 'warning';
                base.message = `디스크 공간 부족: ${(freeBytes / 1024 / 1024).toFixed(0)}MB`;
                return base;
            }
            base.detail = `디렉토리: ${yoctoDir}`;
            return base;
        }
        catch (err) {
            base.status = 'failed';
            base.message = `yocto 디렉토리 확인 실패: ${err.message}`;
            return base;
        }
    }
    /** Zoo Code 확장 호환성 확인 */
    async checkZooCodeCompatibility() {
        const base = {
            name: 'Zoo Code Compatibility',
            status: 'passed',
            message: 'Zoo Code 확장 호환성 정상',
        };
        try {
            const zooExt = vscode.extensions.getExtension('zoocodeorganization.zoo-code');
            if (!zooExt) {
                base.status = 'warning';
                base.message = 'Zoo Code 확장이 설치되어 있지 않음 (선택 사항)';
                return base;
            }
            const version = zooExt.packageJSON?.version || 'unknown';
            base.detail = `버전: ${version}`;
            return base;
        }
        catch (err) {
            base.status = 'warning';
            base.message = `Zoo Code 확인 중 오류: ${err.message}`;
            return base;
        }
    }
    /** 알람 카운터 헬스 체크 */
    async checkNotificationHealth() {
        const base = {
            name: 'Notification Health',
            status: 'passed',
            message: '알람 시스템 정상',
        };
        try {
            const recentCount = exports.alarmMonitor.recentAlarmCount;
            const isThrottled = exports.alarmMonitor.throttled;
            if (isThrottled) {
                base.status = 'warning';
                base.message = `알람이 throttle 중입니다 (최근 ${recentCount}회/분)`;
                return base;
            }
            if (recentCount > 20) {
                base.status = 'warning';
                base.message = `알람 빈도 높음: 최근 ${recentCount}회`;
                return base;
            }
            base.detail = `최근 알람: ${recentCount}회 (limit: 30/분)`;
            return base;
        }
        catch (err) {
            base.status = 'failed';
            base.message = `알람 시스템 확인 실패: ${err.message}`;
            return base;
        }
    }
    /** Git Guard 무결성 진단 */
    async checkGitGuardIntegrity() {
        const base = {
            name: 'Git Guard Integrity',
            status: 'passed',
            message: '.git 디렉토리 보호 상태 정상',
        };
        // 싱글톤 접근 (전역 변수 또는 import된 getter 사용)
        const guardManager = _guardGitManager;
        if (!guardManager) {
            base.status = 'warning';
            base.message = 'Guard.git이 초기화되지 않음';
            return base;
        }
        const integrities = await guardManager.checkIntegrity();
        // C4: 멀티 루트 — 모든 경로 검사
        const failedPaths = integrities.filter((i) => !i.exists);
        const unprotectedPaths = integrities.filter((i) => i.exists && !i.protected && guardManager.isEnabled());
        if (failedPaths.length > 0) {
            base.status = 'failed';
            base.message = `${failedPaths.length}개 .git 디렉토리가 존재하지 않음`;
            base.autoRecoverable = true;
            return base;
        }
        if (unprotectedPaths.length > 0) {
            base.status = 'warning';
            base.message = 'Guard가 활성화되어 있으나 ACL이 적용되지 않은 .git 경로 있음';
            base.autoRecoverable = true;
            return base;
        }
        base.detail = integrities.map((i) => `${i.headRef} (objects:${i.objectCount}, refs:${i.refCount})`).join('; ');
        return base;
    }
    /** 감지된 문제 자동 복구 시도 */
    async autoRecover(failure) {
        if (!failure.autoRecoverable)
            return false;
        console.log(`[SelfCheck:Recovery] 자동 복구 시도: ${failure.name} — ${failure.message}`);
        try {
            switch (failure.name) {
                case 'Bridge Connectivity': {
                    // Bridge 재시작은 SubagentManager에서 처리
                    // 여기서는 재시도 신호만
                    const resp = await fetch('http://localhost:9027/health', {
                        signal: AbortSignal.timeout(5000),
                    });
                    return resp.ok;
                }
                case 'MCP Configuration': {
                    await this.autoConfigureMCP();
                    return true;
                }
                case 'Yocto Backup Directory': {
                    const yoctoDir = path.join(os.homedir(), '.zoo-code', 'yocto');
                    fs.mkdirSync(yoctoDir, { recursive: true });
                    return true;
                }
                default:
                    return false;
            }
        }
        catch (err) {
            console.error(`[SelfCheck:Recovery] 복구 실패: ${failure.name}`, err);
            return false;
        }
    }
    /** MCP 설정 자동 복구 */
    async autoConfigureMCP() {
        const folders = vscode.workspace.workspaceFolders;
        if (!folders?.[0])
            return;
        const root = folders[0].uri.fsPath;
        const zooMCPDir = path.join(root, '.roo');
        const zooMCPPath = path.join(zooMCPDir, 'mcp.json');
        fs.mkdirSync(zooMCPDir, { recursive: true });
        let existingConfig = { mcpServers: {} };
        try {
            if (fs.existsSync(zooMCPPath)) {
                const raw = await fs.promises.readFile(zooMCPPath, 'utf-8');
                if (raw.trim()) {
                    existingConfig = JSON.parse(raw);
                }
            }
        }
        catch (err) {
            console.warn(`[SelfCheck:Recovery] 기존 mcp.json 파싱 실패 (초기화 진행): ${err.message}`);
            existingConfig = { mcpServers: {} };
        }
        if (!existingConfig.mcpServers || typeof existingConfig.mcpServers !== 'object') {
            existingConfig.mcpServers = {};
        }
        existingConfig.mcpServers.vibezoo = {
            url: ConfigService_1.ConfigService.getBridgeUrl('/sse'),
            transport: 'sse',
        };
        try {
            await fs.promises.writeFile(zooMCPPath, JSON.stringify(existingConfig, null, 2), 'utf-8');
            console.log(`[SelfCheck:Recovery] MCP 설정 병합 및 재구성 완료: ${zooMCPPath}`);
        }
        catch (err) {
            console.error(`[SelfCheck:Recovery] MCP 설정 파일 쓰기 실패: ${err.message}`);
        }
    }
    /** 자가진단 결과를 마크다운으로 포맷팅 */
    formatReport(report) {
        const lines = [];
        lines.push(`# 🔍 VibeZoo Self Check Report`);
        lines.push(`> Version: ${report.version} | Timestamp: ${new Date(report.timestamp).toISOString()}`);
        lines.push('');
        const overallIcon = report.overall === 'healthy' ? '✅' : report.overall === 'degraded' ? '⚠️' : '❌';
        lines.push(`## Overall Status: ${overallIcon} ${report.overall.toUpperCase()}`);
        lines.push('');
        lines.push('## Checks');
        lines.push('');
        for (const check of report.checks) {
            const icon = check.status === 'passed' ? '✅' : check.status === 'warning' ? '⚠️' : '❌';
            lines.push(`### ${icon} ${check.name}`);
            lines.push(`**Status**: ${check.status}`);
            lines.push(`**Message**: ${check.message}`);
            if (check.detail)
                lines.push(`**Detail**: ${check.detail}`);
            if (check.autoRecoverable)
                lines.push(`**Auto-Recoverable**: Yes`);
            lines.push('');
        }
        const failed = report.checks.filter(c => c.status === 'failed').length;
        const warnings = report.checks.filter(c => c.status === 'warning').length;
        if (failed > 0 || warnings > 0) {
            lines.push('## Recommendations');
            lines.push('');
            if (failed > 0)
                lines.push(`- ❌ ${failed}개 실패 항목 — 자동 복구 가능한 항목은 "VibeZoo: Self Check" 명령어로 재시도`);
            if (warnings > 0)
                lines.push(`- ⚠️ ${warnings}개 경고 — 필요 시 수동 확인`);
            lines.push('');
        }
        lines.push('---');
        lines.push(`*Report generated by VibeZoo SelfChecker v${report.version}*`);
        return lines.join('\n');
    }
}
exports.SelfChecker = SelfChecker;
//# sourceMappingURL=SelfCheck.js.map