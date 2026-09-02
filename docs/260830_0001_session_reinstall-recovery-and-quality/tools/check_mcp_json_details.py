import os
import sys
import json

sys.stdout.reconfigure(encoding='utf-8')

def check_json(filepath):
    print(f"\n=== {filepath} ===")
    if not os.path.exists(filepath):
        print("Does not exist.")
        return
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            data = json.load(f)
        # Print keys or vibezoo entry
        mcp_servers = data.get('mcpServers', {})
        print("MCP Servers defined:", list(mcp_servers.keys()))
        if 'vibezoo' in mcp_servers:
            print("vibezoo config:", json.dumps(mcp_servers['vibezoo'], indent=2, ensure_ascii=False))
        if 'crow-memory' in mcp_servers:
            print("crow-memory config:", json.dumps(mcp_servers['crow-memory'], indent=2, ensure_ascii=False))
    except Exception as e:
        print("Error parsing JSON:", e)

check_json('.roo/mcp.json')
userprofile = os.environ.get('USERPROFILE', '')
appdata = os.environ.get('APPDATA', '')
check_json(os.path.join(userprofile, '.roo', 'mcp.json'))
check_json(os.path.join(appdata, 'Code', 'User', 'globalStorage', 'rooveterinaryinc.roo-cline', 'settings', 'mcp_settings.json'))
check_json(os.path.join(appdata, 'Code', 'User', 'globalStorage', 'saoudrizwan.claude-dev', 'settings', 'mcp_settings.json'))
