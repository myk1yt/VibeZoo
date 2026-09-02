# -*- coding: utf-8 -*-
"""T3 verification round 2: symbols across full trees, command count, bat files."""
import os, re, json

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 1. grep symbols across both bridge trees
for tree in ['mcp-servers', 'extension/mcp-servers']:
    hits = {}
    for dirpath, dirs, files in os.walk(os.path.join(ROOT, tree)):
        dirs[:] = [d for d in dirs if d not in ('__pycache__', '.pytest_cache')]
        for f in files:
            if not f.endswith('.py'):
                continue
            p = os.path.join(dirpath, f)
            src = open(p, encoding='utf-8', errors='replace').read()
            for sym in ['embedding_health_check', 'rebuild_code_index', 'index_cache',
                        'check_uploaded_files', 'crow_recall', 'crow_ingest', 'crow_admin']:
                if sym in src:
                    hits.setdefault(sym, []).append(os.path.relpath(p, ROOT))
    print('===', tree)
    for k in sorted(hits):
        print('  ', k, '->', hits[k][:4])

# 2. extension command count
pkg = json.load(open(os.path.join(ROOT, 'extension', 'package.json'), encoding='utf-8'))
cmds = pkg.get('contributes', {}).get('commands', [])
print('extension commands:', len(cmds))
print('command ids:', [c['command'] for c in cmds])
removed_cmds = ['vibezoo.findBugs', 'vibezoo.suggestRefactor', 'vibezoo.generateDocs', 'vibezoo.learnProject']
allids = [c['command'] for c in cmds]
print('removed-cmd leakage:', [c for c in allids if c in removed_cmds])

# 3. bridge version / extension version
print('extension version:', pkg.get('version'))

# 4. bat/script existence at root
for f in ['watch_vibezoo_bridge.bat', 'start_vibezoo_servers.bat', 'start_vibezoo_bridge.bat',
          'init_vibezoo.bat', 'init_vibezoo.sh']:
    print(f, os.path.exists(os.path.join(ROOT, f)))

# 5. tool registry in tool_context.py
tc = open(os.path.join(ROOT, 'mcp-servers/bridge/tool_context.py'), encoding='utf-8', errors='replace').read()
m = re.findall(r'"(\w+)":', tc)
print('tool_context keys sample:', m[:60])