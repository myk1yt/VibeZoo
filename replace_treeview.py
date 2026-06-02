import os
import re

fpath = 'extension/src/ui/TreeViewProviders.ts'
if os.path.exists(fpath):
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()

    replacements = [
        ("const placeholder = new vscode.TreeItem('VibeZoo 대기 중...', vscode.TreeItemCollapsibleState.None);", "const placeholder = new vscode.TreeItem(vscode.l10n.t('Waiting for VibeZoo...'), vscode.TreeItemCollapsibleState.None);"),
        ("placeholder.description = '브릿지 연결 시 자동 표시됩니다';", "placeholder.description = vscode.l10n.t('Automatically shown when Bridge connects');"),
        ("placeholder.label = '$(sync~spin) VibeZoo 대기 중...';", "placeholder.label = vscode.l10n.t('$(sync~spin) Waiting for VibeZoo...');"),
        ("title: '에이전트 정보',", "title: vscode.l10n.t('Agent Info'),"),
        ("const placeholder = new vscode.TreeItem('YOLO 기록 없음', vscode.TreeItemCollapsibleState.None);", "const placeholder = new vscode.TreeItem(vscode.l10n.t('No YOLO history'), vscode.TreeItemCollapsibleState.None);"),
        ("placeholder.description = 'YOLO 모드로 작업 시 자동 기록됩니다';", "placeholder.description = vscode.l10n.t('Automatically recorded when working in YOLO mode');"),
        ("placeholder.label = '$(history) YOLO 기록 없음';", "placeholder.label = vscode.l10n.t('$(history) No YOLO history');"),
        ("const placeholder = new vscode.TreeItem('이전 세션 없음', vscode.TreeItemCollapsibleState.None);", "const placeholder = new vscode.TreeItem(vscode.l10n.t('No previous session'), vscode.TreeItemCollapsibleState.None);"),
        ("placeholder.description = 'Crow Memory에서 세션 정보를 불러오는 중...';", "placeholder.description = vscode.l10n.t('Loading session info from Crow Memory...');"),
        ("placeholder.label = '$(empty) 불러온 세션 없음';", "placeholder.label = vscode.l10n.t('$(empty) No loaded session');"),
        ("children.push(new SessionResumeItem(session, 'summary', `📋 ${session.summary || '요약 없음'}`));", "children.push(new SessionResumeItem(session, 'summary', vscode.l10n.t('📋 {0}', session.summary || vscode.l10n.t('No summary'))));"),
        ("children.push(new SessionResumeItem(session, 'project', `📁 ${session.projectPath || '프로젝트 경로 없음'}`));", "children.push(new SessionResumeItem(session, 'project', vscode.l10n.t('📁 {0}', session.projectPath || vscode.l10n.t('No project path'))));"),
        ("const decisionLabel = `📌 주요 결정 (${session.keyDecisions.length})`;", "const decisionLabel = vscode.l10n.t('📌 Key Decisions ({0})', session.keyDecisions.length);"),
        ("const filesLabel = `📄 수정 파일 (${session.touchedFiles.length})`;", "const filesLabel = vscode.l10n.t('📄 Modified Files ({0})', session.touchedFiles.length);"),
        ("const tasksLabel = `⏳ 미완료 작업 (${session.pendingTasks.length})`;", "const tasksLabel = vscode.l10n.t('⏳ Pending Tasks ({0})', session.pendingTasks.length);"),
    ]
    
    for old, new_s in replacements:
        content = content.replace(old, new_s)
        
    # The multiline markdown template is complex, let's just do it cleanly via regex
    content = re.sub(
        r"`\*\*세션 요약\*\*\\n\\n\$\{session\.summary \|\| '요약 없음'\}\\n\\n\*\*프로젝트\*\*: \$\{session\.projectPath \|\| 'N/A'\}\\n\*\*모드\*\*: \$\{session\.mode\}\\n\*\*시작\*\*: \$\{new Date\(session\.startedAt\)\.toLocaleString\('ko-KR'\)\}\$\{session\.keyDecisions\.length \? `\\n\*\*주요 결정\*\*: \$\{session\.keyDecisions\.length\}개` : ''\}\$\{session\.touchedFiles\.length \? `\\n\*\*수정 파일\*\*: \$\{session\.touchedFiles\.length\}개` : ''\}\$\{session\.pendingTasks\.length \? `\\n\*\*미완료 작업\*\*: \$\{session\.pendingTasks\.length\}개` : ''\}`",
        r"vscode.l10n.t('**Session Summary**\\n\\n{0}\\n\\n**Project**: {1}\\n**Mode**: {2}\\n**Started**: {3}{4}{5}{6}', session.summary || vscode.l10n.t('No summary'), session.projectPath || 'N/A', session.mode, new Date(session.startedAt).toLocaleString(), session.keyDecisions.length ? vscode.l10n.t('\\n**Key Decisions**: {0}', session.keyDecisions.length) : '', session.touchedFiles.length ? vscode.l10n.t('\\n**Modified Files**: {0}', session.touchedFiles.length) : '', session.pendingTasks.length ? vscode.l10n.t('\\n**Pending Tasks**: {0}', session.pendingTasks.length) : '')",
        content
    )
        
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(content)
print("Done")
