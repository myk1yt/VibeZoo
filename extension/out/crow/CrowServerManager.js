"use strict";
// VibeZoo: Crow Memory 연결 감지 관리자
// VibeZoo는 Crow 서버를 직접 실행하지 않는다.
// Crow는 Zoo Code가 관리하는 외부 독립 시스템이다.
// VibeZoo는 Zoo Code의 Crow 서버 연결 상태를 감지만 한다.
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
exports.CrowServerManager = void 0;
const vscode = __importStar(require("vscode"));
const ConfigService_1 = require("../config/ConfigService");
class CrowServerManager {
    config;
    healthCheckTimer = null;
    _onStatusChange = new vscode.EventEmitter();
    onStatusChange = this._onStatusChange.event;
    /** 마지막 healthCheck 결과 캐시 (외부에서 재사용 가능) */
    _lastHealthy = false;
    /** Bridge 통합 모드에서 직접 healthy 상태 설정 */
    markHealthy() {
        this._lastHealthy = true;
        this._onStatusChange.fire({ connected: true });
        this.startHealthCheck();
    }
    constructor() {
        this.config = {
            port: vscode.workspace.getConfiguration('vibezoo').get('crow.port', 9020),
            healthCheckIntervalMs: 30000,
        };
    }
    /** 마지막 healthCheck 결과 */
    get lastHealthy() {
        return this._lastHealthy;
    }
    /** Crow 서버 헬스체크 (HTTP GET /health) */
    async healthCheck() {
        try {
            const controller = new AbortController();
            const timeout = setTimeout(() => controller.abort(), 3000);
            const url = ConfigService_1.ConfigService.getCrowUrl('/health');
            const response = await fetch(url, {
                signal: controller.signal,
            });
            clearTimeout(timeout);
            const ok = response.ok;
            console.log(`[VibeZoo] Crow healthCheck → ${url} → ${ok ? '✅ 성공' : '❌ 실패'} (status=${response.status})`);
            return ok;
        }
        catch (err) {
            console.log(`[VibeZoo] Crow healthCheck → ${ConfigService_1.ConfigService.getCrowUrl('/health')} → 💥 예외: ${err.message}`);
            return false;
        }
    }
    /** Zoo Code의 Crow 서버 연결 확인 (기존 서버 재시작 없이 감지만) */
    async reconnect(maxRetries = 3) {
        for (let attempt = 0; attempt < maxRetries; attempt++) {
            this._onStatusChange.fire({ connected: false });
            const healthy = await this.healthCheck();
            if (healthy) {
                this._lastHealthy = true;
                console.log(`[VibeZoo] ✅ Zoo Code Crow 서버 연결 확인: 포트 ${this.config.port}`);
                this.startHealthCheck();
                this._onStatusChange.fire({ connected: true });
                return true;
            }
            console.log(`[VibeZoo] ⏳ Zoo Code Crow 서버 응답 없음 (${attempt + 1}/${maxRetries}). 5초 후 재시도…`);
            if (attempt < maxRetries - 1) {
                await new Promise((r) => setTimeout(r, 5000));
            }
        }
        this._lastHealthy = false;
        console.warn(`[VibeZoo] ❌ Zoo Code Crow 서버 연결 최종 실패 (${maxRetries}회 시도).`);
        this._onStatusChange.fire({ connected: false });
        return false;
    }
    /** 연결 해제 (구독 정리만) */
    disconnect() {
        this.stopHealthCheck();
        this._lastHealthy = false;
        this._onStatusChange.fire({ connected: false });
        console.log('[VibeZoo] Crow 연결 해제됨 (Zoo Code 서버는 계속 실행 중)');
    }
    /** Extension 비활성화 시 정리 */
    onDeactivate() {
        this.stopHealthCheck();
    }
    startHealthCheck() {
        this.stopHealthCheck();
        this.healthCheckTimer = setInterval(async () => {
            const healthy = await this.healthCheck();
            this._lastHealthy = healthy;
            if (!healthy) {
                this._onStatusChange.fire({ connected: false });
            }
        }, this.config.healthCheckIntervalMs);
    }
    stopHealthCheck() {
        if (this.healthCheckTimer) {
            clearInterval(this.healthCheckTimer);
            this.healthCheckTimer = null;
        }
    }
}
exports.CrowServerManager = CrowServerManager;
//# sourceMappingURL=CrowServerManager.js.map