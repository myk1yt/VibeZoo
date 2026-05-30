#!/usr/bin/env python
# VibeZoo MCP Bridge에 fetch_page 웹 검색 도구 추가
# 사용법: python mcp-servers/add_web_tools.py

import os, sys, shutil

ROOT = r'c:/Users/k1yt/OneDrive/문서/각종자료/공부자료들/파이썬_Python/VibeZoo_forZoocode'
BRIDGE = os.path.join(ROOT, 'mcp-servers', 'vibezoo_mcp_bridge.py')

WEB_TOOLS_CODE = r'''


# ═══════════════════════════════════════════════════════════
# Web Tools: fetch_page — URL/웹 검색 도구
# ═══════════════════════════════════════════════════════════

import urllib.request
import urllib.parse
import re as _re

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
                if self.in_skip: return
                
                attrs_dict = dict(attrs)
                
                if tag in ('h1','h2','h3','h4','h5','h6'):
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
                if self.in_skip: return
                
                if self.in_h:
                    self.output.append('\n')
                    self.in_h = 0
                elif tag == 'li':
                    self.in_li = False
                elif tag in ('ul', 'ol'):
                    self.list_depth = max(0, self.list_depth - 1)
                    if self.list_depth == 0:
                        pass
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
                if self.in_skip: return
                if self.in_pre:
                    self.output.append(data)
                else:
                    # Clean whitespace
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
        result = _re.sub(r'\n{4,}', '\n\n\n', result)
        result = _re.sub(r' {3,}', ' ', result)
        
        # Truncate
        if len(result) > max_length:
            result = result[:max_length] + f'\n\n... [truncated {len(result) - max_length} more chars]'
        
        return result.strip()
    except Exception as e:
        # Fallback: basic strip
        return _re.sub(r'<[^>]+>', ' ', html).strip()[:max_length]


@mcp.tool
def fetch_page(url: str, max_length: int = 50000) -> str:
    """웹 페이지를 가져와서 마크다운으로 변환합니다.
    외부 API나 라이브러리 없이 순수 Python 표준 라이브러리만으로 동작합니다.
    
    Args:
        url: 가져올 웹 페이지 URL (http:// 또는 https://)
        max_length: 최대 결과 길이 (기본: 50000 문자)
    
    Returns:
        HTML을 깔끔한 마크다운으로 변환한 내용
    """
    err = _validate_string(url, "url")
    if err:
        return _markdown_header("Fetch Error", "❌") + f"**{err}**\\n" + _markdown_footer()
    
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
            }
        )
        
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8', errors='replace')
            content_type = response.headers.get('Content-Type', '')
        
        if 'application/json' in content_type or url.endswith('.json'):
            # JSON 응답
            try:
                import json as _json
                parsed = _json.loads(html)
                result = _json.dumps(parsed, indent=2, ensure_ascii=False)
                if len(result) > max_length:
                    result = result[:max_length] + f'\\n\\n... [truncated]'
                return _markdown_header(f"JSON: {url}") + f"```json\\n{result}\\n```\\n" + _markdown_footer()
            except:
                pass
        
        markdown = _html_to_markdown(html, max_length)
        
        output = _markdown_header(f"Fetch: {url}")
        output += f"**Source**: {url}\\n\\n"
        output += markdown
        output += _markdown_footer()
        
        return output
        
    except urllib.error.HTTPError as e:
        return (_markdown_header("Fetch Error", "❌")
                + f"**HTTP {e.code}**: {e.reason} for `{url}`\\n"
                + _markdown_footer())
    except urllib.error.URLError as e:
        return (_markdown_header("Fetch Error", "❌")
                + f"**Connection failed**: {e.reason}\\n"
                + _markdown_footer())
    except Exception as e:
        return (_markdown_header("Fetch Error", "❌")
                + f"**Error**: {e}\\n"
                + _markdown_footer())


@mcp.tool
def web_search(query: str, max_results: int = 5) -> str:
    """웹 검색을 수행합니다. Google 검색 결과를 가져와서 요약합니다.
    
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
        search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&num={min(max_results, 10)}"
        content = fetch_page(search_url, max_length=30000)
        
        # Extract search results from markdown
        output = _markdown_header(f"Web Search: {query}")
        output += content
        output += _markdown_footer()
        
        try_crow_ingest(f"Web search: {query}", register="life_context")
        return output
        
    except Exception as e:
        return (_markdown_header("Search Error", "❌")
                + f"**Search failed**: {e}\\n"
                + _markdown_footer())
'''

print(f"📖 Reading current bridge...")
with open(BRIDGE, 'r', encoding='utf-8') as f:
    content = f.read()
print(f"   Current: {len(content)} chars, {content.count(chr(10)) + 1} lines")

# Add web tools before the main block
main_marker = '# ═══════════════════════════════════════════════════════════\n# 메인 — SSE 서버 시작'
if main_marker in content:
    content = content.replace(main_marker, WEB_TOOLS_CODE + '\n\n' + main_marker)
    print("✅ Web tools code inserted")
else:
    print("❌ Main marker not found!")
    # Fallback: add at the very end
    content += WEB_TOOLS_CODE
    print("✅ Web tools code appended at end")

# Verify syntax
try:
    compile(content, BRIDGE, 'exec')
    print("✅ Syntax: OK")
except SyntaxError as e:
    print(f"❌ Syntax error: {e}")
    # Try to fix common issues
    print("   Attempting syntax repair...")
    sys.exit(1)

# Atomic write using the known working approach
print(f"\n📝 Writing {len(content)} chars...")
# Step 1: write_to_file already broke the monitoring cycle
# Step 2: Now do atomic write
tmp = BRIDGE + '.webtmp'
try:
    with open(tmp, 'w', encoding='utf-8') as f:
        f.write(content)
    os.replace(tmp, BRIDGE)
    print("✅ Write complete!")
except Exception as e:
    print(f"❌ Write failed: {e}")
    sys.exit(1)

# Verify
with open(BRIDGE, 'r', encoding='utf-8') as f:
    final = f.read()
print(f"📊 Final: {len(final)} chars, {final.count(chr(10)) + 1} lines")
print(f"   Has fetch_page: {'fetch_page' in final}")
print(f"   Has web_search: {'web_search' in final}")
print(f"   Has _html_to_markdown: {'_html_to_markdown' in final}")
print("\n✅ Web tools added successfully!")
print("   Bridge restart required to activate.")
