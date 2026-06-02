import re
import os

files = [
    'extension/src/extension.ts',
    'extension/src/ui/StatusBarManager.ts',
    'extension/src/visual/VisualVibePanels.ts',
    'extension/src/ui/TreeViewProviders.ts',
    'extension/src/orchestra/FixLoopManager.ts'
]

replacements = [
    (r"vscode\.window\.showWarningMessage\('VibeZoo: YOLO 안전망이 비활성화되어 있습니다\.'\)", 
     r"vscode.window.showWarningMessage(vscode.l10n.t('VibeZoo: YOLO safety net is disabled.'))"),
     
    (r"vscode\.window\.showInformationMessage\(\s*YOLO Rewind 완료: \$\{result\.restoredFiles\}/\$\{result\.totalFiles\} 파일 복구 \(\$\{result\.durationMs\}ms\)\s*\)",
     r"vscode.window.showInformationMessage(vscode.l10n.t('YOLO Rewind complete: {0}/{1} files restored ({2}ms)', result.restoredFiles, result.totalFiles, result.durationMs))"),
     
    (r"vscode\.window\.showErrorMessage\(Rewind 실패: \$\{err\.message\}\)",
     r"vscode.window.showErrorMessage(vscode.l10n.t('Rewind failed: {0}', err.message))"),
     
    (r"vscode\.window\.showInformationMessage\('✅ VibeZoo: Zoo Code Crow Memory 연결 확인 성공!'\)",
     r"vscode.window.showInformationMessage(vscode.l10n.t('✅ VibeZoo: Zoo Code Crow Memory connection verified!'))"),
     
    (r"vscode\.window\.showWarningMessage\('⚠️ VibeZoo: Zoo Code Crow Memory에 연결할 수 없습니다\.'\)",
     r"vscode.window.showWarningMessage(vscode.l10n.t('⚠️ VibeZoo: Cannot connect to Zoo Code Crow Memory.'))"),
     
    (r"vscode\.window\.showErrorMessage\(❌ Crow 연결 실패: \$\{err\.message\}\)",
     r"vscode.window.showErrorMessage(vscode.l10n.t('❌ Crow connection failed: {0}', err.message))"),
     
    (r"vscode\.window\.showInformationMessage\(\s*🔍 \$\{node\.name\}: \$\{node\.currentTask \|\| node\.status \|\| 'ready'\} \\(port: \$\{node\.port\}\\)\s*\)",
     r"vscode.window.showInformationMessage(vscode.l10n.t('🔍 {0}: {1} (port: {2})', node.name, node.currentTask || node.status || 'ready', node.port))"),
     
    (r"vscode\.window\.showInformationMessage\(\s*'🎉 VibeZoo 준비 완료! Ctrl\+Shift\+P → VibeZoo: Help',\s*'Help 보기',\s*'닫기'\s*\)",
     r"vscode.window.showInformationMessage(vscode.l10n.t('🎉 VibeZoo ready! Ctrl+Shift+P → VibeZoo: Help'), vscode.l10n.t('View Help'), vscode.l10n.t('Close'))"),
     
    (r"vscode\.window\.showInformationMessage\(\s*VibeZoo: AutoBuildFix 성공 \(\$\{outcome\.attempt\}회 시도\)\s*\)",
     r"vscode.window.showInformationMessage(vscode.l10n.t('VibeZoo: AutoBuildFix succeeded ({0} attempts)', outcome.attempt))"),
     
    (r"vscode\.window\.showInformationMessage\('VibeZoo: Continuous Improvement Mode 시작'\)",
     r"vscode.window.showInformationMessage(vscode.l10n.t('VibeZoo: Continuous Improvement Mode started'))"),
     
    (r"vscode\.window\.showInformationMessage\('VibeZoo: Continuous Improvement Mode 중지'\)",
     r"vscode.window.showInformationMessage(vscode.l10n.t('VibeZoo: Continuous Improvement Mode stopped'))"),
     
    (r"vscode\.window\.showInformationMessage\('VibeZoo: Zoo Code 채팅에서 \"코드 설명해줘\" 라고 입력하세요\. \(explain_code MCP 도구\)'\)",
     r"vscode.window.showInformationMessage(vscode.l10n.t('VibeZoo: Please type \"explain code\" in Zoo Code chat. (explain_code MCP tool)'))"),
     
    (r"vscode\.window\.showInformationMessage\('VibeZoo: Zoo Code 채팅에서 \"변경사항 분석해줘\" 라고 입력하세요\. \(analyze_changes MCP 도구\)'\)",
     r"vscode.window.showInformationMessage(vscode.l10n.t('VibeZoo: Please type \"analyze changes\" in Zoo Code chat. (analyze_changes MCP tool)'))"),
     
    (r"vscode\.window\.showInformationMessage\('VibeZoo: Zoo Code 채팅에서 \"PR 리뷰해줘\" 라고 입력하세요\. \(review_pr MCP 도구\)'\)",
     r"vscode.window.showInformationMessage(vscode.l10n.t('VibeZoo: Please type \"review PR\" in Zoo Code chat. (review_pr MCP tool)'))"),
     
    (r"vscode\.window\.showInformationMessage\('VibeZoo: Zoo Code 채팅에서 \"리팩토링해줘\" 라고 입력하세요\. \(refactor_across_files MCP 도구\)'\)",
     r"vscode.window.showInformationMessage(vscode.l10n.t('VibeZoo: Please type \"refactor\" in Zoo Code chat. (refactor_across_files MCP tool)'))"),
     
    (r"vscode\.window\.showInformationMessage\('VibeZoo: Zoo Code 채팅에서 \"프로젝트 학습해줘\" 라고 입력하세요\. \(learn_project MCP 도구\)'\)",
     r"vscode.window.showInformationMessage(vscode.l10n.t('VibeZoo: Please type \"learn project\" in Zoo Code chat. (learn_project MCP tool)'))"),
     
    (r"vscode\.window\.showInformationMessage\('VibeZoo: Zoo Code 채팅에서 \"프로젝트 기억해줘\" 라고 입력하세요\. \(recall_project MCP 도구\)'\)",
     r"vscode.window.showInformationMessage(vscode.l10n.t('VibeZoo: Please type \"recall project\" in Zoo Code chat. (recall_project MCP tool)'))"),
     
    (r"vscode\.window\.showInformationMessage\('VibeZoo: Zoo Code 채팅에서 \"선호도 학습해줘\" 라고 입력하세요\. \(learn_preference MCP 도구\)'\)",
     r"vscode.window.showInformationMessage(vscode.l10n.t('VibeZoo: Please type \"learn preference\" in Zoo Code chat. (learn_preference MCP tool)'))"),
     
    (r"vscode\.window\.showInformationMessage\('VibeZoo: Zoo Code 채팅에서 \"선호도 보여줘\" 라고 입력하세요\. \(get_preferences MCP 도구\)'\)",
     r"vscode.window.showInformationMessage(vscode.l10n.t('VibeZoo: Please type \"show preferences\" in Zoo Code chat. (get_preferences MCP tool)'))"),
     
    (r"vscode\.window\.showInformationMessage\('VibeZoo: Auto-Fix Loop 일시 중지됨'\)",
     r"vscode.window.showInformationMessage(vscode.l10n.t('VibeZoo: Auto-Fix Loop paused'))"),
     
    (r"vscode\.window\.showInformationMessage\('VibeZoo: Auto-Fix Loop 재개됨'\)",
     r"vscode.window.showInformationMessage(vscode.l10n.t('VibeZoo: Auto-Fix Loop resumed'))"),
     
    (r"vscode\.window\.showInformationMessage\('VibeZoo: Auto-Fix Loop 중단됨'\)",
     r"vscode.window.showInformationMessage(vscode.l10n.t('VibeZoo: Auto-Fix Loop aborted'))"),
     
    (r"vscode\.window\.showInformationMessage\(✅ \$\{fileTypeLabel\}이 업로드되었습니다\. \(경로가 클립보드에 복사되었습니다\. 채팅창에 붙여넣어 LLM에게 지시하세요!\)\)",
     r"vscode.window.showInformationMessage(vscode.l10n.t('✅ {0} uploaded. (Path copied to clipboard. Paste it in chat to instruct the LLM!)', fileTypeLabel))"),
     
    (r"statusItem\.tooltip = '파일 저장 시 자동 tsc 검사';",
     r"statusItem.tooltip = vscode.l10n.t('Auto tsc check on file save');"),
     
    (r"this\.item\.tooltip = VibeZoo: \$\{reason\}\\n클릭하여 모드 변경;",
     r"this.item.tooltip = vscode.l10n.t('VibeZoo: {0}\\nClick to change mode', reason);"),
     
    (r"placeholder\.tooltip = 'VibeZoo MCP Bridge가 연결되면 Agent 상태가 표시됩니다\.';",
     r"placeholder.tooltip = vscode.l10n.t('Agent status will be displayed when VibeZoo MCP Bridge is connected.');"),
     
    (r"placeholder\.tooltip = 'YOLO\(Yocto OnLine Offline\) 모드로 YOCTO 스냅샷을 생성하면 여기에 기록이 표시됩니다\.';",
     r"placeholder.tooltip = vscode.l10n.t('YOLO session history will be displayed here when YOLO snapshots are created.');"),
     
    (r"this\.tooltip = YOLO 세션: \$\{name\}\\n우클릭 → Rewind 실행;",
     r"this.tooltip = vscode.l10n.t('YOLO Session: {0}\\nRight-click → Run Rewind', name);"),
     
    (r"placeholder\.tooltip = 'Crow Memory 또는 로컬 파일에서 세션 요약을 불러올 수 없습니다\.';",
     r"placeholder.tooltip = vscode.l10n.t('Cannot load session resume from Crow Memory or local file.');")
]

for fpath in files:
    if not os.path.exists(fpath):
        continue
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    for pattern, repl in replacements:
        content = re.sub(pattern, repl, content)
        
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(content)

print("Done")
