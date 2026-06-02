import json
import urllib.request
import urllib.parse
from fastmcp import FastMCP

mcp = FastMCP(name="vibezoo-web-search")

SEARXNG_INSTANCES = [
    "https://searx.be",
    "https://searx.tiekoetter.com",
    "https://searx.work",
    "https://paulgo.io"
]

@mcp.tool()
def web_search(query: str, max_results: int = 5, time_range: str = "") -> str:
    """
    Search the web using a pool of privacy-respecting SearxNG instances.
    
    Args:
        query (str): The search query.
        max_results (int): Maximum number of results to return.
        time_range (str): Time range for search results (e.g., 'day', 'week', 'month', 'year', ''). Empty means no time restriction.
    """
    params = {
        "q": query,
        "format": "json",
    }
    if time_range:
        params["time_range"] = time_range
        
    query_string = urllib.parse.urlencode(params)
    
    errors = []
    
    for instance in SEARXNG_INSTANCES:
        url = f"{instance}/search?{query_string}"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    results = data.get("results", [])
                    
                    if not results:
                        errors.append(f"{instance}: No results found")
                        continue
                        
                    output = [f"Search Results for '{query}' (from {instance}):\n"]
                    for idx, res in enumerate(results[:max_results]):
                        title = res.get("title", "No Title")
                        link = res.get("url", "")
                        content = res.get("content", "No content available")
                        output.append(f"{idx+1}. {title}")
                        output.append(f"   URL: {link}")
                        output.append(f"   Snippet: {content}\n")
                        
                    return "\n".join(output)
        except Exception as e:
            errors.append(f"{instance}: {str(e)}")
            continue

    return f"Failed to fetch results from all SearxNG instances.\nErrors:\n" + "\n".join(errors)

if __name__ == "__main__":
    # Can run as a standalone stdio or SSE server. For standalone MCP, stdio is standard.
    # fastmcp uses stdio by default when mcp.run() is called without transport args
    mcp.run()
