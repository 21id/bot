from pathlib import Path

from app.bot.i18n.core import I18nContext, I18nCore
from app.domain.campus.campus import Campus

import pytest

TESTS_DIR = Path(__file__).parent
LOCALES_DIR = TESTS_DIR.parent / "bot" / "locales"


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Mark tests as unit / integration by their folder."""
    for item in items:
        parts = Path(str(item.fspath)).relative_to(TESTS_DIR).parts
        if parts and parts[0] in ("unit", "integration"):
            item.add_marker(getattr(pytest.mark, parts[0]))


@pytest.fixture(scope="session")
def i18n_core() -> I18nCore:
    """I18n core with real bot locales."""
    core = I18nCore(locales_dir=str(LOCALES_DIR))
    core.load()
    return core


@pytest.fixture
def i18n(i18n_core: I18nCore) -> I18nContext:
    """English translation context."""
    return i18n_core.get_context("en")


@pytest.fixture
def campus() -> Campus:
    """Sample campus."""
    return Campus(uuid="c-uuid", short_name="TAS")
