import urllib.request, re, sys

url = 'https://www.autoview.co.kr/ko-kr/articles/99605'
req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode('utf-8', errors='replace')
    print(f"Fetched {len(html)} bytes")
    
    # Find all images
    imgs = re.findall(r'<img[^>]+src="([^"]+)"[^>]*>', html)
    print(f"Found {len(imgs)} images")
    for i, img in enumerate(imgs):
        print(f"  {i}: {img[:150]}")
    
    # Find the last image
    if imgs:
        last = imgs[-1]
        print(f"\nLast image URL: {last}")
        # Alt text
        alt = re.search(r'<img[^>]+src="' + re.escape(last) + r'"[^>]*alt="([^"]*)"', html)
        if alt:
            print(f"Alt text: {alt.group(1)}")
        # Context
        idx = html.find(last)
        context = html[max(0,idx-500):idx+300]
        # Strip tags for readability
        text_only = re.sub(r'<[^>]+>', ' ', context)
        text_only = re.sub(r'\s+', ' ', text_only).strip()
        print(f"\nContext around image:\n{text_only[:500]}")
except Exception as e:
    print(f"Error: {e}")
