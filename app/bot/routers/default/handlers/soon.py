from app.bot.routers.default.router import router

from aiogram import F
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery


@router.callback_query(StateFilter("*"), F.data == "soon")
async def soon(callback: CallbackQuery) -> None:
    """Handle requests, which should indicate that functionality will be added soon."""

    text = (
        "This functionality will be available soon!\n"
        "Contact @megaplov for questions."
    )

    await callback.answer(text)
