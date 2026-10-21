import sentry_sdk

from app.bootstrap import Container
from app.domain.mass_invite.mass_invite import NICKNAME_RE
from app.domain.user.status import StudentStatus
from app.domain.user.user import User
from app.domain.verification.method import VerificationMethod
from app.infrastructure.s21.v1.models.responses.student import ParticipantV1DTO
from app.bot.routers.user.mass_invite.router import router
from app.bot.routers.user.mass_invite.states import MassInviteStates
from app.bot.routers.user.menu.keyboard import menu as menu_kb
from app.bot.i18n.core import I18nContext

from aiogram import F, Bot
from aiogram.types import Message
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import CommandObject, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext


@router.message(
    CommandStart(deep_link=True, magic=F.args.startswith("mi_")),
    F.chat.type == "private",
)
async def redeem_link(
    message: Message,
    command: CommandObject,
    state: FSMContext,
    container: Container,
    i18n: I18nContext,
) -> None:
    """Open mass-invite link and ask for the nickname."""
    user = await container.user_service.get_by_telegram_id(message.from_user.id)
    if user and user.is_verified:
        await message.reply(
            i18n.get("join-invite-already-registered"), reply_markup=menu_kb.get(i18n)
        )
        return

    token = command.args.removeprefix("mi_")
    if not await container.mass_invite_service.get(token):
        await message.reply(i18n.get("mass-invite-not-found"))
        return

    await state.clear()
    await state.set_state(MassInviteStates.nickname)
    await state.update_data(mi_token=token)

    await message.reply(i18n.get("mass-invite-prompt"))


@router.message(StateFilter(MassInviteStates.nickname), F.text)
async def redeem_nickname(  # noqa: C901
    message: Message,
    state: FSMContext,
    container: Container,
    bot: Bot,
    i18n: I18nContext,
) -> None:
    """Verify student, if his nickname is in the mass-invite link."""
    nickname_ = message.text.strip().lower()
    user_tg_id = message.from_user.id

    if not NICKNAME_RE.match(nickname_):
        await message.reply(i18n.get("mass-invite-invalid"))
        return

    rl_key = f"rl:mi:{user_tg_id}"
    count = await container.redis.incr(rl_key)
    if count == 1:
        await container.redis.expire(rl_key, 3600)
    if count > 5:
        seconds = await container.redis.ttl(rl_key)
        await message.reply(i18n.get("rate-limited", seconds=seconds))
        return

    failed = i18n.get("mass-invite-failed", nickname=nickname_)
    token: str = await state.get_value("mi_token")

    link = await container.mass_invite_service.get(token)
    if not link or nickname_ not in link.nicknames or nickname_ in link.used_by:
        await message.reply(failed)
        return

    user = await container.user_service.get_by_nickname(nickname_)
    if user and user.is_verified and user.telegram_id != user_tg_id:
        await message.reply(failed)
        return

    if await container.user_service.telegram_id_taken(
        user_tg_id, exclude_user_id=str(user.id) if user else None
    ):
        await state.clear()
        await message.reply(i18n.get("join-invite-already-registered"))
        return

    try:
        student = await container.s21api_client.get_student_by_nickname(nickname_)
    except Exception as e:
        sentry_sdk.capture_exception(e)
        student = None

    if (
        not isinstance(student, ParticipantV1DTO)
        or student.status == StudentStatus.BLOCKED
    ):
        await message.reply(failed)
        return

    # Marked before completing, so two accounts can't redeem one nickname
    if not await container.mass_invite_service.mark_used(token, nickname_, user_tg_id):
        await message.reply(failed)
        return

    if not user:
        user = User(**student.model_dump(), is_verified=True, telegram_id=user_tg_id)

    try:
        await container.verification_service.complete(
            user, VerificationMethod.MASS_INVITE, user_tg_id, details={"link": token}
        )
    except Exception as e:
        sentry_sdk.capture_exception(e)
        # Releasing nickname, so student can retry without manual fix
        await container.mass_invite_service.unmark_used(token, nickname_)
        await message.reply(failed)
        return

    try:
        campus = user.campus.short_name if user.campus else "-"
        local_text = f"NEW {user.nickname} ({user.wave_name}, {campus}) via mass-invite"
        await bot.send_message(container.admin_id, local_text)
    except TelegramAPIError as e:
        sentry_sdk.capture_exception(e)

    await state.clear()
    await message.reply(
        i18n.get("mass-invite-success", nickname=nickname_),
        reply_markup=menu_kb.get(i18n),
    )
