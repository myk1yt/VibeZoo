import os

fpath = 'extension/src/visual/VisualVibePanels.ts'
if os.path.exists(fpath):
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()

    content = content.replace("vscode.l10n.t(\\'Enter text\\')", 'vscode.l10n.t("Enter text")')
    content = content.replace("vscode.l10n.t(\\'Text\\')", 'vscode.l10n.t("Text")')
    
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(content)
print("Done")
