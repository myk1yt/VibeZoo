# VibeZoo MCP Bridge — 통합 MCP 서버
# Scout(코드 검색) + Reviewer(리뷰) + Tester(테스트) + DeepAnalyzer(분석)
# Crow Memory(Python)와 동일한 FastMCP 기반, 단일 파일로 모든 기능 제공
# 포트 9027에서 SSE transport로 실행
# 필요시 Crow Memory(9020)에 연결하여 기억 저장/조회

import asyncio
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

try:
    from fastmcp import FastMCP
except ImportError:
    print("fastmcp not installed. Install with: pip install fastmcp")
    sys.exit(1)

try:
    from starlette.responses import JSONResponse
    from starlette.requests import Request
except ImportError:
    # FastMCP 의존성에 포함되어 있음
    from starlette.responses import JSONResponse
    from starlette.requests import Request

CROW_URL = os.environ.get("CROW_SERVER_URL", "http://localhost:9020")
mcp = FastMCP(name="vibezoo")


# ── Health Check ──────────────────────────────────────────

@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """헬스체크 엔드포인트 — Bridge 상태 및 Crow 연결 상태 반환"""
    crow_ok = False
    try:
        import requests
        resp = requests.get(f"{CROW_URL}/health", timeout=2)
        crow_ok = resp.ok
    except Exception:
        pass
    return JSONResponse({
        "status": "ok",
        "crow": crow_ok,
        "timestamp": time.time(),
        "version": "0.11.1",
    })

# ── 도우미 함수 ──────────────────────────────────────────

# 화이트보드 파일 경로 (피드백 루프용)
WHITEBOARD_FILE = os.path.join(os.path.expanduser("~"), ".vibezoo-whiteboard.json")

# ── 도우미 함수 ──────────────────────────────────────────

# Tree-sitter 초기화 (M1-B: AST 파싱)
_ts_available = False
_ts_parser = None
_ts_ts_language = None
_ts_ts_language_js = None


def _init_tree_sitter():
    """Tree-sitter 초기화 — 실패 시 False 반환 (regex fallback)"""
    global _ts_available, _ts_parser
    if _ts_available:
        return True
    try:
        # tree-sitter 설치 시도
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "tree-sitter", "--quiet"],
            capture_output=True, text=True, timeout=30
        )
    except Exception:
        pass
    try:
        import tree_sitter as ts
        _ts_parser = ts.Parser()
        # TypeScript/JavaScript 언어 로드 시도
        try:
            from tree_sitter_languages import get_language
            _ts_ts_language = get_language("typescript")
            _ts_ts_language_js = get_language("javascript")
        except ImportError:
            # tree_sitter_languages가 없으면 tree-sitter-typescript 시도
            try:
                from tree_sitter_typescript import language as ts_lang
                from tree_sitter_javascript import language as js_lang
                _ts_ts_language = ts_lang()
                _ts_ts_language_js = js_lang()
            except ImportError:
                print("[VibeZoo] tree-sitter languages not available, using regex fallback")
                return False
        _ts_available = True
        return True
    except Exception as e:
        print(f"[VibeZoo] tree-sitter init failed: {e}, using regex fallback")
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
                    classes.append({
                        "name": content[name_node.start_byte:name_node.end_byte],
                        "line": node.start_point[0] + 1,
                    })
            elif node_type in ("interface_declaration", "type_alias_declaration"):
                name_node = node.child_by_field_name("name")
                if name_node:
                    interfaces.append({
                        "name": content[name_node.start_byte:name_node.end_byte],
                        "line": node.start_point[0] + 1,
                        "type": node_type,
                    })
            for child in node.children:
                walk(child, depth + 1)

        walk(root)
        return {"functions": functions, "classes": classes, "interfaces": interfaces}
    except Exception as e:
        print(f"[VibeZoo] tree-sitter parse error: {e}")
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
                    # 내장 호출 제외 (단순화)
                    if name not in ("require", "import"):
                        calls.append({
                            "name": name,
                            "line": node.start_point[0] + 1,
                        })
            for child in node.children:
                walk(child, depth + 1)

        walk(root)
        return calls
    except Exception as e:
        print(f"[VibeZoo] AST call extraction error: {e}")
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
            # import { ... } from 'module'
            if node.type == "import_statement":
                source_node = node.child_by_field_name("source")
                if source_node:
                    module = content[source_node.start_byte:source_node.end_byte]
                    imports.append({
                        "module": module.strip("'\""),
                        "type": "import",
                        "line": node.start_point[0] + 1,
                    })
            # require('module') call
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
            # import.meta / dynamic import
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
    except Exception as e:
        print(f"[VibeZoo] AST import extraction error: {e}")
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
                # object_type 내부의 property_signature 찾기
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
                            # 타입이 명시되지 않았을 수 있음
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
    except Exception as e:
        print(f"[VibeZoo] AST field extraction error: {e}")
        return {}


@mcp.tool
def capture_screen() -> str:
    """화면을 캡처하여 화이트보드에 자동으로 붙여넣습니다. AI가 시각적 분석이 필요할 때 호출합니다."""
    try:
        from PIL import ImageGrab
        import base64
        from io import BytesIO
        
        img = ImageGrab.grab()
        buf = BytesIO()
        img.save(buf, format='PNG')
        img_b64 = base64.b64encode(buf.getvalue()).decode()
        
        # 화이트보드 파일에 저장
        data = {
            "timestamp": time.time(),
            "type": "screenshot",
            "image": f"data:image/png;base64,{img_b64}"
        }
        with open(WHITEBOARD_FILE, "w") as f:
            json.dump(data, f)
        
        return f"Screen captured ({img.width}x{img.height}). Image saved to whiteboard."
    except ImportError:
        return "Pillow not installed. Run: pip install Pillow"
    except Exception as e:
        return f"Capture failed: {e}"

def get_project_root(target_path: str = "") -> str:
    if target_path:
        p = Path(target_path)
        if p.exists():
            return str(p if p.is_dir() else p.parent)
    return os.getcwd()

def find_files(patterns: list[str], exclude_dirs: set = None) -> list[str]:
    if exclude_dirs is None:
        exclude_dirs = {".git", "node_modules", ".zoo-code", "dist", "build", ".next", "coverage", "target", "vendor", "__pycache__"}
    results = []
    root = Path(os.getcwd())
    for pattern in patterns:
        for p in root.rglob(pattern):
            if not any(part in str(p) for part in exclude_dirs):
                results.append(str(p.relative_to(root)))
    return results

def extract_imports(file_path: str) -> list[str]:
    """파일에서 import 문 추출"""
    try:
        content = Path(file_path).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []
    imports = []
    for line in content.split("\n"):
        line = line.strip()
        # TypeScript/JavaScript
        m = re.search(r'from [\'"]([^\'"]+)[\'"]', line)
        if m:
            imports.append(m.group(1))
        # Python
        m = re.match(r'(?:import|from)\s+(\S+)', line)
        if m:
            imports.append(m.group(1))
        # Go
        m = re.match(r'import\s+"([^"]+)"', line)
        if m:
            imports.append(m.group(1))
    return imports

def try_crow_ingest(content: str, register: str = "context", **kwargs):
    """선택적으로 Crow Memory에 저장 (실패해도 무시)"""
    try:
        import requests
        payload = {"content": content, "register": register, **kwargs}
        requests.post(f"{CROW_URL}/ingest", json=payload, timeout=2)
    except Exception:
        pass

def try_crow_recall(query: str, register: str = "context", limit: int = 5) -> list:
    """선택적으로 Crow Memory에서 회상"""
    try:
        import requests
        resp = requests.get(f"{CROW_URL}/recall", params={"query": query, "register": register, "limit": limit}, timeout=2)
        if resp.ok:
            return resp.json().get("results", [])
    except Exception:
        pass
    return []

# ═══════════════════════════════════════════════════════════
# Scout: 코드 탐색 도구 (M1-B: tree-sitter AST 업그레이드)
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
    patterns = file_patterns.split(",") if file_patterns else ["*.ts", "*.tsx", "*.js", "*.jsx", "*.py", "*.go", "*.rs"]
    root = Path(os.getcwd())
    results = []
    ast_results = []
    exclude = {".git", "node_modules", ".zoo-code", "dist", "build", ".next", "vendor", "__pycache__"}

    # tree-sitter 초기화 시도
    _init_tree_sitter()

    # 쿼리 유형 감지: AST 구조 검색인가, 일반 텍스트 검색인가
    is_ast_query = any(keyword in query.lower() for keyword in [
        "function ", "class ", "interface ", "type ", "method ",
        "함수", "클래스", "인터페이스"
    ])

    for pattern in patterns:
        for p in root.rglob(pattern):
            if any(part in str(p) for part in exclude):
                continue
            try:
                content = p.read_text(encoding="utf-8", errors="ignore")
                rel = str(p.relative_to(root))
                ext = p.suffix.lower()

                # tree-sitter AST 파싱 (TS/JS만)
                if is_ast_query and ext in (".ts", ".tsx", ".js", ".jsx"):
                    ast = _parse_with_tree_sitter(content, ext)
                    query_lower = query.lower()

                    # 함수 검색
                    for fn in ast.get("functions", []):
                        if query_lower in fn["name"].lower():
                            ast_results.append(
                                f"{rel}:{fn['line']}: `{fn['type']} {fn['name']}` (lines {fn['line']}-{fn['end_line']})"
                            )

                    # 클래스 검색
                    for cls in ast.get("classes", []):
                        if query_lower in cls["name"].lower():
                            ast_results.append(
                                f"{rel}:{cls['line']}: `class {cls['name']}`"
                            )

                    # 인터페이스 검색
                    for iface in ast.get("interfaces", []):
                        if query_lower in iface["name"].lower():
                            ast_results.append(
                                f"{rel}:{iface['line']}: `{iface['type']} {iface['name']}`"
                            )

                # regex line search (fallback + 일반 검색)
                for i, line in enumerate(content.split("\n"), 1):
                    if query.lower() in line.lower():
                        results.append(f"{rel}:{i}: {line.strip()[:120]}")
                        if len(results) >= max_results:
                            break
                if len(results) >= max_results:
                    break
            except Exception:
                continue
        if len(results) >= max_results:
            break

    output = f"# Search Results for: {query}\n\n"

    # AST 결과 우선 표시
    if ast_results:
        output += f"## 🔍 AST Structure Results\n\nFound {len(ast_results)} structural matches\n\n"
        for r in ast_results[:max_results]:
            output += f"- `{r}`\n"
        output += "\n"

    # 일반 검색 결과
    output += f"## 📄 Line Search Results\n\nFound {len(results)} matches\n\n"
    for r in results[:max_results]:
        output += f"- `{r}`\n"

    if not ast_results and not results:
        output += "No results found.\n"

    # Crow에 검색 기록 저장
    try_crow_ingest(f"Searched: {query}, found {len(results)} line + {len(ast_results)} AST results", register="life_context")

    return output

@mcp.tool
def find_references(symbol: str) -> str:
    """주어진 심볼(함수, 클래스, 변수)의 모든 참조를 찾습니다.
    
    Args:
        symbol: 찾을 심볼 이름
    """
    return search_codebase(query=symbol, max_results=20)

@mcp.tool
def summarize_architecture(target_path: Optional[str] = None) -> str:
    """프로젝트 아키텍처를 분석하여 요약합니다.
    
    Args:
        target_path: 분석 대상 디렉토리 경로
    """
    root = Path(get_project_root(target_path))
    output = "# Project Architecture Summary\n\n"

    # 디렉토리 구조
    output += "## Directory Structure\n\n"
    for p in sorted(root.rglob("*")):
        if any(part in str(p) for part in [".git", "node_modules", ".zoo-code", "dist", "build", ".next", "__pycache__"]):
            continue
        rel = p.relative_to(root)
        depth = len(rel.parts) - 1
        if depth > 3:
            continue
        indent = "  " * depth
        if p.is_dir():
            output += f"{indent}📁 {rel}/\n"
        else:
            output += f"{indent}📄 {rel}\n"

    # 기술 스택 감지
    output += "\n## Detected Technologies\n\n"
    techs = {
        "package.json": "Node.js / TypeScript",
        "go.mod": "Go",
        "Cargo.toml": "Rust",
        "pyproject.toml": "Python",
        "pom.xml": "Java / Maven",
    }
    for file, tech in techs.items():
        if (root / file).exists():
            output += f"- **{tech}**\n"

    # 파일 통계
    stats = {}
    for p in root.rglob("*"):
        if p.is_file() and not any(part in str(p) for part in [".git", "node_modules", ".zoo-code"]):
            ext = p.suffix or "(no ext)"
            stats[ext] = stats.get(ext, 0) + 1
    output += "\n## File Statistics\n\n"
    for ext, count in sorted(stats.items(), key=lambda x: -x[1])[:15]:
        output += f"- `{ext}`: {count} files\n"

    try_crow_ingest(f"Architecture analyzed: {len(stats)} file types", register="arch")
    return output

# ═══════════════════════════════════════════════════════════
# Reviewer: 코드 리뷰 도구
# ═══════════════════════════════════════════════════════════

@mcp.tool
def review_code(file_path: str) -> str:
    """지정된 파일의 코드 리뷰를 수행합니다.
    
    Args:
        file_path: 리뷰할 파일 경로
    """
    p = Path(get_project_root(file_path))
    if not p.exists():
        # 상대 경로로 시도
        p = Path(os.getcwd()) / file_path
    if not p.exists():
        return f"File not found: {file_path}"

    try:
        content = p.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        return f"Cannot read file: {e}"

    lines = content.split("\n")
    output = f"# Code Review: {p.name}\n\n"
    output += f"- **Lines**: {len(lines)}\n"
    output += f"- **Size**: {len(content)} bytes\n\n"

    # 기본 검사
    issues = 0
    for i, line in enumerate(lines, 1):
        if len(line) > 120:
            output += f"- ⚠️ Line {i}: Too long ({len(line)} chars)\n"
            issues += 1
        if "TODO" in line or "FIXME" in line:
            output += f"- 📝 Line {i}: TODO/FIXME: {line.strip()}\n"
            issues += 1
        if "console.log" in line and ".ts" in file_path:
            output += f"- ⚠️ Line {i}: console.log left in code\n"
            issues += 1

    if issues == 0:
        output += "\n✅ No obvious issues found.\n"
    else:
        output += f"\nFound {issues} potential issues.\n"

    try_crow_ingest(f"Reviewed {p.name}: {issues} issues", register="style")
    return output

@mcp.tool
def check_quality(target_path: Optional[str] = None) -> str:
    """프로젝트의 코드 품질을 검사합니다.
    
    Args:
        target_path: 검사 대상 경로
    """
    root = Path(get_project_root(target_path))
    output = "# Code Quality Check\n\n"

    # ESLint
    if (root / "package.json").exists():
        try:
            result = subprocess.run(["npx.cmd" if sys.platform == "win32" else "npx", "eslint", ".", "--ext", ".ts,.tsx,.js,.jsx", "--format", "compact", "--quiet"],
                                    cwd=str(root), capture_output=True, text=True, timeout=30)
            if result.stdout:
                output += f"## ESLint\n\n```\n{result.stdout[:2000]}\n```\n"
            else:
                output += "## ESLint\n\n✅ No issues found.\n"
        except Exception:
            output += "## ESLint\n\n❌ ESLint not available\n"

    # go vet
    if (root / "go.mod").exists():
        try:
            result = subprocess.run(["go", "vet", "./..."], cwd=str(root), capture_output=True, text=True, timeout=30)
            if result.stderr:
                output += f"## go vet\n\n```\n{result.stderr[:1000]}\n```\n"
            else:
                output += "## go vet\n\n✅ No issues found.\n"
        except Exception:
            output += "## go vet\n\n❌ go not available\n"

    return output

# ═══════════════════════════════════════════════════════════
# Deep Analyzer: 코드 심층 분석 도구
# ═══════════════════════════════════════════════════════════

@mcp.tool
def analyze_call_graph(file_path: Optional[str] = None, depth: int = 3) -> str:
    """프로젝트의 함수 호출 그래프를 분석합니다.
    tree-sitter AST로 실제 call_expression 노드를 추출하여 정확한 호출 관계를 파악합니다.
    
    Args:
        file_path: 분석할 파일 경로 (기본: 전체 프로젝트)
        depth: 호출 깊이 (기본: 3)
    """
    root = Path(get_project_root(file_path))
    output = "# Call Graph Analysis\n\n"

    # tree-sitter 초기화
    _init_tree_sitter()

    if (root / "go.mod").exists():
        try:
            result = subprocess.run(["go", "callgraph", "./..."], cwd=str(root), capture_output=True, text=True, timeout=30)
            if result.stdout:
                output += f"## Go Call Graph\n\n```\n{result.stdout[:2000]}\n```\n"
        except Exception:
            output += "## Go call graph: go not available\n"

    # TypeScript/JavaScript: AST 기반 함수 호출 분석
    output += "\n## Function Call Graph (AST)\n\n"
    total_calls = 0
    from collections import Counter
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.suffix not in (".ts", ".tsx", ".js", ".jsx"):
            continue
        if any(part in str(p) for part in [".git", "node_modules", "dist", "build"]):
            continue
        try:
            content = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        rel = p.relative_to(root)
        calls = _extract_ast_calls(content, p.suffix)
        if calls:
            call_counts = Counter(c["name"] for c in calls)
            top_calls = call_counts.most_common(10)
            output += f"### `{rel}`\n\n"
            output += f"- **Total calls**: {len(calls)}\n"
            output += f"- **Unique functions called**: {len(call_counts)}\n"
            for func_name, count in top_calls:
                output += f"  - `{func_name}` ({count}x)\n"
            output += "\n"
            total_calls += len(calls)

    if total_calls == 0:
        output += "- No function calls detected via AST.\n"

    # 파일 간 의존성 (AST 기반 import)
    output += "\n## File-Level Dependencies (AST)\n\n"
    dep_count = 0
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.suffix not in (".ts", ".tsx", ".js", ".jsx"):
            continue
        if any(part in str(p) for part in [".git", "node_modules", "dist", "build"]):
            continue
        try:
            content = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        rel = p.relative_to(root)
        ast_imports = _extract_ast_imports(content, p.suffix)
        if ast_imports:
            modules = list(set(i["module"] for i in ast_imports if not i["module"].startswith(".")))
            local = list(set(i["module"] for i in ast_imports if i["module"].startswith(".")))
            output += f"- `{rel}` → {len(modules)} external + {len(local)} local imports\n"
            dep_count += 1

    if dep_count == 0:
        output += "- No dependencies detected.\n"

    try_crow_ingest(f"Call graph: {total_calls} calls across {dep_count} files", register="arch")
    return output

@mcp.tool
def map_dependencies(target_path: Optional[str] = None) -> str:
    """프로젝트 파일 간 의존성을 분석하고 순환 참조를 탐지합니다.
    tree-sitter AST로 import/require 문을 정확히 분석합니다.
    
    Args:
        target_path: 분석 대상 경로
    """
    root = Path(get_project_root(target_path))
    output = "# Dependency Map\n\n"

    # tree-sitter 초기화
    _init_tree_sitter()

    # 모든 파일에서 import 수집 (AST 우선, regex fallback)
    deps = {}
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        ext = p.suffix
        if ext not in (".ts", ".tsx", ".js", ".jsx", ".py", ".go"):
            continue
        if any(part in str(p) for part in [".git", "node_modules", ".zoo-code"]):
            continue
        rel = str(p.relative_to(root))

        # AST 기반 import 추출 (TS/JS/JSX)
        if ext in (".ts", ".tsx", ".js", ".jsx"):
            try:
                content = p.read_text(encoding="utf-8", errors="ignore")
                ast_imports = _extract_ast_imports(content, ext)
                if ast_imports:
                    deps[rel] = [i["module"] for i in ast_imports]
                    continue
            except Exception:
                pass

        # regex fallback (Python, Go, 또는 AST 실패 시)
        imports = extract_imports(str(p))
        if imports:
            deps[rel] = imports

    # 순환 참조 탐지 (DFS)
    def find_cycles(graph, start, path=None, visited=None):
        if path is None:
            path = []
        if visited is None:
            visited = set()
        if start in path:
            idx = path.index(start)
            return [" → ".join(path[idx:] + [start])]
        if start in visited:
            return []
        visited.add(start)
        cycles = []
        for dep in graph.get(start, []):
            if dep in graph:
                cycles.extend(find_cycles(graph, dep, path + [start], visited))
        return cycles

    all_cycles = []
    for file in deps:
        all_cycles.extend(find_cycles(deps, file))

    if all_cycles:
        all_cycles = list(set(all_cycles))[:10]
        output += "### ⚠️ Circular Dependencies Found\n\n"
        for cycle in all_cycles:
            output += f"- `{cycle}`\n"
    else:
        output += "✅ No circular dependencies detected.\n"

    # 파일별 의존성 수
    output += "\n## Import Count by File\n\n"
    for file, imports in sorted(deps.items(), key=lambda x: -len(x[1]))[:20]:
        output += f"- `{file}`: **{len(imports)}** imports\n"

    try_crow_ingest(f"Dep analysis: {len(deps)} files, {len(all_cycles)} cycles (AST)", register="arch")
    return output

@mcp.tool
def extract_patterns(target_path: Optional[str] = None, min_occurrences: int = 3) -> str:
    """프로젝트 전체에서 반복되는 코드 패턴을 추출합니다.
    
    Args:
        target_path: 분석 대상 경로
        min_occurrences: 최소 발생 횟수 (기본: 3)
    """
    root = Path(get_project_root(target_path))
    patterns = {
        "async/await usage": 0,
        "try-catch usage": 0,
        "console.log usage": 0,
        "TODO/FIXME": 0,
        "Promise chains": 0,
        "arrow functions": 0,
        "export (default|const|function)": 0,
        "interface/type definitions": 0,
    }

    for p in root.rglob("*"):
        if not p.is_file() or p.suffix not in (".ts", ".tsx", ".js", ".jsx", ".py", ".go", ".rs"):
            continue
        if any(part in str(p) for part in [".git", "node_modules", ".zoo-code", "dist", "build"]):
            continue
        try:
            content = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        for key in patterns:
            if key == "async/await usage":
                patterns[key] += content.count("async ") + content.count("await ")
            elif key == "try-catch usage":
                patterns[key] += content.count("try {") + content.count("catch (")
            elif key == "console.log usage":
                patterns[key] += content.count("console.log")
            elif key == "TODO/FIXME":
                patterns[key] += content.count("TODO") + content.count("FIXME")
            elif key == "Promise chains":
                patterns[key] += content.count(".then(") + content.count(".catch(")
            elif key == "arrow functions":
                patterns[key] += content.count("=>")
            elif key == "export (default|const|function)":
                patterns[key] += content.count("export default") + content.count("export const") + content.count("export function")
            elif key == "interface/type definitions":
                patterns[key] += content.count("interface ") + content.count("type ")
                patterns[key] += content.count("struct ") + content.count("class ")

    output = f"# Code Pattern Analysis (min {min_occurrences} occurrences)\n\n"
    for pattern, count in sorted(patterns.items(), key=lambda x: -x[1]):
        if count >= min_occurrences:
            output += f"- ✅ `{pattern}`: **{count}** occurrences\n"
        elif count > 0:
            output += f"- ⬜ `{pattern}`: {count} (below threshold)\n"

    try_crow_ingest(f"Pattern analysis: {sum(patterns.values())} total patterns", register="style")
    return output

@mcp.tool
def reverse_engineer(target_path: Optional[str] = None, format: str = "markdown") -> str:
    """코드베이스로부터 아키텍처 문서, API 명세, ERD를 자동 생성합니다.
    tree-sitter AST로 데이터 모델의 실제 필드까지 추출합니다.
    
    Args:
        target_path: 분석 대상 경로
        format: 출력 형식 (markdown, openapi, mermaid). 기본: markdown
    """
    root = Path(get_project_root(target_path))
    output = "# Reverse Engineering Report\n\n"

    # tree-sitter 초기화
    _init_tree_sitter()

    # 프로젝트 메타데이터
    pkg_json = root / "package.json"
    if pkg_json.exists():
        try:
            pkg = json.loads(pkg_json.read_text())
            output += f"- **Name**: {pkg.get('name', 'N/A')}\n"
            output += f"- **Description**: {pkg.get('description', 'N/A')}\n"
            output += f"- **Version**: {pkg.get('version', 'N/A')}\n\n"
        except Exception:
            pass

    # API 엔드포인트 추출 (Express / Next.js / FastAPI)
    output += "## API Endpoints\n\n"
    endpoints = []
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix not in (".ts", ".tsx", ".js", ".py"):
            continue
        if any(part in str(p) for part in [".git", "node_modules"]):
            continue
        try:
            content = p.read_text(encoding="utf-8", errors="ignore")
            for m in ["get", "post", "put", "delete", "patch"]:
                for match in re.finditer(rf'{m}\s*\([\'"]([^\'"]+)[\'"]', content, re.IGNORECASE):
                    rel = str(p.relative_to(root))
                    endpoints.append(f"- `{m.upper()}` `{match.group(1)}` ({rel})")
        except Exception:
            continue
    for ep in endpoints[:20]:
        output += ep + "\n"
    if not endpoints:
        output += "- No API endpoints detected.\n"

    # 데이터 모델 (AST 기반 필드 추출)
    output += "\n## Data Models\n\n"
    models = []
    all_fields = {}  # model_name -> [fields]
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix not in (".ts", ".tsx", ".js", ".jsx", ".go"):
            continue
        if any(part in str(p) for part in [".git", "node_modules"]):
            continue
        try:
            content = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        rel = p.relative_to(root)

        # AST 기반 필드 추출 (TS/JS)
        if p.suffix in (".ts", ".tsx", ".js", ".jsx"):
            ast_fields = _extract_ast_fields(content, p.suffix)
            for model in ast_fields.get("models", []):
                model_name = model["name"]
                field_list = model["fields"]
                models.append(f"- `{model_name}` → **{len(field_list)} fields** ({rel})")
                if field_list:
                    all_fields[model_name] = field_list
        else:
            # Go: regex fallback
            for match in re.finditer(r'(?:type\s+)?(\w+)\s+struct\s*\{', content):
                models.append(f"- `{match.group(1)}` ({rel})")

    # 필드 상세 정보 출력
    if all_fields:
        output += "\n### Field Details\n\n"
        for model_name, fields in all_fields.items():
            output += f"**{model_name}**\n\n"
            for f in fields:
                output += f"- `{f['name']}`: `{f['type']}`\n"
            output += "\n"

    for m in models[:20]:
        output += m + "\n"
    if not models:
        output += "- No data models detected.\n"

    # 형식별 출력
    if format == "mermaid":
        # 동적 Mermaid ERD 생성
        output += "\n## ER Diagram (Mermaid)\n\n```mermaid\nerDiagram\n"
        if all_fields:
            for model_name, fields in all_fields.items():
                output += f"  {model_name} {{\n"
                for f in fields:
                    ftype = f["type"].replace("|", " or ")
                    output += f"    {f['type']} {f['name']}\n"
                output += "  }\n"
        else:
            output += "  User ||--o{ Order : places\n  Order ||--|{ OrderItem : contains\n"
        output += "```\n"
    elif format == "openapi":
        output += "\n## OpenAPI 3.0 Spec\n\n```yaml\nopenapi: 3.0.0\ninfo:\n  title: Auto-detected API\n  version: 0.1.0\npaths: {}\n```\n"

    return output

# ═══════════════════════════════════════════════════════════
# Tester: 테스트 생성 도구
# ═══════════════════════════════════════════════════════════

@mcp.tool
def generate_tests(source_path: str, framework: Optional[str] = None) -> str:
    """지정된 소스 파일에 대한 단위 테스트를 생성합니다.
    
    Args:
        source_path: 테스트 대상 소스 파일 경로
        framework: 테스트 프레임워크 (jest, vitest, pytest, go test). 자동 감지됨.
    """
    root = Path(os.getcwd())
    target = Path(source_path)
    if not target.is_absolute():
        target = root / source_path

    if not target.exists():
        return f"File not found: {source_path}"

    try:
        content = target.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        return f"Cannot read file: {e}"

    ext = target.suffix
    lines = content.split("\n")
    func_count = 0
    for line in lines:
        if re.search(r'(?:export\s+)?(?:function|async function|const\s+\w+\s*=\s*(?:async\s*)?\(|def\s+\w+\s*\()', line):
            func_count += 1

    output = f"# Test Generation: {target.name}\n\n"
    output += f"- **Framework**: {framework or 'auto-detect'}\n"
    output += f"- **Functions detected**: {func_count}\n"
    output += f"- **Lines**: {len(lines)}\n\n"

    if ext in (".ts", ".tsx"):
        output += "## Jest/Vitest Test Structure\n\n"
        output += "```typescript\nimport { describe, it, expect } from 'vitest';\n"
        output += f"import {{ ... }} from './{target.stem}';\n\n"
        output += "describe('', () => {\n  it('should work', () => {\n    // TODO: write test\n  });\n});\n```\n"
    elif ext == ".py":
        output += "## pytest Test Structure\n\n"
        output += "```python\nimport pytest\n\n\ndef test_():\n    \"\"\"TODO: write test\"\"\"\n    pass\n```\n"
    elif ext == ".go":
        output += "## Go Test Structure\n\n"
        output += "```go\npackage main\n\nimport \"testing\"\n\nfunc Test_(t *testing.T) {\n\t// TODO: write test\n}\n```\n"

    return output

@mcp.tool
def analyze_coverage(target_path: Optional[str] = None) -> str:
    """테스트 커버리지를 분석합니다.
    
    Args:
        target_path: 분석 대상 경로
    """
    root = Path(get_project_root(target_path))
    output = "# Coverage Analysis\n\n"

    if (root / "package.json").exists():
        try:
            result = subprocess.run(["npx.cmd" if sys.platform == "win32" else "npx", "vitest", "run", "--coverage", "--reporter=text"],
                                    cwd=str(root), capture_output=True, text=True, timeout=60)
            if result.stdout:
                # Last 30 lines have coverage summary
                lines = result.stdout.strip().split("\n")
                output += "```\n" + "\n".join(lines[-30:]) + "\n```\n"
            else:
                output += "❌ No coverage data available.\n"
        except Exception:
            output += "❌ vitest not available.\n"

    return output

# ═══════════════════════════════════════════════════════════
# Whiteboard: AI-사용자 양방향 드로잉
# ═══════════════════════════════════════════════════════════

@mcp.tool
def draw_on_whiteboard(commands: str) -> str:
    """AI가 화이트보드에 그림을 그립니다. VibeZoo가 이 명령을 받아 Webview에 렌더링합니다.
    
    Args:
        commands: JSON 배열 형태의 Fabric.js 드로잉 명령.
                 각 명령: {"type":"rect|circle|line|text|arrow|freehand|clear", "props":{...}}
    """
    try:
        parsed = json.loads(commands)
        data = {"timestamp": time.time(), "commands": parsed}
        with open(WHITEBOARD_FILE, "w") as f:
            json.dump(data, f, indent=2)
        try_crow_ingest(f"Whiteboard: {len(parsed)} drawing commands", register="context")
        return f"Drew {len(parsed)} shapes on whiteboard. User can now modify and discuss."
    except Exception as e:
        return f"Failed to draw on whiteboard: {e}"

@mcp.tool
def get_whiteboard_state() -> str:
    """현재 화이트보드의 상태를 조회합니다. 사용자가 수정한 내용을 확인합니다."""
    try:
        if os.path.exists(WHITEBOARD_FILE):
            with open(WHITEBOARD_FILE) as f:
                return f.read()
        return '{"commands":[], "timestamp":0}'
    except Exception as e:
        return f"Failed: {e}"

@mcp.tool
def open_whiteboard(message: str = "") -> str:
    """VibeZoo 화이트보드를 엽니다. AI가 시각적 설명이 필요할 때 호출합니다."""
    try:
        data = {"action": "open", "message": message, "timestamp": time.time()}
        with open(WHITEBOARD_FILE.replace(".json", "-action.json"), "w") as f:
            json.dump(data, f)
        return f"Whiteboard opened. {message}"
    except Exception as e:
        return f"Failed: {e}"

@mcp.tool
def open_ui_preview(code: str = "", framework: str = "react") -> str:
    """UI Preview 패널을 열고 코드를 렌더링합니다."""
    try:
        data = {"action": "open_ui", "code": code, "framework": framework, "timestamp": time.time()}
        action_file = os.path.join(os.path.expanduser("~"), ".vibezoo-ui-action.json")
        with open(action_file, "w") as f:
            json.dump(data, f)
        return f"UI Preview opened. Rendering {framework} component."
    except Exception as e:
        return f"Failed: {e}"

# ═══════════════════════════════════════════════════════════
# M1-A: Auto-Fix Loop — MCP 도구
# ═══════════════════════════════════════════════════════════

FIX_REQUEST_FILE = os.path.join(os.path.expanduser("~"), ".vibezoo-fix-request.json")
CHAT_PENDING_FILE = os.path.join(os.path.expanduser("~"), ".vibezoo-chat-pending.json")


@mcp.tool
def auto_fix_status() -> str:
    """현재 진행 중인 Auto-Fix 세션의 상태와 에러 정보를 조회합니다.
    LLM이 빌드 에러를 분석하고 수정을 시작할 때 호출합니다.
    과거 유사 에러 패턴을 Crow Memory에서 조회하여 함께 반환합니다.

    Returns:
        JSON: { status, attempt, maxAttempts, diagnostics, history, pastFixes }
    """
    if not os.path.exists(FIX_REQUEST_FILE):
        return json.dumps({"status": "idle", "message": "No active fix request"})

    try:
        with open(FIX_REQUEST_FILE) as f:
            data = json.load(f)

        # 상태를 in_progress로 변경
        data["status"] = "in_progress"
        data["lastReadAt"] = time.time()
        with open(FIX_REQUEST_FILE, "w") as f:
            json.dump(data, f, indent=2)

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

        return json.dumps(data, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@mcp.tool
def retry_build() -> str:
    """빌드를 재실행하고 결과를 반환합니다.
    LLM이 수정 코드를 적용한 후 빌드 성공 여부를 확인할 때 호출합니다.

    Returns:
        JSON: { exitCode, stdout, stderr, success, diagnostics }
    """
    import subprocess
    import sys

    root = os.getcwd()

    # 프로젝트 타입 감지
    pkg_json = Path(root) / "package.json"
    if pkg_json.exists():
        cmd = ["npx.cmd" if sys.platform == "win32" else "npx", "tsc", "--noEmit"]
    else:
        return json.dumps({
            "exitCode": -1,
            "diagnostics": [],
            "success": False,
            "error": "No build command detected (package.json not found)"
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
                # 새 attempt 추가
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
                with open(FIX_REQUEST_FILE, "w") as f:
                    json.dump(fix_data, f, indent=2)

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
            "stdout": result.stdout[-2000:],
            "stderr": result.stderr[-2000:],
            "success": result.returncode == 0
        }, indent=2, ensure_ascii=False)

    except subprocess.TimeoutExpired:
        return json.dumps({
            "exitCode": -1,
            "success": False,
            "error": "Build timed out after 60s"
        })
    except Exception as e:
        return json.dumps({
            "exitCode": -1,
            "success": False,
            "error": str(e)
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
        "should_pause": False
    }

    # 1. Whiteboard 확인
    if os.path.exists(WHITEBOARD_FILE):
        try:
            with open(WHITEBOARD_FILE) as f:
                wb_data = json.load(f)
            # 텍스트 객체만 추출 (사용자 메모)
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
# Q1: Quick Win — 시나리오 통합 MCP 도구 4개
# ═══════════════════════════════════════════════════════════

def _run_tool(name: str, **kwargs):
    """내부적으로 기존 MCP 도구 함수를 호출하여 결과를 문자열로 반환"""
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
    }
    fn = tools.get(name)
    if not fn:
        return f"Tool not found: {name}"
    sig = inspect.signature(fn)
    filtered = {k: v for k, v in kwargs.items() if k in sig.parameters}
    try:
        result = fn(**filtered)
        return str(result)
    except Exception as e:
        return f"Error in {name}: {e}"


@mcp.tool
def review_project(target_path: str) -> str:
    """search_codebase + review_code + check_quality + extract_patterns 통합.
    프로젝트 전체를 종합 리뷰하여 하나의 마크다운 보고서로 반환합니다.

    Args:
        target_path: 분석 대상 디렉토리 경로
    """
    sections = []
    sections.append("# 📋 Project Review Report\n")
    sections.append(f"> Target: `{target_path}`\n")

    # 1. search_codebase — 주요 패턴 검색
    sections.append("## 🔍 Code Search\n")
    search_result = _run_tool("search_codebase", query="TODO|FIXME|HACK|BUG", max_results=20)
    sections.append(search_result)

    # 2. review_code — 주요 파일 리뷰
    sections.append("## 📝 Code Review\n")
    root = Path(get_project_root(target_path))
    reviewed = 0
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.suffix not in (".ts", ".tsx", ".js", ".jsx", ".py", ".go", ".rs"):
            continue
        if any(part in str(p) for part in [".git", "node_modules", ".zoo-code", "dist", "build", "__pycache__"]):
            continue
        if reviewed >= 5:
            sections.append(f"\n> ... and more files (reviewed top 5 of {sum(1 for _ in root.rglob('*') if _.is_file())} total)\n")
            break
        review = _run_tool("review_code", file_path=str(p))
        sections.append(review)
        reviewed += 1

    # 3. check_quality
    sections.append("## ✅ Quality Check\n")
    quality = _run_tool("check_quality", target_path=target_path)
    sections.append(quality)

    # 4. extract_patterns
    sections.append("## 📊 Pattern Analysis\n")
    patterns = _run_tool("extract_patterns", target_path=target_path, min_occurrences=3)
    sections.append(patterns)

    # M1-C: Crow ingest (register="style") — 리뷰 결과를 코딩 스타일 학습에 저장
    try_crow_ingest(
        json.dumps({
            "action": "review_project",
            "target": target_path,
            "patterns_found": patterns.count("⚠️") + patterns.count("✅"),
            "timestamp": time.time(),
        }),
        register="style"
    )
    return "\n\n---\n\n".join(sections)


@mcp.tool
def find_bugs(target_path: str) -> str:
    """extract_patterns + search_codebase(console.log|debugger|any) + Crow recall 통합.
    프로젝트에서 잠재적 버그를 찾아 마크다운으로 반환합니다.

    Args:
        target_path: 분석 대상 디렉토리 경로
    """
    sections = []
    sections.append("# 🐛 Bug Finder Report\n")
    sections.append(f"> Target: `{target_path}`\n")

    # 1. extract_patterns — 콘솔 로그, TODO 등 패턴 분석
    sections.append("## 📊 Pattern Analysis\n")
    patterns = _run_tool("extract_patterns", target_path=target_path, min_occurrences=1)
    sections.append(patterns)

    # 2. search_codebase — 버그 의심 패턴 검색
    sections.append("## ⚠️ Suspicious Patterns\n")
    for query in ["console.log", "debugger", ".only(", "fit(", "fdescribe", "TODO", "FIXME", "HACK", "XXX", "any", "as any", "@ts-ignore", "@ts-nocheck"]:
        result = _run_tool("search_codebase", query=query, max_results=10)
        if "Found 0 results" not in result:
            sections.append(result)

    # 3. Crow recall — 이전 버그 패턴 회상
    sections.append("## 🧠 Crow Memory Recall\n")
    crow_results = try_crow_recall(query="bug pattern error in project", register="bug", limit=10)
    if crow_results:
        sections.append("### Previous bug patterns from Crow memory:\n")
        for item in crow_results:
            content = item.get("content", item.get("value", str(item)))
            sections.append(f"- {content[:300]}")
    else:
        sections.append("- No relevant bug patterns found in Crow memory.\n")

    # M1-C: Crow ingest (register="bug") — 찾은 버그 패턴을 버그 학습에 저장
    bug_summary = {
        "action": "find_bugs",
        "target": target_path,
        "suspicious_count": len([s for s in sections if "Suspicious" in s]),
        "crow_recall_count": len(crow_results),
        "timestamp": time.time(),
    }
    try_crow_ingest(json.dumps(bug_summary), register="bug")
    return "\n\n---\n\n".join(sections)


@mcp.tool
def suggest_refactor(target_path: str) -> str:
    """map_dependencies + extract_patterns + analyze_call_graph 통합.
    프로젝트의 리팩터링 제안을 마크다운으로 반환합니다.

    Args:
        target_path: 분석 대상 디렉토리 경로
    """
    sections = []
    sections.append("# 🔧 Refactoring Suggestions\n")
    sections.append(f"> Target: `{target_path}`\n")

    # 1. map_dependencies — 의존성 분석 + 순환 참조
    sections.append("## 🔗 Dependency Map\n")
    deps = _run_tool("map_dependencies", target_path=target_path)
    sections.append(deps)

    # 2. extract_patterns — 중복 패턴 찾기
    sections.append("## 📊 Pattern Duplication\n")
    patterns = _run_tool("extract_patterns", target_path=target_path, min_occurrences=5)
    sections.append(patterns)

    # 3. analyze_call_graph — 호출 구조 분석
    sections.append("## 📞 Call Graph\n")
    callgraph = _run_tool("analyze_call_graph", file_path=target_path, depth=3)
    sections.append(callgraph)

    # M1-C: Crow recall (register="style") — 과거 코딩 스타일 규칙 조회
    style_rules = try_crow_recall(query="coding style rules patterns", register="style", limit=5)
    if style_rules:
        sections.append("\n\n## 🎨 Crow Style Rules\n")
        sections.append("### Previous coding style rules from Crow memory:\n")
        for item in style_rules:
            content = item.get("content", item.get("value", str(item)))
            sections.append(f"- {content[:300]}")
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
    return "\n\n---\n\n".join(sections)


@mcp.tool
def generate_docs(target_path: str, format: str = "markdown") -> str:
    """reverse_engineer + summarize_architecture + draw_on_whiteboard(architecture diagram) 통합.
    프로젝트 문서를 자동 생성하고 아키텍처 다이어그램을 화이트보드에 그립니다.
    format='mermaid' 시 ERD 다이어그램을 함께 생성합니다.

    Args:
        target_path: 분석 대상 디렉토리 경로
        format: 출력 형식 (markdown, openapi, mermaid). 기본: markdown
    """
    sections = []
    sections.append("# 📚 Auto-Generated Documentation\n")
    sections.append(f"> Target: `{target_path}`  \n> Format: `{format}`\n")

    # 1. summarize_architecture
    sections.append("## 🏗️ Architecture Summary\n")
    arch = _run_tool("summarize_architecture", target_path=target_path)
    sections.append(arch)

    # 2. reverse_engineer (AST 기반 데이터 모델 필드 포함)
    sections.append("## 🔄 Reverse Engineering\n")
    rev = _run_tool("reverse_engineer", target_path=target_path, format=format)
    sections.append(rev)

    # 3. draw_on_whiteboard — 개선된 아키텍처 다이어그램 (recursive 디렉토리 구조 + 파일 포함)
    sections.append("## 🎨 Architecture Diagram (Whiteboard)\n")
    try:
        root = Path(get_project_root(target_path))
        commands = []
        # 재귀적으로 디렉토리 구조 수집 (depth 2)
        entries = []
        def collect(p, depth=0):
            if depth > 2:
                return
            for child in sorted(p.iterdir()):
                if child.name.startswith(".") or child.name in ("node_modules", "dist", "build", "__pycache__"):
                    continue
                entries.append((child, depth))
                if child.is_dir():
                    collect(child, depth + 1)
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
            draw_result = _run_tool("draw_on_whiteboard", commands=json.dumps(commands))
            sections.append(f"- {draw_result}")
        else:
            sections.append("- No directory structure to visualize.\n")

        # 4. Mermaid ERD 다이어그램 문자열 생성 (format=mermaid)
        if format == "mermaid":
            sections.append("\n## 📊 Mermaid ER Diagram\n\n")
            try:
                # reverse_engineer 결과에서 데이터 모델 파싱
                models_found = []
                for line in rev.split("\n"):
                    m = re.match(r'^- `(\w+)` → \*\*(\d+)\*\* fields', line)
                    if m:
                        models_found.append((m.group(1), int(m.group(2))))

                if models_found:
                    mermaid_lines = ["```mermaid", "erDiagram"]
                    for model_name, field_count in models_found:
                        mermaid_lines.append(f"  {model_name} {{")
                        # 필드 상세 정보 찾기
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
        sections.append(f"- Could not draw diagram: {e}\n")

    try_crow_ingest(f"generate_docs completed for {target_path} (format={format})", register="arch")
    return "\n\n---\n\n".join(sections)


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
    root = Path(os.getcwd())
    target = root / file_path
    if not target.exists():
        return f"File not found: {file_path}"

    try:
        content = target.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        return f"Cannot read file: {e}"

    lines = content.split("\n")
    if line_number < 1 or line_number > len(lines):
        return f"Line {line_number} is out of range (file has {len(lines)} lines)"

    # Extract the line content
    line_content = lines[line_number - 1].strip()
    if not line_content:
        return f"Line {line_number} is empty."

    # Initialize tree-sitter
    _init_tree_sitter()

    output = f"# Code Explanation: `{file_path}:{line_number}`\n\n"
    output += f"> `{line_content}`\n\n"

    ext = target.suffix.lower()
    if ext in (".ts", ".tsx", ".js", ".jsx") and _ts_available:
        ast = _parse_with_tree_sitter(content, ext)

        # Find enclosing function/class/interface
        enclosing_func = None
        enclosing_class = None
        enclosing_iface = None

        for fn in ast.get("functions", []):
            if fn["line"] <= line_number <= fn["end_line"]:
                enclosing_func = fn

        for cls in ast.get("classes", []):
            if cls["line"] <= line_number:
                enclosing_class = cls

        for iface in ast.get("interfaces", []):
            if iface["line"] <= line_number:
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
    output = "# 📊 Git Changes Analysis\n\n"

    try:
        # git diff --stat
        stat_result = subprocess.run(
            ["git", "diff", "--stat"],
            cwd=root, capture_output=True, text=True, timeout=10
        )
        stat_output = stat_result.stdout.strip()

        # git diff (full)
        diff_result = subprocess.run(
            ["git", "diff"],
            cwd=root, capture_output=True, text=True, timeout=10
        )
        diff_output = diff_result.stdout.strip()

        if not stat_output:
            output += "✅ No uncommitted changes detected.\n"
            return output

        # Parse changed files from --stat
        changed_files = []
        for line in stat_output.split("\n"):
            if "|" in line:
                parts = line.split("|")
                file_path = parts[0].strip()
                changed_files.append(file_path)

        output += f"## Changed Files ({len(changed_files)})\n\n"
        for f in changed_files:
            output += f"- `{f}`\n"
        output += "\n"

        # Full diff (truncated)
        output += "## Diff Content\n\n"
        if len(diff_output) > 8000:
            output += f"> Diff is too large ({len(diff_output)} chars), showing first 8000 chars\n\n"
            output += "```diff\n" + diff_output[:8000] + "\n```\n"
            output += f"\n> ... ({len(diff_output) - 8000} more chars)\n"
        else:
            output += "```diff\n" + diff_output + "\n```\n"

        # Crow recall for related context
        if changed_files:
            output += "\n## 🧠 Related Crow Context\n\n"
            for f in changed_files[:5]:  # Top 5 files
                try:
                    file_name = os.path.basename(f)
                    past_context = try_crow_recall(
                        query=f"file changes in {file_name}",
                        register="context",
                        limit=2
                    )
                    if past_context:
                        for item in past_context:
                            content = item.get("content", item.get("value", str(item)))
                            output += f"- `{file_name}`: {content[:200]}\n"
                    else:
                        output += f"- `{file_name}`: No Crow context found.\n"
                except Exception:
                    output += f"- `{file_name}`: Could not query Crow.\n"

    except FileNotFoundError:
        output += "❌ Git not available. Make sure git is installed and this is a git repository.\n"
    except subprocess.TimeoutExpired:
        output += "❌ Git diff timed out.\n"
    except Exception as e:
        output += f"❌ Error: {e}\n"

    try_crow_ingest(f"analyze_changes: {len(changed_files)} files changed", register="life_context")
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
    root = os.getcwd()
    output = "# 🔍 Pull Request Review\n\n"
    output += f"> **Base**: `{base_branch}` → **Head**: `{head_branch or 'current'}`\n\n"

    try:
        # Build diff command
        diff_cmd = ["git", "diff"]
        if head_branch:
            diff_cmd.extend([f"{base_branch}...{head_branch}"])
        else:
            diff_cmd.append(f"{base_branch}..HEAD")

        # Get diff stat
        stat_result = subprocess.run(
            diff_cmd + ["--stat"],
            cwd=root, capture_output=True, text=True, timeout=10
        )
        stat_output = stat_result.stdout.strip()

        # Get full diff
        diff_result = subprocess.run(
            diff_cmd,
            cwd=root, capture_output=True, text=True, timeout=10
        )
        diff_output = diff_result.stdout.strip()

        if not stat_output:
            output += "⚠️ No differences found between branches.\n"
            return output

        # Parse changed files
        changed_files = []
        for line in stat_output.split("\n"):
            if "|" in line:
                parts = line.split("|")
                file_path = parts[0].strip()
                changed_files.append(file_path)

        output += f"## 📂 Changed Files ({len(changed_files)})\n\n"
        for f in changed_files:
            output += f"- `{f}`\n"
        output += "\n"

        # Summary statistics
        total_additions = 0
        total_deletions = 0
        for line in stat_output.split("\n"):
            m = re.search(r'(\d+) insertion', line)
            if m:
                total_additions += int(m.group(1))
            m = re.search(r'(\d+) deletion', line)
            if m:
                total_deletions += int(m.group(1))

        output += f"## 📈 Stats\n\n"
        output += f"- **{len(changed_files)}** files changed\n"
        output += f"- **+{total_additions}** / **-{total_deletions}** lines\n\n"

        # Review each changed file
        output += "## 📝 Code Review per File\n\n"
        for f in changed_files[:10]:  # Limit to 10 files
            output += f"### `{f}`\n\n"
            p = Path(root) / f
            if p.exists():
                review_result = review_code(f)
                for line in review_result.split("\n"):
                    if "⚠️" in line or "📝" in line or "✅" in line or "Found" in line:
                        output += line + "\n"
            else:
                output += "*(file deleted in this PR)*\n"
            output += "\n"

        # Show diff for context
        output += "## 🔍 Diff Preview\n\n"
        if len(diff_output) > 4000:
            output += f"```diff\n{diff_output[:4000]}\n```\n"
            output += f"\n> ... ({len(diff_output) - 4000} more chars)\n"
        else:
            output += f"```diff\n{diff_output}\n```\n"

        # Crow recall for related context
        output += "\n## 🧠 Crow Memory Context\n\n"
        for f in changed_files[:3]:
            file_name = os.path.basename(f)
            past_context = try_crow_recall(query=f"review {file_name}", register="style", limit=2)
            if past_context:
                for item in past_context:
                    content = item.get("content", item.get("value", str(item)))
                    output += f"- `{file_name}`: {content[:200]}\n"
        output += "\n"

    except FileNotFoundError:
        output += "❌ Git not available. Make sure git is installed and this is a git repository.\n"
    except subprocess.TimeoutExpired:
        output += "❌ Git diff timed out.\n"
    except Exception as e:
        output += f"❌ Error: {e}\n"

    try_crow_ingest(
        json.dumps({"action": "review_pr", "base": base_branch, "head": head_branch}),
        register="context"
    )
    return output


# ═══════════════════════════════════════════════════════════
# M3-C: refactor_across_files — 멀티 파일 리팩토링
# ═══════════════════════════════════════════════════════════

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
    output = "# 🔧 Multi-File Refactoring Proposal\n\n"
    output += f"> **Search**: `{pattern}`\n"
    output += f"> **Replace with**: `{new_pattern}`\n"
    output += f"> **File patterns**: `{file_patterns or '*.ts,*.tsx,*.js,*.jsx,*.py'}`\n\n"

    # Search for the pattern
    search_result = search_codebase(query=pattern, file_patterns=file_patterns, max_results=50)

    # Parse search results to extract file:line entries
    occurrences = []
    for line in search_result.split("\n"):
        m = re.match(r'^- `(.+?:\d+):', line)
        if m:
            occurrences.append(m.group(1))
        m2 = re.match(r'^- `(.+?:\d+)`', line)
        if m2:
            occurrences.append(m2.group(1))

    if not occurrences:
        output += "✅ No occurrences found for this pattern.\n"
        return output

    output += f"## Found {len(occurrences)} Occurrences\n\n"

    # Group by file
    from collections import defaultdict
    by_file = defaultdict(list)
    for occ in occurrences:
        parts = occ.split(":")
        if len(parts) >= 2:
            file_path = parts[0]
            line_num = parts[1]
            by_file[file_path].append(line_num)

    output += f"### Files Affected: {len(by_file)}\n\n"
    for file_path, lines in sorted(by_file.items()):
        line_list = ", ".join(lines[:10])
        suffix = f" ... and {len(lines)-10} more" if len(lines) > 10 else ""
        output += f"- `{file_path}` — lines {line_list}{suffix}\n"

    # Generate replacement suggestions
    output += "\n## Suggested Changes\n\n"
    for file_path, lines in sorted(by_file.items())[:10]:  # Limit to 10 files
        actual_path = Path(os.getcwd()) / file_path
        if not actual_path.exists():
            continue
        try:
            content = actual_path.read_text(encoding="utf-8", errors="ignore")
            file_lines = content.split("\n")
        except Exception:
            continue

        output += f"### `{file_path}`\n\n"
        output += f"```diff\n"
        for line_num_str in lines[:5]:  # Show up to 5 changes per file
            idx = int(line_num_str) - 1
            if 0 <= idx < len(file_lines):
                original = file_lines[idx]
                output += f"-{original}\n"
                suggested = original.replace(pattern, new_pattern)
                output += f"+{suggested}\n"
        output += f"```\n\n"

    # Risk analysis
    output += "## ⚠️ Risk Assessment\n\n"
    output += f"- **Scale**: {len(occurrences)} changes across {len(by_file)} files\n"
    output += "- **Pattern type**: text replacement\n"
    output += "- **Recommendation**: Review each change manually before applying\n"
    output += "- **Rollback**: Use YOLO rewind if changes cause issues\n"

    output += "\n> Note: This is a **proposal only**. No files have been modified.\n"
    output += "> To apply changes, use your editor's find-and-replace or manual editing.\n"

    try_crow_ingest(
        json.dumps({
            "action": "refactor_across_files",
            "pattern": pattern,
            "new_pattern": new_pattern,
            "occurrences": len(occurrences),
            "files_affected": len(by_file),
        }),
        register="style"
    )
    return output


# ═══════════════════════════════════════════════════════════
# M3-D: learn_project / recall_project — 프로젝트 지식 Crow 축적
# ═══════════════════════════════════════════════════════════

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
    output = "# 🧠 Project Knowledge Ingestion\n\n"
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

    output = "# 🧠 Project Knowledge Recall\n\n"
    output += f"> Target: `{root}`\n"
    output += f"> Project key: `{project_key}`\n\n"

    # 1. Query arch register
    output += "## 🏗️ Architecture (arch register)\n\n"
    arch_results = try_crow_recall(query=root_str, register="arch", limit=5)
    if arch_results:
        for item in arch_results:
            content = item.get("content", item.get("value", str(item)))
            output += f"- {content[:300]}\n"
    else:
        output += "- No architecture data found in Crow.\n"
        output += "  → Run `learn_project()` first to store project knowledge.\n"

    # 2. Query style register (patterns)
    output += "\n## 📊 Code Patterns (style register)\n\n"
    style_results = try_crow_recall(query=root_str, register="style", limit=5)
    if style_results:
        for item in style_results:
            content = item.get("content", item.get("value", str(item)))
            output += f"- {content[:300]}\n"
    else:
        output += "- No pattern data found in Crow.\n"

    # 3. Query life_context for project identity
    output += "\n## 🔑 Project Identity (life_context)\n\n"
    life_results = try_crow_recall(query=project_key, register="life_context", limit=3)
    if life_results:
        for item in life_results:
            content = item.get("content", item.get("value", str(item)))
            output += f"- {content[:300]}\n"
    else:
        output += "- No project identity found in Crow.\n"

    # 4. Summary
    total = len(arch_results) + len(style_results) + len(life_results)
    output += f"\n---\n**Total {total} knowledge items recalled from Crow.**\n"

    return output


# ═══════════════════════════════════════════════════════════
# M3-E: learn_preference / get_preferences — 사용자 선호도 학습
# ═══════════════════════════════════════════════════════════

PREFERENCES_FILE = os.path.join(os.path.expanduser("~"), ".vibezoo-preferences.json")


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
        with open(PREFERENCES_FILE, "w") as f:
            json.dump(prefs, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

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

    return f"✅ Preference saved: [{category}] {rule}\n\nStored in local preferences file and Crow Memory (life_context)."


@mcp.tool
def get_preferences(category: Optional[str] = None) -> str:
    """저장된 모든 사용자 선호도/규칙을 조회합니다.

    Args:
        category: 특정 카테고리만 조회 (생략 시 전체)

    Returns:
        Markdown 형식의 저장된 선호도 목록
    """
    output = "# 🎨 User Preferences\n\n"

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
            output += f"- {content[:200]}\n"
    else:
        output += "- No preference data in Crow.\n"

    return output


# ═══════════════════════════════════════════════════════════
# 메인 — SSE 서버 시작
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VibeZoo MCP Bridge Server")
    parser.add_argument("--port", type=int, default=9027, help="SSE server port")
    args = parser.parse_args()

    print(f"🚀 VibeZoo MCP Bridge starting on port {args.port}...")
    print(f"   Crow Memory: {CROW_URL}")

    mcp.run(transport="sse", host="127.0.0.1", port=args.port)
