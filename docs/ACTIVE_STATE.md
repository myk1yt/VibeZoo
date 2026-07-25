# VibeZoo — Active State (Dynamic)

## Current Session
- **Date**: 2026-07-25
- **Session**: Workspace Onboarding (`/init` protocol)
- **Status**: In Progress

## Recent Changes
- Added "Reset Errors" button to Critical error notification (`extension/src/flow/ErrorCollection.ts`)
- Built VSIX: `extension/vibezoo-0.15.1.vsix` (pending install — requires VS Code restart)
- Created `.rooignore` for context pollution prevention

## Known Issues
1. **Registry.json accumulation**: `~/.vibezoo-errors/registry.json` accumulates test artifacts (web_search ValueError/URLError from unittest mocks). New "Reset Errors" button addresses this.
2. **VSIX install blocked**: VS Code locks the extension directory while running. Install requires closing VS Code first.
3. **Dual mcp-servers/**: Root-level `mcp-servers/` and `extension/mcp-servers/` contain duplicate Python code. Merge plan exists in `plans/bridge-merge-plan.md`.
4. **LICENSE file missing**: `vsce package` warns about missing LICENSE.

## Active Plans
- `plans/bridge-merge-plan.md` — Merge dual mcp-servers directories
- `plans/guard-git-design.md` — Guard.git design document
- `plans/error-collection-system.md` — Error collection system design

## Session Reports (docs/)
- `260725_0001_session_tools-ecosystem-overhaul/` — Tool ecosystem overhaul (completed)
- `260725_0002_session_i18n-full-support/` — i18n full support (completed)
- `260725_0003_session_error-reset-button/` — Error reset button (completed)
- `260725_0004_session_workspace-onboarding/` — Workspace onboarding (current)

## Pending Tasks
- Install VSIX after VS Code restart
- Merge dual mcp-servers/ directories (bridge-merge-plan.md)
