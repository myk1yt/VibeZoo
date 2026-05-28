import re
import os

with open('mcp-servers/vibezoo_mcp_bridge.py', 'r', encoding='utf-8') as f:
    content = f.read()

atomic_func = """
import tempfile
import json

def _atomic_write_json(file_path: str, data: dict, indent: int = 2):
    base_dir = os.path.dirname(file_path)
    if not base_dir:
        base_dir = os.getcwd()
    os.makedirs(base_dir, exist_ok=True)
    temp_fd, temp_file_path = tempfile.mkstemp(dir=base_dir, suffix=".vztmp")
    try:
        with os.fdopen(temp_fd, "w", encoding="utf-8") as temp_file:
            json.dump(data, temp_file, indent=indent, ensure_ascii=False)
        if hasattr(os, "sync"):
            os.sync()
        os.replace(temp_file_path, file_path)
    except Exception as write_error:
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        raise write_error
"""

if '_atomic_write_json' not in content:
    content = re.sub(r'(def _truncate.*?return.*?)(?=\n\n)', r'\1\n\n' + atomic_func, content, flags=re.DOTALL)

pattern = re.compile(r'with open\(([^,]+),\s*"w"\)\s*as\s*[a-zA-Z0-9_]+:\s*\n\s*json\.dump\(([^,]+),\s*[a-zA-Z0-9_]+(.*?)\)', re.MULTILINE)

def replacer(match):
    file_path = match.group(1)
    data_var = match.group(2)
    args = match.group(3)
    indent_val = "2"
    if 'indent=' in args:
        indent_match = re.search(r'indent=(\d+)', args)
        if indent_match:
            indent_val = indent_match.group(1)
    return f"_atomic_write_json({file_path}, {data_var}, indent={indent_val})"

content = pattern.sub(replacer, content)

with open('mcp-servers/vibezoo_mcp_bridge.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Bridge updated successfully')
