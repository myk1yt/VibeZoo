# Search Quality Analysis — VibeZoo Tool Ecosystem

## 1. Search Engine Architecture ([`search_engine.py`](mcp-servers/bridge/search_engine.py:21))

### Three-Tier Fallback

The [`SearchEngine`](mcp-servers/bridge/search_engine.py:21) class implements a cascading search strategy:

| Tier | Backend | When Used | Speed | Quality |
|------|---------|-----------|-------|---------|
| 1 | **ripgrep** (`rg`) | When installed (checks via `rg --version`) | ⚡ Fastest | High (regex, respects .gitignore) |
| 2 | **git grep** | When in a git repo and ripgrep unavailable | ⚡ Fast | Medium (only indexed files) |
| 3 | **os.walk + regex** | Final fallback | 🐌 Slow | Low (brute force, no smart exclusions) |

**Key finding**: This is **NOT semantic search**. It's purely regex/text-based matching. The "semantic" mode label in `search_codebase` is misleading.

### What `search_codebase` Actually Does ([`scout.py`](mcp-servers/bridge/tools/scout.py:66))

The implementation at [`_search_codebase_impl()`](mcp-servers/bridge/tools/scout.py:66) works as follows:

1. **Phase 1 — Text Search** ([`SearchEngine.search()`](mcp-servers/bridge/search_engine.py:66)): Regex-based matching using ripgrep/git grep/os.walk
2. **Phase 2 — AST Search** (L126-219): For symbol-like queries (single identifier or containing keywords like "function", "class", "def"), it scans all matching files with tree-sitter AST to find function/class/interface definitions
3. **Phase 3 — Semantic Ranking** (L98-100): Only when `mode="semantic"`, applies [`ResultRanker`](mcp-servers/bridge/result_ranker.py:8) which is BM25-based (not true embedding-based semantic search)

### Mode Analysis

| Mode | Description in Docstring | Actual Behavior | Gap |
|------|--------------------------|-----------------|-----|
| `"auto"` | Default | Text search + auto AST for symbol queries | ✅ Matches |
| `"exact"` | Case-sensitive search | ripgrep with `-s` flag | ✅ Matches |
| `"fuzzy"` | Fuzzy search | Same as auto (no actual fuzzy logic) | 🔴 **Misleading** — no fuzzy matching implemented |
| `"ast"` | AST search | Forces AST scan regardless of query type | ✅ Matches |
| `"semantic"` | Semantic search | BM25 reranking of text search results | 🔴 **Misleading** — not embedding-based |

**Critical issue**: The `"fuzzy"` and `"semantic"` modes are falsely advertised. `"fuzzy"` behaves identically to `"auto"`, and `"semantic"` uses BM25 keyword similarity, not true semantic/embedding search.

### `find_references` Analysis ([`scout.py`](mcp-servers/bridge/tools/scout.py:260))

**Implementation quality: GOOD**
- Uses AST for definition detection (multi-language: TS/JS/Python/Go/Rust)
- Classifies reference types: `call`, `read`, `write`, `type_ref`, `import_ref`
- Provides call chain analysis (who calls the function that uses this symbol)
- Groups results by file and by reference type

**Weakness**: Uses simple string matching (`symbol not in line`) for usage detection (L309), which can produce false positives (e.g., searching for "io" matches "action", "configuration", etc.).

### `summarize_architecture` Analysis ([`scout.py`](mcp-servers/bridge/tools/scout.py:397))

**Summary mode**: Quick overview (file count, tech stack, entry points, cache stats)
**Full mode**: Comprehensive analysis including:
- Entry points detection
- File type distribution
- Import-based layer discovery
- Technical debt diagnosis (circular deps, hub modules)
- Git activity trends
- Path-based layer classification

**Quality: GOOD** but slow for large projects (reads all files for line counting at L455-458).

---

## 2. Web Search Analysis ([`web.py`](mcp-servers/bridge/tools/web.py:1))

### Implementation

[`WebSearchEngine`](mcp-servers/bridge/tools/web.py:21) uses **Exa API** exclusively:
- Endpoint: `https://api.exa.ai/search`
- Authentication: `EXA_API_KEY` via environment variable or Python `keyring`
- Highlights mode: enabled
- Timeout: 10 seconds
- Max results: capped at 10

### Tool Description vs Implementation

**`web_search` description** (L157): `"Exa API 기반 신경망 웹 검색(Neural Web Search)"`

**Actual behavior**: 
- **Only Exa** — there is no DuckDuckGo fallback, no other search engine
- The `engine` parameter accepts values but only `"exa"` and `"auto"` work. Any other value is silently defaulted to `"exa"` (L167-168)
- Error message (L179-182) correctly suggests EXA_API_KEY setup

**The `engine` parameter is a vestigial abstraction** — it was likely designed to support multiple backends but only Exa was ever implemented. The parameter adds confusion.

### Error Handling
- ✅ Graceful degradation: returns empty list on API failure
- ✅ Key validation before making requests
- ❌ No retry logic for transient failures
- ❌ No caching of search results
- ❌ Silent failure: `except Exception: return []` at L82-83 swallows all errors

---

## 3. Codebase Search Quality Assessment

### Strengths

1. **AST-powered symbol search** ([`scout.py`](mcp-servers/bridge/tools/scout.py:126-219]): When a query looks like a symbol name, AST parsing finds actual function/class/struct definitions, not just text matches
2. **Multi-language support**: TS/JS, Python, Go, Rust via tree-sitter
3. **ripgrep-first strategy**: Fast and respects `.gitignore`
4. **Crow integration**: Search patterns are ingested into Crow Memory for learning

### Weaknesses

1. **No true semantic search**: Despite the "semantic" mode label, there's no embedding-based search. The `ResultRanker` ([`result_ranker.py`](mcp-servers/bridge/result_ranker.py:8)) uses BM25, which is keyword-overlap based
2. **Fuzzy mode is fake**: `"fuzzy"` mode behaves identically to `"auto"`
3. **String-based reference matching**: [`find_references()`](mcp-servers/bridge/tools/scout.py:260) uses `symbol not in line` (L309) for usage detection, leading to false positives
4. **Slow for large projects**: The `summarize_architecture` full mode reads ALL files for line counting
5. **No index building**: Every search scans the entire project (or uses ripgrep which is fast but still regex-based)
6. **context_lines parameter ignored in semantic mode**: The parameter is accepted but ResultRanker doesn't use it

### Comparison: What Agents Actually See

When an agent calls `search_codebase(query="SearchEngine")`:
1. ripgrep finds all lines containing "SearchEngine" (text match)
2. AST engine searches for any function/class named "SearchEngine" (symbol match)
3. Both result sets are combined and displayed

This is **adequate for code navigation** but **insufficient for conceptual search** (e.g., "find code related to caching strategy" would fail because it's keyword-based).

---

## 4. External Dependencies for Search

| Dependency | Required? | Purpose | Fallback |
|-----------|-----------|---------|----------|
| `ripgrep` (rg) | No (recommended) | Fast code search | os.walk fallback |
| `tree-sitter` | No (optional) | AST parsing | Regex fallback |
| `tree-sitter-*` lang packs | No (optional) | Language-specific AST | Generic parsing |
| `Exa API key` | Only for web_search | Web search | Empty results |
| `Keyring` | No (optional) | Secure API key storage | Environment variable only |

---

## 5. Recommendations for Search Improvements

1. **Add actual fuzzy matching**: Implement Levenshtein distance or trigram similarity for `"fuzzy"` mode
2. **Implement embedding-based semantic search**: Use a local embedding model (e.g., `nomic-embed-text` if available, or `sentence-transformers`) for true semantic search
3. **Fix `find_references` false positives**: Use AST-based occurrence counting instead of `symbol in line`
4. **Clean up `engine` parameter in `web_search`**: Either add alternative backends or remove the parameter
5. **Add search result caching**: Cache ripgrep results for repeated queries on the same project
6. **Remove dead `max_tokens` parameter** from `summarize_architecture` or implement truncation
