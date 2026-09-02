"""Python 3.11 py_compile sweep over bridge/**/*.py in both repo trees,
plus the deployed extension tree under %USERPROFILE%\\mcp-servers\\vibezoo.

Usage: venv python (3.11) _fstring311_verify.py
Prints PASS/FAIL per file; exit code 0 iff all pass.
"""
import glob
import os
import py_compile
import sys

ROOTS = [
    os.path.join("mcp-servers", "bridge"),
    os.path.join("extension", "mcp-servers", "bridge"),
    os.path.join(os.path.expanduser("~"), "mcp-servers", "vibezoo",
                 "extension", "mcp-servers", "bridge"),
    os.path.join(os.path.expanduser("~"), "mcp-servers", "vibezoo",
                 "mcp-servers", "bridge"),
]

files = []
for root in ROOTS:
    files.extend(sorted(glob.glob(os.path.join(root, "**", "*.py"), recursive=True)))

print("Python:", sys.version.split()[0])
print("Files to compile:", len(files))

fails = []
for f in files:
    try:
        py_compile.compile(f, doraise=True)
        print(f"PASS {f}")
    except py_compile.PyCompileError as e:
        fails.append((f, str(e)))
        print(f"FAIL {f}\n     {e}")

print()
print(f"Result: {len(files) - len(fails)}/{len(files)} pass, {len(fails)} fail")
if fails:
    for f, e in fails:
        print(f"FAILED: {f}")
    sys.exit(1)
print("ALL 3.11 py_compile PASS")