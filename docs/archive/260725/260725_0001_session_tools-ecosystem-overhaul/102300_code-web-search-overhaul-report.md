# Code Task Report: ST-02 Web Search Overhaul

## Task Summary
Overhauled `web_search` tool: added DuckDuckGo fallback, honest `engine` parameter behavior, structured error logging (replacing silent `except: return []`), and retry logic with exponential backoff. Dual-applied to both root and extension copies.

## Actions Taken

### B.1: Honest `engine` parameter + DuckDuckGo fallback
- Added `_duckduckgo_search(query, max_results)` method using stdlib-only DuckDuckGo HTML endpoint (`https://html.duckduckgo.com/html/?q=...`), parsing result anchors with regex. No new dependencies.
- Added `_decode_ddg_url()` helper to extract real URLs from DDG redirect links (`//duckduckgo.com/l/?uddg=...`).
- Refactored `WebSearchEngine.search()` to dispatch based on `engine` parameter:
  - `"auto"` (default): Exa if `EXA_API_KEY` present, else DuckDuckGo
  - `"exa"`: Exa only (raises ValueError if no key)
  - `"ddg"`: DuckDuckGo only
  - Unknown values: returns `[]` with `WEB/search/001` error in `_last_error`
- Changed `web_search` tool default from `engine="exa"` to `engine="auto"`.
- Rewrote docstring to: "웹 검색. EXA_API_KEY가 있으면 Exa neural search, 없으면 DuckDuckGo로 폴백. engine: auto|exa|ddg"
- Output now shows the actual engine used (not hardcoded "exa").

### B.2: Real error logging instead of silent `except: return []`
- Replaced bare `except Exception: return []` with structured error capture:
  - Stores error reason in `self._last_error` with error code `WEB/search/002`
  - Logs via `logger.error()` with `exc_info=True`
  - Records to `ErrorRegistry` (best-effort, from `bridge.error_handler`)
  - Still returns `[]` (contract preserved)
- `web_search()` tool surfaces `"검색 실패: <reason>"` when results are empty.

### E.2: Retry logic
- Added `_urlopen_with_retry(req, timeout)` static method:
  - 2 retries with exponential backoff (0.5s, 1.5s) — total worst-case ~2s
  - Retries on `URLError`, `TimeoutError`, `OSError`, and 5xx `HTTPError`
  - Never retries on 4xx (client error) — raises immediately
- Both `_exa_search()` and `_duckduckgo_search()` use this retry wrapper.

### Tests
- Created `test_web_search.py` with 15 test cases across 5 test classes:
  - `TestExaSearch`: Exa path with mocked urlopen, no-key error
  - `TestDDGFallback`: DDG fallback on auto, explicit ddg, URL decoding
  - `TestRetryLogic`: retry on URLError, no-retry on 4xx, retry on 5xx, exhaustion
  - `TestErrorSurfacing`: error surfaced not silent, unknown engine error, Exa error
  - `TestEngineAutoResolution`: auto→exa when key, auto→ddg when no key
- All tests CI-safe (no real API calls, `urlopen` mocked).

## Result
✅ Success — all changes implemented and verified.

### Verification Evidence
- Import smoke test: `python -c "from bridge.tools.web import register; print('OK')"` → `OK` (both roots)
- Test suite: `python -m unittest tests.test_web_search -v` → `Ran 15 tests in 0.028s` → `OK` (both copies)

## Issues Discovered
- `keyring` package is installed on this system, so `EXA_API_KEY` stored in keyring persists even when the env var is cleared. Tests that simulate "no key" must mock `_get_api_key()` directly rather than relying on `@patch.dict(os.environ, {}, clear=True)`. Fixed in test file.

## Affected File List
- `mcp-servers/bridge/tools/web.py` (full rewrite of WebSearchEngine + web_search tool)
- `extension/mcp-servers/bridge/tools/web.py` (identical changes)
- `mcp-servers/tests/test_web_search.py` (new file, 15 tests)
- `extension/mcp-servers/tests/test_web_search.py` (identical new file)
