from app.bot.routers.user.registration.router import router
from app.bot.routers.user.registration.callback import GetDetails
from app.bot.routers.user.registration.keyboards import info as info_kb
from app.bot.i18n.core import I18nContext

from aiogram.types import CallbackQuery
from aiogram.filters import StateFilter


@router.callback_query(StateFilter(None), GetDetails.filter())
async def info(callback: CallbackQuery, i18n: I18nContext) -> None:
    """Information page."""
    text = i18n.get("info-text")
    keyboard = info_kb.get(i18n)
    await callback.message.edit_text(text, reply_markup=keyboard)
