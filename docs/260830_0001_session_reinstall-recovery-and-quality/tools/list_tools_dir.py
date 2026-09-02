import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

r_tools = sorted(os.listdir('mcp-servers/bridge/tools'))
e_tools = sorted(os.listdir('extension/mcp-servers/bridge/tools'))

print("mcp-servers/bridge/tools files (", len(r_tools), "):", r_tools)
print("extension/mcp-servers/bridge/tools files (", len(e_tools), "):", e_tools)
