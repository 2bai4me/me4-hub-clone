"""
ME4 Hub i18n Helper — python-i18n wrapper with JSON support.

Loads translations from locales/ directory at import time.
Provides _() as the gettext-style shorthand for i18n.t().

Locale selection:
- For HTTP dashboard: Accept-Language header → first supported locale
- For MCP stdio / programmatic: i18n_helper.set_locale('de')
- Default: 'de' (per ADR-002/003)
"""

import os
import logging
from pathlib import Path
from typing import Optional

import i18n
import i18n.loaders.json_loader

logger = logging.getLogger("me4-hub.i18n")

# ═══════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════

LOCALES_DIR = Path(__file__).parent / "locales"
SUPPORTED_LOCALES = ["de", "en"]
DEFAULT_LOCALE = "de"

# ═══════════════════════════════════════════════
# Initialize python-i18n with JSON loader
# ═══════════════════════════════════════════════

def _init_i18n():
    """Register JSON loader, set load path, and preload all translations."""
    # Register JSON loader
    i18n.register_loader(i18n.loaders.json_loader.JsonLoader, ["json"])

    # Configure
    i18n.set("file_format", "json")
    i18n.set("load_path", [str(LOCALES_DIR)])
    i18n.set("locale", DEFAULT_LOCALE)
    i18n.set("fallback", DEFAULT_LOCALE)
    i18n.set("available_locales", SUPPORTED_LOCALES)
    i18n.set("enable_memoization", True)

    # Preload all translation files manually (auto-load doesn't fire otherwise)
    _preload_translations()

    logger.debug(f"i18n initialized: locales={SUPPORTED_LOCALES}, default={DEFAULT_LOCALE}")


def _preload_translations():
    """Load all JSON locale files into the translation container."""
    loader = i18n.loaders.json_loader.JsonLoader()

    for locale in SUPPORTED_LOCALES:
        filepath = LOCALES_DIR / f"{locale}.json"
        if filepath.exists():
            try:
                data = loader.load_resource(str(filepath), root_data=None)
                i18n.resource_loader.load_translation_dic(data, "", locale)
                logger.debug(f"Loaded {len(data)} top-level keys from {filepath}")
            except Exception as e:
                logger.warning(f"Failed to load translations from {filepath}: {e}")
        else:
            logger.warning(f"Locale file not found: {filepath}")


# ═══════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════

def _(key: str, **kwargs) -> str:
    """Translation shorthand. Calls i18n.t() with formatting support.

    Usage:
        _("errors.not_found")
        _("server.dashboard_started", port=8088)
    """
    translated = i18n.t(key)
    if kwargs:
        try:
            return translated.format(**kwargs)
        except (KeyError, ValueError):
            # If formatting fails, return raw translation with a note
            return translated
    return translated


def set_locale(locale: str) -> None:
    """Set the active locale. Falls back to DEFAULT_LOCALE if unsupported."""
    if locale in SUPPORTED_LOCALES:
        i18n.set("locale", locale)
    else:
        i18n.set("locale", DEFAULT_LOCALE)
    logger.debug(f"Locale set to: {i18n.config.get('locale')}")


def get_locale() -> str:
    """Get the currently active locale."""
    return i18n.config.get("locale") or DEFAULT_LOCALE


def parse_accept_language(header: Optional[str]) -> str:
    """Parse Accept-Language header and return best matching locale.

    Args:
        header: Raw Accept-Language header value (e.g. "de-DE,de;q=0.9,en;q=0.8")

    Returns:
        Best matching supported locale, or DEFAULT_LOCALE.
    """
    if not header:
        return DEFAULT_LOCALE

    try:
        # Parse quality-weighted locales
        locales = []
        for part in header.split(","):
            part = part.strip()
            if ";" in part:
                lang, quality = part.split(";", 1)
                try:
                    q = float(quality.strip().replace("q=", ""))
                except ValueError:
                    q = 1.0
            else:
                lang = part
                q = 1.0

            # Extract primary language tag
            lang = lang.strip().split("-")[0].lower()
            locales.append((q, lang))

        # Sort by quality (descending)
        locales.sort(key=lambda x: x[0], reverse=True)

        # Return first supported
        for _, lang in locales:
            if lang in SUPPORTED_LOCALES:
                return lang

    except Exception:
        pass

    return DEFAULT_LOCALE


# ═══════════════════════════════════════════════
# Initialize on import
# ═══════════════════════════════════════════════

_init_i18n()
