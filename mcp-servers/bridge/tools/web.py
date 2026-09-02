# VibeZoo Bridge — Web 도구 그룹
# fetch_page + web_search

import json
import logging
import os
import re as _re
import time
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
from bridge.i18n import t

logger = logging.getLogger(__name__)

# ── Retry configuration (E.2) ──────────────────────────
_MAX_RETRIES = 2
_RETRY_BACKOFF = [0.5, 1.5]  # seconds — total worst-case added latency ~2s


class WebSearchEngine:
    """웹 검색 엔진 래퍼. Exa neural search + DuckDuckGo 폴백."""

    def __init__(self):
        self._last_error: str = ""

    def _get_api_key(self) -> str:
        api_key = os.environ.get("EXA_API_KEY", "")
        if not api_key:
            try:
                import keyring
                api_key = keyring.get_password("VibeZoo", "EXA_API_KEY")
            except ImportError:
                pass
        return api_key or ""

    # ── Retry-aware urlopen (E.2) ──────────────────────────

    @staticmethod
    def _urlopen_with_retry(req, timeout: int = 10):
        """urlopen with 2 retries, exponential backoff (0.5s, 1.5s).

        Retries on URLError / timeout / 5xx.
        Never retries on 4xx (client error).
        """
        last_exc = None
        for attempt in range(_MAX_RETRIES + 1):
            try:
                return urllib.request.urlopen(req, timeout=timeout)
            except urllib.error.HTTPError as e:
                # 4xx: client error — do not retry
                if 400 <= e.code < 500:
                    raise
                # 5xx: server error — retry
                last_exc = e
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                last_exc = e

            if attempt < _MAX_RETRIES:
                time.sleep(_RETRY_BACKOFF[attempt])

        raise last_exc

    # ── Exa search ─────────────────────────────────────────

    def _exa_search(self, query: str, max_results: int) -> list:
        """Exa API neural search. Raises on error (caller handles)."""
        api_key = self._get_api_key()
        if not api_key:
            raise ValueError("EXA_API_KEY not found")

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
        with self._urlopen_with_retry(req, timeout=10) as response:
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

    # ── DuckDuckGo search (B.1) ───────────────────────────

    def _duckduckgo_search(self, query: str, max_results: int) -> list:
        """DuckDuckGo HTML endpoint search. Stdlib only, no new deps.

        Uses https://html.duckduckgo.com/html/?q=... and parses result
        anchors with regex. Raises on error (caller handles).
        """
        search_url = "https://html.duckduckgo.com/html/"
        params = urllib.parse.urlencode({"q": query})
        full_url = f"{search_url}?{params}"

        req = urllib.request.Request(
            full_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            }
        )
        with self._urlopen_with_retry(req, timeout=15) as response:
            html = response.read().decode('utf-8', errors='replace')

        results = []

        # DDG HTML: <a rel="nofollow" class="result__a" href="...">Title</a>
        link_pattern = _re.compile(
            r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
            _re.DOTALL
        )
        # DDG HTML: <a class="result__snippet" ...>snippet</a>
        snippet_pattern = _re.compile(
            r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>',
            _re.DOTALL
        )

        links = link_pattern.findall(html)
        snippets = snippet_pattern.findall(html)

        for i, (raw_url, title_html) in enumerate(links):
            page_url = self._decode_ddg_url(raw_url)

            # Strip HTML tags from title and snippet
            title = _re.sub(r'<[^>]+>', '', title_html).strip()
            snippet_html = snippets[i] if i < len(snippets) else ""
            snippet = _re.sub(r'<[^>]+>', '', snippet_html).strip()

            if not title:
                title = page_url

            results.append({
                "title": title,
                "url": page_url,
                "snippet": snippet if snippet else "No description available.",
            })

            if len(results) >= max_results:
                break

        return results

    @staticmethod
    def _decode_ddg_url(raw_url: str) -> str:
        """Decode DuckDuckGo redirect URL to get the actual target URL."""
        # DDG format: //duckduckgo.com/l/?uddg=<encoded_url>&rut=...
        if 'uddg=' in raw_url:
            parsed = urllib.parse.urlparse(raw_url)
            qs = urllib.parse.parse_qs(parsed.query)
            if 'uddg' in qs:
                return urllib.parse.unquote(qs['uddg'][0])
        return raw_url

    # ── Main search dispatcher ─────────────────────────────

    def search(self, query: str, max_results: int = 5,
               engine: str = "auto") -> list:
        """웹 검색. EXA_API_KEY가 있으면 Exa neural search, 없으면 DuckDuckGo로 폴백.

        Args:
            query: 검색어
            max_results: 최대 결과 수
            engine: auto|exa|ddg
                - "auto" (default): Exa if EXA_API_KEY present, else DuckDuckGo
                - "exa": Exa only (error if no key)
                - "ddg": DuckDuckGo only

        Returns:
            검색 결과 목록 (실패 시 빈 리스트, self._last_error에 원인 저장)
        """
        self._last_error = ""

        # Resolve engine (B.1: honest engine parameter)
        if engine == "auto":
            if self._get_api_key():
                engine = "exa"
            else:
                engine = "ddg"
        elif engine not in ("exa", "ddg"):
            self._last_error = (
                f"WEB/search/001: 알 수 없는 엔진 '{engine}'. "
                f"auto|exa|ddg 중 하나를 사용하세요."
            )
            return []

        # Execute search
        try:
            if engine == "exa":
                return self._exa_search(query, max_results)
            else:
                return self._duckduckgo_search(query, max_results)
        except Exception as exc:
            # B.2: Structured error capture instead of silent swallow
            self._last_error = (
                f"WEB/search/002: 검색 실패 ({engine}): "
                f"{type(exc).__name__}: {exc}"
            )
            logger.error(
                "WebSearchEngine.search failed [engine=%s]: %s",
                engine, exc, exc_info=True
            )

            # Record to ErrorRegistry (best-effort)
            try:
                from bridge.error_handler import ErrorRegistry
                registry = ErrorRegistry()
                registry.record("web_search", exc, {"query": query, "engine": engine})
            except Exception:
                pass  # ErrorRegistry is best-effort

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
        """웹 검색. EXA_API_KEY가 있으면 Exa neural search, 없으면 DuckDuckGo로 폴백. engine: auto|exa|ddg

        Args:
            query: 검색어
            max_results: 최대 결과 수 (기본: 5)
            engine: auto|exa|ddg (기본: auto)

        Returns:
            검색 결과 목록 (제목, URL, 요약)
        """
        err = _validate_string(query, "query")
        if err:
            return _markdown_header("Search Error", "❌") + f"**{err}**\n" + _markdown_footer()

        web_engine = WebSearchEngine()
        results = web_engine.search(query, max_results, engine)

        if not results:
            error_reason = web_engine._last_error or "결과 없음"
            return (_markdown_header(f"Search: {query}", "⚠️")
                    + f"**검색 실패: {error_reason}**\n\n"
                    + "- `engine=auto` (기본): EXA_API_KEY가 있으면 Exa, 없으면 DuckDuckGo 사용\n"
                    + "- `engine=exa`: Exa 전용 (키 필요)\n"
                    + "- `engine=ddg`: DuckDuckGo 전용\n"
                    + _markdown_footer())

        # Determine which engine was actually used
        used_engine = engine
        if engine == "auto":
            used_engine = "exa" if web_engine._get_api_key() else "ddg"

        output = _markdown_header(f"Search Results: {query}", "🌐")
        output += f"**Query**: `{query}`\n"
        output += f"**Engine**: `{used_engine}`\n\n"
        for r in results:
            output += f"### 🔗 [{r['title']}]({r['url']})\n"
            output += f"- **URL**: {r['url']}\n"
            output += f"- **Summary**: {r['snippet']}\n\n"

        try_crow_ingest(f"Web search success: {query} (engine={used_engine})", register="life_context")
        output += _markdown_footer()
        return output
