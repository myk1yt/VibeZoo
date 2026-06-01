import os, ast

p = r'c:/Users/k1yt/OneDrive/문서/각종자료/공부자료들/파이썬_Python/VibeZoo_forZoocode/mcp-servers/vibezoo_mcp_bridge.py'
with open(p, 'r', encoding='utf-8') as f:
    content = f.read()
lines = content.split('\n')
print(f'Lines: {len(lines)}')
print(f'First: {lines[0][:80]}')
print(f'Last: {lines[-1][:80]}')

# Check for non-breaking spaces
if '\xa0' in content:
    print('WARNING: Non-breaking spaces (\\xa0) found!')
else:
    print('No \\xa0 found - file is clean')

# Check syntax
try:
    ast.parse(content)
    print('Syntax: OK')
except SyntaxError as e:
    print(f'Syntax ERROR: {e}')

# Check features (브라우저 드랍존 /upload 제거됨 — Webview 전용)
features = {
    'main block': 'if __name__ == "__main__"',
    'aggregate_spatial_pixels': 'aggregate_spatial_pixels',
    'GrabCut': 'grabCut',
    'Saliency': 'cv2.saliency',
    'LBP Texture': 'local_binary_pattern',
    'Median Cut': 'median_cut',
    'Histogram': 'compareHist',
    'k-means': 'kmeans',
    'SSA resize (640px)': 'target_w = 640',
    'coord fix [0][1]': '[0][1]',
    'contrib msg': 'contrib',
    'fetch_page': 'fetch_page',
    'web_search (DDG)': 'duckduckgo',
    '_html_to_markdown': '_html_to_markdown',
    'infra: _bm25_score': '_bm25_score',
    'infra: _fuzzy_match': '_fuzzy_match',
    'infra: _detect_secrets': '_detect_secrets',
}

for name, pattern in features.items():
    found = pattern.lower() in content.lower()
    status = '✅' if found else '❌'
    print(f'  {status} {name}')

print(f'\nTotal: {len(lines)} lines, {len(content.encode("utf-8"))} bytes')
