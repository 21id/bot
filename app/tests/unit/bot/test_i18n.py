import json
import string
from unittest.mock import AsyncMock, MagicMock

from app.bot.i18n.core import I18nCore
from app.bot.i18n.middleware import I18nMiddleware
from app.tests.conftest import LOCALES_DIR

import pytest


@pytest.fixture
def core(tmp_path):
    (tmp_path / "en.json").write_text(
        json.dumps({"hello": "Hello, {name}!", "only-en": "EN"})
    )
    (tmp_path / "ru.json").write_text(json.dumps({"hello": "Привет, {name}!"}))
    c = I18nCore(locales_dir=str(tmp_path))
    c.load()
    return c


def test_loads_locales(core):
    assert core.available_locales == ["en", "ru"]


def test_translation_with_placeholder(core):
    assert core.get_context("ru").get("hello", name="Bob") == "Привет, Bob!"
    assert core.get_context("en")("hello", name="Bob") == "Hello, Bob!"


def test_unknown_locale_falls_back_to_default(core):
    ctx = core.get_context("xx")
    assert ctx.get("hello", name="A") == "Hello, A!"


def test_missing_key_returns_key(core):
    # Missing keys aren't merged from default locale, key name is returned
    assert core.get_context("ru").get("only-en") == "only-en"
    assert core.get_context("en").get("nope") == "nope"


def test_missing_placeholder_kwarg_returns_raw_text(core):
    assert core.get_context("en").get("hello", other=1) == "Hello, {name}!"


def test_missing_dir_loads_nothing(tmp_path):
    c = I18nCore(locales_dir=str(tmp_path / "missing"))
    c.load()
    assert c.available_locales == []
    assert c.get_context("en").get("k") == "k"


def _placeholders(text: str) -> set[str]:
    return {f for _, f, _, _ in string.Formatter().parse(text) if f is not None}


def _locales() -> dict[str, dict]:
    return {
        p.stem: json.loads(p.read_text(encoding="utf-8"))
        for p in sorted(LOCALES_DIR.glob("*.json"))
    }


def test_all_locales_present():
    assert set(_locales()) == {"en", "ru", "uz", "uz_new", "tg"}


@pytest.mark.parametrize("locale", ["ru", "uz", "uz_new", "tg"])
def test_locale_has_same_keys_as_en(locale):
    locales = _locales()
    en, other = locales["en"], locales[locale]
    assert set(other) - set(en) == set(), "extra keys"
    assert set(en) - set(other) == set(), "missing keys"


@pytest.mark.parametrize("locale", ["en", "ru", "uz", "uz_new", "tg"])
def test_locale_placeholders_match_en(locale):
    locales = _locales()
    en = locales["en"]
    mismatched = {
        key: (_placeholders(en[key]), _placeholders(text))
        for key, text in locales[locale].items()
        if key in en and _placeholders(en[key]) != _placeholders(text)
    }
    assert mismatched == {}


async def test_middleware_prefers_fsm_language(i18n_core):
    state = MagicMock()
    state.get_value = AsyncMock(return_value="ru")
    db_user = MagicMock(language="uz")
    container = MagicMock()
    container.user_service.get_by_telegram_id = AsyncMock(return_value=db_user)
    data = {"state": state, "container": container, "event_from_user": MagicMock(id=1)}
    handler = AsyncMock()

    await I18nMiddleware(i18n_core)(handler, MagicMock(), data)
    assert data["i18n"].locale == "ru"
    assert data["db_user"] is db_user


async def test_middleware_uses_db_language_then_default(i18n_core):
    container = MagicMock()
    container.user_service.get_by_telegram_id = AsyncMock(
        return_value=MagicMock(language="uz")
    )
    data = {"container": container, "event_from_user": MagicMock(id=1)}
    await I18nMiddleware(i18n_core)(AsyncMock(), MagicMock(), data)
    assert data["i18n"].locale == "uz"

    data = {}
    await I18nMiddleware(i18n_core)(AsyncMock(), MagicMock(), data)
    assert data["i18n"].locale == "en" and data["db_user"] is None
