# VibeZoo Initialization Guide

To initialize VibeZoo upon cloning:

1. **Start MCP Bridge Server**: Run `python mcp-servers/vibezoo_mcp_bridge.py` in background (`WaitMsBeforeAsync=5000`).
2. **Register Server**: Add to `.zoo/mcp.json`:
   `{"mcpServers":{"vibezoo-bridge":{"url":"http://127.0.0.1:9027/mcp"}}}`
3. **Run Setup Tool**: Use `vibezoo_setup(target="full")` to install Python dependencies and download models.
4. **Build UI**: Run `cd extension && npm install && npx tsc`.

Notify user when ready.
