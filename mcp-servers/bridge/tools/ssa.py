# VibeZoo Bridge — SSA 도구 그룹
# aggregate_spatial_pixels
# Statistical Spatial Aggregator v3 — 이미지를 공간 통계 매트릭스로 압축

import json
import math
import os
import time
from collections import Counter
from io import BytesIO
from pathlib import Path
from typing import Optional

from bridge.config import (
    VERSION, IMAGE_CACHE_DIR, UPLOADED_IMAGE_PATH, WHITEBOARD_ACTION_FILE,
)
from bridge.utils import (
    _markdown_header, _markdown_footer,
    _validate_string,
    _atomic_write_json,
)
from bridge.crow_client import try_crow_ingest


# ── OpenCV 상태 ─────────────────────────────────────

try:
    import cv2  # type: ignore[import]
    import numpy as np  # type: ignore[import]
    _CV2_AVAILABLE = True
except ImportError:
    _CV2_AVAILABLE = False


# ── 헬퍼 ─────────────────────────────────────────────

def _imread_korean_safe(image_path: str):
    """
    한글 경로를 포함한 이미지 파일 읽기.
    cv2.imread는 한글 경로를 처리하지 못하므로,
    파일을 바이트로 읽어서 cv2.imdecode로 디코딩.
    """
    try:
        # 방법 1: numpy 바이트 버퍼 → imdecode (한글 경로 대응)
        with open(image_path, 'rb') as f:
            file_bytes = np.frombuffer(f.read(), np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        if img is not None:
            return img
    except Exception:
        pass

    # 방법 2: PIL로 읽어서 numpy 변환 (fallback)
    try:
        from PIL import Image
        pil_img = Image.open(image_path).convert('RGB')
        return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    except Exception:
        pass

    # 방법 3: 직접 cv2.imread (영어 경로만 동작)
    return cv2.imread(image_path)


_COLOR_NAMES_CACHE = {}


def _bgr_to_name(bgr) -> str:
    """BGR 색상 → 색상명"""
    key = tuple(bgr)
    if key in _COLOR_NAMES_CACHE:
        return _COLOR_NAMES_CACHE[key]

    b, g, r = int(bgr[0]), int(bgr[1]), int(bgr[2])
    if max(b, g, r) < 50:
        name = "Black"
    elif min(b, g, r) > 200:
        name = "White"
    elif abs(r - g) < 30 and abs(g - b) < 30:
        name = "Gray"
    elif r > g and r > b:
        name = "Red" if r > 2 * max(g, b) else "Brown"
    elif g > r and g > b:
        name = "Green"
    elif b > r and b > g:
        name = "Blue"
    elif r > b and g > b:
        name = "Yellow"
    elif b > r and g > r:
        name = "Cyan"
    else:
        name = f"RGB({r},{g},{b})"

    _COLOR_NAMES_CACHE[key] = name
    return name


# ── SSA v3 분석 코어 ─────────────────────────────────

def _analyze_image(img, detail: str = "auto", orig_w: int = 0, orig_h: int = 0) -> str:
    """
    SSA v3 분석 코어 — 이미지 numpy 배열을 받아 분석 보고서 생성.

    Args:
        img: OpenCV BGR 이미지 (numpy array)
        detail: "auto" | "quick" | "full"
        orig_w, orig_h: 원본 해상도 (resize 전)

    Returns:
        마크다운 형식의 분석 보고서
    """
    orig_h = orig_h or img.shape[0]
    orig_w = orig_w or img.shape[1]

    h, w, _ = img.shape
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    lines = []
    lines.append("### SYSTEM_VISION_REPORT_V3")
    lines.append(f"- Original Resolution: {orig_w}x{orig_h} ({(orig_w * orig_h) / 1e6:.1f}MP)")
    lines.append(f"- Analysis Scaled: {w}x{h}")

    # === 1. Spatial Grid (8x8) ===
    g = 8
    ch, cw = h // g, w // g
    rows = []
    grid_data = []  # for summary
    for r in range(g):
        row = []
        for c in range(g):
            y1, y2 = r * ch, (r + 1) * ch
            x1, x2 = c * cw, (c + 1) * cw
            cell = gray[y1:y2, x1:x2]
            cell_hsv = hsv[y1:y2, x1:x2]
            avg_v = int(np.mean(cell_hsv[:, :, 2]))
            lap = cv2.Laplacian(cell, cv2.CV_64F).var()
            tex = "R" if lap > 350 else "S"
            if avg_v < 40:
                col = "Black"
            else:
                ah = int(np.mean(cell_hsv[:, :, 0]))
                if ah < 10 or ah > 170:
                    col = "Red"
                elif ah < 25:
                    col = "Orange"
                elif ah < 35:
                    col = "Yellow"
                elif ah < 85:
                    col = "Green"
                elif ah < 130:
                    col = "Blue"
                else:
                    col = "Purple"
            row.append(f"{col}({tex})")
        rows.append(row)
        grid_data.append(row)

    lines.append("\n### 8x8 Grid")
    lines.append("| Y\\X | " + " | ".join([f"X{i}" for i in range(g)]) + " |")
    lines.append("|---|" + "|---" * g + "|")
    for r in range(g):
        lines.append(f"| Y{r} | " + " | ".join(rows[r]) + " |")

    # === 2. GrabCut 객체 분할 ===
    fg_pct = 0
    shape_desc = "unknown"
    h_pos = v_pos = "center"
    bx = by = bw = bh = 0
    orig_scale = orig_w / w

    try:
        mask = np.zeros(img.shape[:2], np.uint8)
        bgd = np.zeros((1, 65), np.float64)
        fgd = np.zeros((1, 65), np.float64)
        rect = (w // 8, h // 8, w * 3 // 4, h * 3 // 4)
        cv2.grabCut(img, mask, rect, bgd, fgd, 3, cv2.GC_INIT_WITH_RECT)
        fg_mask = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 1, 0).astype(np.uint8)
        fg_pct = np.sum(fg_mask) / (h * w) * 100

        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest = max(contours, key=cv2.contourArea)
            bx, by, bw, bh = cv2.boundingRect(largest)
            cx, cy = bx + bw // 2, by + bh // 2
            v_pos = "top" if cy < h // 3 else "bottom" if cy > 2 * h // 3 else "center"
            h_pos = "left" if cx < w // 3 else "right" if cx > 2 * w // 3 else "center"
            aspect = bw / bh if bh > 0 else 0
            if aspect > 1.5:
                shape_desc = "horizontal/wide"
            elif aspect < 0.66:
                shape_desc = "vertical/tall"
            else:
                shape_desc = "near-square"

            lines.append(f"\n### Object Detection (GrabCut)")
            lines.append(f"- Foreground: {fg_pct:.0f}% of image")
            lines.append(f"- Main object: {int(bw * orig_scale)}x{int(bh * orig_scale)}px at ({h_pos},{v_pos}), shape={shape_desc}")
            lines.append(f"- Position: center={(cx / w * 100):.0f}%H,{(cy / h * 100):.0f}%V")
    except Exception:
        lines.append(f"\n### Object Detection: unavailable")

    # === 3. k-means Dominant Colors ===
    pixels = img.reshape(-1, 3).astype(np.float32)
    k = 4
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

    color_counts = Counter(labels.flatten())

    lines.append("\n### Color Composition")
    dominant_colors = []
    for label_id, count in color_counts.most_common(k):
        bgr = centers[int(label_id)]
        name = _bgr_to_name(bgr)
        pct = count / len(labels) * 100
        bars = "█" * int(pct / 2.5)
        lines.append(f"- {name}: {pct:.0f}% {bars}")
        dominant_colors.append((name, pct))

    # === 4. Median Cut 색상 양자화 (full 모드에서만) ===
    if detail != "quick":
        try:
            def median_cut(img_flat, depth=4):
                if depth == 0 or len(img_flat) < 16:
                    avg = np.mean(img_flat, axis=0).astype(int)
                    return [avg]
                ranges = [np.max(img_flat[:, i]) - np.min(img_flat[:, i]) for i in range(3)]
                channel = np.argmax(ranges)
                sorted_idx = np.argsort(img_flat[:, channel])
                split = len(sorted_idx) // 2
                left = median_cut(img_flat[sorted_idx[:split]], depth - 1)
                right = median_cut(img_flat[sorted_idx[split:]], depth - 1)
                return left + right

            mc_colors = median_cut(pixels[:min(len(pixels), 10000)], 4)
            mc_colors = mc_colors[:8]
            lines.append(f"\n### Dominant Colors (Median Cut)")
            for c in mc_colors[:4]:
                name = _bgr_to_name(c)
                lines.append(f"- {name} ({c[2]},{c[1]},{c[0]})")
        except Exception:
            pass

    # === 5. LBP Texture ===
    uniform_pct = 0
    tex_type = "unknown"
    try:
        def local_binary_pattern(img_grayscale, P=8, R=1):
            hh, ww = img_grayscale.shape
            lbp = np.zeros_like(img_grayscale)
            center = img_grayscale[R:hh - R, R:ww - R]
            for k in range(P):
                angle = 2 * np.pi * k / P
                xx = R * np.cos(angle)
                yy = -R * np.sin(angle)
                x1, y1 = int(np.floor(xx)), int(np.floor(yy))
                neighbor = img_grayscale[R + y1:R + y1 + hh - 2 * R, R + x1:R + x1 + ww - 2 * R]
                # Ensure same shape
                nh, nw = neighbor.shape
                ch, cw = center.shape
                if nh != ch or nw != cw:
                    neighbor = neighbor[:ch, :cw]
                lbp[:ch, :cw] += (neighbor >= center[:ch, :cw]) * (1 << k)
            return lbp

        lbp_img = local_binary_pattern(gray)
        hist = cv2.calcHist([lbp_img.astype(np.uint8)], [0], None, [256], [0, 256])
        total_hist = np.sum(hist)
        uniform_pct = np.sum(hist[:32]) / total_hist * 100 if total_hist > 0 else 0

        if uniform_pct > 70:
            tex_type = "Very uniform (solid/smooth)"
        elif uniform_pct > 40:
            tex_type = "Moderately textured"
        elif uniform_pct > 20:
            tex_type = "Highly textured (complex)"
        else:
            tex_type = "Extremely detailed"

        lines.append(f"\n### Texture Analysis (LBP)")
        lines.append(f"- Uniformity: {uniform_pct:.0f}% — {tex_type}")
    except Exception:
        pass

    # === 6. Saliency Detection ===
    salient_pct = 0
    sh = sv = ""
    try:
        saliency = cv2.saliency.StaticSaliencySpectralResidual_create()
        _, saliency_map = saliency.computeSaliency(gray)
        saliency_map = (saliency_map * 255).astype(np.uint8)

        _, salient_binary = cv2.threshold(saliency_map, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        salient_pct = np.sum(salient_binary > 0) / (h * w) * 100

        salient_coords = np.where(salient_binary > 0)
        if len(salient_coords[0]) > 0:
            sy = int(np.mean(salient_coords[0]))
            sx = int(np.mean(salient_coords[1]))
            sv = "top" if sy < h // 3 else "center" if sy < 2 * h // 3 else "bottom"
            sh = "left" if sx < w // 3 else "center" if sx < 2 * w // 3 else "right"
            lines.append(f"\n### Visual Saliency")
            lines.append(f"- Salient area: {salient_pct:.0f}% of image")
            lines.append(f"- Focus: ({sh},{sv})")
    except Exception:
        pass

    # === 7. Histogram Comparison ===
    avg_sim = 0
    comp = "unknown"
    try:
        grid_similarity = []
        for r in range(g - 1):
            for c in range(g - 1):
                y1, y2 = r * ch, (r + 1) * ch
                x1, x2 = c * cw, (c + 1) * cw
                cell1 = hsv[y1:y2, x1:x2]
                x2_next = min(x2 + cw, w)
                if x2_next <= x2:
                    continue
                cell2 = hsv[y1:y2, x2:x2_next]
                if cell2.shape[1] < cw // 2:
                    continue
                hist1 = cv2.calcHist([cell1], [0], None, [30], [0, 180])
                hist2 = cv2.calcHist([cell2], [0], None, [30], [0, 180])
                cv2.normalize(hist1, hist1)
                cv2.normalize(hist2, hist2)
                sim = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
                grid_similarity.append(sim)
        if grid_similarity:
            avg_sim = float(np.mean(grid_similarity))
            if avg_sim > 0.7:
                comp = "Very uniform/repetitive"
            elif avg_sim > 0.4:
                comp = "Moderately varied"
            else:
                comp = "Highly varied/dynamic"
            lines.append(f"\n### Spatial Uniformity")
            lines.append(f"- Grid similarity: {avg_sim:.2f} — {comp}")
    except Exception:
        pass

    # === 8. Full 모드 추가 분석 ===
    if detail == "full":
        # 8a. 엣지 검출 (Canny)
        try:
            edges = cv2.Canny(gray, 50, 150)
            edge_pct = np.sum(edges > 0) / (h * w) * 100
            lines.append(f"\n### Edge Analysis")
            lines.append(f"- Edge density: {edge_pct:.1f}%")
            if edge_pct < 1:
                lines.append("- Very few edges (mostly solid colors/gradients)")
            elif edge_pct < 5:
                lines.append("- Moderate edges (some structure)")
            else:
                lines.append("- Rich edge detail (complex scene)")
        except Exception:
            pass

        # 8b. 밝기/채도 통계
        try:
            v_channel = hsv[:, :, 2]
            s_channel = hsv[:, :, 1]
            lines.append(f"\n### Luminance & Saturation")
            lines.append(f"- Brightness: mean={np.mean(v_channel):.0f}, std={np.std(v_channel):.0f}")
            lines.append(f"- Saturation: mean={np.mean(s_channel):.0f}, std={np.std(s_channel):.0f}")
            if np.mean(v_channel) > 180:
                lines.append("- Overall: Bright image")
            elif np.mean(v_channel) < 60:
                lines.append("- Overall: Dark image")
            else:
                lines.append("- Overall: Normal brightness")
        except Exception:
            pass

        # 8c. 히스토그램 피크 분석
        try:
            hist_b = cv2.calcHist([img], [0], None, [256], [0, 256])
            hist_g = cv2.calcHist([img], [1], None, [256], [0, 256])
            hist_r = cv2.calcHist([img], [2], None, [256], [0, 256])
            peak_b = int(np.argmax(hist_b))
            peak_g = int(np.argmax(hist_g))
            peak_r = int(np.argmax(hist_r))
            lines.append(f"\n### Histogram Peaks")
            lines.append(f"- Blue peak: {peak_b}, Green peak: {peak_g}, Red peak: {peak_r}")
        except Exception:
            pass

    # === 9. 자연어 요약 (항상 출력) ===
    lines.append("\n### AI Spatial Inference")
    main_color_name = dominant_colors[0][0] if dominant_colors else "unknown"
    main_pct = dominant_colors[0][1] if dominant_colors else 0
    lines.append(f"- Dominant color: {main_color_name} ({main_pct:.0f}%)")
    if salient_pct > 5:
        lines.append(f"- Visual focus: {salient_pct:.0f}% area at ({sh},{sv})")
    if fg_pct > 5:
        lines.append(f"- Object occupies: {fg_pct:.0f}% of frame")
    if avg_sim > 0:
        lines.append(f"- Scene type: {comp}")

    return "\n".join(lines)


# ── 자연어 요약 함수 ──────────────────────────────────

def _summarize_ssa_results(raw_report: str) -> str:
    """
    SSA 분석 결과(raw markdown)를 간결한 자연어로 요약.

    LLM이 빠르게 이해할 수 있도록 핵심 정보만 추출하여
    응축된 한글 요약문을 생성한다.
    """
    summary_parts = []
    
    # 해상도 추출
    import re
    m = re.search(r'Original Resolution: (\d+)x(\d+)', raw_report)
    if m:
        w, h = m.group(1), m.group(2)
        mp = f"{(int(w) * int(h)) / 1e6:.1f}MP"
        summary_parts.append(f"📐 {w}×{h} ({mp})")

    # 주 색상 추출
    m = re.search(r'Dominant color: (\w+) \((\d+)%\)', raw_report)
    if m:
        summary_parts.append(f"🎨 주색상={m.group(1)}({m.group(2)}%)")

    # 객체 추출
    m = re.search(r'Foreground: (\d+)%', raw_report)
    if m:
        summary_parts.append(f"📦 전경객체={m.group(1)}%")

    # 시각적 주목 영역
    m = re.search(r'Visual focus: ([\d.]+)% area at \((\w+),(\w+)\)', raw_report)
    if m:
        summary_parts.append(f"👀 주목영역={m.group(2)}-{m.group(3)}({m.group(1)}%)")

    # 질감
    m = re.search(r'Uniformity: ([\d.]+)% — (.+)', raw_report)
    if m:
        summary_parts.append(f"🧩 질감={m.group(2)}")

    # 공간 균일성
    m = re.search(r'Grid similarity: ([\d.]+) — (.+)', raw_report)
    if m:
        summary_parts.append(f"📊 공간균일성={m.group(2)}")

    if summary_parts:
        return "### SSA Quick Summary\n" + " · ".join(summary_parts) + "\n"
    return ""


# ── SSIM 분석 ────────────────────────────────────────

def _ssim_analyze(image_path1: str, image_path2: str = None) -> str:
    """
    SSIM(구조적 유사도) 분석. 두 이미지 비교.

    image_path2가 없으면 image_path1의 self-SSIM (블러/노이즈 감지).
    """
    if not _CV2_AVAILABLE:
        return "SSIM: OpenCV not available."

    img1 = _imread_korean_safe(image_path1)
    if img1 is None:
        return f"SSIM: Cannot read image: {image_path1}"

    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)

    if image_path2:
        img2 = _imread_korean_safe(image_path2)
        if img2 is None:
            return f"SSIM: Cannot read image: {image_path2}"
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

        # 크기 맞추기
        if gray1.shape != gray2.shape:
            gray2 = cv2.resize(gray2, (gray1.shape[1], gray1.shape[0]))
    else:
        # Self-SSIM: 원본 vs 가우시안 블러
        gray2 = cv2.GaussianBlur(gray1, (15, 15), 0)

    # 간단한 SSIM 구현 (scikit-image 의존성 없이)
    try:
        # 평균, 분산, 공분산
        mu1 = cv2.GaussianBlur(gray1, (11, 11), 1.5)
        mu2 = cv2.GaussianBlur(gray2, (11, 11), 1.5)

        mu1_sq = mu1 ** 2
        mu2_sq = mu2 ** 2
        mu12 = mu1 * mu2

        sigma1_sq = cv2.GaussianBlur(gray1 ** 2, (11, 11), 1.5) - mu1_sq
        sigma2_sq = cv2.GaussianBlur(gray2 ** 2, (11, 11), 1.5) - mu2_sq
        sigma12 = cv2.GaussianBlur(gray1 * gray2, (11, 11), 1.5) - mu12

        C1 = (0.01 * 255) ** 2
        C2 = (0.03 * 255) ** 2

        ssim_map = ((2 * mu12 + C1) * (2 * sigma12 + C2)) / \
                   ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))
        ssim_score = float(np.mean(ssim_map))
    except Exception:
        # Fallback: MSE 기반 간단 비교
        diff = cv2.absdiff(gray1, gray2)
        mse = np.mean(diff ** 2)
        ssim_score = 1.0 / (1.0 + mse / 10000.0)

    lines = ["### SSIM Analysis"]
    if image_path2:
        lines.append(f"- Image 1: {os.path.basename(image_path1)}")
        lines.append(f"- Image 2: {os.path.basename(image_path2)}")
    else:
        lines.append(f"- Image: {os.path.basename(image_path1)} (self-SSIM: original vs blurred)")

    lines.append(f"- SSIM: {ssim_score:.4f}")

    if ssim_score > 0.95:
        lines.append("- Verdict: Nearly identical (or already very smooth)")
    elif ssim_score > 0.85:
        lines.append("- Verdict: Very similar (minor differences)")
    elif ssim_score > 0.70:
        lines.append("- Verdict: Moderately similar (noticeable differences)")
    elif ssim_score > 0.50:
        lines.append("- Verdict: Low similarity (significant differences)")
    else:
        lines.append("- Verdict: Very different images")

    return "\n".join(lines)


# ── 도구 등록 ────────────────────────────────────────

# 이미지 드롭존 HTML (Webview 드롭존용)
_DROPZONE_HTML = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>VibeZoo Image Drop Zone</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #1e1e1e; color: #ccc; display: flex;
         justify-content: center; align-items: center; min-height: 100vh; }
  .container { text-align: center; padding: 40px; }
  .dropzone { border: 3px dashed #555; border-radius: 20px; padding: 60px 40px;
              margin: 20px 0; cursor: pointer; transition: all 0.3s; }
  .dropzone:hover, .dropzone.dragover { border-color: #4ec9ff; background: rgba(78,201,255,0.1); }
  .dropzone.has-image { border-color: #6acb6a; }
  .icon { font-size: 64px; margin-bottom: 20px; }
  .hint { color: #888; margin-top: 10px; font-size: 14px; }
  img.preview { max-width: 100%; max-height: 400px; border-radius: 8px;
                margin-top: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.5); }
  .status { margin-top: 15px; padding: 10px; border-radius: 8px; font-size: 14px; }
  .status.success { background: rgba(106,203,106,0.2); color: #6acb6a; }
  .status.error { background: rgba(255,107,107,0.2); color: #ff6b6b; }
  .btn { background: #4ec9ff; color: #1e1e1e; border: none; padding: 10px 24px;
         border-radius: 6px; font-size: 14px; cursor: pointer; margin-top: 15px; }
  .btn:hover { background: #3db8ee; }
</style>
</head>
<body>
<div class="container">
  <h2>📸 VibeZoo Image Drop Zone</h2>
  <p>Drop an image or screenshot here for SSA analysis</p>
  <div class="dropzone" id="dropzone">
    <div class="icon">📁</div>
    <p>Drag & drop an image here</p>
    <p class="hint">or click to browse</p>
    <input type="file" id="fileInput" accept="image/*" style="display:none">
  </div>
  <div id="previewArea"></div>
  <div id="statusArea"></div>
  <button class="btn" id="clearBtn" style="display:none">Clear & Upload Another</button>
</div>

<script>
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('fileInput');
  const previewArea = document.getElementById('previewArea');
  const statusArea = document.getElementById('statusArea');
  const clearBtn = document.getElementById('clearBtn');

  dropzone.addEventListener('click', () => fileInput.click());
  dropzone.addEventListener('dragover', (e) => { e.preventDefault(); dropzone.classList.add('dragover'); });
  dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
  dropzone.addEventListener('drop', (e) => { e.preventDefault(); dropzone.classList.remove('dragover');
    if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]); });
  fileInput.addEventListener('change', () => { if (fileInput.files.length) handleFile(fileInput.files[0]); });

  async function handleFile(file) {
    if (!file.type.startsWith('image/')) {
      showStatus('Please select an image file.', 'error'); return; }
    const reader = new FileReader();
    reader.onload = async (e) => {
      const dataUrl = e.target.result;
      previewArea.innerHTML = `<img src="${dataUrl}" class="preview" />`;
      dropzone.classList.add('has-image');
      showStatus('Uploading...', '');
      try {
        const resp = await fetch('/upload', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ image: dataUrl, filename: file.name })
        });
        const result = await resp.json();
        if (result.success) {
          showStatus('✅ Image uploaded! Path: ' + result.path, 'success');
          clearBtn.style.display = 'inline-block';
        } else {
          showStatus('❌ Upload failed: ' + (result.error || 'unknown'), 'error');
        }
      } catch (err) {
        showStatus('❌ Upload error: ' + err.message, 'error');
      }
    };
    reader.readAsDataURL(file);
  }

  function showStatus(msg, type) {
    statusArea.innerHTML = `<div class="status ${type}">${msg}</div>`; }

  clearBtn.addEventListener('click', () => {
    previewArea.innerHTML = '';
    statusArea.innerHTML = '';
    dropzone.classList.remove('has-image');
    clearBtn.style.display = 'none';
    fileInput.value = '';
  });
</script>
</body>
</html>"""


def register(mcp):
    """SSA 도구 등록"""

    @mcp.tool
    def aggregate_spatial_pixels(image_path: str, detail: str = "auto",
                                  ocr: bool = True, ocr_lang: str = "auto") -> str:
        """Statistical Spatial Aggregator v3 — 이미지를 공간 통계 매트릭스로 압축합니다.
        선택적으로 OCR 텍스트 추출을 포함합니다.

        Args:
            image_path: 분석할 이미지 파일 경로
            detail: 분석 상세도 ("auto", "quick", "full")
            ocr: OCR 텍스트 추출 여부 (기본 True, 미설치 시 조용히 스킵)
            ocr_lang: OCR 언어 ("auto", "eng", "kor", "chi_sim", "jpn")

        Returns:
            마크다운 형식의 이미지 분석 보고서 (SSA + OCR 통합)
        """
        if not _CV2_AVAILABLE:
            return (_markdown_header("SSA Error", "❌")
                    + "**OpenCV not installed.** Run: `pip install opencv-contrib-python-headless numpy`\n"
                    + _markdown_footer())

        if detail not in ("auto", "quick", "full"):
            detail = "auto"

        # ~ 경로 확장 (예: ~/.vibezoo-cache/dropped_image.png)
        image_path = os.path.expanduser(image_path)

        try:
            # 한글 경로 지원: cv2.imread 대신 cv2.imdecode 사용
            img_raw = _imread_korean_safe(image_path)
            if img_raw is None:
                return (_markdown_header("SSA Error", "❌")
                        + f"**Cannot read image:** `{image_path}`\n"
                        + "Try: check file path (Korean characters?) or file format.\n"
                        + _markdown_footer())

            orig_h, orig_w = img_raw.shape[:2]

            # detail="auto" 처리
            if detail == "auto":
                file_size = os.path.getsize(image_path) if os.path.exists(image_path) else 0
                if file_size > 2 * 1024 * 1024:  # > 2MB
                    detail = "quick"
                elif file_size > 500 * 1024:  # > 500KB
                    detail = "quick" if (orig_w * orig_h) > 2_000_000 else "full"
                elif (orig_w * orig_h) > 4_000_000:  # > 4MP
                    detail = "quick"
                elif (orig_w * orig_h) < 300_000:  # < 0.3MP
                    detail = "full"
                else:
                    detail = "full"

            # 리사이즈
            target_w = 640
            target_h = int(orig_h * (target_w / orig_w))
            img = cv2.resize(img_raw, (target_w, target_h))

            # 분석 실행
            report = _analyze_image(img, detail=detail, orig_w=orig_w, orig_h=orig_h)

            # 파일명 추가
            fname = os.path.basename(image_path)
            header = f"### SYSTEM_VISION_REPORT_V3: {fname}\n"
            lines = report.split('\n')
            if lines and lines[0].startswith("### SYSTEM_VISION_REPORT_V3"):
                lines[0] = f"### SYSTEM_VISION_REPORT_V3: {fname}"
            report = '\n'.join(lines)

            # 자연어 요약 추가
            summary = _summarize_ssa_results(report)
            if summary:
                report = summary + "\n" + report

            # ── OCR 통합 ─────────────────────────────────
            ocr_section = ""
            ocr_blocks_count = 0
            ocr_engine_name = "none"
            if ocr:
                try:
                    from bridge.ocr_engine import OcrEngine
                    ocr_engine = OcrEngine()
                    if ocr_engine.is_available():
                        ocr_result = ocr_engine.ocr(image_path, lang=ocr_lang, detail=detail)
                        ocr_engine_name = ocr_result.get("engine", "none")
                        if ocr_result.get("text", "").strip():
                            ocr_section = _format_ocr_section(ocr_result, img.shape)
                            ocr_blocks_count = len(ocr_result.get("blocks", [])) or ocr_result.get("stats", {}).get("word_count", 0)
                            # SSA 자연어 요약에 OCR 정보 추가
                            summary_line = f"📝 OCR: {ocr_result['stats']['word_count']} words detected ({ocr_engine_name})"
                            if summary:
                                summary += " · " + summary_line
                            else:
                                summary = "### SSA Quick Summary\n" + summary_line + "\n"
                                report = summary + "\n" + report
                        # OCR 결과가 있어도 섹션은 항상 추가 (빈 결과도 표시)
                        if not ocr_section:
                            ocr_section = _format_ocr_section(ocr_result, img.shape)
                    else:
                        ocr_section = ("\n### OCR\n"
                                       "- ⚠️ OCR not available. Install Tesseract: "
                                       "`pip install pytesseract` + system package, "
                                       "or `pip install paddleocr`\n")
                except ImportError:
                    ocr_section = ("\n### OCR\n"
                                   "- ⚠️ OCR module not loaded. Run `vibezoo_setup()` to install.\n")
                except Exception:
                    # OCR 실패 시 조용히 스킵 (에러 아님)
                    pass

            if ocr_section:
                report += ocr_section

            try_crow_ingest(f"SSA v3 analyze: {fname} ({orig_w}x{orig_h}, detail={detail}, ocr={ocr_engine_name}, text_blocks={ocr_blocks_count})",
                            register="context")
            return report

        except Exception as e:
            return (_markdown_header("SSA Error", "❌")
                    + f"**Analysis failed:** {e}\n" + _markdown_footer())

# ── OCR 결과 포맷팅 ──────────────────────────────────


def _format_ocr_section(ocr_result: dict, img_shape: tuple) -> str:
    """OCR 결과를 마크다운 섹션으로 포맷팅.

    Args:
        ocr_result: ``OcrEngine.ocr()`` 반환값
        img_shape: OpenCV 이미지 shape (h, w, ...)

    Returns:
        "### OCR Text Extraction" 섹션 마크다운
    """
    lines = []
    engine = ocr_result.get("engine", "none")

    lines.append(f"\n### OCR Text Extraction")

    if ocr_result.get("text", "").strip():
        text = ocr_result["text"]
        lines.append(f"- **Engine**: {engine}")
        lines.append(f"- **Language**: {ocr_result.get('language', 'auto')}")

        stats = ocr_result.get("stats", {})
        lines.append(f"- **Words**: {stats.get('word_count', 0)}")
        lines.append(f"- **Lines**: {stats.get('line_count', 0)}")

        blocks = ocr_result.get("blocks", [])
        if blocks:
            avg_conf = sum(b.get("confidence", 0) for b in blocks) / max(len(blocks), 1)
            lines.append(f"- **Blocks**: {len(blocks)}")
            lines.append(f"- **Avg Confidence**: {avg_conf:.0f}%")

            # 상위 블록 테이블
            top_blocks = sorted(blocks, key=lambda b: -b.get("confidence", 0))[:10]
            h, w = img_shape[:2]
            lines.append("\n| # | Text | Conf | Position | Size |")
            lines.append("|---|------|------|----------|------|")
            for i, b in enumerate(top_blocks, 1):
                t = b.get("text", "")[:50]
                if len(b.get("text", "")) > 50:
                    t += "…"
                lines.append(
                    f"| {i} | {t} | {b.get('confidence', 0):.0f}% "
                    f"| {b.get('position', '?')} | {b.get('size', '?')} |"
                )

        # 전체 텍스트 (접을 수 있게)
        lines.append(f"\n<details>\n<summary>Full extracted text ({len(text)} chars)</summary>\n\n```\n{text[:2000]}\n```\n</details>")
    else:
        lines.append(f"- **Engine**: {engine}")
        if ocr_result.get("text") is not None:
            lines.append("- No text detected in image.")
        else:
            lines.append("- OCR not performed.")

    return "\n".join(lines)
