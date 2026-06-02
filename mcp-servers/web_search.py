import asyncio
import aiohttp
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from googlesearch import search as google_search
from fastmcp import FastMCP

mcp = FastMCP(name="vibezoo-web-search")

async def search_ddg(query: str, max_results: int = 5):
    def _search():
        try:
            with DDGS() as ddgs:
                return list(ddgs.text(query, max_results=max_results))
        except Exception:
            return []

    try:
        raw_results = await asyncio.to_thread(_search)
        results = []
        for r in raw_results:
            results.append({
                "url": r.get("href"),
                "title": r.get("title"),
                "snippet": r.get("body"),
                "engine": "DuckDuckGo"
            })
        return results
    except Exception as e:
        return []

async def search_google_async(query: str, max_results: int = 5):
    def _search():
        try:
            return list(google_search(query, num_results=max_results, advanced=True))
        except Exception:
            return []
    raw_results = await asyncio.to_thread(_search)
    results = []
    for r in raw_results:
        results.append({
            "url": r.url,
            "title": r.title,
            "snippet": r.description,
            "engine": "Google"
        })
    return results

async def search_yahoo(query: str, max_results: int = 5):
    results = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    url = f"https://search.yahoo.com/search?p={query}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    soup = BeautifulSoup(html, "html.parser")
                    for div in soup.select(".algo-sr")[:max_results]:
                        title_a = div.select_one("h3.title a")
                        snippet_div = div.select_one(".compText")
                        if title_a and snippet_div:
                            results.append({
                                "url": title_a.get("href"),
                                "title": title_a.text.strip(),
                                "snippet": snippet_div.text.strip(),
                                "engine": "Yahoo"
                            })
    except Exception:
        pass
    return results

@mcp.tool()
async def web_search(query: str, max_results: int = 5, time_range: str = "") -> str:
    """
    Search the web using DuckDuckGo, Google, and Yahoo in parallel.
    Args:
        query (str): The search query.
        max_results (int): Maximum number of results to return per engine.
        time_range (str): Unused in this version, kept for compatibility.
    """
    tasks = [
        search_ddg(query, max_results),
        search_google_async(query, max_results),
        search_yahoo(query, max_results)
    ]
    results_lists = await asyncio.gather(*tasks, return_exceptions=True)
    deduped = {}
    for res_list in results_lists:
        if isinstance(res_list, Exception): continue
        for item in res_list:
            url = item.get("url")
            if not url: continue
            if url in deduped:
                if item["engine"] not in deduped[url]["engines"]:
                    deduped[url]["engines"].append(item["engine"])
            else:
                item["engines"] = [item["engine"]]
                deduped[url] = item
    if not deduped: return f"'{query}'에 대한 검색 결과를 찾을 수 없습니다."
    md_lines = [f"## 🔍 '{query}' Search Results\n"]
    for url, data in deduped.items():
        engines_str = ", ".join(data["engines"])
        md_lines.append(f"### [{data['title']}]({url})")
        md_lines.append(f"> {data['snippet']}")
        md_lines.append(f"*Source: {engines_str}*\n")
    return "\n".join(md_lines)

if __name__ == "__main__":
    mcp.run()
