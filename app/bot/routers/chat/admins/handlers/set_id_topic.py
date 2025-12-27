from app.bootstrap import Container
from app.bot.routers.chat_admins.router import router

from aiogram.types import Message
from aiogram.filters import Command


@router.message(Command(commands=["set_id_topic"]))
async def set_id_topic(message: Message, container: Container) -> None:
    """Setting 'id_topic_id' (id of topic for ID messages) in chat settings."""

    chat = await container.chat_service.get_by_telegram_id(message.chat.id)

    # Checking if inside topic
    if not message.is_topic_message:
        text = "Not in a topic!"

        await message.reply(text)
        return

    topic_id = message.message_thread_id

    # Updating topic id
    await container.chat_service.update_topic_id(chat_id=chat.chat_id,
                                                 topic_id=topic_id)

    text = "Updated topic!"
    await message.reply(text)
