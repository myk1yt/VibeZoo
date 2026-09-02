import hashlib

with open('mcp-servers/tools/analyzer.py', 'rb') as f1:
    h1 = hashlib.sha256(f1.read()).hexdigest()

with open('extension/mcp-servers/tools/analyzer.py', 'rb') as f2:
    h2 = hashlib.sha256(f2.read()).hexdigest()

print("mcp-servers/tools/analyzer.py sha256:", h1)
print("extension/mcp-servers/tools/analyzer.py sha256:", h2)
print("Identical?", h1 == h2)
