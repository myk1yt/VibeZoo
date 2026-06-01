#!/usr/bin/env python
import sys, os, re
BASE = r'c:\Users\k1yt\OneDrive\문서\각종자료\공부자료들\파이썬_Python\VibeZoo_forZoocode'
wb = os.path.join(BASE, 'mcp-servers', 'bridge', 'tools', 'whiteboard.py')
with open(wb, 'r', encoding='utf-8') as f:
    c = f.read()
old = 'async function handleFile(file){if(!file)return;if(!file.type.startsWith('"'"'image/'"'"')){showStatus('"'"'Not an image file'"'"','"'"'error'"'"');return}\nconst form=new FormData();form.append('"'"'image'"'"',file);\ntry{const r=await fetch('"'"'/upload'"'"',{method:'"'"'POST'"'"',body:form});const t=await r.text();showStatus('"'"'Uploaded! Use aggregate_spatial_pixels() to analyze.'"'"','"'"'success'"'"');preview.src=URL.createObjectURL(file);preview.style.display='"'"'block'"'"';dz.classList.add('"'"'has-image'"'"')}\ncatch(e){showStatus('"'"'Upload failed. Save manually to ~/.vibezoo-cache/dropped_image.png'"'"','"'"'error'"'"')}}'
print(f'old found: {old in c}')
