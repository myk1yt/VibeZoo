import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

print("=== GIT STATUS FOR mcp-servers and extension/mcp-servers ===")
res = subprocess.run(['git', 'status', '--porcelain', 'mcp-servers', 'extension/mcp-servers'], capture_output=True, text=True, encoding='utf-8', errors='replace')
print(res.stdout)

print("\n=== GIT DIFF mcp-servers ===")
res_r = subprocess.run(['git', 'diff', 'mcp-servers'], capture_output=True, text=True, encoding='utf-8', errors='replace')
print(res_r.stdout if res_r.stdout else "No uncommitted modifications in root mcp-servers")

print("\n=== GIT DIFF extension/mcp-servers ===")
res_e = subprocess.run(['git', 'diff', 'extension/mcp-servers'], capture_output=True, text=True, encoding='utf-8', errors='replace')
print(res_e.stdout if res_e.stdout else "No uncommitted modifications in extension/mcp-servers")
