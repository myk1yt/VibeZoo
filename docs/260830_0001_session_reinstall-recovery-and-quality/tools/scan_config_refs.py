import os
import sys
import glob
import json
import re

sys.stdout.reconfigure(encoding='utf-8')

findings = []

def search_text_in_file(filepath, patterns):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            lines = content.splitlines()
        for idx, line in enumerate(lines, 1):
            for pat in patterns:
                if re.search(pat, line, re.IGNORECASE):
                    findings.append({
                        'file': filepath.replace('\\', '/'),
                        'line': idx,
                        'pattern': pat,
                        'content': line.strip()
                    })
    except Exception as e:
        pass

patterns = [
    r'mcp-servers',
    r'vibezoo_mcp_bridge',
    r'crow_memory_server',
    r'start_vibezoo_bridge',
    r'autoStartCommand',
    r'vibezoo.*bridge',
    r'\.vibezoo'
]

# 1. Extension source files
for p in glob.glob('extension/src/**', recursive=True):
    if os.path.isfile(p):
        search_text_in_file(p, patterns)

# 2. Workspace root scripts
for s in ['init_vibezoo.bat', 'init_vibezoo.sh', 'package.json', 'extension/package.json', 'extension/mcp-servers/start_vibezoo_bridge.bat']:
    if os.path.exists(s):
        search_text_in_file(s, patterns)

# 3. .roo configs
for p in glob.glob('.roo/**', recursive=True):
    if os.path.isfile(p):
        search_text_in_file(p, patterns)

# 4. Global configurations
userprofile = os.environ.get('USERPROFILE', '')
appdata = os.environ.get('APPDATA', '')

global_files = [
    os.path.join(userprofile, '.roo', 'mcp.json'),
    os.path.join(userprofile, '.codeium', 'windsurf', 'mcp_config.json'),
    os.path.join(userprofile, '.cursor', 'mcp.json'),
    os.path.join(appdata, 'Code', 'User', 'globalStorage', 'rooveterinaryinc.roo-cline', 'settings', 'mcp_settings.json'),
    os.path.join(appdata, 'Code', 'User', 'globalStorage', 'saoudrizwan.claude-dev', 'settings', 'mcp_settings.json'),
]

for gf in global_files:
    if os.path.exists(gf):
        search_text_in_file(gf, patterns)

print(f"Total findings: {len(findings)}")
for f in findings:
    print(f"[{f['file']}#L{f['line']}] ({f['pattern']}) -> {f['content']}")

with open('docs/260830_0001_session_reinstall-recovery-and-quality/tools/config_ref_findings.json', 'w', encoding='utf-8') as fp:
    json.dump(findings, fp, indent=2, ensure_ascii=False)
