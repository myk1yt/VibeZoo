import os
import json

file_path = 'vibezoo_mcp_bridge.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

bad_block = '''        _atomic_write_json(FIX_REQUEST_FILE) as f:
            data = json.load(f)

        # 상태를 in_progress로 변경
        data["status"] = "in_progress"
        data["lastReadAt"] = time.time()
        with open(FIX_REQUEST_FILE, data, indent=2)'''

good_block = '''        with open(FIX_REQUEST_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 상태를 in_progress로 변경
        data["status"] = "in_progress"
        data["lastReadAt"] = time.time()
        
        _atomic_write_json(FIX_REQUEST_FILE, data, indent=2)'''

if bad_block in content:
    content = content.replace(bad_block, good_block)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Fixed successfully')
else:
    print('Bad block not found')
