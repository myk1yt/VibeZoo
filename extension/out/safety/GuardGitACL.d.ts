import { GuardGitACLResult } from '../types';
export interface IGuardGitACL {
    /** .git 디렉토리에 삭제 방지 ACL 적용 */
    applyProtection(gitDir: string): Promise<GuardGitACLResult>;
    /** .git 디렉토리에서 ACL 제거 (원상복구) */
    removeProtection(gitDir: string): Promise<GuardGitACLResult>;
    /** 현재 ACL 상태 확인 */
    checkProtection(gitDir: string): Promise<boolean>;
    /** 이 OS에서 지원되는 방식의 이름 */
    readonly method: string;
    /** 사전 점검: 필요한 도구가 설치되어 있고, FS가 ACL을 지원하는지 (H4) */
    isAvailable(gitDir: string): Promise<boolean>;
}
/**
 * 플랫폼에 맞는 IGuardGitACL 구현체 생성
 *
 * - win32  → WindowsGuardGitACL (icacls)
 * - linux   → LinuxGuardGitACL (chattr +a, no sudo)
 * - darwin  → MacOSGuardGitACL (chmod +a, chflags fallback)
 * - 그 외   → NoopGuardGitACL (Watcher+Yocto only)
 */
export declare function createGuardGitACL(): IGuardGitACL;
//# sourceMappingURL=GuardGitACL.d.ts.map