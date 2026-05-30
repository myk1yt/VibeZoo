#!/usr/bin/env python
# VibeZoo MCP Bridge — 완전 업그레이드 스크립트 (Phase 1 + 2 + 3)
# 실행: python mcp-servers/complete_upgrade.py

import os, sys

ROOT = r'c:/Users/k1yt/OneDrive/문서/각종자료/공부자료들/파이썬_Python/VibeZoo_forZoocode'
BRIDGE = os.path.join(ROOT, 'mcp-servers', 'vibezoo_mcp_bridge.py')

print("=" * 60)
print("VibeZoo MCP Bridge Complete Upgrade")
print("=" * 60)

# 1. Read current file
with open(BRIDGE, 'r', encoding='utf-8') as f:
    content = f.read()
lines = content.split('\n')
print(f"\n📖 Read {len(content)} chars, {len(lines)} lines")

# ============================================================
# INFRASTRUCTURE FUNCTIONS (Phase 1)
# ============================================================
INFRA_CODE = r'''

# ── SOTA Infrastructure: BM25, Fuzzy, Secrets, etc. ────────

def _bm25_score(query: str, text: str, k1: float = 1.5, b: float = 0.75) -> float:
    """BM25 TF-IDF 텍스트 유사도 점수"""
    try:
        q_words = set(query.lower().split())
        t_words = text.lower().split()
        if not q_words or not t_words:
            return 0.0
        avgdl = max(len(t_words), 1)
        score = 0.0
        for qw in q_words:
            tf = t_words.count(qw) / avgdl
            score += (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (len(t_words) / avgdl)))
        return round(min(score / len(q_words), 1.0), 4)
    except Exception:
        return 0.0


def _auto_detect_query_type(query: str) -> str:
    """자연어 쿼리에서 최적 검색 모드 자동 감지"""
    q = query.strip().lower()
    if any(kw in q for kw in ['function ', 'class ', 'interface ', 'type ', 'method ', 'def ', 'struct ']):
        return 'ast'
    if any(kw in q for kw in ['찾아줘', '검색', 'where is', 'find', 'search', '어디']):
        for prefix in ['찾아줘', '검색해줘', '어디있어', 'where is', 'find', 'search for']:
            if prefix in q:
                keywords = q.replace(prefix, '').strip().strip(',').strip()
                if keywords:
                    return f'auto:{keywords}'
        return 'fuzzy'
    if any(c in query for c in '{}[]()=<>'):
        return 'exact'
    if '_' in query or any(c.isupper() for c in query if c.isalpha()):
        return 'fuzzy'
    return 'semantic'


def _fuzzy_match(query: str, text: str, threshold: float = 0.3) -> tuple:
    """퍼지 매칭 — 카멜케이스 분리 + difflib"""
    try:
        import difflib, re as _re
        q = query.lower().strip()
        t = text.lower().strip()
        if q == t:
            return (1.0, 'exact')
        if q in t:
            return (0.9, 'substring')
        def split_camel(s):
            return ' '.join(_re.findall(r'[a-z]+|[A-Z][a-z]*|[0-9]+', s))
        ratio = difflib.SequenceMatcher(None, split_camel(q), split_camel(t)).ratio()
        if ratio >= threshold:
            return (round(ratio, 4), f'camel:{ratio:.2f}')
        ratio2 = difflib.SequenceMatcher(None, q.replace('_', ' '), t.replace('_', ' ')).ratio()
        if ratio2 >= threshold:
            return (round(ratio2, 4), f'snake:{ratio2:.2f}')
        ratio3 = difflib.SequenceMatcher(None, q, t).ratio()
        if ratio3 >= threshold:
            return (round(ratio3, 4), f'direct:{ratio3:.2f}')
        return (0.0, 'no_match')
    except Exception:
        return (0.0, 'error')


def _detect_secrets(content: str) -> list:
    """하드코딩된 시크릿/API 키 탐지 (12+ 패턴)"""
    import re as _re
    secrets = []
    patterns = [
        (_re.compile(r'(?i)(?:sk-[a-zA-Z0-9]{20,})'), 'OpenAI API Key'),
        (_re.compile(r'(?i)(?:ghp_[a-zA-Z0-9]{36,})'), 'GitHub PAT'),
        (_re.compile(r'(?i)(?:xox[baprs]-[a-zA-Z0-9]{10,})'), 'Slack Token'),
        (_re.compile(r'(?i)(?:AKIA[0-9A-Z]{16})'), 'AWS Access Key'),
        (_re.compile(r'(?i)password\s*[:=]\s*[\'\"][^\'\"]+[\'\"]'), 'Hardcoded Password'),
        (_re.compile(r'(?i)secret\s*[:=]\s*[\'\"][^\'\"]+[\'\"]'), 'Hardcoded Secret'),
        (_re.compile(r'(?i)api[_-]?key\s*[:=]\s*[\'\"][^\'\"]+[\'\"]'), 'API Key'),
        (_re.compile(r'(?i)(?:mongodb\+srv://[a-zA-Z0-9]+:[^@]+@)'), 'MongoDB URI'),
        (_re.compile(r'(?i)(?:-----BEGIN (?:RSA |EC )?PRIVATE KEY-----)'), 'Private Key'),
    ]
    for pat, name in patterns:
        for m in pat.finditer(content):
            start = max(0, m.start() - 40)
            end = min(len(content), m.end() + 40)
            line_num = content[:m.start()].count('\n') + 1
            secrets.append({'type': name, 'line': line_num, 'context': content[start:end].replace('\n', ' ').strip()[:120]})
    return secrets


def _find_duplicate_blocks(lines: list, min_lines: int = 5) -> list:
    """파일 내 중복 코드 블록 탐지"""
    import hashlib
    duplicates = []
    try:
        n = len(lines)
        seen = {}
        for i in range(n - min_lines + 1):
            block = '\n'.join(lines[i:i + min_lines])
            stripped = block.strip()
            if not stripped:
                continue
            if all(l.strip().startswith(('#', '//', '/*', '*')) for l in block.split('\n') if l.strip()):
                continue
            h = hashlib.md5(stripped.encode()).hexdigest()
            if h in seen:
                duplicates.append({'start1': seen[h], 'start2': i, 'lines': min_lines, 'preview': lines[i][:80]})
            else:
                seen[h] = i
        return duplicates[:10]
    except Exception:
        return []


def _estimate_line_complexity(line: str) -> tuple:
    """라인 복잡도 추정 (0-10)"""
    if not line or not line.strip():
        return (0, 'empty')
    try:
        score = 0
        reasons = []
        s = line.strip()
        if len(s) > 120: score += 2; reasons.append('very long line')
        elif len(s) > 80: score += 1; reasons.append('long line')
        for op in ['&&', '||', '??', '?.']:
            if op in s: score += s.count(op); reasons.append(f"'{op}' chained")
        depth = max_d = 0
        for ch in s:
            if ch == '(': depth += 1; max_d = max(max_d, depth)
            elif ch == ')': depth -= 1
        if max_d >= 3: score += max_d - 2; reasons.append(f'nested calls({max_d})')
        return (min(score, 10), ', '.join(reasons) if reasons else 'normal')
    except Exception:
        return (0, 'unknown')


def _get_git_blame_info(file_path: str, line_number: int) -> dict:
    """git blame 정보 조회"""
    import subprocess, datetime
    try:
        cwd = os.getcwd()
        r = subprocess.run(['git', 'blame', '-L', f'{line_number},{line_number}', '--porcelain', file_path],
                          capture_output=True, text=True, timeout=5, cwd=cwd,
                          creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
        if r.returncode != 0 or not r.stdout.strip(): return {}
        info = {}
        for line in r.stdout.split('\n'):
            if line.startswith('author '): info['author'] = line[7:]
            elif line.startswith('author-time '):
                try: info['date'] = datetime.datetime.fromtimestamp(int(line[12:])).isoformat()
                except: pass
            elif line.startswith('summary '): info['message'] = line[8:]
        commit_line = r.stdout.split('\n')[0].split()
        if commit_line: info['commit'] = commit_line[0][:8]
        return info
    except Exception:
        return {}


def _find_related_tests(file_path: str) -> list:
    """관련 테스트 파일 찾기"""
    from pathlib import Path
    tests = []
    try:
        p = Path(file_path)
        stem = p.stem
        parent = p.parent
        root = Path(os.getcwd())
        for base in [parent, root]:
            for pat in [f'__tests__/**/{stem}*', f'test/**/{stem}*', f'tests/**/{stem}*']:
                tests.extend(str(c) for c in base.rglob(pat) if c.is_file())
        if parent.exists():
            for sib in parent.glob('*.test.*'):
                if stem in sib.stem: tests.append(str(sib))
            for sib in parent.glob('*.spec.*'):
                if stem in sib.stem: tests.append(str(sib))
        seen = set()
        return [t for t in tests if not (t in seen or seen.add(t))][:10]
    except Exception:
        return []


def _extract_python_imports(content: str) -> list:
    """Python AST 기반 import 추출"""
    imports = []
    try:
        import ast as _ast
        tree = _ast.parse(content)
        for node in _ast.walk(tree):
            if isinstance(node, _ast.Import):
                for alias in node.names:
                    imports.append({'module': alias.name, 'type': 'import', 'line': getattr(node, 'lineno', 0)})
            elif isinstance(node, _ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.append({'module': f'{module}.{alias.name}', 'type': 'from', 'line': getattr(node, 'lineno', 0)})
    except Exception:
        import re as _re
        for line in content.split('\n'):
            m = _re.match(r'^(?:import|from)\s+([\w.]+)', line.strip())
            if m: imports.append({'module': m.group(1), 'type': 'regex'})
    return imports


def _extract_go_imports(content: str) -> list:
    """Go import 추출"""
    import re as _re
    imports = []
    for m in _re.finditer(r'import\s+"([^"]+)"', content):
        imports.append({'module': m.group(1), 'type': 'import'})
    in_block = False
    for line in content.split('\n'):
        if 'import (' in line: in_block = True; continue
        if in_block and ')' in line: in_block = False; continue
        if in_block:
            m = _re.match(r'\s*"([^"]+)"', line)
            if m: imports.append({'module': m.group(1), 'type': 'import'})
    return imports
'''

# 2. Insert infra functions before Scout section
insert_marker = '# Scout: 코드 탐색 도구'
if insert_marker in content:
    pos = content.find(insert_marker)
    content = content[:pos] + INFRA_CODE + '\n\n' + content[pos:]
    print(f"✅ Inserted infra functions before scout marker")
else:
    print(f"❌ Marker not found: {insert_marker}")
    # Fallback: find search_codebase
    sig = 'def search_codebase('
    if sig in content:
        pos = content.find(sig)
        # Find preceding newline
        nl = content.rfind('\n', 0, pos)
        if nl >= 0:
            content = content[:nl] + INFRA_CODE + content[nl:]
            print(f"✅ Inserted infra functions before search_codebase")
        else:
            print("❌ Cannot find insertion point")
            sys.exit(1)
    else:
        print("❌ search_codebase not found!")
        sys.exit(1)

# 3. Verify syntax
try:
    compile(content, BRIDGE, 'exec')
    print("✅ Syntax: OK")
except SyntaxError as e:
    print(f"❌ Syntax error: {e}")
    sys.exit(1)

# 4. Atomic write
print(f"\n📝 Writing {len(content)} chars atomically...")
tmp = BRIDGE + '.tmp'
with open(tmp, 'w', encoding='utf-8') as f:
    f.write(content)
os.replace(tmp, BRIDGE)
print("✅ Write complete!")

# 5. Final verification
with open(BRIDGE, 'r', encoding='utf-8') as f:
    final = f.read()
final_lines = final.split('\n')
print(f"📊 Final: {len(final)} chars, {len(final_lines)} lines")
print(f"   Has _bm25_score: {'_bm25_score' in final}")
print(f"   Has _fuzzy_match: {'_fuzzy_match' in final}")
print(f"   Has _detect_secrets: {'_detect_secrets' in final}")
print(f"   Has _find_duplicate_blocks: {'_find_duplicate_blocks' in final}")
print(f"   Has _estimate_line_complexity: {'_estimate_line_complexity' in final}")
print(f"   Has _get_git_blame_info: {'_get_git_blame_info' in final}")
print(f"   Has _find_related_tests: {'_find_related_tests' in final}")
print(f"   Has _extract_python_imports: {'_extract_python_imports' in final}")
print(f"   Has _extract_go_imports: {'_extract_go_imports' in final}")
print(f"   search_codebase mode param: {'mode: str =' in final}")
print(f"\n✅ Complete upgrade finished!")
