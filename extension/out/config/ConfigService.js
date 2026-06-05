"use strict";
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
exports.ConfigService = void 0;
const vscode = __importStar(require("vscode"));
class ConfigService {
    static getHost() {
        return vscode.workspace.getConfiguration('vibezoo').get('network.host', '127.0.0.1');
    }
    static getBridgePort() {
        return vscode.workspace.getConfiguration('vibezoo').get('bridge.port', 9027);
    }
    static getBridgeUrl(path = '') {
        return `http://${this.getHost()}:${this.getBridgePort()}${path}`;
    }
    static getCrowPort() {
        return vscode.workspace.getConfiguration('vibezoo').get('crow.port', 9020);
    }
    static getCrowUrl(path = '') {
        return `http://${this.getHost()}:${this.getCrowPort()}${path}`;
    }
    static getAgentUrl(port, path = '') {
        return `http://${this.getHost()}:${port}${path}`;
    }
    static getAgentPorts() {
        const config = vscode.workspace.getConfiguration('vibezoo');
        return [
            { id: 'scout', name: 'Scout', port: config.get('scout.port', 9022) },
            { id: 'reviewer', name: 'Reviewer', port: config.get('reviewer.port', 9023) },
            { id: 'tester', name: 'Tester', port: config.get('tester.port', 9024) },
            { id: 'deepAnalyzer', name: 'Deep Analyzer', port: config.get('deepAnalyzer.port', 9026) },
        ];
    }
    // ── Guard.git 설정 ──────────────────────────────────────
    /** Guard.git 전체 활성화 */
    static getGuardEnabled() {
        return vscode.workspace.getConfiguration('vibezoo').get('guard.enabled', true);
    }
    /** YOLO 모드 진입 시 자동 활성화 */
    static getGuardAutoEnable() {
        return vscode.workspace.getConfiguration('vibezoo').get('guard.autoEnable', true);
    }
    /** .git 핵심 파일을 yocto에 주기적으로 스냅샷 */
    static getGuardYoctoBackupEnabled() {
        return vscode.workspace.getConfiguration('vibezoo').get('guard.yoctoBackupEnabled', true);
    }
    /** .git 스냅샷 간격 (분) */
    static getGuardYoctoBackupIntervalMin() {
        return vscode.workspace.getConfiguration('vibezoo').get('guard.yoctoBackupIntervalMin', 30);
    }
    /** .git 무결성 자동 진단 간격 (분) — H5 대응 */
    static getGuardIntegrityCheckIntervalMin() {
        return vscode.workspace.getConfiguration('vibezoo').get('guard.integrityCheckIntervalMin', 5);
    }
    /** Linux에서 chattr +a 사용 (내부 파일 삭제도 방지 → git gc 실패 가능) — H2 대응 */
    static getGuardLinuxUseChattr() {
        return vscode.workspace.getConfiguration('vibezoo').get('guard.linuxUseChattr', false);
    }
}
exports.ConfigService = ConfigService;
//# sourceMappingURL=ConfigService.js.map