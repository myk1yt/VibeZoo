#!/usr/bin/env python
"""Fix VisualVibePanels.ts: add dropzonePanel property and constants."""
import sys

filepath = r'c:\Users\k1yt\OneDrive\문서\각종자료\공부자료들\파이썬_Python\VibeZoo_forZoocode\extension\src\visual\VisualVibePanels.ts'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"File length: {len(content)}")

# 1. Add dropzone constants after UI_ACTION_FILE
old1 = "const UI_ACTION_FILE = () => path.join(os.homedir(), '.vibezoo-ui-action.json');\n\nconst FABRIC_CDN"
new1 = "const UI_ACTION_FILE = () => path.join(os.homedir(), '.vibezoo-ui-action.json');\n\nconst DROPZONE_CACHE_DIR = () => path.join(os.homedir(), '.vibezoo-cache');\nconst UPLOADED_IMAGE_PATH = () => path.join(DROPZONE_CACHE_DIR(), 'dropped_image.png');\n\nconst FABRIC_CDN"

if old1 in content:
    content = content.replace(old1, new1, 1)
    print("1. Constants added successfully")
else:
    print("1. FAILED: Could not find target string for constants")
    # Debug: find the actual text around that area
    idx = content.find('UI_ACTION_FILE')
    if idx >= 0:
        print(f"   Found UI_ACTION_FILE at {idx}")
        print(f"   Context: {repr(content[idx:idx+100])}")

# 2. Add dropzonePanel property
old2 = "  private diagramPanel: vscode.WebviewPanel | null = null;\n  private readonly homedir: string;"
new2 = "  private diagramPanel: vscode.WebviewPanel | null = null;\n  private dropzonePanel: vscode.WebviewPanel | null = null;\n  private readonly homedir: string;"

if old2 in content:
    content = content.replace(old2, new2, 1)
    print("2. Property added successfully")
else:
    print("2. FAILED: Could not find target string for property")
    idx = content.find('diagramPanel')
    if idx >= 0:
        print(f"   Found diagramPanel at {idx}")
        print(f"   Context: {repr(content[idx:idx+120])}")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("File written successfully")
