from .router import router
from .handlers import join

from aiogram import Router
from aiogram.filters import and_f


def register_filters() -> Router:
    """Importing all needed middlewares to add them into chat join router."""
    from app.bot.filters.user_exists import UserExists
    from app.bot.filters.user_verified import UserVerified

    # Applying filters to check if user is registered and verified
    is_user = and_f(UserExists(exists=True), UserVerified(verified=True))

    router.message.filter(is_user)
    router.callback_query.filter(is_user)

    return router
