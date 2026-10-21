from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock

from app.bot.filters.user_exists import UserExists
from app.bot.filters.user_verified import UserVerified
from app.bot.routers.user.registration.handlers import nickname as nickname_module
from app.bot.routers.user.registration.router import router as registration_router
from app.bot.routers.user.registration.states import RegistrationStates
from app.domain.user.user import User

import pytest
from aiogram.types import Chat, Message


def _handler(callback):
    """Find registered message handler object by its callback."""
    return next(
        h for h in registration_router.message.handlers if h.callback is callback
    )


def _message(text: str) -> Message:
    return Message(
        message_id=1, date=datetime.now(UTC), chat=Chat(id=1, type="private"), text=text
    )


async def _passes(callback, text: str) -> bool:
    passed, _ = await _handler(callback).check(
        _message(text), raw_state=RegistrationStates.nickname.state
    )
    return passed


@pytest.mark.parametrize("text", ["a", "jdoe", "JDoe", "abcdefgh"])
async def test_nickname_regex_accepts(text):
    assert await _passes(nickname_module.nickname, text)
    assert not await _passes(nickname_module.invalid_nickname, text)


@pytest.mark.parametrize(
    "text", ["абвгд", "abcdefghi", "jdoe1", "12345", "", "j doe", "j.doe", "jdoe@x"]
)
async def test_nickname_regex_rejects(text):
    assert not await _passes(nickname_module.nickname, text)
    assert await _passes(nickname_module.invalid_nickname, text)


async def test_nickname_handler_needs_nickname_state():
    passed, _ = await _handler(nickname_module.nickname).check(
        _message("jdoe"), raw_state=None
    )
    assert not passed


def _user(campus, verified: bool) -> User:
    return User(
        nickname="jdoe",
        campus=campus,
        is_verified=verified,
        telegram_id=1 if verified else None,
    )


def _container(user):
    container = MagicMock()
    container.user_service.get_by_telegram_id = AsyncMock(return_value=user)
    return container


@pytest.mark.parametrize("exists", [True, False])
async def test_user_exists_uses_preloaded_user(campus, exists):
    container = _container(None)
    event = MagicMock()
    result = await UserExists(exists=exists)(
        event, container, db_user=_user(campus, True)
    )
    assert result is exists
    container.user_service.get_by_telegram_id.assert_not_awaited()


async def test_user_exists_loads_user_when_not_preloaded():
    container = _container(None)
    event = MagicMock()
    event.from_user.id = 5
    assert await UserExists(exists=False)(event, container) is True
    container.user_service.get_by_telegram_id.assert_awaited_once_with(telegram_id=5)


@pytest.mark.parametrize("verified", [True, False])
async def test_user_verified(campus, verified):
    container = _container(_user(campus, verified))
    assert await UserVerified(verified=True)(MagicMock(), container) is verified
    assert await UserVerified(verified=False)(MagicMock(), container) is not verified


async def test_user_verified_missing_user_is_not_verified():
    assert await UserVerified(verified=False)(MagicMock(), _container(None))
