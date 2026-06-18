import json
import os


class I18nContext:
    """Translation context for a specific locale."""

    def __init__(self, translations: dict, locale: str = "en"):
        self._translations = translations
        self.locale = locale

    def get(self, key: str, **kwargs) -> str:
        """Return translated string for key, substituting kwargs placeholders.

        Falls back to the key name itself if translation is missing.
        """
        text = self._translations.get(key)
        if text is None:
            return key
        if kwargs:
            try:
                text = text.format(**kwargs)
            except (KeyError, IndexError):
                pass
        return text

    def __call__(self, key: str, **kwargs) -> str:
        return self.get(key, **kwargs)


class I18nCore:
    """Loads and manages JSON locale files from a directory."""

    def __init__(self, locales_dir: str, default_locale: str = "en"):
        self.locales_dir = locales_dir
        self.default_locale = default_locale
        self._translations: dict[str, dict] = {}
        self.available_locales: list[str] = []

    def load(self) -> None:
        """Scan locales_dir for *.json files and register each as a locale."""
        if not os.path.isdir(self.locales_dir):
            return

        for fname in sorted(os.listdir(self.locales_dir)):
            if fname.endswith(".json"):
                locale = fname[:-5]
                path = os.path.join(self.locales_dir, fname)
                with open(path, encoding="utf-8") as f:
                    self._translations[locale] = json.load(f)
                self.available_locales.append(locale)

    def get_context(self, locale: str) -> I18nContext:
        """Return I18nContext for locale, falling back to the default locale."""
        translations = (
            self._translations.get(locale)
            or self._translations.get(self.default_locale)
            or {}
        )
        return I18nContext(translations=translations, locale=locale)
