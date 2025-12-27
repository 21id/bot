from app.bootstrap import Container
from app.bot.routers.chat.admins.router import router

from aiogram.types import Message
from aiogram.filters import Command, CommandObject


@router.message(Command(commands=["allow_intensive"]))
async def allow_intensive(message: Message, command: CommandObject,
                          container: Container) -> None:
    """Setting 'allow_intensive' in chat settings."""

    action: str = command.args
    positive_actions = ["true", "yes"]
    negative_actions = ["deny", "no"]
    allowed_actions = [*positive_actions, *negative_actions]

    if not action in allowed_actions:
        text = (
            "Invalid action!\nUse true/yes or deny/no\n\n"
            "For example: /allow_intensive false"
        )
        await message.reply(text)

        return

    # Setting 'allow_intensive' in chat settings
    result = False
    if action in positive_actions:
        result = True
    await container.chat_service.set_allow_intensive(message.chat.id, result)

    text = (
        f"Successfully set 'allow_intensive' to {action}!\n"
        f"Setting will propagate immediately."
    )
    await message.reply(text)

@router.message(Command(commands=["allow_core"]))
async def allow_core(message: Message, command: CommandObject,
                     container: Container) -> None:
    """Setting 'allow_core' in chat settings."""

    action: str = command.args
    positive_actions = ["true", "yes"]
    negative_actions = ["deny", "no"]
    allowed_actions = [*positive_actions, *negative_actions]

    if not action in allowed_actions:
        text = (
            "Invalid action!\nUse true/yes or deny/no\n\n"
            "For example: /allow_intensive false"
        )
        await message.reply(text)

        return

    # Setting 'allow_core' in chat settings
    result = False
    if action in positive_actions:
        result = True
    await container.chat_service.set_allow_core(message.chat.id, result)

    text = (
        f"Successfully set 'allow_core' to {action}!\n"
        f"Setting will propagate immediately."
    )
    await message.reply(text)
