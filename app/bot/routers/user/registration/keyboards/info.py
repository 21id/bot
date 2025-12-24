from app.bot.routers.user.registration.callback import StartRegistration, RegistrationMenu

from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton, InlineKeyboardMarkup


def get() -> InlineKeyboardMarkup:
    """Creating inline keyboard for info message."""
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(
        text="➡️️ Start verification", callback_data=StartRegistration().pack()
    ))

    builder.row(InlineKeyboardButton(
        text="⬅️ Back", callback_data=RegistrationMenu().pack()
    ))

    return builder.as_markup()
