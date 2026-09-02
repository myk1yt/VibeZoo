"""ST-6: remove 4 dead command title keys from package.nls*.json (excluding -myk1yt fork copies).

Flat-file line-surgical removal: each key occupies exactly one line
("<key>": "<value>"), so deleting those lines preserves all other formatting,
BOM, encoding, and line endings. Post-verify with json.load.
"""
import glob
import io
import json
import os
import re

KEYS = (
    "vibezoo.findBugs.title",
    "vibezoo.suggestRefactor.title",
    "vibezoo.generateDocs.title",
    "vibezoo.learnProject.title",
)
PATTERN = re.compile(
    r'^\s*"(?:' + "|".join(re.escape(k) for k in KEYS) + r')"\s*:'
)

EXT_DIR = os.path.join("d:", os.sep, "OneDrive", "Projects", "VibeZoo", "extension")
files = sorted(glob.glob(os.path.join(EXT_DIR, "package.nls*.json")))
targets = [f for f in files if "-myk1yt" not in os.path.basename(f)]

report = {}
for path in targets:
    with open(path, "rb") as fh:
        raw = fh.read()
    has_bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig") if has_bom else raw.decode("utf-8")
    newline = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(newline)
    kept, removed = [], []
    for line in lines:
        if PATTERN.match(line):
            removed.append(line.strip())
        else:
            kept.append(line)
    if not removed:
        report[os.path.basename(path)] = []
        continue
    out = newline.join(kept)
    data = out.encode("utf-8")
    if has_bom:
        data = b"\xef\xbb\xbf" + data
    with open(path, "wb") as fh:
        fh.write(data)
    # validity check
    with open(path, "rb") as fh:
        body = fh.read()
    json.loads(body.decode("utf-8-sig"))
    report[os.path.basename(path)] = removed

skipped = [os.path.basename(f) for f in files if "-myk1yt" in os.path.basename(f)]
print(f"Edited {sum(1 for v in report.values() if v)}/{len(targets)} files")
for name, removed in report.items():
    if removed:
        print(f"  {name}: removed {len(removed)} keys")
        for r in removed:
            print(f"    {r}")
    else:
        print(f"  {name}: no matching keys")
print(f"Skipped (myk1yt fork copies): {len(skipped)}")
# residual check
residual = 0
for path in targets:
    with open(path, "rb") as fh:
        body = fh.read().decode("utf-8-sig")
    for k in KEYS:
        if f'"{k}"' in body:
            print(f"RESIDUAL {os.path.basename(path)}: {k}")
            residual += 1
print(f"Residual key occurrences: {residual}")
