from aiogram import Dispatcher


def register_handlers(dispatcher: Dispatcher) -> None:
    """Importing all needed sub-routers to add them into dispatcher."""
    from app.bot.routers import default, user, chat

    routers = [
        default.router,
        user.register_sub_routers(),
        chat.register_sub_routers()
    ]

    dispatcher.include_routers(*routers)
