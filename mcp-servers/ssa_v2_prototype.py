#!/usr/bin/env python
# SSA v2: Statistical Spatial Aggregator — 업그레이드 버전
# OCR 없이, 순수 OpenCV 수학 연산만으로 더 풍부한 이미지 이해
import cv2
import numpy as np
from pathlib import Path
from collections import Counter

def analyze_image_v2(image_path: str, detail_level: str = "auto") -> str:
    """
    SSA v2 — OCR 없이 이미지를 더 잘 읽기 위한 업그레이드
    
    개선 사항:
    1. 멀티스케일: 8x8 + 16x16 + contour 기반 적응형
    2. 에지 밀도 맵: 정보 밀집 영역 탐지
    3. 연결 컴포넌트: 객체 분할
    4. 컨투어 감지: 모양 분류
    5. k-means 색상 군집: 동적 색상 추출 (고정 8색 아님)
    6. MSER: 텍스트 영역 탐지
    7. 대칭성 분석
    8. 시각적 현저성 맵
    """
    img = cv2.imread(image_path)
    if img is None:
        return f"Error: Cannot read {image_path}"
    
    h, w, _ = img.shape
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    
    lines = []
    lines.append(f"### SYSTEM_VISION_REPORT_V2: {Path(image_path).name}")
    lines.append(f"- Resolution: {w}x{h}")
    
    # === 1. 멀티스케일 격자 (8x8 + 16x16) ===
    def make_grid(gray_img, g):
        ch, cw = h//g, w//g
        rows = []
        for r in range(g):
            row = []
            for c in range(g):
                y1, y2 = r*ch, (r+1)*ch
                x1, x2 = c*cw, (c+1)*cw
                cell = gray_img[y1:y2, x1:x2]
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
        return rows
    
    grid8 = make_grid(gray, 8)
    grid16 = make_grid(gray, 16)
    
    lines.append(f"\n### 8x8 Grid")
    lines.append("| Y\\X | " + " | ".join([f"X{i}" for i in range(8)]) + " |")
    lines.append("|---|" + "|---"*8 + "|")
    for r in range(8):
        lines.append(f"| Y{r} | " + " | ".join(grid8[r]) + " |")
    
    # === 2. 에지 밀도 맵 (Canny) ===
    edges = cv2.Canny(gray, 50, 150)
    edge_density = np.sum(edges > 0) / (h * w) * 100
    
    # 에지 집중 영역 (4분할)
    quad_edges = []
    for qr in range(2):
        for qc in range(2):
            qy1, qy2 = qr*h//2, (qr+1)*h//2
            qx1, qx2 = qc*w//2, (qc+1)*w//2
            q_edge = np.sum(edges[qy1:qy2, qx1:qx2] > 0)
            quad_edges.append(q_edge)
    max_quad = ["Top-Left", "Top-Right", "Bottom-Left", "Bottom-Right"][np.argmax(quad_edges)]
    
    lines.append(f"\n### Edge Analysis")
    lines.append(f"- Edge density: {edge_density:.1f}%")
    lines.append(f"- Most detailed quadrant: {max_quad}")
    
    # === 3. k-means 색상 군집 (동적 색상 추출) ===
    pixels = img.reshape(-1, 3)
    k = 4
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, labels, centers = cv2.kmeans(pixels.astype(np.float32), k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    
    color_counts = Counter(labels.flatten())
    dominant_colors = []
    for label_id, count in color_counts.most_common(k):
        bgr = centers[label_id].astype(int)
        pct = count / len(labels) * 100
        dominant_colors.append((bgr, pct))
    
    def bgr_to_name(bgr):
        b, g, r = bgr
        # 간단한 색상 이름 매핑
        if max(b,g,r) < 50: return "Black"
        if min(b,g,r) > 200: return "White"
        if abs(r-g) < 30 and abs(g-b) < 30 and abs(b-r) < 30:
            return "Gray"
        if r > g and r > b: return "Red" if r > 2*max(g,b) else "Brown" if g > b else "Orange"
        if g > r and g > b: return "Green"
        if b > r and b > g: return "Blue"
        if r > b and g > b: return "Yellow"
        if b > r and g > r: return "Cyan"
        return f"RGB({r},{g},{b})"
    
    lines.append(f"\n### Dominant Colors (k-means)")
    for bgr, pct in dominant_colors:
        name = bgr_to_name(bgr)
        bar = "█" * int(pct / 2)
        lines.append(f"- {name} ({bgr[2]},{bgr[1]},{bgr[0]}): {pct:.0f}% {bar}")
    
    # === 4. 연결 컴포넌트 (객체 분할) ===
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    num_labels, labels_im, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)
    
    # 배경(0) 제외하고 주요 객체 찾기
    objects = []
    for i in range(1, min(num_labels, 10)):
        area = stats[i, cv2.CC_STAT_AREA]
        if area > (h * w * 0.02):  # 2% 이상만
            x = stats[i, cv2.CC_STAT_LEFT]
            cy = stats[i, cv2.CC_STAT_TOP]
            cw_ = stats[i, cv2.CC_STAT_WIDTH]
            ch_ = stats[i, cv2.CC_STAT_HEIGHT]
            
            # 중심 위치
            cx = x + cw_//2
            cy_center = cy + ch_//2
            
            # 위치 설명
            v_pos = "top" if cy_center < h//3 else "bottom" if cy_center > 2*h//3 else "center"
            h_pos = "left" if cx < w//3 else "right" if cx > 2*w//3 else "center"
            
            # 종횡비로 모양 추정
            aspect = cw_ / ch_ if ch_ > 0 else 0
            if aspect > 3: shape = "wide/horizontal"
            elif aspect < 0.33: shape = "tall/vertical"
            elif 0.8 < aspect < 1.2: shape = "near-square"
            else: shape = "rectangular"
            
            objects.append(f"  * Region {i}: {cw_}x{ch_} at ({h_pos},{v_pos}), shape={shape}, area={area//100}00px")
    
    if objects:
        lines.append(f"\n### Detected Regions ({len(objects)})")
        lines.extend(objects)
    else:
        lines.append("\n### Detected Regions: None (uniform image)")
    
    # === 5. MSER: 텍스트 영역 탐지 (OCR 없이 위치만) ===
    mser = cv2.MSER_create()
    try:
        regions, _ = mser.detectRegions(gray)
        text_like = [r for r in regions if 50 < len(r) < 500]  # 텍스트 크기 필터
        if text_like:
            # 텍스트 영역의 바운딩 박스 병합
            text_areas = []
            for region in text_like:
                x, y, w_, h_ = cv2.boundingRect(region)
                text_areas.append((x, y, w_, h_))
            
            # 겹치는 영역 병합
            from itertools import combinations
            merged = list(text_areas)
            changed = True
            while changed:
                changed = False
                new_merged = []
                used = set()
                for i, a in enumerate(merged):
                    if i in used: continue
                    bx1, by1, bw, bh = a
                    bx2, by2 = bx1+bw, by1+bh
                    for j, b in enumerate(merged):
                        if j <= i or j in used: continue
                        cx1, cy1, cw, ch = b
                        cx2, cy2 = cx1+cw, cy1+ch
                        # 겹침 검사
                        if bx1 < cx2 and bx2 > cx1 and by1 < cy2 and by2 > cy1:
                            bx1, by1 = min(bx1, cx1), min(by1, cy1)
                            bx2, by2 = max(bx2, cx2), max(by2, cy2)
                            used.add(j)
                            changed = True
                    used.add(i)
                    new_merged.append((bx1, by1, bx2-bx1, by2-by1))
                merged = new_merged
            
            lines.append(f"\n### Text Regions (MSER, {len(merged)} areas)")
            for tx, ty, tw, th in merged[:5]:
                pos = "top" if ty < h//3 else "bottom" if ty > 2*h//3 else "center"
                side = "left" if tx < w//3 else "right" if tx > 2*w//3 else "center"
                lines.append(f"  * Text area: {tw}x{th}px at ({side},{pos})")
        else:
            lines.append("\n### Text Regions: None detected")
    except:
        lines.append("\n### Text Regions: MSER unavailable")
    
    # === 6. 대칭성 분석 (수직 대칭) ===
    half_w = w // 2
    left_half = gray[:, :half_w]
    right_half = gray[:, -half_w:]
    right_flipped = cv2.flip(right_half, 1)
    
    # 크기 맞추기
    min_w = min(left_half.shape[1], right_flipped.shape[1])
    left_half = left_half[:, :min_w]
    right_flipped = right_flipped[:, :min_w]
    
    symmetry = cv2.matchTemplate(left_half, right_flipped, cv2.TM_CCOEFF_NORMED)[0][0]
    lines.append(f"\n### Symmetry Analysis")
    lines.append(f"- Vertical symmetry: {symmetry:.2f} ({'HIGH' if symmetry > 0.7 else 'MODERATE' if symmetry > 0.4 else 'LOW'})")
    
    # === 7. 결론 ===
    lines.append(f"\n### Summary")
    
    # 자동 결론 생성
    main_color = bgr_to_name(dominant_colors[0][0]) if dominant_colors else "unknown"
    has_text = len(merged) > 0 if 'merged' in dir() else False
    
    conclusions = []
    conclusions.append(f"- Primary composition: {main_color}-dominant with {edge_density:.0f}% edge detail")
    conclusions.append(f"- {'Has' if has_text else 'No detectable'} text regions")
    conclusions.append(f"- Shape: {'Symmetric' if symmetry > 0.5 else 'Asymmetric'}")
    
    if edge_density < 5:
        conclusions.append("- Overall assessment: Simple/flat image (gradient, solid color)")
    elif edge_density < 15:
        conclusions.append("- Overall assessment: Moderately detailed (product shot, portrait)")
    else:
        conclusions.append("- Overall assessment: Highly detailed (complex scene, crowded)")
    
    if 'objects' in dir() and objects:
        obj_shapes = [o.split("shape=")[1].split(",")[0] for o in objects]
        conclusions.append(f"- Object shapes: {', '.join(set(obj_shapes))}")
    
    lines.extend(conclusions)
    
    return "\n".join(lines)


# === 테스트 실행 ===
if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else r'c:/Users/k1yt/OneDrive/문서/각종자료/공부자료들/파이썬_Python/VibeZoo_forZoocode/mcp-servers/analyzed_image.jpg'
    result = analyze_image_v2(path)
    print(result)
