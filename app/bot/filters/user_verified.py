from app.bootstrap import Container
from app.domain.user.user import User

from aiogram.filters import Filter
from aiogram.types import TelegramObject


class UserVerified(Filter):
    """Filter to check if user is verified."""

    def __init__(self, verified: bool) -> None:
        """Initialize filter."""
        self.verified = verified

    async def __call__(
        self, event: TelegramObject, container: Container, db_user: User | None = None
    ) -> bool:
        """Handle call of Telegram event (uses user preloaded by i18n middleware)."""
        user = db_user
        if user is None:
            user = await container.user_service.get_by_telegram_id(
                telegram_id=event.from_user.id
            )

        user_verified = False
        if user is not None and user.is_verified == True:  # noqa: E712
            user_verified = True

        return user_verified is self.verified
