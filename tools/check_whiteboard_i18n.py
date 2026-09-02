import re
import json
from pathlib import Path

def main():
    content = Path("extension/mcp-servers/bridge/tools/whiteboard.py").read_text(encoding="utf-8")
    
    # regex for \bt("...") and \bt('...')
    keys = set()
    for m in re.finditer(r'\bt\("([^"\\]*(?:\\.[^"\\]*)*)"\)', content):
        keys.add(m.group(1).encode().decode('unicode-escape'))
    for m in re.finditer(r"\bt\('([^'\\]*(?:\\.[^'\\]*)*)'\)", content):
        keys.add(m.group(1).encode().decode('unicode-escape'))
        
    print(f"Total keys found in whiteboard.py with word boundary: {len(keys)}")
    
    en_path = Path("extension/mcp-servers/bridge/i18n/translations/en.json")
    ko_path = Path("extension/mcp-servers/bridge/i18n/translations/ko.json")
    
    en_data = json.loads(en_path.read_text(encoding="utf-8"))
    ko_data = json.loads(ko_path.read_text(encoding="utf-8"))
    
    missing_in_en = [k for k in keys if k not in en_data]
    missing_in_ko = [k for k in keys if k not in ko_data or ko_data[k] == k]
    
    print("\nMissing in en.json:", len(missing_in_en))
    for k in sorted(missing_in_en):
        print(" -", repr(k))
        
    print("\nMissing or untranslated in ko.json:", len(missing_in_ko))
    for k in sorted(missing_in_ko):
        print(" -", repr(k), "-> ko val:", repr(ko_data.get(k)))

if __name__ == "__main__":
    main()
