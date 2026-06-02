#!/bin/bash
set -e

echo "==================================================="
echo "  VibeZoo Universal UX Bootstrapper (Linux/macOS)"
echo "==================================================="
echo ""

echo "[1/3] Creating Python Virtual Environment..."
python3 -m venv venv

echo "[2/3] Installing Python Requirements..."
source venv/bin/activate
pip install -r requirements.txt

echo "[3/3] Building Frontend Extension..."
cd extension
npm install
npx tsc
cd ..

echo ""
echo "==================================================="
echo "  VibeZoo is ready!"
echo "==================================================="
echo "Next steps:"
echo "1. Open VS Code or your MCP client."
echo "2. Run the agent and it will auto-bootstrap using .zoo/Agent.md guidelines."
echo "3. The agent can configure your mcp.json settings for you!"
echo ""
