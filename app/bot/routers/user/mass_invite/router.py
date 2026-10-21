from app.bootstrap import Container

from aiogram import Router
from aiogram.types import CallbackQuery, Message

# Temporary feature: no router-wide filters, student handlers serve everyone
router = Router(name="mass_invite")


def is_owner(event: Message | CallbackQuery, container: Container) -> bool:
    """Filter passing only the bot owner (ADMIN_ID)."""
    return event.from_user.id == container.admin_id


def register_filters() -> Router:
    """Import handlers to register them and return router."""
    from .handlers import create, redeem  # noqa: F401

    return router
