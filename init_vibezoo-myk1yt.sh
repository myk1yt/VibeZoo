#!/bin/bash
set -e

TARGET_DIR="$HOME/mcp-servers/vibezoo"
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "==================================================="
echo "  VibeZoo Universal UX Bootstrapper (Linux/macOS)"
echo "==================================================="
echo ""

echo "[1/6] Creating standard target directory..."
mkdir -p "$TARGET_DIR"

echo "[2/6] Copying startup scripts..."
cp "$REPO_DIR/extension/mcp-servers/start_vibezoo_bridge.bat" "$TARGET_DIR/" 2>/dev/null || true
# Note: start_vibezoo_bridge.bat is Windows-only; Linux uses direct python call

echo "[3/6] Copying Python bridge files..."
cp "$REPO_DIR/extension/mcp-servers/vibezoo_mcp_bridge.py" "$TARGET_DIR/"
cp "$REPO_DIR/extension/mcp-servers/crow_memory_server.py" "$TARGET_DIR/"
cp -r "$REPO_DIR/extension/mcp-servers/bridge" "$TARGET_DIR/"
cp -r "$REPO_DIR/extension/mcp-servers/tools" "$TARGET_DIR/"

echo "[4/6] Creating Python Virtual Environment..."
cd "$TARGET_DIR"
python3 -m venv venv

echo "[5/6] Installing Python Dependencies..."
source venv/bin/activate
pip install fastmcp starlette requests tree_sitter_languages

echo "[6/6] Building Frontend Extension..."
cd "$REPO_DIR/extension"
npm install
npx tsc

echo ""
echo "==================================================="
echo "  VibeZoo is ready!"
echo "==================================================="
echo ""
echo "Runtime directory: $TARGET_DIR"
echo ""
echo "Next steps:"
echo "1. Open VS Code or your MCP client."
echo "2. Install the VibeZoo VSIX from extension/."
echo "3. The init script has copied bridge files to $TARGET_DIR."
echo "4. Configure autoStartCommand in global MCP settings:"
echo "   cd ~/mcp-servers/vibezoo && python vibezoo_mcp_bridge.py --port 9027"
echo ""
