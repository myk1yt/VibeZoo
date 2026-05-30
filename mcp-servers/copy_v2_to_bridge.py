# Copy v2 content to bridge using Python atomic write
import os, shutil

root = r'c:/Users/k1yt/OneDrive/문서/각종자료/공부자료들/파이썬_Python/VibeZoo_forZoocode/mcp-servers'
v2 = os.path.join(root, 'vibezoo_mcp_bridge_v2.py')
bridge = os.path.join(root, 'vibezoo_mcp_bridge.py')

# Read v2
with open(v2, 'r', encoding='utf-8') as f:
    content = f.read()

# Atomic write: temp + os.replace
tmp = bridge + '.v2tmp'
with open(tmp, 'w', encoding='utf-8') as f:
    f.write(content)
os.replace(tmp, bridge)

# Verify
import ast
ast.parse(content)
size = os.path.getsize(bridge)
lines = content.count('\n') + 1
print(f'Bridge updated: {size}B, {lines} lines')
print('Syntax OK')

# Check for Phase 2 content
has_phase2 = '_find_cycles_iterative' in content
has_phase3 = '참조 타입' in content or 'read/write' in content
has_grade = 'A-F' in content or 'Grade' in content
print(f'Phase 2: {has_phase2}')
print(f'Phase 3: {has_phase3}')
print(f'Quality Grade: {has_grade}')
