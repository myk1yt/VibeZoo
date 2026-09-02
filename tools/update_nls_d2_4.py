import glob
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def update_nls_files():
    base_dir = Path("extension")
    files = sorted(base_dir.glob("package.nls*.json"))
    print(f"Found {len(files)} files to update.")
    
    translations = {
        "extension/package.nls.ko.json": "VibeZoo: 코드 인덱스 재구축",
        "extension/package.nls.ja.json": "VibeZoo: Rebuild Code Index (コードインデックス再構築)",
    }
    default_text = "VibeZoo: Rebuild Code Index"
    
    for f in files:
        rel_posix = f.as_posix()
        with open(f, "r", encoding="utf-8") as fp:
            data = json.load(fp)
            
        val = translations.get(rel_posix, default_text)
        
        # Build ordered dictionary with vibezoo.rebuildCodeIndex.title right after vibezoo.showSessionResume.title
        new_data = {}
        for k, v in data.items():
            if k == "vibezoo.rebuildCodeIndex.title":
                continue
            new_data[k] = v
            if k == "vibezoo.showSessionResume.title":
                new_data["vibezoo.rebuildCodeIndex.title"] = val
                
        # If vibezoo.showSessionResume.title was not found, append at end
        if "vibezoo.rebuildCodeIndex.title" not in new_data:
            new_data["vibezoo.rebuildCodeIndex.title"] = val
            
        with open(f, "w", encoding="utf-8") as fp:
            json.dump(new_data, fp, ensure_ascii=False, indent=2)
            fp.write("\n")
            
        print(f"Updated {f}: new key count = {len(new_data)}")

if __name__ == "__main__":
    update_nls_files()
