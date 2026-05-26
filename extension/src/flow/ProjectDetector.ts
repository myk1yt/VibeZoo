// VibeZoo Wave 1: Project Auto-Detector
// 워크스페이스가 열릴 때 프로젝트 타입을 감지하고,
// StatusBar에 권장 Zoo Code 모드를 제안한다.

import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';

interface ProjectModeMapping {
  filePattern: string;
  targetMode: string;
  priority: number;
  description: string;
}

const MODE_MAP: ProjectModeMapping[] = [
  { filePattern: '.zoo/config.json', targetMode: 'code_plus_crow', priority: 100, description: '.zoo/config.json 감지' },
  { filePattern: 'AGENTS.md', targetMode: 'code_plus_crow', priority: 85, description: 'AGENTS.md 감지' },
  { filePattern: '.roo/mcp.json', targetMode: 'code_plus_crow', priority: 80, description: '.roo/mcp.json 감지' },
];

export function activateProjectDetector(
  context: vscode.ExtensionContext,
  onModeSuggested: (mode: string, reason: string) => void
): void {
  // 워크스페이스 폴더 변경 감지
  context.subscriptions.push(
    vscode.workspace.onDidChangeWorkspaceFolders((e) => {
      if (e.added.length > 0) {
        detectAndSuggest(e.added[0], onModeSuggested);
      }
    })
  );

  // 현재 열린 워크스페이스 즉시 감지
  const folders = vscode.workspace.workspaceFolders;
  if (folders && folders.length > 0) {
    detectAndSuggest(folders[0], onModeSuggested);
  }
}

async function detectAndSuggest(
  folder: vscode.WorkspaceFolder,
  onModeSuggested: (mode: string, reason: string) => void
): Promise<void> {
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
  } catch {
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

async function detectProjectTypeFromFiles(rootPath: string): Promise<string | null> {
  const detectors: [string, string][] = [
    ['package.json', 'Node.js'],
    ['Cargo.toml', 'Rust'],
    ['go.mod', 'Go'],
    ['pyproject.toml', 'Python'],
  ];
  for (const [file, name] of detectors) {
    if (fs.existsSync(path.join(rootPath, file))) return name;
  }
  return null;
}
