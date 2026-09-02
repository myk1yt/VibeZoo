import glob
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def update_bundle_l10n():
    base_dir = Path("extension/l10n")
    files = sorted(base_dir.glob("bundle.l10n*.json"))
    print(f"Found {len(files)} bundle.l10n files to update.")
    
    source_key = 'VibeZoo: Please type "rebuild code index" in Zoo Code chat. (rebuild_code_index MCP tool)'
    
    translations = {
        "extension/l10n/bundle.l10n.json": 'VibeZoo: Please type "rebuild code index" in Zoo Code chat. (rebuild_code_index MCP tool)',
        "extension/l10n/bundle.l10n.ko.json": 'VibeZoo: Zoo Code 채팅에서 "코드 인덱스 재구축해줘" 라고 입력하세요. (rebuild_code_index MCP 도구)',
        "extension/l10n/bundle.l10n.ja.json": 'VibeZoo: Zoo Codeチャットで"rebuild code index"と入力してください。(rebuild_code_index MCPツール)',
        "extension/l10n/bundle.l10n.ar.json": 'VibeZoo: اكتب "rebuild code index" في دردشة Zoo Code. (أداة MCP rebuild_code_index)',
        "extension/l10n/bundle.l10n.bg.json": 'VibeZoo: Напишете "rebuild code index" в чата на Zoo Code. (инструмент MCP rebuild_code_index)',
        "extension/l10n/bundle.l10n.cs.json": 'VibeZoo: Napište "rebuild code index" v chatu Zoo Code. (nástroj MCP rebuild_code_index)',
        "extension/l10n/bundle.l10n.de.json": 'VibeZoo: Bitte "rebuild code index" im Zoo Code Chat eingeben. (rebuild_code_index MCP-Tool)',
        "extension/l10n/bundle.l10n.es.json": 'VibeZoo: Escriba "rebuild code index" en el chat Zoo Code. (herramienta MCP rebuild_code_index)',
        "extension/l10n/bundle.l10n.fr.json": 'VibeZoo: Veuillez taper "rebuild code index" dans le chat Zoo Code. (outil MCP rebuild_code_index)',
        "extension/l10n/bundle.l10n.he.json": 'VibeZoo: הקלד "rebuild code index" בצ\'אט Zoo Code. (כלי MCP rebuild_code_index)',
        "extension/l10n/bundle.l10n.hu.json": 'VibeZoo: Kérem írja be a "rebuild code index"-t a Zoo Code chatben. (rebuild_code_index MCP eszköz)',
        "extension/l10n/bundle.l10n.it.json": 'VibeZoo: Digita "rebuild code index" nella chat Zoo Code. (strumento MCP rebuild_code_index)',
        "extension/l10n/bundle.l10n.pl.json": 'VibeZoo: Wpisz "rebuild code index" w czacie Zoo Code. (narzędzie MCP rebuild_code_index)',
        "extension/l10n/bundle.l10n.pt-BR.json": 'VibeZoo: Digite "rebuild code index" no chat Zoo Code. (ferramenta MCP rebuild_code_index)',
        "extension/l10n/bundle.l10n.ru.json": 'VibeZoo: Введите "rebuild code index" в чате Zoo Code. (инструмент MCP rebuild_code_index)',
        "extension/l10n/bundle.l10n.th.json": 'VibeZoo: พิมพ์ "rebuild code index" ในแชท Zoo Code (เครื่องมือ MCP rebuild_code_index)',
        "extension/l10n/bundle.l10n.tr.json": 'VibeZoo: Zoo Code sohbetinde "rebuild code index" yazın. (rebuild_code_index MCP aracı)',
        "extension/l10n/bundle.l10n.vi.json": 'VibeZoo: Vui lòng gõ "rebuild code index" trong trò chuyện Zoo Code. (công cụ MCP rebuild_code_index)',
        "extension/l10n/bundle.l10n.zh-CN.json": 'VibeZoo: 请在 Zoo Code 聊天中输入 "rebuild code index"。(rebuild_code_index MCP 工具)',
        "extension/l10n/bundle.l10n.zh-TW.json": 'VibeZoo: 請在 Zoo Code 聊天中輸入 "rebuild code index"。(rebuild_code_index MCP 工具)',
    }
    
    anchor_key = 'VibeZoo: Auto-Fix Loop aborted'
    
    for f in files:
        rel_posix = f.as_posix()
        with open(f, "r", encoding="utf-8") as fp:
            data = json.load(fp)
            
        val = translations.get(rel_posix, translations["extension/l10n/bundle.l10n.json"])
        
        new_data = {}
        for k, v in data.items():
            if k == source_key:
                continue
            new_data[k] = v
            if k == anchor_key:
                new_data[source_key] = val
                
        if source_key not in new_data:
            new_data[source_key] = val
            
        with open(f, "w", encoding="utf-8") as fp:
            json.dump(new_data, fp, ensure_ascii=False, indent=2)
            fp.write("\n")
            
        print(f"Updated {f}: new key count = {len(new_data)}")

if __name__ == "__main__":
    update_bundle_l10n()
