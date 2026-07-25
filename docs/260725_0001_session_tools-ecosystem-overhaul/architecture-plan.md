# VibeZoo Tool Ecosystem Enhancement — Architecture Plan

> **Status**: Phase 3 Architecture (awaiting Ask audit + VP delegation)
> **Report Folder**: `docs/260725_0001_session_tools-ecosystem-overhaul/`
> **Source research**: `260725_091400_project-research-report.md`, `search-quality-analysis.md`, `dead-code-report.md`, `overlap-analysis.md`, `recommendations.md`, `dependency-map.md`, `tool-inventory.md` (all verified against source by architect)

⚠️ **Note on external lookup**: Semantic/embedding-server design in Section A.2 is based on internal knowledge of common embedding HTTP APIs (Ollama-style `/api/embeddings`, OpenAI-style `/v1/embeddings`). No live external documentation was fetched in this phase. The implementation must probe the actual server shape at runtime and degrade gracefully (see A.2 fallback contract), so being wrong about a specific vendor payload is a contained risk.

---

## 0. Executive Summary

The VibeZoo MCP bridge exposes ~40 tools across 16 modules. Phase 2 research (verified line-by-line) shows the ecosystem works but over-promises: two search modes are mislabeled, one core symbol tool produces false positives, one web tool silently fails, and the integrated registry is 60% dead. This plan sequences **14 sub-tasks (ST-01 … ST-14)** across the five requested areas (A–E), ordered so that:

1. **No MCP contract breaks** (tool names + parameter names preserved; only additive optional params or removed-but-aliased params).
2. **Low-risk cleanups land first** (dead code, stale text) to shrink the diff surface before behavioral changes.
3. **Behavioral search upgrades land next** (fuzzy, semantic, find_references) with runtime feature-detection and deterministic fallbacks so CI never depends on an optional external service.
4. **Consolidations land last** because they touch the most call sites.

**Dual-codebase constraint**: two byte-near-identical copies exist — [`mcp-servers/bridge/`](mcp-servers/bridge/) and [`extension/mcp-servers/bridge/`](extension/mcp-servers/bridge/). Both are live distribution artifacts. **Every file change in this plan must be applied to both copies.** A repo-level sync script is out of scope for this plan but is flagged as a follow-up ADR candidate (see Section 7, R-6).

---

## 1. Technical Specification

### 1.1 Goals

| # | Goal | Success Criterion |
|---|------|-------------------|
| G1 | Make `search_codebase` modes honest and useful | `fuzzy` performs real approximate matching; `semantic` performs embedding-based ranking when a server is available, else labeled BM25 fallback |
| G2 | Eliminate `find_references` false positives | Word-boundary + AST-aware matching; searching `io` does not match `action` |
| G3 | Make `web_search` predictable | Clear description, real error surfacing, optional DuckDuckGo fallback when no Exa key |
| G4 | Remove all verified dead code | 12 dead registry entries, dead `_lazy_tool`, dead import, dead `partial_result`, stale hints gone |
| G5 | Consolidate overlapping tools without breaking agents | `auto_analyze_whiteboard` merged into `get_whiteboard_state`; single shared AST singleton |
| G6 | Make `max_tokens` real | Output truncation honored in every tool that declares it |

### 1.2 Non-Goals

- Rewriting the MCP transport or FastMCP layer.
- Removing either copy of the dual codebase (needs VP/CPO decision, see R-6).
- Adding new external paid dependencies. All new capabilities must be stdlib-first with optional extras.
- Changing tool names or required parameter names (MCP contract freeze).

### 1.3 Communication / Data Flow (unchanged boundaries)

This plan does not alter the Frontend↔Backend boundary. All changes stay inside the Python MCP bridge process:

```
Zoo Code Agent (LLM)
   │  MCP/SSE (port 9027), tool name + JSON args
   ▼
vibezoo_mcp_bridge.py  ──register_all_tools()──►  bridge/tools/*.py  (16 register() fns)
   │                                                    │
   │                              ┌─────────────────────┼───────────────────┐
   │                              ▼                     ▼                   ▼
   │                       search_engine.py      ast_engine.py      result_ranker.py
   │                       (ripgrep→git→walk)    (tree-sitter)      (BM25 / NEW: embed)
   │                              │                     │                   │
   │                              ▼                     ▼                   ▼
   │                        file_cache.py  ◄── shared ast singleton   (optional) local
   │                        (L1/L2 cache)        (NEW shared module)   embedding server
   ▼
Structured markdown result back to agent
```

The only *new* cross-process hop is the optional HTTP call to a local embedding server (Section A.2). It is fully optional and time-boxed.

---

## 2. Architecture Decisions & Area Specifications

Each subsection gives: the problem (verified), the design, exact file/line targets, and edge cases. Effort/Risk/Outcome trade-offs are in Section 4.

---

### SECTION A — Search Enhancement (Priority 1)

#### A.1 Real fuzzy matching for `mode="fuzzy"`

**Problem (verified)**: In [`scout.py`](mcp-servers/bridge/tools/scout.py:66) `_search_codebase_impl`, the `mode` value `"fuzzy"` flows into [`SearchEngine.search()`](mcp-servers/bridge/search_engine.py:66) which never branches on fuzzy — behavior is identical to `"auto"`. The mode is advertised but fake.

**Design** — implement fuzzy at the *ranking/filter* layer, not the ripgrep layer (ripgrep has no fuzzy; shelling out to `rg --fuzzy` is not portable):

1. Add a stdlib-only trigram similarity scorer in a new module [`mcp-servers/bridge/fuzzy_matcher.py`](mcp-servers/bridge/fuzzy_matcher.py) (new file):
   - `trigram_similarity(a: str, b: str) -> float` using set-based Dice coefficient on character 3-grams.
   - `fuzzy_filter(query: str, results: list[dict], threshold: float = 0.35) -> list[dict]` that scores each result's `content` and `file` fields, keeps results ≥ threshold, and annotates `result["fuzzy_score"]`.
   - Rationale for trigram over Levenshtein: O(n) per candidate, no `python-Levenshtein` dependency, good enough for identifier typo tolerance. Levenshtein can be added later behind the same interface.
2. Wire into [`_search_codebase_impl()`](mcp-servers/bridge/tools/scout.py:95): after `engine.search(...)` returns, when `mode == "fuzzy"`, broaden the initial text search (use a relaxed query — strip regex metacharacters, or run with the query's longest alphanumeric token) then apply `fuzzy_filter` and cap to `max_results`.
3. Update the [`search_codebase`](mcp-servers/bridge/tools/scout.py:702) docstring to state fuzzy = trigram approximate match with threshold.

**Edge cases**: query shorter than 3 chars (fall back to substring match); binary/empty content (skip); very large result sets (pre-cap to 500 before scoring to bound cost).

#### A.2 True semantic search (embedding-based, optional)

**Problem (verified)**: `mode="semantic"` at [`scout.py:98`](mcp-servers/bridge/tools/scout.py:98) calls [`ResultRanker.rank()`](mcp-servers/bridge/result_ranker.py:11), which is BM25 keyword overlap — not semantic. No embedding code exists anywhere in the repo (verified: zero hits for `embed|nomic|8089` in both Python and TS).

**Design** — add an *optional, feature-detected* embedding provider with a deterministic fallback:

1. New module [`mcp-servers/bridge/embedding_client.py`](mcp-servers/bridge/embedding_client.py) (new file):
   - `class EmbeddingClient` with `is_available() -> bool` (2s probe) and `embed(texts: list[str]) -> list[list[float]] | None`.
   - Endpoint resolution order: env `VIBEZOO_EMBED_URL` → default `http://localhost:8089`. Model name via env `VIBEZOO_EMBED_MODEL` (default `nomic-embed-text`).
   - **Runtime shape probing**: try Ollama-style `POST /api/embeddings` first; on 404 fall back to OpenAI-style `POST /v1/embeddings`. Cache whichever worked for the process lifetime. This makes the "potentially outdated API shape" risk contained and self-healing.
   - Timeout 5s per batch, batch size 32. On any network/schema error → return `None` (never raise).
   - Cosine similarity `rank_by_embedding(query, results)`.
2. Wire into [`_search_codebase_impl()`](mcp-servers/bridge/tools/scout.py:97): when `mode == "semantic"`:
   - If `EmbeddingClient.is_available()` → embed query + each candidate `content`, rank by cosine, label each result `rank_source="embedding"`.
   - Else → existing [`ResultRanker`](mcp-servers/bridge/result_ranker.py:8) BM25 path, and append a markdown note `> ⚠️ semantic: embedding server unavailable, used BM25 keyword ranking`.
3. Index cost note: we rank the *candidate set returned by the text search*, not a full-corpus embedding index. A persistent embedding index is a deliberate non-goal for this phase (keeps CI hermetic and avoids a large new subsystem). Flag as future ADR.

**Edge cases**: server up but wrong model (probe catches, fallback); mixed-language query (nomic handles); >500 candidates (pre-cap like A.1); server returns non-200 mid-run (per-batch `None`, partial results kept with note).

#### A.3 Fix `find_references` false positives

**Problem (verified)**: [`scout.py:310`](mcp-servers/bridge/tools/scout.py:310) uses `if symbol not in line: continue` — substring match. Searching `io` matches `action`, `configuration`.

**Design**:
1. Precompile a word-boundary regex per symbol in [`_find_references_impl`](mcp-servers/bridge/tools/scout.py:260): `pattern = re.compile(r'\b' + re.escape(symbol) + r'\b')` and replace the substring check with `if not pattern.search(line): continue`.
2. The ref-type classifiers at [`scout.py:317-326`](mcp-servers/bridge/tools/scout.py:317) already use f-string containment (`f"new {symbol}"` etc.) — these are mostly safe but tighten the `call` check at [`scout.py:321`](mcp-servers/bridge/tools/scout.py:321) to also use the boundary regex so `myio(` doesn't match symbol `io`.
3. Add a `# SRF` (symbol-reference) comment noting the boundary contract.

**Edge cases**: symbols containing regex metacharacters (`re.escape` handles); symbols that are substrings of operators; non-ASCII identifiers (`\b` is Unicode-aware in Python 3 `re`, acceptable).

#### A.4 Make search-result caching work

**Problem**: Every search re-scans. Research (L3) asks for caching. [`FileCache`](mcp-servers/bridge/file_cache.py:25) already implements L1 memory LRU + L2 disk catalog + L3 mtime invalidation.

**Design**: do **not** build a parallel cache. Reuse `FileCache`:
1. Add a query-result memo layer inside [`SearchEngine.search()`](mcp-servers/bridge/search_engine.py:66): key = `(query, file_patterns, mode, context_lines, root_mtime_bucket)`, value = serialized results, TTL 20s, stored in the existing `FileCache` L1 (it is already an LRU with a lock — thread-safe).
2. Invalidate on mtime change (L3 already does this per-file; the memo just needs the root bucket to bump when any cached file changes).
3. Keep TTL short (≤20s) so agents doing edit→search→edit loops never see stale results. This is a latency optimization, not a correctness layer.

**Edge cases**: rapid successive edits (short TTL + mtime bucket covers); multi-root concurrent searches (key includes root).

---

### SECTION B — Web Search Simplification (Priority 2)

#### B.1 Honest `engine` parameter + DuckDuckGo fallback

**Problem (verified)**: [`web_search()`](mcp-servers/bridge/tools/web.py:156) docstring says "Exa API 기반 신경망 웹 검색". The `engine` param accepts anything; only `exa`/`auto` work and everything silently becomes Exa ([`web.py:167-168`](mcp-servers/bridge/tools/web.py:167)). No fallback when `EXA_API_KEY` is absent ([`web.py:46-47`](mcp-servers/bridge/tools/web.py:46) returns `[]`).

**Design**:
1. Keep the `engine` parameter (MCP contract freeze) but define real behavior: `"auto"` (default) = try Exa if key present, else DuckDuckGo; `"exa"` = Exa only; `"ddg"` = DuckDuckGo only. Unknown values → return a clear error string (not silent default).
2. Add `_duckduckgo_search(query, max_results)` in [`web.py`](mcp-servers/bridge/tools/web.py:21) using the stdlib-only DuckDuckGo HTML endpoint (`https://html.duckduckgo.com/html/?q=...`), parsing result anchors with the existing [`_html_to_markdown`](mcp-servers/bridge/utils.py) helper or a minimal regex. No new dependency.
3. Rewrite the docstring to: "웹 검색. EXA_API_KEY가 있으면 Exa neural search, 없으면 DuckDuckGo로 폴백. engine: auto|exa|ddg".

**Edge cases**: DDG rate-limit (HTTP 202/403 → return error text, not `[]`); no network (URLError → surfaced message); HTML shape change (regex tolerant, worst case returns "no results parsed" message).

#### B.2 Real error logging instead of silent `except: return []`

**Problem (verified)**: [`web.py:82-83`](mcp-servers/bridge/tools/web.py:82) `except Exception: return []` swallows everything, so agents cannot distinguish "no key" from "network down" from "bad response".

**Design**: replace the bare except with structured capture using the existing [`ErrorRegistry`](mcp-servers/bridge/error_handler.py) (same pattern as [`BaseTool.report_error`](mcp-servers/bridge/tools/_base.py:33)). Return `[]` still (contract) but record the exception and include a short reason string in a companion dict so `web_search()` can surface "검색 실패: <reason>" when empty. Add bounded retry (Section E.2).

---

### SECTION C — Dead Code Cleanup (Priority 3)

All verified in Phase 2 and re-confirmed by architect. Pure deletions / text fixes, zero behavioral risk.

| ID | File:Line | Change |
|----|-----------|--------|
| C-1 | [`integrated.py:303-323`](mcp-servers/bridge/tools/integrated.py:303) | Remove 12 dead `_tool_registry` entries (`check_quality`, `generate_tests`, `analyze_coverage`, `explain_code`, `analyze_changes`, `review_pr`, `refactor_across_files`, `learn_project`, `recall_project`, `learn_preference`, `get_preferences`, and the unused `analyze_changes` getter). Keep only the 8 with working lazy getters. |
| C-2 | [`integrated.py:337-343`](mcp-servers/bridge/tools/integrated.py:337) | Delete dead `_lazy_tool()` function. |
| C-3 | [`deep_analyzer.py:7`](mcp-servers/bridge/tools/deep_analyzer.py:7) | Delete unused `import subprocess`. |
| C-4 | [`_base.py:27-31`](mcp-servers/bridge/tools/_base.py:27) | Delete dead `partial_result()` stub. |
| C-5 | [`github_diver.py:52`](mcp-servers/bridge/tools/github_diver.py:52) | Fix hint `github_explore_repository(...)` → `explore_github(repo='...')`. |
| C-6 | [`github_diver.py:102`](mcp-servers/bridge/tools/github_diver.py:102) | Fix hint `github_read_file(...)` → `explore_github(repo='...', file_path='...')`. |
| C-7 | [`deep_analyzer.py:530`](mcp-servers/bridge/tools/deep_analyzer.py:530) | `include_external` param: implement filtering (skip calls to external lib symbols) — preferred over removal to keep contract. |
| C-8 | [`scout.py:10`](mcp-servers/bridge/tools/scout.py:10) | Remove unused `Counter` import (keep `defaultdict`). |

**Note on C-1**: removing registry *entries* does not remove the MCP tools themselves — those tools are registered independently in their own modules ([`tester.py`](mcp-servers/bridge/tools/tester.py), [`analysis.py`](mcp-servers/bridge/tools/analysis.py), [`knowledge.py`](mcp-servers/bridge/tools/knowledge.py)). Only the unused lazy-binding map shrinks. No agent-facing change.

---

### SECTION D — Tool Consolidation (Priority 4)

#### D.1 Merge `auto_analyze_whiteboard` into `get_whiteboard_state`

**Problem (verified)**: [`auto_analyze_whiteboard()`](mcp-servers/bridge/tools/ux_coordinator.py:286) only calls [`get_whiteboard_state()`](mcp-servers/bridge/tools/whiteboard.py:988) plus appends generic suggestions. Thin wrapper = agent confusion.

**Design** (contract-safe merge):
1. Add optional param `analyze: bool = False` to [`get_whiteboard_state()`](mcp-servers/bridge/tools/whiteboard.py:988). When `True`, append the suggestion block currently produced in `ux_coordinator.py`.
2. Keep [`auto_analyze_whiteboard()`](mcp-servers/bridge/tools/ux_coordinator.py:286) registered for one release as a thin alias that calls `get_whiteboard_state(analyze=True)` and emits a `> ⚠️ deprecated: use get_whiteboard_state(analyze=True)` note. This avoids a hard contract break while steering agents.
3. Remove the alias + its registration in a follow-up release (tracked, not in this plan's hard scope).

#### D.2 Consolidate the duplicated `_get_ast_engine()` singleton

**Problem (verified)**: identical singleton copy-pasted in 5 files — [`scout.py:45`](mcp-servers/bridge/tools/scout.py:45), [`analysis.py:35`](mcp-servers/bridge/tools/analysis.py:35), [`deep_analyzer.py:36`](mcp-servers/bridge/tools/deep_analyzer.py:36), [`reviewer.py:37`](mcp-servers/bridge/tools/reviewer.py:37), [`tester.py:34`](mcp-servers/bridge/tools/tester.py:34).

**Design**: create [`mcp-servers/bridge/ast_singleton.py`](mcp-servers/bridge/ast_singleton.py) (new file) exposing `get_ast_engine() -> AstEngine` (lazy, module-global). Replace all 5 local `_get_ast_engine()` bodies with `from bridge.ast_singleton import get_ast_engine as _get_ast_engine` so internal call sites are untouched. Bonus: a single shared engine also shares tree-sitter parser warm-up across tools.

#### D.3 Evaluate `analyze_uploaded_file` vs `auto_analyze_after_drop` merger

**Finding (verified)**: [`auto_analyze_after_drop()`](mcp-servers/bridge/tools/ux_coordinator.py:136) is a **workflow superset** (session tracking + tool-chain suggestions) that delegates real analysis to [`analyze_file()`](mcp-servers/bridge/tools/file_analyzer.py:345). This is *proper composition*, not harmful duplication.

**Decision**: **Do not merge in this phase.** Keep both, but document the relationship in both docstrings (`analyze_uploaded_file` = direct analysis; `auto_analyze_after_drop` = post-drop workflow that calls it). Merging would couple a clean analysis tool to dropzone session state for no agent-visible gain. Revisit only if agents demonstrably pick the wrong one.

---

### SECTION E — Quality & Robustness (Priority 5)

#### E.1 Implement `max_tokens` truncation

**Problem (verified)**: `max_tokens` declared but unused in [`summarize_architecture`](mcp-servers/bridge/tools/scout.py:731), [`review_project`](mcp-servers/bridge/tools/integrated.py:400), [`find_bugs`](mcp-servers/bridge/tools/integrated.py:544), [`suggest_refactor`](mcp-servers/bridge/tools/integrated.py:757), [`generate_docs`](mcp-servers/bridge/tools/integrated.py:886).

**Design**: add a shared helper [`_truncate_to_tokens(text, max_tokens)`](mcp-servers/bridge/utils.py) using the `chars ≈ tokens × 4` heuristic (research L4). At each tool's return point, when `max_tokens > 0`, truncate the assembled markdown and append `\n\n... [truncated to ~N tokens]`. Centralizing in `utils.py` avoids 5 divergent implementations.

#### E.2 Retry logic for `web_search`

**Design**: in [`WebSearchEngine.search()`](mcp-servers/bridge/tools/web.py:33), wrap the `urlopen` in a small retry loop — 2 retries, exponential backoff (0.5s, 1.5s), only on `URLError`/timeout/5xx; never retry on 4xx (client error). Total worst-case added latency ~2s, acceptable for an agent tool.

#### E.3 Pass `context_lines` to `ResultRanker` in semantic mode

**Problem (verified)**: [`scout.py:98-100`](mcp-servers/bridge/tools/scout.py:98) calls `ranker.rank(query, search_results)` without `context_lines`; [`ResultRanker._context_density`](mcp-servers/bridge/result_ranker.py:72) reads `context_before/after` but the ranker isn't told the configured window.

**Design**: extend [`ResultRanker.rank()`](mcp-servers/bridge/result_ranker.py:11) signature to `rank(query, results, context_lines: int = 3)` and use it in `_context_density` normalization (`min(total / max(context_lines,1), 1.0)`). Update the call site to pass the tool's `context_lines`. Additive optional param — no contract break.

---

## 3. Implementation Plan — Sub-tasks for VP delegation

Dependency-ordered. Each ST is independently delegable to `code` and independently testable. **Apply every file change to both `mcp-servers/` and `extension/mcp-servers/` copies.**

### Wave 1 — Zero-risk cleanup (parallel-safe)

**ST-01 Dead code sweep**
- Files: [`integrated.py`](mcp-servers/bridge/tools/integrated.py) (C-1, C-2), [`deep_analyzer.py`](mcp-servers/bridge/tools/deep_analyzer.py) (C-3, C-7), [`_base.py`](mcp-servers/bridge/tools/_base.py) (C-4), [`scout.py`](mcp-servers/bridge/tools/scout.py) (C-8), [`github_diver.py`](mcp-servers/bridge/tools/github_diver.py) (C-5, C-6)
- Prereq: none
- **Test**: `python -c "import bridge.tools.integrated, bridge.tools.deep_analyzer, bridge.tools._base, bridge.tools.scout, bridge.tools.github_diver"` from both roots; plus full smoke in Section 5.

**ST-02 `web.py` honesty + logging + retry + DDG fallback** (B.1 + B.2 + E.2)
- Files: [`web.py`](mcp-servers/bridge/tools/web.py), [`error_handler.py`](mcp-servers/bridge/error_handler.py) (read-only reference)
- Prereq: none (independent of ST-01)
- **Test**: `python -m pytest mcp-servers/tests/test_web_search.py -q` (new file, mocks `urlopen`; asserts Exa path, DDG fallback when no key, retry-on-timeout, error surfaced not silent).

### Wave 2 — Search behavior (depends on Wave 1 imports staying clean)

**ST-03 Shared AST singleton** (D.2)
- Files: new [`ast_singleton.py`](mcp-servers/bridge/ast_singleton.py); edit 5 consumers
- Prereq: ST-01 (so the edited files are already clean)
- **Test**: `python -c "from bridge.ast_singleton import get_ast_engine; a=get_ast_engine(); b=get_ast_engine(); assert a is b"` from both roots.

**ST-04 `find_references` word-boundary fix** (A.3)
- Files: [`scout.py`](mcp-servers/bridge/tools/scout.py) lines 309-326
- Prereq: none
- **Test**: `python -m pytest mcp-servers/tests/test_find_references.py -q` (new; fixture file containing `action`/`configuration` and a real `io` symbol; assert no false positive, real ref still found).

**ST-05 Fuzzy mode** (A.1)
- Files: new [`fuzzy_matcher.py`](mcp-servers/bridge/fuzzy_matcher.py); [`scout.py`](mcp-servers/bridge/tools/scout.py)
- Prereq: none
- **Test**: `python -m pytest mcp-servers/tests/test_fuzzy_search.py -q` (new; trigram similarity unit tests + integration: typo query `SerchEngine` still finds `SearchEngine`).

**ST-06 Semantic embedding mode** (A.2 + E.3)
- Files: new [`embedding_client.py`](mcp-servers/bridge/embedding_client.py); [`scout.py`](mcp-servers/bridge/tools/scout.py); [`result_ranker.py`](mcp-servers/bridge/result_ranker.py) (context_lines param)
- Prereq: ST-05 (shares the same rerank call site)
- **Test**: `python -m pytest mcp-servers/tests/test_semantic_search.py -q` (new; `EmbeddingClient` tested against a stub HTTP server; the `search_codebase` semantic path tested twice — server up (embedding rank) and down (BM25 fallback + note)). **Must not require a real server in CI.**

### Wave 3 — Caching, truncation, consolidation (depends on Wave 2)

**ST-07 Search result caching** (A.4)
- Files: [`search_engine.py`](mcp-servers/bridge/search_engine.py), [`file_cache.py`](mcp-servers/bridge/file_cache.py) (reuse, minimal edit)
- Prereq: ST-05/ST-06 (cache sits under the rerank layer)
- **Test**: `python -m pytest mcp-servers/tests/test_search_cache.py -q` (new; same query twice → second served from memo; file mtime bump → invalidated).

**ST-08 `max_tokens` truncation** (E.1)
- Files: [`utils.py`](mcp-servers/bridge/utils.py) (helper) + the 5 tools listed in E.1
- Prereq: none logically, but sequence after ST-06 to avoid rebase churn in `scout.py`/`integrated.py`
- **Test**: `python -m pytest mcp-servers/tests/test_max_tokens.py -q` (new; each tool with `max_tokens=10` returns ≤ ~40 chars + truncation marker).

**ST-09 Whiteboard merge** (D.1)
- Files: [`whiteboard.py`](mcp-servers/bridge/tools/whiteboard.py), [`ux_coordinator.py`](mcp-servers/bridge/tools/ux_coordinator.py)
- Prereq: none
- **Test**: `python -m pytest mcp-servers/tests/test_whiteboard_merge.py -q` (new; `get_whiteboard_state(analyze=True)` returns state + suggestions; alias still works + deprecation note).

---

## 4. Design Options & Trade-offs (per mandatory 3-option rule)

For the two decisions with real trade-offs, three options each. VP decides.

### Decision 1 — Semantic search strategy (A.2)

| | Effort | Risk | Outcome |
|---|--------|------|---------|
| **A — Full embedding index** (persist corpus embeddings, ANN search) | High (multi-day, new subsystem, index invalidation) | High (storage, staleness, CI needs server or heavy mocking) | Best recall; true semantic over whole repo |
| **B — Candidate rerank (RECOMMENDED)** | Medium (1 module + wiring) | Low (optional, graceful fallback, hermetic CI) | Big quality jump over BM25 for modest cost; no index to maintain |
| **C — Re-label only** ("semantic"→"ranked") | Trivial | None | Honest but no new capability; fails G1 |

**Recommendation: B.** It satisfies G1 with contained risk and keeps CI independent of any external service.

### Decision 2 — Dual codebase sync

| | Effort | Risk | Outcome |
|---|--------|------|---------|
| **A — Single source + build-time copy** | Medium (pick canonical, add sync script/CI check) | Medium (must not break extension packaging) | Permanent fix; no drift ever |
| **B — Manual dual-apply (this plan)** | Low now | Medium (human can forget one copy) | Works today; drift risk persists |
| **C — Symlink/junction** | Low | High on Windows/OneDrive (this repo is under OneDrive) | Fragile; not recommended |

**Recommendation: B for this plan (explicit dual-apply), with A filed as a follow-up ADR (R-6).** C is rejected due to OneDrive path.

---

## 5. Testing Strategy

**New test directory**: `mcp-servers/tests/` (mirrored at `extension/mcp-servers/tests/`). Framework: `pytest` (stdlib `unittest` acceptable if pytest absent; tests must avoid network and optional deps).

| Test file | Covers | CI-safe? |
|-----------|--------|----------|
| `test_web_search.py` | ST-02 | ✅ mocks `urlopen` |
| `test_find_references.py` | ST-04 | ✅ fixture files only |
| `test_fuzzy_search.py` | ST-05 | ✅ pure logic |
| `test_semantic_search.py` | ST-06 | ✅ stub HTTP server; no real embedding server |
| `test_search_cache.py` | ST-07 | ✅ tmp dirs |
| `test_max_tokens.py` | ST-08 | ✅ string assertions |
| `test_whiteboard_merge.py` | ST-09 | ✅ fixture JSON |

**Whole-suite smoke (run from each root after every wave):**
```powershell
python -c "from bridge.tools import register_all_tools; from fastmcp import FastMCP; m=FastMCP('t'); register_all_tools(m); print('OK')"
python -m pytest mcp-servers/tests -q
```
**CI gate**: all new tests pass on both copies + the import smoke returns `OK`. No test may require Exa key, embedding server, ripgrep, or tree-sitter (guard with `pytest.importorskip` / availability checks).

---

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| R-1 Embedding server API shape differs from assumption | Medium | Low | Runtime shape-probing (Ollama→OpenAI), fallback to BM25 |
| R-2 Fuzzy threshold too loose/tight hurts results | Medium | Low | Tunable threshold const; tests pin behavior |
| R-3 Dual-apply forgets one copy | Medium | Medium | Section 5 smoke runs on **both** roots; VP gate checks both |
| R-4 Word-boundary regex misses valid refs (e.g. `obj.symbol`) | Low | Medium | `\b` still matches after `.`; tests include dotted access |
| R-5 Removing registry entries breaks an unseen caller | Low | Low | Entries had `None` values and no callers (verified); import smoke catches regressions |
| R-6 Dual codebase is itself the root design flaw | — | Strategic | File ADR for single-source-of-truth (Decision 2, Option A) |
| R-7 DDG HTML scraping breaks on shape change | Medium | Low | Tolerant parse + clear failure message; Exa path unaffected |

---

## 7. Follow-ups (out of scope, recommend ADRs)

- **R-6 / ADR-1**: Single source of truth for `bridge/` (eliminate dual copy). 
- **ADR-2**: Persistent embedding index for whole-repo semantic search (Decision 1 → Option A) if candidate-rerank proves insufficient.
- **ADR-3**: Remove deprecated `auto_analyze_whiteboard` alias after one release.
- **L5**: Update pinned ripgrep URL in [`setup.py:404`](mcp-servers/bridge/tools/setup.py:404).

---

## 8. Acceptance Checklist (for Ask/VP audit)

- [ ] `fuzzy` mode returns trigram-scored approximate matches (test pins it).
- [ ] `semantic` mode uses embeddings when available, labeled BM25 otherwise.
- [ ] `find_references("io")` does not match `action`.
- [ ] `web_search` with no key uses DuckDuckGo and never fails silently.
- [ ] 12 dead registry entries + dead fns/imports removed; import smoke `OK` on both roots.
- [ ] Single shared AST singleton; `get_ast_engine() is get_ast_engine()`.
- [ ] `get_whiteboard_state(analyze=True)` supersedes `auto_analyze_whiteboard` (alias deprecated).
- [ ] All `max_tokens` params truncate with marker.
- [ ] All new tests green on both copies; no optional dependency required in CI.
