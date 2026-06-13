import * as vscode from 'vscode';

export class ConfigService {
    public static getHost(): string {
        return vscode.workspace.getConfiguration('vibezoo').get('network.host', '127.0.0.1');
    }

    public static getBridgePort(): number {
        return vscode.workspace.getConfiguration('vibezoo').get('bridge.port', 9027);
    }

    public static getBridgeUrl(path: string = ''): string {
        return `http://${this.getHost()}:${this.getBridgePort()}${path}`;
    }

    public static getCrowPort(): number {
        return vscode.workspace.getConfiguration('vibezoo').get('crow.port', 9020);
    }

    public static getCrowUrl(path: string = ''): string {
        return `http://${this.getHost()}:${this.getCrowPort()}${path}`;
    }

    public static getAgentUrl(port: number, path: string = ''): string {
        return `http://${this.getHost()}:${port}${path}`;
    }

    public static getAgentPorts(): Array<{ id: string; name: string; port: number }> {
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
    public static getGuardEnabled(): boolean {
        return vscode.workspace.getConfiguration('vibezoo').get('guard.enabled', true);
    }

    /** YOLO 모드 진입 시 자동 활성화 */
    public static getGuardAutoEnable(): boolean {
        return vscode.workspace.getConfiguration('vibezoo').get('guard.autoEnable', true);
    }

    /** .git 핵심 파일을 yocto에 주기적으로 스냅샷 */
    public static getGuardYoctoBackupEnabled(): boolean {
        return vscode.workspace.getConfiguration('vibezoo').get('guard.yoctoBackupEnabled', true);
    }

    /** .git 스냅샷 간격 (분) */
    public static getGuardYoctoBackupIntervalMin(): number {
        return vscode.workspace.getConfiguration('vibezoo').get('guard.yoctoBackupIntervalMin', 30);
    }

    /** .git 무결성 자동 진단 간격 (분) — H5 대응 */
    public static getGuardIntegrityCheckIntervalMin(): number {
        return vscode.workspace.getConfiguration('vibezoo').get('guard.integrityCheckIntervalMin', 5);
    }

    /** Linux에서 chattr +a 사용 (내부 파일 삭제도 방지 → git gc 실패 가능) — H2 대응 */
    public static getGuardLinuxUseChattr(): boolean {
        return vscode.workspace.getConfiguration('vibezoo').get('guard.linuxUseChattr', false);
    }

    // ── Python Path ─────────────────────────────────────────

    /** 사용자 지정 Python 인터프리터 경로 (vibezoo.advanced.pythonPath) */
    public static getAdvancedPythonPath(): string {
        return vscode.workspace.getConfiguration('vibezoo').get('advanced.pythonPath', '');
    }
}
