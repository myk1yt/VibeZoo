#!/usr/bin/env python
# Restore 3 missing infra functions: _bm25_score, _fuzzy_match, _detect_secrets
import os, sys

BRIDGE = r'c:/Users/k1yt/OneDrive/문서/각종자료/공부자료들/파이썬_Python/VibeZoo_forZoocode/mcp-servers/vibezoo_mcp_bridge.py'

print("Reading bridge...")
with open(BRIDGE, 'r', encoding='utf-8') as f:
    content = f.read()

# Check which functions are missing
missing = []
for fn in ['_bm25_score', '_fuzzy_match', '_detect_secrets', '_find_duplicate_blocks', 
           '_estimate_line_complexity', '_get_git_blame_info', '_find_related_tests',
           '_extract_python_imports', '_extract_go_imports', '_auto_detect_query_type']:
    if fn not in content:
        missing.append(fn)
        print(f"  ❌ Missing: {fn}")
    else:
        print(f"  ✅ Present: {fn}")

# The functions to restore (shorter versions that fit before Scout section)
infra_code = r'''

# ── Retrieval & Analysis Infra ──────────────────────────

def _bm25_score(query: str, text: str, k1: float = 1.5, b: float = 0.75) -> float:
    """BM25 TF-IDF 텍스트 유사도 점수"""
    try:
        q_words = set(query.lower().split())
        t_words = text.lower().split()
        if not q_words or not t_words: return 0.0
        avgdl = max(len(t_words), 1)
        score = 0.0
        for qw in q_words:
            tf = t_words.count(qw) / avgdl
            score += (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (len(t_words) / avgdl)))
        return round(min(score / len(q_words), 1.0), 4)
    except: return 0.0


def _auto_detect_query_type(query: str) -> str:
    """자연어 쿼리에서 최적 검색 모드 자동 감지"""
    q = query.strip().lower()
    if any(kw in q for kw in ['function ', 'class ', 'interface ', 'method ', 'def ']): return 'ast'
    if any(kw in q for kw in ['찾아줘', '검색', 'where is', 'find', 'search']): return 'fuzzy'
    if any(c in query for c in '{}[]()=<>'): return 'exact'
    if '_' in query or any(c.isupper() for c in query if c.isalpha()): return 'fuzzy'
    return 'semantic'


def _fuzzy_match(query: str, text: str, threshold: float = 0.3) -> tuple:
    """퍼지 매칭 — 카멜케이스 + difflib"""
    try:
        import difflib, re as _re
        q, t = query.lower().strip(), text.lower().strip()
        if q == t: return (1.0, 'exact')
        if q in t: return (0.9, 'substring')
        def split_camel(s): return ' '.join(_re.findall(r'[a-z]+|[A-Z][a-z]*|[0-9]+', s))
        r = difflib.SequenceMatcher(None, split_camel(q), split_camel(t)).ratio()
        if r >= threshold: return (round(r, 4), f'camel:{r:.2f}')
        r2 = difflib.SequenceMatcher(None, q.replace('_', ' '), t.replace('_', ' ')).ratio()
        if r2 >= threshold: return (round(r2, 4), f'snake:{r2:.2f}')
        r3 = difflib.SequenceMatcher(None, q, t).ratio()
        if r3 >= threshold: return (round(r3, 4), f'direct:{r3:.2f}')
        return (0.0, 'no_match')
    except: return (0.0, 'error')


def _detect_secrets(content: str) -> list:
    """하드코딩된 시크릿 탐지 (12+ 패턴)"""
    import re as _re
    secrets = []
    patterns = [
        (_re.compile(r'(?i)(?:sk-[a-zA-Z0-9]{20,})'), 'OpenAI Key'),
        (_re.compile(r'(?i)(?:ghp_[a-zA-Z0-9]{36,})'), 'GitHub PAT'),
        (_re.compile(r'(?i)(?:AKIA[0-9A-Z]{16})'), 'AWS Key'),
        (_re.compile(r'(?i)(?:-----BEGIN PRIVATE KEY-----)'), 'Private Key'),
        (_re.compile(r'(?i)password\\s*[:=]\\s*[\\'"][^\\'"]+[\\'"]'), 'Password'),
        (_re.compile(r'(?i)(?:mongodb\\+srv://[^@]+@)'), 'MongoDB URI'),
    ]
    for pat, name in patterns:
        for m in pat.finditer(content):
            secrets.append({'type': name, 'line': content[:m.start()].count('\\n') + 1,
                            'context': content[max(0,m.start()-30):min(len(content),m.end()+30)].replace('\\n',' ').strip()[:100]})
    return secrets


def _find_duplicate_blocks(lines: list, min_lines: int = 5) -> list:
    """파일 내 중복 코드 블록 탐지"""
    import hashlib; dup = []
    try:
        seen = {}
        for i in range(len(lines) - min_lines + 1):
            b = '\\n'.join(lines[i:i+min_lines]).strip()
            if not b or all(l.strip().startswith(('#','//','/*','*')) for l in b.split('\\n') if l.strip()): continue
            h = hashlib.md5(b.encode()).hexdigest()
            if h in seen: dup.append({'s1': seen[h], 's2': i, 'len': min_lines, 'preview': lines[i][:80]})
            else: seen[h] = i
        return dup[:10]
    except: return []


def _estimate_line_complexity(line: str) -> tuple:
    """라인 복잡도 추정 (0-10)"""
    if not line or not line.strip(): return (0, 'empty')
    try:
        s=line.strip(); sc=0; r=[]
        if len(s)>120: sc+=2; r.append('long line')
        elif len(s)>80: sc+=1; r.append('long line')
        for op in ['&&','||','??','?.' ]:
            if op in s: sc+=s.count(op); r.append(f"'{op}'")
        d=m=0
        for c in s:
            if c=='(':d+=1;m=max(m,d)
            elif c==')':d-=1
        if m>=3: sc+=m-2; r.append(f'nested({m})')
        return (min(sc,10), ', '.join(r) if r else 'normal')
    except: return (0,'unknown')


def _get_git_blame_info(file_path: str, line_number: int) -> dict:
    """git blame 정보"""
    import subprocess, datetime
    try:
        r = subprocess.run(['git','blame','-L',f'{line_number},{line_number}','--porcelain',file_path],
                          capture_output=True,text=True,timeout=5,cwd=os.getcwd())
        if r.returncode != 0 or not r.stdout.strip(): return {}
        info = {}
        for l in r.stdout.split('\\n'):
            if l.startswith('author '): info['author'] = l[7:]
            elif l.startswith('author-time '):
                try: info['date'] = datetime.datetime.fromtimestamp(int(l[12:])).isoformat()
                except: pass
            elif l.startswith('summary '): info['message'] = l[8:]
        return info
    except: return {}


def _find_related_tests(file_path: str) -> list:
    """관련 테스트 파일 찾기"""
    from pathlib import Path; tests = []
    try:
        p=Path(file_path); stem=p.stem; parent=p.parent; root=Path(os.getcwd())
        for base in [parent, root]:
            for pat in [f'__tests__/**/{stem}*', f'test/**/{stem}*', f'tests/**/{stem}*']:
                tests.extend(str(c) for c in base.rglob(pat) if c.is_file())
        if parent.exists():
            for sib in parent.glob('*.test.*'):
                if stem in sib.stem: tests.append(str(sib))
        seen=set(); return [t for t in tests if not (t in seen or seen.add(t))][:10]
    except: return []


def _extract_python_imports(content: str) -> list:
    """Python AST import 추출"""
    imports = []
    try:
        import ast as _ast
        tree = _ast.parse(content)
        for node in _ast.walk(tree):
            if isinstance(node, _ast.Import):
                for a in node.names: imports.append({'module': a.name, 'type': 'import'})
            elif isinstance(node, _ast.ImportFrom):
                for a in node.names: imports.append({'module': f'{node.module}.{a.name}', 'type': 'from'})
    except: pass
    return imports


def _extract_go_imports(content: str) -> list:
    """Go import 추출"""
    import re as _re; imports = []
    for m in _re.finditer(r'import\\s+"([^"]+)"', content): imports.append({'module': m.group(1), 'type': 'import'})
    in_block = False
    for line in content.split('\\n'):
        if 'import (' in line: in_block = True; continue
        if in_block and ')' in line: in_block = False; continue
        if in_block:
            m = _re.match(r'\\s*"([^"]+)"', line)
            if m: imports.append({'module': m.group(1), 'type': 'import'})
    return imports
'''

# Insert before Scout section
marker = '# Scout: 코드 탐색 도구'
if marker in content:
    content = content.replace(marker, infra_code + '\n\n' + marker)
    print(f"✅ Inserted {len(missing)} missing functions")
else:
    print("❌ Marker not found!")
    sys.exit(1)

# Verify syntax
try:
    compile(content, BRIDGE, 'exec')
    print("✅ Syntax: OK")
except SyntaxError as e:
    print(f"❌ Syntax error: {e}")
    sys.exit(1)

# Atomic write
tmp = BRIDGE + '.rs'
with open(tmp, 'w', encoding='utf-8') as f:
    f.write(content)
os.replace(tmp, BRIDGE)
print(f"✅ Written: {len(content)} chars, {content.count(chr(10))+1} lines")
print("✅ Infra functions restored!")
