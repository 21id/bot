from aiogram import Router
from aiogram.filters import and_f

router = Router(name="menu")


def register_filters() -> Router:
    """Importing all needed middlewares & filters to add them into users router."""
    from app.bot.filters.user_exists import UserExists
    from app.bot.filters.user_verified import UserVerified

    # Applying filters to check if is fully verified and registered
    verified = and_f(UserExists(exists=True), UserVerified(verified=True))

    router.message.filter(verified)
    router.callback_query.filter(verified)

    return router
