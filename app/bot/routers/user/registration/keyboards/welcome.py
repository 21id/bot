from app.bot.routers.user.registration.callback import StartRegistration, GetDetails
from app.bot.routers.user.language.callback import ChooseLanguage
from app.bot.i18n.core import I18nContext

from aiogram.utils.keyboard import (
    InlineKeyboardBuilder,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


def get(i18n: I18nContext) -> InlineKeyboardMarkup:
    """Creating inline keyboard for welcome message."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-start-verification"),
            callback_data=StartRegistration().pack(),
        )
    )

    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-learn-more"), callback_data=GetDetails().pack()
        )
    )

    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-language"),
            callback_data=ChooseLanguage(back_to="welcome").pack(),
        )
    )

    return builder.as_markup()
