from app.bootstrap import Container
from app.bot.routers.chat.admins.router import router

from aiogram.types import Message
from aiogram.filters import Command, CommandObject
from aiogram.enums import ParseMode

from app.bot.routers.user.registration.keyboards import (student_deeplink as
                                                         student_deeplink_kb)


@router.message(Command(commands=["manual_mention"]))
async def manual_mention(message: Message, command: CommandObject,
                         container: Container) -> None:
    """Sending 'id message' in chat."""

    nickname: str = command.args

    # Checking if user exists
    user = await container.user_service.get_by_nickname(nickname)

    if not user:
        text = f"User {nickname} not found!"

        await message.reply(text)
        return

    local_text = (
        f'<a href="tg://user?id={user.telegram_id}">{user.nickname}</a> '
        f'({user.wave_name}, {user.campus.short_name})'
    )

    chat_info = await message.bot.get_chat(user.telegram_id)
    if not chat_info.has_private_forwards:
        keyboard = student_deeplink_kb.get(chat_id=user.telegram_id,
                                           nickname=user.nickname)
    else:
        keyboard = student_deeplink_kb.get(nickname=user.nickname)

    await message.answer(
        text=local_text,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML,
    )
