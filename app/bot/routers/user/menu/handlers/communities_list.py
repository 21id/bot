from app.bootstrap import Container
from app.bot.routers.user.menu.callback import GetCommunities
from app.bot.routers.user.menu.router import router
from app.bot.routers.user.menu.keyboard import communities_list as communities_list_kb
from app.i18n.core import I18nContext

from aiogram.types import CallbackQuery


@router.callback_query(GetCommunities.filter())
async def communities(
    callback: CallbackQuery, container: Container, i18n: I18nContext
):
    chats = container.chat_service.get_all_public()
    keyboard = await communities_list_kb.get(chats)
    text = i18n.get("communities-text")
    await callback.message.edit_text(text, reply_markup=keyboard)
