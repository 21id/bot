from aiogram import Router
from aiogram.filters import and_f

router = Router(name="migration")


def register_filters() -> Router:
    """Importing all needed middlewares & filters to add them into users router."""
    from app.bot.filters.user_exists import UserExists
    from app.bot.filters.user_verified import UserVerified

    verified = and_f(UserExists(exists=True), UserVerified(verified=True))

    router.message.filter(verified)
    router.callback_query.filter(verified)

    return router
