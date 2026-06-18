from app.bot.routers.user.registration.callback import ChangeNickname, RegistrationMenu
from app.i18n.core import I18nContext

from aiogram.utils.keyboard import (InlineKeyboardBuilder, InlineKeyboardButton,
                                    InlineKeyboardMarkup)


def get(i18n: I18nContext, set_change_bt_flag: bool = False) -> InlineKeyboardMarkup:
    """Creating inline keyboard to change nickname."""
    builder = InlineKeyboardBuilder()

    if set_change_bt_flag:
        builder.row(InlineKeyboardButton(
            text=i18n.get("btn-change-nickname"),
            callback_data=ChangeNickname().pack()
        ))

    builder.row(InlineKeyboardButton(
        text=i18n.get("btn-back-to-menu"),
        callback_data=RegistrationMenu().pack()
    ))

    return builder.as_markup()
