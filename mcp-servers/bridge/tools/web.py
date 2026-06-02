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

    ENGINES = ["auto", "duckduckgo", "mojeek", "wikipedia", "google", "bing"]

    def search(self, query: str, max_results: int = 5,
               preferred_engine: str = "auto") -> list:
        """검색 엔진 폴백 체인 — DuckDuckGo Lite → Mojeek → Wikipedia → 병렬 폴백.

        Args:
            query: 검색어
            max_results: 최대 결과 수
            preferred_engine: "auto" | "duckduckgo" | "mojeek" | "wikipedia" |  | "google" | "bing"

        Returns:
            검색 결과 목록 (실패 시 빈 리스트)
        """
        if preferred_engine == "auto":
            # 순차적 폴백: Lite → Mojeek → Wikipedia
            engines = [
                self._search_duckduckgo,
                self._search_mojeek,
                self._search_wikipedia,
            ]
            for engine_fn in engines:
                try:
                    results = engine_fn(query, max_results)
                    if results:
                        return results
                except Exception:
                    continue
            return self._parallel_search(query, max_results)
        elif preferred_engine == "duckduckgo":
            return self._search_duckduckgo(query, max_results)
        elif preferred_engine == "mojeek":
            return self._search_mojeek(query, max_results)
        elif preferred_engine == "wikipedia":
            return self._search_wikipedia(query, max_results)
        elif preferred_engine == :
        elif preferred_engine == "google":
            return self._search_google_api(query, max_results)
        elif preferred_engine == "bing":
            return self._search_bing_api(query, max_results)
        return []

    def _parallel_search(self, query: str, max_results: int) -> list:
        """나머지 엔진을 병렬로 동시 호출, 가장 빠른 결과 사용.

        DuckDuckGo Lite/Mojeek/Wikipedia가 모두 실패한 후 호출되므로,
        """
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
            future_map = {}

            # Mojeek (빠른 HTML 스크래핑)
            future = pool.submit(self._search_mojeek, query, max_results)
            future_map[future] = "mojeek"

            # Wikipedia (빠른 API)
            future = pool.submit(self._search_wikipedia, query, max_results)
            future_map[future] = "wikipedia"

            future_map[future] = 

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
        """DuckDuckGo Lite 검색 (JS 없음, 차단 약함)"""
        encoded_query = urllib.parse.quote(query)
        try:
            url = f"https://lite.duckduckgo.com/lite/?q={encoded_query}"
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml',
                'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
            })
            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read().decode('utf-8', errors='replace')

            results = []
            # 결과 링크 추출
            for a_tag in _re.finditer(r'<a[^>]*href="(https?://[^"]+)"[^>]*>(.*?)</a>', html, _re.DOTALL):
                href = a_tag.group(1)
                if 'duckduckgo.com' in href or 'duck.com' in href:
                    continue
                title = _re.sub(r'<[^>]+>', '', a_tag.group(2)).strip()
                if title:
                    results.append({"title": title, "url": href, "snippet": ""})
                    if len(results) >= max_results:
                        break

            # snippet 추출 (별도 블록)
            snippets = _re.findall(r'<td[^>]*class="result-snippet"[^>]*>(.*?)</td>', html, _re.DOTALL)
            for i, snip in enumerate(snippets):
                if i < len(results):
                    results[i]["snippet"] = _re.sub(r'<[^>]+>', '', snip).strip()

            if results:
                return results
        except Exception:
            pass
        return []

    def _search_mojeek(self, query: str, max_results: int) -> list:
        """Mojeek 검색 (API 키 불필요)"""
        encoded_query = urllib.parse.quote(query)
        try:
            url = f"https://www.mojeek.com/search?q={encoded_query}"
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml',
            })
            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read().decode('utf-8', errors='replace')

            results = []
            # Mojeek 결과: <h2 class="title"><a href="...">title</a></h2>
            blocks = _re.findall(
                r'<h2[^>]*class="title"[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>\s*</h2>',
                html, _re.DOTALL
            )
            for href, title_raw in blocks[:max_results]:
                title = _re.sub(r'<[^>]+>', '', title_raw).strip()
                if title:
                    results.append({
                        "title": title,
                        "url": href,
                        "snippet": "No description available.",
                    })
            return results
        except Exception:
            return []

    def _search_wikipedia(self, query: str, max_results: int) -> list:
        """Wikipedia API 검색"""
        encoded_query = urllib.parse.quote(query)
        try:
            url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={encoded_query}&format=json&srlimit={max_results}"
            req = urllib.request.Request(url, headers={'User-Agent': 'VibeZoo/1.0'})
            with urllib.request.urlopen(req, timeout=8) as response:
                data = json.loads(response.read().decode('utf-8'))
            results = []
            for item in data.get("query", {}).get("search", []):
                title = item.get("title", "")
                page_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
                results.append({
                    "title": f"[Wikipedia] {title}",
                    "url": page_url,
                    "snippet": item.get("snippet", ""),
                })
            return results
        except Exception:
            return []

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
        """웹 검색을 수행합니다. DuckDuckGo Lite → Mojeek → Wikipedia → 병렬 폴백.

        Args:
            query: 검색어
            max_results: 최대 결과 수 (기본: 5)
            engine: 검색 엔진 ("auto" (기본), "duckduckgo", "mojeek", "wikipedia", "google", "bing")

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
                error_details.append("DuckDuckGo Lite 차단/무응답")
                error_details.append("Mojeek 무응답")
                error_details.append("Wikipedia API 무응답")
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
