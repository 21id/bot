from app.bootstrap import Container
from app.bot.routers.user.registration.router import router
from app.bot.routers.user.menu.keyboard import menu as menu_kb

from aiogram.types import Message
from aiogram.filters import CommandObject, CommandStart


@router.message(CommandStart(deep_link=True))
async def join_invite(
        message: Message, command: CommandObject, container: Container
):
    """Using invite OTP to verify user."""

    invite_otp: str = command.args

    user = await container.user_service.get_by_invite_otp(invite_otp)

    # Notify user that bot can't find user in database by his invite OTP
    if not user:
        text = (
            f"❌ Dear user, your OTP is expired (already used) or doesn't "
            "exist. Please, try to get your link again from Invitation email\n\n❓ If "
            "you have  any questions or believe that it's a mistake - please contact "
            "@megaplov"
        )

        await message.reply(text)
        return

    keyboard = None

    try:
        # Verify user
        user.telegram_id = message.from_user.id
        await container.user_service.verify(user)
    except Exception as e:
        # TODO: add error logging
        text = (
            f"❗️ Error has occurred on Database update\n\n"
            f"Message: {e}\n\n"
            "✍️ Please, notify @megaplov about this problem from your perspective"
        )
    else:
        text = (
            f"👋 Welcome to 21ID, {user.nickname}!\n\n🔽 Basic functionality that "
            "you may need is right below, which you can access in main menu with "
            "/start command\n\n🪪 To find other peers, please use inline mode. "
            "Guide on how to use 21ID Bot inline search is here: t.me/ident21/9"
        )

        keyboard = menu_kb.get()

    await message.reply(text, keyboard=keyboard)