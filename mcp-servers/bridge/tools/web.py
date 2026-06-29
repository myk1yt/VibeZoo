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

    def _get_api_key(self) -> str:
        api_key = os.environ.get("EXA_API_KEY", "")
        if not api_key:
            try:
                import keyring
                api_key = keyring.get_password("VibeZoo", "EXA_API_KEY")
            except ImportError:
                pass
        return api_key or ""

    def search(self, query: str, max_results: int = 5,
               preferred_engine: str = "exa") -> list:
        """Exa API를 사용한 웹 검색.

        Args:
            query: 검색어
            max_results: 최대 결과 수
            preferred_engine: 하위 호환성을 위해 유지되나, 실제로는 exa 고정

        Returns:
            검색 결과 목록 (실패 시 빈 리스트)
        """
        api_key = self._get_api_key()
        if not api_key:
            return []

        try:
            url = "https://api.exa.ai/search"
            payload = {
                "query": query,
                "numResults": min(max_results, 10),
                "contents": {
                    "highlights": True
                }
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={
                    "x-api-key": api_key,
                    "Content-Type": "application/json"
                }
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))

            results = []
            for item in data.get("results", []):
                title = item.get("title", "")
                page_url = item.get("url", "")
                highlights = item.get("highlights", [])
                snippet = " ... ".join(highlights) if highlights else "No description available."

                results.append({
                    "title": title,
                    "url": page_url,
                    "snippet": snippet,
                })
            return results
        except Exception:
            return []


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
        """웹 검색을 수행합니다. Exa API 기반 (하위 호환 engine 파라미터 유지).

        Args:
            query: 검색어
            max_results: 최대 결과 수 (기본: 5)
            engine: 하위 호환성을 위해 유지되나, 실제로는 exa 엔진 사용

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
                    + "**검색 결과를 가져오지 못했습니다.**\n\n"
                    + "- Exa API 키가 없거나 만료되었을 수 있습니다.\n"
                    + "- 환경변수 `EXA_API_KEY`를 설정하거나 Python의 `keyring` 패키지를 통해 'VibeZoo' 서비스, 'EXA_API_KEY' 사용자 이름으로 키를 저장하세요.\n"
                    + _markdown_footer())

        output = _markdown_header(f"Search Results: {query}", "🌐")
        output += f"**Query**: `{query}`\n"
        output += f"**Engine**: `exa`\n\n"
        for r in results:
            output += f"### 🔗 [{r['title']}]({r['url']})\n"
            output += f"- **URL**: {r['url']}\n"
            output += f"- **Summary**: {r['snippet']}\n\n"

        try_crow_ingest(f"Web search success: {query} (engine={engine})", register="life_context")
        output += _markdown_footer()
        return output
