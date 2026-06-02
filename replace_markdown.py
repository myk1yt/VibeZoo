import os

fpath = 'extension/src/extension.ts'
if os.path.exists(fpath):
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()

    replacements = [
        ("const lines = ['# 🔍 VibeZoo Foundation 진단', ''];", "const lines = [vscode.l10n.t('# 🔍 VibeZoo Foundation Diagnostics'), ''];"),
        ("lines.push(crowHealthy ? '✅ Zoo Code Crow Memory: 연결됨' : '❌ Zoo Code Crow Memory: 연결 실패');", "lines.push(crowHealthy ? vscode.l10n.t('✅ Zoo Code Crow Memory: Connected') : vscode.l10n.t('❌ Zoo Code Crow Memory: Connection failed'));"),
        ("lines.push('✅ VibeZoo Extension: 활성화됨');", "lines.push(vscode.l10n.t('✅ VibeZoo Extension: Active'));"),
        ("lines.push(fs.existsSync(yoctoDir) ? '✅ yocto 디렉토리: 존재함' : '⚠️ yocto 디렉토리: 없음');", "lines.push(fs.existsSync(yoctoDir) ? vscode.l10n.t('✅ yocto directory: Exists') : vscode.l10n.t('⚠️ yocto directory: Missing'));"),
        ("lines.push(fs.existsSync(zooDir) ? '✅ .zoo/ 디렉토리: 존재함' : '⚠️ .zoo/ 디렉토리: 없음');", "lines.push(fs.existsSync(zooDir) ? vscode.l10n.t('✅ .zoo/ directory: Exists') : vscode.l10n.t('⚠️ .zoo/ directory: Missing'));"),
        ("lines.push('', '## 설정');", "lines.push('', vscode.l10n.t('## Settings'));"),
        ("const lines = ['# 🔍 VibeZoo 자가진단', '', '## 시스템 상태'];", "const lines = [vscode.l10n.t('# 🔍 VibeZoo Self Check'), '', vscode.l10n.t('## System Status')];"),
        ("lines.push(resp.ok ? '✅ MCP Bridge: 정상' : '⚠️ MCP Bridge: 비정상 응답');", "lines.push(resp.ok ? vscode.l10n.t('✅ MCP Bridge: Normal') : vscode.l10n.t('⚠️ MCP Bridge: Abnormal response'));"),
        ("lines.push('❌ MCP Bridge: 연결 실패');", "lines.push(vscode.l10n.t('❌ MCP Bridge: Connection failed'));"),
        ("lines.push(crowServer?.lastHealthy ? '✅ Crow Memory: 연결됨' : '⚠️ Crow Memory: 연결 안 됨');", "lines.push(crowServer?.lastHealthy ? vscode.l10n.t('✅ Crow Memory: Connected') : vscode.l10n.t('⚠️ Crow Memory: Disconnected'));"),
        ("lines.push(fs.existsSync(yoctoDir) ? '✅ yocto 디렉토리' : '⚠️ yocto 디렉토리 없음');", "lines.push(fs.existsSync(yoctoDir) ? vscode.l10n.t('✅ yocto directory') : vscode.l10n.t('⚠️ no yocto directory'));"),
        ("lines.push(found ? '✅ vibezoo_mcp_bridge.py' : '❌ vibezoo_mcp_bridge.py 없음');", "lines.push(found ? vscode.l10n.t('✅ vibezoo_mcp_bridge.py') : vscode.l10n.t('❌ vibezoo_mcp_bridge.py not found'));"),
        ("'## 단축키',", "vscode.l10n.t('## Shortcuts'),"),
        ("'| 키 | 기능 |',", "vscode.l10n.t('| Key | Function |'),"),
        ("'| **Ctrl+Shift+Z** | Instant Rewind (YOLO 복구) |',", "vscode.l10n.t('| **Ctrl+Shift+Z** | Instant Rewind |'),"),
        ("'| **Ctrl+Shift+R** | Session Resume (이전 세션) |',", "vscode.l10n.t('| **Ctrl+Shift+R** | Session Resume |'),"),
        ("'## 명령어 (`Ctrl+Shift+P`)',", "vscode.l10n.t('## Commands (`Ctrl+Shift+P`)'),"),
        ("'| 명령어 | 기능 |',", "vscode.l10n.t('| Command | Function |'),"),
        ("'| `VibeZoo: Open Whiteboard` | 🎨 AI와 그림 그리며 협업 |',", "vscode.l10n.t('| `VibeZoo: Open Whiteboard` | 🎨 Collaborate with AI drawing |'),"),
        ("'| `VibeZoo: Open UI Preview` | 🖼️ React/Vue 실시간 미리보기 |',", "vscode.l10n.t('| `VibeZoo: Open UI Preview` | 🖼️ React/Vue Live Preview |'),"),
        ("'| `VibeZoo: Instant Rewind` | ⏪ YOLO 즉시 복구 |',", "vscode.l10n.t('| `VibeZoo: Instant Rewind` | ⏪ YOLO Instant Recovery |'),"),
        ("'| `VibeZoo: Verify Foundation` | 🔍 상태 진단 |',", "vscode.l10n.t('| `VibeZoo: Verify Foundation` | 🔍 State Diagnostics |'),"),
        ("'## MCP 도구 (Zoo Code 채팅)',", "vscode.l10n.t('## MCP Tools (Zoo Code Chat)'),"),
        ("'| \"코드 검색해줘\" | Scout: search_codebase |',", "vscode.l10n.t('| \"search code\" | Scout: search_codebase |'),"),
        ("'| \"코드 리뷰해줘\" | Reviewer: review_code |',", "vscode.l10n.t('| \"review code\" | Reviewer: review_code |'),"),
        ("'| \"의존성 분석해줘\" | DeepAnalyzer: map_dependencies |',", "vscode.l10n.t('| \"analyze dependencies\" | DeepAnalyzer: map_dependencies |'),"),
        ("'| \"그림 그려줘\" | Whiteboard: draw_on_whiteboard |',", "vscode.l10n.t('| \"draw a picture\" | Whiteboard: draw_on_whiteboard |'),"),
        ("'## 자동 기능',", "vscode.l10n.t('## Auto Features'),"),
        ("'- 🤫 Silent Build (빌드 에러 Crow 저장)',", "vscode.l10n.t('- 🤫 Silent Build (Save build errors to Crow)'),"),
        ("'- 📸 yocto 백업 (모든 파일 변경 실시간 저장)',", "vscode.l10n.t('- 📸 yocto Backup (Real-time save of file changes)'),"),
        ("'- 🔧 AutoBuildFix (빌드 실패 자동 수정)',", "vscode.l10n.t('- 🔧 AutoBuildFix (Auto-fix build failures)'),")
    ]
    
    for old, new_s in replacements:
        content = content.replace(old, new_s)
        
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(content)
print("Done")
