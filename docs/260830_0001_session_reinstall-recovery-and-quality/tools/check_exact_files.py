import os
import sys
import json
import hashlib
import ast
import difflib
import subprocess

sys.stdout.reconfigure(encoding='utf-8')

def get_files_tree(base_dir, ignore_dirs=['__pycache__', '.pytest_cache']):
    files = {}
    for root, dirs, filenames in os.walk(base_dir):
        # filter ignore_dirs
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for f in filenames:
            if f.endswith('.pyc'):
                continue
            full = os.path.join(root, f)
            rel = os.path.relpath(full, base_dir).replace('\\', '/')
            st = os.stat(full)
            with open(full, 'rb') as fp:
                data = fp.read()
            sha = hashlib.sha256(data).hexdigest()
            try:
                text = data.decode('utf-8')
                lines = text.splitlines()
            except Exception:
                text = ""
                lines = []
            files[rel] = {
                'size': st.st_size,
                'mtime': st.st_mtime,
                'sha256': sha,
                'lines': len(lines),
                'text': text,
                'full': full.replace('\\', '/')
            }
    return files

root_f = get_files_tree('mcp-servers')
ext_f = get_files_tree('extension/mcp-servers')

print(f"Excluding caches:")
print(f"Root files count: {len(root_f)}")
print(f"Ext  files count: {len(ext_f)}")

root_set = set(root_f.keys())
ext_set = set(ext_f.keys())

root_only = sorted(list(root_set - ext_set))
ext_only = sorted(list(ext_set - root_set))
common = sorted(list(root_set & ext_set))

print(f"Root unique files: {root_only}")
print(f"Ext  unique files: {ext_only}")
print(f"Common files count: {len(common)}")

diff_list = []
ident_list = []

for k in common:
    if root_f[k]['sha256'] == ext_f[k]['sha256']:
        ident_list.append(k)
    else:
        diff_list.append(k)

print(f"Identical count: {len(ident_list)}")
print(f"Different count: {len(diff_list)}")
print("\n--- DIFFERENT FILES ---")
for k in diff_list:
    r = root_f[k]
    e = ext_f[k]
    print(f"{k}:")
    print(f"  Root: {r['size']} B, {r['lines']} L, sha={r['sha256'][:8]}")
    print(f"  Ext : {e['size']} B, {e['lines']} L, sha={e['sha256'][:8]}")
