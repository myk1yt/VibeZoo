# Requirement Checklist
## Task: VibeZoo Tool Ecosystem Enhancement
## Date: 260725

### Search Enhancement
- [ ] [REQ-001] `fuzzy` mode performs real trigram approximate matching (not identical to `auto`)
- [ ] [REQ-002] `semantic` mode uses embedding-based ranking when server available, labeled BM25 fallback otherwise
- [ ] [REQ-003] `find_references` uses word-boundary regex (searching `io` does not match `action`)
- [ ] [REQ-004] Search result caching via FileCache L1 with 20s TTL

### Web Search Simplification
- [ ] [REQ-005] `web_search` has honest `engine` parameter (auto|exa|ddg) with DuckDuckGo fallback
- [ ] [REQ-006] `web_search` surfaces errors instead of silent `except: return []`
- [ ] [REQ-007] `web_search` has retry logic (2 retries, exponential backoff)

### Dead Code Cleanup
- [ ] [REQ-008] 12 dead `_tool_registry` entries removed from integrated.py
- [ ] [REQ-009] Dead `_lazy_tool()` function removed from integrated.py
- [ ] [REQ-010] Dead `subprocess` import removed from deep_analyzer.py
- [ ] [REQ-011] Dead `partial_result()` stub removed from _base.py
- [ ] [REQ-012] Stale function references fixed in github_diver.py
- [ ] [REQ-013] Unused `Counter` import removed from scout.py
- [ ] [REQ-014] `include_external` parameter implemented or documented in deep_analyzer.py

### Tool Consolidation
- [ ] [REQ-015] Shared `ast_singleton.py` module replaces 5 duplicated `_get_ast_engine()` singletons
- [ ] [REQ-016] `auto_analyze_whiteboard` merged into `get_whiteboard_state(analyze=True)` with deprecated alias

### Quality & Robustness
- [ ] [REQ-017] `max_tokens` parameter implemented with actual output truncation in all 5 tools
- [ ] [REQ-018] `context_lines` passed to ResultRanker in semantic mode
- [ ] [REQ-019] All changes applied to BOTH `mcp-servers/` and `extension/mcp-servers/` copies
- [ ] [REQ-020] All new tests pass CI (no optional deps required)
- [ ] [REQ-021] Import smoke test passes on both roots
