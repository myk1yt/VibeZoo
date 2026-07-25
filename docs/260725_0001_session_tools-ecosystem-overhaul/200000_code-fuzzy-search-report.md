# Code Task Report: ST-05 Implement Real Fuzzy Search Mode

## Task Summary
Implemented actual trigram-based fuzzy matching for `mode="fuzzy"` in `search_codebase`, replacing the previous pass-through behavior where fuzzy mode was identical to auto mode.

## Actions Taken

### 1. Created `fuzzy_matcher.py` (both copies)
- **Files**: [`fuzzy_matcher.py`](mcp-servers/bridge/fuzzy_matcher.py), [`fuzzy_matcher.py`](extension/mcp-servers/bridge/fuzzy_matcher.py)
- Implemented `trigram_similarity(a, b)` using Dice coefficient on character 3-grams
  - Case-insensitive matching
  - Substring containment fallback for strings shorter than 3 chars
  - Explicit empty-string guard (returns 0.0)
- Implemented `fuzzy_filter(query, results, threshold=0.35, max_results=50)`
  - Scores each result's content lines (first 10) and filename against query
  - Pre-caps input at 500 candidates to bound cost
  - Annotates results with `fuzzy_score`
  - Sorts by score descending, caps at `max_results`
  - Skips results with no content and no filename

### 2. Wired fuzzy_filter into `_search_codebase_impl()` (both copies)
- **Files**: [`scout.py`](mcp-servers/bridge/tools/scout.py), [`scout.py`](extension/mcp-servers/bridge/tools/scout.py)
- Added import: `from bridge.fuzzy_matcher import fuzzy_filter`
- When `mode == "fuzzy"`:
  - Strips regex metacharacters from query for broader text search
  - Falls back to longest alphanumeric token (>= 2 chars) if needed
  - Runs `engine.search()` with `max_results * 2` to get a wider candidate pool
  - Applies `fuzzy_filter(query, results, threshold=0.35, max_results=max_results)`
- Non-fuzzy modes use the original `engine.search()` call unchanged

### 3. Updated `search_codebase` docstring (both copies)
- Added: `"fuzzy" = trigram approximate match (Dice coefficient on character 3-grams, threshold 0.35)`

### 4. Created test file (both copies)
- **Files**: [`test_fuzzy_search.py`](mcp-servers/tests/test_fuzzy_search.py), [`test_fuzzy_search.py`](extension/mcp-servers/tests/test_fuzzy_search.py)
- 18 tests total, all pure logic (no external deps):
  - `TestTrigramSimilarity` (8 tests): identical strings, typo similarity > 0.5, completely different, case-insensitive, short string fallback, single char, empty strings, partial overlap
  - `TestFuzzyFilter` (10 tests): empty query, empty results, typo finds original, threshold filtering, max_results cap, score annotation, sorted by score, pre-cap 500, binary/empty skip, filename matching

### 5. Bug fix during testing
- `trigram_similarity("", "")` returned 1.0 due to Python's `"" in ""` being `True`
- Added explicit `if not a or not b: return 0.0` guard at the top of the function
- Applied to both copies

## Result
✅ **Success** — All 18 tests pass on both root copies:

```
# Root copy (mcp-servers/)
18 passed in 0.28s

# Extension copy (extension/mcp-servers/)
18 passed in 0.32s
```

## Issues Discovered
- Python's `"" in ""` evaluates to `True`, causing the substring fallback to return 1.0 for empty strings. Fixed with an explicit empty-string guard.

## Affected File List
- `mcp-servers/bridge/fuzzy_matcher.py` (new)
- `extension/mcp-servers/bridge/fuzzy_matcher.py` (new)
- `mcp-servers/bridge/tools/scout.py` (modified: import, fuzzy mode wiring, docstring)
- `extension/mcp-servers/bridge/tools/scout.py` (modified: import, fuzzy mode wiring, docstring)
- `mcp-servers/tests/test_fuzzy_search.py` (new)
- `extension/mcp-servers/tests/test_fuzzy_search.py` (new)
