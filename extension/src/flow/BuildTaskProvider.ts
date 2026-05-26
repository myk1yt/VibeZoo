// VibeZoo Wave 1: Silent Build Task Provider
// 프로젝트 타입을 자동 감지하여 silent 빌드 태스크를 등록한다.
// 빌드 성공 시 터미널이 나타나지 않는다 (presentation.reveal: silent).

import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';

const BUILD_DEFS: Record<string, { command: string; args: string[]; problemMatcher: string }> = {
  node: { command: 'npm', args: ['run', 'build'], problemMatcher: '$tsc-watch' },
  rust: { command: 'cargo', args: ['build'], problemMatcher: '$rustc' },
  go: { command: 'go', args: ['build', './...'], problemMatcher: '$go' },
  python: { command: 'python', args: ['-m', 'pytest'], problemMatcher: '$pytest' },
  java: { command: 'mvn', args: ['compile'], problemMatcher: '$lessCompile' },
};

export async function detectProjectType(workspaceRoot: string): Promise<string> {
  const detectors: [string, string][] = [
    ['package.json', 'node'],
    ['Cargo.toml', 'rust'],
    ['go.mod', 'go'],
    ['pyproject.toml', 'python'],
    ['pom.xml', 'java'],
  ];
  for (const [file, type] of detectors) {
    if (fs.existsSync(path.join(workspaceRoot, file))) return type;
  }
  return 'unknown';
}

export function registerBuildTaskProvider(context: vscode.ExtensionContext): void {
  const provider = vscode.tasks.registerTaskProvider('vibezoo', {
    async provideTasks(): Promise<vscode.Task[]> {
      const folders = vscode.workspace.workspaceFolders;
      if (!folders || folders.length === 0) return [];

      const rootPath = folders[0].uri.fsPath;
      const projectType = await detectProjectType(rootPath);
      const def = BUILD_DEFS[projectType];
      if (!def) return [];

      const silentMode = vscode.workspace
        .getConfiguration('vibezoo')
        .get('build.silentMode', true);

      const task = new vscode.Task(
        { type: 'vibezoo', task: 'build' },
        vscode.TaskScope.Workspace,
        'vibezoo: build',
        'VibeZoo',
        new vscode.ShellExecution(def.command, def.args),
        def.problemMatcher
      );

      task.presentationOptions = {
        reveal: silentMode
          ? vscode.TaskRevealKind.Silent
          : vscode.TaskRevealKind.Always,
        panel: vscode.TaskPanelKind.Dedicated,
        close: true,
        focus: false,
        clear: true,
        echo: false,
        showReuseMessage: false,
      };

      return [task];
    },
    resolveTask(task: vscode.Task): vscode.Task | undefined {
      return task;
    },
  });

  context.subscriptions.push(provider);
}
