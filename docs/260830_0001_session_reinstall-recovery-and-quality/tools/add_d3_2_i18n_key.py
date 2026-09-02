# -*- coding: utf-8 -*-
"""Add D3-2 vision fallback i18n key to all 20 translation files."""
import json
import os
import sys

TRANS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..",
                         "mcp-servers", "bridge", "i18n", "translations")

# The i18n key (English)
NEW_KEY = (
    "\u26a0\ufe0f MiniCPM vision model is not installed or failed to load. "
    "Image: {0}. Alternatives: (1) Paste image into Dropzone (Ctrl+V) "
    "\u2014 file path copied as Markdown to clipboard for AI chat. "
    "(2) See README Vision section for model setup."
)

# Korean translation
KO_VALUE = (
    "\u26a0\ufe0f MiniCPM \ube44\uc804 \ubaa8\ub378\uc774 \uc124\uce58\ub418\uc9c0 "
    "\uc54a\uc73c\uc2dc\uacfc \ud655 \ub85c\ub4dc\uc5d0 \uc2e4\ud328\ud588\uc2b5\ub2c8\ub2e4. "
    "\uc774\ubbf8\uc9c0: {0}. "
    "\ub300\uc548: (1) \uc774\ubbf8\uc9c0\ub97c \ub450\ud3ec\uc9c0\ub294(Ctrl+V)\uc5d0 "
    "\ubd99\uc5ec\ub120\ub824\uba74 \ud30c\uc77c \uacbd\ub85c\uac00 \ud074\ub9bd\ubcf4\ub4dc\uc5d0 "
    "\ub9c8\ud06c\ub370\uc778\uc73c\ub85c \ubcf5\uc0ac\ub418\uc5b4 AI \ub300\ud654\uc5d0 "
    "\ubd99\uc5ec\ub120\ub824 \uc0ac\uc6a9\ud560 \uc218 \uc788\uc2b5\ub2c8\ub2e4. "
    "(2) \ubaa8\ub378 \uc124\uc815\uc774 \ud544\uc694\ud558\uba74 "
    "README\uc758 Vision \uc139\uc744 \ucc38\uc870\ud558\uc138\uc694."
)

# English value = key itself
EN_VALUE = NEW_KEY

added_count = 0
skipped_count = 0

for fname in sorted(os.listdir(TRANS_DIR)):
    if not fname.endswith(".json") or fname == "en.json":
        continue
    fpath = os.path.join(TRANS_DIR, fname)
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
    if NEW_KEY not in data:
        if fname == "ko.json":
            data[NEW_KEY] = KO_VALUE
        else:
            data[NEW_KEY] = EN_VALUE
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"  ADDED  -> {fname}")
        added_count += 1
    else:
        print(f"  SKIP   -> {fname} (already present)")
        skipped_count += 1

print(f"\nSummary: {added_count} added, {skipped_count} skipped")
