import os
import sys
import json
import hashlib
import ast
import difflib
import subprocess

sys.stdout.reconfigure(encoding='utf-8')

def parse_py_file(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        code = f.read()
    
    info = {
        'version': None,
        'tools': {},
        'functions': {},
        'classes': {},
        'imports': []
    }
    try:
        tree = ast.parse(code, filename=path)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                is_tool = False
                for dec in node.decorator_list:
                    dstr = ast.unparse(dec) if hasattr(ast, 'unparse') else ''
                    if 'tool' in dstr:
                        is_tool = True
                doc = ast.get_docstring(node) or ''
                sig = {
                    'name': node.name,
                    'args': [a.arg for a in node.args.args],
                    'is_async': isinstance(node, ast.AsyncFunctionDef),
                    'lineno': node.lineno,
                    'doc': doc.strip().splitlines()[0] if doc else ''
                }
                if is_tool:
                    info['tools'][node.name] = sig
                else:
                    info['functions'][node.name] = sig
            elif isinstance(node, ast.ClassDef):
                methods = [m.name for m in node.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]
                info['classes'][node.name] = {
                    'name': node.name,
                    'methods': methods,
                    'lineno': node.lineno
                }
            elif isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name) and t.id == 'VERSION':
                        if isinstance(node.value, ast.Constant):
                            info['version'] = node.value.value
    except Exception as e:
        info['error'] = str(e)
    return info

# Let's inspect all 21 different files in detail
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

print(f"Total different files: {len(diff_files)}")

for rel in diff_files:
    r_path = f"mcp-servers/{rel}"
    e_path = f"extension/mcp-servers/{rel}"

    with open(r_path, 'r', encoding='utf-8', errors='ignore') as f:
        r_text = f.read()
    with open(e_path, 'r', encoding='utf-8', errors='ignore') as f:
        e_text = f.read()

    r_parsed = parse_py_file(r_path)
    e_parsed = parse_py_file(e_path)

    r_tools = set(r_parsed['tools'].keys())
    e_tools = set(e_parsed['tools'].keys())
    
    r_funcs = set(r_parsed['functions'].keys())
    e_funcs = set(e_parsed['functions'].keys())

    r_classes = set(r_parsed['classes'].keys())
    e_classes = set(e_parsed['classes'].keys())

    diff_lines = list(difflib.unified_diff(
        r_text.splitlines(),
        e_text.splitlines(),
        fromfile=r_path,
        tofile=e_path,
        lineterm=''
    ))

    print(f"\n==================== {rel} ====================")
    print(f"Root: {len(r_text)} bytes, {len(r_text.splitlines())} lines | Version: {r_parsed['version']}")
    print(f"Ext : {len(e_text)} bytes, {len(e_text.splitlines())} lines | Version: {e_parsed['version']}")
    
    if r_tools != e_tools:
        print(f"  * TOOLS DIFF: Root only: {r_tools - e_tools} | Ext only: {e_tools - r_tools}")
    else:
        print(f"  * TOOLS MATCH: {len(r_tools)} tools ({', '.join(sorted(r_tools)) if r_tools else 'None'})")

    if r_funcs != e_funcs:
        print(f"  * FUNCS DIFF: Root only: {r_funcs - e_funcs} | Ext only: {e_funcs - r_funcs}")
    
    if r_classes != e_classes:
        print(f"  * CLASSES DIFF: Root only: {r_classes - e_classes} | Ext only: {e_classes - r_classes}")

    # Print summary of unified diff changes
    added_lines = [l for l in diff_lines if l.startswith('+') and not l.startswith('+++')]
    removed_lines = [l for l in diff_lines if l.startswith('-') and not l.startswith('---')]
    print(f"  Unified diff: -{len(removed_lines)} lines, +{len(added_lines)} lines")
    
    # Check if there are unique features in root
    print("  First 10 diff lines:")
    for l in diff_lines[:15]:
        print("   ", l[:120])
