from aiogram import Router

router = Router(name="chat")


def register_sub_routers() -> Router:
    """Importing all needed sub-routers to add them into users router."""
    from app.bot.routers.chat import admins, join

    routers = [
        admins.register_filters(),
        join.register_filters()
    ]

    router.include_routers(*routers)

    # Also adding all filters
    return register_filters()

def register_filters() -> Router:
    """Importing all needed middlewares to add them into users router."""
    from aiogram import F

    # Checking if message has been sent in a chat
    is_chat = F.chat.type.in_({"group", "supergroup"})

    router.message.filter(is_chat)
    router.callback_query.filter(is_chat)

    return router
