# VibeZoo — Active State (Dynamic)

## Current Session
- **Date**: 2026-09-02
- **Session**: VibeZoo Tool Inventory Audit & Full Docs Modernization (`docs/260902_0001_session_vibezoo-tool-inventory-audit/`)
- **Status**: Tool Cleanup + Docs Modernization Completed (T1–T3)

---

## Recent Changes (Session 260902)

1. **Tool Inventory Cleanup (39→33 tools)**:
   - Removed aggregate tools: `auto_analyze_whiteboard`, `auto_analyze_after_drop`, `find_bugs`, `suggest_refactor`, `generate_docs`, `learn_project`.
   - Deleted dead module `github_diver.py`; purged ghost tool `read_project_file` from the registry.
   - `analyze_uploaded_file(file_path, track_dropzone=False)` — merged dropzone session tracking capability.
   - Aggregate workflows are now **prompt-level compositions**: find_bugs = `extract_patterns` + `search_codebase` + `review_code`; suggest_refactor = `map_dependencies` + `analyze_call_graph` + `extract_patterns`; generate_docs = `summarize_architecture` + `reverse_engineer` + whiteboard diagram; learn_project auto-captured at bridge startup (`_auto_learn_project`), retrieval via `recall_project`.
2. **Extension Frontend Sync**:
   - Removed VS Code wrapper commands `vibezoo.findBugs` / `vibezoo.suggestRefactor` / `vibezoo.generateDocs` / `vibezoo.learnProject`.
   - Purged removed-tool `alwaysAllow` entries from MCP config; removed orphaned NLS keys across 20 locales.
3. **Dual-Tree Parity**:
   - Both `mcp-servers/` (dev mirror) and `extension/mcp-servers/` (SOURCE OF TRUTH, deployed by `init_vibezoo.bat` to `%USERPROFILE%\mcp-servers\vibezoo`) are in sync for all cleanup edits. No codegen script exists — manual dual maintenance.
4. **Path-Safety Fixes (T2)**:
   - Absolute-path / user-specific path leakage fixed in bridge and docs.
5. **Docs Modernization (T3)**:
   - `docs/ARCHITECTURE_CORE.md` ± myk1yt, `docs/PROJECT_CONTEXT.md` ± myk1yt, `docs/ACTIVE_STATE.md` ± myk1yt, `docs/INSTALLATION.md`, `README.md`, `README-myk1yt.md` all updated to the 33-tool current state.

---

## Known Issues

1. **User Redeploy Pending**: Runtime directory `%USERPROFILE%\mcp-servers\vibezoo` still holds the pre-cleanup tool set until the user re-runs `init_vibezoo.bat` (or `init_vibezoo.sh`).
2. **-myk1yt Variant Reconciliation (B4)**: `-myk1yt` fork variants (e.g. `scout-myk1yt.py`, `bridge-myk1yt.py`) still carry pre-cleanup symbols (`embedding_health_check`, `rebuild_code_index`, `index_cache.py`); they are dev-personal variants and pending a dedicated reconciliation pass.
3. **Local Embedding Server Offline Notice**: Without `nomic-embed-text` on port `8089`, semantic search falls back to BM25 with a friendly notice (by design).
4. **Windows OneDrive File Locking**: Batch operations inside OneDrive-synced folders may hit file locks (see `docs/INSTALLATION.md` guidance).

---

## Active Plans & Design Documents
- `plans/` (11 design specifications preserved for architecture reference)
- `fromscratch/` (6 foundational roadmap and design specs preserved)
- `docs/ARCHITECTURE_CORE.md` (Core architectural invariants — updated to 33-tool state)
- `docs/PROJECT_CONTEXT.md` (Project context and module mapping — updated)
- `docs/INSTALLATION.md` (Install + troubleshooting guide — verified current)

---

## Session Reports (`docs/`)
- `docs/260902_0001_session_vibezoo-tool-inventory-audit/` (Current session — T1 tool audit, T2 path fixes, T3 docs modernization)
- `docs/260830_0001_session_reinstall-recovery-and-quality/` (Completed)
- `docs/archive/260725/` (Archived: tools-ecosystem-overhaul, i18n-full-support, error-reset-button, workspace-onboarding)

---

## Pending Tasks
- User redeploy via `init_vibezoo.bat` / `init_vibezoo.sh` to propagate the 33-tool set to the runtime directory.
- Reconcile `-myk1yt` variant files with the canonical source (B4).
- VP review and structured Git commit splitting.
