"""
VibeZoo Bridge — i18n (Internationalization) Module

Provides a lightweight translation system for the Bridge tools.
The English string itself is used as the key (no separate key naming convention).

Usage:
    from bridge.i18n import init, t

    # Initialize at bridge startup (reads VIBEZOO_LANG env var if not called)
    init("en")

    # Translate
    msg = t("File not found")
    msg = t("File not found: {0}", file_path)

Translation files are JSON in bridge/i18n/translations/{lang}.json
Missing keys fall back to English, then to the key itself.
"""

import json
import os
import threading
from pathlib import Path
from typing import Optional

# ── Module-level state ───────────────────────────────

_translations_dir: Path = Path(__file__).parent / "translations"

# Current locale (e.g., "en", "ko", "zh-CN")
_current_locale: str = "en"

# Loaded translation tables: {locale: {key: value}}
_translations: dict[str, dict[str, str]] = {}

# Lock for thread-safe access
_lock = threading.RLock()

# Track which locales have been loaded to avoid redundant file reads
_loaded_locales: set[str] = set()


# ── Locale normalization ─────────────────────────────

# VS Code locale → our file name mapping
_LOCALE_NORMALIZATION: dict[str, str] = {
    # Chinese
    "zh-cn": "zh-CN",
    "zh-tw": "zh-TW",
    "zh-hans": "zh-CN",
    "zh-hant": "zh-TW",
    "zh": "zh-CN",
    # Portuguese
    "pt-br": "pt-BR",
    "pt-pt": "pt-PT",
    "pt": "pt-BR",
    # Korean
    "ko-kr": "ko",
    "ko-kore": "ko",
    # Japanese
    "ja-jp": "ja",
    # French
    "fr-fr": "fr",
    # German
    "de-de": "de",
    # Spanish
    "es-es": "es",
    # Russian
    "ru-ru": "ru",
    # Italian
    "it-it": "it",
    # English variants
    "en-us": "en",
    "en-gb": "en",
    "en-au": "en",
    "en-ca": "en",
}


def _normalize(locale: str) -> str:
    """Map VS Code locale to our translation file names.

    Examples:
        "zh-cn" → "zh-CN"
        "pt-br" → "pt-BR"
        "en-us" → "en"
        "ko-kr" → "ko"

    For locales not in the explicit mapping, we try:
        1. Lowercase the whole string and look up
        2. Capitalize the region part (e.g., "es-ar" → "es-AR")
        3. Fall back to the base language (e.g., "fr-ca" → "fr")
    """
    if not locale:
        return "en"

    locale = locale.strip()

    # Exact match in normalization table
    if locale in _LOCALE_NORMALIZATION:
        return _LOCALE_NORMALIZATION[locale]

    # Lowercase lookup
    lower = locale.lower()
    if lower in _LOCALE_NORMALIZATION:
        return _LOCALE_NORMALIZATION[lower]

    # Try capitalizing the region part: "es-ar" → "es-AR"
    if "-" in lower:
        parts = lower.split("-")
        if len(parts) == 2:
            base, region = parts[0], parts[1].upper()
            candidate = f"{base}-{region}"
            # Check if a translation file exists for this
            if (_translations_dir / f"{candidate}.json").exists():
                return candidate
            # Fall back to base language
            if (_translations_dir / f"{base}.json").exists():
                return base
            return candidate

    # Single language code
    if (_translations_dir / f"{lower}.json").exists():
        return lower

    return locale


# ── Translation file loading ─────────────────────────

def _load_translations() -> None:
    """Load translation JSON files for the current locale and English fallback.

    Called internally; uses _lock for thread safety.
    """
    global _translations, _loaded_locales

    locales_to_load = set()

    # Always load English as fallback
    locales_to_load.add("en")

    # Load current locale if different from English
    if _current_locale and _current_locale != "en":
        locales_to_load.add(_current_locale)

    for locale in locales_to_load:
        if locale in _loaded_locales:
            continue

        file_path = _translations_dir / f"{locale}.json"

        if file_path.exists():
            try:
                content = file_path.read_text(encoding="utf-8")
                data = json.loads(content)
                if isinstance(data, dict):
                    _translations[locale] = data
            except (json.JSONDecodeError, OSError, UnicodeDecodeError):
                # Gracefully handle corrupt/missing translation files
                _translations[locale] = {}
        else:
            _translations[locale] = {}

        _loaded_locales.add(locale)


# ── Public API ───────────────────────────────────────

def init(locale: str = "en") -> None:
    """Initialize i18n with the given locale.

    Called at bridge startup. If not called, the module reads
    the VIBEZOO_LANG environment variable, defaulting to "en".

    Args:
        locale: VS Code locale string (e.g., "en", "ko", "zh-cn", "pt-br")
    """
    global _current_locale

    normalized = _normalize(locale)

    with _lock:
        if _current_locale != normalized:
            _current_locale = normalized
            # Load translations for the new locale
            _load_translations()


def t(key: str, *args) -> str:
    """Translate a key to the current locale.

    Falls back to English if the key is missing in the current locale,
    then to the key itself if also missing in English.

    Supports {0}, {1}, ... positional format args.

    Args:
        key: The English string to translate (used as the lookup key)
        *args: Positional arguments to format into the translated string

    Returns:
        The translated (and formatted) string

    Examples:
        t("File not found")
        t("File not found: {0}", file_path)
        t("Found {0} results in {1} files", count, file_count)
    """
    if not key:
        return ""

    with _lock:
        # Ensure translations are loaded
        if not _loaded_locales:
            _load_translations()

        # 1. Try current locale
        result = None
        if _current_locale and _current_locale in _translations:
            result = _translations[_current_locale].get(key)

        # 2. Fall back to English
        if result is None:
            en_table = _translations.get("en", {})
            result = en_table.get(key)

        # 3. Fall back to the key itself
        if result is None:
            result = key

        # Format with positional args if provided
        if args:
            try:
                result = result.format(*args)
            except (IndexError, KeyError, ValueError):
                # If formatting fails, return the unformatted result
                pass

        return result


def get_locale() -> str:
    """Return the current locale string.

    Returns:
        The normalized current locale (e.g., "en", "ko", "zh-CN")
    """
    return _current_locale


def get_available_locales() -> list[str]:
    """Return a list of available locale codes based on translation files.

    Returns:
        List of locale codes (without .json extension), sorted alphabetically.
        Always includes "en" if en.json exists.
    """
    if not _translations_dir.exists():
        return ["en"]

    locales = []
    for f in _translations_dir.glob("*.json"):
        locales.append(f.stem)

    return sorted(locales)


# ── Auto-initialization from environment ─────────────

def _auto_init() -> None:
    """Auto-initialize from VIBEZOO_LANG environment variable.

    Called at module import time. If VIBEZOO_LANG is set, initializes
    with that locale. Otherwise defaults to "en".
    """
    env_locale = os.environ.get("VIBEZOO_LANG", "")
    if env_locale:
        init(env_locale)
    else:
        init("en")


# Auto-initialize on module import
_auto_init()
