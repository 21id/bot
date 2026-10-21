import html

import sentry_sdk

from app.bootstrap import Container
from app.bot.routers.user.search.router import router
from app.bot.filters.user_verified import UserVerified
from app.bot.routers.user.registration.keyboards import (
    student_deeplink as student_deeplink_kb,
)
from app.bot.i18n.core import I18nContext

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import Message
from aiogram.filters import Command, CommandObject
from aiogram.enums import ParseMode


@router.message(Command(commands=["search"]), UserVerified(verified=True))
async def search(  # noqa: C901
    message: Message,
    command: CommandObject,
    container: Container,
    bot: Bot,
    i18n: I18nContext,
) -> None:
    """Search for a 21ID user by nickname, @username, Telegram user ID, or reply."""
    user = None

    if message.reply_to_message and message.reply_to_message.from_user:
        target_tg_id = message.reply_to_message.from_user.id
        user = await container.user_service.get_by_telegram_id(target_tg_id)

    elif command.args:
        args = command.args.strip()

        if args.startswith("@"):
            try:
                chat_info = await bot.get_chat(args)
                user = await container.user_service.get_by_telegram_id(chat_info.id)
            except TelegramAPIError:
                # Username not resolvable by bot
                pass

        elif args.isdigit():
            user = await container.user_service.get_by_telegram_id(int(args))

        else:
            user = await container.user_service.get_by_nickname(args.lower())

    else:
        await message.reply(i18n.get("search-usage"))
        return

    # Invited-but-unregistered users are treated as non-existent
    if not user or user.is_invited:
        await message.reply(i18n.get("search-not-found"))
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
            chat_info = await bot.get_chat(user.telegram_id)
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
