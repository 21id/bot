from app.bootstrap import Container
from app.bot.middlewares.error_handler import ErrorMiddleware
from app.bot.routers import register_handlers

from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.redis import RedisStorage


async def main(botapi_token: str, container: Container) -> None:
    """Running Telegram bot via Bot API with Aiogram."""
    # Params check
    if botapi_token is None:
        raise Exception("BotAPI token is required")

    # Creating and setting up Redis FSM Storage
    storage = RedisStorage(redis=container.redis)

    dispatcher = Dispatcher(storage=storage)
    dispatcher.update.middleware(ErrorMiddleware())
    bot = Bot(token=botapi_token)

    # Registering handlers will automatically
    register_handlers(dispatcher)

    try:
        print("Started polling")
        # Passing through container with services
        await dispatcher.start_polling(bot, container=container)
    finally:
        await bot.session.close()
        print("Stopped polling")
