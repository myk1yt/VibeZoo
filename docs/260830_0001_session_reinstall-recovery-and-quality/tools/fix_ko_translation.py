# -*- coding: utf-8 -*-
"""Fix ko.json D3-2 key with correct Korean text."""
import json
import os, sys
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

TRANS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..",
                         "mcp-servers", "bridge", "i18n", "translations")

NEW_KEY = (
    "\u26a0\ufe0f MiniCPM vision model is not installed or failed to load. "
    "Image: {0}. Alternatives: (1) Paste image into Dropzone (Ctrl+V) "
    "\u2014 file path copied as Markdown to clipboard for AI chat. "
    "(2) See README Vision section for model setup."
)

# Read the correct Korean text from a separate file to avoid encoding issues
# Use: write_to_file to create ko_correct_text.txt first
txt_path = os.path.join(os.path.dirname(__file__), "ko_correct_text.txt")
if os.path.exists(txt_path):
    with open(txt_path, "r", encoding="utf-8") as f:
        CORRECTED_KO = f.read().strip()
else:
    print(f"ERROR: {txt_path} not found. Create it first.")
    sys.exit(1)

fpath = os.path.join(TRANS_DIR, "ko.json")
with open(fpath, "r", encoding="utf-8") as f:
    data = json.load(f)

if NEW_KEY in data:
    old_val = data[NEW_KEY]
    data[NEW_KEY] = CORRECTED_KO
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"Fixed ko.json D3-2 key")
    # Verify substrings
    with open(fpath, "r", encoding="utf-8") as f:
        v = json.load(f)[NEW_KEY]
    checks = {
        "dropzone": "드롭존" in v,
        "clipboard": "클립보드" in v,
        "markdown": "마크다운" in v,
        "image_path_placeholder": "{0}" in v,
    }
    for k, ok in checks.items():
        print(f"  {k}: {'PASS' if ok else 'FAIL'}")
    if not all(checks.values()):
        print(f"  VALUE: {v}")
        sys.exit(1)
else:
    print("Key not found in ko.json!")
    sys.exit(1)
