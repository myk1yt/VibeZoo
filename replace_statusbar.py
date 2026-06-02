import os
import re

fpath = 'extension/src/ui/StatusBarManager.ts'
if os.path.exists(fpath):
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()

    replacements = [
        ("private _baseTooltip: string = 'VibeZoo: 활성화됨';", "private _baseTooltip: string = vscode.l10n.t('VibeZoo: Active');"),
        ("this._baseTooltip = `VibeZoo Bridge: 연결됨 (:${bridgePort || 9027})`;", "this._baseTooltip = vscode.l10n.t('VibeZoo Bridge: Connected (:{0})', bridgePort || 9027);"),
        ("this._baseTooltip = 'VibeZoo: 활성화됨';", "this._baseTooltip = vscode.l10n.t('VibeZoo: Active');"),
        ("tooltip += ' | Crow: 연결됨';", "tooltip += vscode.l10n.t(' | Crow: Connected');"),
        ("tooltip += ' | Crow: 없음';", "tooltip += vscode.l10n.t(' | Crow: Disconnected');"),
        ("this.item.text = `$(gear) 권장: ${mode}`;", "this.item.text = vscode.l10n.t('$(gear) Suggested: {0}', mode);")
    ]
    
    for old, new_s in replacements:
        content = content.replace(old, new_s)
        
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(content)
print("Done")
