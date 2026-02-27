from app.bot.routers.user.registration.callback import StartRegistration

from aiogram.utils.keyboard import (InlineKeyboardBuilder, InlineKeyboardButton,
                                    InlineKeyboardMarkup)


def get(chat_id: int, chat_title: str) -> InlineKeyboardMarkup:
    """Creating inline keyboard for join request message."""
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(
        text="➡️️ Start verification", callback_data=StartRegistration(
            approve_join=True, join_chat_id=chat_id, join_chat_title=chat_title).pack()
    ))

    return builder.as_markup()
