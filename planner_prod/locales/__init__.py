"""
Internationalisation helpers.

Usage:
    from locales import t

    text = t("welcome_new", lang="ru")
    text = t("task_saved", lang="en")
    text = t("city_found", lang="ru", city="Москва", timezone="Europe/Moscow")
"""

from locales.ru import STRINGS as RU
from locales.en import STRINGS as EN

_LOCALES: dict[str, dict[str, str]] = {"ru": RU, "en": EN}

SUPPORTED_LANGUAGES = {"ru": "🇷🇺 Русский", "en": "🇬🇧 English"}


def t(key: str, lang: str = "ru", **kwargs) -> str:
    """Translate a key to the given language, with optional format arguments."""
    strings = _LOCALES.get(lang, RU)
    text = strings.get(key) or RU.get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    return text
