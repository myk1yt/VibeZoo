# VibeZoo Bridge — Web 도구 그룹
# fetch_page + web_search

import json
import os
import re as _re
import urllib.error
import urllib.parse
import urllib.request
from typing import Optional

from bridge.config import VERSION
from bridge.utils import (
    _markdown_header, _markdown_footer,
    _validate_string, _truncate,
    _html_to_markdown,
)
from bridge.crow_client import try_crow_ingest


class WebSearchEngine:
    """다중 검색 엔진 폴백 체인 — DuckDuckGo 우선"""

    ENGINES = ["duckduckgo", "google", "bing"]

    def search(self, query: str, max_results: int = 5,
               preferred_engine: str = "auto") -> list:
        """검색 엔진 폴백 체인"""
        return self._search_duckduckgo(query, max_results)

    def _search_duckduckgo(self, query: str, max_results: int) -> list:
        """DuckDuckGo HTML 검색"""
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

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read().decode('utf-8', errors='replace')
        except Exception:
            return []

        results = []
        blocks = _re.findall(r'<div class="result__body">.*?</div>\s*</div>', html, _re.DOTALL)

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

                results.append({
                    "title": title,
                    "url": href,
                    "snippet": snippet,
                })

        return results


def register(mcp):
    """Web 도구 등록"""

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
            return _markdown_header("Fetch Error", "❌") + f"**{err}**\n" + _markdown_footer()

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
                try:
                    import json as _json
                    parsed = _json.loads(html)
                    result = _json.dumps(parsed, indent=2, ensure_ascii=False)
                    if len(result) > max_length:
                        result = result[:max_length] + f'\n\n... [truncated]'
                    return _markdown_header(f"JSON: {url}") + f"```json\n{result}\n```\n" + _markdown_footer()
                except Exception:
                    pass

            markdown = _html_to_markdown(html, max_length)

            output = _markdown_header(f"Fetch: {url}")
            output += f"**Source**: {url}\n\n"
            output += markdown
            output += _markdown_footer()

            return output

        except urllib.error.HTTPError as e:
            return (_markdown_header("Fetch Error", "❌")
                    + f"**HTTP {e.code}**: {e.reason} for `{url}`\n"
                    + _markdown_footer())
        except urllib.error.URLError as e:
            return (_markdown_header("Fetch Error", "❌")
                    + f"**Connection failed**: {e.reason}\n"
                    + _markdown_footer())
        except Exception as e:
            return (_markdown_header("Fetch Error", "❌")
                    + f"**Error**: {e}\n"
                    + _markdown_footer())

    @mcp.tool
    def web_search(query: str, max_results: int = 5, engine: str = "auto") -> str:
        """웹 검색을 수행합니다. 차단이 적은 DuckDuckGo HTML 엔진을 사용해
        노이즈 없이 정제된 결과만 반환합니다.

        Args:
            query: 검색어
            max_results: 최대 결과 수 (기본: 5)
            engine: 검색 엔진 ("auto", "duckduckgo", "google", "bing"). 기본: "auto"

        Returns:
            검색 결과 목록 (제목, URL, 요약)
        """
        err = _validate_string(query, "query")
        if err:
            return _markdown_header("Search Error", "❌") + f"**{err}**\n" + _markdown_footer()

        web_engine = WebSearchEngine()
        results = web_engine.search(query, max_results, engine)

        if not results:
            return (_markdown_header(f"Search: {query}", "⚠️")
                    + "검색 결과를 가져오지 못했습니다. 쿼리를 단순화해보세요.\n"
                    + _markdown_footer())

        output = _markdown_header(f"Search Results: {query}", "🌐")
        output += f"**Query**: `{query}`\n\n"
        for r in results:
            output += f"### 🔗 [{r['title']}]({r['url']})\n"
            output += f"- **URL**: {r['url']}\n"
            output += f"- **Summary**: {r['snippet']}\n\n"

        try_crow_ingest(f"Web search success: {query}", register="life_context")
        output += _markdown_footer()
        return output
