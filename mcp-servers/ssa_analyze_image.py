#!/usr/bin/env python
# SSA: 이미지 다운로드 → 8x8 공간 매트릭스 분석
import urllib.request, cv2, numpy as np, os, sys

url = 'https://cdn.www.autoview.co.kr/w800/q80/article-images/2026-04-07/d4a25fff-babd-4918-9bc8-9ef3e88905e2.jpg'

print(f"Downloading: {url}")
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req, timeout=15)
img_data = np.asarray(bytearray(resp.read()), dtype=np.uint8)
img = cv2.imdecode(img_data, cv2.IMREAD_COLOR)

if img is None:
    print("ERROR: Could not decode image")
    sys.exit(1)

h, w, _ = img.shape
print(f"Image: {w}x{h} ({w*h/1e6:.1f}MP)")

# Save locally
local_path = r'c:/Users/k1yt/OneDrive/문서/각종자료/공부자료들/파이썬_Python/VibeZoo_forZoocode/mcp-servers/analyzed_image.jpg'
cv2.imwrite(local_path, img)
print(f"Saved to: {local_path}")

# SSA 8x8
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
g = 8
ch, cw = h//g, w//g

rows = []
for r in range(g):
    row = []
    for c in range(g):
        y1, y2 = r*ch, (r+1)*ch
        x1, x2 = c*cw, (c+1)*cw
        cell_hsv = hsv[y1:y2, x1:x2]
        cell_gray = gray[y1:y2, x1:x2]
        
        ah = int(np.mean(cell_hsv[:,:,0]))
        av = int(np.mean(cell_hsv[:,:,2]))
        lap = cv2.Laplacian(cell_gray, cv2.CV_64F).var()
        
        tex = "R" if lap > 350 else "S"
        if av < 40: col = "Black"
        elif ah < 10 or ah > 170: col = "Red"
        elif ah < 25: col = "Orange"
        elif ah < 35: col = "Yellow"
        elif ah < 85: col = "Green"
        elif ah < 130: col = "Blue"
        else: col = "Purple"
        
        row.append(f"{col}({tex})")
    rows.append(row)

print(f"\n=== 8x8 SPATIAL MATRIX ===")
print(f"Image: {url}")
print(f"Resolution: {w}x{h}")
print(f"Grid: {g}x{g}")
print()
header = "| Y\\X | " + " | ".join([f"X{i}" for i in range(g)]) + " |"
sep = "|---|" + "|---" * g + "|"
print(header)
print(sep)
for r in range(g):
    line = f"| **Y{r}** | " + " | ".join(rows[r]) + " |"
    print(line)

# Summary statistics
colors = [cell.split("(")[0] for row in rows for cell in row]
textures = [cell.split("(")[1].rstrip(")") for row in rows for cell in row]
from collections import Counter
color_dist = Counter(colors)
texture_dist = Counter(textures)

print(f"\n=== COLOR DISTRIBUTION ===")
for color, count in color_dist.most_common():
    bar = "█" * count
    print(f"  {color:8s}: {bar} ({count} cells)")

print(f"\n=== TEXTURE DISTRIBUTION ===")
for tex, count in texture_dist.most_common():
    pct = count / 64 * 100
    print(f"  {tex}: {count}/{64} ({pct:.0f}%)")

print(f"\n=== SPATIAL ANALYSIS ===")
# Detect center vs edge patterns
center = [rows[r][c] for r in range(2,6) for c in range(2,6)]
edge = [rows[r][c] for r in range(8) for c in range(8) 
        if not (2 <= r <= 5 and 2 <= c <= 5)]
center_colors = Counter(c.split("(")[0] for c in center)
edge_colors = Counter(c.split("(")[0] for c in edge)
print(f"Center dominant: {center_colors.most_common(1)[0][0] if center_colors else 'N/A'}")
print(f"Edge dominant: {edge_colors.most_common(1)[0][0] if edge_colors else 'N/A'}")
print(f"Center-edge contrast: {'HIGH' if center_colors.most_common(1)[0][0] != edge_colors.most_common(1)[0][0] else 'LOW'}")
