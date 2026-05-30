#!/usr/bin/env python
# VibeZoo MCP Bridge에 SSA v2 (Statistical Spatial Aggregator) 도구 추가
import os, sys, re

BRIDGE = r'c:/Users/k1yt/OneDrive/문서/각종자료/공부자료들/파이썬_Python/VibeZoo_forZoocode/mcp-servers/vibezoo_mcp_bridge.py'

print("📖 Reading bridge...")
with open(BRIDGE, 'r', encoding='utf-8') as f:
    content = f.read()
print(f"   Current: {len(content)} chars, {content.count(chr(10))+1} lines")

# SSA v2 코드 (cv2 임포트 포함)
ssa_code = r'''

# ═══════════════════════════════════════════════════════════
# SSA v2: Statistical Spatial Aggregator — 이미지 공간 분석
# OCR 없이 순수 OpenCV 수학 연산으로 이미지 구조 이해
# ═══════════════════════════════════════════════════════════

try:
    import cv2
    import numpy as np
    _CV2_AVAILABLE = True
except ImportError:
    _CV2_AVAILABLE = False


@mcp.tool
def aggregate_spatial_pixels(image_path: str, detail: str = "auto") -> str:
    """Statistical Spatial Aggregator v2 — OCR 없이 이미지를 공간 통계 매트릭스로 압축합니다.
    외부 비전 모델(VLM) 없이, 순수 OpenCV 수학 연산만으로 이미지의 
    색상 분포, 질감, 텍스트 영역, 대칭성 등을 분석하여 LLM이 이해할 수 있는 형태로 변환합니다.
    
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
                    + f"**Cannot read image:** `{image_path}`\n"
                    + _markdown_footer())
        
        h, w, _ = img.shape
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        lines = []
        fname = os.path.basename(image_path) if 'os' in dir() else image_path.split('/')[-1]
        lines.append(f"### SYSTEM_VISION_REPORT: {fname}")
        lines.append(f"- Resolution: {w}x{h} ({(w*h)/1e6:.1f}MP)")
        
        # 1. 8x8 Grid
        g = 8
        ch, cw = h//g, w//g
        rows = []
        for r in range(g):
            row = []
            for c in range(g):
                y1, y2 = r*ch, (r+1)*ch
                x1, x2 = c*cw, (c+1)*cw
                cell = gray[y1:y2, x1:x2]
                cell_hsv = hsv[y1:y2, x1:x2]
                
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
        
        lines.append("\n### Spatial Grid (8x8)")
        lines.append("| Y\\X | " + " | ".join([f"X{i}" for i in range(g)]) + " |")
        lines.append("|---|" + "|---"*g + "|")
        for r in range(g):
            lines.append(f"| Y{r} | " + " | ".join(rows[r]) + " |")
        
        # 2. k-means Dominant Colors
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
        
        lines.append("\n### Color Composition (k-means)")
        for label_id, count in color_counts.most_common(k):
            bgr = centers[int(label_id)]
            name = bgr_to_name(bgr)
            pct = count / len(labels) * 100
            bars = "█" * int(pct / 2.5)
            lines.append(f"- {name}: {pct:.0f}% {bars}")
        
        # 3. Edge & Texture
        edges = cv2.Canny(gray, 50, 150)
        edge_pct = np.sum(edges > 0) / (h * w) * 100
        
        lines.append("\n### Edge & Texture")
        if edge_pct < 3: texture_desc = "Very smooth (solid color/gradient)"
        elif edge_pct < 8: texture_desc = "Smooth (simple product shot)"
        elif edge_pct < 15: texture_desc = "Moderately detailed (natural scene)"
        else: texture_desc = "Highly detailed (complex scene)"
        lines.append(f"- Edge density: {edge_pct:.1f}% — {texture_desc}")
        
        # 4. Text Region Detection (MSER)
        try:
            mser = cv2.MSER_create()
            regions, _ = mser.detectRegions(gray)
            text_like = [r for r in regions if 30 < len(r) < 800]
            if text_like:
                lines.append(f"\n### Text Regions (MSER)")
                lines.append(f"- Detected: {len(text_like)} text-like regions")
                # Count regions by position
                top = sum(1 for r in text_like if np.mean(r[:,1]) < h/3)
                bottom = sum(1 for r in text_like if np.mean(r[:,1]) > 2*h/3)
                center = len(text_like) - top - bottom
                if top > 0: lines.append(f"- Top area: ~{top} text regions")
                if center > 0: lines.append(f"- Center area: ~{center} text regions")
                if bottom > 0: lines.append(f"- Bottom area: ~{bottom} text regions")
            else:
                lines.append("\n### Text Regions: None detected")
        except Exception:
            lines.append("\n### Text Regions: Detection unavailable")
        
        # 5. Symmetry
        half = w // 2
        left = gray[:, :half]
        right = cv2.flip(gray[:, -half:], 1)
        min_w = min(left.shape[1], right.shape[1])
        try:
            sym = cv2.matchTemplate(left[:, :min_w], right[:, :min_w], cv2.TM_CCOEFF_NORMED)[0][0]
            lines.append(f"\n### Symmetry: {sym:.2f} ({'High' if sym > 0.6 else 'Moderate' if sym > 0.35 else 'Low'})")
        except:
            pass
        
        # 6. Summary
        lines.append("\n### AI Spatial Inference")
        main_color = bgr_to_name(centers[color_counts.most_common(1)[0][0]])
        has_text = len(text_like) > 5 if 'text_like' in dir() else False
        
        lines.append(f"- Dominant: {main_color} ({color_counts.most_common(1)[1] * 100 // len(labels) if len(color_counts) > 1 else 100}%)")
        lines.append(f"- {'Contains text elements' if has_text else 'No text detected'}")
        lines.append(f"- Composition: {'symmetric' if sym > 0.5 else 'asymmetric'}")
        
        try_crow_ingest(f"SSA v2 analyze: {fname} ({w}x{h})", register="context")
        return "\n".join(lines)
        
    except Exception as e:
        return (_markdown_header("SSA Error", "❌")
                + f"**Analysis failed:** {e}\n"
                + _markdown_footer())
'''

# Find insertion point (before main block)
marker = "# ═══════════════════════════════════════════════════════════\n# 메인 — SSE 서버 시작"
if marker in content:
    content = content.replace(marker, ssa_code + '\n\n' + marker)
    print("✅ SSA v2 code inserted")
else:
    print("❌ Main marker not found!")
    sys.exit(1)

# Verify syntax
try:
    compile(content, BRIDGE, 'exec')
    print("✅ Syntax: OK")
except SyntaxError as e:
    print(f"❌ Syntax error at line {e.lineno}: {e.msg}")
    sys.exit(1)

# Atomic write
print(f"\n📝 Writing {len(content)} chars...")
tmp = BRIDGE + '.ssa_tmp'
with open(tmp, 'w', encoding='utf-8') as f:
    f.write(content)
os.replace(tmp, BRIDGE)
print("✅ Write complete!")

# Verify
with open(BRIDGE, 'r', encoding='utf-8') as f:
    final = f.read()
print(f"📊 Final: {len(final)} chars, {final.count(chr(10))+1} lines")
print(f"   Has aggregate_spatial_pixels: {'aggregate_spatial_pixels' in final}")
print(f"   Has MSER: {'MSER_create' in final}")
print(f"   Has k-means: {'kmeans' in final}")
print("\n✅ SSA v2 added to bridge!")
print("   Bridge restart required to activate.")
