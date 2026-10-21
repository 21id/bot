from app.bootstrap import Container
from app.domain.user.user import User

from aiogram.filters import Filter
from aiogram.types import TelegramObject


class UserExists(Filter):
    """Filter to check if user exists."""

    def __init__(self, exists: bool) -> None:
        """Initialize filter."""
        self.exists = exists

    async def __call__(
        self, event: TelegramObject, container: Container, db_user: User | None = None
    ) -> bool:
        """Handle call of Telegram event (uses user preloaded by i18n middleware)."""
        user = db_user
        if user is None:
            user = await container.user_service.get_by_telegram_id(
                telegram_id=event.from_user.id
            )

        user_exists = False
        if user is not None:
            user_exists = True

        return user_exists is self.exists
