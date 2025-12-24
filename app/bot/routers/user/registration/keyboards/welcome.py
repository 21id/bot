from app.bot.routers.user.registration.callback import StartRegistration, GetDetails

from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton, InlineKeyboardMarkup


def get() -> InlineKeyboardMarkup:
    """Creating inline keyboard for welcome message."""
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(
        text="➡️️ Start verification", callback_data=StartRegistration().pack()
    ))

    builder.row(InlineKeyboardButton(
        text="ℹ️ Learn more about 21ID", callback_data=GetDetails().pack()
    ))

    return builder.as_markup()
