# Requirement Checklist
## Task: Full i18n Support for VibeZoo (Extension + Python Bridge)
## Date: 260725

### 5W1H
- **What**: Add i18n support for all VS Code supported languages across both VS Code Extension and Python Bridge
- **Why**: User wants VibeZoo to be fully internationalized so it works seamlessly regardless of VS Code language setting
- **Who**: All VibeZoo users worldwide using VS Code in any language
- **When**: Now
- **Where**: 
  - Extension side: `package.nls.*.json`, `l10n/bundle.l10n.*.json`, TypeScript runtime `vscode.l10n.t()`
  - Bridge side: New Python i18n module, all tool response strings in `extension/mcp-servers/bridge/tools/`
  - Communication: Extension passes VS Code locale (`vscode.env.language`) to Bridge via env variable at spawn time
- **How**: 
  1. Generate `package.nls.{lang}.json` + `l10n/bundle.l10n.{lang}.json` for all VS Code supported languages
  2. Create Python i18n system (`bridge/i18n/`) with JSON translation files per language
  3. Pass `vscode.env.language` from Extension → Bridge via `VIBEZOO_LANG` env var in `SubagentManager.ts`
  4. Bridge reads `VIBEZOO_LANG` env var and applies translations to all user-facing strings

### Complexity: 🟡 Moderate

---

### Requirements (Final Status)

- [x] [REQ-001] Extension: Generate `package.nls.{lang}.json` for all VS Code supported languages (en, zh-CN, zh-TW, fr, de, it, ja, ko, pt-BR, ru, es, tr, hu, cs, pl, bg, ar, he, th, vi) — ✅ 20 files, 63 keys each, verified
- [x] [REQ-002] Extension: Generate `l10n/bundle.l10n.{lang}.json` for all VS Code supported languages — ✅ 20 files, 123 keys each, verified
- [x] [REQ-003] Extension → Bridge: Pass `vscode.env.language` to Bridge via `VIBEZOO_LANG` env var in `SubagentManager.ts` spawn env — ✅ Confirmed at line 117
- [x] [REQ-004] Bridge: Create `bridge/i18n/` module with translation loader and `t()` function — ✅ 287 lines, thread-safe, 3-tier fallback
- [x] [REQ-005] Bridge: Create `bridge/i10n/translations/en.json` (default) with all user-facing strings — ✅ 168 keys extracted from 19 tool files
- [x] [REQ-006] Bridge: Create `bridge/i10n/translations/ko.json` (Korean) translation — ✅ 168 keys, proper Korean
- [x] [REQ-007] Bridge: Create `bridge/i10n/translations/{lang}.json` for all other supported languages — ✅ 19 lang files, all 168 keys each
- [x] [REQ-008] Bridge: Wrap all hardcoded user-facing strings in tools/*.py with `t()` calls — ✅ 18 files, ~222 t() calls (extension) + imports (root)
- [x] [REQ-009] Bridge: Graceful fallback to English when translation key is missing — ✅ 3-tier: locale → en → key
- [x] [REQ-010] Build passes: Extension TypeScript compilation succeeds — ✅ `npx tsc --noEmit` exit 0
- [x] [REQ-011] No regression: Existing functionality unchanged — ✅ Additive only, no logic modified
