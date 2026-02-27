from app.bot.routers.default.router import router

from aiogram import F
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery


@router.callback_query(StateFilter("*"), F.data == "none")
async def none(callback: CallbackQuery) -> None:
    """Handle requests, that should do nothing."""

    await callback.answer()
