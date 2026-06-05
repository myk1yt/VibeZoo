"use strict";
// VibeZoo v0.14.3: GuardGitACL — OS ACL 추상화 계층
//
// C1: 모든 OS 명령어는 child_process.execFile()만 사용 (shell injection 방지)
// C1: 경로 검증 정규식으로 허용 문자만 통과
// C1/C2: 모든 호출에 timeout: 10000 (10초)
// C2: sudo 절대 사용 금지
// C3: Linux setfacl fallback 사용 금지
// H4: FS 타입 확인 (isAvailable()에서)
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
exports.createGuardGitACL = createGuardGitACL;
const child_process = __importStar(require("child_process"));
// ── 공통 상수 ─────────────────────────────────────────────────
/** C1: 경로 검증 정규식 — 허용 문자만 통과 */
const SAFE_PATH_REGEX = /^[a-zA-Z0-9_\-\\:. \/@]+$/;
/** C1/C2: 기본 타임아웃 (10초) */
const DEFAULT_TIMEOUT_MS = 10000;
// ── 공통 유틸리티 ─────────────────────────────────────────────
/**
 * C1: 경로 검증 — 안전하지 않은 문자 포함 시 예외 발생
 */
function validatePath(gitDir) {
    if (!SAFE_PATH_REGEX.test(gitDir)) {
        throw new Error(`Guard.git: 안전하지 않은 경로 문자 포함 — "${gitDir}"`);
    }
    if (gitDir.length > 250) {
        throw new Error(`Guard.git: 경로가 너무 깁니다 (${gitDir.length}자)`);
    }
}
/**
 * C1/C2: execFile 래퍼 — shell: false, timeout 적용
 *
 * 모든 OS 명령어는 이 함수를 통해서만 실행된다.
 */
function execFileSafe(command, args, timeoutMs = DEFAULT_TIMEOUT_MS) {
    return new Promise((resolve, reject) => {
        const child = child_process.execFile(command, args, {
            timeout: timeoutMs,
            windowsHide: true,
            shell: false,
        }, (error, stdout, stderr) => {
            if (error) {
                reject(error);
            }
            else {
                resolve({ stdout, stderr });
            }
        });
    });
}
// ── Windows 구현: icacls deny (DE) ────────────────────────────
/**
 * WindowsGuardGitACL
 *
 * 전략: icacls deny Delete (DE)
 *   - S-1-1-0 = Everyone (SID 기반 — 로케일 독립)
 *   - DC(Delete Child)는 의도적으로 미적용 (git gc, prune, repack 허용)
 *
 * 적용: execFile('icacls', [gitDir, '/deny', '*S-1-1-0:(DE)'])
 * 해제: execFile('icacls', [gitDir, '/remove:d', '*S-1-1-0'])
 * 확인: execFile('icacls', [gitDir]) → stdout.includes('DENY')
 */
class WindowsGuardGitACL {
    method = 'icacls (DE deny)';
    async isAvailable(gitDir) {
        validatePath(gitDir);
        // H4: NTFS 여부 간접 확인 (icacls는 NTFS에서만 동작)
        try {
            await execFileSafe('icacls', [gitDir], 3000);
            return true;
        }
        catch {
            console.warn('[Guard.git] icacls 실패 — FS가 ACL을 지원하지 않을 수 있음');
            return false;
        }
    }
    async applyProtection(gitDir) {
        validatePath(gitDir);
        try {
            const result = await execFileSafe('icacls', [gitDir, '/deny', '*S-1-1-0:(DE)']);
            return {
                success: true,
                command: `icacls ${gitDir} /deny *S-1-1-0:(DE)`,
                stdout: result.stdout,
                stderr: result.stderr,
            };
        }
        catch (err) {
            return { success: false, error: err.message };
        }
    }
    async removeProtection(gitDir) {
        validatePath(gitDir);
        try {
            const result = await execFileSafe('icacls', [gitDir, '/remove:d', '*S-1-1-0']);
            return {
                success: true,
                command: `icacls ${gitDir} /remove:d *S-1-1-0`,
                stdout: result.stdout,
                stderr: result.stderr,
            };
        }
        catch (err) {
            return { success: false, error: err.message };
        }
    }
    async checkProtection(gitDir) {
        try {
            const { stdout } = await execFileSafe('icacls', [gitDir], 5000);
            return stdout.includes('DENY');
        }
        catch {
            return false;
        }
    }
}
// ── Linux 구현: chattr +a (optional) ─────────────────────────
/**
 * LinuxGuardGitACL
 *
 * C2: sudo 절대 사용 금지 — 사용자 권한으로만 시도, 실패 시 Watcher+Yocto fallback
 * C3: setfacl fallback 제거 — setfacl로 디렉토리 삭제 방지 불가
 * H2: 기본 비활성화 (linuxUseChattr: false)
 *
 * 전략: chattr +a (append-only)
 *   - 디렉토리 삭제 방지, 내부 파일 삭제도 방지 (git gc 실패 가능 → H2)
 *   - 사용자가 linuxUseChattr: true로 명시적 활성화 필요
 *
 * 적용: execFile('chattr', ['+a', gitDir])
 * 해제: execFile('chattr', ['-a', gitDir])
 * 확인: execFile('lsattr', [gitDir]) → stdout.includes('a')
 */
class LinuxGuardGitACL {
    method = 'chattr +a';
    async isAvailable(gitDir) {
        validatePath(gitDir);
        // H4: FS 타입 확인 (ext4, btrfs, xfs만 chattr 지원)
        try {
            const { stdout } = await execFileSafe('stat', ['-f', '-c', '%T', gitDir], 3000);
            const fsType = stdout.trim();
            const supportedFS = ['ext2/ext3', 'ext4', 'btrfs', 'xfs', 'tmpfs'];
            if (!supportedFS.some(fs => fsType.includes(fs))) {
                console.log(`[Guard.git] FS 타입 '${fsType}'는 chattr 미지원 → Watcher+Yocto fallback`);
                return false;
            }
            // chattr 실행 가능 여부 확인 (sudo 없이)
            await execFileSafe('chattr', ['-R', '--help'], 3000);
            // 소유권 확인 — pre-flight check
            try {
                await execFileSafe('chattr', ['+a', gitDir], 3000);
                // 성공 시 바로 해제
                await execFileSafe('chattr', ['-a', gitDir], 3000);
                return true;
            }
            catch {
                console.log('[Guard.git] chattr 권한 없음 → Watcher+Yocto fallback');
                return false;
            }
        }
        catch {
            return false;
        }
    }
    async applyProtection(gitDir) {
        validatePath(gitDir);
        try {
            // C2: sudo 없이 chattr 시도
            const result = await execFileSafe('chattr', ['+a', gitDir]);
            return {
                success: true,
                command: `chattr +a ${gitDir}`,
                stdout: result.stdout,
                stderr: result.stderr,
            };
        }
        catch (err) {
            // C2: 실패 시 Watcher+Yocto fallback
            return {
                success: false,
                error: `chattr 실패 (Watcher+Yocto fallback): ${err.message}`,
            };
        }
    }
    async removeProtection(gitDir) {
        validatePath(gitDir);
        try {
            const result = await execFileSafe('chattr', ['-a', gitDir]);
            return {
                success: true,
                command: `chattr -a ${gitDir}`,
                stdout: result.stdout,
                stderr: result.stderr,
            };
        }
        catch (err) {
            return { success: false, error: err.message };
        }
    }
    async checkProtection(gitDir) {
        try {
            const { stdout } = await execFileSafe('lsattr', [gitDir], 5000);
            // lsattr 출력: "----a-------- ./git" → 'a' 속성이 있으면 보호 중
            return /^[^ ]*a[^ ]* /.test(stdout);
        }
        catch {
            return false;
        }
    }
}
// ── macOS 구현: chmod +a ACL ─────────────────────────────────
/**
 * MacOSGuardGitACL
 *
 * 전략: chmod +a ACL
 *   - everyone deny delete ACL 적용
 *   - Fallback: chflags uchg (쓰기도 막힘 — 경고 후 Yocto 의존)
 *
 * 적용: execFile('chmod', ['+a', 'everyone deny delete', gitDir])
 * 해제: execFile('chmod', ['-a', 'everyone deny delete', gitDir])
 * 확인: execFile('ls', ['-le', gitDir]) → stdout.includes('deny delete')
 */
class MacOSGuardGitACL {
    method = 'chmod +a';
    async isAvailable(gitDir) {
        validatePath(gitDir);
        try {
            await execFileSafe('chmod', ['+a', 'everyone deny delete', gitDir], 3000);
            // 성공 시 바로 해제 (pre-flight)
            await execFileSafe('chmod', ['-a', 'everyone deny delete', gitDir], 3000);
            return true;
        }
        catch {
            console.warn('[Guard.git] chmod +a 실패 — ACL 미지원 FS일 수 있음');
            return false;
        }
    }
    async applyProtection(gitDir) {
        validatePath(gitDir);
        try {
            const result = await execFileSafe('chmod', ['+a', 'everyone deny delete', gitDir]);
            return {
                success: true,
                command: `chmod +a 'everyone deny delete' ${gitDir}`,
                stdout: result.stdout,
                stderr: result.stderr,
            };
        }
        catch (err) {
            // Fallback: chflags uchg 시도
            try {
                await execFileSafe('chflags', ['uchg', gitDir]);
                return {
                    success: true,
                    command: `chflags uchg ${gitDir} (fallback)`,
                    stdout: '',
                    stderr: `chmod +a 실패, chflags uchg fallback 사용: ${err.message}`,
                };
            }
            catch (err2) {
                return { success: false, error: `chmod +a 및 chflags uchg 실패: ${err2.message}` };
            }
        }
    }
    async removeProtection(gitDir) {
        validatePath(gitDir);
        try {
            const result = await execFileSafe('chmod', ['-a', 'everyone deny delete', gitDir]);
            return {
                success: true,
                command: `chmod -a 'everyone deny delete' ${gitDir}`,
                stdout: result.stdout,
                stderr: result.stderr,
            };
        }
        catch (err) {
            // chflags 해제 시도
            try {
                await execFileSafe('chflags', ['nouchg', gitDir]);
                return {
                    success: true,
                    command: `chflags nouchg ${gitDir} (fallback)`,
                    stdout: '',
                    stderr: `chmod -a 실패, chflags nouchg fallback 사용: ${err.message}`,
                };
            }
            catch (err2) {
                return { success: false, error: `chmod -a 및 chflags nouchg 실패: ${err2.message}` };
            }
        }
    }
    async checkProtection(gitDir) {
        try {
            const { stdout } = await execFileSafe('ls', ['-le', gitDir], 5000);
            return stdout.includes('deny delete');
        }
        catch {
            return false;
        }
    }
}
// ── Noop Fallback ────────────────────────────────────────────
/**
 * NoopGuardGitACL — 미지원 플랫폼 fallback
 *
 * 모든 호출을 성공으로 처리하되, 실제 ACL 작업은 수행하지 않는다.
 * 가드 역할은 Watcher + Yocto only 모드로 수행된다.
 */
class NoopGuardGitACL {
    method = 'noop (unsupported platform)';
    async isAvailable(_gitDir) {
        return false; // ACL 미지원 — Watcher+Yocto only
    }
    async applyProtection(_gitDir) {
        return { success: true, command: 'noop (unsupported platform)' };
    }
    async removeProtection(_gitDir) {
        return { success: true, command: 'noop (unsupported platform)' };
    }
    async checkProtection(_gitDir) {
        return false;
    }
}
// ── Factory ──────────────────────────────────────────────────
/**
 * 플랫폼에 맞는 IGuardGitACL 구현체 생성
 *
 * - win32  → WindowsGuardGitACL (icacls)
 * - linux   → LinuxGuardGitACL (chattr +a, no sudo)
 * - darwin  → MacOSGuardGitACL (chmod +a, chflags fallback)
 * - 그 외   → NoopGuardGitACL (Watcher+Yocto only)
 */
function createGuardGitACL() {
    const platform = process.platform;
    switch (platform) {
        case 'win32': return new WindowsGuardGitACL();
        case 'linux': return new LinuxGuardGitACL();
        case 'darwin': return new MacOSGuardGitACL();
        default: return new NoopGuardGitACL();
    }
}
//# sourceMappingURL=GuardGitACL.js.map