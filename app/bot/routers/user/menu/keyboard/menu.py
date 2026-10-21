from app.bot.routers.user.menu.callback import GetCommunities, Settings
from app.bot.i18n.core import I18nContext

from aiogram.utils.keyboard import (
    InlineKeyboardBuilder,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


def get(i18n: I18nContext) -> InlineKeyboardMarkup:
    """Creating inline keyboard for menu message."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-list-communities"), callback_data=GetCommunities().pack()
        )
    )

    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-settings"), callback_data=Settings().pack()
        )
    )

    return builder.as_markup()
