# -*- coding: utf-8 -*-
"""T3 doc modernization ground-truth verification."""
import re, os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

for tree in ['mcp-servers/bridge/tools', 'extension/mcp-servers/bridge/tools']:
    total = 0
    per = {}
    for f in sorted(os.listdir(os.path.join(ROOT, tree))):
        if not f.endswith('.py'):
            continue
        src = open(os.path.join(ROOT, tree, f), encoding='utf-8', errors='replace').read()
        names = re.findall(r'@mcp\.tool\(\)?\s*\ndef\s+(\w+)', src)
        n = len(names)
        if n:
            per[f] = (n, names)
            total += n
    print('===', tree, 'TOTAL', total)
    for k, (n, names) in per.items():
        print('  ', k, n, names)

for tree in ['mcp-servers/bridge', 'extension/mcp-servers/bridge']:
    src = ''
    for f in ['tools/scout.py', 'tools/whiteboard.py', 'tools/file_analyzer.py',
              'tools/integrated.py', 'tools/knowledge.py', 'tool_context.py']:
        p = os.path.join(ROOT, tree, f)
        if os.path.exists(p):
            src += open(p, encoding='utf-8', errors='replace').read()
    for sym in ['embedding_health_check', 'rebuild_code_index', 'check_uploaded_files',
                'track_dropzone', 'github_diver', 'review_project', 'recall_project',
                'learn_preference', 'get_preferences', 'analyze_uploaded_file']:
        print(tree, sym, sym in src)
    print(tree, 'index_cache.py exists:', os.path.exists(os.path.join(ROOT, tree, 'index_cache.py')))
    # integrated.py / knowledge.py sizes
    for f in ['tools/integrated.py', 'tools/knowledge.py', 'tool_context.py']:
        p = os.path.join(ROOT, tree, f)
        if os.path.exists(p):
            print(tree, f, 'lines:', sum(1 for _ in open(p, encoding='utf-8', errors='replace')))