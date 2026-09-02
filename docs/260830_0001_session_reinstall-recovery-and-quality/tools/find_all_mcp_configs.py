import os
import sys
import glob

sys.stdout.reconfigure(encoding='utf-8')

userprofile = os.environ.get('USERPROFILE', '')
appdata = os.environ.get('APPDATA', '')
localappdata = os.environ.get('LOCALAPPDATA', '')

search_patterns = [
    os.path.join(userprofile, '.vscode', '**', '*mcp*'),
    os.path.join(userprofile, '.roo', '**'),
    os.path.join(appdata, '**', '*mcp_settings.json'),
    os.path.join(appdata, '**', '*mcp.json'),
    os.path.join(userprofile, 'mcp-servers', '**'),
]

found = []
for pat in search_patterns:
    for p in glob.glob(pat, recursive=True):
        if os.path.isfile(p):
            found.append(p)

print(f"Found {len(found)} MCP related files:")
for f in found:
    print(" -", f)
