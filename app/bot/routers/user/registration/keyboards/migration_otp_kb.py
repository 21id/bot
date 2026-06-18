from app.bot.routers.user.registration.callback import (ChangeNickname,
                                                         SendMigrationOtpEmail)
from app.i18n.core import I18nContext

from aiogram.utils.keyboard import (InlineKeyboardBuilder, InlineKeyboardButton,
                                    InlineKeyboardMarkup)


def get(i18n: I18nContext) -> InlineKeyboardMarkup:
    """Creating inline keyboard for migration OTP input step."""
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(
        text=i18n.get("btn-send-via-email"),
        callback_data=SendMigrationOtpEmail().pack()
    ))

    builder.row(InlineKeyboardButton(
        text=i18n.get("btn-back-change-nickname"),
        callback_data=ChangeNickname().pack()
    ))

    return builder.as_markup()
