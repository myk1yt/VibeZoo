<project_architecture>

# VibeZoo — Core Architecture (Read-Only)

## Identity
- **Name**: VibeZoo
- **Version**: 0.15.1 (extension), 0.16.0 (bridge)
- **Publisher**: local (VS Code marketplace)
- **License**: MIT
- **Repository**: https://github.com/vibezoo/vibezoo

## Tech Stack

### Extension (TypeScript)
- Runtime: VS Code Engine ^1.90.0, Node.js
- Language: TypeScript ES2022, CommonJS modules
- Single runtime dependency: `minimatch` ^10.2.5
- Build: `tsc -p ./` → `extension/out/`
- Package: `vsce package` → `.vsix`

### MCP Bridge (Python)
- Framework: FastMCP + uvicorn + starlette
- Transport: SSE on `http://127.0.0.1:9027/sse`
- HTTP client: `requests` (for Crow Memory)
- Optional: tree-sitter, Pillow, pytesseract, MiniCPM-V

### Crow Memory (External)
- Protocol: HTTP REST API on port 9020
- Endpoints: `/ingest`, `/recall`, `/health`
- Managed externally; VibeZoo only detects/spawns it

## 3-Tier Architecture

```
VS Code Extension (TypeScript, Node.js host)
    │
    ├── child_process.spawn() → MCP Bridge (Python, SSE :9027)
    ├── HTTP health check → Crow Memory (Python, REST :9020)
    └── File-based IPC ← Bridge writes JSON to ~/.vibezoo-*.json
         │
Zoo Code (MCP client) ──SSE──→ Bridge (:9027/sse)
Bridge ──HTTP REST──→ Crow Memory (:9020)
```

## Communication Methods

| Connection | Protocol | Port | Pattern |
|-----------|----------|------|---------|
| Extension → Bridge | HTTP health | 9027 | GET /health polling |
| Extension → Crow | HTTP health | 9020 | GET /health polling |
| Bridge → Crow | HTTP REST | 9020 | POST /ingest, GET /recall |
| Zoo Code → Bridge | SSE (MCP) | 9027 | MCP tool calls |
| Bridge → Extension | File watch | N/A | JSON in ~/.vibezoo-*.json |

## Extension Module Layers (activation order)

1. **Phase 0 Foundation**: directories, templates, Crow connection, StatusBar
2. **Wave 1 Flow**: BuildTaskProvider, BuildFeedback, ProjectDetector
3. **Wave 2 Safety**: YoctoManager, GuardGitManager, AutoBuildFix, GitStashManager
4. **Wave 3 Context**: ContextIndicator, ExplainLessSuggestor, SessionResume, EmotionalDetector
5. **Wave 3.5 Bridge**: SubagentManager spawns Python bridge
6. **Wave 4 Orchestra**: MentionRouter, Chat Participants
7. **Wave 5 Visual**: VisualVibePanels (Whiteboard, UI Preview, Dashboard)
8. **Wave 7 Error**: ErrorDashboard polling

## Source-of-Truth & Mirror Dual-Tree Layout

- **`extension/mcp-servers/` is the SOURCE OF TRUTH** for the Python bridge. `init_vibezoo.bat` / `init_vibezoo.sh` deploy it to `%USERPROFILE%\mcp-servers\vibezoo` (the standard runtime directory).
- **`mcp-servers/` (root)** is a development mirror of the same tree, kept in sync manually — **NO codegen script exists**; any bridge edit must be applied to BOTH trees.
- Historical note: `github_diver.py` was deleted and ghost tool `read_project_file` purged during the v0.16.x tool-inventory audit.

## MCP Tool Inventory (33 tools, 16 tool modules)

| Module | Tools |
|--------|-------|
| `tools/setup.py` | `vibezoo_setup` |
| `tools/scout.py` | `search_codebase`, `find_references`, `summarize_architecture` |
| `tools/reviewer.py` | `review_code` |
| `tools/tester.py` | `generate_tests`, `analyze_coverage` |
| `tools/deep_analyzer.py` | `analyze_call_graph`, `map_dependencies`, `extract_patterns`, `reverse_engineer` |
| `tools/file_analyzer.py` | `analyze_uploaded_file` (with dropzone session tracking) |
| `tools/whiteboard.py` | `draw_on_whiteboard`, `get_whiteboard_state`, `capture_screen`, `check_uploaded_files` |
| `tools/fix_loop.py` | `auto_fix_status`, `retry_build`, `check_intervention` |
| `tools/integrated.py` | `review_project` (sole aggregate; ~250 lines) |
| `tools/analysis.py` | `explain_code`, `analyze_changes`, `review_pr`, `refactor_across_files` |
| `tools/knowledge.py` | `recall_project`, `learn_preference`, `get_preferences` (~297 lines) |
| `tools/web.py` | `fetch_page`, `web_search` |
| `tools/ssa.py` | `aggregate_spatial_pixels` |
| `tools/editor.py` | `apply_patch` |
| `tools/ux_coordinator.py` | `ux_coordinator` |
| `tools/feedback.py` | `vibezoo_feedback` |

Former aggregate tools (`find_bugs`, `suggest_refactor`, `generate_docs`, `learn_project`, `auto_analyze_whiteboard`, `auto_analyze_after_drop`) were removed; equivalent workflows are now **prompt-level compositions** of the remaining tools (e.g. find_bugs = `extract_patterns` + `search_codebase` + `review_code`; learn_project is auto-captured at bridge startup via `_auto_learn_project`, retrieval via `recall_project`).

## Key Source Paths

| Module | Path |
|--------|------|
| Entry point | `extension/src/extension.ts` |
| Config | `extension/src/config/ConfigService.ts` |
| Bridge spawn | `extension/src/orchestra/SubagentManager.ts` |
| Crow manager | `extension/src/crow/CrowServerManager.ts` |
| Safety: snapshots | `extension/src/safety/YoctoManager.ts` |
| Safety: git guard | `extension/src/safety/GuardGitManager.ts` |
| Safety: self-check | `extension/src/safety/SelfCheck.ts` |
| Visual: whiteboard | `extension/src/visual/VisualVibePanels.ts` |
| Error collection | `extension/src/flow/ErrorCollection.ts` |
| Bridge entry (source of truth) | `extension/mcp-servers/vibezoo_mcp_bridge.py` |
| Bridge tools | `extension/mcp-servers/bridge/tools/` (16 tool modules) |
| Bridge config | `extension/mcp-servers/bridge/config.py` |
| Tool context (slimmed manifest) | `extension/mcp-servers/bridge/tool_context.py` |
| Shared types | `extension/src/types/index.ts` |

## Build Commands

| Command | Purpose |
|---------|---------|
| `cd extension; npm run compile` | TypeScript → JavaScript |
| `cd extension; npm run watch` | Incremental dev build |
| `cd extension; npm run package` | Create .vsix |
| `cd extension; npm run lint` | ESLint |

## Port Allocation

| Port | Service |
|------|---------|
| 9020 | Crow Memory REST API |
| 9027 | VibeZoo MCP Bridge (SSE) |
| 8089 | Embedding Server (optional) |

## Rules
- Extension MUST NOT write application code directly; delegates to Code mode
- Bridge is single-process (all 33 tools share one Python process)
- File-based IPC has 500ms latency (fs.watchFile interval)
- Guard.git uses OS-specific ACLs (Windows: icacls, Linux: chmod, macOS: chmod)
- Python deps auto-installed by SubagentManager on first startup
- Any bridge code change MUST be mirrored between `extension/mcp-servers/` (source of truth) and root `mcp-servers/` (dev mirror) — manual dual maintenance

</project_architecture>
