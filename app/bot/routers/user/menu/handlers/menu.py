from app.bootstrap import Container
from app.bot.routers.user.menu.router import router

from aiogram.types import Message
from aiogram.filters import Command


@router.message(Command(commands=["start"]))
async def menu(message: Message, container: Container):
    user_id = message.from_user.id

    user = await container.user_service.get_by_telegram_id(user_id)

    text = (
        f"👋 Hey, {user.nickname}!\n\nNothing here for now, but something interesting "
        "will be here later 😉"
    )

    await message.reply(text)