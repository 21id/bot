from datetime import datetime, timedelta, UTC
from unittest.mock import AsyncMock, MagicMock

from app.bot.routers.user.mass_invite.handlers.create import (
    collect,
    finish,
    mass_invite,
)
from app.bot.routers.user.mass_invite.handlers.redeem import (
    redeem_link,
    redeem_nickname,
)
from app.bot.routers.user.mass_invite.callback import MassInviteFinish
from app.bot.routers.user.mass_invite.router import router as mi_router
from app.bot.routers.user.mass_invite.states import MassInviteStates
from app.bot.routers.user.registration.handlers.join_invite import join_invite
from app.bot.routers.user.registration.router import router as reg_router
from app.domain.user.user import User
from app.tests.integration.test_registration_flow import STUDENT, _message

import pytest
from aiogram.filters import CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import Chat, Message
from aiogram.types import User as TgUser

TG_ID = 2002
OWNER_ID = 999


def _state(redis, tg_id: int) -> FSMContext:
    return FSMContext(
        storage=RedisStorage(redis=redis),
        key=StorageKey(bot_id=42, chat_id=tg_id, user_id=tg_id),
    )


def _tg_message(text: str, tg_id: int) -> Message:
    return Message(
        message_id=1,
        date=datetime.now(UTC),
        chat=Chat(id=tg_id, type="private"),
        from_user=TgUser(id=tg_id, is_bot=False, first_name="x"),
        text=text,
    )


@pytest.fixture
def bot():
    b = AsyncMock()
    b.me.return_value = MagicMock(username="ident21bot")
    return b


async def _create_link(container, redis, bot, i18n, nicknames: str) -> str:
    state = _state(redis, OWNER_ID)
    await mass_invite(
        message=_message("/mass_invite", OWNER_ID), state=state, i18n=i18n
    )
    assert await state.get_state() == MassInviteStates.collecting.state

    await collect(message=_message(nicknames, OWNER_ID), state=state, i18n=i18n)

    callback = MagicMock(from_user=MagicMock(id=OWNER_ID))
    callback.message.edit_text = AsyncMock()
    callback.answer = AsyncMock()
    await finish(
        callback=callback,
        callback_data=MassInviteFinish(done=True),
        state=state,
        container=container,
        bot=bot,
        i18n=i18n,
    )
    assert await state.get_state() is None
    text = callback.message.edit_text.await_args.args[0]
    return text.split("?start=")[1].strip()


async def _redeem(container, redis, bot, i18n, payload: str, nickname: str):
    state = _state(redis, TG_ID)
    start = _message(f"/start {payload}", TG_ID)
    await redeem_link(
        message=start,
        command=CommandObject(args=payload),
        state=state,
        container=container,
        i18n=i18n,
    )
    msg = _message(nickname, TG_ID)
    await redeem_nickname(
        message=msg, state=state, container=container, bot=bot, i18n=i18n
    )
    return start, msg, state


async def test_owner_creates_student_redeems(container, redis, bot, i18n, user_service):
    container.s21api_client.get_student_by_nickname.return_value = STUDENT
    payload = await _create_link(container, redis, bot, i18n, "JDoe, other, b@d")
    assert payload.startswith("mi_")

    _, msg, state = await _redeem(container, redis, bot, i18n, payload, " JDOE ")

    user = await user_service.get_by_telegram_id(TG_ID)
    assert user.nickname == "jdoe" and user.is_verified
    assert [v.method for v in user.verifications] == ["mass_invite"]
    assert user.verifications[0].details == {"link": payload[3:]}
    assert msg.reply.await_args.args[0] == i18n.get(
        "mass-invite-success", nickname="jdoe"
    )
    assert await state.get_state() is None
    assert "mass-invite" in bot.send_message.await_args.args[1]
    link = await container.mass_invite_service.get(payload[3:])
    assert link.used_by == {"jdoe": TG_ID}


async def test_nickname_not_in_list(container, redis, bot, i18n, user_service):
    container.s21api_client.get_student_by_nickname.return_value = STUDENT
    payload = await _create_link(container, redis, bot, i18n, "other")

    _, msg, state = await _redeem(container, redis, bot, i18n, payload, "jdoe")

    assert msg.reply.await_args.args[0] == i18n.get(
        "mass-invite-failed", nickname="jdoe"
    )
    assert await user_service.get_by_telegram_id(TG_ID) is None
    assert await state.get_state() == MassInviteStates.nickname.state


async def test_nickname_already_used(container, redis, bot, i18n, user_service):
    container.s21api_client.get_student_by_nickname.return_value = STUDENT
    payload = await _create_link(container, redis, bot, i18n, "jdoe")
    assert await container.mass_invite_service.mark_used(payload[3:], "jdoe", 1)

    _, msg, _ = await _redeem(container, redis, bot, i18n, payload, "jdoe")

    assert msg.reply.await_args.args[0] == i18n.get(
        "mass-invite-failed", nickname="jdoe"
    )
    assert await user_service.get_by_telegram_id(TG_ID) is None


async def test_telegram_already_registered(
    container, redis, bot, i18n, user_service, campus
):
    await user_service.upsert(
        User(nickname="member", campus=campus, is_verified=True, telegram_id=TG_ID)
    )
    payload = await _create_link(container, redis, bot, i18n, "jdoe")

    start, _, state = await _redeem(container, redis, bot, i18n, payload, "jdoe")

    assert start.reply.await_args.args[0] == i18n.get("join-invite-already-registered")
    assert await state.get_state() is None
    assert (await user_service.get_by_nickname("jdoe")) is None


async def test_expired_link(container, redis, bot, i18n, migrated_mongo):
    payload = await _create_link(container, redis, bot, i18n, "jdoe")
    await migrated_mongo.mass_invite().update_one(
        {"_id": payload[3:]},
        {"$set": {"expires_at": datetime.now(UTC) - timedelta(minutes=1)}},
    )

    start, _, state = await _redeem(container, redis, bot, i18n, payload, "jdoe")

    assert start.reply.await_args.args[0] == i18n.get("mass-invite-not-found")
    assert await state.get_state() is None


async def test_attempts_rate_limited(container, redis, bot, i18n):
    payload = await _create_link(container, redis, bot, i18n, "jdoe")
    for _ in range(6):
        _, msg, _ = await _redeem(container, redis, bot, i18n, payload, "nope")
    assert msg.reply.await_args.args[0].startswith(
        i18n.get("rate-limited").split("{")[0]
    )


def _handler(router, callback):
    return next(h for h in router.message.handlers if h.callback is callback)


async def test_non_owner_mass_invite_ignored(container, bot):
    handler = _handler(mi_router, mass_invite)
    passed, _ = await handler.check(
        _tg_message("/mass_invite", TG_ID), container=container, bot=bot
    )
    assert not passed
    passed, _ = await handler.check(
        _tg_message("/mass_invite", OWNER_ID), container=container, bot=bot
    )
    assert passed


async def test_mi_deeplink_skips_join_invite(container, bot):
    message = _tg_message("/start mi_abc", TG_ID)
    assert (await _handler(mi_router, redeem_link).check(message, bot=bot))[0]
    assert not (await _handler(reg_router, join_invite).check(message, bot=bot))[0]
    other = _tg_message("/start invite-otp", TG_ID)
    assert (await _handler(reg_router, join_invite).check(other, bot=bot))[0]
