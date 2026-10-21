from unittest.mock import AsyncMock, MagicMock

from app.bot.middlewares.error_handler import ErrorMiddleware
from app.domain.base_error import BaseError

import pytest
from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import AnswerCallbackQuery
from aiogram.types import Chat, User as TgUser

ADMIN_ID = 999
USER = TgUser(id=5, is_bot=False, first_name="U")
CHAT = Chat(id=-100, type="supergroup")


@pytest.fixture
def bot():
    return AsyncMock()


def _data(bot, i18n=None, user=USER, chat=CHAT) -> dict:
    data = {"bot": bot, "event_from_user": user, "event_chat": chat}
    if i18n:
        data["i18n"] = i18n
    return data


def _raiser(exc: Exception):
    async def handler(event, data):
        raise exc

    return handler


def _user_texts(bot) -> list[tuple[int, str]]:
    return [
        (c.args[0], c.args[1])
        for c in bot.send_message.await_args_list
        if c.args[0] != ADMIN_ID
    ]


async def test_passes_through_result(bot):
    async def handler(event, data):
        return "ok"

    assert await ErrorMiddleware(ADMIN_ID)(handler, MagicMock(), _data(bot)) == "ok"
    bot.send_message.assert_not_awaited()


async def test_generic_error_hides_details(bot, i18n):
    await ErrorMiddleware(ADMIN_ID)(
        _raiser(ValueError("secret db password")), MagicMock(), _data(bot, i18n)
    )
    admin = [c for c in bot.send_message.await_args_list if c.args[0] == ADMIN_ID]
    assert admin and "secret db password" in admin[0].args[1]

    [(target, text)] = _user_texts(bot)
    assert target == USER.id
    assert "secret" not in text
    assert text.startswith(i18n.get("error-generic", uuid="X").split("X")[0])


async def test_generic_error_without_i18n(bot):
    await ErrorMiddleware(ADMIN_ID)(
        _raiser(ValueError("secret")), MagicMock(), _data(bot)
    )
    [(_, text)] = _user_texts(bot)
    assert "secret" not in text and "ERROR UUID" in text


async def test_base_error_shows_client_message(bot, i18n):
    err = BaseError(client_message="Nice message", support_details="internal")
    await ErrorMiddleware(ADMIN_ID)(_raiser(err), MagicMock(), _data(bot, i18n))
    [(_, text)] = _user_texts(bot)
    assert "Nice message" in text and "internal" not in text


async def test_base_error_without_notify_only_reports_admin(bot):
    err = BaseError(client_message="x", notify_user=False)
    await ErrorMiddleware(ADMIN_ID)(_raiser(err), MagicMock(), _data(bot))
    assert _user_texts(bot) == []
    assert bot.send_message.await_count == 1


async def test_expired_callback_ignored(bot):
    err = TelegramBadRequest(
        method=AnswerCallbackQuery(callback_query_id="1"),
        message="Bad Request: query is too old and response timeout expired",
    )
    assert (
        await ErrorMiddleware(ADMIN_ID)(_raiser(err), MagicMock(), _data(bot)) is None
    )
    bot.send_message.assert_not_awaited()


async def test_other_bad_request_reported(bot):
    err = TelegramBadRequest(
        method=AnswerCallbackQuery(callback_query_id="1"),
        message="Bad Request: chat not found",
    )
    await ErrorMiddleware(ADMIN_ID)(_raiser(err), MagicMock(), _data(bot))
    assert len(_user_texts(bot)) == 1


async def test_falls_back_to_chat_id_when_user_unreachable(bot):
    async def send(chat_id, text, **kwargs):
        if chat_id == USER.id:
            raise RuntimeError("blocked by user")

    bot.send_message.side_effect = send

    await ErrorMiddleware(ADMIN_ID)(_raiser(ValueError()), MagicMock(), _data(bot))
    targets = [t for t, _ in _user_texts(bot)]
    assert targets == [USER.id, CHAT.id]


async def test_chat_only_event(bot):
    await ErrorMiddleware(ADMIN_ID)(
        _raiser(ValueError()), MagicMock(), _data(bot, user=None)
    )
    assert [t for t, _ in _user_texts(bot)] == [CHAT.id]


async def test_admin_report_failure_doesnt_block_user_message(bot):
    async def send(chat_id, text, **kwargs):
        if chat_id == ADMIN_ID:
            raise RuntimeError("admin blocked bot")

    bot.send_message.side_effect = send
    await ErrorMiddleware(ADMIN_ID)(_raiser(ValueError()), MagicMock(), _data(bot))
    assert [t for t, _ in _user_texts(bot)] == [USER.id]
