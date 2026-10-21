from aiogram import Router
from aiogram.filters import and_f, or_f

router = Router()


def register_filters() -> Router:
    """Importing all needed middlewares & filters to add them into users router."""
    from app.bot.filters.user_exists import UserExists
    from app.bot.filters.user_verified import UserVerified

    # Applying filters to check if user is either not registered at all, or isn't
    # verified (added to database via public chats parsing)
    not_exists = and_f(UserExists(exists=False), UserVerified(verified=False))
    not_verified = and_f(UserExists(exists=True), UserVerified(verified=False))

    router.message.filter(or_f(not_exists, not_verified))
    router.callback_query.filter(or_f(not_exists, not_verified))

    return router
