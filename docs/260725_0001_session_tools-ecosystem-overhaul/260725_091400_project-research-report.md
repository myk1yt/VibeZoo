# Project Research Task Report

## Task Summary
Comprehensive deep investigation of VibeZoo's MCP tool ecosystem (16 tool files, 40 MCP tools, 12 supporting modules). Analyzed all implementations, identified dead code, cross-tool overlaps, search quality gaps, and external dependency requirements.

## Actions Taken
1. Read all 16 tool implementation files in `mcp-servers/bridge/tools/`
2. Read core infrastructure: `search_engine.py`, `config.py`, `result_ranker.py`, `intent_detector.py`
3. Read and analyzed MCP registration system (`tools/__init__.py`)
4. Generated 6 comprehensive report files

## Result
✅ Complete — All 6 deliverable reports generated in `docs/260725_0001_session_tools-ecosystem-overhaul/`

## Key Findings

### Search Quality Issues
1. **`"fuzzy"` mode is fake** — behaves identically to `"auto"` ([`scout.py`](mcp-servers/bridge/tools/scout.py:713))
2. **`"semantic"` mode is misleading** — uses BM25 keyword similarity, not embedding-based search ([`scout.py`](mcp-servers/bridge/tools/scout.py:98))
3. **`web_search` engine parameter is vestigial** — only Exa is implemented despite the `engine` parameter ([`web.py`](mcp-servers/bridge/tools/web.py:156))
4. **`find_references` has false positives** — uses `symbol in line` string matching instead of word-boundary regex ([`scout.py`](mcp-servers/bridge/tools/scout.py:309))

### Dead Code
1. **12/20 dead entries in `_tool_registry`** in [`integrated.py`](mcp-servers/bridge/tools/integrated.py:303)
2. **Dead `_lazy_tool()` function** at [`integrated.py:337`](mcp-servers/bridge/tools/integrated.py:337)
3. **Dead `subprocess` import** at [`deep_analyzer.py:7`](mcp-servers/bridge/tools/deep_analyzer.py:7)
4. **7 unused `max_tokens` parameters** across integrated tools
5. **Dead `BaseTool.partial_result()` method** at [`_base.py:27`](mcp-servers/bridge/tools/_base.py:27)
6. **Stale tool name references** in [`github_diver.py`](mcp-servers/bridge/tools/github_diver.py:52) L52/L102

### Cross-Tool Overlaps
1. **`analyze_uploaded_file` vs `auto_analyze_after_drop`** — significant overlap; latter is a superset
2. **`get_whiteboard_state` vs `auto_analyze_whiteboard`** — latter just wraps former + adds suggestions
3. **`_get_ast_engine()` singleton** duplicated in 5 separate files

### Top Priority Recommendations
1. 🔴 Fix misleading search mode labels (H1)
2. 🔴 Fix `find_references` false positives (M8)
3. 🟡 Clean dead `_tool_registry` entries (H2)
4. 🟡 Fix stale github_diver text (H3)
5. 🟡 Consolidate AST singleton (H4)
6. 🟡 Remove dead `max_tokens` parameters (M3)

## Affected File List
- `mcp-servers/bridge/tools/__init__.py` (registration)
- `mcp-servers/bridge/tools/scout.py` (search + references + architecture)
- `mcp-servers/bridge/tools/web.py` (web search)
- `mcp-servers/bridge/tools/integrated.py` (composite tools + dead registry)
- `mcp-servers/bridge/tools/deep_analyzer.py` (dead import)
- `mcp-servers/bridge/tools/_base.py` (dead method)
- `mcp-servers/bridge/tools/github_diver.py` (stale references)
- `mcp-servers/bridge/search_engine.py` (search core)
- `mcp-servers/bridge/result_ranker.py` (BM25 ranking)
- `mcp-servers/bridge/tools/analysis.py` (analysis tools)
- `mcp-servers/bridge/tools/feedback.py` (feedback)
- `mcp-servers/bridge/tools/file_analyzer.py` (file analysis)
- `mcp-servers/bridge/tools/fix_loop.py` (fix loop)
- `mcp-servers/bridge/tools/knowledge.py` (knowledge/memory)
- `mcp-servers/bridge/tools/reviewer.py` (code review)
- `mcp-servers/bridge/tools/setup.py` (setup)
- `mcp-servers/bridge/tools/ssa.py` (SSA)
- `mcp-servers/bridge/tools/tester.py` (testing)
- `mcp-servers/bridge/tools/ux_coordinator.py` (UX coordination)
- `mcp-servers/bridge/tools/whiteboard.py` (whiteboard)
- `mcp-servers/bridge/tools/editor.py` (file editing)
- `mcp-servers/bridge/config.py` (configuration)
- `mcp-servers/bridge/intent_detector.py` (intent detection)

## Next Step Recommendations
1. VP should delegate to **architect** for tool consolidation design (H1, H4, M5)
2. VP should delegate to **code** for quick cleanup passes (H2, H3, M2, M4, M7)
3. VP should consider an ADR for search engine strategy (embeddings vs BM25 vs hybrid)
4. VP should evaluate whether 40 MCP tools is the right count or if consolidation can reduce cognitive load for agents
