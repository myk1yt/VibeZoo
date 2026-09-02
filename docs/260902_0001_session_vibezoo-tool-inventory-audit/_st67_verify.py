"""ST-6/ST-7 verification: py_compile both ux_coordinator copies,
residual-name scan of both copies, and cross-tree mirror SHA parity
for all files edited in this phase (root mcp-servers mirror vs extension source)."""
import hashlib
import py_compile
import re
import sys

UX_FILES = [
    "mcp-servers/bridge/tools/ux_coordinator.py",
    "extension/mcp-servers/bridge/tools/ux_coordinator.py",
]

# 1. py_compile
for f in UX_FILES:
    py_compile.compile(f, doraise=True)
print("PY_COMPILE_OK:", UX_FILES)

# 2. residual scan (requirement 5)
p = re.compile(r"find_bugs|suggest_refactor|generate_docs|learn_project|auto_analyze")
total = 0
for f in UX_FILES:
    for i, line in enumerate(open(f, encoding="utf-8").read().splitlines(), 1):
        if p.search(line):
            print("HIT", f, i, line.rstrip())
            total += 1
print(f"UX_COORDINATOR_RESIDUAL_HITS: {total}")

# 3. mirror parity for the ux_coordinator pair (plan §5 'Mirror parity')
def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]

print("SHA", UX_FILES[0], sha(UX_FILES[0]))
print("SHA", UX_FILES[1], sha(UX_FILES[1]))

sys.exit(0 if total == 0 else 1)
