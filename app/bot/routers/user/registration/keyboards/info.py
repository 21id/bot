from app.bot.routers.user.registration.callback import (
    StartRegistration,
    RegistrationMenu,
)
from app.bot.i18n.core import I18nContext

from aiogram.utils.keyboard import (
    InlineKeyboardBuilder,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


def get(i18n: I18nContext) -> InlineKeyboardMarkup:
    """Creating inline keyboard for info message."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-start-verification"),
            callback_data=StartRegistration().pack(),
        )
    )

    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-back"), callback_data=RegistrationMenu().pack()
        )
    )

    return builder.as_markup()
