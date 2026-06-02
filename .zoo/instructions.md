# VibeZoo Initialization Guide for LLM Agents

You are currently inside the VibeZoo repository. If the user has just cloned this project and asks you to "install", "setup", or "initialize" VibeZoo, you **MUST** follow this exact sequence to break the Chicken-and-Egg problem.

## 1. Start the MCP Bridge Server
VibeZoo's advanced tools (like `vibezoo_setup` and `explore_github`) are provided via an MCP server that might not be running yet.
You must start it manually using your `run_command` tool.
Run this command in the background (e.g., WaitMsBeforeAsync=5000):
```bash
python mcp-servers/vibezoo_mcp_bridge.py
```

## 2. Register the MCP Server
Ensure that the VibeZoo MCP bridge is registered in the user's global MCP settings or local `.zoo/mcp.json`.
The bridge runs as an SSE server on `http://127.0.0.1:9027/sse`.
Example `.zoo/mcp.json` content:
```json
{
  "mcpServers": {
    "vibezoo-bridge": {
      "url": "http://127.0.0.1:9027/sse"
    }
  }
}
```

## 3. Run the Autonomous Setup Tool
Once the server is running and registered, the `vibezoo_setup` tool will become available to you.
Use the `vibezoo_setup` tool with the argument `target="full"` to automatically install Python packages (PyMuPDF, python-docx, paddlepaddle, etc.) and download the GGUF vision models (MiniCPM-V) from HuggingFace.

## 4. Build the Frontend (TypeScript UI)
VibeZoo requires its Webview UI (Dropzone, Diagram, Whiteboard) to be compiled so the VS Code Extension can display them.
Run the following command using your `run_command` tool:
```bash
cd extension && npm install && npx tsc
```

Once all 4 steps are complete, inform the user that VibeZoo is fully installed, built, and ready for use!
