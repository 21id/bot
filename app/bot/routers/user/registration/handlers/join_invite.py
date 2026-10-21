import sentry_sdk

from app.bootstrap import Container
from app.domain.verification.method import VerificationMethod
from app.bot.routers.user.registration.router import router
from app.bot.routers.user.menu.keyboard import menu as menu_kb
from app.bot.i18n.core import I18nContext

from aiogram import F
from aiogram.types import Message
from aiogram.filters import CommandObject, CommandStart


@router.message(CommandStart(deep_link=True, magic=~F.args.startswith("mi_")))
async def join_invite(
    message: Message, command: CommandObject, container: Container, i18n: I18nContext
) -> None:
    """Using invite OTP to verify user."""
    invite_otp: str = command.args

    user = await container.user_service.get_by_invite_otp(invite_otp)

    if not user:
        await message.reply(i18n.get("join-invite-not-found"))
        return

    if await container.user_service.telegram_id_taken(message.from_user.id):
        await message.reply(i18n.get("join-invite-already-registered"))
        return

    keyboard = None

    try:
        await container.verification_service.complete(
            user, VerificationMethod.INVITE, message.from_user.id
        )
    except Exception as e:
        sentry_sdk.capture_exception(e)
        text = i18n.get("join-invite-db-error")
    else:
        text = i18n.get("join-invite-success", nickname=user.nickname)
        keyboard = menu_kb.get(i18n)

    await message.reply(text, reply_markup=keyboard)
