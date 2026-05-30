#!/usr/bin/env python
# Replace web_search function with DuckDuckGo version
import os, re

BRIDGE = r'c:/Users/k1yt/OneDrive/문서/각종자료/공부자료들/파이썬_Python/VibeZoo_forZoocode/mcp-servers/vibezoo_mcp_bridge.py'

# Read bridge
with open(BRIDGE, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the old web_search function
old_start = content.find('@mcp.tool\ndef web_search(query')
old_end = content.find('\n\n# ═══════════════════════════════════════════════════════════\n# 메인 — SSE 서버 시작')

if old_start == -1 or old_end == -1:
    print("ERROR: Could not find web_search function boundaries")
    print(f"old_start: {old_start}, old_end: {old_end}")
    exit(1)

# The new web_search function (user's DuckDuckGo version)
new_func = '''@mcp.tool
def web_search(query: str, max_results: int = 5) -> str:
    """웹 검색을 수행합니다. 차단이 적은 DuckDuckGo HTML 엔진을 사용해 
    노이즈 없이 정제된 결과만 딥시크에게 피딩합니다.
    
    Args:
        query: 검색어
        max_results: 최대 결과 수 (기본: 5)
    
    Returns:
        검색 결과 목록 (제목, URL, 요약)
    """
    err = _validate_string(query, "query")
    if err:
        return _markdown_header("Search Error", "❌") + f"**{err}**\\n" + _markdown_footer()
    
    try:
        # 1. 구글 대신 차단이 없고 가벼운 DuckDuckGo HTML 엔드포인트 타겟팅
        encoded_query = urllib.parse.quote(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
        
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml',
                'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8'
            }
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='replace')
        
        # 2. 정규표현식을 이용해 무거운 HTML 전체 변환을 피하고 검색 결과 블록만 정밀 타격
        results = []
        blocks = _re.findall(r'<div class="result__body">.*?</div>\\s*</div>', html, _re.DOTALL)
        
        for block in blocks[:max_results]:
            title_match = _re.search(r'<a class="result__url"[^>]*>(.*?)</a>', block, _re.DOTALL)
            href_match = _re.search(r'href="([^"]+)"', block)
            snippet_match = _re.search(r'<a class="result__snippet"[^>]*>(.*?)</a>', block, _re.DOTALL)
            
            if title_match and href_match:
                title = _re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
                raw_href = href_match.group(1)
                
                if '/l/?kh=' in raw_href:
                    parsed_url = urllib.parse.parse_qs(urllib.parse.urlparse(raw_href).query)
                    href = parsed_url.get('uddg', [raw_href])[0]
                else:
                    href = raw_href
                    
                snippet = _re.sub(r'<[^>]+>', '', snippet_match.group(1)).strip() if snippet_match else "No description available."
                
                results.append(f"### \\ud83d\\udd17 [{title}]({href})\\n- **URL**: {href}\\n- **Summary**: {snippet}\\n")
        
        if not results:
            return _markdown_header(f"Search: {query}", "\\u26a0\\ufe0f") + "검색 결과를 파싱하지 못했거나 차단되었습니다. 쿼리를 단순화해보세요.\\n" + _markdown_footer()
        
        output = _markdown_header(f"Search Results: {query}", "\\U0001f310")
        output += f"**Query**: `{query}`\\n\\n"
        output += "\\n".join(results)
        output += _markdown_footer()
        
        try_crow_ingest(f"Web search success: {query}", register="life_context")
        return output
        
    except Exception as e:
        return (_markdown_header("Search Error", "❌")
                + f"**Search failed due to system/network level block**: {e}\\n"
                + _markdown_footer())'''

# Replace
new_content = content[:old_start] + new_func + content[old_end:]

# Verify
if 'web_search' not in new_content:
    print("ERROR: web_search missing after replacement")
    exit(1)

# Check syntax
try:
    compile(new_content, BRIDGE, 'exec')
    print("✅ Syntax OK")
except SyntaxError as e:
    print(f"❌ Syntax error: {e}")
    exit(1)

# Atomic write
tmp = BRIDGE + '.ws_tmp'
with open(tmp, 'w', encoding='utf-8') as f:
    f.write(new_content)
os.replace(tmp, BRIDGE)
print(f"✅ Written: {len(new_content)} chars, {new_content.count(chr(10)) + 1} lines")
print("✅ web_search replaced with DuckDuckGo version!")

# Verify
with open(BRIDGE, 'r', encoding='utf-8') as f:
    final = f.read()
print(f"   DuckDuckGo in file: {'duckduckgo' in final.lower()}")
