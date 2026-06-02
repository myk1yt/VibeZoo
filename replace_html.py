import re
import os

fpath = 'extension/src/visual/VisualVibePanels.ts'
if os.path.exists(fpath):
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()

    replacements = [
        ("<h2>⚠️ Fabric.js를 불러올 수 없습니다</h2>", "<h2>${vscode.l10n.t('⚠️ Cannot load Fabric.js')}</h2>"),
        ("<p>인터넷 연결을 확인하거나 CDN이 차단되지 않았는지 확인하세요.</p>", "<p>${vscode.l10n.t('Please check your internet connection or if the CDN is blocked.')}</p>"),
        ("✏️ 그리기", "${vscode.l10n.t('✏️ Draw')}"),
        ("⬜ 사각형", "${vscode.l10n.t('⬜ Rectangle')}"),
        ("📝 텍스트", "${vscode.l10n.t('📝 Text')}"),
        ("🖱️ 선택", "${vscode.l10n.t('🖱️ Select')}"),
        ("📸 캡처", "${vscode.l10n.t('📸 Capture')}"),
        (">📷 이미지<", ">${vscode.l10n.t('📷 Image')}<"),
        ("🗑️ 선택 삭제", "${vscode.l10n.t('🗑️ Delete Selected')}"),
        ("🧹 전체 삭제", "${vscode.l10n.t('🧹 Clear All')}"),
        ("new fabric.Textbox('텍스트 입력'", "new fabric.Textbox('${vscode.l10n.t(\\'Enter text\\')}'"),
        ("<p>AI가 React/Vue 컴포넌트 코드를 생성하면 이곳에 실시간 렌더링됩니다.</p>", "<p>${vscode.l10n.t('When AI generates React/Vue component code, it will be rendered here in real-time.')}</p>"),
        ("Mermaid 렌더링 오류", "${vscode.l10n.t('Mermaid render error')}"),
        ("텍스트", "${vscode.l10n.t('Text')}"),  # Need to be careful here, we saw `props.text || '텍스트'`
        ("props.text || '텍스트'", "props.text || '${vscode.l10n.t(\\'Text\\')}'")
    ]
    
    for old, new_s in replacements:
        content = content.replace(old, new_s)
        
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(content)
print("Done")
