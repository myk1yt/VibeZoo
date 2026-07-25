# Code Task Report: ST-06 Semantic Embedding Search Mode + ResultRanker Context Lines

## Task Summary
Implemented embedding-based semantic search for `search_codebase` tool, replacing the previous BM25-only "semantic" mode with true embedding cosine similarity ranking. Added `context_lines` parameter to `ResultRanker.rank()` for proper context density normalization. All changes applied to both root and extension copies.

## Actions Taken

### 1. Created `embedding_client.py` (both copies)
- **Files**: [`mcp-servers/bridge/embedding_client.py`](mcp-servers/bridge/embedding_client.py), [`extension/mcp-servers/bridge/embedding_client.py`](extension/mcp-servers/bridge/embedding_client.py)
- `EmbeddingClient` class with runtime API shape probing (Ollama → OpenAI fallback)
- `is_available()` with 2s timeout and result caching
- `embed()` batch embedding with graceful None on error
- `cosine_similarity()` pure function for vector comparison
- `rank_by_embedding()` reranking function with 2000-char content cap

### 2. Extended `ResultRanker.rank()` with `context_lines` (both copies)
- **Files**: [`mcp-servers/bridge/result_ranker.py`](mcp-servers/bridge/result_ranker.py:11), [`extension/mcp-servers/bridge/result_ranker.py`](extension/mcp-servers/bridge/result_ranker.py:11)
- Added `context_lines: int = 3` parameter to `rank()`
- Updated `_context_density()` to use `min(total / max(context_lines, 1), 1.0)` for normalization instead of hardcoded `/3.0`

### 3. Wired semantic mode into `_search_codebase_impl()` (both copies)
- **Files**: [`mcp-servers/bridge/tools/scout.py`](mcp-servers/bridge/tools/scout.py:105), [`extension/mcp-servers/bridge/tools/scout.py`](extension/mcp-servers/bridge/tools/scout.py:105)
- Added import: `from bridge.embedding_client import EmbeddingClient, rank_by_embedding`
- When `mode == "semantic"`:
  - Tries `EmbeddingClient.is_available()` first
  - If available: embeds query + candidate contents, ranks by cosine similarity, labels `rank_source="embedding"`
  - If unavailable: falls back to `ResultRanker` BM25 path with `context_lines` passed through, appends warning note
- Injected `semantic_note` into output after `rg_note`

### 4. Created test file (both copies)
- **Files**: [`mcp-servers/tests/test_semantic_search.py`](mcp-servers/tests/test_semantic_search.py), [`extension/mcp-servers/tests/test_semantic_search.py`](extension/mcp-servers/tests/test_semantic_search.py)
- 23 tests across 6 test classes:
  - `TestCosineSimilarity` (5 tests): identical, orthogonal, opposite, zero vectors, known similarity
  - `TestEmbeddingClientAvailability` (4 tests): Ollama available, OpenAI fallback, server down, cached availability
  - `TestEmbeddingClientEmbed` (5 tests): Ollama embed, OpenAI embed, unavailable, empty list, error handling
  - `TestRankByEmbedding` (3 tests): ordering by similarity, None fallback, content cap
  - `TestResultRankerContextLines` (4 tests): accepts param, default behavior, density normalization, zero edge case
  - `TestSemanticSearchIntegration` (2 tests): server up (embedding rank), server down (BM25 fallback + note)

## Result
✅ **Success** — All 23 tests pass on both root and extension copies.

```
# Root copy
23 passed in 7.67s

# Extension copy
23 passed in 6.67s
```

## Issues Discovered
None. All changes applied cleanly to both copies.

## Next Step Recommendations
- Consider adding a warm-up call to `EmbeddingClient.is_available()` at bridge startup to cache availability early
- The `VIBEZOO_EMBED_URL` and `VIBEZOO_EMBED_MODEL` env vars are documented in code but could be added to `.zoo/config.json` for discoverability

## Affected File List
- `mcp-servers/bridge/embedding_client.py` (new)
- `mcp-servers/bridge/result_ranker.py` (modified)
- `mcp-servers/bridge/tools/scout.py` (modified)
- `mcp-servers/tests/test_semantic_search.py` (new)
- `extension/mcp-servers/bridge/embedding_client.py` (new)
- `extension/mcp-servers/bridge/result_ranker.py` (modified)
- `extension/mcp-servers/bridge/tools/scout.py` (modified)
- `extension/mcp-servers/tests/test_semantic_search.py` (new)
