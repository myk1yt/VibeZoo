"use strict";
// VibeZoo Wave 2: Git Stash Manager
// YOLO 진입/퇴장 시 Git stash를 자동으로 생성/복원한다.
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
exports.GitStashManager = void 0;
const vscode = __importStar(require("vscode"));
const StatusBarManager_1 = require("../ui/StatusBarManager");
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const child_process_1 = require("child_process");
const util_1 = require("util");
const execAsync = (0, util_1.promisify)(child_process_1.exec);
class GitStashManager {
    stashName = null;
    workspaceRoot = null;
    constructor() {
        const folders = vscode.workspace.workspaceFolders;
        this.workspaceRoot = folders?.[0]?.uri.fsPath ?? null;
    }
    get cwd() {
        return this.workspaceRoot || '.';
    }
    /** YOLO 모드 진입 — 현재 상태를 stash에 저장 */
    async enterYolo() {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        this.stashName = `vibezoo-yolo-${timestamp}`;
        try {
            await execAsync(`git stash push -m "${this.stashName}" --include-untracked`, { cwd: this.cwd });
            StatusBarManager_1.NotificationThrottle.showInfo(`VibeZoo: YOLO 모드 시작 — 현재 상태가 stash에 저장되었습니다.`);
            return true;
        }
        catch (err) {
            // Git 저장소가 아니거나 stash 실패 — yocto만으로도 작동
            console.warn('[VibeZoo] Git stash 실패 (yocto로만 진행):', err.message);
            return false;
        }
    }
    /** YOLO 모드 퇴장 — 성공 시 커밋, 실패 시 복구 */
    async exitYolo(success) {
        if (success) {
            try {
                // YOLO 성공: 변경사항을 자동 커밋
                await execAsync('git add -A', { cwd: this.cwd });
                const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
                await execAsync(`git commit -m "vibezoo-yolo-complete-${timestamp}" --no-verify`, { cwd: this.cwd });
                StatusBarManager_1.NotificationThrottle.showInfo('VibeZoo: YOLO 완료 — 변경사항이 커밋되었습니다.');
            }
            catch (err) {
                console.warn('[VibeZoo] Git 커밋 실패:', err.message);
            }
        }
        else {
            // YOLO 실패: 사용자에게 되돌릴지 묻기
            const choice = await StatusBarManager_1.NotificationThrottle.showWarning('YOLO가 실패했습니다. 이전 상태로 되돌리시겠습니까?', 'Instant Rewind', '수동으로 처리');
            if (choice === 'Instant Rewind') {
                vscode.commands.executeCommand('vibezoo.instantRewind');
            }
            // Git stash 복원 시도
            if (this.stashName) {
                try {
                    await execAsync(`git stash pop 'stash@{/${this.stashName}}'`, { cwd: this.cwd });
                }
                catch (err) {
                    console.warn('[VibeZoo] Git stash pop 실패:', err.message);
                }
            }
        }
        this.stashName = null;
    }
    /** Git 저장소인지 확인 */
    isGitRepo() {
        try {
            const gitDir = path.join(this.workspaceRoot || '', '.git');
            return fs.existsSync(gitDir);
        }
        catch {
            return false;
        }
    }
}
exports.GitStashManager = GitStashManager;
//# sourceMappingURL=GitStashManager.js.map