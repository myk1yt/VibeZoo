# i18n Architecture Plan — VibeZoo Full Internationalization

## Current State
- **Extension**: `package.nls.json` (en) + `package.nls.ko.json` (ko), `l10n/bundle.l10n.json` (en) + `bundle.l10n.ko.json` (ko)
- **Bridge**: No i18n. ~167+ hardcoded English/Korean strings across `bridge/tools/*.py`
- **Language pass-through**: Not implemented. Bridge spawn env only has `CROW_SERVER_URL`

## Target Languages (VS Code Display Languages)
en, zh-CN, zh-TW, fr, de, it, ja, ko, pt-BR, ru, es, tr, hu, cs, pl, bg, ar, he, th, vi

## Architecture

### 1. Extension Side — Language File Generation

#### 1a. `package.nls.{lang}.json` (Command/Settings labels)
- **Source of truth**: `package.nls.json` (English)
- **Existing**: `package.nls.ko.json`
- **Generate**: 18 additional `package.nls.{lang}.json` files
- **Mechanism**: VS Code auto-loads `package.nls.{lang}.json` based on `vscode.env.language`

#### 1b. `l10n/bundle.l10n.{lang}.json` (Runtime strings via `vscode.l10n.t()`)
- **Source of truth**: `bundle.l10n.json` (English)
- **Existing**: `bundle.l10n.ko.json`
- **Generate**: 18 additional `bundle.l10n.{lang}.json` files
- **Mechanism**: VS Code auto-loads `bundle.l10n.{lang}.json` at runtime

### 2. Extension → Bridge Language Pass-Through

**File**: `extension/src/orchestra/SubagentManager.ts`
**Change**: Add `VIBEZOO_LANG` to spawn env:
```typescript
env: {
  ...process.env,
  CROW_SERVER_URL: ConfigService.getCrowUrl(),
  VIBEZOO_LANG: vscode.env.language,  // ← NEW
},
```

### 3. Bridge Side — Python i18n Module

#### 3a. Module Structure
```
extension/mcp-servers/bridge/i18n/
├── __init__.py          # exports t(), get_locale(), set_locale()
└── translations/
    ├── en.json          # English (source of truth)
    ├── ko.json          # Korean
    ├── zh-CN.json       # Chinese Simplified
    ├── zh-TW.json       # Chinese Traditional
    ├── fr.json          # French
    ├── de.json          # German
    ├── it.json          # Italian
    ├── ja.json          # Japanese
    ├── pt-BR.json       # Portuguese (Brazil)
    ├── ru.json          # Russian
    ├── es.json          # Spanish
    ├── tr.json          # Turkish
    ├── hu.json          # Hungarian
    ├── cs.json          # Czech
    ├── pl.json          # Polish
    ├── bg.json          # Bulgarian
    ├── ar.json          # Arabic
    ├── he.json          # Hebrew
    ├── th.json          # Thai
    └── vi.json          # Vietnamese
```

#### 3b. i18n Module Design (`__init__.py`)
```python
import json, os
from pathlib import Path

_current_locale = "en"
_translations: dict[str, dict[str, str]] = {}
_fallback: dict[str, str] = {}

def init(locale: str = "en"):
    """Initialize i18n with given locale. Called at bridge startup."""
    global _current_locale, _fallback
    _current_locale = _normalize(locale)
    _load_translations()

def t(key: str, *args) -> str:
    """Translate key to current locale. Falls back to English."""
    template = _translations.get(_current_locale, {}).get(key) or _fallback.get(key) or key
    if args:
        try:
            template = template.format(*args)
        except (IndexError, KeyError):
            pass
    return template

def _normalize(locale: str) -> str:
    """Map VS Code locale to our file names."""
    mapping = {
        "zh-cn": "zh-CN", "zh-tw": "zh-TW", "pt-br": "pt-BR",
        "en": "en", "ko": "ko", "fr": "fr", "de": "de",
        "it": "it", "ja": "ja", "ru": "ru", "es": "es",
        "tr": "tr", "hu": "hu", "cs": "cs", "pl": "pl",
        "bg": "bg", "ar": "ar", "he": "he", "th": "th", "vi": "vi",
    }
    return mapping.get(locale.lower().replace("_", "-"), "en")
```

#### 3c. Integration Point
**File**: `extension/mcp-servers/vibezoo_mcp_bridge.py`
**Change**: At startup, read `VIBEZOO_LANG` env var and init i18n:
```python
from bridge.i18n import init
init(os.environ.get("VIBEZOO_LANG", "en"))
```

#### 3d. String Wrapping Pattern
**Before:**
```python
output = _markdown_header("Code Review Error", "❌") + f"**File not found: {file_path}**\n" + _markdown_footer()
```
**After:**
```python
from bridge.i18n import t
output = _markdown_header(t("Code Review Error"), "❌") + f"**{t('File not found: {0}', file_path)}**\n" + _markdown_footer()
```

### 4. String Extraction Strategy

1. Extract all unique English strings from `bridge/tools/*.py` into `en.json`
2. Generate `ko.json` with full Korean translations
3. Generate other `{lang}.json` files with translations (AI-assisted)
4. Keys use the English string itself as key (simpler extraction, no key naming convention needed)

### 5. Files Modified

| File | Change |
|------|--------|
| `extension/src/orchestra/SubagentManager.ts` | Add `VIBEZOO_LANG` env var |
| `extension/package.nls.{lang}.json` × 18 | New translation files |
| `extension/l10n/bundle.l10n.{lang}.json` × 18 | New translation files |
| `extension/mcp-servers/bridge/i18n/__init__.py` | New i18n module |
| `extension/mcp-servers/bridge/i18n/translations/*.json` × 20 | Translation files |
| `extension/mcp-servers/vibezoo_mcp_bridge.py` | Init i18n at startup |
| `extension/mcp-servers/bridge/tools/*.py` × 15+ | Wrap strings with `t()` |
