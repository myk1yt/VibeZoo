#!/usr/bin/env python
import sys
filepath = r'c:\Users\k1yt\OneDrive\문서\각종자료\공부자료들\파이썬_Python\VibeZoo_forZoocode\extension\src\visual\VisualVibePanels.ts'

# Read as raw bytes first
with open(filepath, 'rb') as f:
    raw = f.read()

print(f"Has CRLF: {b'\r\n' in raw}")
print(f"Has LF only: {b'\r\n' not in raw and b'\n' in raw}")

# Read as text
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Test if replacements work
old1 = "const UI_ACTION_FILE = () => path.join(os.homedir(), '.vibezoo-ui-action.json');\n\nconst FABRIC_CDN"
print(f"old1 in content: {old1 in content}")

old2 = "  private diagramPanel: vscode.WebviewPanel | null = null;\n  private readonly homedir: string;"
print(f"old2 in content: {old2 in content}")

# Do replacements
new1 = "const UI_ACTION_FILE = () => path.join(os.homedir(), '.vibezoo-ui-action.json');\n\nconst DROPZONE_CACHE_DIR = () => path.join(os.homedir(), '.vibezoo-cache');\nconst UPLOADED_IMAGE_PATH = () => path.join(DROPZONE_CACHE_DIR(), 'dropped_image.png');\n\nconst FABRIC_CDN"
new2 = "  private diagramPanel: vscode.WebviewPanel | null = null;\n  private dropzonePanel: vscode.WebviewPanel | null = null;\n  private readonly homedir: string;"

if old1 in content:
    content = content.replace(old1, new1, 1)
    print("1. Replaced constants")
if old2 in content:
    content = content.replace(old2, new2, 1)
    print("2. Replaced property")

# Write back
with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

# Verify
with open(filepath, 'r', encoding='utf-8') as f:
    verify = f.read()
print(f"DROPZONE_CACHE_DIR in verify: {'DROPZONE_CACHE_DIR' in verify}")
print(f"dropzonePanel in verify: {'dropzonePanel' in verify}")
print(f"Verify size: {len(verify)}")
