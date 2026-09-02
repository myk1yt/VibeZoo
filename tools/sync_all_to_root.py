import hashlib, os, shutil

files_to_sync = [
    'bridge/tools/__init__.py',
    'bridge/tools/analysis.py',
    'bridge/tools/integrated.py',
    'bridge/tool_context.py',
    'vibezoo_mcp_bridge.py',
    'tests/test_whiteboard_merge.py',
]

def sha256(path):
    if not os.path.exists(path):
        return None
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

print("=== Synchronizing extension/mcp-servers -> mcp-servers ===")
for f in files_to_sync:
    src = os.path.join('extension/mcp-servers', f)
    dst = os.path.join('mcp-servers', f)
    if os.path.exists(src):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        h1 = sha256(src)
        h2 = sha256(dst)
        print(f"Synced {f}: {'[OK] IDENTICAL' if h1 == h2 else '[FAIL] MISMATCH'}")
    else:
        print(f"Source missing: {src}")
