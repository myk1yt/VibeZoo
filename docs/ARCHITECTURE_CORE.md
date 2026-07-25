<project_architecture>

# VibeZoo — Core Architecture (Read-Only)

## Identity
- **Name**: VibeZoo
- **Version**: 0.15.1 (extension), 0.14.4 (bridge)
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
| Bridge entry | `mcp-servers/vibezoo_mcp_bridge.py` |
| Bridge tools | `mcp-servers/bridge/tools/` (16 modules) |
| Bridge config | `mcp-servers/bridge/config.py` |
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
- Bridge is single-process (all 19 tools share one Python process)
- File-based IPC has 500ms latency (fs.watchFile interval)
- Guard.git uses OS-specific ACLs (Windows: icacls, Linux: chmod, macOS: chmod)
- Python deps auto-installed by SubagentManager on first startup

</project_architecture>
