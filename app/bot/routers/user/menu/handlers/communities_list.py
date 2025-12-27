from app.bootstrap import Container
from app.bot.routers.user.menu.callback import GetCommunities
from app.bot.routers.user.menu.router import router
from app.bot.routers.user.menu.keyboard import communities_list as communities_list_kb

from aiogram.types import CallbackQuery


@router.callback_query(GetCommunities.filter())
async def communities(callback: CallbackQuery, container: Container):
    chats = container.chat_service.get_all_public()

    keyboard = await communities_list_kb.get(chats)

    text = "List of all public communities, which are part of 21ID ecosystem"

    await callback.message.edit_text(text, reply_markup=keyboard)
