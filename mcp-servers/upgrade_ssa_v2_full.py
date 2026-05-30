#!/usr/bin/env python
# SSA v2 Full Upgrade: GrabCut + Saliency + LBP + MedianCut + Histogram + AdaptiveGrid
import os, sys, re

BRIDGE = r'c:/Users/k1yt/OneDrive/문서/각종자료/공부자료들/파이썬_Python/VibeZoo_forZoocode/mcp-servers/vibezoo_mcp_bridge.py'

print("📖 Reading bridge...")
with open(BRIDGE, 'r', encoding='utf-8') as f:
    content = f.read()
print(f"   Current: {len(content)} chars")

# New SSA v3 code with 6 improvements
ssa_v3 = r'''

# ═══════════════════════════════════════════════════════════
# SSA v3: Enhanced Aggregator — 6가지 컴퓨터 비전 분석
# GrabCut + Saliency + LBP + MedianCut + Histogram + Grid
# ═══════════════════════════════════════════════════════════

@mcp.tool
def aggregate_spatial_pixels(image_path: str, detail: str = "auto") -> str:
    """Statistical Spatial Aggregator v3 — 이미지를 공간 통계 매트릭스로 압축합니다.
    OCR 없이 순수 OpenCV 수학 연산으로 색상/질감/객체/텍스트/대칭성/현저성 분석.
    
    Args:
        image_path: 분석할 이미지 파일 경로
        detail: 분석 상세도 ("auto", "quick", "full")
    
    Returns:
        마크다운 형식의 이미지 분석 보고서
    """
    if not _CV2_AVAILABLE:
        return (_markdown_header("SSA Error", "❌")
                + "**OpenCV not installed.** Run: `pip install opencv-python-headless numpy`\n"
                + _markdown_footer())
    
    try:
        img = cv2.imread(image_path)
        if img is None:
            return (_markdown_header("SSA Error", "❌")
                    + f"**Cannot read image:** `{image_path}`\n" + _markdown_footer())
        
        h, w, _ = img.shape
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        lines = []
        fname = os.path.basename(image_path) if 'os' in dir() else image_path.split('/')[-1]
        lines.append(f"### SYSTEM_VISION_REPORT: {fname}")
        lines.append(f"- Resolution: {w}x{h} ({(w*h)/1e6:.1f}MP)")
        
        # === 1. Spatial Grid (8x8) ===
        g = 8; ch, cw = h//g, w//g
        rows = []
        for r in range(g):
            row = []
            for c in range(g):
                y1, y2 = r*ch, (r+1)*ch; x1, x2 = c*cw, (c+1)*cw
                cell = gray[y1:y2, x1:x2]; cell_hsv = hsv[y1:y2, x1:x2]
                avg_v = int(np.mean(cell_hsv[:,:,2]))
                lap = cv2.Laplacian(cell, cv2.CV_64F).var()
                tex = "R" if lap > 350 else "S"
                if avg_v < 40: col = "Black"
                else:
                    ah = int(np.mean(cell_hsv[:,:,0]))
                    if ah < 10 or ah > 170: col = "Red"
                    elif ah < 25: col = "Orange"
                    elif ah < 35: col = "Yellow"
                    elif ah < 85: col = "Green"
                    elif ah < 130: col = "Blue"
                    else: col = "Purple"
                row.append(f"{col}({tex})")
            rows.append(row)
        
        lines.append("\n### 8x8 Grid")
        lines.append("| Y\\X | " + " | ".join([f"X{i}" for i in range(g)]) + " |")
        lines.append("|---|" + "|---"*g + "|")
        for r in range(g):
            lines.append(f"| Y{r} | " + " | ".join(rows[r]) + " |")
        
        # === 2. GrabCut 객체 분할 ===
        try:
            mask = np.zeros(img.shape[:2], np.uint8)
            bgd = np.zeros((1,65), np.float64)
            fgd = np.zeros((1,65), np.float64)
            rect = (w//8, h//8, w*3//4, h*3//4)  # 중앙 75% 영역
            cv2.grabCut(img, mask, rect, bgd, fgd, 3, cv2.GC_INIT_WITH_RECT)
            fg_mask = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 1, 0).astype(np.uint8)
            fg_pct = np.sum(fg_mask) / (h * w) * 100
            
            # 객체의 바운딩 박스
            contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                largest = max(contours, key=cv2.contourArea)
                x, y, bw, bh = cv2.boundingRect(largest)
                cx, cy = x + bw//2, y + bh//2
                v_pos = "top" if cy < h//3 else "bottom" if cy > 2*h//3 else "center"
                h_pos = "left" if cx < w//3 else "right" if cx > 2*w//3 else "center"
                aspect = bw / bh if bh > 0 else 0
                if aspect > 1.5: shape = "horizontal/wide"
                elif aspect < 0.66: shape = "vertical/tall"
                else: shape = "near-square"
                lines.append(f"\n### Object Detection (GrabCut)")
                lines.append(f"- Foreground: {fg_pct:.0f}% of image")
                lines.append(f"- Main object: {bw}x{bh}px at ({h_pos},{v_pos}), shape={shape}")
                lines.append(f"- Position: center={(cx/w*100):.0f}%H,{(cy/h*100):.0f}%V")
        except Exception as e:
            lines.append(f"\n### Object Detection: unavailable")
        
        # === 3. k-means Dominant Colors ===
        pixels = img.reshape(-1, 3).astype(np.float32)
        k = 4
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        
        from collections import Counter
        color_counts = Counter(labels.flatten())
        
        def bgr_to_name(bgr):
            b, g, r = int(bgr[0]), int(bgr[1]), int(bgr[2])
            if max(b,g,r) < 50: return "Black"
            if min(b,g,r) > 200: return "White"
            if abs(r-g) < 30 and abs(g-b) < 30: return "Gray"
            if r > g and r > b: return "Red" if r > 2*max(g,b) else "Brown"
            if g > r and g > b: return "Green"
            if b > r and b > g: return "Blue"
            if r > b and g > b: return "Yellow"
            if b > r and g > r: return "Cyan"
            return f"RGB({r},{g},{b})"
        
        lines.append("\n### Color Composition")
        for label_id, count in color_counts.most_common(k):
            bgr = centers[int(label_id)]
            name = bgr_to_name(bgr)
            pct = count / len(labels) * 100
            bars = "█" * int(pct / 2.5)
            lines.append(f"- {name}: {pct:.0f}% {bars}")
        
        # === 4. Median Cut 색상 양자화 (k-means보다 정확) ===
        try:
            from collections import defaultdict
            def median_cut(img_flat, depth=4):
                if depth == 0 or len(img_flat) < 16:
                    avg = np.mean(img_flat, axis=0).astype(int)
                    return [avg]
                # 가장 범위가 큰 채널 선택
                ranges = [np.max(img_flat[:,i]) - np.min(img_flat[:,i]) for i in range(3)]
                channel = np.argmax(ranges)
                sorted_idx = np.argsort(img_flat[:, channel])
                split = len(sorted_idx) // 2
                left = median_cut(img_flat[sorted_idx[:split]], depth-1)
                right = median_cut(img_flat[sorted_idx[split:]], depth-1)
                return left + right
            
            mc_colors = median_cut(pixels[:min(len(pixels), 10000)], 4)
            mc_colors = mc_colors[:8]  # 최대 8색
            lines.append(f"\n### Dominant Colors (Median Cut)")
            for c in mc_colors[:4]:
                name = bgr_to_name(c)
                lines.append(f"- {name} ({c[2]},{c[1]},{c[0]})")
        except Exception:
            pass
        
        # === 5. LBP Texture ===
        try:
            def local_binary_pattern(img_grayscale, P=8, R=1):
                """LBP 구현 (np만 사용)"""
                h, w = img_grayscale.shape
                lbp = np.zeros_like(img_grayscale)
                center = img_grayscale[R:h-R, R:w-R]
                code = 0
                for k in range(P):
                    angle = 2 * np.pi * k / P
                    x = R * np.cos(angle)
                    y = -R * np.sin(angle)
                    x1, y1 = int(np.floor(x)), int(np.floor(y))
                    x2, y2 = int(np.ceil(x)), int(np.ceil(y))
                    neighbor = img_grayscale[R+y1:R+y1+h-2*R, R+x1:R+x1+w-2*R]
                    code += (neighbor >= center) * (1 << k)
                lbp[R:h-R, R:w-R] = code
                return lbp
            
            lbp_img = local_binary_pattern(gray)
            # LBP 히스토그램
            hist = cv2.calcHist([lbp_img.astype(np.uint8)], [0], None, [256], [0, 256])
            # 질감 균일도 측정
            uniform = np.sum(hist[:32]) / np.sum(hist) * 100
            if uniform > 70: tex_type = "Very uniform (solid/smooth)"
            elif uniform > 40: tex_type = "Moderately textured"
            elif uniform > 20: tex_type = "Highly textured (complex)"
            else: tex_type = "Extremely detailed"
            lines.append(f"\n### Texture Analysis (LBP)")
            lines.append(f"- Uniformity: {uniform:.0f}% — {tex_type}")
        except Exception:
            pass
        
        # === 6. Saliency Detection ===
        try:
            saliency = cv2.saliency.StaticSaliencySpectralResidual_create()
            _, saliency_map = saliency.computeSaliency(gray)
            saliency_map = (saliency_map * 255).astype(np.uint8)
            
            # 현저한 영역 임계값
            _, salient_binary = cv2.threshold(saliency_map, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            salient_pct = np.sum(salient_binary > 0) / (h * w) * 100
            
            # 가장 현저한 위치
            salient_coords = np.where(salient_binary > 0)
            if len(salient_coords[0]) > 0:
                sy = int(np.mean(salient_coords[0]))
                sx = int(np.mean(salient_coords[1]))
                sv = "top" if sy < h//3 else "center" if sy < 2*h//3 else "bottom"
                sh = "left" if sx < w//3 else "center" if sx < 2*w//3 else "right"
                lines.append(f"\n### Visual Saliency")
                lines.append(f"- Salient area: {salient_pct:.0f}% of image")
                lines.append(f"- Focus: ({sh},{sv})")
        except Exception:
            pass
        
        # === 7. Histogram Comparison ===
        try:
            grid_similarity = []
            for r in range(g-1):
                for c in range(g-1):
                    y1,y2 = r*ch, (r+1)*ch; x1,x2 = c*cw, (c+1)*cw
                    cell1 = hsv[y1:y2, x1:x2]
                    cell2 = hsv[y1:y2, min(x2+cw, w):min(x2+2*cw, w)]
                    if cell2.shape[1] < cw//2: continue
                    hist1 = cv2.calcHist([cell1], [0], None, [30], [0, 180])
                    hist2 = cv2.calcHist([cell2], [0], None, [30], [0, 180])
                    cv2.normalize(hist1, hist1); cv2.normalize(hist2, hist2)
                    sim = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
                    grid_similarity.append(sim)
            if grid_similarity:
                avg_sim = np.mean(grid_similarity)
                if avg_sim > 0.7: comp = "Very uniform/repetitive"
                elif avg_sim > 0.4: comp = "Moderately varied"
                else: comp = "Highly varied/dynamic"
                lines.append(f"\n### Spatial Uniformity")
                lines.append(f"- Grid similarity: {avg_sim:.2f} — {comp}")
        except Exception:
            pass
        
        # === 8. Summary ===
        lines.append("\n### AI Spatial Inference")
        main_color = bgr_to_name(centers[color_counts.most_common(1)[0][0]])
        lines.append(f"- Dominant color: {main_color} ({color_counts.most_common(1)[1]*100//len(labels)}%)")
        if 'salient_pct' in dir() and salient_pct > 5:
            lines.append(f"- Visual focus: {salient_pct:.0f}% area at ({sh},{sv})")
        if 'fg_pct' in dir() and fg_pct > 5:
            lines.append(f"- Object occupies: {fg_pct:.0f}% of frame")
        if 'avg_sim' in dir():
            lines.append(f"- Scene type: {comp}")
        
        try_crow_ingest(f"SSA v3 analyze: {fname} ({w}x{h})", register="context")
        return "\n".join(lines)
        
    except Exception as e:
        return (_markdown_header("SSA Error", "❌")
                + f"**Analysis failed:** {e}\n" + _markdown_footer())
'''

# Replace old SSA function with new v3
old_marker = "@mcp.tool\ndef aggregate_spatial_pixels(image_path: str, detail: str = \"auto\") -> str:"
new_marker = ssa_v3.split('@mcp.tool')[0] + '@mcp.tool'

if old_marker in content:
    # Find the old function boundaries
    start = content.find(old_marker)
    # Find the next function or end
    rest = content[start:]
    next_func = re.search(r'\n@mcp\.tool(?:\n|(?=[^"]))', rest)
    if next_func:
        end = start + next_func.start()
    else:
        end = len(content)
    
    old_func = content[start:end]
    content = content.replace(old_func, ssa_v3)
    print("✅ SSA v3 code replaced (6 new features)")
else:
    print("❌ Old SSA function not found!")
    # Try finding by name only
    if 'def aggregate_spatial_pixels' in content:
        idx = content.find('def aggregate_spatial_pixels')
        # Find the next @mcp.tool or main block
        rest = content[idx:]
        next_mcp = re.search(r'\n@mcp\.tool', rest)
        next_main = rest.find('# ════════════════')
        end = idx + (next_mcp.start() if next_mcp else next_main if next_main > 0 else len(rest))
        content = content[:idx] + ssa_v3.split('@mcp.tool', 1)[1].lstrip() + content[end:]
        print("✅ SSA v3 inserted via fallback")
    else:
        print("❌ Cannot find SSA function at all!")
        sys.exit(1)

# Verify syntax
try:
    compile(content, BRIDGE, 'exec')
    print("✅ Syntax: OK")
except SyntaxError as e:
    print(f"❌ Syntax error at line {e.lineno}: {e.msg}")
    # Show context around error
    lines = content.split('\n')
    if e.lineno:
        for i in range(max(0, e.lineno-3), min(len(lines), e.lineno+2)):
            print(f"  {i+1}: {lines[i][:100]}")
    sys.exit(1)

# Atomic write
print(f"\n📝 Writing {len(content)} chars...")
tmp = BRIDGE + '.v3tmp'
with open(tmp, 'w', encoding='utf-8') as f:
    f.write(content)
os.replace(tmp, BRIDGE)
print("✅ Write complete!")

# Verify
with open(BRIDGE, 'r', encoding='utf-8') as f:
    final = f.read()
print(f"📊 Final: {len(final)} chars, {final.count(chr(10))+1} lines")
checks = ['aggregate_spatial_pixels', 'GrabCut', 'grabCut', 'saliency', 'LBP', 'median_cut', 'compareHist']
for c in checks:
    print(f"   Has {c}: {c in final}")
print("\n✅ SSA v3 upgrade complete! Bridge restart required.")
