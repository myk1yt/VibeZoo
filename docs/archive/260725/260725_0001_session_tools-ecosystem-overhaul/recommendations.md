# Prioritized Improvement Recommendations — VibeZoo Tool Ecosystem

## Priority 🔴 HIGH — Immediate Impact

### H1. Fix Misleading Search Mode Labels
**File**: [`scout.py`](mcp-servers/bridge/tools/scout.py:702)
**Effort**: Small (30 min)

The `mode` parameter of `search_codebase` has 5 values, but 2 are misleading:
- `"fuzzy"` — behaves identically to `"auto"` (no fuzzy logic implemented)
- `"semantic"` — uses BM25 keyword similarity, not embedding-based semantic search

**Action**:
- Rename `"fuzzy"` to document it as alias for `"auto"`, or implement actual fuzzy matching (Levenshtein/trigram)
- Rename `"semantic"` to `"ranked"` or implement actual embedding-based search
- Update tool description docstring to accurately reflect each mode's behavior

### H2. Clean Up Dead `_tool_registry` Entries
**File**: [`integrated.py`](mcp-servers/bridge/tools/integrated.py:303)
**Effort**: Small (20 min)

The `_tool_registry` dict at L303-323 has 20 entries, but only 8 have working lazy getters. 12 entries are dead.

**Action**: Remove the 12 dead entries (`check_quality`, `generate_tests`, `analyze_coverage`, `explain_code`, `analyze_changes`, `review_pr`, `refactor_across_files`, `learn_project`, `recall_project`, `learn_preference`, `get_preferences`). Remove the dead `_lazy_tool()` function at L337-343.

### H3. Fix Stale Tool References in `github_diver.py`
**File**: [`github_diver.py`](mcp-servers/bridge/tools/github_diver.py:52)
**Effort**: Small (10 min)

The tool's output text references non-existent functions:
- L52: `"github_explore_repository(repo_name)"` → should be `"explore_github(repo='...')"`
- L102: `"github_read_file(repo_name, file_path)"` → should be `"explore_github(repo='...', file_path='...')"`

### H4. Consolidate `_get_ast_engine()` Singleton
**Files**: 5 tool files with duplicated singleton pattern
**Effort**: Medium (1 hour)

The `_get_ast_engine()` singleton is copy-pasted in 5 files:
- [`scout.py:45`](mcp-servers/bridge/tools/scout.py:45)
- [`analysis.py:35`](mcp-servers/bridge/tools/analysis.py:35)
- [`deep_analyzer.py:36`](mcp-servers/bridge/tools/deep_analyzer.py:36)
- [`reviewer.py:37`](mcp-servers/bridge/tools/reviewer.py:37)
- [`tester.py:34`](mcp-servers/bridge/tools/tester.py:34)

**Action**: Create a shared singleton in `bridge/ast_singleton.py`:
```python
from bridge.ast_engine import AstEngine
_instance = None
def get_ast_engine() -> AstEngine:
    global _instance
    if _instance is None:
        _instance = AstEngine()
    return _instance
```
All 5 files import from this shared module.

---

## Priority 🟡 MEDIUM — Significant Improvement

### M1. Clean Up `engine` Parameter in `web_search`
**File**: [`web.py`](mcp-servers/bridge/tools/web.py:156)
**Effort**: Small (15 min)

The `engine` parameter accepts values but only `"exa"` works. This is confusing.

**Action**: Either:
- (A) Remove the parameter entirely (hardcode Exa), or
- (B) Add fallback engines (e.g., DuckDuckGo) and implement the multi-engine strategy, or
- (C) At minimum, document that only `"exa"` is supported and reject other values with a clear error

### M2. Remove Dead `subprocess` Import
**File**: [`deep_analyzer.py`](mcp-servers/bridge/tools/deep_analyzer.py:7)
**Effort**: Trivial (2 min)

`import subprocess` at L7 is never used in this file.

### M3. Remove Unused `max_tokens` Parameters
**Files**: Multiple integrated tools
**Effort**: Small (30 min)

The `max_tokens` parameter is declared in 5+ tool signatures but never used in the implementation:
- [`summarize_architecture`](mcp-servers/bridge/tools/scout.py:731) L734
- [`review_project`](mcp-servers/bridge/tools/integrated.py:400) L401
- [`find_bugs`](mcp-servers/bridge/tools/integrated.py:544) L453
- [`suggest_refactor`](mcp-servers/bridge/tools/integrated.py:757) L758
- [`generate_docs`](mcp-servers/bridge/tools/integrated.py:886) L887

**Action**: Either implement output truncation based on `max_tokens` or remove the parameter.

### M4. Remove Unused `include_external` Parameter
**File**: [`deep_analyzer.py`](mcp-servers/bridge/tools/deep_analyzer.py:528)
**Effort**: Trivial (5 min)

`include_external` parameter in `analyze_call_graph` (L530) is declared but never used.

### M5. Merge `auto_analyze_whiteboard` into `get_whiteboard_state`
**Files**: [`whiteboard.py`](mcp-servers/bridge/tools/whiteboard.py:988), [`ux_coordinator.py`](mcp-servers/bridge/tools/ux_coordinator.py:286)
**Effort**: Medium (1 hour)

`auto_analyze_whiteboard` just calls `get_whiteboard_state()` and adds generic suggestions. Add an optional `analyze` parameter to `get_whiteboard_state` and remove `auto_analyze_whiteboard` from MCP registration.

### M6. Add Error Logging in `WebSearchEngine.search()`
**File**: [`web.py`](mcp-servers/bridge/tools/web.py:82)
**Effort**: Small (10 min)

The `except Exception: return []` at L82-83 silently swallows all errors. Add logging or error context to the returned result.

### M7. Remove Dead `BaseTool.partial_result()` Method
**File**: [`_base.py`](mcp-servers/bridge/tools/_base.py:27)
**Effort**: Trivial (2 min)

`partial_result()` at L27-31 is a stub that's never called by any tool. Remove it.

### M8. Fix `find_references` False Positives
**File**: [`scout.py`](mcp-servers/bridge/tools/scout.py:309)
**Effort**: Medium (1 hour)

The `symbol not in line` string matching at L309 produces false positives (e.g., searching for "io" matches "action", "configuration").

**Action**: Use word-boundary matching: `\b{symbol}\b` regex instead of `symbol in line`.

---

## Priority 🟢 LOW — Cleanup & Polish

### L1. Fix `ResultRanker` to Actually Use `context_lines`
**File**: [`result_ranker.py`](mcp-servers/bridge/result_ranker.py:8)
**Effort**: Small (15 min)

The `_context_density()` method at L72 already considers context lines, but `search_codebase` in semantic mode doesn't pass `context_lines` to `ResultRanker.rank()`.

### L2. Consolidate `analyze_uploaded_file` and `auto_analyze_after_drop`
**Files**: [`file_analyzer.py`](mcp-servers/bridge/tools/file_analyzer.py:345), [`ux_coordinator.py`](mcp-servers/bridge/tools/ux_coordinator.py:136)
**Effort**: Large (3 hours)

`auto_analyze_after_drop` is a superset of `analyze_uploaded_file` with added session tracking. Consider merging into a single tool with optional session tracking.

### L3. Add Search Result Caching
**File**: [`search_engine.py`](mcp-servers/bridge/search_engine.py:21)
**Effort**: Medium (2 hours)

Currently every search scans the entire project. Add a TTL-based cache for repeated queries.

### L4. Add `max_tokens` Implementation
**Files**: All tools with `max_tokens` parameter
**Effort**: Medium (2 hours)

Implement actual output truncation: count output characters and truncate at `max_tokens * 4` (approximate char count).

### L5. Update `setup.py` Ripgrep Version
**File**: [`setup.py`](mcp-servers/bridge/tools/setup.py:404)
**Effort**: Trivial (5 min)

The hardcoded ripgrep URL at L404 points to version 14.1.1. Update to latest stable release.

---

## Summary: Impact vs Effort Matrix

| ID | Recommendation | Impact | Effort | ROI |
|----|---------------|--------|--------|-----|
| H1 | Fix misleading search modes | 🔴 High | 🟢 Small | ⭐⭐⭐⭐⭐ |
| H2 | Clean dead `_tool_registry` | 🟡 Medium | 🟢 Small | ⭐⭐⭐⭐ |
| H3 | Fix stale github_diver text | 🟡 Medium | 🟢 Trivial | ⭐⭐⭐⭐ |
| H4 | Consolidate AST singleton | 🟡 Medium | 🟡 Medium | ⭐⭐⭐ |
| M1 | Clean `engine` param in web_search | 🟡 Medium | 🟢 Small | ⭐⭐⭐ |
| M2 | Remove dead import | 🟢 Low | 🟢 Trivial | ⭐⭐ |
| M3 | Remove dead `max_tokens` params | 🟡 Medium | 🟢 Small | ⭐⭐⭐ |
| M4 | Remove dead `include_external` | 🟢 Low | 🟢 Trivial | ⭐⭐ |
| M5 | Merge whiteboard analysis tools | 🟡 Medium | 🟡 Medium | ⭐⭐⭐ |
| M6 | Add error logging in web search | 🟡 Medium | 🟢 Small | ⭐⭐⭐ |
| M7 | Remove dead `partial_result()` | 🟢 Low | 🟢 Trivial | ⭐ |
| M8 | Fix `find_references` false positives | 🔴 High | 🟡 Medium | ⭐⭐⭐⭐ |

**Recommended execution order**: H1 → H3 → H2 → M2 → M4 → M7 → M1 → M3 → H4 → M8 → M6 → M5 → L1 → L5
