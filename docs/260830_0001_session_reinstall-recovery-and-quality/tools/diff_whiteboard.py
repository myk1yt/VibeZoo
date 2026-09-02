import sys
import difflib

sys.stdout.reconfigure(encoding='utf-8')

with open("mcp-servers/bridge/tools/whiteboard.py", "r", encoding="utf-8") as f:
    r_lines = f.readlines()
with open("extension/mcp-servers/bridge/tools/whiteboard.py", "r", encoding="utf-8") as f:
    e_lines = f.readlines()

diff = list(difflib.unified_diff(r_lines, e_lines, fromfile="root whiteboard.py", tofile="ext whiteboard.py"))
for l in diff:
    print(l, end="")
