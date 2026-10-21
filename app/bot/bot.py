from pathlib import Path

from app.bootstrap import Container
from app.bot.middlewares.error_handler import ErrorMiddleware
from app.bot.routers import register_handlers
from app.bot.i18n.core import I18nCore
from app.bot.i18n.middleware import I18nMiddleware

from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.redis import RedisStorage


async def main(botapi_token: str, container: Container) -> None:
    """Running Telegram bot via Bot API with Aiogram."""
    if botapi_token is None:
        raise Exception("BotAPI token is required")

    locales_dir = str(Path(__file__).parent / "locales")
    i18n_core = I18nCore(locales_dir=locales_dir)
    i18n_core.load()
    container.i18n_core = i18n_core

    storage = RedisStorage(redis=container.redis, state_ttl=86400, data_ttl=86400)

    dispatcher = Dispatcher(storage=storage)
    dispatcher.update.middleware(ErrorMiddleware(admin_id=container.admin_id))
    dispatcher.update.middleware(I18nMiddleware(i18n_core))
    bot = Bot(token=botapi_token)

    register_handlers(dispatcher)

    try:
        print("Started polling")
        await dispatcher.start_polling(bot, container=container)
    finally:
        await bot.session.close()
        await container.s21api_client.close()
        await container.mail_client.close()
        container.mongo.client.close()
        await container.redis.aclose()
        print("Stopped polling")
