import random

from app.bot.routers.user.migration.callback import MigrateConfirm

from aiogram.utils.keyboard import (InlineKeyboardBuilder, InlineKeyboardButton,
                                    InlineKeyboardMarkup)
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, KeyboardButtonRequestUsers


def get_select_user(i18n=None) -> ReplyKeyboardMarkup:
    """Keyboard for selecting a new Telegram account to migrate to."""
    text = i18n.get("btn-select-account") if i18n else "Select account"
    return ReplyKeyboardMarkup(
        keyboard=[[
            KeyboardButton(
                text=text,
                request_users=KeyboardButtonRequestUsers(
                    request_id=1,
                    user_is_bot=False,
                    max_quantity=1,
                )
            )
        ]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def get_confirm() -> InlineKeyboardMarkup:
    """Confirmation keyboard with 1 yes and 2 no buttons in random order."""
    yes_labels = ("Yes", "100% yes", "Totally", "For sure", "Do it")
    no_labels = ("No", "Nope", "Not a chance", "No way", "Cancel")

    yes_text = random.choice(yes_labels)
    no_texts = random.sample(no_labels, 2)

    buttons = [
        InlineKeyboardButton(
            text=yes_text,
            callback_data=MigrateConfirm(confirmed=True).pack()
        ),
        InlineKeyboardButton(
            text=no_texts[0],
            callback_data=MigrateConfirm(confirmed=False).pack()
        ),
        InlineKeyboardButton(
            text=no_texts[1],
            callback_data=MigrateConfirm(confirmed=False).pack()
        ),
    ]
    random.shuffle(buttons)

    builder = InlineKeyboardBuilder()
    for btn in buttons:
        builder.row(btn)

    return builder.as_markup()
