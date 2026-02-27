from app.bootstrap import Container
from app.bot.routers.chat.admins.router import router
from app.domain.chat.chat import Chat

from aiogram.types import Message
from aiogram.filters import Command


@router.message(Command(commands=["base_create"]))
async def base_create(message: Message, container: Container) -> None:
    """Creating chat object in database."""

    chat = await container.chat_service.get_by_telegram_id(message.chat.id)

    if not chat:
        chat = Chat(chat_id=message.chat.id)
        await container.chat_service.upsert(chat)

        text = "Created chat in database!"
    else:
        text = "Chat already exists in database!"

    await message.reply(text)
