from aiogram import Dispatcher


def register_handlers(dispatcher: Dispatcher) -> None:
    """Importing all needed sub-routers to add them into dispatcher."""
    from app.bot.routers import default, user, chat_admins

    routers = [
        default.router,
        user.register_sub_routers(),
        chat_admins.register_filters()
    ]

    dispatcher.include_routers(*routers)
