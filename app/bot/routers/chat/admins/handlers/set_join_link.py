from app.bootstrap import Container
from app.bot.routers.chat.admins.router import router

from aiogram.types import Message
from aiogram.filters import Command, CommandObject


@router.message(Command(commands=["set_join_link"]))
async def set_join_link(message: Message, command: CommandObject,
                        container: Container) -> None:
    """Setting join link in chat settings."""

    join_link: str = command.args

    # Returning if no join link has been provided
    if not join_link:
        text = "No join link provided!\n\nExample: /set_join_link https://t.me/SOMELINK"
        await message.reply(text)

        return

    await container.chat_service.set_join_link(message.chat.id, join_link)

    text = (
        f"Successfully set join link to {join_link}!\n"
        f"Setting will propagate immediately."
    )
    await message.reply(text)
