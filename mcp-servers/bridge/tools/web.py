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
    """다중 검색 엔진 폴백 체인 — DuckDuckGo 우선, SearXNG 차선, Google/Bing API 키"""

    ENGINES = ["auto", "duckduckgo", "searxng", "google", "bing"]
    SEARXNG_INSTANCES = [
        "https://searx.be",
        "https://search.sapti.me",
        "https://search.nerdvpn.de",
        "https://search.mdosch.de",
        "https://searx.work",
    ]

    def search(self, query: str, max_results: int = 5,
               preferred_engine: str = "auto") -> list:
        """검색 엔진 폴백 체인 — 첫 번째 엔진에 3초, 실패 시 나머지 병렬 2초.

        Args:
            query: 검색어
            max_results: 최대 결과 수
            preferred_engine: "auto" | "duckduckgo" | "searxng" | "google" | "bing"

        Returns:
            검색 결과 목록 (실패 시 빈 리스트)
        """
        if preferred_engine == "auto" or preferred_engine == "duckduckgo":
            results = self._search_duckduckgo(query, max_results)
            if results:
                return results
        elif preferred_engine == "searxng":
            results = self._search_searxng(query, max_results)
            if results:
                return results
        elif preferred_engine == "google":
            return self._search_google_api(query, max_results)
        elif preferred_engine == "bing":
            return self._search_bing_api(query, max_results)

        # ── 병렬 fallback ──
        return self._parallel_search(query, max_results)

    def _parallel_search(self, query: str, max_results: int) -> list:
        """나머지 엔진을 병렬로 동시 호출, 가장 빠른 결과 사용.

        먼저 DuckDuckGo에 3초 timeout 시도, 실패 시 SearXNG/Google/Bing을 병렬 2초 timeout.
        """
        # 1. DuckDuckGo (먼저 시도, 3초)
        try:
            results = self._search_duckduckgo(query, max_results)
            if results:
                return results
        except Exception:
            pass

        # 2. 나머지 엔진 병렬 (2초 timeout)
        import concurrent.futures

        def _safe_search(engine_name: str, *args, **kwargs) -> list:
            try:
                return args[0](*args[1:], **kwargs) if len(args) > 0 else []
            except Exception:
                return []

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            future_map = {}

            # SearXNG
            if True:
                future = pool.submit(self._search_searxng, query, max_results)
                future_map[future] = "searxng"

            # Google (키 있으면)
            if os.environ.get("GOOGLE_API_KEY"):
                future = pool.submit(self._search_google_api, query, max_results)
                future_map[future] = "google"

            # Bing (키 있으면)
            if os.environ.get("BING_API_KEY"):
                future = pool.submit(self._search_bing_api, query, max_results)
                future_map[future] = "bing"

            if not future_map:
                return []

            try:
                for future in concurrent.futures.as_completed(future_map, timeout=2):
                    try:
                        result = future.result()
                        if result:
                            return result
                    except Exception:
                        continue
            except concurrent.futures.TimeoutError:
                pass

        return []

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

    def _search_searxng(self, query: str, max_results: int) -> list:
        """SearXNG 공개 인스턴스 검색"""
        for instance in self.SEARXNG_INSTANCES:
            try:
                search_url = f"{instance}/search"
                data = urllib.parse.urlencode({"q": query, "format": "json", "language": "ko-KR"}).encode()
                req = urllib.request.Request(
                    search_url,
                    data=data,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Accept': 'application/json',
                        'Content-Type': 'application/x-www-form-urlencoded',
                    }
                )
                with urllib.request.urlopen(req, timeout=8) as response:
                    json_data = json.loads(response.read().decode('utf-8', errors='replace'))

                results = []
                for r in json_data.get("results", [])[:max_results]:
                    results.append({
                        "title": r.get("title", "No title"),
                        "url": r.get("url", ""),
                        "snippet": r.get("content", r.get("snippet", "No description available.")),
                    })
                if results:
                    return results
            except Exception:
                continue
        return []

    def _search_google_api(self, query: str, max_results: int) -> list:
        """Google Custom Search API 검색 (환경변수: GOOGLE_API_KEY, GOOGLE_CX)"""
        api_key = os.environ.get("GOOGLE_API_KEY", "")
        cx = os.environ.get("GOOGLE_CX", "")
        if not api_key or not cx:
            return []

        try:
            params = urllib.parse.urlencode({
                "key": api_key,
                "cx": cx,
                "q": query,
                "num": min(max_results, 10),
            })
            url = f"https://www.googleapis.com/customsearch/v1?{params}"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=8) as response:
                data = json.loads(response.read().decode('utf-8'))

            results = []
            for item in data.get("items", [])[:max_results]:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                })
            return results
        except Exception:
            return []

    def _search_bing_api(self, query: str, max_results: int) -> list:
        """Bing Web Search API 검색 (환경변수: BING_API_KEY)"""
        api_key = os.environ.get("BING_API_KEY", "")
        if not api_key:
            return []

        try:
            params = urllib.parse.urlencode({"q": query, "count": min(max_results, 10)})
            url = f"https://api.bing.microsoft.com/v7.0/search?{params}"
            req = urllib.request.Request(url, headers={"Ocp-Apim-Subscription-Key": api_key})
            with urllib.request.urlopen(req, timeout=8) as response:
                data = json.loads(response.read().decode('utf-8'))

            results = []
            for item in data.get("webPages", {}).get("value", [])[:max_results]:
                results.append({
                    "title": item.get("name", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("snippet", ""),
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
        """웹 검색을 수행합니다. DuckDuckGo 우선, SearXNG 차선, Google/Bing API 키 fallback.

        Args:
            query: 검색어
            max_results: 최대 결과 수 (기본: 5)
            engine: 검색 엔진 ("auto" (기본), "duckduckgo", "searxng", "google", "bing")

        Returns:
            검색 결과 목록 (제목, URL, 요약)
        """
        err = _validate_string(query, "query")
        if err:
            return _markdown_header("Search Error", "❌") + f"**{err}**\n" + _markdown_footer()

        web_engine = WebSearchEngine()
        results = web_engine.search(query, max_results, engine)

        if not results:
            # 모든 엔진 실패 시 명확한 에러 메시지
            error_details = []
            if engine == "auto":
                error_details.append("DuckDuckGo 차단됨")
                error_details.append("SearXNG 공개 인스턴스 사용 불가")
                if os.environ.get("GOOGLE_API_KEY"):
                    error_details.append("Google API 키 오류")
                else:
                    error_details.append("Google API 키 설정 필요 (GOOGLE_API_KEY + GOOGLE_CX)")
                if os.environ.get("BING_API_KEY"):
                    error_details.append("Bing API 키 오류")
                else:
                    error_details.append("Bing API 키 설정 필요 (BING_API_KEY)")
            return (_markdown_header(f"Search: {query}", "⚠️")
                    + "**검색 결과를 가져오지 못했습니다.**\n\n"
                    + "".join(f"- {e}\n" for e in error_details)
                    + "\n> 환경변수 설정: `GOOGLE_API_KEY` + `GOOGLE_CX` (Google), `BING_API_KEY` (Bing)\n"
                    + _markdown_footer())

        output = _markdown_header(f"Search Results: {query}", "🌐")
        output += f"**Query**: `{query}`\n"
        output += f"**Engine**: `{engine}`\n\n"
        for r in results:
            output += f"### 🔗 [{r['title']}]({r['url']})\n"
            output += f"- **URL**: {r['url']}\n"
            output += f"- **Summary**: {r['snippet']}\n\n"

        try_crow_ingest(f"Web search success: {query} (engine={engine})", register="life_context")
        output += _markdown_footer()
        return output
