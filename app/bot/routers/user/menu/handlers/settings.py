from app.bot.routers.user.menu.router import router
from app.bot.routers.user.menu.callback import Settings
from app.bot.routers.user.menu.keyboard import settings as settings_kb
from app.bot.utilities import reply_edit
from app.bot.i18n.core import I18nContext

from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command


@router.message(Command(commands=["settings"]), F.chat.type.in_({"private"}))
@router.callback_query(Settings.filter())
async def settings(request: Message | CallbackQuery, i18n: I18nContext) -> None:
    """Opening settings page."""
    text = i18n.get("settings-text")
    keyboard = settings_kb.get(i18n)
    await reply_edit.answer(request, text=text, reply_markup=keyboard)
