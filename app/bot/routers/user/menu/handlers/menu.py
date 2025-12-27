from app.bootstrap import Container
from app.bot.routers.user.menu.callback import Menu
from app.bot.routers.user.menu.router import router
from app.bot.routers.user.menu.keyboard import menu as menu_kb
from app.bot.utilities import reply_edit

from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command


@router.message(Command(commands=["start", "menu", "main"]),
                F.chat.type.in_({"private"}))
@router.callback_query(Menu.filter())
async def menu(request: Message | CallbackQuery, container: Container):
    user_id = request.from_user.id

    user = await container.user_service.get_by_telegram_id(user_id)

    text = (
        f"👋 Hey, {user.nickname}!"
    )

    keyboard = menu_kb.get()

    await reply_edit.answer(request, text=text, reply_markup=keyboard)
