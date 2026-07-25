# Code Task Report: ST-01 Dead Code Sweep

## Task Summary
Removed verified dead code and fixed stale hints across the VibeZoo bridge tools ecosystem. All changes applied to both `mcp-servers/bridge/tools/` (root copy) and `extension/mcp-servers/bridge/tools/` (extension copy).

## Actions Taken

### C-1: Remove 12 dead `_tool_registry` entries (integrated.py)
- Removed 12 entries from the `_tool_registry` dict that had no working lazy getters: `check_quality`, `generate_tests`, `analyze_coverage`, `explain_code`, `analyze_changes`, `review_pr`, `refactor_across_files`, `learn_project`, `recall_project`, `learn_preference`, `get_preferences`.
- Kept only the 8 entries with working lazy getters: `search_codebase`, `review_code`, `extract_patterns`, `map_dependencies`, `analyze_call_graph`, `reverse_engineer`, `summarize_architecture`, `draw_on_whiteboard`.
- Note: `_get_check_quality()` and `_get_analyze_changes()` lazy getter functions were left in place — `_get_check_quality()` is actively called by `review_project()` at line ~483, and `_get_analyze_changes()` was outside the task scope.

### C-2: Delete dead `_lazy_tool()` function (integrated.py)
- Removed the `_lazy_tool()` function (was ~L337-343). It was never called anywhere in the codebase.

### C-3: Delete unused `import subprocess` (deep_analyzer.py)
- Removed `import subprocess` from line 7. Confirmed via search that `subprocess` is never referenced anywhere in the file.

### C-4: Delete dead `partial_result()` stub (_base.py)
- Removed the `partial_result()` static method (was L27-31). Confirmed via project-wide search that it was never called.

### C-5: Fix stale hint text (github_diver.py L52)
- Changed `github_explore_repository(repo_name)` to `explore_github(repo='...')` in the search results tip.

### C-6: Fix stale hint text (github_diver.py L102)
- Changed `github_read_file(repo_name, file_path)` to `explore_github(repo='...', file_path='...')` in the explore results tip.

### C-7: Implement `include_external` filtering (deep_analyzer.py)
- Updated the docstring to explain the parameter's behavior.
- Fan-in/fan-out section: when `include_external=False`, unmatched calls (external library calls) are no longer added to `all_calls`. When `True`, all calls are included (original behavior).
- Per-file call analysis: when `include_external=False`, calls are filtered to only those targeting functions defined in the project. The output shows filtered count vs total when they differ.
- When `include_external=True`, all calls are included (original behavior preserved).

### C-8: SKIPPED — Counter is actively used in scout.py
- The task requested removing `Counter` from `from collections import Counter, defaultdict` in scout.py.
- **Investigation found `Counter` is actively used at line 620**: `date_counts = Counter(commits)` inside the `summarize_architecture` function.
- Removing `Counter` would cause a `NameError` at runtime. This change was correctly skipped to avoid breaking the code.

## Result
✅ Success — All 7 applicable changes (C-1 through C-7) applied to both root and extension copies. C-8 skipped with justification.

### Verification
Both roots passed the import smoke test:
```
python -c "import bridge.tools.integrated, bridge.tools.deep_analyzer, bridge.tools._base, bridge.tools.scout, bridge.tools.github_diver; print('OK')"
```
- `mcp-servers/` → `OK` (exit code 0)
- `extension/mcp-servers/` → `OK` (exit code 0)

## Issues Discovered
- **C-8 was based on incorrect dead-code analysis**: `Counter` is actively used in `scout.py` at line 620 (`date_counts = Counter(commits)`). The original analysis missed this usage. Removing it would have introduced a runtime `NameError`.

## Next Step Recommendations
- VP should update the dead-code report (`dead-code-report.md`) to mark C-8 as "not dead — false positive".
- Consider auditing the remaining `_get_analyze_changes()` lazy getter in integrated.py — it has no call site but was outside this task's scope.

## Affected File List
- `mcp-servers/bridge/tools/integrated.py`
- `mcp-servers/bridge/tools/deep_analyzer.py`
- `mcp-servers/bridge/tools/_base.py`
- `mcp-servers/bridge/tools/github_diver.py`
- `extension/mcp-servers/bridge/tools/integrated.py`
- `extension/mcp-servers/bridge/tools/deep_analyzer.py`
- `extension/mcp-servers/bridge/tools/_base.py`
- `extension/mcp-servers/bridge/tools/github_diver.py`
