import os, sys

root = r'c:/Users/k1yt/OneDrive/문서/각종자료/공부자료들/파이썬_Python/VibeZoo_forZoocode/mcp-servers'
bridge = os.path.join(root, 'vibezoo_mcp_bridge.py')
orig = os.path.join(root, 'vibezoo_mcp_bridge_ORIG.py')

print(f"Reading ORIG: {orig}")
with open(orig, 'r', encoding='utf-8') as f:
    content = f.read()
print(f"Read {len(content)} chars, {len(content.splitlines())} lines")

# Upgrade search_codebase signature
old_sig = 'def search_codebase(query: str, file_patterns: Optional[str] = None, max_results: int = 10) -> str:'
new_sig = 'def search_codebase(query: str, file_patterns: Optional[str] = None, max_results: int = 10, mode: str = "auto", context_lines: int = 3) -> str:'

if old_sig in content:
    content = content.replace(old_sig, new_sig)
    print("search_codebase signature upgraded")
else:
    print("WARNING: old signature not found!")
    idx = content.find('def search_codebase')
    if idx >= 0:
        print(f"Found at {idx}: {content[idx:idx+120]}")

# Validate syntax
try:
    compile(content, bridge, 'exec')
    print("Syntax: OK")
except SyntaxError as e:
    print(f"Syntax error: {e}")
    sys.exit(1)

# Atomic write
print(f"Writing {len(content)} chars atomically...")
tmp = bridge + '.tmp'
with open(tmp, 'w', encoding='utf-8') as f:
    f.write(content)
os.replace(tmp, bridge)
print("Write complete!")

# Verify
with open(bridge, 'r', encoding='utf-8') as f:
    verify = f.read()
print(f"Verified: {len(verify)} chars, {len(verify.splitlines())} lines")
print(f"First line: {verify.splitlines()[0][:80]}")
