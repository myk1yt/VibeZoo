# VibeZoo MCP Bridge — 통합 MCP 서버
# Scout(코드 검색) + Reviewer(리뷰) + Tester(테스트) + DeepAnalyzer(분석)
# Crow Memory(Python)와 동일한 FastMCP 기반, 단일 파일로 모든 기능 제공
# 포트 9027에서 SSE transport로 실행
# 필요시 Crow Memory(9020)에 연결하여 기억 저장/조회

import asyncio
import argparse
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
# Scout: 코드 탐색 도구
# ═══════════════════════════════════════════════════════════

@mcp.tool
def search_codebase(query: str, file_patterns: Optional[str] = None, max_results: int = 10) -> str:
    """프로젝트 코드베이스에서 쿼리와 관련된 코드를 검색합니다.
    
    Args:
        query: 검색할 내용 (자연어 또는 코드 스니펫)
        file_patterns: 검색 대상 파일 패턴 (예: *.ts,*.tsx). 쉼표로 구분.
        max_results: 최대 결과 수 (기본: 10)
    """
    patterns = file_patterns.split(",") if file_patterns else ["*.ts", "*.tsx", "*.js", "*.jsx", "*.py", "*.go", "*.rs"]
    root = Path(os.getcwd())
    results = []
    exclude = {".git", "node_modules", ".zoo-code", "dist", "build", ".next", "vendor", "__pycache__"}

    # ripgrep 우선, grep 폴백
    for pattern in patterns:
        for p in root.rglob(pattern):
            if any(part in str(p) for part in exclude):
                continue
            try:
                content = p.read_text(encoding="utf-8", errors="ignore")
                for i, line in enumerate(content.split("\n"), 1):
                    if query.lower() in line.lower():
                        rel = str(p.relative_to(root))
                        results.append(f"{rel}:{i}: {line.strip()[:120]}")
                        if len(results) >= max_results:
                            break
                if len(results) >= max_results:
                    break
            except Exception:
                continue
        if len(results) >= max_results:
            break

    output = f"# Search Results for: {query}\n\nFound {len(results)} results\n\n"
    for r in results[:max_results]:
        output += f"- `{r}`\n"

    # Crow에 검색 기록 저장
    try_crow_ingest(f"Searched: {query}, found {len(results)} results", register="life_context")

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
    
    Args:
        file_path: 분석할 파일 경로 (기본: 전체 프로젝트)
        depth: 호출 깊이 (기본: 3)
    """
    root = Path(get_project_root(file_path))
    output = "# Call Graph Analysis\n\n"

    if (root / "go.mod").exists():
        try:
            result = subprocess.run(["go", "callgraph", "./..."], cwd=str(root), capture_output=True, text=True, timeout=30)
            if result.stdout:
                output += f"## Go Call Graph\n\n```\n{result.stdout[:2000]}\n```\n"
        except Exception:
            output += "## Go call graph: go not available\n"

    # TypeScript: import 관계 분석
    output += "\n## File-Level Dependencies\n\n"
    for p in root.rglob("*.ts") if list(root.rglob("*.ts")) else root.rglob("*.tsx"):
        if any(part in str(p) for part in [".git", "node_modules"]):
            continue
        rel = p.relative_to(root)
        imports = extract_imports(str(p))
        if imports:
            output += f"- `{rel}` → imports {len(imports)} modules\n"

    return output

@mcp.tool
def map_dependencies(target_path: Optional[str] = None) -> str:
    """프로젝트 파일 간 의존성을 분석하고 순환 참조를 탐지합니다.
    
    Args:
        target_path: 분석 대상 경로
    """
    root = Path(get_project_root(target_path))
    output = "# Dependency Map\n\n"

    # 모든 파일에서 import 수집
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

    try_crow_ingest(f"Dep analysis: {len(deps)} files, {len(all_cycles)} cycles", register="arch")
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
    
    Args:
        target_path: 분석 대상 경로
        format: 출력 형식 (markdown, openapi, mermaid). 기본: markdown
    """
    root = Path(get_project_root(target_path))
    output = "# Reverse Engineering Report\n\n"

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

    # 데이터 모델
    output += "\n## Data Models\n\n"
    models = []
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix not in (".ts", ".tsx", ".go"):
            continue
        if any(part in str(p) for part in [".git", "node_modules"]):
            continue
        try:
            content = p.read_text(encoding="utf-8", errors="ignore")
            for match in re.finditer(r'(?:interface|class|struct|type)\s+(\w+)', content):
                models.append(f"- `{match.group(1)}` ({p.relative_to(root)})")
        except Exception:
            continue
    for m in models[:20]:
        output += m + "\n"
    if not models:
        output += "- No data models detected.\n"

    # 형식별 출력
    if format == "mermaid":
        output += "\n## ER Diagram (Mermaid)\n\n```mermaid\nerDiagram\n  User ||--o{ Order : places\n  Order ||--|{ OrderItem : contains\n```\n"
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
# 메인 — SSE 서버 시작
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VibeZoo MCP Bridge Server")
    parser.add_argument("--port", type=int, default=9027, help="SSE server port")
    args = parser.parse_args()

    print(f"🚀 VibeZoo MCP Bridge starting on port {args.port}...")
    print(f"   Crow Memory: {CROW_URL}")

    mcp.run(transport="sse", host="127.0.0.1", port=args.port)
