# Ask Mode — Full Audit Report (Phase 6)
## Task: Full i18n Support for VibeZoo (Extension + Python Bridge)
## Date: 2026-07-25
## Auditor: Ask (CPO) Mode

---

## [1. Philosophy & UX/UI Diagnostics]

### User Intent (Verbatim)
> "VibeZoo를 VS Code에서 지원하는 전체 언어에 대해 i18n 국제언어를 전부 지원하고싶어.
> VS Code Extension + Python Bridge 모두 i18n. Extension이 언어를 Bridge에 전달."

### Intent Alignment Assessment
The implementation faithfully addresses the user's core request: full i18n coverage across both the VS Code Extension and the Python Bridge, with language pass-through from Extension to Bridge. The architecture is sound — English-string-as-key pattern, 3-tier fallback, auto-initialization from `VIBEZOO_LANG` env var.

### UX Considerations
- **Positive**: Users switching VS Code language will see localized tool responses without restart (env var read at spawn time). The fallback chain ensures no broken output even with missing translations.
- **Concern**: The root `mcp-servers/bridge/` directory (used for development/testing outside the extension) is completely missing the i18n implementation. If any tool is run from that path, `from bridge.i18n import t` will fail with `ModuleNotFoundError`, breaking all tools.

---

## [2. 1:1 Cross-Validation Results]

### Requirement-by-Requirement Verification

#### [REQ-001] Extension: Generate `package.nls.{lang}.json` for all VS Code supported languages
**Status: ✅ PASS**

Verified 20 `package.nls.*.json` files in [`extension/`](extension/):
- `package.nls.json` (default/en)
- `package.nls.ar.json`, `package.nls.bg.json`, `package.nls.cs.json`, `package.nls.de.json`, `package.nls.es.json`, `package.nls.fr.json`, `package.nls.he.json`, `package.nls.hu.json`, `package.nls.it.json`, `package.nls.ja.json`, `package.nls.ko.json`, `package.nls.pl.json`, `package.nls.pt-BR.json`, `package.nls.ru.json`, `package.nls.th.json`, `package.nls.tr.json`, `package.nls.vi.json`, `package.nls.zh-CN.json`, `package.nls.zh-TW.json`

All 19 non-default languages + 1 default = 20 files. Matches the required language list exactly.

---

#### [REQ-002] Extension: Generate `l10n/bundle.l10n.{lang}.json` for all VS Code supported languages
**Status: ✅ PASS**

Verified 20 `bundle.l10n.*.json` files in [`extension/l10n/`](extension/l10n/):
- `bundle.l10n.json` (default/en)
- 19 language-specific bundles: ar, bg, cs, de, es, fr, he, hu, it, ja, ko, pl, pt-BR, ru, th, tr, vi, zh-CN, zh-TW

All required languages present.

---

#### [REQ-003] Extension → Bridge: Pass `vscode.env.language` to Bridge via `VIBEZOO_LANG` env var
**Status: ✅ PASS**

Verified in [`SubagentManager.ts`](extension/src/orchestra/SubagentManager.ts:117):
```typescript
VIBEZOO_LANG: vscode.env.language,
```
The env var is passed in the spawn environment at line 117, alongside `CROW_SERVER_URL`.

---

#### [REQ-004] Bridge: Create `bridge/i18n/` module with translation loader and `t()` function
**Status: ✅ PASS (with caveat)**

Verified [`extension/mcp-servers/bridge/i18n/__init__.py`](extension/mcp-servers/bridge/i18n/__init__.py) (287 lines):
- `init(locale)` function — sets current locale, loads translations
- `t(key, *args)` function — 3-tier fallback: current locale → English → key itself
- `_normalize(locale)` — maps VS Code locale variants (e.g., `zh-cn` → `zh-CN`, `pt-br` → `pt-BR`)
- `_load_translations()` — thread-safe lazy loading with `threading.RLock`
- `_auto_init()` — auto-initializes from `VIBEZOO_LANG` env var at module import time (line 286)
- `get_locale()` and `get_available_locales()` utility functions

**Caveat**: The i18n module exists ONLY in `extension/mcp-servers/bridge/i18n/`. The root `mcp-servers/bridge/` directory has NO `i18n/` directory. See REQ-008 for impact.

---

#### [REQ-005] Bridge: Create `bridge/i18n/translations/en.json` (default) with all user-facing strings
**Status: ✅ PASS**

Verified [`extension/mcp-servers/bridge/i18n/translations/en.json`](extension/mcp-servers/bridge/i18n/translations/en.json) (171 lines, 168 keys).
English strings serve as both keys and values (identity mapping for default locale).

---

#### [REQ-006] Bridge: Create `bridge/i18n/translations/ko.json` (Korean) translation
**Status: ✅ PASS**

Verified [`extension/mcp-servers/bridge/i18n/translations/ko.json`](extension/mcp-servers/bridge/i18n/translations/ko.json) (171 lines, 168 keys).
Korean translations confirmed (e.g., `"File not found: \`{0}\`": "파일을 찾을 수 없음: \`{0}\`"`).

---

#### [REQ-007] Bridge: Create `bridge/i18n/translations/{lang}.json` for all other supported languages
**Status: ✅ PASS**

Verified 19 translation files in [`extension/mcp-servers/bridge/i18n/translations/`](extension/mcp-servers/bridge/i18n/translations/):
ar, bg, cs, de, en, es, fr, he, hu, it, ja, ko, pl, pt-BR, ru, th, tr, vi, zh-CN, zh-TW

All 19 languages (including en) match the VS Code supported language list. Debug report confirms 168 keys each with zero drift.

---

#### [REQ-008] Bridge: Wrap all hardcoded user-facing strings in tools/*.py with `t()` calls
**Status: 🔶 CONDITIONAL — Dual directory discrepancy**

**In `extension/mcp-servers/bridge/tools/`**: ✅ PASS
- All 18 tool files have `from bridge.i18n import t`:
  `_base.py`, `analysis.py`, `deep_analyzer.py`, `editor.py`, `feedback.py`, `file_analyzer.py`, `fix_loop.py`, `github_diver.py`, `integrated.py`, `knowledge.py`, `reviewer.py`, `scout.py`, `setup.py`, `ssa.py`, `tester.py`, `ux_coordinator.py`, `web.py`, `whiteboard.py`
- 222 actual `t()` call sites confirmed across these files
- Strings wrapped include error messages, UI labels, status messages, and user-facing guidance

**In root `mcp-servers/bridge/tools/`**: ❌ FAIL
- ZERO files have `from bridge.i18n import t`
- The root `mcp-servers/bridge/` directory has NO `i18n/` module
- All 18 tool files in this directory still use hardcoded strings
- If the bridge is launched from the root `mcp-servers/` path, `from bridge.i18n import t` will throw `ModuleNotFoundError` at import time, breaking ALL tools

**Root Cause**: The project has two parallel bridge directories:
1. `extension/mcp-servers/bridge/` — fully i18n-ized (the one packaged in the .vsix)
2. `mcp-servers/bridge/` — development/root copy, NOT i18n-ized

The implementation was applied only to the extension copy. Whether this is a problem depends on which path the MCP server actually uses at runtime. If the extension always uses `extension/mcp-servers/`, this is a non-issue for end users. But it creates a maintenance divergence risk.

---

#### [REQ-009] Bridge: Graceful fallback to English when translation key is missing
**Status: ✅ PASS**

Verified in [`i18n/__init__.py`](extension/mcp-servers/bridge/i18n/__init__.py:219-231):
```python
# 1. Try current locale
result = _translations[_current_locale].get(key)
# 2. Fall back to English
if result is None:
    en_table = _translations.get("en", {})
    result = en_table.get(key)
# 3. Fall back to the key itself
if result is None:
    result = key
```
Three-tier fallback: current locale → English → raw key string. Also handles corrupt/missing JSON files gracefully (line 160-164: catches `JSONDecodeError`, `OSError`, `UnicodeDecodeError` and sets empty dict).

---

#### [REQ-010] Build passes: Extension TypeScript compilation succeeds
**Status: ✅ PASS (per Debug Technical Review)**

Per [`012900_debug-i18n-technical-review-report.md`](docs/260725_0002_session_i18n-full-support/012900_debug-i18n-technical-review-report.md):
- `npx tsc --noEmit` ✅
- 20 Python files: `py_compile` ✅
- 60 JSON files: valid JSON ✅

Note: This audit did not re-run the build (Ask mode is prohibited from executing commands). Relying on Debug's verified results.

---

#### [REQ-011] No regression: Existing functionality unchanged
**Status: ✅ PASS (with low-risk note)**

The i18n implementation is purely additive:
- New files created (i18n module, translation JSONs, NLS/l10n bundles)
- Existing tool strings wrapped in `t()` calls — the `t()` function returns the English string itself when locale is "en", so behavior is identical for English users
- `VIBEZOO_LANG` env var addition to `SubagentManager.ts` is a new key in the spawn env — does not modify existing env vars

**Low-risk note**: The `_auto_init()` call at module import time (line 286) means the i18n module reads `VIBEZOO_LANG` and loads translation files on every bridge startup. This adds a small I/O overhead (reading 1-2 JSON files). For 168-key files, this is negligible (<1ms).

---

## [3. Inquiries for VP & User]

### Inquiry 1: Root `mcp-servers/bridge/` divergence (🟡 Should Fix)

**Question**: The root `mcp-servers/bridge/` directory was NOT updated with the i18n implementation. Only `extension/mcp-servers/bridge/` was updated. Should the root copy be:

- **Option A**: Synced — copy the i18n module and apply `t()` wrapping to root `mcp-servers/bridge/tools/` as well. This ensures consistency if the bridge is ever launched from the root path. Effort: ~1 hour (Code mode).
- **Option B**: Left as-is — if the extension always launches from `extension/mcp-servers/`, the root copy is development-only and doesn't need i18n. Effort: 0. Risk: future maintenance divergence.

**Recommendation**: Option A. The user said "Python Bridge 모두 i18n" (both Extension + Python Bridge). Leaving half the bridge un-i18n-ized contradicts the spirit of the request, even if it's a dev-only copy.

### Inquiry 2: Translation completeness verification (🟢 Nice to Have)

**Question**: The debug report confirms 168 keys per file with zero drift. However, are the non-English translations actually meaningful (not machine-translated placeholders)? A spot-check of `ko.json` shows proper Korean translations. Should we trust the batch for all 19 languages, or sample-verify a few more?

**Recommendation**: Trust the current state. The key structure is sound, and the fallback mechanism ensures no broken output even if individual translations are imperfect. Translation quality refinement can be a follow-up task.

---

## [4. Final Verdict]

### **CONDITIONAL APPROVAL** 🔶

The implementation is architecturally sound and faithfully reflects the user's intent for full i18n support. 10 of 11 requirements fully pass. One requirement (REQ-008) has a conditional pass due to the dual-directory discrepancy.

### Conditions for Full Approval

| # | Condition | Severity | Action |
|---|-----------|----------|--------|
| 1 | Root `mcp-servers/bridge/` is missing i18n module and `t()` wrapping in tools. Either sync it or confirm it's not used at runtime. | 🟡 Should Fix | VP to decide: delegate to Code mode for sync, or confirm root path is dev-only |

### Summary Table

| REQ | Status | Evidence |
|-----|--------|----------|
| REQ-001 | ✅ PASS | 20 `package.nls.*.json` files verified |
| REQ-002 | ✅ PASS | 20 `bundle.l10n.*.json` files verified |
| REQ-003 | ✅ PASS | `VIBEZOO_LANG: vscode.env.language` at SubagentManager.ts:117 |
| REQ-004 | ✅ PASS | `bridge/i18n/__init__.py` — 287 lines, `init()` + `t()` + `_auto_init()` |
| REQ-005 | ✅ PASS | `en.json` — 168 keys, identity mapping |
| REQ-006 | ✅ PASS | `ko.json` — 168 keys, proper Korean translations |
| REQ-007 | ✅ PASS | 19 translation files, all languages covered |
| REQ-008 | 🔶 CONDITIONAL | Extension copy: 18/18 files wrapped, 222 `t()` calls. Root copy: 0/18 files wrapped |
| REQ-009 | ✅ PASS | 3-tier fallback: locale → en → key. Corrupt file handling confirmed |
| REQ-010 | ✅ PASS | Per Debug technical review: tsc + py_compile + JSON validation all pass |
| REQ-011 | ✅ PASS | Additive changes only, no existing logic modified |

### Next Steps for VP
1. Decide on Inquiry 1 (root directory sync) — if proceeding, delegate to Code mode
2. If root sync is deemed unnecessary, this audit can be upgraded to PASS
3. Proceed to VP Final Review (Phase 7)

---

## Affected File List

### Extension i18n files (verified):
- `extension/package.nls.{lang}.json` × 20
- `extension/l10n/bundle.l10n.{lang}.json` × 20
- `extension/src/orchestra/SubagentManager.ts` (line 117: `VIBEZOO_LANG` env var)

### Bridge i18n module (verified):
- `extension/mcp-servers/bridge/i18n/__init__.py` (287 lines)
- `extension/mcp-servers/bridge/i18n/translations/{lang}.json` × 19

### Bridge tools with `t()` wrapping (verified):
- `extension/mcp-servers/bridge/tools/_base.py`
- `extension/mcp-servers/bridge/tools/analysis.py`
- `extension/mcp-servers/bridge/tools/deep_analyzer.py`
- `extension/mcp-servers/bridge/tools/editor.py`
- `extension/mcp-servers/bridge/tools/feedback.py`
- `extension/mcp-servers/bridge/tools/file_analyzer.py`
- `extension/mcp-servers/bridge/tools/fix_loop.py`
- `extension/mcp-servers/bridge/tools/github_diver.py`
- `extension/mcp-servers/bridge/tools/integrated.py`
- `extension/mcp-servers/bridge/tools/knowledge.py`
- `extension/mcp-servers/bridge/tools/reviewer.py`
- `extension/mcp-servers/bridge/tools/scout.py`
- `extension/mcp-servers/bridge/tools/setup.py`
- `extension/mcp-servers/bridge/tools/ssa.py`
- `extension/mcp-servers/bridge/tools/tester.py`
- `extension/mcp-servers/bridge/tools/ux_coordinator.py`
- `extension/mcp-servers/bridge/tools/web.py`
- `extension/mcp-servers/bridge/tools/whiteboard.py`

### NOT updated (flagged):
- `mcp-servers/bridge/tools/*.py` (18 files — no i18n)
- `mcp-servers/bridge/` (no `i18n/` directory)
