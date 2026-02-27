from app.bootstrap import Container

from aiogram.filters import Filter
from aiogram.types import TelegramObject


class UserExists(Filter):
    """Filter to check if user exists."""

    def __init__(self, exists: bool) -> None:
        """Initialize filter."""
        self.exists = exists

    async def __call__(self, event: TelegramObject, container: Container) -> bool:
        """Handle call of Telegram event."""
        user_id = event.from_user.id

        user = await container.user_service.get_by_telegram_id(telegram_id=user_id)

        user_exists = False
        if user is not None:
            user_exists = True

        return user_exists is self.exists
