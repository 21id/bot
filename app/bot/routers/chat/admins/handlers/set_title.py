from app.bootstrap import Container
from app.bot.routers.chat.admins.router import router

from aiogram.types import Message
from aiogram.filters import Command, CommandObject


@router.message(Command(commands=["set_title"]))
async def set_title(message: Message, command: CommandObject,
                    container: Container) -> None:
    """Setting title to command argument."""

    title: str = command.args

    # Setting title on join
    await container.chat_service.set_title(message.chat.id, title)

    text = (
        f"Successfully set chat title to {title}"
    )
    await message.reply(text)
