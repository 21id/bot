from app.bot.routers.default.router import router

from aiogram import F
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery


@router.callback_query(StateFilter("*"), F.data == "not_provided")
async def not_provided(callback: CallbackQuery) -> None:
    """Handle requests of 'this is not provided'."""

    text = "This information isn't accessible or doesn't exist!"

    await callback.answer(text)
