export declare class ConfigService {
    static getHost(): string;
    static getBridgePort(): number;
    static getBridgeUrl(path?: string): string;
    static getCrowPort(): number;
    static getCrowUrl(path?: string): string;
    static getAgentUrl(port: number, path?: string): string;
    static getAgentPorts(): Array<{
        id: string;
        name: string;
        port: number;
    }>;
    /** Guard.git 전체 활성화 */
    static getGuardEnabled(): boolean;
    /** YOLO 모드 진입 시 자동 활성화 */
    static getGuardAutoEnable(): boolean;
    /** .git 핵심 파일을 yocto에 주기적으로 스냅샷 */
    static getGuardYoctoBackupEnabled(): boolean;
    /** .git 스냅샷 간격 (분) */
    static getGuardYoctoBackupIntervalMin(): number;
    /** .git 무결성 자동 진단 간격 (분) — H5 대응 */
    static getGuardIntegrityCheckIntervalMin(): number;
    /** Linux에서 chattr +a 사용 (내부 파일 삭제도 방지 → git gc 실패 가능) — H2 대응 */
    static getGuardLinuxUseChattr(): boolean;
}
//# sourceMappingURL=ConfigService.d.ts.map