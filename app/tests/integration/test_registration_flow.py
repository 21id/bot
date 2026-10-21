from unittest.mock import AsyncMock, MagicMock

from app.bot.routers.chat.admins.handlers.manual_mention import manual_mention
from app.bot.routers.user.registration.handlers.nickname import nickname
from app.bot.routers.user.registration.handlers.verification import code_verification
from app.bot.routers.user.registration.states import RegistrationStates
from app.bot.routers.user.search.handlers.search_command import search
from app.domain.user.user import User
from app.domain.user.status import StudentStatus
from app.infrastructure.s21.v1.models.responses.student import ParticipantV1DTO

import pytest
from aiogram.filters import CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import Message

TG_ID = 1001
STUDENT = ParticipantV1DTO(
    login="jdoe",
    className="24_03_TAS",
    parallelName="Core program",
    expValue=100,
    level=1,
    expToNextLevel=300,
    status=StudentStatus.ACTIVE,
    campus={"id": "c-uuid", "shortName": "TAS"},
)


def _message(text: str, tg_id: int = TG_ID) -> MagicMock:
    """Message stub passing isinstance(..., Message) checks."""
    message = MagicMock(spec=Message)
    message.text = text
    message.from_user = MagicMock(id=tg_id)
    message.reply_to_message = None
    message.answer = AsyncMock()
    message.reply = AsyncMock()
    return message


def _sent_text(message: MagicMock) -> str:
    call = message.answer.await_args or message.reply.await_args
    return call.kwargs.get("text") or call.args[0]


def _prefix(template: str) -> str:
    return template.split("{")[0]


@pytest.fixture
async def state(redis):
    storage = RedisStorage(redis=redis)
    ctx = FSMContext(
        storage=storage, key=StorageKey(bot_id=42, chat_id=TG_ID, user_id=TG_ID)
    )
    await ctx.set_state(RegistrationStates.nickname)
    return ctx


@pytest.fixture
def bot():
    return AsyncMock()


async def test_nickname_code_verified_user(
    container, state, bot, i18n, mailer, user_service
):
    container.s21api_client.get_student_by_nickname.return_value = STUDENT

    msg = _message("JDoe")
    await nickname(request=msg, state=state, container=container, bot=bot, i18n=i18n)

    assert await state.get_state() == RegistrationStates.verification.state
    assert _sent_text(msg).startswith(_prefix(i18n.get("nickname-otp-sent")))
    container.s21api_client.get_student_by_nickname.assert_awaited_once_with("jdoe")
    mail = mailer.send_from_template.await_args.kwargs
    assert mail["to"] == "jdoe@student.21-school.ru"
    code = mail["context"]["code"]

    # Wrong code first
    wrong = _message("000000" if code != "000000" else "111111")
    await code_verification(
        message=wrong, state=state, container=container, bot=bot, i18n=i18n
    )
    assert _sent_text(wrong).startswith(_prefix(i18n.get("verification-wrong-code")))
    assert await user_service.get_by_telegram_id(TG_ID) is None

    ok = _message(code)
    await code_verification(
        message=ok, state=state, container=container, bot=bot, i18n=i18n
    )

    user = await user_service.get_by_telegram_id(TG_ID)
    assert user.nickname == "jdoe" and user.is_verified
    assert [v.method for v in user.verifications] == ["email_otp"]
    assert await state.get_state() is None
    assert _sent_text(ok) == i18n.get("verification-success", nickname="jdoe")
    bot.send_message.assert_awaited()
    assert bot.send_message.await_args.args[0] == container.admin_id


async def test_second_nickname_within_minute_rate_limited(
    container, state, bot, i18n, mailer
):
    container.s21api_client.get_student_by_nickname.return_value = STUDENT

    await nickname(
        request=_message("jdoe"), state=state, container=container, bot=bot, i18n=i18n
    )
    await state.set_state(RegistrationStates.nickname)
    second = _message("jdoe")
    await nickname(request=second, state=state, container=container, bot=bot, i18n=i18n)

    assert mailer.send_from_template.await_count == 1
    assert _sent_text(second).startswith(_prefix(i18n.get("rate-limited")))
    assert 0 < await container.redis.ttl(f"rl:otp:{TG_ID}") <= 60


async def test_unknown_nickname(container, state, bot, i18n, mailer):
    container.s21api_client.get_student_by_nickname.return_value = None
    msg = _message("ghost")
    await nickname(request=msg, state=state, container=container, bot=bot, i18n=i18n)
    assert _sent_text(msg) == i18n.get("nickname-not-found", nickname="ghost")
    mailer.send_from_template.assert_not_awaited()


@pytest.fixture
async def invited_and_verified(user_service, campus):
    await user_service.upsert(
        User(nickname="invitee", campus=campus, is_verified=False, invite_otp="inv-otp")
    )
    await user_service.upsert(
        User(nickname="member", campus=campus, is_verified=True, telegram_id=555)
    )


async def test_invited_hidden_from_manual_mention(
    container, i18n, invited_and_verified
):
    msg = _message("/manual_mention invitee")
    await manual_mention(
        message=msg,
        command=CommandObject(args="invitee"),
        container=container,
        i18n=i18n,
    )
    msg.reply.assert_awaited_once_with(
        i18n.get("manual-mention-not-found", nickname="invitee")
    )
    msg.answer.assert_not_awaited()

    msg = _message("/manual_mention member")
    msg.bot = AsyncMock()
    msg.bot.get_chat.return_value = MagicMock(has_private_forwards=True)
    await manual_mention(
        message=msg,
        command=CommandObject(args="member"),
        container=container,
        i18n=i18n,
    )
    assert "member" in msg.answer.await_args.kwargs["text"]


async def test_invited_hidden_from_search(container, i18n, bot, invited_and_verified):
    msg = _message("/search invitee")
    await search(
        message=msg,
        command=CommandObject(args="invitee"),
        container=container,
        bot=bot,
        i18n=i18n,
    )
    msg.reply.assert_awaited_once_with(i18n.get("search-not-found"))

    msg = _message("/search member")
    bot.get_chat.return_value = MagicMock(has_private_forwards=False)
    await search(
        message=msg,
        command=CommandObject(args="member"),
        container=container,
        bot=bot,
        i18n=i18n,
    )
    assert "tg://user?id=555" in msg.answer.await_args.kwargs["text"]
