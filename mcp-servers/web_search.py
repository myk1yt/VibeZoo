import asyncio
import httpx
from bs4 import BeautifulSoup
from curl_cffi.requests import AsyncSession
from selectolax.parser import HTMLParser
from fastmcp import FastMCP

mcp = FastMCP(name="vibezoo-web-search")

async def search_curl_cffi(query: str, max_results: int = 5):
    """Search DuckDuckGo using curl_cffi"""
    results = []
    try:
        async with AsyncSession(impersonate="chrome") as session:
            r = await session.get(f"https://html.duckduckgo.com/html/?q={query}", timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.select(".result__title .result__a")[:max_results]:
                snippet_elem = a.find_next(class_="result__snippet")
                snippet = snippet_elem.text.strip() if snippet_elem else ""
                url = a.get("href")
                # DuckDuckGo sometimes prepends a redirect url like "//duckduckgo.com/l/?uddg="
                if url and "uddg=" in url:
                    import urllib.parse
                    parsed = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
                    if "uddg" in parsed:
                        url = parsed["uddg"][0]
                
                results.append({
                    "url": url,
                    "title": a.text.strip(),
                    "snippet": snippet,
                    "engine": "DuckDuckGo (curl_cffi)"
                })
    except Exception as e:
        print(f"curl_cffi error: {e}")
    return results

async def search_selectolax(query: str, max_results: int = 5):
    """Search Yahoo using httpx and selectolax"""
    results = []
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        async with httpx.AsyncClient(headers=headers, timeout=10) as client:
            r = await client.get(f"https://search.yahoo.com/search?p={query}")
            tree = HTMLParser(r.text)
            for div in tree.css(".algo-sr")[:max_results]:
                title_a = div.css_first("h3.title a")
                snippet_div = div.css_first(".compText")
                if title_a and snippet_div:
                    results.append({
                        "url": title_a.attributes.get("href"),
                        "title": title_a.text(strip=True),
                        "snippet": snippet_div.text(strip=True),
                        "engine": "Yahoo (selectolax+httpx)"
                    })
    except Exception as e:
        print(f"selectolax error: {e}")
    return results

@mcp.tool()
async def web_search(query: str, max_results: int = 5, time_range: str = "") -> str:
    """
    Search the web using surviving async methods (curl_cffi, selectolax+httpx) in parallel.
    Args:
        query (str): The search query.
        max_results (int): Maximum number of results to return per engine.
        time_range (str): Unused in this version, kept for compatibility.
    """
    tasks = [
        search_curl_cffi(query, max_results),
        search_selectolax(query, max_results)
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
