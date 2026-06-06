# VibeZoo MCP Bridge Merge Plan

> Based on Research Analysis | 2026-06-02

## Decision: Keep v1 Modular Architecture, Archive v2

v1(`0.14.1`) is superior to v2(`0.12.0`) in every aspect:
- More recent version (0.14.1 > 0.12.0)
- No 7 ghost tools
- Supports capture_screen source parameter
- Advanced features like WhiteboardDataConverter, IntentDetector

## Action Plan

| Phase | Task | File | Description |
|-------|------|------|-------------|
| 1 | Move v2 to archive | `vibezoo_mcp_bridge_v2.py` → `_archive/vibezoo_mcp_bridge_v2.py` | No longer in use |
| 2 | Update Extension | [`SubagentManager.ts`](extension/src/orchestra/SubagentManager.ts) | Change reference from `_v2.py` → `.py` |
| 3 | Update v1 bridge capture_screen (already completed) | [`whiteboard.py`](mcp-servers/bridge/tools/whiteboard.py) | source parameter support, includes `check_uploaded_files` tool |
| 4 | Delete old VSIX files | `extension/vibezoo-*.vsix` | Remove all old VSIX versions |
| 5 | VSIX build + install | — | Reflect modified Extension code |
| 6 | GitHub commit + push | — | Keep v0.14.1 |

> This plan will be implemented immediately in Code mode.
