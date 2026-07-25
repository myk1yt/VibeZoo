# VibeZoo Bridge — 범용 유틸리티 함수
# 기존 vibezoo_mcp_bridge.py의 유틸리티 함수들을 이전

import difflib
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from bridge.config import SOURCE_EXTS, DEFAULT_EXCLUDE_DIRS, TS_JS_EXTS, CONFIG_FILES


# ── 시간/포맷 ────────────────────────────────────────


def _get_timestamp() -> str:
    """ISO 8601 타임스탬프 반환"""
    return datetime.now(timezone.utc).isoformat()


def _markdown_header(title: str, status: str = "✅") -> str:
    """간소화된 마크다운 헤더 — AI 소비에 최적화"""
    return f"## {status} {title}\n\n"


def _markdown_footer() -> str:
    """간소화된 푸터"""
    return ""


# ── 검증 ─────────────────────────────────────────────


def _validate_file_path(file_path: str) -> Optional[str]:
    """파일 경로 검증. 문제 시 오류 메시지 반환, 정상 시 None."""
    if not file_path or not file_path.strip():
        return "File path must not be empty."
    p = Path(file_path)
    cwd = os.getcwd()
    if not p.exists():
        if not p.is_absolute():
            attempted = Path(cwd) / file_path
            if not attempted.exists():
                return (
                    f"File not found: `{file_path}`\n"
                    f"- Tried relative path: `{attempted}`\n"
                    f"- Working directory: `{cwd}`\n"
                    f"- Tip: Use an absolute path or verify the file exists relative to the workspace root."
                )
            return None
        return f"File not found: `{file_path}` (absolute path does not exist)"
    if not p.is_file():
        return f"Path is not a file: `{file_path}`"
    return None


def _validate_string(value: Optional[str], name: str) -> Optional[str]:
    """문자열이 비어있지 않은지 검증."""
    if not value or not value.strip():
        return f"`{name}` must not be empty."
    return None


def _validate_int(value: int, name: str, min_val: int = 0, max_val: int = 1000) -> Optional[str]:
    """정수 범위 검증."""
    if not isinstance(value, int):
        return f"`{name}` must be an integer."
    if value < min_val:
        return f"`{name}` must be >= {min_val}."
    if value > max_val:
        return f"`{name}` must be <= {max_val}."
    return None


# ── 파일 I/O ─────────────────────────────────────────


def _iter_project_files(root: Path, extensions: set = None, exclude_dirs: set = None,
                        max_depth: int = -1, include_names: Optional[set[str]] = None) -> list:
    """성능 최적화된 프로젝트 파일 순회 (os.walk, 단일 패스).

    Args:
        include_names: 확장자 없는 파일명 집합 (예: {"Dockerfile", "Makefile"}).
                       extensions와 OR 조건으로 매칭.
    """
    if extensions is None:
        extensions = SOURCE_EXTS
    if exclude_dirs is None:
        exclude_dirs = DEFAULT_EXCLUDE_DIRS

    results = []
    root_str = str(root)
    try:
        for dirpath, dirnames, filenames in os.walk(root_str):
            rel_dir = os.path.relpath(dirpath, root_str)
            if rel_dir != ".":
                parts = rel_dir.replace("\\", "/").split("/")
                if any(part in exclude_dirs for part in parts):
                    dirnames.clear()
                    continue

            dirnames[:] = [d for d in dirnames if d not in exclude_dirs]

            if rel_dir == ".":
                depth = 0
            else:
                depth = len(rel_dir.replace("\\", "/").split("/"))
            if max_depth > 0 and depth > max_depth:
                dirnames.clear()
                continue

            for fname in filenames:
                ext = os.path.splitext(fname)[1]
                if ext in extensions or (include_names and fname in include_names):
                    results.append(Path(dirpath) / fname)
    except (PermissionError, OSError):
        pass
    return results


# ── 파일 스캔 캐시 (중복 스캔 방지, TTL 5초) ─────────

_file_scan_cache: dict = {}
_file_scan_cache_ttl: int = 5


def _iter_project_files_cached(root: Path, extensions: set = None, exclude_dirs: set = None,
                                max_depth: int = -1, include_names: Optional[set[str]] = None) -> list:
    """_iter_project_files 결과를 캐싱하는 래퍼."""
    cache_key = (
        str(root),
        tuple(sorted(extensions)) if extensions else tuple(sorted(SOURCE_EXTS)),
        tuple(sorted(exclude_dirs)) if exclude_dirs else tuple(sorted(DEFAULT_EXCLUDE_DIRS)),
        max_depth,
        tuple(sorted(include_names)) if include_names else None,
    )
    cached = _file_scan_cache.get(cache_key)
    if cached and (time.time() - cached["time"]) < _file_scan_cache_ttl:
        return cached["results"]

    results = _iter_project_files(root, extensions, exclude_dirs, max_depth, include_names)
    _file_scan_cache[cache_key] = {"results": results, "time": time.time()}
    return results


def _read_file_content(path: Path) -> Optional[str]:
    """안전한 파일 읽기"""
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except (OSError, PermissionError):
        return None


def _truncate(text: str, max_len: int = 2000, ellipsis: str = "...") -> str:
    """텍스트를 최대 길이로 자르기"""
    if len(text) <= max_len:
        return text
    return text[:max_len] + f"\n\n[{ellipsis} ({len(text) - max_len} more chars truncated)]"


def _atomic_write_json(file_path: str, data: dict, indent: int = 2):
    """원자적 JSON 파일 쓰기 (부분 쓰기 방지)
    * 수정: 윈도우에서 os.replace()는 VS Code의 fs.watch를 깨뜨리므로
      직접 쓰기(overwrite) 모드로 변경합니다. (TS 쪽에 재시도 로직이 있으므로 안전함)
    """
    base_dir = os.path.dirname(file_path)
    if not base_dir:
        base_dir = os.getcwd()
    os.makedirs(base_dir, exist_ok=True)
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)
        f.flush()
        if hasattr(os, "sync"):
            os.sync()
        elif hasattr(os, "fsync"):
            os.fsync(f.fileno())


def _npx_cmd() -> str:
    """Windows 호환 npx 명령어"""
    return "npx.cmd" if sys.platform == "win32" else "npx"


def _normalize_path(path_str: str) -> str:
    """경로 구분자 통일 (Windows backslash → forward slash)"""
    return path_str.replace("\\", "/")


def get_project_root(target_path: str = "") -> str:
    """프로젝트 루트 경로 반환"""
    if target_path:
        p = Path(target_path)
        if p.exists():
            return str(p if p.is_dir() else p.parent)
    return os.getcwd()


# ── 검색/매칭 유틸 ───────────────────────────────────


def _bm25_score(query: str, text: str, k1: float = 1.5, b: float = 0.75) -> float:
    """BM25 유사도 점수"""
    qw = set(query.lower().split())
    tw = text.lower().split()
    if not qw or not tw:
        return 0.0
    s = 0.0
    avg_len = sum(len(t) for t in tw) / max(len(tw), 1)
    for q in qw:
        tf = tw.count(q) / max(len(tw), 1)
        dl = len(text) / max(avg_len, 1)
        s += (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl))
    return round(min(s / len(qw), 1.0), 4)


def _auto_detect_query_type(query: str) -> str:
    """쿼리 타입 자동 감지"""
    q = query.strip().lower()
    if any(k in q for k in ['function ', 'class ', 'interface ', 'method ', 'def ']):
        return 'ast'
    if any(k in q for k in ['찾아줘', '검색', 'find', 'search']):
        return 'fuzzy'
    if any(c in query for c in '{}[]()=<>'):
        return 'exact'
    return 'fuzzy' if '_' in query or any(c.isupper() for c in query) else 'semantic'


def _fuzzy_match(query: str, text: str, threshold: float = 0.3) -> tuple:
    """퍼지 매칭 — (score, match_type) 반환"""
    q, t = query.lower().strip(), text.lower().strip()
    if q == t:
        return (1.0, 'exact')
    if q in t:
        return (0.9, 'substring')
    sc = lambda s: ' '.join(re.findall(r'[a-z]+|[A-Z][a-z]*|[0-9]+', s))
    r = difflib.SequenceMatcher(None, sc(q), sc(t)).ratio()
    if r >= threshold:
        return (round(r, 4), 'camel')
    r2 = difflib.SequenceMatcher(None, q.replace('_', ' '), t.replace('_', ' ')).ratio()
    if r2 >= threshold:
        return (round(r2, 4), 'snake')
    r3 = difflib.SequenceMatcher(None, q, t).ratio()
    if r3 >= threshold:
        return (round(r3, 4), 'direct')
    return (0.0, 'no_match')


# ── 보안/코드 분석 유틸 ─────────────────────────────


def _detect_secrets(content: str) -> list:
    """코드 내 시크릿/API 키 탐지"""
    secrets = []
    patterns = [
        (r'(?i)sk-[a-zA-Z0-9]{20,}', 'OpenAI Key'),
        (r'(?i)ghp_[a-zA-Z0-9]{36,}', 'GitHub PAT'),
        (r'password.{0,5}[=:].{0,5}[\'"][^\'"]+[\'"]', 'Password'),
        (r'(?i)api[_-]?key.{0,5}[=:].{0,5}[\'"][^\'"]+[\'"]', 'API Key'),
        (r'(?i)mongodb[+]srv://[^@]+@', 'MongoDB URI'),
    ]
    for pat, name in patterns:
        for m in re.finditer(pat, content):
            secrets.append({'type': name, 'line': content[:m.start()].count('\n') + 1})
    return secrets


def _find_duplicate_blocks(lines: list, min_lines: int = 5) -> list:
    """중복 코드 블록 탐지 (hashed)"""
    seen = {}
    duplicates = []
    for i in range(len(lines) - min_lines + 1):
        block = '\n'.join(lines[i:i + min_lines]).strip()
        if not block:
            continue
        h = hashlib.md5(block.encode()).hexdigest()
        if h in seen:
            duplicates.append({
                'block': block[:100],
                'first': seen[h],
                'second': i,
            })
        else:
            seen[h] = i
    return duplicates


# ── HTML 변환 (웹 도구용) ────────────────────────────


def _html_to_markdown(html: str, max_length: int = 50000) -> str:
    """HTML을 깔끔한 마크다운으로 변환 (외부 라이브러리 없이)"""
    try:
        from html.parser import HTMLParser

        class MDConverter(HTMLParser):
            def __init__(self):
                super().__init__()
                self.output = []
                self.skip_tags = {'script', 'style', 'nav', 'footer', 'header', 'noscript'}
                self.in_skip = 0
                self.in_pre = False
                self.list_depth = 0
                self.in_li = False
                self.in_a = False
                self.a_href = ''
                self.in_strong = False
                self.in_em = False
                self.in_code = False
                self.in_h = 0
                self.in_img = False

            def handle_starttag(self, tag, attrs):
                tag = tag.lower()
                if tag in self.skip_tags:
                    self.in_skip += 1
                    return
                if self.in_skip:
                    return

                attrs_dict = dict(attrs)

                if tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
                    self.in_h = int(tag[1])
                    self.output.append('\n' + '#' * self.in_h + ' ')
                elif tag == 'p':
                    self.output.append('\n\n')
                elif tag == 'br':
                    self.output.append('\n')
                elif tag == 'hr':
                    self.output.append('\n\n---\n\n')
                elif tag == 'ul':
                    self.list_depth += 1
                    self.output.append('\n')
                elif tag == 'ol':
                    self.list_depth += 1
                    self.output.append('\n')
                elif tag == 'li':
                    self.in_li = True
                    self.output.append('\n' + '  ' * (self.list_depth - 1) + '- ')
                elif tag == 'a':
                    self.in_a = True
                    self.a_href = attrs_dict.get('href', '')
                elif tag in ('strong', 'b'):
                    self.in_strong = True
                    self.output.append('**')
                elif tag in ('em', 'i'):
                    self.in_em = True
                    self.output.append('*')
                elif tag == 'code':
                    self.in_code = True
                    self.output.append('`')
                elif tag == 'pre':
                    self.in_pre = True
                    self.output.append('\n```\n')
                elif tag == 'blockquote':
                    self.output.append('\n> ')
                elif tag in ('table', 'tr'):
                    self.output.append('\n')
                elif tag == 'th':
                    self.output.append('| **')
                elif tag == 'td':
                    self.output.append('| ')
                elif tag == 'img':
                    alt = attrs_dict.get('alt', '')
                    src = attrs_dict.get('src', '')
                    self.output.append(f'![{alt}]({src})')
                    self.in_img = True
                elif tag == 'div':
                    pass

            def handle_endtag(self, tag):
                tag = tag.lower()
                if tag in self.skip_tags:
                    self.in_skip -= 1
                    return
                if self.in_skip:
                    return

                if self.in_h:
                    self.output.append('\n')
                    self.in_h = 0
                elif tag == 'li':
                    self.in_li = False
                elif tag in ('ul', 'ol'):
                    self.list_depth = max(0, self.list_depth - 1)
                elif tag == 'a':
                    if self.a_href and self.a_href.startswith('http'):
                        self.output.append(f'({self.a_href})')
                    self.in_a = False
                    self.a_href = ''
                elif tag in ('strong', 'b'):
                    self.in_strong = False
                    self.output.append('**')
                elif tag in ('em', 'i'):
                    self.in_em = False
                    self.output.append('*')
                elif tag == 'code':
                    self.in_code = False
                    self.output.append('`')
                elif tag == 'pre':
                    self.in_pre = False
                    self.output.append('\n```\n')
                elif tag == 'blockquote':
                    self.output.append('\n')
                elif tag == 'th':
                    self.output.append('**|')
                elif tag == 'td':
                    self.output.append(' |')
                elif tag == 'tr':
                    self.output.append('\n')
                elif tag == 'table':
                    self.output.append('\n')

            def handle_data(self, data):
                if self.in_skip:
                    return
                if self.in_pre:
                    self.output.append(data)
                else:
                    cleaned = ' '.join(data.split())
                    if cleaned:
                        self.output.append(cleaned)

            def handle_entityref(self, name):
                char = {
                    'amp': '&', 'lt': '<', 'gt': '>', 'quot': '"',
                    'apos': "'", 'nbsp': ' ', '#39': "'",
                }.get(name, f'&{name};')
                if not self.in_skip:
                    self.output.append(char)

        converter = MDConverter()
        converter.feed(html)
        result = ''.join(converter.output)

        # Clean up excessive whitespace
        result = re.sub(r'\n{4,}', '\n\n\n', result)
        result = re.sub(r' {3,}', ' ', result)

        # Truncate
        if len(result) > max_length:
            result = result[:max_length] + f'\n\n... [truncated {len(result) - max_length} more chars]'

        return result.strip()
    except Exception:
        # Fallback: basic strip
        return re.sub(r'<[^>]+>', ' ', html).strip()[:max_length]


# ── Import 추출 (regex fallback) ─────────────────────


def _extract_regex_imports(file_path: str) -> list:
    """파일에서 import 문 추출 (regex fallback)"""
    try:
        content = Path(file_path).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []
    imports = []
    for line in content.split("\n"):
        line = line.strip()
        # TypeScript/JavaScript
        m = re.search(r'(?:from|require)\s*[\'"]([^\'"]+)[\'"]', line)
        if m:
            imports.append(m.group(1))
            continue
        # Python
        m = re.match(r'(?:import|from)\s+([\w.]+)', line)
        if m:
            imports.append(m.group(1))
            continue
        # Go
        m = re.search(r'import\s+"([^"]+)"', line)
        if m:
            imports.append(m.group(1))
            continue
        # Go grouped import
        m = re.search(r'^\s*"([^"]+)"', line)
        if m:
            imports.append(m.group(1))
    return imports


def _extract_python_imports(content: str) -> list:
    """Python import 문 추출 (regex)"""
    imports = []
    for line in content.split("\n"):
        line = line.strip()
        m = re.match(r'import\s+(\w+(?:\.\w+)*)', line)
        if m:
            imports.append({"module": m.group(1), "type": "import", "line": 0})
            continue
        m = re.match(r'from\s+(\w+(?:\.\w+)*)\s+import', line)
        if m:
            imports.append({"module": m.group(1), "type": "from", "line": 0})
    return imports


def _extract_go_imports(content: str) -> list:
    """Go import 문 추출 (regex)"""
    imports = []
    in_group = False
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith('import ('):
            in_group = True
            continue
        if in_group:
            if line == ')':
                in_group = False
                continue
            m = re.match(r'^\s*"([^"]+)"', line)
            if m:
                imports.append({"module": m.group(1), "type": "import", "line": 0})
            continue
        m = re.search(r'import\s+"([^"]+)"', line)
        if m:
            imports.append({"module": m.group(1), "type": "import", "line": 0})
    return imports


# ── Git 유틸 ─────────────────────────────────────────


def _get_git_blame_info(file_path: str, line_number: int) -> dict:
    """Git blame 정보 조회"""
    try:
        r = subprocess.run(['git', 'blame', '-L', f'{line_number},{line_number}', '--porcelain', file_path],
                          capture_output=True, text=True, timeout=5, cwd=os.getcwd())
        if r.returncode != 0:
            return {}
        info = {}
        for l in r.stdout.split('\n'):
            if l.startswith('author '):
                info['author'] = l[7:]
            elif l.startswith('summary '):
                info['message'] = l[8:]
        return info
    except Exception:
        return {}


def _find_related_tests(file_path: str) -> list:
    """관련 테스트 파일 찾기"""
    tests = []
    try:
        p = Path(file_path)
        stem = p.stem
        parent = p.parent
        for base in [parent, Path(os.getcwd())]:
            for pat in [f'__tests__/**/{stem}*', f'test/**/{stem}*']:
                tests.extend(str(c) for c in base.rglob(pat) if c.is_file())
    except Exception:
        pass
    return tests[:5]


# ── ST-08: Token Truncation ────────────────────────────


def truncate_to_tokens(text: str, max_tokens: int) -> str:
    """Truncate text to approximately max_tokens using chars ≈ tokens × 4 heuristic.

    Args:
        text: The text to potentially truncate.
        max_tokens: Maximum approximate token count. If <= 0, returns text unchanged.

    Returns:
        The original text if within the limit, or truncated text with a marker.
    """
    if max_tokens <= 0:
        return text
    max_chars = max_tokens * 4
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n... [truncated to ~{} tokens]".format(max_tokens)
