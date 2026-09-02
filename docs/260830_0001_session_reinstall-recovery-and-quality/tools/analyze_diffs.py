import os
import hashlib
import json
import time
import subprocess
import difflib
import ast
import glob

def get_file_info(filepath):
    st = os.stat(filepath)
    with open(filepath, 'rb') as f:
        content = f.read()
    sha = hashlib.sha256(content).hexdigest()
    try:
        text = content.decode('utf-8')
        lines = text.splitlines()
        line_count = len(lines)
    except Exception:
        text = None
        lines = []
        line_count = -1
    return {
        'size': st.st_size,
        'mtime': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(st.st_mtime)),
        'mtime_ts': st.st_mtime,
        'sha256': sha,
        'line_count': line_count,
        'text': text,
        'lines': lines
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

def parse_ast_details(code, filename):
    details = {
        'version': None,
        'tools': {},
        'functions': {},
        'classes': {},
        'imports': []
    }
    try:
        tree = ast.parse(code, filename=filename)
    except Exception as e:
        details['parse_error'] = str(e)
        return details

    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            details['imports'].append(ast.unparse(node) if hasattr(ast, 'unparse') else str(type(node)))
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == 'VERSION':
                    if isinstance(node.value, ast.Constant):
                        details['version'] = node.value.value
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            is_tool = False
            for dec in node.decorator_list:
                dec_str = ast.unparse(dec) if hasattr(ast, 'unparse') else ''
                if 'tool' in dec_str:
                    is_tool = True
            doc = ast.get_docstring(node) or ''
            func_sig = {
                'name': node.name,
                'args': [a.arg for a in node.args.args],
                'doc': doc[:100],
                'is_async': isinstance(node, ast.AsyncFunctionDef)
            }
            if is_tool:
                details['tools'][node.name] = func_sig
            else:
                details['functions'][node.name] = func_sig
        elif isinstance(node, ast.ClassDef):
            methods = [m.name for m in node.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]
            details['classes'][node.name] = {
                'name': node.name,
                'methods': methods,
                'doc': (ast.get_docstring(node) or '')[:100]
            }
    return details

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

    diff_analyses = {}

    for k in common:
        rf = root_files[k]
        ef = ext_files[k]
        if rf['sha256'] == ef['sha256']:
            identical.append(k)
        else:
            different.append(k)
            # Unified diff
            r_lines = rf['lines']
            e_lines = ef['lines']
            diff_lines = list(difflib.unified_diff(
                r_lines, e_lines,
                fromfile=f"mcp-servers/{k}",
                tofile=f"extension/mcp-servers/{k}",
                lineterm=''
            ))

            # AST comparison if Python
            r_ast = parse_ast_details(rf['text'], f"mcp-servers/{k}") if k.endswith('.py') and rf['text'] else {}
            e_ast = parse_ast_details(ef['text'], f"extension/mcp-servers/{k}") if k.endswith('.py') and ef['text'] else {}

            # Check git history
            try:
                r_git = subprocess.check_output(['git', 'log', '-n', '1', '--format=%h | %ad | %s', '--date=iso', '--', f'mcp-servers/{k}'], encoding='utf-8', errors='replace').strip()
            except Exception:
                r_git = ''
            try:
                e_git = subprocess.check_output(['git', 'log', '-n', '1', '--format=%h | %ad | %s', '--date=iso', '--', f'extension/mcp-servers/{k}'], encoding='utf-8', errors='replace').strip()
            except Exception:
                e_git = ''

            # Tool/Function/Class differences
            r_tools = set(r_ast.get('tools', {}).keys())
            e_tools = set(e_ast.get('tools', {}).keys())

            r_funcs = set(r_ast.get('functions', {}).keys())
            e_funcs = set(e_ast.get('functions', {}).keys())

            r_classes = set(r_ast.get('classes', {}).keys())
            e_classes = set(e_ast.get('classes', {}).keys())

            diff_analyses[k] = {
                'root_size': rf['size'],
                'ext_size': ef['size'],
                'root_lines': rf['line_count'],
                'ext_lines': ef['line_count'],
                'root_mtime': rf['mtime'],
                'ext_mtime': ef['mtime'],
                'root_git': r_git,
                'ext_git': e_git,
                'root_version': r_ast.get('version'),
                'ext_version': e_ast.get('version'),
                'root_tools': sorted(list(r_tools)),
                'ext_tools': sorted(list(e_tools)),
                'root_only_tools': sorted(list(r_tools - e_tools)),
                'ext_only_tools': sorted(list(e_tools - r_tools)),
                'root_only_funcs': sorted(list(r_funcs - e_funcs)),
                'ext_only_funcs': sorted(list(e_funcs - r_funcs)),
                'root_only_classes': sorted(list(r_classes - e_classes)),
                'ext_only_classes': sorted(list(e_classes - r_classes)),
                'diff_line_count': len(diff_lines),
                'diff_sample': diff_lines[:40]
            }

    # Search config files for mcp references
    config_refs = []
    # 1. search .roo/
    for p in glob.glob('.roo/**', recursive=True):
        if os.path.isfile(p):
            try:
                with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                    content = fp.read()
                    if 'mcp-server' in content or 'vibezoo' in content or 'start_vibezoo' in content:
                        config_refs.append({'path': p, 'type': 'workspace_config'})
            except Exception:
                pass

    # 2. search extension/src
    for p in glob.glob('extension/src/**', recursive=True):
        if os.path.isfile(p) and (p.endswith('.ts') or p.endswith('.json')):
            try:
                with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                    content = fp.read()
                    if 'mcp-servers' in content or 'start_vibezoo' in content or 'vibezoo_mcp_bridge' in content:
                        config_refs.append({'path': p, 'type': 'extension_src'})
            except Exception:
                pass

    # 3. scripts in workspace
    for s in ['init_vibezoo.bat', 'init_vibezoo.sh', 'package.json']:
        if os.path.exists(s):
            try:
                with open(s, 'r', encoding='utf-8', errors='ignore') as fp:
                    content = fp.read()
                    if 'mcp-server' in content or 'vibezoo' in content:
                        config_refs.append({'path': s, 'type': 'workspace_script'})
            except Exception:
                pass

    # 4. Global MCP config locations on Windows
    userprofile = os.environ.get('USERPROFILE', '')
    appdata = os.environ.get('APPDATA', '')
    localappdata = os.environ.get('LOCALAPPDATA', '')

    global_paths = [
        os.path.join(userprofile, '.roo', 'mcp.json'),
        os.path.join(userprofile, '.codeium', 'windsurf', 'mcp_config.json'),
        os.path.join(userprofile, '.cursor', 'mcp.json'),
        os.path.join(appdata, 'Code', 'User', 'globalStorage', 'rooveterinaryinc.roo-cline', 'settings', 'mcp_settings.json'),
        os.path.join(appdata, 'Code', 'User', 'globalStorage', 'saoudrizwan.claude-dev', 'settings', 'mcp_settings.json'),
        os.path.join(appdata, 'Cursor', 'User', 'globalStorage', 'rooveterinaryinc.roo-cline', 'settings', 'mcp_settings.json'),
    ]

    global_mcp_findings = []
    for gp in global_paths:
        if os.path.exists(gp):
            try:
                with open(gp, 'r', encoding='utf-8', errors='ignore') as fp:
                    c = fp.read()
                    global_mcp_findings.append({
                        'path': gp,
                        'exists': True,
                        'size': len(c),
                        'has_vibezoo': 'vibezoo' in c or 'mcp-servers' in c,
                        'content_preview': c[:500]
                    })
            except Exception as e:
                global_mcp_findings.append({'path': gp, 'exists': True, 'error': str(e)})
        else:
            global_mcp_findings.append({'path': gp, 'exists': False})

    # Git working tree status
    git_status_full = subprocess.check_output(['git', 'status', '-s'], encoding='utf-8', errors='replace')
    git_diff_root = subprocess.check_output(['git', 'diff', 'mcp-servers'], encoding='utf-8', errors='replace')
    git_diff_ext = subprocess.check_output(['git', 'diff', 'extension/mcp-servers'], encoding='utf-8', errors='replace')

    analysis_out = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'summary': {
            'root_total_files': len(root_files),
            'ext_total_files': len(ext_files),
            'root_only_files': root_only,
            'ext_only_files': ext_only,
            'identical_count': len(identical),
            'different_count': len(different)
        },
        'root_only_details': {k: {key: root_files[k][key] for key in ['size', 'mtime', 'sha256', 'line_count']} for k in root_only},
        'ext_only_details': {k: {key: ext_files[k][key] for key in ['size', 'mtime', 'sha256', 'line_count']} for k in ext_only},
        'identical_files': identical,
        'different_analyses': diff_analyses,
        'config_references': config_refs,
        'global_mcp_findings': global_mcp_findings,
        'git_status_mcp': [line for line in git_status_full.splitlines() if 'mcp-servers' in line],
        'git_diff_root_summary': f"{len(git_diff_root.splitlines())} lines modified" if git_diff_root else "clean",
        'git_diff_ext_summary': f"{len(git_diff_ext.splitlines())} lines modified" if git_diff_ext else "clean",
        'all_root_files': {k: {key: root_files[k][key] for key in ['size', 'mtime', 'sha256', 'line_count']} for k in sorted(root_files.keys())},
        'all_ext_files': {k: {key: ext_files[k][key] for key in ['size', 'mtime', 'sha256', 'line_count']} for k in sorted(ext_files.keys())}
    }

    out_file = 'docs/260830_0001_session_reinstall-recovery-and-quality/tools/detailed_diff_analysis.json'
    with open(out_file, 'w', encoding='utf-8') as fp:
        json.dump(analysis_out, fp, indent=2, ensure_ascii=False)
    print(f"Analysis saved to {out_file}")

if __name__ == '__main__':
    main()
