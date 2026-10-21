import html

import sentry_sdk

from app.bootstrap import Container
from app.bot.routers.chat.admins.router import router
from app.bot.i18n.core import I18nContext

from aiogram.exceptions import TelegramAPIError
from aiogram.types import Message
from aiogram.filters import Command, CommandObject
from aiogram.enums import ParseMode

from app.bot.routers.user.registration.keyboards import (
    student_deeplink as student_deeplink_kb,
)


@router.message(Command(commands=["manual_mention"]))
async def manual_mention(
    message: Message,
    command: CommandObject,
    container: Container,
    i18n: I18nContext,
) -> None:
    """Sending 'id message' in chat."""
    nickname: str = command.args

    user = await container.user_service.get_by_nickname(nickname)

    # Invited-but-unregistered users are treated as non-existent
    if not user or user.is_invited:
        await message.reply(
            i18n.get("manual-mention-not-found", nickname=html.escape(str(nickname)))
        )
        return

    nickname_html = html.escape(user.nickname)
    if user.telegram_id:
        nickname_html = f'<a href="tg://user?id={user.telegram_id}">{nickname_html}</a>'
    campus = user.campus.short_name if user.campus else "-"
    local_text = (
        f"{nickname_html} ({html.escape(str(user.wave_name))}, {html.escape(campus)})"
    )

    if user.telegram_id:
        try:
            chat_info = await message.bot.get_chat(user.telegram_id)
            private = chat_info.has_private_forwards
        except TelegramAPIError as e:
            sentry_sdk.capture_exception(e)
            private = True
        if not private:
            keyboard = student_deeplink_kb.get(
                chat_id=user.telegram_id, nickname=user.nickname
            )
        else:
            keyboard = student_deeplink_kb.get(nickname=user.nickname)
    else:
        keyboard = student_deeplink_kb.get(nickname=user.nickname)

    await message.answer(
        text=local_text,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML,
    )
