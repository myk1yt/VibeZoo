import os, filecmp, shutil

def sync_mirrors():
    root_base = 'mcp-servers'
    ext_base = 'extension/mcp-servers'
    
    # Check all files in extension/mcp-servers and compare with mcp-servers
    diffs = []
    for dirpath, dirnames, filenames in os.walk(ext_base):
        if '__pycache__' in dirpath or '.pytest_cache' in dirpath:
            continue
        rel_dir = os.path.relpath(dirpath, ext_base)
        root_dir = os.path.join(root_base, rel_dir) if rel_dir != '.' else root_base
        for fn in filenames:
            if fn.endswith('.pyc'):
                continue
            ext_f = os.path.join(dirpath, fn)
            root_f = os.path.join(root_dir, fn)
            rel_f = os.path.relpath(ext_f, ext_base)
            if not os.path.exists(root_f):
                print(f"File missing in root: {rel_f} -> copying to root")
                os.makedirs(root_dir, exist_ok=True)
                shutil.copy2(ext_f, root_f)
            elif not filecmp.cmp(ext_f, root_f, shallow=False):
                print(f"Difference found: {rel_f}")
                diffs.append(rel_f)
                
    print(f"Total differences found: {len(diffs)}")
    return diffs

if __name__ == '__main__':
    sync_mirrors()
