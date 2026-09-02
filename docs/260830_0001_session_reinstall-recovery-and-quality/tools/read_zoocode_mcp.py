import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

appdata = os.environ.get('APPDATA', '')
mcp_settings = os.path.join(appdata, 'Code', 'User', 'globalStorage', 'zoocodeorganization.zoo-code', 'settings', 'mcp_settings.json')

if os.path.exists(mcp_settings):
    with open(mcp_settings, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print("mcp_settings.json servers:", list(data.get('mcpServers', {}).keys()))
    print(json.dumps(data, indent=2, ensure_ascii=False))
else:
    print("File does not exist:", mcp_settings)
