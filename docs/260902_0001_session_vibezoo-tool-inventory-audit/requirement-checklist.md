# Requirement Checklist
## Task: VibeZoo Tool Inventory Audit (count tools + identify unnecessary ones)
## Date: 260902

- [ ] [REQ-001] Count the total number of tools currently exposed by the VibeZoo MCP bridge server (including tools registered in `mcp-servers/vibezoo_mcp_bridge.py` and per-tool modules under [`mcp-servers/bridge/tools/`](mcp-servers/bridge/tools/__init__.py:1))
- [ ] [REQ-002] For each tool, record: name, purpose, source file, registration location
- [ ] [REQ-003] Identify redundancy candidates — overlapping functionality, deprecated tools, unused/never-referenced tools (e.g., check for deprecated wrappers like `auto_analyze_whiteboard`)
- [ ] [REQ-004] Classify each tool as KEEP / REVIEW / REMOVE-candidate with evidence (cross-reference usage in extension code, docs, plans)
- [ ] [REQ-005] Produce a written report with the full inventory table and cleanup recommendations for the user's decision (read-only analysis — NO code modification)

## Constraints
- Read-only analysis. No tool removal in this session; user decides after seeing the report.