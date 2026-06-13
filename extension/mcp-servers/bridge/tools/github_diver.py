import urllib.request
import urllib.error
import json
import os

def _get_headers():
    headers = {"User-Agent": "VibeZoo-DeepDiver/1.0", "Accept": "application/vnd.github.v3+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
    return headers

def _make_request(url: str):
    req = urllib.request.Request(url, headers=_get_headers())
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        if e.code == 403:
            return {"error": f"GitHub API Rate limit exceeded. (Code 403). Consider setting GITHUB_TOKEN environment variable. Details: {e.read().decode('utf-8')}"}
        elif e.code == 404:
            return {"error": "Not found. The repository or file might not exist."}
        return {"error": f"HTTP Error {e.code}: {e.reason}"}
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}

def _search(query: str, limit: int = 5) -> str:
    """GitHub에서 키워드로 오픈소스 리포지토리를 검색합니다. (별점, 설명, 풀네임 반환)
    
    Args:
        query: 검색어 (예: 'fastapi websocket chat')
        limit: 반환할 리포지토리 최대 개수 (기본 5)
    """
    url = f"https://api.github.com/search/repositories?q={urllib.parse.quote(query)}&sort=stars&order=desc&per_page={limit}"
    data = _make_request(url)
    
    if "error" in data:
        return data["error"]
        
    items = data.get("items", [])
    if not items:
        return f"No repositories found for query: '{query}'"
        
    result = [f"🔍 GitHub Search Results for '{query}':\n"]
    for i, item in enumerate(items, 1):
        result.append(f"{i}. **{item.get('full_name')}** (⭐ {item.get('stargazers_count')})")
        result.append(f"   - Description: {item.get('description')}")
        result.append(f"   - URL: {item.get('html_url')}")
        result.append(f"   - Language: {item.get('language')}")
        result.append("")
        
    result.append("\n💡 Tip: Use `github_explore_repository(repo_name)` to view its file structure.")
    return "\n".join(result)

def _explore(repo_name: str) -> str:
    """특정 리포지토리의 핵심 폴더/파일 트리(뼈대) 구조를 스캔합니다.
    
    Args:
        repo_name: 리포지토리 풀네임 (예: 'tiangolo/fastapi')
    """
    # 기본 브랜치의 최상단 트리를 가져온 후, 하위 핵심 디렉토리를 재귀 스캔하는 방식 (단순화)
    # 여기서는 GitHub Tree API (recursive=1)를 활용
    url = f"https://api.github.com/repos/{repo_name}/git/trees/HEAD?recursive=1"
    data = _make_request(url)
    
    if "error" in data:
        return data["error"]
        
    tree = data.get("tree", [])
    if not tree:
        return "Empty repository or cannot read tree."
        
    # 핵심 폴더 필터링 룰
    important_dirs = ("src/", "lib/", "core/", "app/", "pkg/")
    important_files = ("readme", "package.json", "requirements.txt", "main.py", "index.js", "setup.py", "go.mod", "cargo.toml")
    
    filtered_paths = []
    for item in tree:
        path = item.get("path", "")
        # 폴더는 생략하고 파일만 기록하되, 핵심 경로에 있거나 핵심 파일인 경우만 기록
        if item.get("type") == "blob":
            path_lower = path.lower()
            if path_lower.startswith(important_dirs) or path_lower.split("/")[-1] in important_files:
                filtered_paths.append(path)
                
    # 만약 필터링된 게 너무 없으면 루트 레벨 파일들을 추가
    if len(filtered_paths) < 5:
        for item in tree:
            path = item.get("path", "")
            if item.get("type") == "blob" and "/" not in path:
                if path not in filtered_paths:
                    filtered_paths.append(path)
                    
    # 결과가 너무 길면 자름
    if len(filtered_paths) > 100:
        filtered_paths = filtered_paths[:100] + [f"... and {len(filtered_paths) - 100} more core files"]
        
    result = [f"📂 Core Structure of `{repo_name}`:\n"]
    for path in filtered_paths:
        result.append(f"  - {path}")
        
    result.append("\n💡 Tip: Use `github_read_file(repo_name, file_path)` to extract the code.")
    return "\n".join(result)

def _read(repo_name: str, file_path: str) -> str:
    """GitHub 리포지토리에서 특정 파일의 소스코드를 그대로 읽어옵니다.
    
    Args:
        repo_name: 리포지토리 풀네임 (예: 'tiangolo/fastapi')
        file_path: 파일 경로 (예: 'fastapi/applications.py')
    """
    url = f"https://raw.githubusercontent.com/{repo_name}/HEAD/{urllib.parse.quote(file_path)}"
    
    req = urllib.request.Request(url, headers={"User-Agent": "VibeZoo-DeepDiver"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"token {token}")
        
    try:
        with urllib.request.urlopen(req) as response:
            content = response.read().decode('utf-8')
            return f"📄 File: `{repo_name}/{file_path}`\n\n```\n{content}\n```"
    except urllib.error.HTTPError as e:
        if e.code == 404:
            # HEAD를 찾을 수 없는 경우 master나 main으로 시도
            for branch in ["main", "master"]:
                url = f"https://raw.githubusercontent.com/{repo_name}/{branch}/{urllib.parse.quote(file_path)}"
                req = urllib.request.Request(url, headers={"User-Agent": "VibeZoo-DeepDiver"})
                if token: req.add_header("Authorization", f"token {token}")
                try:
                    with urllib.request.urlopen(req) as response:
                        content = response.read().decode('utf-8')
                        return f"📄 File: `{repo_name}/{file_path}` (Branch: {branch})\n\n```\n{content}\n```"
                except:
                    continue
            return f"❌ Failed to read {file_path}. It might not exist in HEAD, main, or master branch."
        return f"❌ HTTP Error {e.code}: {e.reason}"
    except Exception as e:
        return f"❌ Failed to read file: {str(e)}"


def explore_github(query: str = "", repo: str = "", file_path: str = "") -> str:
    """GitHub 통합 탐색 도구. 단 하나로 검색, 구조 스캔, 코드 추출을 모두 수행합니다.
    
    사용 예시:
    1. 리포지토리 검색: query="fastapi websocket" (repo, file_path는 비움)
    2. 레포 구조 스캔: repo="tiangolo/fastapi" (query, file_path는 비움)
    3. 특정 파일 읽기: repo="tiangolo/fastapi", file_path="src/main.py"
    """
    if repo and file_path:
        return _read(repo, file_path)
    elif repo:
        return _explore(repo)
    elif query:
        return _search(query, limit=5)
    else:
        return "❌ Error: You must provide either 'query', 'repo', or both 'repo' and 'file_path'."

def register(mcp):
    mcp.tool()(explore_github)
