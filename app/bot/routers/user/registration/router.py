from aiogram import Router

router = Router()


def register_filters() -> Router:
    """Importing all needed middlewares & filters to add them into users router."""
    from app.bot.filters.user_exists import UserExists
    from app.bot.filters.user_verified import UserVerified

    # Applying filters to check if user is either not registered at all, or isn't
    # verified (added to database via public chats parsing)
    not_exists = UserExists(exists=False) and UserVerified(verified=False)
    not_verified = UserExists(exists=True) and UserVerified(verified=False)

    router.message.filter(not_exists or not_verified)
    router.callback_query.filter(not_exists or not_verified)

    return router
