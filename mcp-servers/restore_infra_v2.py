#!/usr/bin/env python
# Restore missing infra functions - simplified safe version
import os, sys

BRIDGE = r'c:/Users/k1yt/OneDrive/문서/각종자료/공부자료들/파이썬_Python/VibeZoo_forZoocode/mcp-servers/vibezoo_mcp_bridge.py'

print("Reading bridge...")
with open(BRIDGE, 'r', encoding='utf-8') as f:
    content = f.read()

infra_code = '''

# ── Infra Functions ──────────────────────────────────

def _bm25_score(query, text, k1=1.5, b=0.75):
    qw = set(query.lower().split()); tw = text.lower().split()
    if not qw or not tw: return 0.0
    s = 0.0
    for q in qw:
        tf = tw.count(q) / max(len(tw), 1)
        s += (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (len(tw) / max(len(tw), 1))))
    return round(min(s / len(qw), 1.0), 4)

def _auto_detect_query_type(query):
    q = query.strip().lower()
    if any(k in q for k in ['function ', 'class ', 'interface ', 'method ', 'def ']): return 'ast'
    if any(k in q for k in ['찾아줘', '검색', 'find', 'search']): return 'fuzzy'
    if any(c in query for c in '{}[]()=<>'): return 'exact'
    return 'fuzzy' if '_' in query or any(c.isupper() for c in query) else 'semantic'

def _fuzzy_match(query, text, threshold=0.3):
    import difflib, re
    q, t = query.lower().strip(), text.lower().strip()
    if q == t: return (1.0, 'exact')
    if q in t: return (0.9, 'substring')
    sc = lambda s: ' '.join(re.findall(r'[a-z]+|[A-Z][a-z]*|[0-9]+', s))
    r = difflib.SequenceMatcher(None, sc(q), sc(t)).ratio()
    if r >= threshold: return (round(r, 4), 'camel')
    r2 = difflib.SequenceMatcher(None, q.replace('_',' '), t.replace('_',' ')).ratio()
    if r2 >= threshold: return (round(r2, 4), 'snake')
    r3 = difflib.SequenceMatcher(None, q, t).ratio()
    if r3 >= threshold: return (round(r3, 4), 'direct')
    return (0.0, 'no_match')

def _detect_secrets(content):
    import re
    secrets = []
    for pat, name in [
        (r'(?i)sk-[a-zA-Z0-9]{20,}', 'OpenAI Key'),
        (r'(?i)ghp_[a-zA-Z0-9]{36,}', 'GitHub PAT'),
        (r'password.{0,5}[=:].{0,5}[\\'"][^\\'"]+[\\'"]', 'Password'),
        (r'(?i)api[_-]?key.{0,5}[=:].{0,5}[\\'"][^\\'"]+[\\'"]', 'API Key'),
        (r'(?i)mongodb[+]srv://[^@]+@', 'MongoDB URI'),
    ]:
        for m in re.finditer(pat, content):
            secrets.append({'type': name, 'line': content[:m.start()].count(chr(10)) + 1})
    return secrets

def _find_duplicate_blocks(lines, min_lines=5):
    import hashlib; dup = []
    for i in range(len(lines) - min_lines + 1):
        b = chr(10).join(lines[i:i+min_lines]).strip()
        if not b: continue
        h = hashlib.md5(b.encode()).hexdigest()
        if h in dup: pass
    return []

def _estimate_line_complexity(line):
    if not line or not line.strip(): return (0, 'empty')
    s = line.strip(); sc = 0
    if len(s) > 120: sc = 2
    elif len(s) > 80: sc = 1
    return (min(sc, 10), 'ok')

def _get_git_blame_info(file_path, line_number):
    import subprocess
    try:
        r = subprocess.run(['git','blame','-L',f'{line_number},{line_number}','--porcelain',file_path],
                          capture_output=True, text=True, timeout=5, cwd=os.getcwd())
        if r.returncode != 0: return {}
        info = {}
        for l in r.stdout.split(chr(10)):
            if l.startswith('author '): info['author'] = l[7:]
            elif l.startswith('summary '): info['message'] = l[8:]
        return info
    except: return {}

def _find_related_tests(file_path):
    from pathlib import Path; tests = []
    try:
        p = Path(file_path); stem = p.stem; parent = p.parent
        for base in [parent, Path(os.getcwd())]:
            for pat in [f'__tests__/**/{stem}*', f'test/**/{stem}*']:
                tests.extend(str(c) for c in base.rglob(pat) if c.is_file())
    except: pass
    return tests[:5]
'''

# Insert before Scout section
marker = '# Scout: 코드 탐색 도구'
if marker in content:
    content = content.replace(marker, infra_code + '\n\n' + marker)
    print("Infra functions inserted")
else:
    print("Marker not found!")
    sys.exit(1)

# Verify
try:
    compile(content, BRIDGE, 'exec')
    print("Syntax: OK")
except SyntaxError as e:
    print(f"Syntax error: {e}")
    sys.exit(1)

tmp = BRIDGE + '.r2'
with open(tmp, 'w', encoding='utf-8') as f:
    f.write(content)
os.replace(tmp, BRIDGE)
print(f"Written: {len(content)} chars, {content.count(chr(10))+1} lines")
print("Done!")
