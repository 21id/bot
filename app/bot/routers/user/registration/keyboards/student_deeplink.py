from app.bot.routers.user.search.callback import SendNotification

from aiogram.utils.keyboard import (InlineKeyboardBuilder, InlineKeyboardButton,
                                    InlineKeyboardMarkup)


def get(chat_id: int = None, nickname: str = None) -> (
        InlineKeyboardMarkup):
    """Creating inline keyboard to get student via deeplink."""
    builder = InlineKeyboardBuilder()

    if chat_id:
        builder.row(InlineKeyboardButton(
            text="🔗 Open profile", url=f"tg://user?id={chat_id}"
        ))

    if nickname:
        builder.row(InlineKeyboardButton(
            text=f"📤 Send notification",
            callback_data=SendNotification(nickname=nickname).pack(),
        ))

    return builder.as_markup()
