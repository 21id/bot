from app.bot.routers.user.registration.callback import ChangeNickname, RegistrationMenu

from aiogram.utils.keyboard import (InlineKeyboardBuilder, InlineKeyboardButton,
                                    InlineKeyboardMarkup)


def get(set_change_bt_flag: bool = False) -> InlineKeyboardMarkup:
    """Creating inline keyboard to change nickname."""
    builder = InlineKeyboardBuilder()

    # If this flag is true - means change nickname button is needed
    if set_change_bt_flag:
        builder.row(InlineKeyboardButton(
            text="➡️️ Change nickname", callback_data=ChangeNickname().pack()
        ))

    builder.row(InlineKeyboardButton(
        text="⬅️ Back to menu", callback_data=RegistrationMenu().pack()
    ))

    return builder.as_markup()
