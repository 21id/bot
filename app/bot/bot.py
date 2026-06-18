from pathlib import Path

from app.bootstrap import Container
from app.bot.middlewares.error_handler import ErrorMiddleware
from app.bot.routers import register_handlers
from app.i18n.core import I18nCore
from app.i18n.middleware import I18nMiddleware

from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.redis import RedisStorage


async def main(botapi_token: str, container: Container) -> None:
    """Running Telegram bot via Bot API with Aiogram."""
    if botapi_token is None:
        raise Exception("BotAPI token is required")

    locales_dir = str(Path(__file__).parent.parent / "locales")
    i18n_core = I18nCore(locales_dir=locales_dir)
    i18n_core.load()
    container.i18n_core = i18n_core

    storage = RedisStorage(redis=container.redis)

    dispatcher = Dispatcher(storage=storage)
    dispatcher.update.middleware(ErrorMiddleware())
    dispatcher.update.middleware(I18nMiddleware(i18n_core))
    bot = Bot(token=botapi_token)

    register_handlers(dispatcher)

    try:
        print("Started polling")
        await dispatcher.start_polling(bot, container=container)
    finally:
        await bot.session.close()
        print("Stopped polling")
