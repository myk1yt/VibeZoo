"use strict";
// VibeZoo Wave 1: Project Auto-Detector
// 워크스페이스가 열릴 때 프로젝트 타입을 감지하고,
// StatusBar에 권장 Zoo Code 모드를 제안한다.
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
exports.activateProjectDetector = activateProjectDetector;
const vscode = __importStar(require("vscode"));
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const MODE_MAP = [
    { filePattern: '.zoo/config.json', targetMode: 'code_plus_crow', priority: 100, description: '.zoo/config.json 감지' },
    { filePattern: 'AGENTS.md', targetMode: 'code_plus_crow', priority: 85, description: 'AGENTS.md 감지' },
    { filePattern: '.roo/mcp.json', targetMode: 'code_plus_crow', priority: 80, description: '.roo/mcp.json 감지' },
];
function activateProjectDetector(context, onModeSuggested) {
    // 워크스페이스 폴더 변경 감지
    context.subscriptions.push(vscode.workspace.onDidChangeWorkspaceFolders((e) => {
        if (e.added.length > 0) {
            detectAndSuggest(e.added[0], onModeSuggested);
        }
    }));
    // 현재 열린 워크스페이스 즉시 감지
    const folders = vscode.workspace.workspaceFolders;
    if (folders && folders.length > 0) {
        detectAndSuggest(folders[0], onModeSuggested);
    }
}
async function detectAndSuggest(folder, onModeSuggested) {
    const rootPath = folder.uri.fsPath;
    // .zoo/config.json 우선 확인
    try {
        const configPath = path.join(rootPath, '.zoo', 'config.json');
        if (fs.existsSync(configPath)) {
            const config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
            if (config.defaultMode) {
                onModeSuggested(config.defaultMode, '프로젝트 설정 파일');
                return;
            }
        }
    }
    catch {
        // 설정 파일 없음 또는 파싱 실패 — 계속 진행
    }
    // 파일 기반 감지
    const sorted = [...MODE_MAP].sort((a, b) => b.priority - a.priority);
    for (const mapping of sorted) {
        const filePath = path.join(rootPath, mapping.filePattern);
        if (fs.existsSync(filePath)) {
            onModeSuggested(mapping.targetMode, mapping.description);
            return;
        }
    }
    // 프로젝트 타입 기반 기본값
    const projectType = await detectProjectTypeFromFiles(rootPath);
    if (projectType) {
        onModeSuggested('code', `${projectType} 프로젝트 감지`);
    }
}
async function detectProjectTypeFromFiles(rootPath) {
    const detectors = [
        ['package.json', 'Node.js'],
        ['Cargo.toml', 'Rust'],
        ['go.mod', 'Go'],
        ['pyproject.toml', 'Python'],
    ];
    for (const [file, name] of detectors) {
        if (fs.existsSync(path.join(rootPath, file)))
            return name;
    }
    return null;
}
//# sourceMappingURL=ProjectDetector.js.map