import os
import sys
import difflib

sys.stdout.reconfigure(encoding='utf-8')

diff_files = [
    "bridge/config.py",
    "bridge/tools/_base.py",
    "bridge/tools/analysis.py",
    "bridge/tools/deep_analyzer.py",
    "bridge/tools/editor.py",
    "bridge/tools/feedback.py",
    "bridge/tools/file_analyzer.py",
    "bridge/tools/fix_loop.py",
    "bridge/tools/github_diver.py",
    "bridge/tools/integrated.py",
    "bridge/tools/knowledge.py",
    "bridge/tools/reviewer.py",
    "bridge/tools/scout.py",
    "bridge/tools/setup.py",
    "bridge/tools/ssa.py",
    "bridge/tools/tester.py",
    "bridge/tools/ux_coordinator.py",
    "bridge/tools/web.py",
    "bridge/tools/whiteboard.py",
    "crow_memory_server.py",
    "vibezoo_mcp_bridge.py"
]

for rel in diff_files:
    r_path = f"mcp-servers/{rel}"
    e_path = f"extension/mcp-servers/{rel}"
    with open(r_path, 'r', encoding='utf-8', errors='ignore') as f:
        r_lines = f.readlines()
    with open(e_path, 'r', encoding='utf-8', errors='ignore') as f:
        e_lines = f.readlines()
    
    diff = list(difflib.unified_diff(r_lines, e_lines, fromfile=r_path, tofile=e_path))
    
    print(f"\n==========================================")
    print(f"DIFF FOR {rel} (Total diff lines: {len(diff)})")
    print(f"==========================================")
    for line in diff:
        print(line, end='')
