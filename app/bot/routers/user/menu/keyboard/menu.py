from app.bot.routers.user.menu.callback import GetCommunities

from aiogram.utils.keyboard import (InlineKeyboardBuilder, InlineKeyboardButton,
                                    InlineKeyboardMarkup)


def get() -> InlineKeyboardMarkup:
    """Creating inline keyboard for menu message."""

    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(
        text="📄 List communities", callback_data=GetCommunities().pack()
    ))

    return builder.as_markup()
