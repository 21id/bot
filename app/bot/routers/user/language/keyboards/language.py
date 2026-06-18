from app.bot.routers.user.language.callback import SetLanguage
from app.i18n.core import I18nContext

from aiogram.utils.keyboard import (InlineKeyboardBuilder, InlineKeyboardButton,
                                    InlineKeyboardMarkup)


def get(
    locales: list[tuple[str, str]],
    back_to: str,
    i18n: I18nContext,
) -> InlineKeyboardMarkup:
    """Language picker keyboard. locales is a list of (locale_code, display_name)."""
    builder = InlineKeyboardBuilder()

    for locale_code, display_name in locales:
        builder.row(InlineKeyboardButton(
            text=display_name,
            callback_data=SetLanguage(locale=locale_code, back_to=back_to).pack()
        ))

    builder.row(InlineKeyboardButton(
        text=i18n.get("btn-back"),
        callback_data=_back_callback(back_to),
    ))

    return builder.as_markup()


def _back_callback(back_to: str) -> str:
    if back_to == "settings":
        from app.bot.routers.user.menu.callback import Settings
        return Settings().pack()
    from app.bot.routers.user.registration.callback import RegistrationMenu
    return RegistrationMenu().pack()
