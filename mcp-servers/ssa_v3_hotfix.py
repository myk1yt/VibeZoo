#!/usr/bin/env python
# SSA v3 Hotfix: IndexError, saliency deps, resize optimization, coord projection
import os, sys, re

BRIDGE = r'c:/Users/k1yt/OneDrive/문서/각종자료/공부자료들/파이썬_Python/VibeZoo_forZoocode/mcp-servers/vibezoo_mcp_bridge.py'

print("📖 Reading bridge...")
with open(BRIDGE, 'r', encoding='utf-8') as f:
    content = f.read()
print(f"   Current: {len(content)} chars")

# Fix 1: IndexError - color_counts.most_common(1)[1] -> [0][1]
old_idx = 'color_counts.most_common(1)[1]*100//len(labels)'
new_idx = 'color_counts.most_common(1)[0][1]*100//len(labels)'
if old_idx in content:
    content = content.replace(old_idx, new_idx)
    print("✅ Fix 1: IndexError fixed ([1]→[0][1])")
else:
    print("⚠️ Fix 1: Already fixed or not found")

# Fix 2: Install message - add opencv-contrib
old_install_msg = 'pip install opencv-python-headless numpy'
new_install_msg = 'pip install opencv-contrib-python-headless numpy'
if old_install_msg in content:
    content = content.replace(old_install_msg, new_install_msg)
    print("✅ Fix 2: Install message updated (contrib)")
else:
    print("⚠️ Fix 2: Already fixed or not found")

# Fix 3: Resize + coordinate projection
# Find the function body start
body_marker = 'try:\n        img = cv2.imread(image_path)'
resize_code = '''try:
        img_raw = cv2.imread(image_path)
        if img_raw is None:
            return (_markdown_header("SSA Error", "❌")
                    + f"**Cannot read image:** `{image_path}`\\n" + _markdown_footer())
        
        orig_h, orig_w, _ = img_raw.shape
        
        # [PERFORMANCE] 내부 연산용 이미지를 640px로 리사이즈 (원본 형태 보존, 속도 20배)
        target_w = 640
        target_h = int(orig_h * (target_w / orig_w))
        img = cv2.resize(img_raw, (target_w, target_h))
        
        h, w, _ = img.shape
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        orig_scale = orig_w / target_w
        
        lines = []
        fname = os.path.basename(image_path) if 'os' in dir() else image_path.split('/')[-1]
        lines.append(f"### SYSTEM_VISION_REPORT_V3: {fname}")
        lines.append(f"- Original Resolution: {orig_w}x{orig_h} ({(orig_w*orig_h)/1e6:.1f}MP)")
        lines.append(f"- Analysis Scaled: {w}x{h} ({(orig_w*orig_h)/(target_w*target_h):.0f}x speedup)")
        
        # === 1. Spatial Grid'''

old_body = '''try:
        img = cv2.imread(image_path)
        if img is None:
            return (_markdown_header("SSA Error", "❌")
                    + f"**Cannot read image:** `{image_path}`\\n" + _markdown_footer())
        
        h, w, _ = img.shape
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        lines = []
        fname = os.path.basename(image_path) if 'os' in dir() else image_path.split('/')[-1]
        lines.append(f"### SYSTEM_VISION_REPORT: {fname}")
        lines.append(f"- Resolution: {w}x{h} ({(w*h)/1e6:.1f}MP)")
        
        g = 8'''

if old_body in content:
    content = content.replace(old_body, resize_code, 1)
    print("✅ Fix 3: Resize + coord projection added")
elif body_marker in content:
    # Try alternate match
    content = content.replace(body_marker, resize_code, 1)
    print("✅ Fix 3: Applied via alternate match")
else:
    print("⚠️ Fix 3: Body marker not found, trying end section")
    # Try to find the old section and replace
    for pattern in ['try:\\n        img_raw = cv2.imread', 'try:\\n        img = cv2.imread']:
        if pattern in content:
            print(f"   Found alternate: {pattern}")

# Also fix the GrabCut coordinate to add orig_scale projection
old_grabcut_line1 = 'lines.append(f"- Main object: {bw}x{bh}px at ({h_pos},{v_pos}), shape={shape}")'
new_grabcut_line1 = 'lines.append(f"- Main object: {int(bw*orig_scale)}x{int(bh*orig_scale)}px at ({h_pos},{v_pos}), shape={shape}")'
if old_grabcut_line1 in content:
    content = content.replace(old_grabcut_line1, new_grabcut_line1)
    print("✅ Fix 4: GrabCut coord projection added")

# Verify syntax
try:
    compile(content, BRIDGE, 'exec')
    print("✅ Syntax: OK")
except SyntaxError as e:
    print(f"❌ Syntax error at line {e.lineno}: {e.msg}")
    lines = content.split('\\n')
    if e.lineno:
        for i in range(max(0, e.lineno-3), min(len(lines), e.lineno+2)):
            print(f"  {i+1}: {lines[i][:100]}")
    sys.exit(1)

# Atomic write
tmp = BRIDGE + '.hotfix'
with open(tmp, 'w', encoding='utf-8') as f:
    f.write(content)
os.replace(tmp, BRIDGE)
print(f"✅ Written: {len(content)} chars")

# Verify
with open(BRIDGE, 'r', encoding='utf-8') as f:
    final = f.read()
print(f"   IndexError fix: {'[0][1]' in final}")
print(f"   Contrib msg: {'contrib' in final}")
print(f"   Resize: {'640' in final and 'img_raw' in final}")
print(f"   Coord projection: {'orig_scale' in final}")
print("✅ SSA v3 hotfix complete!")
