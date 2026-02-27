from app.bootstrap import Container
from app.bot.routers.chat.admins.router import router

from aiogram.types import Message
from aiogram.filters import Command, CommandObject


@router.message(Command(commands=["disable_description"]))
async def disable_description(message: Message, container: Container) -> None:
    """Setting description to None, if admin chose to disable it."""

    # Setting description on join to None
    await container.chat_service.set_desc(message.chat.id)

    text = (
        "Successfully removed description on join!"
    )
    await message.reply(text)

@router.message(Command(commands=["set_description"]))
async def set_description(message: Message, command: CommandObject,
                          container: Container) -> None:
    """Setting description to command argument."""

    description: str = command.args

    # Setting description on join to None
    await container.chat_service.set_desc(message.chat.id, description)

    text = (
        f"Successfully set description to..\n\n{description}"
    )
    await message.reply(text)
