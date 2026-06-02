import re
import os

files = [
    'extension/src/extension.ts',
    'extension/src/ui/StatusBarManager.ts',
    'extension/src/visual/VisualVibePanels.ts',
    'extension/src/ui/TreeViewProviders.ts',
    'extension/src/orchestra/FixLoopManager.ts'
]

def multi_replace(fpath):
    if not os.path.exists(fpath): return
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Manual replacements for multi-line or tricky strings
    content = content.replace("vscode.window.showInformationMessage(\n          YOLO Rewind 완료: / 파일 복구 (ms)\n        );", "vscode.window.showInformationMessage(\n          vscode.l10n.t('YOLO Rewind complete: {0}/{1} files restored ({2}ms)', result.restoredFiles, result.totalFiles, result.durationMs)\n        );")
    
    content = content.replace("vscode.window.showErrorMessage(Rewind 실패: );", "vscode.window.showErrorMessage(vscode.l10n.t('Rewind failed: {0}', err.message));")
    
    content = content.replace("vscode.window.showErrorMessage(❌ Crow 연결 실패: );", "vscode.window.showErrorMessage(vscode.l10n.t('❌ Crow connection failed: {0}', err.message));")
    
    content = content.replace("vscode.window.showInformationMessage(\n            🔍 :  (port: )\n          );", "vscode.window.showInformationMessage(\n            vscode.l10n.t('🔍 {0}: {1} (port: {2})', node.name, node.currentTask || node.status || 'ready', node.port)\n          );")
    
    content = content.replace("vscode.window.showInformationMessage(\n              VibeZoo: AutoBuildFix 성공 (회 시도)\n            );", "vscode.window.showInformationMessage(\n              vscode.l10n.t('VibeZoo: AutoBuildFix succeeded ({0} attempts)', outcome.attempt)\n            );")

    content = content.replace("this.item.tooltip = VibeZoo: \\n클릭하여 모드 변경;", "this.item.tooltip = vscode.l10n.t('VibeZoo: {0}\\nClick to change mode', reason);")

    content = content.replace("this.tooltip = YOLO 세션: \\n우클릭 → Rewind 실행;", "this.tooltip = vscode.l10n.t('YOLO Session: {0}\\nRight-click → Run Rewind', name);")

    content = content.replace("vscode.window.showInformationMessage(✅ 이 업로드되었습니다. (경로가 클립보드에 복사되었습니다. 채팅창에 붙여넣어 LLM에게 지시하세요!));", "vscode.window.showInformationMessage(vscode.l10n.t('✅ {0} uploaded. (Path copied to clipboard. Paste it in chat to instruct the LLM!)', fileTypeLabel));")

    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(content)

for f in files:
    multi_replace(f)
print("Done")
