from app.bootstrap import Container
from app.bot.routers.user.registration.router import router
from app.bot.routers.user.menu.keyboard import menu as menu_kb
from app.i18n.core import I18nContext

from aiogram.types import Message
from aiogram.filters import CommandObject, CommandStart


@router.message(CommandStart(deep_link=True))
async def join_invite(
    message: Message, command: CommandObject, container: Container, i18n: I18nContext
):
    """Using invite OTP to verify user."""
    invite_otp: str = command.args

    user = await container.user_service.get_by_invite_otp(invite_otp)

    if not user:
        await message.reply(i18n.get("join-invite-not-found"))
        return

    keyboard = None

    try:
        user.telegram_id = message.from_user.id
        await container.user_service.verify(user)
    except Exception as e:
        text = i18n.get("join-invite-db-error", error=e)
    else:
        text = i18n.get("join-invite-success", nickname=user.nickname)
        keyboard = menu_kb.get(i18n)

    await message.reply(text, reply_markup=keyboard)
