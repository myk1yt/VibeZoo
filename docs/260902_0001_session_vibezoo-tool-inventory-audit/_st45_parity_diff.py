# -*- coding: utf-8 -*-
"""Characterize root-vs-extension drift for edited files (line-level unified diff)."""
import difflib
import io

PAIRS = [
    ("mcp-servers/bridge/tools/integrated.py", "extension/mcp-servers/bridge/tools/integrated.py"),
    ("mcp-servers/bridge/tools/knowledge.py", "extension/mcp-servers/bridge/tools/knowledge.py"),
]

for a, b in PAIRS:
    la = io.open(a, encoding="utf-8").readlines()
    lb = io.open(b, encoding="utf-8").readlines()
    d = list(difflib.unified_diff(la, lb, fromfile=a, tofile=b, n=1))
    print("=== %s vs %s : %d diff lines ===" % (a, b, len(d)))
    out = "".join(d[:120])
    print(out if out else "(no line-level differences)")
    if len(d) > 120:
        print("... (%d more diff lines)" % (len(d) - 120))
    print()