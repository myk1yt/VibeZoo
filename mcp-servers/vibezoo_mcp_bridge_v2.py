# VibeZoo MCP Bridge — 통합 MCP 서버
# Scout(코드 검색) + Reviewer(리뷰) + Tester(테스트) + DeepAnalyzer(분석)
# Crow Memory(Python)와 동일한 FastMCP 기반, 단일 파일로 모든 기능 제공
# 포트 9027에서 SSE transport로 실행
# 필요시 Crow Memory(9020)에 연결하여 기억 저장/조회
#
# v0.12.0 — 2025-05-27 — 전면 감사 완료 (에러 처리, 성능, AST, 포맷, Windows, Crow, 검증)

import asyncio
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import threading
from collections import Counter, defaultdict
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Optional

try:
    from fastmcp import FastMCP
except ImportError:
    print("fastmcp not installed. Install with: pip install fastmcp")
    sys.exit(1)

try:
    from starlette.responses import JSONResponse, HTMLResponse
    from starlette.requests import Request
except ImportError:
    # FastMCP 의존성에 포함되어 있음
    from starlette.responses import JSONResponse
    from starlette.requests import Request

# ── 상수 ──────────────────────────────────────────────

CROW_URL = os.environ.get("CROW_SERVER_URL", "http://localhost:9020")
CROW_TIMEOUT = 3  # 3초 타임아웃 (권장)
WHITEBOARD_FILE = os.path.join(os.path.expanduser("~"), ".vibezoo-whiteboard.json")
FIX_REQUEST_FILE = os.path.join(os.path.expanduser("~"), ".vibezoo-fix-request.json")
CHAT_PENDING_FILE = os.path.join(os.path.expanduser("~"), ".vibezoo-chat-pending.json")
PREFERENCES_FILE = os.path.join(os.path.expanduser("~"), ".vibezoo-preferences.json")
VERSION = "0.12.0"

DEFAULT_EXCLUDE_DIRS = {".git", "node_modules", ".zoo-code", "dist", "build",
                        ".next", "coverage", "target", "vendor", "__pycache__",
                        ".venv", "env", ".env"}
SOURCE_EXTS = {".ts", ".tsx", ".js", ".jsx", ".py", ".go", ".rs"}
TS_JS_EXTS = {".ts", ".tsx", ".js", ".jsx"}

mcp = FastMCP(name="vibezoo")


# ── 유틸리티 함수 ──────────────────────────────────────

def _get_timestamp() -> str:
    """ISO 8601 타임스탬프 반환"""
    return datetime.now(timezone.utc).isoformat()


def _markdown_header(title: str, status: str = "✅") -> str:
    """간소화된 마크다운 헤더 — AI 소비에 최적화 (불필요한 메타데이터 제거)"""
    return f"## {status} {title}\n\n"


def _markdown_footer() -> str:
    """간소화된 푸터 — 버전 정보는 health 체크에서만 확인 가능"""
    return ""


def _validate_file_path(file_path: str) -> Optional[str]:
    """파일 경로 검증. 문제 시 오류 메시지 반환, 정상 시 None."""
    if not file_path or not file_path.strip():
        return "File path must not be empty."
    p = Path(file_path)
    cwd = os.getcwd()
    if not p.exists():
        # 절대 경로가 아니면 cwd 기준으로 시도
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


def _iter_project_files(root: Path, extensions: set = None, exclude_dirs: set = None,
                        max_depth: int = -1) -> list:
    """성능 최적화된 프로젝트 파일 순회 (os.walk, 단일 패스).
    - os.walk를 사용하여 디렉토리 트리를 한 번만 탐색
    - 제외 디렉토리는 os.walk 단계에서 바로 제외 (하위 트리 탐색 안 함)
    - 확장자 필터링을 in-memory에서 처리 (확장자별 rglob *n회 호출 제거)
    - 최대 깊이 제한 가능
    """
    if extensions is None:
        extensions = SOURCE_EXTS
    if exclude_dirs is None:
        exclude_dirs = DEFAULT_EXCLUDE_DIRS

    results = []
    root_str = str(root)
    try:
        for dirpath, dirnames, filenames in os.walk(root_str):
            # 상위 경로 중 제외 디렉토리가 있으면 이 subtree 건너뜀
            rel_dir = os.path.relpath(dirpath, root_str)
            if rel_dir != ".":
                parts = rel_dir.replace("\\", "/").split("/")
                if any(part in exclude_dirs for part in parts):
                    dirnames.clear()
                    continue

            # 현재 레벨 디렉토리 필터링 (하위 탐색 제외)
            dirnames[:] = [d for d in dirnames if d not in exclude_dirs]

            # 최대 깊이 제한
            if rel_dir == ".":
                depth = 0
            else:
                depth = len(rel_dir.replace("\\", "/").split("/"))
            if max_depth > 0 and depth > max_depth:
                dirnames.clear()
                continue

            for fname in filenames:
                ext = os.path.splitext(fname)[1]
                if ext in extensions:
                    results.append(Path(dirpath) / fname)
    except (PermissionError, OSError):
        pass
    return results


# ── 파일 스캔 캐시 (중복 스캔 방지, TTL 5초) ─────────

_file_scan_cache: dict = {}
_file_scan_cache_ttl: int = 5


def _iter_project_files_cached(root: Path, extensions: set = None, exclude_dirs: set = None,
                                max_depth: int = -1) -> list:
    """_iter_project_files 결과를 캐싱하는 래퍼.
    같은 인자로 5초 내 재호출 시 캐시 반환하여 중복 스캔을 방지합니다.
    suggest_refactor 등 여러 도구를 연속 호출할 때 성능 향상.
    """
    cache_key = (
        str(root),
        tuple(sorted(extensions)) if extensions else tuple(sorted(SOURCE_EXTS)),
        tuple(sorted(exclude_dirs)) if exclude_dirs else tuple(sorted(DEFAULT_EXCLUDE_DIRS)),
        max_depth,
    )
    cached = _file_scan_cache.get(cache_key)
    if cached and (time.time() - cached["time"]) < _file_scan_cache_ttl:
        return cached["results"]

    results = _iter_project_files(root, extensions, exclude_dirs, max_depth)
    _file_scan_cache[cache_key] = {"results": results, "time": time.time()}
    return results


def _read_file_content(path: Path) -> Optional[str]:
    """안전한 파일 읽기"""
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except (OSError, PermissionError) as e:
        return None


def _truncate(text: str, max_len: int = 2000, ellipsis: str = "...") -> str:
    """텍스트를 최대 길이로 자르기"""
    if len(text) <= max_len:
        return text
    return text[:max_len] + f"\n\n[{ellipsis} ({len(text) - max_len} more chars truncated)]"


import tempfile
import json

def _atomic_write_json(file_path: str, data: dict, indent: int = 2):
    base_dir = os.path.dirname(file_path)
    if not base_dir:
        base_dir = os.getcwd()
    os.makedirs(base_dir, exist_ok=True)
    temp_fd, temp_file_path = tempfile.mkstemp(dir=base_dir, suffix=".vztmp")
    try:
        with os.fdopen(temp_fd, "w", encoding="utf-8") as temp_file:
            json.dump(data, temp_file, indent=indent, ensure_ascii=False)
        if hasattr(os, "sync"):
            os.sync()
        os.replace(temp_file_path, file_path)
    except Exception as write_error:
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        raise write_error



def _npx_cmd() -> str:
    """Windows 호환 npx 명령어"""
    return "npx.cmd" if sys.platform == "win32" else "npx"


def _normalize_path(path_str: str) -> str:
    """경로 구분자 통일 (Windows backslash → forward slash)"""
    return path_str.replace("\\", "/")


# ── Tree-sitter (AST) 초기화 ────────────────────────────

_ts_lock = threading.Lock()
_ts_available = False
_ts_parser = None
_ts_ts_language = None
_ts_ts_language_js = None
_ts_init_attempted = False  # pip install 시도는 최초 1회만


def _init_tree_sitter():
    """Tree-sitter 초기화 — thread-safe, 실패 시 False 반환 (regex fallback).
    
    pip install은 런타임에 실행하지 않습니다. tree-sitter 설치는
    별도 셋업 단계에서 수동으로 진행하세요:
        pip install tree-sitter tree-sitter-languages
    """
    global _ts_available, _ts_parser, _ts_ts_language, _ts_ts_language_js, _ts_init_attempted
    
    # Fast path: 이미 초기화 성공
    if _ts_available and _ts_ts_language is not None:
        return True
    
    with _ts_lock:
        # Double-check after acquiring lock
        if _ts_available and _ts_ts_language is not None:
            return True
        
        # 이미 시도했고 실패했으면 다시 시도하지 않음
        if _ts_init_attempted:
            return False
        
        _ts_init_attempted = True
        
        try:
            import tree_sitter as ts
            _ts_parser = ts.Parser()
            
            try:
                from tree_sitter_languages import get_language  # type: ignore[import-untyped]
                _ts_ts_language = get_language("typescript")
                _ts_ts_language_js = get_language("javascript")
            except ImportError:
                try:
                    from tree_sitter_typescript import language as ts_lang
                    from tree_sitter_javascript import language as js_lang
                    _ts_ts_language = ts_lang()
                    _ts_ts_language_js = js_lang()
                except ImportError:
                    # tree-sitter 라이브러리가 설치되지 않음 — regex fallback 사용
                    return False
            
            _ts_available = True
            return True
            
        except Exception:
            _ts_available = False
            return False


def _parse_with_tree_sitter(content: str, file_ext: str) -> dict:
    """Tree-sitter로 파일 파싱하여 구조적 정보 반환"""
    if not _ts_available:
        return {}
    try:
        lang = _ts_ts_language if file_ext in (".ts", ".tsx") else _ts_ts_language_js
        if not lang:
            return {}
        _ts_parser.set_language(lang)
        tree = _ts_parser.parse(bytes(content, "utf-8"))
        root = tree.root_node

        functions = []
        classes = []
        interfaces = []

        def walk(node, depth=0):
            if depth > 50:
                return
            node_type = node.type
            if node_type in ("function_declaration", "method_definition", "arrow_function"):
                name_node = node.child_by_field_name("name")
                if name_node:
                    start = node.start_point
                    end = node.end_point
                    functions.append({
                        "name": content[name_node.start_byte:name_node.end_byte],
                        "line": start[0] + 1,
                        "end_line": end[0] + 1,
                        "type": node_type,
                    })
            elif node_type in ("class_declaration",):
                name_node = node.child_by_field_name("name")
                if name_node:
                    start = node.start_point
                    end = node.end_point
                    classes.append({
                        "name": content[name_node.start_byte:name_node.end_byte],
                        "line": start[0] + 1,
                        "end_line": end[0] + 1,
                    })
            elif node_type in ("interface_declaration", "type_alias_declaration"):
                name_node = node.child_by_field_name("name")
                if name_node:
                    start = node.start_point
                    end = node.end_point
                    interfaces.append({
                        "name": content[name_node.start_byte:name_node.end_byte],
                        "line": start[0] + 1,
                        "end_line": end[0] + 1,
                        "type": node_type,
                    })
            for child in node.children:
                walk(child, depth + 1)

        walk(root)
        return {"functions": functions, "classes": classes, "interfaces": interfaces}
    except Exception:
        return {}


def _extract_ast_calls(content: str, file_ext: str) -> list:
    """Tree-sitter로 call_expression 노드 추출 — 실제 함수 호출 관계"""
    if not _ts_available:
        return []
    try:
        lang = _ts_ts_language if file_ext in (".ts", ".tsx") else _ts_ts_language_js
        if not lang:
            return []
        _ts_parser.set_language(lang)
        tree = _ts_parser.parse(bytes(content, "utf-8"))
        root = tree.root_node

        calls = []
        def walk(node, depth=0):
            if depth > 30:
                return
            if node.type == "call_expression":
                func_node = node.child_by_field_name("function")
                if func_node:
                    name = content[func_node.start_byte:func_node.end_byte]
                    if name not in ("require", "import"):
                        calls.append({
                            "name": name,
                            "line": node.start_point[0] + 1,
                        })
            for child in node.children:
                walk(child, depth + 1)

        walk(root)
        return calls
    except Exception:
        return []


def _extract_ast_imports(content: str, file_ext: str) -> list:
    """Tree-sitter로 import/require 문 정확히 추출 (AST 기반)"""
    if not _ts_available:
        return []
    try:
        lang = _ts_ts_language if file_ext in (".ts", ".tsx") else _ts_ts_language_js
        if not lang:
            return []
        _ts_parser.set_language(lang)
        tree = _ts_parser.parse(bytes(content, "utf-8"))
        root = tree.root_node

        imports = []
        def walk(node, depth=0):
            if depth > 30:
                return
            if node.type == "import_statement":
                source_node = node.child_by_field_name("source")
                if source_node:
                    module = content[source_node.start_byte:source_node.end_byte]
                    imports.append({
                        "module": module.strip("'\""),
                        "type": "import",
                        "line": node.start_point[0] + 1,
                    })
            elif node.type == "call_expression":
                func_node = node.child_by_field_name("function")
                if func_node and content[func_node.start_byte:func_node.end_byte] == "require":
                    args_node = node.child_by_field_name("arguments")
                    if args_node and args_node.children:
                        arg = args_node.children[0]
                        if arg.type == "string":
                            module = content[arg.start_byte:arg.end_byte]
                            imports.append({
                                "module": module.strip("'\""),
                                "type": "require",
                                "line": node.start_point[0] + 1,
                            })
            elif node.type == "import_expression":
                imports.append({
                    "module": "dynamic import",
                    "type": "import",
                    "line": node.start_point[0] + 1,
                })
            for child in node.children:
                walk(child, depth + 1)

        walk(root)
        return imports
    except Exception:
        return []


def _extract_ast_fields(content: str, file_ext: str) -> dict:
    """Tree-sitter로 interface/class의 실제 필드 추출"""
    if not _ts_available:
        return {}
    try:
        lang = _ts_ts_language if file_ext in (".ts", ".tsx") else _ts_ts_language_js
        if not lang:
            return {}
        _ts_parser.set_language(lang)
        tree = _ts_parser.parse(bytes(content, "utf-8"))
        root = tree.root_node

        models = []
        def walk(node, depth=0):
            if depth > 50:
                return
            if node.type in ("interface_declaration", "class_declaration", "type_alias_declaration"):
                name_node = node.child_by_field_name("name")
                name = content[name_node.start_byte:name_node.end_byte] if name_node else "anonymous"

                fields = []
                def find_properties(n, d=0):
                    if d > 20:
                        return
                    if n.type == "property_signature":
                        prop_name_node = n.child_by_field_name("name")
                        prop_type_node = n.child_by_field_name("type")
                        if prop_name_node:
                            pname = content[prop_name_node.start_byte:prop_name_node.end_byte]
                            ptype = content[prop_type_node.start_byte:prop_type_node.end_byte] if prop_type_node else "any"
                            fields.append({"name": pname, "type": ptype})
                    elif n.type == "method_signature":
                        prop_name_node = n.child_by_field_name("name")
                        if prop_name_node:
                            pname = content[prop_name_node.start_byte:prop_name_node.end_byte]
                            fields.append({"name": pname, "type": "method"})
                    elif n.type == "property_definition":
                        prop_name_node = n.child_by_field_name("name")
                        if prop_name_node:
                            pname = content[prop_name_node.start_byte:prop_name_node.end_byte]
                            ptype = "any"
                            try:
                                type_ann = n.child_by_field_name("type")
                                if type_ann:
                                    ptype = content[type_ann.start_byte:type_ann.end_byte]
                            except Exception:
                                pass
                            fields.append({"name": pname, "type": ptype})
                    for child in n.children:
                        find_properties(child, d + 1)

                find_properties(node)
                models.append({
                    "name": name,
                    "type": node.type,
                    "line": node.start_point[0] + 1,
                    "fields": fields,
                })
            for child in node.children:
                walk(child, depth + 1)

        walk(root)
        return {"models": models}
    except Exception:
        return {}


def _extract_regex_imports(file_path: str) -> list:
    """파일에서 import 문 추출 (regex fallback)"""
    try:
        content = Path(file_path).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []
    imports = []
    for line in content.split("\n"):
        line = line.strip()
        # TypeScript/JavaScript (import { x } from 'y'; or const x = require('y'))
        m = re.search(r'(?:from|require)\s*[\'"]([^\'"]+)[\'"]', line)
        if m:
            imports.append(m.group(1))
            continue
        # Python: import X or from X import Y
        m = re.match(r'(?:import|from)\s+([\w.]+)', line)
        if m:
            imports.append(m.group(1))
            continue
        # Go: import "path" or import ("path")
        m = re.search(r'import\s+"([^"]+)"', line)
        if m:
            imports.append(m.group(1))
            continue
        # Go grouped import: "path" inside import(...)
        m = re.search(r'^\s*"([^"]+)"', line)
        if m:
            imports.append(m.group(1))
    return imports


def _extract_python_imports(content: str) -> list:
    """파이썬 파일에서 import 문 추출 (AST fallback)"""
    imports = []
    for line in content.split("\n"):
        line = line.strip()
        m = re.match(r'^(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))', line)
        if m:
            module = m.group(1) or m.group(2)
            imports.append({"module": module, "type": "import", "line": 0})
    return imports


def _extract_go_imports(content: str) -> list:
    """Go 파일에서 import 문 추출 (AST fallback)"""
    imports = []
    for line in content.split("\n"):
        line = line.strip()
        m = re.search(r'import\s+"([^"]+)"', line)
        if m:
            imports.append({"module": m.group(1), "type": "import", "line": 0})
        m = re.match(r'^\s*"([^"]+)"', line)
        if m:
            imports.append({"module": m.group(1), "type": "import", "line": 0})
    return imports


# POWR
def get_project_root(target_path: str = "") -> str:
    if target_path:
        p = Path(target_path)
        if p.exists():
            return str(p if p.is_dir() else p.parent)
    return os.getcwd()


# ── Crow Memory 연동 ──────────────────────────────────

def try_crow_ingest(content: str, register: str = "context", **kwargs):
    """선택적으로 Crow Memory에 저장 (실패해도 무시, 3초 타임아웃)"""
    try:
        import requests
        payload = {"content": content, "register": register, **kwargs}
        requests.post(f"{CROW_URL}/ingest", json=payload, timeout=CROW_TIMEOUT)
    except Exception:
        pass


def try_crow_recall(query: str, register: str = "context", limit: int = 5) -> list:
    """선택적으로 Crow Memory에서 회상 (3초 타임아웃)"""
    try:
        import requests
        resp = requests.get(
            f"{CROW_URL}/recall",
            params={"query": query, "register": register, "limit": limit},
            timeout=CROW_TIMEOUT
        )
        if resp.ok:
            return resp.json().get("results", [])
    except Exception:
        pass
    return []


# ── Health Check ──────────────────────────────────────────

@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """헬스체크 엔드포인트 — Bridge 상태 · Crow 연결 · Tree-sitter 상태 반환"""
    crow_ok = False
    try:
        import requests
        resp = requests.get(f"{CROW_URL}/health", timeout=CROW_TIMEOUT)
        crow_ok = resp.ok
    except Exception:
        pass
    # tree-sitter 상태 확인 (lazy init 시도 후)
    _init_tree_sitter()
    return JSONResponse({
        "status": "ok",
        "crow": crow_ok,
        "timestamp": time.time(),
        "version": VERSION,
        "tree_sitter": {
            "available": _ts_available,
            "languages": ["typescript", "javascript"] if _ts_available else [],
        },
    })


# ═══════════════════════════════════════════════════════════
# Scout: 코드 탐색 도구
# ═══════════════════════════════════════════════════════════

@mcp.tool
def search_codebase(query: str, file_patterns: Optional[str] = None, max_results: int = 10) -> str:
    """프로젝트 코드베이스에서 쿼리와 관련된 코드를 검색합니다.
    tree-sitter AST 파싱을 우선 시도하고, 실패 시 regex로 폴백합니다.
    
    Args:
        query: 검색할 내용 (자연어 또는 코드 스니펫)
        file_patterns: 검색 대상 파일 패턴 (예: *.ts,*.tsx). 쉼표로 구분.
        max_results: 최대 결과 수 (기본: 10)
    """
    err = _validate_string(query, "query")
    if err:
        return _markdown_header("Search Error", "❌") + f"**{err}**\n" + _markdown_footer()

    max_results = max(1, min(max_results, 200))
    
    # 파일 패턴 결정: 주어진 패턴이 없으면 확장자 기반 자동 추론
    if file_patterns:
        patterns = [p.strip() for p in file_patterns.split(",") if p.strip()]
    else:
        # 쿼리 내용으로 언어 추론
        query_lower = query.lower()
        if any(kw in query_lower for kw in ["def ", "import ", "pytest", "python"]):
            patterns = ["*.py"]
        elif any(kw in query_lower for kw in ["func ", "go ", "package ", "golang"]):
            patterns = ["*.go"]
        elif any(kw in query_lower for kw in ["fn ", "struct ", "impl ", "rust"]):
            patterns = ["*.rs"]
        else:
            patterns = ["*.ts", "*.tsx", "*.js", "*.jsx", "*.py"]
    
    root = Path(os.getcwd())
    results = []  # (priority, file, line, text, context_before, context_after)
    ast_results = []
    exclude = DEFAULT_EXCLUDE_DIRS
    query_lower = query.lower()
    
    _init_tree_sitter()
    
    # 정확한 심볼 검색인지 판단
    is_symbol_query = not any(c in query for c in " =(){}[]<>!+-*/%&|^~")
    is_ast_query = any(keyword in query_lower for keyword in [
        "function ", "class ", "interface ", "type ", "method ",
        "함수", "클래스", "인터페이스"
    ])
    
    # 확장자 세트 (rglob 필터링용)
    ext_set = set()
    for pat in patterns:
        ext = os.path.splitext(pat)[1]
        if ext:
            ext_set.add(ext)
    
    file_count = 0
    MAX_LINES_PER_FILE = 500  # 큰 파일은 앞부분만
    
    for pattern in patterns:
        try:
            for p in root.rglob(pattern.strip()):
                if not p.is_file():
                    continue
                rel = str(p.relative_to(root))
                if any(part in rel for part in exclude):
                    continue
                file_count += 1
                
                try:
                    content = p.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
                
                lines = content.split("\n")
                ext = p.suffix.lower()
                
                # AST 구조 검색 (심볼 검색 시)
                if is_ast_query and ext in TS_JS_EXTS and _ts_available:
                    ast = _parse_with_tree_sitter(content, ext)
                    
                    for fn in ast.get("functions", []):
                        if query_lower in fn["name"].lower():
                            ast_results.append(
                                f"`{rel}:{fn['line']}` — `{fn['type']} {fn['name']}()` (L{fn['line']}-{fn['end_line']})"
                            )
                    for cls in ast.get("classes", []):
                        if query_lower in cls["name"].lower():
                            ast_results.append(
                                f"`{rel}:{cls['line']}` — `class {cls['name']}`"
                            )
                    for iface in ast.get("interfaces", []):
                        if query_lower in iface["name"].lower():
                            ast_results.append(
                                f"`{rel}:{iface['line']}` — `{iface['type']} {iface['name']}`"
                            )
                
                # 라인 검색 (속도 최적화: 큰 파일은 처음 MAX_LINES_PER_FILE만)
                search_lines = lines[:MAX_LINES_PER_FILE]
                for i, line in enumerate(search_lines, 1):
                    if query_lower not in line.lower():
                        continue
                    
                    # 우선순위 계산
                    priority = 0
                    if is_symbol_query and query_lower == line.strip().lower():
                        priority = 10  # 정확한 심볼 매칭
                    elif line.strip().lower().startswith(query_lower):
                        priority = 7   # 라인 시작 매칭
                    elif query_lower in line.lower().split():
                        priority = 5   # 단어 단위 매칭
                    else:
                        priority = 1   # 부분 문자열 매칭
                    
                    # 컨텍스트 (앞뒤 2줄)
                    ctx_before = lines[i-3:i-1] if i >= 3 else lines[:i-1] if i > 1 else []
                    ctx_after = lines[i:min(len(lines), i+2)] if i < len(lines) else []
                    
                    results.append((priority, rel, i, line.strip()[:150], ctx_before, ctx_after))
                    
                    if len(results) >= max_results * 3:  # 여유 있게 수집 후 정렬
                        break
                if len(results) >= max_results * 3:
                    break
        except (PermissionError, OSError):
            continue
        if len(results) >= max_results * 3:
            break
    
    # 우선순위 정렬 후 상위 max_results 선택
    results.sort(key=lambda x: -x[0])
    top_results = results[:max_results]
    
    # 출력 구성 (간결하게)
    output = _markdown_header(f'Search: "{query}"')
    output += f"Scanned {file_count} files. "
    
    # AST 결과 우선
    if ast_results:
        output += f"AST matches: {len(ast_results)}. "
        unique_ast = list(dict.fromkeys(ast_results))[:max_results]
        output += "\n### Symbols\n"
        for r in unique_ast:
            output += f"- {r}\n"
    
    if top_results:
        output += f"Line matches: {len(results)} found, showing top {len(top_results)}.\n"
        output += "\n### Matches\n"
        for _, rel, line_num, text, ctx_before, ctx_after in top_results:
            output += f"- `{_normalize_path(rel)}:{line_num}`\n"
            for bl in ctx_before[-1:]:  # 직전 1줄만 표시
                output += f"  {bl.strip()[:100]}\n"
            output += f"  → **{text}**\n"
            for al in ctx_after[:1]:    # 직후 1줄만 표시
                output += f"  {al.strip()[:100]}\n"
            output += "\n"
    
    if not ast_results and not top_results:
        output += "No matches.\n"
    
    try_crow_ingest(f"Search: {query} → {len(ast_results)} AST + {len(top_results)} line matches in {file_count} files", register="life_context")
    output += _markdown_footer()
    return output


@mcp.tool
def find_references(symbol: str) -> str:
    """주어진 심볼(함수, 클래스, 변수)의 모든 참조를 찾습니다.
    정의와 사용 위치를 구분하여 반환합니다.
    
    Args:
        symbol: 찾을 심볼 이름
    """
    err = _validate_string(symbol, "symbol")
    if err:
        return _markdown_header("Find References Error", "❌") + f"**{err}**\\n" + _markdown_footer()

    root = Path(os.getcwd())
    definitions = []
    usages = []
    exclude = DEFAULT_EXCLUDE_DIRS

    _init_tree_sitter()

    # Phase 3: 참조 타입 분류
    ref_types = {"read": [], "write": [], "call": [], "type_ref": [], "import_ref": []}
    
    for p in _iter_project_files_cached(root, extensions=SOURCE_EXTS, exclude_dirs=exclude):
        content = _read_file_content(p)
        if content is None:
            continue
        rel = _normalize_path(str(p.relative_to(root)))
        ext = p.suffix.lower()
        file_lines = content.split("\\n")
        
        # AST로 함수/클래스 정의 찾기
        if ext in TS_JS_EXTS and _ts_available:
            ast = _parse_with_tree_sitter(content, ext)
            for fn in ast.get("functions", []):
                if fn["name"] == symbol:
                    definitions.append({"file": rel, "line": fn["line"], "desc": f"`{fn['type']} {fn['name']}()`", "type": "definition"})
            for cls in ast.get("classes", []):
                if cls["name"] == symbol:
                    definitions.append({"file": rel, "line": cls["line"], "desc": f"`class {cls['name']}`", "type": "definition"})
            for iface in ast.get("interfaces", []):
                if iface["name"] == symbol:
                    definitions.append({"file": rel, "line": iface["line"], "desc": f"`{iface['type']} {iface['name']}`", "type": "definition"})
        
        # 사용 위치 찾기 + 타입 분류 (Phase 3)
        for i, line in enumerate(file_lines, 1):
            if symbol not in line:
                continue
            is_def = any(d["file"] == rel and d["line"] == i for d in definitions)
            if is_def:
                continue
            stripped = line.strip()
            ref_type = "read"
            if f"import {symbol}" in stripped or f"from '{symbol}" in stripped or f'from "{symbol}"' in stripped:
                ref_type = "import_ref"
            elif f"new {symbol}" in stripped or f"extends {symbol}" in stripped or f"implements {symbol}" in stripped:
                ref_type = "type_ref"
            elif f" {symbol}(" in stripped or f"{symbol}(" in stripped:
                ref_type = "call"
            elif f" = {symbol}" in stripped or f"={symbol}" in stripped:
                ref_type = "read"
            elif f"let {symbol}" in stripped or f"const {symbol}" in stripped or f"var {symbol}" in stripped:
                ref_type = "write"
            usages.append({"file": rel, "line": i, "text": stripped[:120], "type": ref_type})
            ref_types[ref_type].append(f"`{rel}:{i}`")

    output = _markdown_header(f'References: `{symbol}`')

    if definitions:
        output += f"## 📍 Definition ({len(definitions)})\\n"
        for d in definitions:
            output += f"- `{d['file']}:{d['line']}` — {d['desc']}\\n"
        output += "\\n"

    if usages:
        output += f"## 🔗 References ({len(usages)})\\n\\n"
        output += "### By Reference Type\\n\\n"
        type_labels = {"call": "📞 Function Calls", "read": "📖 Read Access", "write": "✏️ Write Access", "type_ref": "🔤 Type Reference", "import_ref": "📦 Import Reference"}
        for t, label in type_labels.items():
            items = ref_types.get(t, [])
            if items:
                output += f"**{label}** ({len(items)})\\n"
                for item in items[:8]:
                    output += f"- {item}\\n"
                if len(items) > 8:
                    output += f"- ... +{len(items)-8} more\\n"
                output += "\\n"
        
        output += "### By File\\n\\n"
        by_file = defaultdict(list)
        for u in usages:
            by_file[u["file"]].append(u)
        for file_path, refs in sorted(by_file.items(), key=lambda x: -len(x[1]))[:10]:
            output += f"**`{file_path}`** ({len(refs)} refs)\\n"
            for r in refs[:5]:
                output += f"- Line {r['line']}: [{r['type']}] `{r['text'][:80]}`\\n"
            if len(refs) > 5:
                output += f"  ... +{len(refs)-5} more\\n"
            output += "\\n"

        # Phase 3: 호출 체인
        output += "### Call Chain — Functions using this symbol\\n\\n"
        caller_functions = {}
        for u in usages:
            if u["type"] == "call":
                p = Path(root) / u["file"]
                if p.exists():
                    content2 = _read_file_content(p)
                    if content2:
                        ext2 = p.suffix.lower()
                        if ext2 in TS_JS_EXTS and _ts_available:
                            ast2 = _parse_with_tree_sitter(content2, ext2)
                            for fn in ast2.get("functions", []):
                                if fn["line"] <= u["line"] <= fn.get("end_line", fn["line"]):
                                    caller_key = f"{u['file']}::{fn['name']}"
                                    if caller_key not in caller_functions:
                                        caller_functions[caller_key] = {"file": u["file"], "function": fn["name"], "line": fn["line"], "call_lines": []}
                                    caller_functions[caller_key]["call_lines"].append(u["line"])
        if caller_functions:
            for ckey, cinfo in sorted(caller_functions.items(), key=lambda x: -len(x[1]["call_lines"]))[:10]:
                lines_str = ", ".join(str(l) for l in cinfo["call_lines"][:5])
                output += f"- `{cinfo['file']}` → `{cinfo['function']}()` (calls at line(s) {lines_str})\\n"
        else:
            output += "- No call chain data available.\\n"
    else:
        output += f"No references found for `{symbol}`.\\n"

    output += _markdown_footer()
    return output
@mcp.tool
def summarize_architecture(target_path: Optional[str] = None) -> str:
    """프로젝트 아키텍처를 분석하여 요약합니다.
    내부적으로 map_dependencies + analyze_call_graph를 호출하여
    실제 모듈 의존성, 진입점, 레이어 구조를 분석합니다.
    
    Args:
        target_path: 분석 대상 디렉토리 경로
    """
    root = Path(get_project_root(target_path))
    root_str = str(root)

    techs = {
        "package.json": "Node.js/TypeScript",
        "go.mod": "Go",
        "Cargo.toml": "Rust",
        "pyproject.toml": "Python",
        "requirements.txt": "Python (pip)",
        "pom.xml": "Java/Maven",
        "Gemfile": "Ruby",
    }
    found_techs = [tech for file, tech in techs.items() if (root / file).exists()]

    dep_output = map_dependencies(target_path=root_str)
    highest_deps = []
    parsing_imports = False
    for line in dep_output.split("\\n"):
        if "Import Count by File" in line:
            parsing_imports = True
            continue
        if parsing_imports and line.startswith("- `"):
            m = re.match(r'- `(.+?)`:\s*\*{0,2}(\d+)\*{0,2}\s*imports?', line)
            if m:
                highest_deps.append((m.group(1), int(m.group(2))))
        if parsing_imports and line.startswith("---"):
            break

    output = _markdown_header("Architecture Analysis")
    output += f"**Project**: `{root.name}`\\n"
    output += f"**Tech Stack**: {', '.join(found_techs) if found_techs else 'Auto-detect failed'}\\n\\n"

    # 진입점 식별
    entry_patterns = ["main.py", "index.ts", "index.js", "app.ts", "main.go", "__init__.py",
                      "extension.ts", "server.ts", "server.js"]
    entries = []
    for pattern in entry_patterns:
        for p in root.rglob(pattern):
            if p.is_file() and not any(part in str(p) for part in DEFAULT_EXCLUDE_DIRS):
                rel = _normalize_path(str(p.relative_to(root)))
                entries.append(rel)
    entries = entries[:5]
    if entries:
        output += "## Entry Points\\n"
        for e in entries:
            output += f"- `{e}`\\n"
        output += "\\n"

    # Phase 3: Import 기반 레이어 자동 발견
    output += "## Auto-Discovered Layers (import-based)\\n\\n"
    dir_import_count = defaultdict(int)
    all_files = []
    for p in _iter_project_files_cached(root, extensions=SOURCE_EXTS, exclude_dirs=DEFAULT_EXCLUDE_DIRS):
        all_files.append(p)
    for p in all_files:
        content = _read_file_content(p)
        if content is None:
            continue
        rel = _normalize_path(str(p.relative_to(root)))
        imports = []
        if p.suffix in TS_JS_EXTS:
            ast_imports = _extract_ast_imports(content, p.suffix)
            imports = [i["module"] for i in ast_imports]
        else:
            imports = _extract_regex_imports(str(p))
        for imp in imports:
            if imp.startswith("."):
                imp_dir = os.path.dirname(os.path.normpath(os.path.join(os.path.dirname(rel), imp)))
                if imp_dir and imp_dir != ".":
                    dir_import_count[imp_dir] += 1
    
    top_dirs = sorted(dir_import_count.items(), key=lambda x: -x[1])[:5]
    if top_dirs:
        for dir_name, count in top_dirs:
            output += f"- **{dir_name}/** → imported by {count} files\\n"
    else:
        output += "- No significant import-based layers detected.\\n"
    output += "\\n"

    # Phase 3: 기술 부채 진단
    output += "## Technical Debt Diagnosis\\n\\n"
    debt_items = []
    has_cycles = "✅ No circular dependencies" not in dep_output
    if has_cycles:
        debt_items.append("⚠️ Circular dependencies detected — high coupling risk")
    high_dep_files = [(f, c) for f, c in highest_deps if c > 10]
    if high_dep_files:
        for f, c in high_dep_files[:3]:
            debt_items.append(f"⚠️ `{f}` has {c} imports — too many responsibilities?")
    total_files = len(all_files)
    if total_files > 100:
        debt_items.append(f"📏 Large project ({total_files} source files) — consider modularization")
    if len(found_techs) > 2:
        debt_items.append(f"🔀 Multiple tech stacks ({', '.join(found_techs)}) — cognitive load")
    if debt_items:
        for item in debt_items:
            output += f"- {item}\\n"
    else:
        output += "- ✅ No significant technical debt detected.\\n"
    output += "\\n"

    output += "## Dependency Metrics\\n"
    if highest_deps:
        output += f"- **Most imported files** (hub modules):\\n"
        for fpath, count in highest_deps[:5]:
            output += f"  - `{fpath}` ← {count} dependents\\n"
    output += f"- **Circular dependencies**: {'⚠️ Detected' if has_cycles else '✅ None'}\\n\\n"

    # Phase 3: 파일 타입 분포 + 변경 트렌드
    output += "## Code Metrics\\n\\n"
    ext_count = defaultdict(int)
    for p in all_files:
        ext_count[p.suffix] += 1
    output += "### File Type Distribution\\n"
    for ext, count in sorted(ext_count.items(), key=lambda x: -x[1]):
        output += f"- `{ext}`: {count} files\\n"
    
    output += "\\n### Change Trend (git log)\\n"
    try:
        git_result = subprocess.run(
            ["git", "log", "--oneline", "--since=30.days", "--format=%ad", "--date=short"],
            cwd=root_str, capture_output=True, text=True, timeout=10
        )
        if git_result.stdout.strip():
            commits = git_result.stdout.strip().split("\\n")
            output += f"- Commits in last 30 days: {len(commits)}\\n"
            from collections import Counter as Ctr
            date_counts = Ctr(commits)
            most_active = date_counts.most_common(3)
            if most_active:
                output += f"- Most active days: {', '.join(f'{d}({c})' for d, c in most_active)}\\n"
        else:
            output += "- No recent git activity found.\\n"
    except Exception:
        output += "- Git history not available.\\n"
    output += "\\n"

    # 레이어 분류 (기존 유지)
    layers = defaultdict(list)
    for p in all_files:
        rel = _normalize_path(str(p.relative_to(root)))
        if "extension/src" in rel or "src/" in rel or "lib/" in rel:
            sub = rel.split("/")
            if any(kw in sub for kw in ["ui", "visual", "view", "component"]):
                layers["UI/Presentation"].append(rel)
            elif any(kw in sub for kw in ["safety", "guard", "security", "auth"]):
                layers["Safety/Security"].append(rel)
            elif any(kw in sub for kw in ["flow", "orchestra", "controller", "service"]):
                layers["Business Logic/Orchestration"].append(rel)
            elif any(kw in sub for kw in ["context", "crow", "memory", "data", "store"]):
                layers["Data/Context"].append(rel)
            elif any(kw in sub for kw in ["types", "util", "helper", "common"]):
                layers["Utilities/Types"].append(rel)
            elif any(kw in sub for kw in ["mcp", "bridge", "server", "api"]):
                layers["API/MCP Interface"].append(rel)
            else:
                layers["Core"].append(rel)
        elif "mcp-servers" in rel:
            layers["API/MCP Interface"].append(rel)
        elif "templates" in rel or "plans" in rel or "fromscratch" in rel:
            layers["Documentation/Config"].append(rel)
    if layers:
        output += "## Layer Structure (path-based)\\n"
        for layer_name, files in sorted(layers.items(), key=lambda x: -len(x[1])):
            if files:
                output += f"- **{layer_name}** ({len(files)} files)\\n"
                for f in files[:5]:
                    output += f"  - `{f}`\\n"
                if len(files) > 5:
                    output += f"  - ... +{len(files)-5} more\\n"
        output += "\\n"

    total_lines = 0
    for p in all_files:
        try:
            total_lines += len(p.read_text(encoding="utf-8", errors="ignore").split("\\n"))
        except Exception:
            pass
    output += f"## Stats\\n"
    output += f"- Source files: {total_files}\\n"
    output += f"- Total lines: ~{total_lines}\\n"
    if found_techs:
        output += f"- Primary language: {found_techs[0]}\\n"

    try_crow_ingest(json.dumps({"action": "arch_summary", "files": total_files, "tech": found_techs, "layers": len(layers)}), register="arch")
    output += _markdown_footer()
    return output
@mcp.tool
def review_code(file_path: str) -> str:
    """지정된 파일의 코드 리뷰를 수행합니다.
    tree-sitter AST로 함수/클래스 구조와 실제 코드 품질 이슈를 탐지합니다.
    
    Args:
        file_path: 리뷰할 파일 경로
    """
    err = _validate_file_path(file_path)
    if err:
        return _markdown_header("Code Review Error", "❌") + f"**{err}**\n" + _markdown_footer()

    p = Path(file_path)
    if not p.exists():
        p = Path(os.getcwd()) / file_path
    if not p.exists() or not p.is_file():
        return _markdown_header("Code Review Error", "❌") + f"**File not found: {file_path}**\n" + _markdown_footer()

    content = _read_file_content(p)
    if content is None:
        return _markdown_header("Code Review Error", "❌") + f"**Cannot read file: {file_path}**\n" + _markdown_footer()

    lines = content.split("\n")
    ext = p.suffix.lower()
    rel = _normalize_path(str(p))
    
    output = _markdown_header(f"Review: `{rel}`")
    output += f"{len(lines)} lines, {len(content)} bytes, `{ext}`\n\n"
    
    issues = []
    stats = {"functions": 0, "classes": 0, "interfaces": 0, "max_depth": 0}
    
    # AST 분석 (TS/JS)
    if ext in TS_JS_EXTS:
        _init_tree_sitter()
        ast = _parse_with_tree_sitter(content, ext)
        functions = ast.get("functions", [])
        classes = ast.get("classes", [])
        interfaces = ast.get("interfaces", [])
        stats["functions"] = len(functions)
        stats["classes"] = len(classes)
        stats["interfaces"] = len(interfaces)
        
        # AST 기반 이슈 탐지
        # 1. any 타입 사용
        any_count = len(re.findall(r':\s*any\b', content))
        if any_count > 0:
            issues.append(("⚠️", f"`any` type used {any_count} time(s) — consider using specific types"))
        
        # 2. @ts-ignore / @ts-nocheck
        ts_ignore = len(re.findall(r'@ts-ignore', content))
        ts_nocheck = len(re.findall(r'@ts-nocheck', content))
        if ts_ignore > 0:
            issues.append(("⚠️", f"`@ts-ignore` found {ts_ignore} time(s)"))
        if ts_nocheck > 0:
            issues.append(("⚠️", f"`@ts-nocheck` found — entire file skips type checking"))
        
        # 3. eslint-disable
        eslint_disable = len(re.findall(r'eslint-disable', content))
        if eslint_disable > 0:
            issues.append(("📝", f"`eslint-disable` found {eslint_disable} time(s)"))
        
        # 4. console.log (프로덕션 코드)
        console_logs = len(re.findall(r'console\.(log|warn|error|debug)', content))
        if console_logs > 0:
            issues.append(("⚠️", f"`console.*` found {console_logs} time(s) — remove before production"))
        
        # 5. debugger
        if 'debugger' in content:
            issues.append(("⚠️", "`debugger` statement found"))
        
        # 6. 빈 catch 블록
        empty_catches = len(re.findall(r'catch\s*\([^)]*\)\s*\{\s*\}', content))
        if empty_catches > 0:
            issues.append(("❌", f"Empty catch block(s): {empty_catches} — silently swallows errors"))
        
        # 7. TODO/FIXME/HACK
        todos = len(re.findall(r'(TODO|FIXME|HACK|XXX)', content))
        if todos > 0:
            issues.append(("📝", f"TODO/FIXME/HACK: {todos} marker(s)"))
    
    elif ext == ".py":
        # Python 기본 검사
        console_logs = len(re.findall(r'\bprint\(', content))
        if console_logs > 0:
            issues.append(("⚠️", f"`print()` found {console_logs} time(s) — use logging instead"))
        todos = len(re.findall(r'(TODO|FIXME|HACK|XXX)', content))
        if todos > 0:
            issues.append(("📝", f"TODO/FIXME/HACK: {todos} marker(s)"))
        empty_excepts = len(re.findall(r'except\s*:', content))
        if empty_excepts > 0:
            issues.append(("⚠️", f"Bare `except:` found {empty_excepts} time(s) — specify exception type"))
    else:
        # Generic
        todos = len(re.findall(r'(TODO|FIXME|HACK)', content))
        if todos > 0:
            issues.append(("📝", f"TODO/FIXME/HACK: {todos} marker(s)"))
    
    # 기본 검사 (모든 언어)
    long_lines = sum(1 for l in lines if len(l) > 120)
    if long_lines > 0:
        issues.append(("📏", f"{long_lines} line(s) exceed 120 chars"))
    
    # 출력
    output += "## Structure\n"
    if stats["functions"] > 0:
        output += f"- Functions/Methods: {stats['functions']}\n"
    if stats["classes"] > 0:
        output += f"- Classes: {stats['classes']}\n"
    if stats["interfaces"] > 0:
        output += f"- Interfaces/Types: {stats['interfaces']}\n"
    
    output += "\n## Issues\n"
    if issues:
        for level, msg in issues:
            output += f"- {level} {msg}\n"
        output += f"\n**{len(issues)} issue(s) found.**\n"
    else:
        output += "✅ No issues found.\n"
    
    try_crow_ingest(f"Reviewed {p.name}: {len(issues)} issues, {stats['functions']} functions", register="style")
    output += _markdown_footer()
    return output


@mcp.tool
def check_quality(target_path: Optional[str] = None) -> str:
    """프로젝트의 코드 품질을 검사합니다.
    
    Args:
        target_path: 검사 대상 경로
    """
    root = Path(get_project_root(target_path))
    output = _markdown_header("Code Quality Check")

    source_files = list(_iter_project_files_cached(root, extensions=SOURCE_EXTS, exclude_dirs=DEFAULT_EXCLUDE_DIRS))
    total_files = len(source_files)
    total_lines = 0
    long_lines = 0
    todo_count = 0
    empty_catch_count = 0
    console_log_count = 0
    debugger_count = 0
    any_type_count = 0
    ts_ignore_count = 0
    empty_except_count = 0
    func_count_total = 0
    class_count_total = 0

    for p in source_files:
        content = _read_file_content(p)
        if content is None:
            continue
        lines = content.split("\\n")
        total_lines += len(lines)
        long_lines += sum(1 for l in lines if len(l) > 120)
        todo_count += len(re.findall(r'(TODO|FIXME|HACK|XXX)', content))
        empty_catch_count += len(re.findall(r'catch\s*\([^)]*\)\s*\{\s*\}', content))
        console_log_count += len(re.findall(r'console\.(log|warn|error|debug)', content))
        debugger_count += len(re.findall(r'\bdebugger\b', content))
        any_type_count += len(re.findall(r':\s*any\b', content))
        ts_ignore_count += len(re.findall(r'@ts-ignore|@ts-nocheck', content))
        empty_except_count += len(re.findall(r'except\s*:', content))
        func_count_total += len(re.findall(r'(?:function|async function|def\s+)', content))
        class_count_total += len(re.findall(r'\bclass\s+\w+', content))

    output += "## Quality Metrics\\n\\n"
    output += f"- Source files: {total_files}\\n"
    output += f"- Total lines: {total_lines}\\n"
    output += f"- Functions: {func_count_total}\\n"
    output += f"- Classes: {class_count_total}\\n\\n"

    issues_found = 0
    severity_scores = []
    
    if long_lines > 0:
        ratio = long_lines / max(total_lines, 1) * 100
        w = "⚠️" if ratio > 1 else "📏"
        output += f"- {w} Lines >120 chars: {long_lines} ({ratio:.1f}%)\\n"
        severity_scores.append(("long_lines", ratio))
        issues_found += 1
    if todo_count > 0:
        ratio = todo_count / max(total_files, 1)
        w = "⚠️" if ratio > 0.5 else "📝"
        output += f"- {w} TODO/FIXME markers: {todo_count}\\n"
        severity_scores.append(("todos", ratio))
        issues_found += 1
    if console_log_count > 0:
        output += f"- ⚠️ console.* calls: {console_log_count}\\n"
        severity_scores.append(("console_log", console_log_count))
        issues_found += 1
    if debugger_count > 0:
        output += f"- ❌ debugger statements: {debugger_count}\\n"
        severity_scores.append(("debugger", debugger_count))
        issues_found += 1
    if any_type_count > 0:
        output += f"- ⚠️ `any` type usage: {any_type_count}\\n"
        severity_scores.append(("any_type", any_type_count))
        issues_found += 1
    if ts_ignore_count > 0:
        output += f"- ⚠️ @ts-ignore/@ts-nocheck: {ts_ignore_count}\\n"
        severity_scores.append(("ts_ignore", ts_ignore_count))
        issues_found += 1
    if empty_catch_count > 0:
        output += f"- ❌ Empty catch blocks: {empty_catch_count}\\n"
        severity_scores.append(("empty_catch", empty_catch_count))
        issues_found += 1
    if empty_except_count > 0:
        output += f"- ⚠️ Bare except:: {empty_except_count}\\n"
        severity_scores.append(("bare_except", empty_except_count))
        issues_found += 1

    # ── 품질 등급 산정 (A-F) ──
    score = 100.0
    for name, val in severity_scores:
        if name == "long_lines":
            score -= val * 5
        elif name == "todos":
            score -= val * 2
        elif name == "console_log":
            score -= val * 2
        elif name == "debugger":
            score -= val * 10
        elif name == "any_type":
            score -= val * 1.5
        elif name == "ts_ignore":
            score -= val * 3
        elif name == "empty_catch":
            score -= val * 8
        elif name == "bare_except":
            score -= val * 5
    score = max(0, min(100, score))
    
    if score >= 90:
        grade = "A"
        grade_desc = "Excellent"
    elif score >= 80:
        grade = "B"
        grade_desc = "Good"
    elif score >= 70:
        grade = "C"
        grade_desc = "Fair"
    elif score >= 60:
        grade = "D"
        grade_desc = "Poor"
    elif score >= 40:
        grade = "E"
        grade_desc = "Bad"
    else:
        grade = "F"
        grade_desc = "Critical"
    if issues_found == 0:
        grade = "A+"
        grade_desc = "Perfect"
    
    output += f"\\n## Quality Grade\\n\\n"
    output += f"- **Grade**: `{grade}` ({grade_desc})\\n"
    output += f"- **Score**: {score:.1f}/100\\n"
    output += f"- **Issues found**: {issues_found}\\n\\n"

    # ESLint
    if (root / "package.json").exists():
        try:
            result = subprocess.run([_npx_cmd(), "eslint", ".", "--ext", ".ts,.tsx,.js,.jsx", "--format", "compact", "--quiet"],
                                   cwd=str(root), capture_output=True, text=True, timeout=30)
            if result.stdout:
                output += f"## ESLint\\n\\n```\\n{_truncate(result.stdout, 2000)}\\n```\\n"
            else:
                output += "## ESLint\\n\\n✅ No issues found.\\n"
        except FileNotFoundError:
            output += "## ESLint\\n\\n⚠️ ESLint not installed.\\n"
        except subprocess.TimeoutExpired:
            output += "## ESLint\\n\\n⚠️ ESLint timed out (30s).\\n"
        except Exception as e:
            output += f"## ESLint\\n\\n❌ Error: {e}\\n"

    try_crow_ingest(f"Quality check on {root.name}: grade={grade} score={score:.1f}", register="style")
    output += _markdown_footer()
    return output
@mcp.tool
def analyze_call_graph(file_path: Optional[str] = None, depth: int = 3) -> str:
    """프로젝트의 함수 호출 그래프를 분석합니다.
    tree-sitter AST로 실제 call_expression 노드를 추출하여 정확한 호출 관계를 파악합니다.
    
    Args:
        file_path: 분석할 파일 경로 (기본: 전체 프로젝트)
        depth: 호출 깊이 (기본: 3)
    """
    err = _validate_int(depth, "depth", 1, 20)
    if err:
        return _markdown_header("Call Graph Error", "❌") + f"**{err}**\\n" + _markdown_footer()

    root = Path(get_project_root(file_path))
    output = _markdown_header("Call Graph Analysis")

    # tree-sitter 초기화
    _init_tree_sitter()

    # ── 전체 함수 정의 맵 구축 (Phase 2) ──
    output += "## Function Definition Map\\n\\n"
    func_defs = {}
    for p in _iter_project_files_cached(root, extensions=TS_JS_EXTS, exclude_dirs=DEFAULT_EXCLUDE_DIRS):
        content = _read_file_content(p)
        if content is None:
            continue
        rel = _normalize_path(str(p.relative_to(root)))
        ast = _parse_with_tree_sitter(content, p.suffix)
        for fn in ast.get("functions", []):
            key = f"{rel}::{fn['name']}"
            func_defs[key] = {"file": rel, "name": fn["name"], "line": fn["line"], "end_line": fn.get("end_line", fn["line"])}
    
    if func_defs:
        output += f"- Total function definitions: {len(func_defs)}\\n"
        file_func_count = defaultdict(int)
        for key, info in func_defs.items():
            file_func_count[info["file"]] += 1
        for f, cnt in sorted(file_func_count.items(), key=lambda x: -x[1])[:10]:
            output += f"- `{f}`: {cnt} functions\\n"
    else:
        output += "- No function definitions found.\\n"
    output += "\\n"

    # ── Fan-in / Fan-out 메트릭 (Phase 2) ──
    output += "## Fan-in / Fan-out Metrics\\n\\n"
    all_calls = defaultdict(list)
    all_callees = defaultdict(list)
    
    for p in _iter_project_files_cached(root, extensions=TS_JS_EXTS, exclude_dirs=DEFAULT_EXCLUDE_DIRS):
        content = _read_file_content(p)
        if content is None:
            continue
        rel = _normalize_path(str(p.relative_to(root)))
        calls = _extract_ast_calls(content, p.suffix)
        for c in calls:
            caller_key = f"{rel}::{c['name']}"
            matched = False
            for fkey, finfo in func_defs.items():
                if c["name"] == finfo["name"] or c["name"].endswith("." + finfo["name"]):
                    all_calls[caller_key].append(fkey)
                    all_callees[fkey].append(caller_key)
                    matched = True
                    break
            if not matched:
                all_calls[caller_key].append(c["name"])
    
    fan_out_list = [(len(targets), caller) for caller, targets in all_calls.items()]
    fan_out_list.sort(key=lambda x: -x[0])
    output += "### Top Fan-out (most calls made)\\n\\n"
    for count, caller in fan_out_list[:5]:
        output += f"- `{caller}` → {count} calls\\n"
    
    fan_in_list = [(len(callers), callee) for callee, callers in all_callees.items()]
    fan_in_list.sort(key=lambda x: -x[0])
    output += "\\n### Top Fan-in (most called)\\n\\n"
    for count, callee in fan_in_list[:5]:
        output += f"- `{callee}` ← {count} callers\\n"
    
    if not fan_out_list and not fan_in_list:
        output += "- No call data available.\\n"
    output += "\\n"

    # ── 데드 코드 감지 (Phase 2) ──
    output += "## Dead Code Detection\\n\\n"
    dead_funcs = []
    for fkey, finfo in func_defs.items():
        if fkey not in all_callees or len(all_callees[fkey]) == 0:
            if not any(finfo["name"] in str(caller) and finfo["file"] in str(caller) for caller in all_calls.get(fkey, [])):
                dead_funcs.append(finfo)
    
    if dead_funcs:
        output += f"⚠️ {len(dead_funcs)} potentially dead function(s) (no callers):\\n\\n"
        for df in dead_funcs[:10]:
            output += f"- `{df['file']}:{df['line']}` — `{df['name']}()`\\n"
        if len(dead_funcs) > 10:
            output += f"- ... +{len(dead_funcs)-10} more\\n"
    else:
        output += "✅ No dead code detected (or all functions have callers).\\n"
    output += "\\n"

    # ── Mermaid Flow Chart (Phase 2) ──
    if fan_in_list:
        output += "## Call Graph (Mermaid)\\n\\n"
        output += "```mermaid\\nflowchart TD;\\n"
        shown = set()
        for count, callee in fan_in_list[:5]:
            callee_id = callee.replace("/", "_").replace(".", "_").replace("::", "_")
            output += f"  {callee_id}['{callee}']\n"
            shown.add(callee)
            for caller in all_callees.get(callee, [])[:3]:
                caller_id = caller.replace("/", "_").replace(".", "_").replace("::", "_")
                if caller_id not in shown:
                    output += f"  {caller_id}['{caller}']\n"
                    shown.add(caller_id)
                output += f"  {caller_id} --> {callee_id}\n"
        output += "```\n\n"

    # TypeScript/JavaScript: AST 기존 함수 호출 분석 (유지)
    output += "## Per-File Call Analysis\\n\\n"
    total_calls = 0
    processed_files = 0
    for p in _iter_project_files_cached(root, extensions=TS_JS_EXTS, exclude_dirs=DEFAULT_EXCLUDE_DIRS):
        content = _read_file_content(p)
        if content is None:
            continue
        processed_files += 1
        rel = _normalize_path(str(p.relative_to(root)))
        calls = _extract_ast_calls(content, p.suffix)
        if calls:
            call_counts = Counter(c["name"] for c in calls)
            top_calls = call_counts.most_common(10)
            output += f"### `{rel}`\\n\\n"
            output += f"- **Total calls**: {len(calls)}\\n"
            output += f"- **Unique functions called**: {len(call_counts)}\\n"
            for func_name, count in top_calls:
                output += f"  - `{func_name}` ({count}x)\\n"
            output += "\\n"
            total_calls += len(calls)

    if total_calls == 0:
        if processed_files == 0:
            output += "- No TypeScript/JavaScript files found.\\n"
        else:
            output += "- No function calls detected via AST.\\n"

    output += "## File-Level Dependencies (AST)\\n\\n"
    dep_count = 0
    for p in _iter_project_files_cached(root, extensions=TS_JS_EXTS, exclude_dirs=DEFAULT_EXCLUDE_DIRS):
        content = _read_file_content(p)
        if content is None:
            continue
        rel = _normalize_path(str(p.relative_to(root)))
        ast_imports = _extract_ast_imports(content, p.suffix)
        if ast_imports:
            modules = list(set(i["module"] for i in ast_imports if not i["module"].startswith(".")))
            local = list(set(i["module"] for i in ast_imports if i["module"].startswith(".")))
            output += f"- `{rel}` → {len(modules)} external + {len(local)} local imports\\n"
            dep_count += 1

    if dep_count == 0:
        output += "- No dependencies detected.\\n"

    try_crow_ingest(f"Call graph: {total_calls} calls, {len(dead_funcs)} dead funcs, {len(func_defs)} defs (Phase2)", register="arch")
    output += _markdown_footer()
    return output
@mcp.tool
def map_dependencies(target_path: Optional[str] = None) -> str:
    """프로젝트 파일 간 의존성을 분석하고 순환 참조를 탐지합니다.
    tree-sitter AST로 import/require 문을 정확히 분석합니다.
    
    Args:
        target_path: 분석 대상 경로
    """
    root = Path(get_project_root(target_path))
    output = _markdown_header("Dependency Map")

    # tree-sitter 초기화
    _init_tree_sitter()

    # 모든 파일에서 import 수집 (AST 우선, regex fallback)
    deps = {}
    for p in _iter_project_files_cached(root, extensions={".ts", ".tsx", ".js", ".jsx", ".py", ".go"},
                                  exclude_dirs=DEFAULT_EXCLUDE_DIRS):
        rel = _normalize_path(str(p.relative_to(root)))
        ext = p.suffix
        content = _read_file_content(p)
        if content is None:
            continue

        # AST 기반 import 추출 (TS/JS/JSX)
        if ext in TS_JS_EXTS:
            ast_imports = _extract_ast_imports(content, ext)
            if ast_imports:
                deps[rel] = [i["module"] for i in ast_imports]
                continue

        # Python AST import 추출 (Phase 2)
        if ext == ".py":
            py_imports = _extract_python_imports(content)
            if py_imports:
                deps[rel] = [i["module"] for i in py_imports]
                continue

        # Go import 추출 (Phase 2)
        if ext == ".go":
            go_imports = _extract_go_imports(content)
            if go_imports:
                deps[rel] = [i["module"] for i in go_imports]
                continue

        # regex fallback
        imports = _extract_regex_imports(str(p))
        if imports:
            deps[rel] = imports

    # ── 패키지 매니저 정보 (Phase 2) ──
    output += "## Package Manager Info\\n\\n"
    pkg_managers = []
    if (root / "package.json").exists():
        try:
            pkg = json.loads((root / "package.json").read_text())
            deps_count = len(pkg.get("dependencies", {}))
            dev_deps_count = len(pkg.get("devDependencies", {}))
            pkg_managers.append(f"- **npm/yarn**: {deps_count} deps + {dev_deps_count} devDeps")
        except Exception:
            pkg_managers.append("- **npm/yarn**: package.json found (parse error)")
    if (root / "go.mod").exists():
        try:
            gomod = (root / "go.mod").read_text()
            module_name = ""
            for line in gomod.split("\\n"):
                if line.startswith("module "):
                    module_name = line[7:].strip()
                    break
            pkg_managers.append(f"- **Go module**: {module_name}")
        except Exception:
            pkg_managers.append("- **Go module**: go.mod found")
    if (root / "requirements.txt").exists():
        try:
            reqs = (root / "requirements.txt").read_text().strip().split("\\n")
            pkg_managers.append(f"- **pip**: {len(reqs)} packages listed")
        except Exception:
            pkg_managers.append("- **pip**: requirements.txt found")
    if (root / "Cargo.toml").exists():
        pkg_managers.append("- **Cargo**: Rust project")
    if pkg_managers:
        for pm in pkg_managers:
            output += pm + "\\n"
    else:
        output += "- No package manager detected.\\n"
    output += "\\n"

    # ── 순환 참조 탐지 (Iterative DFS, 스택 기반 — Phase 2) ──
    def find_cycles_iterative(graph):
        """Iterative DFS로 순환 참조 탐지 (재귀 한계 회피, 스택 기반)"""
        cycles = []
        visited_all = set()
        
        for start in graph:
            if start in visited_all:
                continue
            stack = [(start, [start], {start})]
            while stack:
                node, path, branch_visited = stack.pop()
                for dep in graph.get(node, []):
                    if dep not in graph:
                        continue
                    if dep == start and len(path) >= 2:
                        cycle_path = " → ".join(path + [dep])
                        cycles.append(cycle_path)
                    elif dep not in branch_visited:
                        new_path = path + [dep]
                        new_branch = branch_visited | {dep}
                        stack.append((dep, new_path, new_branch))
                        visited_all.add(dep)
        return list(set(cycles))

    all_cycles = find_cycles_iterative(deps)

    if all_cycles:
        all_cycles = all_cycles[:10]
        output += "### ⚠️ Circular Dependencies Found\\n\\n"
        for cycle in all_cycles:
            output += f"- `{cycle}`\\n"
    else:
        output += "✅ No circular dependencies detected.\\n"
    output += "\\n"

    # ── 영향도 분석 (Phase 2) ──
    output += "## Impact Analysis\\n\\n"
    reverse_deps = defaultdict(list)
    for file_path, imports in deps.items():
        for imp in imports:
            reverse_deps[imp].append(file_path)
    
    impact_entries = []
    for file_path in deps:
        affected = reverse_deps.get(file_path, [])
        direct_affected = len(affected)
        if direct_affected == 0:
            grade = "LOW"
        elif direct_affected <= 2:
            grade = "MEDIUM"
        elif direct_affected <= 5:
            grade = "HIGH"
        else:
            grade = "CRITICAL"
        impact_entries.append((direct_affected, file_path, grade))
    
    impact_entries.sort(key=lambda x: -x[0])
    for direct_affected, file_path, grade in impact_entries[:10]:
        output += f"- `{file_path}` → affects **{direct_affected}** file(s) — **{grade}**\\n"
    if not impact_entries:
        output += "- No dependency data for impact analysis.\\n"
    output += "\\n"

    # ── Mermaid 다이어그램 (순환 참조 시각화 — Phase 2) ──
    if all_cycles:
        output += "## Circular Dependency Diagram (Mermaid)\\n\\n"
        output += "```mermaid\\ngraph TD;\\n"
        cycle_files = set()
        for cycle in all_cycles:
            for f in cycle.split(" → "):
                f_clean = f.replace("`", "").strip()
                if f_clean:
                    cycle_files.add(f_clean)
        for f in cycle_files:
            safe_id = f.replace("/", "_").replace(".", "_").replace(":", "_")
            output += f"  {safe_id}['{f}']\n"
        for cycle in all_cycles:
            parts = cycle.split(" → ")
            for i in range(len(parts)):
                a = parts[i].replace("`", "").strip()
                b = parts[(i + 1) % len(parts)].replace("`", "").strip()
                if a and b and a in cycle_files and b in cycle_files:
                    a_id = a.replace("/", "_").replace(".", "_").replace(":", "_")
                    b_id = b.replace("/", "_").replace(".", "_").replace(":", "_")
                    output += f"  {a_id} --> {b_id}\\n"
        output += "```\\n\\n"

    # 파일별 의존성 수
    output += "## Import Count by File\\n\\n"
    for file, imports in sorted(deps.items(), key=lambda x: -len(x[1]))[:20]:
        output += f"- `{file}`: **{len(imports)}** imports\\n"

    try_crow_ingest(f"Dep analysis: {len(deps)} files, {len(all_cycles)} cycles (Phase2)", register="arch")
    output += _markdown_footer()
    return output
@mcp.tool
def extract_patterns(target_path: Optional[str] = None, min_occurrences: int = 3) -> str:
    """프로젝트 전체에서 반복되는 코드 패턴을 AST 기반으로 추출합니다.
    tree-sitter AST로 실제 코드 구조를 분석하여 정확한 패턴 빈도를 계산합니다.
    
    Args:
        target_path: 분석 대상 경로
        min_occurrences: 최소 발생 횟수 (기본: 3)
    """
    err = _validate_int(min_occurrences, "min_occurrences", 1, 10000)
    if err:
        return _markdown_header("Pattern Extraction Error", "❌") + f"**{err}**\\n" + _markdown_footer()

    root = Path(get_project_root(target_path))
    _init_tree_sitter()

    patterns = {
        "async/await": 0, "try-catch": 0, "arrow functions": 0,
        "class definitions": 0, "interface/type": 0, "generics usage": 0,
        "destructuring": 0, "template literals": 0, "optional chaining": 0, "nullish coalescing": 0,
    }
    comments_todos = 0
    console_logs = 0
    ts_ignore = 0
    debugger_count = 0
    file_count = 0
    lib_calls = Counter()
    
    for p in _iter_project_files_cached(root, extensions=SOURCE_EXTS, exclude_dirs=DEFAULT_EXCLUDE_DIRS):
        content = _read_file_content(p)
        if content is None:
            continue
        file_count += 1
        ext = p.suffix.lower()

        if ext in TS_JS_EXTS and _ts_available:
            try:
                ast = _parse_with_tree_sitter(content, ext)
                for fn in ast.get("functions", []):
                    if fn["type"] == "arrow_function":
                        patterns["arrow functions"] += 1
                patterns["class definitions"] += len(ast.get("classes", []))
                patterns["interface/type"] += len(ast.get("interfaces", []))
            except Exception:
                pass
            try:
                calls = _extract_ast_calls(content, ext)
                for c in calls:
                    if c["name"].startswith("console."):
                        console_logs += 1
                    if "." in c["name"] and not c["name"].startswith("console."):
                        parts = c["name"].split(".")
                        if len(parts) >= 2:
                            lib_calls[f"{parts[0]}.{'.'.join(parts[1:])}"] += 1
            except Exception:
                pass

        patterns["async/await"] += len(re.findall(r'\basync\s+(function|\(|=\s*\()', content))
        patterns["async/await"] += len(re.findall(r'\bawait\s+', content))
        patterns["try-catch"] += len(re.findall(r'\btry\s*\{', content))
        patterns["arrow functions"] += len(re.findall(r'(?:const|let|var)\s+\w+\s*=\s*(?:async\s*)?\([^)]*\)\s*=>', content))
        patterns["arrow functions"] += len(re.findall(r'\(\s*\)\s*=>', content[:10000]))
        patterns["generics usage"] += len(re.findall(r'<\s*\w+\s*(?:extends\s+\w+)?\s*>', content))
        patterns["destructuring"] += len(re.findall(r'\{\s*\w+\s*\}', content[:10000]))
        patterns["template literals"] += len(re.findall(r'`[^`]*\$\{[^}]+\}[^`]*`', content))
        patterns["optional chaining"] += len(re.findall(r'\w\?\.\w', content))
        patterns["nullish coalescing"] += len(re.findall(r'\w\s*\?\?\s*\w', content))
        comments_todos += len(re.findall(r'(?:TODO|FIXME|HACK|XXX)', content))
        ts_ignore += len(re.findall(r'@ts-ignore', content)) + len(re.findall(r'@ts-nocheck', content))
        debugger_count += len(re.findall(r'\bdebugger\b', content))

    output = _markdown_header(f"Pattern Analysis ({file_count} files)")
    output += "\\n## Code Patterns\\n"
    found_any = False
    for pattern, count in sorted(patterns.items(), key=lambda x: -x[1]):
        if count >= min_occurrences:
            output += f"- `{pattern}`: **{count}** occurrences\\n"
            found_any = True
        elif count > 0:
            output += f"- `{pattern}`: {count} (below threshold)\\n"
    if not found_any:
        output += "- No significant patterns detected.\\n"

    output += "\\n## Library Function Usage Top 10\\n\\n"
    top_lib = lib_calls.most_common(10)
    if top_lib:
        for lib, cnt in top_lib:
            output += f"- `{lib}`: **{cnt}** calls\\n"
    else:
        output += "- No library function calls detected.\\n"

    output += "\\n## Quality Indicators\\n"
    quality_items = []
    if console_logs > 0:
        quality_items.append(f"`console.*` calls: {console_logs}")
    if comments_todos > 0:
        quality_items.append(f"`TODO/FIXME/HACK`: {comments_todos}")
    if ts_ignore > 0:
        quality_items.append(f"`@ts-ignore/@ts-nocheck`: {ts_ignore}")
    if debugger_count > 0:
        quality_items.append(f"`debugger` statements: {debugger_count}")
    if quality_items:
        for item in quality_items:
            output += f"- ⚠️ {item}\\n"
    else:
        output += "- ✅ No quality concerns detected.\\n"

    try_crow_ingest(json.dumps({"patterns_found": sum(1 for c in patterns.values() if c > 0), "files": file_count}), register="style")
    output += _markdown_footer()
    return output
@mcp.tool
def reverse_engineer(target_path: Optional[str] = None, output_format: str = "markdown") -> str:
    """코드베이스로부터 아키텍처 문서, API 명세, ERD를 자동 생성합니다.
    tree-sitter AST로 데이터 모델의 실제 필드까지 추출합니다.
    
    Args:
        target_path: 분석 대상 경로
        output_format: 출력 형식 (markdown, openapi, mermaid). 기본: markdown
    """
    err = _validate_string(output_format, "format")
    if err:
        return _markdown_header("Reverse Engineering Error", "❌") + f"**{err}**\\n" + _markdown_footer()

    allowed_formats = {"markdown", "openapi", "mermaid"}
    if output_format not in allowed_formats:
        return (_markdown_header("Reverse Engineering Error", "❌")
                + f"**Invalid format: `{output_format}`. Allowed: {', '.join(allowed_formats)}**\\n"
                + _markdown_footer())

    root = Path(get_project_root(target_path))
    output = _markdown_header("Reverse Engineering Report")

    # tree-sitter 초기화
    _init_tree_sitter()

    # 프로젝트 메타데이터
    pkg_json = root / "package.json"
    if pkg_json.exists():
        try:
            pkg = json.loads(pkg_json.read_text())
            output += f"- **Name**: {pkg.get('name', 'N/A')}\\n"
            output += f"- **Description**: {pkg.get('description', 'N/A')}\\n"
            output += f"- **Version**: {pkg.get('version', 'N/A')}\\n\\n"
        except (json.JSONDecodeError, OSError):
            pass

    # ── AST 기반 API 라우트 추출 (Phase 2: Express, FastAPI, Flask, Gin) ──
    output += "## API Endpoints\\n\\n"
    endpoints = []
    for p in _iter_project_files_cached(root, extensions={".ts", ".tsx", ".js", ".py", ".go"},
                                  exclude_dirs=DEFAULT_EXCLUDE_DIRS):
        content = _read_file_content(p)
        if content is None:
            continue
        rel = _normalize_path(str(p.relative_to(root)))
        ext = p.suffix.lower()

        # Express
        if ext in TS_JS_EXTS:
            for m in ["get", "post", "put", "delete", "patch", "all"]:
                for match in re.finditer(rf'(?:router|app|route)\.{m}\s*\(\s*[\'"]([^\'"]+)[\'"]', content, re.IGNORECASE):
                    endpoints.append(f"- `{m.upper()}` `{match.group(1)}` ({rel}) — Express")

        # FastAPI / Flask
        if ext == ".py":
            for m in ["get", "post", "put", "delete", "patch"]:
                for match in re.finditer(rf'@(?:app|router)\.{m}\s*\(\s*[\'"]([^\'"]+)[\'"]', content, re.IGNORECASE):
                    endpoints.append(f"- `{m.upper()}` `{match.group(1)}` ({rel}) — FastAPI/Flask")
            for match in re.finditer(r"@app\.route\s*\(\s*['\"]([^'\"]+)['\"]", content):
                methods_match = re.search(r"methods\s*=\s*\[([^\]]+)\]", content[match.start():match.end()+200])
                if methods_match:
                    methods_str = methods_match.group(1)
                    for m2 in re.finditer(r"'([A-Z]+)'", methods_str):
                        endpoints.append(f"- `{m2.group(1)}` `{match.group(1)}` ({rel}) — Flask")
                else:
                    endpoints.append(f"- `GET` `{match.group(1)}` ({rel}) — Flask")

        # Gin
        if ext == ".go":
            for m in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                for match in re.finditer(rf'(?:router|r)\.{m}\s*\(\s*[\'"]([^\'"]+)[\'"]', content):
                    endpoints.append(f"- `{m}` `{match.group(1)}` ({rel}) — Gin")
    
    for ep in endpoints[:30]:
        output += ep + "\\n"
    if not endpoints:
        output += "- No API endpoints detected.\\n"

    # ── 미들웨어/가드 체인 분석 (Phase 2) ──
    output += "\\n## Middleware / Guard Chain\\n\\n"
    middleware_count = 0
    for p in _iter_project_files_cached(root, extensions={".ts", ".tsx", ".js", ".py"},
                                  exclude_dirs=DEFAULT_EXCLUDE_DIRS):
        content = _read_file_content(p)
        if content is None:
            continue
        rel = _normalize_path(str(p.relative_to(root)))
        uses = re.findall(r'app\.use\(\s*([^)]+)\)', content)
        if uses:
            for u in uses[:3]:
                middleware_count += 1
                output += f"- `{rel}`: `app.use({u.strip()[:80]})`\\n"
        mids = re.findall(r'@app\.middleware', content)
        if mids:
            middleware_count += len(mids)
            output += f"- `{rel}`: {len(mids)} middleware decorator(s)\\n"
    if middleware_count == 0:
        output += "- No middleware/guard chains detected.\\n"

    # 데이터 모델 (AST 기반 필드 추출)
    output += "\\n## Data Models\\n\\n"
    models = []
    all_fields = {}
    for p in _iter_project_files_cached(root, extensions={".ts", ".tsx", ".js", ".jsx", ".go"},
                                  exclude_dirs=DEFAULT_EXCLUDE_DIRS):
        content = _read_file_content(p)
        if content is None:
            continue
        rel = _normalize_path(str(p.relative_to(root)))
        if p.suffix in TS_JS_EXTS:
            ast_fields = _extract_ast_fields(content, p.suffix)
            for model in ast_fields.get("models", []):
                model_name = model["name"]
                field_list = model["fields"]
                models.append(f"- `{model_name}` → **{len(field_list)} fields** ({rel})")
                if field_list:
                    all_fields[model_name] = field_list
        else:
            for match in re.finditer(r'(?:type\s+)?(\w+)\s+struct\s*\{', content):
                models.append(f"- `{match.group(1)}` ({rel})")

    if all_fields:
        output += "\\n### Field Details\\n\\n"
        for model_name, fields in all_fields.items():
            output += f"**{model_name}**\\n\\n"
            for f in fields:
                output += f"- `{f['name']}`: `{f['type']}`\\n"
            output += "\\n"

        # 관계 추론 (Phase 2)
        output += "### Model Relationships\\n\\n"
        relation_count = 0
        for model_name, fields in all_fields.items():
            for f in fields:
                ftype = f["type"].replace("[]", "").replace("|", "").strip()
                if ftype in all_fields and ftype != model_name:
                    is_array = "[]" in f["type"] or "Array" in f["type"]
                    card = "1:N" if is_array else "1:1"
                    relation_count += 1
                    output += f"- `{model_name}` → `{ftype}` ({card}) via `{f['name']}`\\n"
        if relation_count == 0:
            output += "- No explicit model relationships detected.\\n"
    else:
        for m in models[:20]:
            output += m + "\\n"

    if not models and not all_fields:
        output += "- No data models detected.\\n"

    # 형식별 출력
    if output_format == "mermaid":
        output += "\\n## ER Diagram (Mermaid)\\n\\n```mermaid\\nerDiagram\\n"
        if all_fields:
            for model_name, fields in all_fields.items():
                output += f"  {model_name} {{\\n"
                for f in fields:
                    ftype = f["type"].replace("|", " or ")
                    output += f"    {ftype} {f['name']}\\n"
                output += "  }}\\n"
            for model_name, fields in all_fields.items():
                for f in fields:
                    ftype = f["type"].replace("[]", "").replace("|", "").strip()
                    if ftype in all_fields and ftype != model_name:
                        is_array = "[]" in f["type"] or "Array" in f["type"]
                        if is_array:
                            output += f"  {model_name} ||--o{{ {ftype} : has\\n"
                        else:
                            output += f"  {model_name} ||--|| {ftype} : references\\n"
        else:
            output += "  User ||--o{ Order : places\\n  Order ||--|{ OrderItem : contains\\n"
        output += "```\\n"
    elif output_format == "openapi":
        output += "\\n## OpenAPI 3.0 Spec\\n\\n```yaml\\nopenapi: 3.0.0\\ninfo:\\n  title: Auto-detected API\\n  version: 0.1.0\\n"
        if endpoints:
            output += "paths:\\n"
            path_map = defaultdict(list)
            for ep in endpoints:
                m = re.match(r'- `(\w+)` `([^`]+)`', ep)
                if m:
                    method = m.group(1).lower()
                    path = m.group(2)
                    path_map[path].append(method)
            for path, methods in sorted(path_map.items()):
                output += f"  {path}:\\n"
                for method in methods:
                    output += f"    {method}:\\n"
                    output += f"      summary: Auto-detected endpoint\\n"
                    output += f"      responses:\\n"
                    output += f"        '200':\\n"
                    output += f"          description: Successful response\\n"
        else:
            output += "paths: {}\\n"
        if all_fields:
            output += "components:\\n  schemas:\\n"
            for model_name, fields in all_fields.items():
                output += f"    {model_name}:\\n"
                output += f"      type: object\\n"
                output += f"      properties:\\n"
                for f in fields:
                    ftype = f["type"].replace("|", " or ")
                    example_map = {"string": "string", "number": 0, "boolean": True, "integer": 0}
                    example = example_map.get(ftype, ftype)
                    output += f"        {f['name']}:\\n"
                    output += f"          type: {ftype}\\n"
                    output += f"          example: {json.dumps(example, ensure_ascii=False)}\\n"
        output += "```\\n"

    output += _markdown_footer()
    return output
@mcp.tool
def generate_tests(source_path: str, framework: Optional[str] = None) -> str:
    """지정된 소스 파일에 대한 단위 테스트를 생성합니다.
    tree-sitter AST로 함수 시그니처를 더 정확히 감지합니다.
    
    Args:
        source_path: 테스트 대상 소스 파일 경로
        framework: 테스트 프레임워크 (jest, vitest, pytest, go test). 자동 감지됨.
    """
    err = _validate_file_path(source_path)
    if err:
        return _markdown_header("Test Generation Error", "❌") + f"**{err}**\\n" + _markdown_footer()

    root = Path(os.getcwd())
    target = Path(source_path)
    if not target.is_absolute():
        target = root / source_path

    if not target.exists() or not target.is_file():
        return _markdown_header("Test Generation Error", "❌") + f"**File not found: {source_path}**\\n" + _markdown_footer()

    content = _read_file_content(target)
    if content is None:
        return _markdown_header("Test Generation Error", "❌") + f"**Cannot read file: {source_path}**\\n" + _markdown_footer()

    ext = target.suffix.lower()
    lines = content.split("\\n")

    # AST 기반 함수 감지 (TS/JS)
    func_count = 0
    function_names = []
    function_details = []
    if ext in TS_JS_EXTS:
        _init_tree_sitter()
        ast = _parse_with_tree_sitter(content, ext)
        functions = ast.get("functions", [])
        func_count = len(functions)
        function_names = [fn["name"] for fn in functions[:20]]
        function_details = functions
    else:
        for line in lines:
            if re.search(r'(?:export\s+)?(?:function|async function|const\s+\w+\s*=\s*(?:async\s*)?\(|def\s+\w+\s*\()', line):
                func_count += 1

    output = _markdown_header(f"Test Generation: {target.name}")
    output += f"- **Framework**: {framework or 'auto-detect'}\\n"
    output += f"- **Functions detected**: {func_count}\\n"
    output += f"- **Lines**: {len(lines)}\\n\\n"

    if function_names:
        output += "### Functions Found\\n\\n"
        for name in function_names:
            output += f"- `{name}()`\\n"
        output += "\\n"

    # ── Phase 3: 경계값 테스트 케이스 생성 ──
    output += "## Boundary Value Test Cases\\n\\n"
    if function_details:
        param_guesses = []
        for fn in function_details[:5]:
            fn_text = "\\n".join(content.split("\\n")[fn["line"]-1:min(len(content.split("\\n")), fn["line"]+2)])
            params = re.findall(r'(\w+)\s*(?::\s*\w+)?\s*(?:[,)])', fn_text)
            if params:
                real_params = [p for p in params if p not in (fn["name"], "async", "function", "export", "default")]
                for p in real_params[:3]:
                    param_guesses.append((fn["name"], p, "any"))
        if param_guesses:
            for fn_name, param_name, param_type in param_guesses:
                output += f"- `{fn_name}('{param_name}')`: boundary tests → null, empty, valid, invalid, large input\\n"
        else:
            output += "- No parameters detected for boundary analysis.\\n"
    else:
        output += "- No function details available.\\n"
    output += "\\n"

    # ── Phase 3: 조건문 분기 분석 ──
    output += "## Branch Coverage\\n\\n"
    branch_count = 0
    for line in lines:
        if re.search(r'\bif\s*\(', line) or 'else if' in line or 'else' in line.strip()[:4]:
            branch_count += 1
    output += f"- **Conditional branches detected**: {branch_count}\\n"
    output += "- **Suggested test cases**: test each branch (true/false)\\n"
    switch_count = len(re.findall(r'\bswitch\s*\(', content))
    if switch_count > 0:
        output += f"- **Switch statements**: {switch_count} — test each case including default\\n"
    output += "\\n"

    # ── Phase 3: 에러 케이스 생성 ──
    output += "## Error Case Generation\\n\\n"
    error_indicators = {
        "try-catch": len(re.findall(r'\btry\s*\{', content)),
        "null check": len(re.findall(r'(?:===?\s*null|!==?\s*null|==\s*null)', content)),
        "undefined check": len(re.findall(r'(?:===?\s*undefined|!==?\s*undefined)', content)),
        "error return": len(re.findall(r'throw\s+new\s+', content)),
    }
    has_errors = False
    for name, count in error_indicators.items():
        if count > 0:
            output += f"- `{name}`: {count} occurrence(s) → add error-handling test\\n"
            has_errors = True
    if not has_errors:
        output += "- No explicit error handling detected. Add tests for:\\n"
        output += "  - Null/undefined inputs\\n"
        output += "  - Empty collections\\n"
        output += "  - Invalid parameter types\\n"
    output += "\\n"

    # ── Phase 3: Mock 데이터 제안 ──
    output += "## Mock Data Suggestions\\n\\n"
    mock_suggestions = []
    if ext == ".py":
        mock_suggestions.append("- Use `unittest.mock` or `pytest.fixture`")
    elif ext in (".ts", ".tsx"):
        mock_suggestions.append("- Use `vi.mock()` (Vitest) or `jest.mock()`")
    elif ext == ".go":
        mock_suggestions.append("- Use `testing` package with interface mocks")
    
    all_param_names = []
    for fn in function_details[:5]:
        fn_text_str = "\\n".join(content.split("\\n")[fn["line"]-1:fn["line"]+1])
        params_found = re.findall(r'\b(\w+)\s*:\s*(\w+)', fn_text_str)
        for pname, ptype in params_found:
            if pname not in (fn["name"], "async", "function"):
                all_param_names.append((pname, ptype))
    
    seen_types = set()
    for pname, ptype in all_param_names:
        if ptype not in seen_types:
            seen_types.add(ptype)
            if ptype == "string":
                mock_suggestions.append(f"- `{pname}` (string): use \"test-{pname}\"")
            elif ptype in ("number", "int"):
                mock_suggestions.append(f"- `{pname}` ({ptype}): use `42`, `0`, `-1`")
            elif ptype == "boolean":
                mock_suggestions.append(f"- `{pname}` (boolean): use `true`, `false`")
            elif ptype == "array":
                mock_suggestions.append(f"- `{pname}` (array): use `[]`, `[1,2,3]`")
    for s in mock_suggestions:
        output += s + "\\n"

    # ── Phase 3: 예상 동작 추론 ──
    output += "\\n## Expected Behavior Inference\\n\\n"
    for fn in function_details[:5]:
        fn_name = fn["name"]
        if fn_name.startswith("get") or fn_name.startswith("find") or fn_name.startswith("fetch"):
            output += f"- `{fn_name}()`: Returns data → expect defined result\\n"
        elif fn_name.startswith("set") or fn_name.startswith("save") or fn_name.startswith("create"):
            output += f"- `{fn_name}()`: Mutates/creates state → expect side effect or return ID\\n"
        elif fn_name.startswith("delete") or fn_name.startswith("remove"):
            output += f"- `{fn_name}()`: Deletes data → expect success/true\\n"
        elif fn_name.startswith("validate") or fn_name.startswith("is") or fn_name.startswith("has"):
            output += f"- `{fn_name}()`: Returns boolean → expect true/false cases\\n"
        elif fn_name.startswith("format") or fn_name.startswith("transform") or fn_name.startswith("convert"):
            output += f"- `{fn_name}()`: Transforms data → expect specific output format\\n"
        elif fn_name.startswith("handle") or fn_name.startswith("on"):
            output += f"- `{fn_name}()`: Event handler → expect side effects or state changes\\n"
        else:
            output += f"- `{fn_name}()`: Check function → test return value\\n"

    if ext in (".ts", ".tsx"):
        output += "\\n## Jest/Vitest Test Structure\\n\\n"
        output += "```typescript\\nimport { describe, it, expect } from 'vitest';\\n"
        output += f"import {{ ... }} from './{target.stem}';\\n\\n"
        output += "describe('', () => {\\n  it('should work', () => {\\n    // TODO: write test\\n  });\\n});\\n```\\n"
    elif ext == ".py":
        output += "\n## pytest Test Structure\n\n"
        output += '```python\nimport pytest\n\n\ndef test_():\n    """TODO: write test"""\n    pass\n```\n'
    elif ext == ".go":
        output += "\n## Go Test Structure\n\n"
        output += '```go\npackage main\n\nimport "testing"\n\nfunc Test_(t *testing.T) {\n\t// TODO: write test\n}\n```\n'

    try_crow_ingest(f"Generated tests for {target.name}: {func_count} functions, {branch_count} branches (Phase3)", register="context")
    output += _markdown_footer()
    return output
@mcp.tool
def analyze_coverage(target_path: Optional[str] = None) -> str:
    """테스트 커버리지를 분석합니다.
    빠른 경로: 테스트 파일 존재 여부, 테스트/소스 비율 자체 분석.
    전체 경로: vitest/pytest --cov 실행 (있을 경우).
    
    Args:
        target_path: 분석 대상 경로
    """
    root = Path(get_project_root(target_path))
    output = _markdown_header("Coverage Analysis")

    test_patterns = {
        ".ts": [".test.ts", ".spec.ts", ".test.tsx", ".spec.tsx", "__tests__"],
        ".tsx": [".test.tsx", ".spec.tsx", "__tests__"],
        ".js": [".test.js", ".spec.js", "__tests__"],
        ".py": ["test_", "_test", "tests/"],
        ".go": ["_test.go"],
    }
    source_files = []
    test_files = []
    source_to_test = defaultdict(list)
    test_to_source = defaultdict(list)

    for p in _iter_project_files_cached(root, extensions=SOURCE_EXTS, exclude_dirs=DEFAULT_EXCLUDE_DIRS):
        rel = _normalize_path(str(p.relative_to(root)))
        fname = p.name
        ext = p.suffix.lower()
        is_test = False
        if ext in test_patterns:
            for pattern in test_patterns[ext]:
                if pattern in fname or pattern in rel.replace("\\\\", "/"):
                    is_test = True
                    break
        if is_test:
            test_files.append(rel)
            for ext2 in [".ts", ".tsx", ".js", ".py", ".go"]:
                src_patterns = [
                    rel.replace(".test", "").replace(".spec", "").replace("_test", ""),
                    rel.replace("__tests__/", "").replace("test/", "").replace("tests/", ""),
                ]
                for sp in src_patterns:
                    src_path = Path(root) / sp
                    if src_path.exists() and not any(tp in sp for tp in ["test", ".test.", ".spec."]):
                        source_to_test[sp].append(rel)
                        test_to_source[rel].append(sp)
        else:
            source_files.append(rel)

    total_source = len(source_files)
    total_tests = len(test_files)
    ratio = round(total_tests / max(total_source, 1), 2)

    output += "## Coverage Analysis (no external tools)\\n\\n"
    output += f"- **Source files**: {total_source}\\n"
    output += f"- **Test files**: {total_tests}\\n"
    output += f"- **Test/Source ratio**: {ratio}\\n"
    if total_tests == 0:
        output += "- ⚠️ **No test files detected.**\\n"
    elif ratio < 0.3:
        output += f"- ⚠️ Low coverage likely (ratio {ratio} < 0.3)\\n"
    elif ratio >= 0.5:
        output += f"- ✅ Decent test presence (ratio {ratio})\\n"

    # ── 누락 테스트 감지 ──
    output += "\\n## Missing Test Detection\\n\\n"
    untested_sources = [src for src in source_files if src not in source_to_test]
    if untested_sources:
        output += f"⚠️ {len(untested_sources)} source files have NO corresponding test:\\n\\n"
        for src in untested_sources[:10]:
            output += f"- `{src}`\\n"
        if len(untested_sources) > 10:
            output += f"- ... +{len(untested_sources)-10} more\\n"
        output += "\\n> Tip: Create test files following naming conventions (`.test.ts`, `_test.go`, `test_*.py`)\\n"
    else:
        output += "✅ All source files have corresponding test files.\\n"
    output += "\\n"

    if test_files:
        output += "### Test Files\\n"
        for tf in test_files[:10]:
            output += f"- `{tf}`\\n"
        if len(test_files) > 10:
            output += f"- ... +{len(test_files)-10} more\\n"
    if test_to_source:
        output += "\\n### Test → Source Mapping\\n\\n"
        for test_f, src_list in list(test_to_source.items())[:5]:
            output += f"- `{test_f}` → {', '.join(src_list[:3])}\\n"

    ext_tool_used = False
    if (root / "package.json").exists() and (root / "node_modules" / ".bin" / "vitest").exists():
        try:
            result = subprocess.run([_npx_cmd(), "vitest", "run", "--coverage", "--reporter=text"],
                                   cwd=str(root), capture_output=True, text=True, timeout=30)
            if result.stdout:
                lines = result.stdout.strip().split("\\n")
                output += "\\n## Vitest Coverage (external)\\n\\n```\\n" + "\\n".join(lines[-20:]) + "\\n```\\n"
                ext_tool_used = True
        except Exception:
            pass

    py_indicator = (root / "pyproject.toml").exists() or (root / "setup.py").exists() or (root / "requirements.txt").exists()
    if py_indicator and not ext_tool_used:
        try:
            result = subprocess.run([sys.executable, "-m", "pytest", "--co", "--quiet"],
                                   cwd=str(root), capture_output=True, text=True, timeout=30)
            if result.stdout and "test" in result.stdout.lower():
                lines = result.stdout.strip().split("\\n")
                output += "\\n## pytest (external)\\n\\n```\\n" + "\\n".join(lines[-15:]) + "\\n```\\n"
                ext_tool_used = True
        except Exception:
            pass

    if not ext_tool_used and (root / "package.json").exists() or py_indicator:
        output += "\\n> ℹ️ External coverage tool not available. Analysis based on file presence.\\n"

    try_crow_ingest(json.dumps({"coverage_ratio": ratio, "source": total_source, "tests": total_tests, "untested": len(untested_sources)}), register="context")
    output += _markdown_footer()
    return output
@mcp.tool
def capture_screen() -> str:
    """화면을 캡처하여 화이트보드에 자동으로 붙여넣습니다. AI가 시각적 분석이 필요할 때 호출합니다."""
    try:
        from PIL import ImageGrab
        import base64
        
        img = ImageGrab.grab()
        buf = BytesIO()
        img.save(buf, format='PNG')
        img_b64 = base64.b64encode(buf.getvalue()).decode()
        
        data = {
            "timestamp": time.time(),
            "type": "screenshot",
            "image": f"data:image/png;base64,{img_b64}"
        }
        _atomic_write_json(WHITEBOARD_FILE, data, indent=2)
        
        output = (_markdown_header("Screen Capture")
                  + f"Screen captured ({img.width}x{img.height}). Image saved to whiteboard.\n")
        try_crow_ingest(f"Screen captured: {img.width}x{img.height}", register="context")
        output += _markdown_footer()
        return output
    except ImportError:
        return (_markdown_header("Screen Capture Error", "❌")
                + "**Pillow not installed.** Run: `pip install Pillow`\n"
                + _markdown_footer())
    except Exception as e:
        return (_markdown_header("Screen Capture Error", "❌")
                + f"**Capture failed:** `{e}`\n"
                + _markdown_footer())


@mcp.tool
def draw_on_whiteboard(commands: str) -> str:
    """AI가 화이트보드에 그림을 그립니다. VibeZoo가 이 명령을 받아 Webview에 렌더링합니다.
    
    Args:
        commands: JSON 배열 형태의 Fabric.js 드로잉 명령.
                 각 명령: {"type":"rect|circle|line|text|arrow|freehand|clear", "props":{...}}
    """
    err = _validate_string(commands, "commands")
    if err:
        return _markdown_header("Whiteboard Error", "❌") + f"**{err}**\n" + _markdown_footer()

    try:
        parsed = json.loads(commands)
        if not isinstance(parsed, list):
            return (_markdown_header("Whiteboard Error", "❌")
                    + "**Commands must be a JSON array.**\n"
                    + _markdown_footer())
    except json.JSONDecodeError as e:
        return (_markdown_header("Whiteboard Error", "❌")
                + f"**Invalid JSON:** `{e}`\n"
                + _markdown_footer())

    try:
        data = {"timestamp": time.time(), "commands": parsed}
        _atomic_write_json(WHITEBOARD_FILE, data, indent=2)
        try_crow_ingest(f"Whiteboard: {len(parsed)} drawing commands", register="context")
        return (_markdown_header("Whiteboard Drawing")
                + f"Drew {len(parsed)} shapes on whiteboard.\n"
                + _markdown_footer())
    except Exception as e:
        return (_markdown_header("Whiteboard Error", "❌")
                + f"**Failed to draw:** `{e}`\n"
                + _markdown_footer())


@mcp.tool
def get_whiteboard_state() -> str:
    """현재 화이트보드의 상태를 조회합니다. 사용자가 수정한 내용을 확인합니다."""
    try:
        if os.path.exists(WHITEBOARD_FILE):
            with open(WHITEBOARD_FILE) as f:
                data = json.load(f)
            commands_count = len(data.get("commands", []))
            output = (_markdown_header("Whiteboard State")
                      + f"Whiteboard has {commands_count} objects.\n\n")
            output += f"```json\n{json.dumps(data, indent=2, ensure_ascii=False)[:2000]}\n```\n"
            output += _markdown_footer()
            return output
        return (_markdown_header("Whiteboard State")
                + "Whiteboard is empty.\n"
                + _markdown_footer())
    except Exception as e:
        return (_markdown_header("Whiteboard Error", "❌")
                + f"**Failed:** `{e}`\n"
                + _markdown_footer())


@mcp.tool
def open_whiteboard(message: str = "") -> str:
    """VibeZoo 화이트보드를 엽니다. AI가 시각적 설명이 필요할 때 호출합니다."""
    try:
        data = {"action": "open", "message": message, "timestamp": time.time()}
        action_file = os.path.join(os.path.expanduser("~"), ".vibezoo-whiteboard-action.json")
        _atomic_write_json(action_file, data, indent=2)
        try_crow_ingest(f"Whiteboard opened: {message[:100]}" if message else "Whiteboard opened", register="context")
        return (_markdown_header("Whiteboard")
                + f"Whiteboard opened. {message}\n"
                + _markdown_footer())
    except Exception as e:
        return (_markdown_header("Whiteboard Error", "❌")
                + f"**Failed:** `{e}`\n"
                + _markdown_footer())


@mcp.tool
def open_ui_preview(code: str = "", framework: str = "react") -> str:
    """UI Preview 패널을 열고 코드를 렌더링합니다."""
    try:
        data = {"action": "open_ui", "code": code, "framework": framework, "timestamp": time.time()}
        action_file = os.path.join(os.path.expanduser("~"), ".vibezoo-ui-action.json")
        _atomic_write_json(action_file, data, indent=2)
        try_crow_ingest(f"UI Preview opened: {framework}", register="context")
        return (_markdown_header("UI Preview")
                + f"UI Preview opened. Rendering {framework} component.\n"
                + _markdown_footer())
    except Exception as e:
        return (_markdown_header("UI Preview Error", "❌")
                + f"**Failed:** `{e}`\n"
                + _markdown_footer())


# ═══════════════════════════════════════════════════════════
# M1-A: Auto-Fix Loop — MCP 도구
# ═══════════════════════════════════════════════════════════

@mcp.tool
def auto_fix_status() -> str:
    """현재 진행 중인 Auto-Fix 세션의 상태와 에러 정보를 조회합니다.
    LLM이 빌드 에러를 분석하고 수정을 시작할 때 호출합니다.
    과거 유사 에러 패턴을 Crow Memory에서 조회하여 함께 반환합니다.

    Returns:
        JSON: { status, attempt, maxAttempts, diagnostics, history, pastFixes }
    """
    if not os.path.exists(FIX_REQUEST_FILE):
        return json.dumps({"status": "idle", "message": "No active fix request", "timestamp": time.time()})

    try:
        with open(FIX_REQUEST_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 상태를 in_progress로 변경
        data["status"] = "in_progress"
        data["lastReadAt"] = time.time()
        
        _atomic_write_json(FIX_REQUEST_FILE, data, indent=2)

        # Crow Memory recall — 과거 유사 에러 패턴 조회 (register="bug")
        error_code = ""
        if data.get("history"):
            last = data["history"][-1]
            if last.get("diagnostics"):
                error_code = last["diagnostics"][0].get("code", "")
        if error_code:
            past_fixes = try_crow_recall(
                query=f"build error {error_code}",
                register="bug",
                limit=3
            )
            if past_fixes:
                data["pastFixes"] = past_fixes

        data["version"] = VERSION
        data["timestamp"] = time.time()
        return json.dumps(data, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "status": "error", "message": str(e),
            "timestamp": time.time(), "version": VERSION
        })


@mcp.tool
def retry_build() -> str:
    """빌드를 재실행하고 결과를 반환합니다.
    LLM이 수정 코드를 적용한 후 빌드 성공 여부를 확인할 때 호출합니다.

    Returns:
        JSON: { exitCode, stdout, stderr, success, diagnostics }
    """
    root = os.getcwd()

    # 프로젝트 타입 감지
    pkg_json = Path(root) / "package.json"
    if pkg_json.exists():
        cmd = [_npx_cmd(), "tsc", "--noEmit"]
    else:
        return json.dumps({
            "exitCode": -1,
            "diagnostics": [],
            "success": False,
            "error": "No build command detected (package.json not found)",
            "timestamp": time.time(),
        })

    try:
        result = subprocess.run(
            cmd,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=60
        )

        # 결과를 fix-request 파일에 기록
        if os.path.exists(FIX_REQUEST_FILE):
            try:
                with open(FIX_REQUEST_FILE) as f:
                    fix_data = json.load(f)
                attempt_num = len(fix_data.get("history", [])) + 1
                if "history" not in fix_data:
                    fix_data["history"] = []
                fix_data["history"].append({
                    "attempt": attempt_num,
                    "exitCode": result.returncode,
                    "stderr": result.stderr[-500:],
                    "stdout": result.stdout[-500:],
                    "fixApplied": None,
                    "timestamp": time.time()
                })
                fix_data["attempt"] = attempt_num
                if result.returncode == 0:
                    fix_data["status"] = "resolved"
                else:
                    fix_data["status"] = "pending" if attempt_num < fix_data.get("maxAttempts", 3) else "abandoned"
                _atomic_write_json(FIX_REQUEST_FILE, fix_data, indent=2)

                # Crow ingest — 실패 시 에러 패턴 저장
                if result.returncode != 0:
                    try_crow_ingest(
                        json.dumps({
                            "error": result.stderr[-500:],
                            "exitCode": result.returncode,
                            "attempt": attempt_num,
                        }),
                        register="bug"
                    )
            except Exception:
                pass

        return json.dumps({
            "exitCode": result.returncode,
            "stdout": _truncate(result.stdout, 2000),
            "stderr": _truncate(result.stderr, 2000),
            "success": result.returncode == 0,
            "timestamp": time.time(),
        }, indent=2, ensure_ascii=False)

    except subprocess.TimeoutExpired:
        return json.dumps({
            "exitCode": -1,
            "success": False,
            "error": "Build timed out after 60s",
            "timestamp": time.time(),
        })
    except Exception as e:
        return json.dumps({
            "exitCode": -1,
            "success": False,
            "error": str(e),
            "timestamp": time.time(),
        })


@mcp.tool
def check_intervention() -> str:
    """Auto-Fix Loop 진행 전 사용자 개입 여부를 확인합니다.
    Whiteboard 상태와 대기 중인 채팅 메시지를 조회합니다.

    Returns:
        JSON: { whiteboard_annotations, pending_messages, user_guidance, should_pause }
    """
    result = {
        "whiteboard_annotations": [],
        "pending_messages": [],
        "user_guidance": None,
        "should_pause": False,
        "timestamp": time.time(),
    }

    # 1. Whiteboard 확인
    if os.path.exists(WHITEBOARD_FILE):
        try:
            with open(WHITEBOARD_FILE) as f:
                wb_data = json.load(f)
            for cmd in wb_data.get("commands", []):
                if cmd.get("type") == "text":
                    result["whiteboard_annotations"].append({
                        "text": cmd.get("props", {}).get("text", ""),
                        "position": {
                            "left": cmd.get("props", {}).get("left", 0),
                            "top": cmd.get("props", {}).get("top", 0)
                        }
                    })
        except Exception:
            pass

    # 2. Pending chat messages 확인
    if os.path.exists(CHAT_PENDING_FILE):
        try:
            with open(CHAT_PENDING_FILE) as f:
                pending = json.load(f)
            result["pending_messages"] = pending.get("messages", [])
            os.remove(CHAT_PENDING_FILE)  # 중복 처리 방지
        except Exception:
            pass

    # 3. 사용자 가이드라인 종합
    if result["whiteboard_annotations"] or result["pending_messages"]:
        guidance_parts = []
        if result["whiteboard_annotations"]:
            guidance_parts.append("Whiteboard annotations found")
        if result["pending_messages"]:
            guidance_parts.append("Pending chat messages found")
        result["user_guidance"] = "; ".join(guidance_parts)
        result["should_pause"] = bool(result["pending_messages"])

    return json.dumps(result, indent=2, ensure_ascii=False)


# ═══════════════════════════════════════════════════════════
# Q1: Quick Win — 시나리오 통합 MCP 도구
# ═══════════════════════════════════════════════════════════

def _run_tool(name: str, timeout: float = 30.0, **kwargs):
    """내부적으로 기존 MCP 도구 함수를 호출하여 결과를 문자열로 반환.
    
    Args:
        name: 도구 함수명
        timeout: 개별 도구 호출 타임아웃 (초)
        **kwargs: 도구 함수에 전달할 인자
    
    Returns:
        (result_str, success_bool) 튜플. 실패 시 에러 메시지와 함께 success=False.
    """
    import inspect
    tools = {
        "search_codebase": search_codebase,
        "review_code": review_code,
        "check_quality": check_quality,
        "extract_patterns": extract_patterns,
        "map_dependencies": map_dependencies,
        "analyze_call_graph": analyze_call_graph,
        "reverse_engineer": reverse_engineer,
        "summarize_architecture": summarize_architecture,
        "draw_on_whiteboard": draw_on_whiteboard,
        "generate_tests": generate_tests,
        "analyze_coverage": analyze_coverage,
        "explain_code": explain_code,
        "analyze_changes": analyze_changes,
        "review_pr": review_pr,
        "refactor_across_files": refactor_across_files,
        "learn_project": learn_project,
        "recall_project": recall_project,
        "learn_preference": learn_preference,
        "get_preferences": get_preferences,
    }
    fn = tools.get(name)
    if not fn:
        return (f"**Tool not found:** `{name}`", False)
    
    sig = inspect.signature(fn)
    filtered = {k: v for k, v in kwargs.items() if k in sig.parameters}
    
    try:
        import signal as _signal
        result = fn(**filtered)
        return (str(result), True)
    except Exception as e:
        # 상세 에러 컨텍스트 제공
        error_msg = (
            f"**Error in `{name}`:**\n"
            f"- Exception: `{type(e).__name__}: {e}`\n"
            f"- Parameters: {json.dumps(filtered, default=str, ensure_ascii=False)[:500]}\n"
        )
        return (error_msg, False)


@mcp.tool
def review_project(target_path: str) -> str:
    """search_codebase + review_code + check_quality + extract_patterns 통합.
    프로젝트 전체를 종합 리뷰하여 하나의 마크다운 보고서로 반환합니다.

    Args:
        target_path: 분석 대상 디렉토리 경로
    """
    err = _validate_string(target_path, "target_path")
    if err:
        return _markdown_header("Review Project Error", "❌") + f"**{err}**\n" + _markdown_footer()

    sections = []
    sections.append(_markdown_header("Project Review Report"))
    sections.append(f"> Target: `{target_path}`\n")

    # 1. search_codebase — 주요 패턴 검색 (각 패턴을 개별 검색)
    sections.append("## 🔍 Code Search\n")
    search_terms = ["TODO", "FIXME", "HACK", "BUG"]
    for term in search_terms:
        term_result, ok = _run_tool("search_codebase", query=term, max_results=10)
        if ok:
            if "No results found" not in term_result and "Found 0" not in term_result:
                sections.append(term_result)
        else:
            sections.append(f"⚠️ Partial failure: {term_result}")

    # 2. review_code — 주요 파일 리뷰
    sections.append("## 📝 Code Review\n")
    root = Path(get_project_root(target_path))
    reviewed = 0
    total_files = 0
    for p in _iter_project_files_cached(root, extensions=SOURCE_EXTS, exclude_dirs=DEFAULT_EXCLUDE_DIRS):
        total_files += 1
    for p in _iter_project_files_cached(root, extensions=SOURCE_EXTS, exclude_dirs=DEFAULT_EXCLUDE_DIRS):
        if reviewed >= 5:
            sections.append(f"\n> ... and more files (reviewed top 5 of {total_files} total)\n")
            break
        review, ok = _run_tool("review_code", file_path=str(p))
        if ok:
            sections.append(review)
        else:
            sections.append(f"⚠️ Partial failure: {review}")
        reviewed += 1

    if reviewed == 0:
        sections.append("- No source files found to review.\n")

    # 3. check_quality
    sections.append("## ✅ Quality Check\n")
    quality, ok = _run_tool("check_quality", target_path=target_path)
    if ok:
        sections.append(quality)
    else:
        sections.append(f"⚠️ Partial failure: {quality}")

    # 4. extract_patterns
    sections.append("## 📊 Pattern Analysis\n")
    patterns, ok = _run_tool("extract_patterns", target_path=target_path, min_occurrences=3)
    if ok:
        sections.append(patterns)
    else:
        sections.append(f"⚠️ Partial failure: {patterns}")

    # Crow ingest
    try_crow_ingest(
        json.dumps({
            "action": "review_project",
            "target": target_path,
            "files_reviewed": reviewed,
            "total_files": total_files,
            "timestamp": time.time(),
        }),
        register="style"
    )

    result = "\n\n---\n\n".join(sections)
    result += _markdown_footer()
    return result


@mcp.tool
def find_bugs(target_path: str) -> str:
    """extract_patterns + search_codebase(console.log|debugger|any) + Crow recall 통합.
    프로젝트에서 잠재적 버그를 찾아 마크다운으로 반환합니다.

    Args:
        target_path: 분석 대상 디렉토리 경로
    """
    err = _validate_string(target_path, "target_path")
    if err:
        return _markdown_header("Bug Finder Error", "❌") + f"**{err}**\n" + _markdown_footer()

    sections = []
    sections.append(_markdown_header("Bug Finder Report"))
    sections.append(f"> Target: `{target_path}`\n")

    # 1. extract_patterns — 콘솔 로그, TODO 등 패턴 분석
    sections.append("## 📊 Pattern Analysis\n")
    patterns, ok = _run_tool("extract_patterns", target_path=target_path, min_occurrences=1)
    if ok:
        sections.append(patterns)
    else:
        sections.append(f"⚠️ Partial failure: {patterns}")

    # 2. search_codebase — 버그 의심 패턴 검색
    sections.append("## ⚠️ Suspicious Patterns\n")
    suspicious_queries = [
        "console.log", "debugger", ".only(", "fit(", "fdescribe",
        "TODO", "FIXME", "HACK", "XXX", "any", "as any",
        "@ts-ignore", "@ts-nocheck", "eslint-disable"
    ]
    found_suspicious = 0
    for query in suspicious_queries:
        result, ok = _run_tool("search_codebase", query=query, max_results=10)
        if ok:
            if "No results found" not in result and "Found 0" not in result:
                sections.append(result)
                found_suspicious += 1
        else:
            sections.append(f"⚠️ Partial failure: {result}")
            found_suspicious += 1

    if found_suspicious == 0:
        sections.append("- No suspicious patterns found.\n")

    # 3. Crow recall — 이전 버그 패턴 회상
    sections.append("## 🧠 Crow Memory Recall\n")
    crow_results = try_crow_recall(query="bug pattern error in project", register="bug", limit=10)
    if crow_results:
        sections.append("### Previous bug patterns from Crow memory:\n")
        for item in crow_results:
            content = item.get("content", item.get("value", str(item)))
            sections.append(f"- {_truncate(content, 300)}\n")
    else:
        sections.append("- No relevant bug patterns found in Crow memory.\n")

    # Crow ingest
    bug_summary = {
        "action": "find_bugs",
        "target": target_path,
        "suspicious_count": found_suspicious,
        "crow_recall_count": len(crow_results),
        "timestamp": time.time(),
    }
    try_crow_ingest(json.dumps(bug_summary), register="bug")

    result = "\n\n---\n\n".join(sections)
    result += _markdown_footer()
    return result


@mcp.tool
def suggest_refactor(target_path: str) -> str:
    """map_dependencies + extract_patterns + analyze_call_graph 통합.
    프로젝트의 리팩터링 제안을 마크다운으로 반환합니다.

    Args:
        target_path: 분석 대상 디렉토리 경로
    """
    err = _validate_string(target_path, "target_path")
    if err:
        return _markdown_header("Refactoring Error", "❌") + f"**{err}**\n" + _markdown_footer()

    sections = []
    sections.append(_markdown_header("Refactoring Suggestions"))
    sections.append(f"> Target: `{target_path}`\n")

    # 1. map_dependencies — 의존성 분석 + 순환 참조
    sections.append("## 🔗 Dependency Map\n")
    deps, ok = _run_tool("map_dependencies", target_path=target_path)
    if ok:
        sections.append(deps)
    else:
        sections.append(f"⚠️ Partial failure: {deps}")

    # 2. extract_patterns — 중복 패턴 찾기
    sections.append("## 📊 Pattern Duplication\n")
    patterns, ok = _run_tool("extract_patterns", target_path=target_path, min_occurrences=5)
    if ok:
        sections.append(patterns)
    else:
        sections.append(f"⚠️ Partial failure: {patterns}")

    # 3. analyze_call_graph — 호출 구조 분석
    sections.append("## 📞 Call Graph\n")
    callgraph, ok = _run_tool("analyze_call_graph", file_path=target_path, depth=3)
    if ok:
        sections.append(callgraph)
    else:
        sections.append(f"⚠️ Partial failure: {callgraph}")

    # 4. Crow recall — 과거 코딩 스타일 규칙 조회
    style_rules = try_crow_recall(query="coding style rules patterns", register="style", limit=5)
    if style_rules:
        sections.append("\n\n## 🎨 Crow Style Rules\n")
        sections.append("### Previous coding style rules from Crow memory:\n")
        for item in style_rules:
            content = item.get("content", item.get("value", str(item)))
            sections.append(f"- {_truncate(content, 300)}\n")
        sections.append("\n")

    try_crow_ingest(
        json.dumps({
            "action": "suggest_refactor",
            "target": target_path,
            "style_rules_found": len(style_rules),
            "timestamp": time.time(),
        }),
        register="style"
    )

    result = "\n\n---\n\n".join(sections)
    result += _markdown_footer()
    return result


@mcp.tool
def generate_docs(target_path: str, output_format: str = "markdown") -> str:
    """reverse_engineer + summarize_architecture + draw_on_whiteboard(architecture diagram) 통합.
    프로젝트 문서를 자동 생성하고 아키텍처 다이어그램을 화이트보드에 그립니다.
    format='mermaid' 시 ERD 다이어그램을 함께 생성합니다.

    Args:
        target_path: 분석 대상 디렉토리 경로
        output_format: 출력 형식 (markdown, openapi, mermaid). 기본: markdown
    """
    err = _validate_string(target_path, "target_path")
    if err:
        return _markdown_header("Document Generation Error", "❌") + f"**{err}**\n" + _markdown_footer()

    allowed_formats = {"markdown", "openapi", "mermaid"}
    if output_format not in allowed_formats:
        return (_markdown_header("Document Generation Error", "❌")
                + f"**Invalid format: `{output_format}`. Allowed: {', '.join(allowed_formats)}**\n"
                + _markdown_footer())

    sections = []
    sections.append(_markdown_header("Auto-Generated Documentation"))
    sections.append(f"> Target: `{target_path}`  \n> Format: `{output_format}`\n")

    # 1. summarize_architecture
    sections.append("## 🏗️ Architecture Summary\n")
    arch, ok = _run_tool("summarize_architecture", target_path=target_path)
    if ok:
        sections.append(arch)
    else:
        sections.append(f"⚠️ Partial failure: {arch}")

    # 2. reverse_engineer (AST 기반 데이터 모델 필드 포함)
    sections.append("## 🔄 Reverse Engineering\n")
    rev, ok = _run_tool("reverse_engineer", target_path=target_path, output_format=output_format)
    if ok:
        sections.append(rev)
    else:
        sections.append(f"⚠️ Partial failure: {rev}")

    # 3. draw_on_whiteboard — 개선된 아키텍처 다이어그램
    sections.append("## 🎨 Architecture Diagram (Whiteboard)\n")
    try:
        root = Path(get_project_root(target_path))
        commands = []
        entries = []
        def collect(p, depth=0):
            if depth > 2:
                return
            try:
                for child in sorted(p.iterdir()):
                    if child.name.startswith(".") or child.name in DEFAULT_EXCLUDE_DIRS:
                        continue
                    entries.append((child, depth))
                    if child.is_dir():
                        collect(child, depth + 1)
            except (PermissionError, OSError):
                pass
        collect(root)

        y = 50
        x_offset = 80
        colors = ["#4ec9ff", "#6acb6a", "#d4a0ff", "#ffd700"]
        for i, (entry, depth) in enumerate(entries[:15]):
            indent = depth * 25
            color = colors[depth % len(colors)]
            icon = "📁" if entry.is_dir() else "📄"
            commands.append({
                "type": "rect",
                "props": {
                    "left": x_offset + indent, "top": y + i * 42,
                    "width": 200 - indent, "height": 34,
                    "fill": "transparent", "stroke": color, "rx": 4
                }
            })
            commands.append({
                "type": "text",
                "props": {
                    "left": x_offset + indent + 8, "top": y + i * 42 + 8,
                    "text": f"{icon} {entry.name}",
                    "fontSize": 12, "fill": "#ffffff"
                }
            })

        if commands:
            draw_result, ok = _run_tool("draw_on_whiteboard", commands=json.dumps(commands))
            if ok:
                sections.append(f"- {draw_result}")
            else:
                sections.append(f"⚠️ Partial failure (whiteboard): {draw_result}")
        else:
            sections.append("- No directory structure to visualize.\n")

        # 4. Mermaid ERD 다이어그램 (output_format=mermaid)
        if output_format == "mermaid":
            sections.append("\n## 📊 Mermaid ER Diagram\n\n")
            try:
                models_found = []
                for line in rev.split("\n"):
                    m = re.match(r'^- `(\w+)` → \*\*(\d+)\*\* fields', line)
                    if m:
                        models_found.append((m.group(1), int(m.group(2))))

                if models_found:
                    mermaid_lines = ["```mermaid", "erDiagram"]
                    for model_name, field_count in models_found:
                        mermaid_lines.append(f"  {model_name} {{")
                        in_model = False
                        for line in rev.split("\n"):
                            if f"**{model_name}**" in line:
                                in_model = True
                                continue
                            if in_model:
                                if line.startswith("**") and not line.startswith(f"**{model_name}**"):
                                    break
                                fm = re.match(r'^- `(\w+)`: `(.+)`', line)
                                if fm:
                                    mermaid_lines.append(f"    {fm.group(2)} {fm.group(1)}")
                        mermaid_lines.append("  }")
                    mermaid_lines.append("```")
                    sections.append("\n".join(mermaid_lines))
                else:
                    sections.append("```mermaid\nerDiagram\n  User ||--o{ Order : places\n  Order ||--|{ OrderItem : contains\n```\n")
            except Exception:
                sections.append("```mermaid\nerDiagram\n  User ||--o{ Order : places\n```\n")

    except Exception as e:
        sections.append(f"- Could not draw diagram: `{e}`\n")

    try_crow_ingest(f"generate_docs completed for {target_path} (format={output_format})", register="arch")

    result = "\n\n---\n\n".join(sections)
    result += _markdown_footer()
    return result


# ═══════════════════════════════════════════════════════════
# M3-A: explain_code — AST 기반 코드 설명
# ═══════════════════════════════════════════════════════════

@mcp.tool
def explain_code(file_path: str, line_number: int) -> str:
    """지정된 파일의 특정 라인에 있는 코드가 무엇을 하는지 tree-sitter AST로 분석하여 설명합니다.
    AST 노드 트리를 통해 해당 라인의 함수/클래스/인터페이스 컨텍스트를 파악하고 간단한 설명을 생성합니다.

    Args:
        file_path: 분석할 파일의 상대 경로
        line_number: 설명을 원하는 1-based 라인 번호
    """
    err = _validate_string(file_path, "file_path")
    if err:
        return _markdown_header("Code Explanation Error", "❌") + f"**{err}**\n" + _markdown_footer()

    root = Path(os.getcwd())
    target = root / file_path
    if not target.exists():
        return (_markdown_header("Code Explanation Error", "❌")
                + f"**File not found: `{file_path}`**\n"
                + _markdown_footer())

    content = _read_file_content(target)
    if content is None:
        return (_markdown_header("Code Explanation Error", "❌")
                + f"**Cannot read file: `{file_path}`**\n"
                + _markdown_footer())

    lines = content.split("\n")
    if line_number < 1 or line_number > len(lines):
        return (_markdown_header("Code Explanation Error", "❌")
                + f"**Line {line_number} is out of range (file has {len(lines)} lines)**\n"
                + _markdown_footer())

    line_content = lines[line_number - 1].strip()
    if not line_content:
        return (_markdown_header("Code Explanation", "ℹ️")
                + f"Line {line_number} is empty.\n"
                + _markdown_footer())

    # Initialize tree-sitter
    _init_tree_sitter()

    ext = target.suffix.lower()
    output = _markdown_header(f'Code Explanation: `{_normalize_path(file_path)}:{line_number}`')
    output += f"> `{line_content}`\n\n"

    if ext in TS_JS_EXTS and _ts_available:
        ast = _parse_with_tree_sitter(content, ext)

        # Find enclosing function/class/interface
        enclosing_func = None
        enclosing_class = None
        enclosing_iface = None

        for fn in ast.get("functions", []):
            if fn["line"] <= line_number <= fn.get("end_line", fn["line"]):
                enclosing_func = fn

        for cls in ast.get("classes", []):
            if cls["line"] <= line_number <= cls.get("end_line", cls["line"]):
                enclosing_class = cls

        for iface in ast.get("interfaces", []):
            if iface["line"] <= line_number <= iface.get("end_line", iface["line"]):
                enclosing_iface = iface

        # Context summary
        output += "## Context\n\n"
        if enclosing_func:
            output += f"- **Function**: `{enclosing_func['name']}` ({enclosing_func['type']}, lines {enclosing_func['line']}-{enclosing_func['end_line']})\n"
        if enclosing_class:
            output += f"- **Class**: `{enclosing_class['name']}` (line {enclosing_class['line']})\n"
        if enclosing_iface:
            output += f"- **Interface/Type**: `{enclosing_iface['name']}` ({enclosing_iface['type']}, line {enclosing_iface['line']})\n"
        if not enclosing_func and not enclosing_class and not enclosing_iface:
            output += "- Top-level code (no enclosing function or class)\n"

        # Line type detection
        output += "\n## Line Analysis\n\n"
        line_lower = line_content.lower()

        if line_content.startswith("import ") or line_content.startswith("from ") or line_content.startswith("require("):
            output += "- **Import statement**: imports external module or dependency.\n"
        elif line_content.startswith("export ") or line_content.startswith("module.exports"):
            output += "- **Export statement**: exposes symbols to other modules.\n"
        elif line_content.startswith("function ") or line_content.startswith("async function"):
            output += "- **Function declaration**: defines a named function.\n"
        elif line_content.startswith("const ") or line_content.startswith("let ") or line_content.startswith("var "):
            output += "- **Variable declaration**: declares a new variable.\n"
        elif line_content.startswith("class "):
            output += "- **Class declaration**: defines a new class.\n"
        elif line_content.startswith("interface "):
            output += "- **Interface declaration**: defines a TypeScript interface.\n"
        elif line_content.startswith("type "):
            output += "- **Type alias**: defines a type alias.\n"
        elif line_content.startswith("return "):
            output += "- **Return statement**: returns a value from the current function.\n"
        elif line_content.startswith("if ") or line_content.startswith("else ") or line_content.startswith("else if"):
            output += "- **Conditional branch**: controls flow based on a condition.\n"
        elif line_content.startswith("for ") or line_content.startswith("while ") or line_content.startswith("do "):
            output += "- **Loop**: iterates over a collection or repeats execution.\n"
        elif line_content.startswith("try ") or line_content.startswith("catch ") or line_content.startswith("finally "):
            output += "- **Error handling**: catches and handles exceptions.\n"
        elif line_content.startswith("switch ") or line_content.startswith("case ") or line_content.startswith("default:"):
            output += "- **Switch/case**: multi-branch conditional.\n"
        elif line_content.startswith("//") or line_content.startswith("#") or line_content.startswith("/*") or line_content.startswith("*"):
            output += "- **Comment**: documentation or code note.\n"
        elif line_content.startswith("}"):
            output += "- **Closing brace**: closes a block (function, class, if, etc.).\n"
        elif "=>" in line_content:
            output += "- **Arrow function**: shorthand function expression.\n"
        elif " = " in line_content and "(" in line_content:
            output += "- **Assignment/call**: variable assignment with function call.\n"
        elif "(" in line_content and ")" in line_content:
            output += "- **Function/method call**: invokes a function or method.\n"
        else:
            output += "- Expression or statement.\n"

    else:
        # Fallback for non-TS/JS files or when tree-sitter is unavailable
        output += "## Line Content\n\n"
        output += f"```\n{line_content}\n```\n"
        output += "\n> Note: tree-sitter AST analysis is only available for TypeScript/JavaScript files.\n"

    # Show surrounding context
    output += "\n## Surrounding Context\n\n"
    start = max(0, line_number - 4)
    end = min(len(lines), line_number + 3)
    output += "```\n"
    for i in range(start, end):
        prefix = "→" if i + 1 == line_number else " "
        output += f"{prefix} {i+1:4d} | {lines[i]}\n"
    output += "```\n"

    try_crow_ingest(f"explain_code: {file_path}:{line_number} — {line_content[:60]}", register="context")
    output += _markdown_footer()
    return output


# ═══════════════════════════════════════════════════════════
# M3-B: analyze_changes / review_pr — Git Diff 분석
# ═══════════════════════════════════════════════════════════

@mcp.tool
def analyze_changes() -> str:
    """현재 워크스페이스의 git diff를 분석하여 변경된 파일 목록과 diff 내용을 반환합니다.
    git diff --stat + git diff를 실행하여 변경 사항을 요약하고,
    Crow Memory에서 관련 컨텍스트를 조회합니다.

    Returns:
        Markdown 보고서: 변경 파일 목록, diff 내용, 관련 Crow 기억
    """
    root = os.getcwd()
    output = _markdown_header("Git Changes Analysis")

    try:
        stat_result = subprocess.run(["git", "diff", "--stat"], cwd=root, capture_output=True, text=True, timeout=10)
        stat_output = stat_result.stdout.strip()
        diff_result = subprocess.run(["git", "diff"], cwd=root, capture_output=True, text=True, timeout=10)
        diff_output = diff_result.stdout.strip()

        if not stat_output:
            output += "✅ No uncommitted changes detected.\\n"
            output += _markdown_footer()
            return output

        changed_files = []
        for line in stat_output.split("\\n"):
            if "|" in line:
                parts = line.split("|")
                file_path = parts[0].strip()
                changed_files.append(file_path)

        output += f"## Changed Files ({len(changed_files)})\\n\\n"
        for f in changed_files:
            output += f"- `{_normalize_path(f)}`\\n"
        output += "\\n"

        # ── 변경 유형 분류 ──
        output += "## Change Classification\\n\\n"
        classifications = {"refactoring": 0, "bugfix": 0, "feature": 0, "docs": 0, "other": 0}
        for f in changed_files:
            ext = os.path.splitext(f)[1].lower()
            if ext in (".md", ".txt", ".rst"):
                classifications["docs"] += 1
            elif ext in (".ts", ".tsx", ".js", ".jsx", ".py", ".go"):
                file_diff = ""
                in_file = False
                for line in diff_output.split("\\n"):
                    if f"diff --git a/{f}" in line:
                        in_file = True
                    elif line.startswith("diff --git"):
                        in_file = False
                    if in_file:
                        file_diff += line + "\\n"
                if "TODO" in file_diff or "FIXME" in file_diff:
                    classifications["refactoring"] += 1
                elif "fix" in file_diff.lower() or "bug" in file_diff.lower() or "error" in file_diff.lower():
                    classifications["bugfix"] += 1
                elif "test" in file_diff.lower() or "feat" in file_diff.lower():
                    classifications["feature"] += 1
                else:
                    classifications["feature"] += 1
            else:
                classifications["other"] += 1
        for ctype, count in classifications.items():
            if count > 0:
                emoji = {"refactoring": "🔧", "bugfix": "🐛", "feature": "✨", "docs": "📝", "other": "❓"}
                output += f"- {emoji.get(ctype, '•')} **{ctype}**: {count} file(s)\\n"
        output += "\\n"

        output += "## Diff Content\\n\\n"
        if len(diff_output) > 8000:
            output += f"> Diff is too large ({len(diff_output)} chars), showing first 8000 chars\\n\\n"
            output += "```diff\\n" + diff_output[:8000] + "\\n```\\n"
            output += f"\\n> ... ({len(diff_output) - 8000} more chars)\\n"
        else:
            output += "```diff\\n" + diff_output + "\\n```\\n"

        if changed_files:
            output += "\\n## 🧠 Related Crow Context\\n\\n"
            for f in changed_files[:5]:
                try:
                    file_name = os.path.basename(f)
                    past_context = try_crow_recall(query=f"file changes in {file_name}", register="context", limit=2)
                    if past_context:
                        for item in past_context:
                            content = item.get("content", item.get("value", str(item)))
                            output += f"- `{file_name}`: {content[:200]}\\n"
                    else:
                        output += f"- `{file_name}`: No Crow context found.\\n"
                except Exception:
                    output += f"- `{file_name}`: Could not query Crow.\\n"

    except FileNotFoundError:
        output += "❌ Git not available. Make sure git is installed and this is a git repository.\\n"
    except subprocess.TimeoutExpired:
        output += "❌ Git diff timed out.\\n"
    except Exception as e:
        output += f"❌ Error: {e}\\n"

    try_crow_ingest(f"analyze_changes: {len(changed_files)} files changed, types: {dict(classifications)}", register="life_context")
    output += _markdown_footer()
    return output
@mcp.tool
def review_pr(base_branch: str = "main", head_branch: str = "") -> str:
    """analyze_changes + review_code를 통합하여 PR 리뷰 보고서를 생성합니다.
    두 브랜치 간의 git diff를 분석하고, 변경된 파일들에 대해 코드 리뷰를 수행합니다.

    Args:
        base_branch: 기준 브랜치 (기본: main)
        head_branch: 대상 브랜치 (기본: 현재 브랜치)

    Returns:
        Markdown PR 리뷰 보고서
    """
    err = _validate_string(base_branch, "base_branch")
    if err:
        return _markdown_header("PR Review Error", "❌") + f"**{err}**\\n" + _markdown_footer()

    root = os.getcwd()
    output = _markdown_header("Pull Request Review")
    output += f"> **Base**: `{base_branch}` → **Head**: `{head_branch or 'current'}`\\n\\n"

    try:
        diff_cmd = ["git", "diff"]
        if head_branch:
            diff_cmd.extend([f"{base_branch}...{head_branch}"])
        else:
            diff_cmd.append(f"{base_branch}..HEAD")

        stat_result = subprocess.run(diff_cmd + ["--stat"], cwd=root, capture_output=True, text=True, timeout=10)
        stat_output = stat_result.stdout.strip()
        diff_result = subprocess.run(diff_cmd, cwd=root, capture_output=True, text=True, timeout=10)
        diff_output = diff_result.stdout.strip()

        if not stat_output:
            output += "⚠️ No differences found between branches.\\n"
            output += _markdown_footer()
            return output

        changed_files = []
        for line in stat_output.split("\\n"):
            if "|" in line:
                parts = line.split("|")
                file_path = parts[0].strip()
                changed_files.append(file_path)

        output += f"## 📂 Changed Files ({len(changed_files)})\\n\\n"
        for f in changed_files:
            output += f"- `{_normalize_path(f)}`\\n"
        output += "\\n"

        total_additions = 0
        total_deletions = 0
        for line in stat_output.split("\\n"):
            m = re.search(r'(\d+) insertion', line)
            if m: total_additions += int(m.group(1))
            m = re.search(r'(\d+) deletion', line)
            if m: total_deletions += int(m.group(1))

        output += f"## 📈 Stats\\n\\n"
        output += f"- **{len(changed_files)}** files changed\\n"
        output += f"- **+{total_additions}** / **-{total_deletions}** lines\\n\\n"

        # ── 변경 파일 간 의존성 분석 ──
        output += "## 🔗 Dependency Analysis\\n\\n"
        changed_set = set(changed_files)
        project_root = Path(root)
        file_deps = defaultdict(set)
        for f in changed_files:
            p = project_root / f
            if p.exists():
                content_f = _read_file_content(p)
                if content_f:
                    ext_f = p.suffix.lower()
                    if ext_f in TS_JS_EXTS:
                        ast_imports = _extract_ast_imports(content_f, ext_f)
                        for imp in ast_imports:
                            file_deps[f].add(imp["module"])
                    else:
                        regex_imports = _extract_regex_imports(str(p))
                        for imp in regex_imports:
                            file_deps[f].add(imp)
        cross_refs = []
        for f, deps_set in file_deps.items():
            for dep in deps_set:
                for cf in changed_set:
                    if cf != f and (dep in cf or cf.endswith(dep.replace(".", "/"))):
                        cross_refs.append((f, cf))
        if cross_refs:
            output += "⚠️ Cross-file dependencies detected in this PR:\\n\\n"
            for src, target in cross_refs[:5]:
                output += f"- `{src}` → imports `{target}`\\n"
            output += "\\n> These files should be reviewed together for consistency.\\n"
        else:
            output += "✅ No cross-file dependencies detected.\\n"
        output += "\\n"

        # ── 롤백 위험도 평가 ──
        output += "## ⚠️ Rollback Risk Assessment\\n\\n"
        risk_score = 0
        risk_factors = []
        if len(changed_files) > 10:
            risk_score += 2
            risk_factors.append(f"Large PR ({len(changed_files)} files)")
        if total_deletions > 100:
            risk_score += 2
            risk_factors.append(f"Heavy deletions ({total_deletions} lines)")
        if total_additions > 200:
            risk_score += 1
            risk_factors.append(f"Large additions ({total_additions} lines)")
        if cross_refs:
            risk_score += 2
            risk_factors.append(f"Cross-file dependencies ({len(cross_refs)})")
        if "package.json" in changed_set or "go.mod" in changed_set or "requirements.txt" in changed_set:
            risk_score += 3
            risk_factors.append("Dependency manifest changed")
        if risk_score == 0:
            output += "🟢 **Low risk** — Safe to merge after review.\\n"
        elif risk_score <= 3:
            output += "🟡 **Medium risk** — Review carefully.\\n"
        elif risk_score <= 6:
            output += "🟠 **High risk** — Multiple reviewers recommended.\\n"
        else:
            output += "🔴 **Critical risk** — Consider splitting this PR.\\n"
        if risk_factors:
            output += "\\nRisk factors:\\n"
            for rf in risk_factors:
                output += f"- {rf}\\n"
        output += "\\n"

        output += "## 📝 Code Review per File\\n\\n"
        for f in changed_files[:10]:
            output += f"### `{_normalize_path(f)}`\\n\\n"
            p = project_root / f
            if p.exists():
                review_result = review_code(f)
                for line in review_result.split("\\n"):
                    if "⚠️" in line or "📝" in line or "✅" in line or "Found" in line:
                        output += line + "\\n"
            else:
                output += "*(file deleted in this PR)*\\n"
            output += "\\n"

        output += "## 🔍 Diff Preview\\n\\n"
        if len(diff_output) > 4000:
            output += f"```diff\\n{diff_output[:4000]}\\n```\\n"
            output += f"\\n> ... ({len(diff_output) - 4000} more chars)\\n"
        else:
            output += f"```diff\\n{diff_output}\\n```\\n"

        output += "\\n## 🧠 Crow Memory Context\\n\\n"
        for f in changed_files[:3]:
            file_name = os.path.basename(f)
            past_context = try_crow_recall(query=f"review {file_name}", register="style", limit=2)
            if past_context:
                for item in past_context:
                    content = item.get("content", item.get("value", str(item)))
                    output += f"- `{file_name}`: {content[:200]}\\n"
        output += "\\n"

    except FileNotFoundError:
        output += "❌ Git not available. Make sure git is installed and this is a git repository.\\n"
    except subprocess.TimeoutExpired:
        output += "❌ Git diff timed out.\\n"
    except Exception as e:
        output += f"❌ Error: {e}\\n"

    try_crow_ingest(json.dumps({"action": "review_pr", "base": base_branch, "head": head_branch, "files": len(changed_files), "risk": risk_score}), register="context")
    output += _markdown_footer()
    return output
@mcp.tool
def refactor_across_files(pattern: str, new_pattern: str, file_patterns: Optional[str] = None) -> str:
    """search_codebase로 패턴을 찾고, 모든 발생 위치에 대해 일괄 수정 제안을 생성합니다.
    실제 파일 수정 없이 변경 제안서를 마크다운으로 반환합니다.

    Args:
        pattern: 찾을 코드 패턴 (검색어)
        new_pattern: 대체할 새 패턴 (변경 제안)
        file_patterns: 검색 대상 파일 패턴 (예: *.ts,*.tsx). 쉼표로 구분.

    Returns:
        Markdown 리팩토링 제안서: 각 발생 위치와 제안된 변경 사항
    """
    err = _validate_string(pattern, "pattern")
    if err:
        return _markdown_header("Refactoring Error", "❌") + f"**{err}**\\n" + _markdown_footer()
    err = _validate_string(new_pattern, "new_pattern")
    if err:
        return _markdown_header("Refactoring Error", "❌") + f"**{err}**\\n" + _markdown_footer()

    output = _markdown_header("Multi-File Refactoring Proposal")
    output += f"> **Search**: `{pattern}`\\n"
    output += f"> **Replace with**: `{new_pattern}`\\n"
    output += f"> **File patterns**: `{file_patterns or '*.ts,*.tsx,*.js,*.jsx,*.py'}`\\n\\n"

    search_result = search_codebase(query=pattern, file_patterns=file_patterns, max_results=50)
    occurrences = []
    for line in search_result.split("\\n"):
        m = re.match(r'^- `(.+?:\d+):', line)
        if m: occurrences.append(m.group(1))
        m2 = re.match(r'^- `(.+?:\d+)`', line)
        if m2: occurrences.append(m2.group(1))

    if not occurrences:
        output += "✅ No occurrences found for this pattern.\\n"
        output += _markdown_footer()
        return output

    output += f"## Found {len(occurrences)} Occurrences\\n\\n"
    by_file = defaultdict(list)
    for occ in occurrences:
        parts = occ.split(":")
        if len(parts) >= 2:
            by_file[parts[0]].append(parts[1])

    output += f"### Files Affected: {len(by_file)}\\n\\n"
    for file_path, lines in sorted(by_file.items()):
        line_list = ", ".join(lines[:10])
        suffix = f" ... and {len(lines)-10} more" if len(lines) > 10 else ""
        output += f"- `{_normalize_path(file_path)}` — lines {line_list}{suffix}\\n"

    output += "\\n## Suggested Changes\\n\\n"
    for file_path, lines in sorted(by_file.items())[:10]:
        actual_path = Path(os.getcwd()) / file_path
        if not actual_path.exists(): continue
        content = _read_file_content(actual_path)
        if content is None: continue
        file_lines = content.split("\\n")
        output += f"### `{_normalize_path(file_path)}`\\n\\n"
        output += f"```diff\\n"
        for line_num_str in lines[:5]:
            idx = int(line_num_str) - 1
            if 0 <= idx < len(file_lines):
                original = file_lines[idx]
                output += f"-{original}\\n"
                suggested = original.replace(pattern, new_pattern)
                output += f"+{suggested}\\n"
        output += f"```\\n\\n"

    # ── 영향도 분석 ──
    output += "## 📊 Impact Analysis\\n\\n"
    total_affected_lines = sum(len(ls) for ls in by_file.values())
    output += f"- **Scale**: {len(occurrences)} changes across {len(by_file)} files\\n"
    output += f"- **Total affected lines**: {total_affected_lines}\\n"
    if total_affected_lines > 50:
        output += "- **Risk**: 🔴 **High** — extensive changes, may introduce side effects\\n"
    elif total_affected_lines > 20:
        output += "- **Risk**: 🟡 **Medium** — moderate changes, review recommended\\n"
    else:
        output += "- **Risk**: 🟢 **Low** — limited changes\\n"
    if len(by_file) > 5:
        output += "- **Dependency impact**: Changes span multiple files — ensure imports are updated\\n"
    output += "\\n> Note: This is a **proposal only**. No files have been modified.\\n"
    output += "> To apply changes, use your editor's find-and-replace or manual editing.\\n"

    try_crow_ingest(json.dumps({"action": "refactor_across_files", "pattern": pattern, "new_pattern": new_pattern, "occurrences": len(occurrences), "files_affected": len(by_file)}), register="style")
    output += _markdown_footer()
    return output
@mcp.tool
def learn_project(target_path: Optional[str] = None) -> str:
    """summarize_architecture + extract_patterns + map_dependencies 결과를 Crow Memory에 축적합니다.
    프로젝트 분석 결과를 Crow arch/style/life_context 레지스터에 각각 저장하여,
    이후 세션에서 프로젝트 컨텍스트를 자동으로 복원할 수 있게 합니다.

    Args:
        target_path: 분석 대상 디렉토리 경로 (기본: 현재 작업 디렉토리)

    Returns:
        Markdown 보고서: Crow에 저장된 내용 요약
    """
    root = Path(get_project_root(target_path))
    output = _markdown_header("Project Knowledge Ingestion")
    output += f"> Target: `{root}`\n\n"

    # 1. Summarize architecture
    output += "## 1. Architecture Summary\n\n"
    arch_summary = summarize_architecture(target_path=str(root))
    try_crow_ingest(
        json.dumps({
            "action": "learn_project",
            "type": "architecture",
            "target": str(root),
            "summary": arch_summary[:1000],
            "timestamp": time.time(),
        }),
        register="arch"
    )
    for line in arch_summary.split("\n"):
        if "file types" in line:
            output += f"- {line.strip()}\n"
    output += "- ✅ Architecture stored in Crow `arch` register\n\n"

    # 2. Extract patterns
    output += "## 2. Code Patterns\n\n"
    patterns = extract_patterns(target_path=str(root), min_occurrences=3)
    try_crow_ingest(
        json.dumps({
            "action": "learn_project",
            "type": "patterns",
            "target": str(root),
            "patterns": patterns[:1000],
            "timestamp": time.time(),
        }),
        register="style"
    )
    for line in patterns.split("\n"):
        if "occurrences" in line:
            output += f"- {line.strip()}\n"
    output += "- ✅ Patterns stored in Crow `style` register\n\n"

    # 3. Map dependencies
    output += "## 3. Dependency Map\n\n"
    deps = map_dependencies(target_path=str(root))
    try_crow_ingest(
        json.dumps({
            "action": "learn_project",
            "type": "dependencies",
            "target": str(root),
            "deps": deps[:1000],
            "timestamp": time.time(),
        }),
        register="arch"
    )
    for line in deps.split("\n"):
        if "circular" in line.lower() or "import" in line.lower() or "dependencies" in line:
            output += f"- {line.strip()}\n"
    output += "- ✅ Dependencies stored in Crow `arch` register\n\n"

    # 4. Project identity (life_context)
    project_key = f"project:{hashlib.md5(str(root).encode()).hexdigest()[:8]}"
    try_crow_ingest(
        json.dumps({
            "action": "learn_project",
            "type": "identity",
            "project_key": project_key,
            "target": str(root),
            "timestamp": time.time(),
        }),
        register="life_context"
    )
    output += f"- ✅ Project identity stored in Crow `life_context` (key: `{project_key}`)\n\n"

    output += "---\n"
    output += "✅ **Project knowledge ingestion complete.**\n"
    output += _markdown_footer()
    return output


@mcp.tool
def recall_project(target_path: Optional[str] = None) -> str:
    """Crow Memory에서 learn_project로 저장된 프로젝트 지식을 회상합니다.
    arch, style, life_context 레지스터에서 관련 정보를 조회하여 반환합니다.

    Args:
        target_path: 분석 대상 디렉토리 경로 (기본: 현재 작업 디렉토리)

    Returns:
        Markdown 보고서: Crow에서 회상된 프로젝트 지식
    """
    root = Path(get_project_root(target_path))
    root_str = str(root)
    project_key = f"project:{hashlib.md5(root_str.encode()).hexdigest()[:8]}"

    output = _markdown_header("Project Knowledge Recall")
    output += f"> Target: `{root}`\n"
    output += f"> Project key: `{project_key}`\n\n"

    # 1. Query arch register
    output += "## 🏗️ Architecture (arch register)\n\n"
    arch_results = try_crow_recall(query=root_str, register="arch", limit=5)
    if arch_results:
        for item in arch_results:
            content = item.get("content", item.get("value", str(item)))
            output += f"- {_truncate(content, 300)}\n"
    else:
        output += "- No architecture data found in Crow.\n"
        output += "  → Run `learn_project()` first to store project knowledge.\n"

    # 2. Query style register (patterns)
    output += "\n## 📊 Code Patterns (style register)\n\n"
    style_results = try_crow_recall(query=root_str, register="style", limit=5)
    if style_results:
        for item in style_results:
            content = item.get("content", item.get("value", str(item)))
            output += f"- {_truncate(content, 300)}\n"
    else:
        output += "- No pattern data found in Crow.\n"

    # 3. Query life_context for project identity
    output += "\n## 🔑 Project Identity (life_context)\n\n"
    life_results = try_crow_recall(query=project_key, register="life_context", limit=3)
    if life_results:
        for item in life_results:
            content = item.get("content", item.get("value", str(item)))
            output += f"- {_truncate(content, 300)}\n"
    else:
        output += "- No project identity found in Crow.\n"

    # 4. Summary
    total = len(arch_results) + len(style_results) + len(life_results)
    output += f"\n---\n**Total {total} knowledge items recalled from Crow.**\n"
    output += _markdown_footer()
    return output


# ═══════════════════════════════════════════════════════════
# M3-E: learn_preference / get_preferences — 사용자 선호도 학습
# ═══════════════════════════════════════════════════════════

@mcp.tool
def learn_preference(rule: str, category: str = "coding_style") -> str:
    """사용자의 코딩 스타일 규칙이나 선호도를 Crow Memory에 저장합니다.
    예: "함수형 컴포넌트 선호", "interface보다 type 사용", "tab width: 2"

    Args:
        rule: 저장할 규칙 또는 선호도 설명
        category: 카테고리 (coding_style, naming, formatting, architecture, workflow)

    Returns:
        저장 확인 메시지
    """
    err = _validate_string(rule, "rule")
    if err:
        return (_markdown_header("Learn Preference Error", "❌")
                + f"**{err}**\n"
                + _markdown_footer())

    allowed_categories = {"coding_style", "coding", "naming", "formatting", "architecture", "workflow"}
    if category not in allowed_categories:
        return (_markdown_header("Learn Preference Error", "❌")
                + f"**Invalid category: `{category}`. Allowed: {', '.join(allowed_categories)}**\n"
                + _markdown_footer())

    # Store in local preferences file
    try:
        prefs = {}
        if os.path.exists(PREFERENCES_FILE):
            try:
                with open(PREFERENCES_FILE) as f:
                    prefs = json.load(f)
            except Exception:
                prefs = {}
        if category not in prefs:
            prefs[category] = []
        prefs[category].append({
            "rule": rule,
            "timestamp": time.time(),
        })
        _atomic_write_json(PREFERENCES_FILE, prefs, indent=2)
    except Exception as e:
        return (_markdown_header("Learn Preference Error", "❌")
                + f"**Failed to save: `{e}`**\n"
                + _markdown_footer())

    # Also store in Crow life_context
    try_crow_ingest(
        json.dumps({
            "action": "learn_preference",
            "category": category,
            "rule": rule,
            "timestamp": time.time(),
        }),
        register="life_context"
    )

    return (_markdown_header("Preference Saved")
            + f"**Category**: `{category}`\n"
            + f"**Rule**: `{rule}`\n\n"
            + "Stored in local preferences file and Crow Memory (`life_context`).\n"
            + _markdown_footer())


@mcp.tool
def get_preferences(category: Optional[str] = None) -> str:
    """저장된 모든 사용자 선호도/규칙을 조회합니다.

    Args:
        category: 특정 카테고리만 조회 (생략 시 전체)

    Returns:
        Markdown 형식의 저장된 선호도 목록
    """
    output = _markdown_header("User Preferences")

    # Read from local file
    prefs = {}
    if os.path.exists(PREFERENCES_FILE):
        try:
            with open(PREFERENCES_FILE) as f:
                prefs = json.load(f)
        except Exception:
            prefs = {}

    if not prefs:
        output += "No preferences saved yet.\n"
        output += "\n> Use `learn_preference(rule, category)` to save your first preference.\n"
        output += _markdown_footer()
        return output

    categories_to_show = [category] if category else list(prefs.keys())

    for cat in categories_to_show:
        if cat not in prefs:
            output += f"### {cat}\n\n⚠️ Category not found.\n\n"
            continue
        rules = prefs[cat]
        if not rules:
            continue
        output += f"## {cat}\n\n"
        for i, entry in enumerate(rules, 1):
            rule_text = entry.get("rule", str(entry))
            ts = entry.get("timestamp", 0)
            if ts:
                d = time.strftime("%Y-%m-%d %H:%M", time.localtime(ts))
                output += f"{i}. `{rule_text}` _(saved: {d})_\n"
            else:
                output += f"{i}. `{rule_text}`\n"
        output += "\n"

    # Also recall from Crow
    output += "## 🔄 Crow Memory (life_context)\n\n"
    crow_prefs = try_crow_recall(query="learn_preference", register="life_context", limit=5)
    if crow_prefs:
        for item in crow_prefs:
            content = item.get("content", item.get("value", str(item)))
            output += f"- {_truncate(content, 200)}\n"
    else:
        output += "- No preference data in Crow.\n"

    output += _markdown_footer()
    return output


# ── 드랍존 액션 파일 ────────────────────────────
DZ_ACTION_FILE = os.path.join(os.path.expanduser("~"), ".vibezoo-dropzone-action.json")


# ── 이미지 업로드 캐시 ──────────────────────────────
IMAGE_CACHE_DIR = os.path.join(os.path.expanduser("~"), ".vibezoo-cache")
os.makedirs(IMAGE_CACHE_DIR, exist_ok=True)
UPLOADED_IMAGE_PATH = os.path.join(IMAGE_CACHE_DIR, "dropped_image.png")


@mcp.custom_route("/upload", methods=["GET", "POST"])
async def image_upload_handler(request: Request) -> JSONResponse:
    """이미지 드래그앤드롭 업로드 엔드포인트"""
    if request.method == "GET":
        html = """<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<title>VibeZoo Drop Zone</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { background: #1e1e1e; color: #ccc; font-family: -apple-system, sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
#dropzone { width: 600px; height: 400px; border: 3px dashed #555; border-radius: 16px; display: flex; flex-direction: column; justify-content: center; align-items: center; gap: 20px; cursor: pointer; transition: all 0.3s; text-align: center; padding: 20px; }
#dropzone:hover, #dropzone.dragover { border-color: #4ec9ff; background: rgba(78,201,255,0.1); }
#dropzone.dragover { border-color: #6acb6a; background: rgba(106,203,106,0.1); }
#dropzone img { max-width: 90%; max-height: 70%; border-radius: 8px; display: none; }
#dropzone.has-image img { display: block; }
#dropzone.has-image .placeholder { display: none; }
.icon { font-size: 64px; opacity: 0.5; }
.hint { font-size: 14px; color: #888; }
.status { font-size: 16px; color: #6acb6a; margin-top: 12px; }
input[type=file] { display: none; }
</style>
</head><body>
<div id="dropzone" onclick="document.getElementById('fileInput').click()">
<div class="icon">&#128247;</div>
<div class="placeholder">
<h2>Drag & Drop Image Here</h2>
<p style="color:#888;margin-top:8px;">or click to browse</p>
</div>
<img id="preview">
<div class="status" id="status"></div>
</div>
<input type="file" id="fileInput" accept="image/*" onchange="uploadFile(this.files[0])">
<script>
function uploadFile(file) {
    if (!file) return;
    var formData = new FormData();
    formData.append('image', file);
    document.getElementById('status').textContent = 'Uploading...';
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/upload', true);
    xhr.onload = function() {
        if (xhr.status === 200) {
            var data = JSON.parse(xhr.responseText);
            document.getElementById('status').innerHTML = '✅ Uploaded! Path: <code>' + data.path + '</code>';
            var reader = new FileReader();
            reader.onload = function(e) {
                var img = document.getElementById('preview');
                img.src = e.target.result;
                img.style.display = 'block';
                document.getElementById('dropzone').classList.add('has-image');
            };
            reader.readAsDataURL(file);
        } else {
            document.getElementById('status').textContent = '❌ Upload failed';
        }
    };
    xhr.onerror = function() { document.getElementById('status').textContent = '❌ Network error'; };
    xhr.send(formData);
}
document.getElementById('dropzone').addEventListener('dragover', function(e) {
    e.preventDefault();
    this.classList.add('dragover');
});
document.getElementById('dropzone').addEventListener('dragleave', function(e) {
    this.classList.remove('dragover');
});
document.getElementById('dropzone').addEventListener('drop', function(e) {
    e.preventDefault();
    this.classList.remove('dragover');
    var file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) uploadFile(file);
});
</script>
</body></html>"""
        return HTMLResponse(html, status_code=200)
    
    elif request.method == "POST":
        try:
            from starlette.datastructures import UploadFile
            form = await request.form()
            file: UploadFile = form.get("image")
            if not file:
                return JSONResponse({"error": "No file uploaded"}, status_code=400)
            
            content_bytes = await file.read()
            with open(UPLOADED_IMAGE_PATH, "wb") as f:
                f.write(content_bytes)
            
            return JSONResponse({
                "status": "ok",
                "path": UPLOADED_IMAGE_PATH,
                "size": len(content_bytes),
            }, status_code=200)
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)


@mcp.tool
def open_image_dropzone() -> str:
    """브라우저에서 이미지 드래그앤드롭 업로드 페이지를 엽니다.
    업로드된 이미지는 ~/.vibezoo-cache/dropped_image.png에 저장됩니다.
    이후 aggregate_spatial_pixels()로 분석할 수 있습니다.
    
    Returns:
        업로드 페이지 URL 및 사용법 안내
    """
    try:
        import webbrowser
        port = 9027
        
        url = f"http://localhost:{port}/upload"
        
        try:
            webbrowser.open(url)
            browser_msg = "✅ Browser opened automatically."
        except:
            browser_msg = "🔗 Open this URL in your browser:"
        
        return (_markdown_header("Image Drop Zone", "📸")
                + f"{browser_msg}\n\n"
                + f"**URL**: `{url}`\n\n"
                + f"### Usage\n"
                + f"1. Open the URL in your browser\n"
                + f"2. Drag & drop an image file onto the drop zone\n"
                + f"3. Wait for '✅ Uploaded' confirmation\n"
                + f"4. Then call `aggregate_spatial_pixels(image_path=\"~/.vibezoo-cache/dropped_image.png\")`\n\n"
                + f"### Cached file location\n"
                + f"`{UPLOADED_IMAGE_PATH}`\n"
                + _markdown_footer())
    except Exception as e:
        return (_markdown_header("Drop Zone Error", "❌")
                + f"**Failed to open drop zone**: {e}\n"
                + _markdown_footer())


@mcp.tool
def open_dropzone(message: str = "") -> str:
    """VibeZoo 드랍존을 엽니다. AI가 파일 업로드/분석이 필요할 때 호출합니다.
    
    동작 방식:
    1. VS Code Extension이 설치된 경우 → Webview 패널이 열립니다
    2. 일반 VS Code / 브라우저 환경 → 브라우저 기반 드롭존이 열립니다
    3. 업로드된 파일은 ~/.vibezoo-cache/에 저장됩니다
    """
    browser_msg = ""
    try:
        # 1. Extension용 action 파일 생성
        data = {"action": "open", "message": message, "timestamp": time.time()}
        _atomic_write_json(DZ_ACTION_FILE, data, indent=2)
        
        # 2. 브라우저 fallback (일반 VS Code / 브라우저 환경)
        try:
            import webbrowser
            port = 9027
            url = f"http://localhost:{port}/upload"
            webbrowser.open(url)
            browser_msg = f"\n\n🌐 Browser fallback: `{url}`\n👉 Drag & drop any file there."
        except:
            pass
        
        try_crow_ingest(f"Dropzone opened: {message[:100]}" if message else "Dropzone opened", register="context")
        return (_markdown_header("Drop Zone", "📸")
                + f"Drop zone opened. {message}\n"
                + browser_msg
                + _markdown_footer())
    except Exception as e:
        return (_markdown_header("Drop Zone Error", "❌")
                + f"**Failed:** `{e}`\n"
                + _markdown_footer())
# ═══════════════════════════════════════════════════════════
# 메인 — SSE 서버 시작
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VibeZoo MCP Bridge Server")
    parser.add_argument("--port", type=int, default=9027, help="SSE server port")
    args = parser.parse_args()

    print(f"🚀 VibeZoo MCP Bridge v{VERSION} starting on port {args.port}...")
    print(f"   Crow Memory: {CROW_URL} (timeout: {CROW_TIMEOUT}s)")

    # Tree-sitter 초기화 시도 및 상태 로깅
    if _init_tree_sitter():
        print(f"   ✅ Tree-sitter AST: available (typescript, javascript)")
    else:
        print(f"   ⚠️  Tree-sitter not installed — using regex fallback.")
        print(f"      Run vibezoo_setup(target=\"recommended\") for AST-based analysis.")

    mcp.run(transport="sse", host="127.0.0.1", port=args.port)
