import os
import hashlib
import json
import time
import subprocess
import ast

def get_file_info(filepath):
    st = os.stat(filepath)
    with open(filepath, 'rb') as f:
        content = f.read()
    sha = hashlib.sha256(content).hexdigest()
    try:
        text = content.decode('utf-8')
        line_count = len(text.splitlines())
    except Exception:
        line_count = -1
    return {
        'size': st.st_size,
        'mtime': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(st.st_mtime)),
        'mtime_ts': st.st_mtime,
        'sha256': sha,
        'line_count': line_count
    }

def scan_dir(base_dir):
    res = {}
    if not os.path.exists(base_dir):
        return res
    for root, dirs, files in os.walk(base_dir):
        if '__pycache__' in root:
            continue
        for f in files:
            if f.endswith('.pyc'):
                continue
            full = os.path.join(root, f)
            rel = os.path.relpath(full, base_dir).replace('\\', '/')
            info = get_file_info(full)
            info['rel_path'] = rel
            info['full_path'] = full.replace('\\', '/')
            res[rel] = info
    return res

def extract_py_symbols(filepath):
    symbols = {'functions': [], 'classes': [], 'tools': [], 'version': None, 'imports': []}
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()
        tree = ast.parse(code, filename=filepath)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check decorators for mcp.tool
                is_tool = False
                for dec in node.decorator_list:
                    if isinstance(dec, ast.Attribute) and dec.attr == 'tool':
                        is_tool = True
                    elif isinstance(dec, ast.Call):
                        if isinstance(dec.func, ast.Attribute) and dec.func.attr == 'tool':
                            is_tool = True
                if is_tool:
                    symbols['tools'].append(node.name)
                else:
                    symbols['functions'].append(node.name)
            elif isinstance(node, ast.ClassDef):
                symbols['classes'].append(node.name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == 'VERSION':
                        if isinstance(node.value, ast.Constant):
                            symbols['version'] = node.value.value
    except Exception as e:
        symbols['error'] = str(e)
    return symbols

def main():
    root_dir = 'mcp-servers'
    ext_dir = 'extension/mcp-servers'

    root_files = scan_dir(root_dir)
    ext_files = scan_dir(ext_dir)

    root_keys = set(root_files.keys())
    ext_keys = set(ext_files.keys())

    root_only = sorted(list(root_keys - ext_keys))
    ext_only = sorted(list(ext_keys - root_keys))
    common = sorted(list(root_keys & ext_keys))

    identical = []
    different = []

    diff_details = {}

    for k in common:
        rf = root_files[k]
        ef = ext_files[k]
        if rf['sha256'] == ef['sha256']:
            identical.append(k)
        else:
            different.append(k)
            # Analyze diff
            r_full = os.path.join(root_dir, k)
            e_full = os.path.join(ext_dir, k)
            
            # git diff / compare
            r_sym = extract_py_symbols(r_full) if k.endswith('.py') else {}
            e_sym = extract_py_symbols(e_full) if k.endswith('.py') else {}

            diff_details[k] = {
                'root_size': rf['size'],
                'ext_size': ef['size'],
                'root_lines': rf['line_count'],
                'ext_lines': ef['line_count'],
                'root_mtime': rf['mtime'],
                'ext_mtime': ef['mtime'],
                'mtime_winner': 'ext' if ef['mtime_ts'] > rf['mtime_ts'] else ('root' if rf['mtime_ts'] > ef['mtime_ts'] else 'equal'),
                'root_version': r_sym.get('version'),
                'ext_version': e_sym.get('version'),
                'root_tools': r_sym.get('tools', []),
                'ext_tools': e_sym.get('tools', []),
                'root_only_tools': list(set(r_sym.get('tools', [])) - set(e_sym.get('tools', []))),
                'ext_only_tools': list(set(e_sym.get('tools', [])) - set(r_sym.get('tools', []))),
                'root_only_funcs': list(set(r_sym.get('functions', [])) - set(e_sym.get('functions', []))),
                'ext_only_funcs': list(set(e_sym.get('functions', [])) - set(r_sym.get('functions', []))),
                'root_only_classes': list(set(r_sym.get('classes', [])) - set(e_sym.get('classes', []))),
                'ext_only_classes': list(set(e_sym.get('classes', [])) - set(r_sym.get('classes', []))),
            }

    # Git status check
    try:
        git_st = subprocess.check_output(['git', 'status', '--porcelain', 'mcp-servers', 'extension/mcp-servers'], text=True)
    except Exception as e:
        git_st = str(e)

    # Git log check
    git_logs = {}
    for k in common:
        try:
            r_log = subprocess.check_output(['git', 'log', '-n', '1', '--format=%h | %cd | %s', '--', f'mcp-servers/{k}'], text=True).strip()
        except Exception:
            r_log = ''
        try:
            e_log = subprocess.check_output(['git', 'log', '-n', '1', '--format=%h | %cd | %s', '--', f'extension/mcp-servers/{k}'], text=True).strip()
        except Exception:
            e_log = ''
        git_logs[k] = {'root_log': r_log, 'ext_log': e_log}

    out = {
        'summary': {
            'root_total': len(root_files),
            'ext_total': len(ext_files),
            'root_only_count': len(root_only),
            'ext_only_count': len(ext_only),
            'identical_count': len(identical),
            'different_count': len(different)
        },
        'root_only': root_only,
        'ext_only': ext_only,
        'identical': identical,
        'different': different,
        'diff_details': diff_details,
        'git_status': git_st,
        'git_logs': git_logs,
        'root_files': root_files,
        'ext_files': ext_files
    }

    out_path = 'docs/260830_0001_session_reinstall-recovery-and-quality/tools/inventory_data.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"Scan complete. Output written to {out_path}")
    print(json.dumps(out['summary'], indent=2))

if __name__ == '__main__':
    main()
