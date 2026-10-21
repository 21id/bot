from app.bot.routers.user.menu.callback import AccountMigration, Menu
from app.bot.routers.user.language.callback import ChooseLanguage
from app.bot.i18n.core import I18nContext

from aiogram.utils.keyboard import (
    InlineKeyboardBuilder,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


def get(i18n: I18nContext) -> InlineKeyboardMarkup:
    """Creating inline keyboard for settings page."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-account-migration"),
            callback_data=AccountMigration().pack(),
        )
    )

    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-language"),
            callback_data=ChooseLanguage(back_to="settings").pack(),
        )
    )

    builder.row(
        InlineKeyboardButton(text=i18n.get("btn-back"), callback_data=Menu().pack())
    )

    return builder.as_markup()
