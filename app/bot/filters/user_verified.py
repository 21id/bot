from app.bootstrap import Container

from aiogram.filters import Filter
from aiogram.types import TelegramObject


class UserVerified(Filter):
    """Filter to check if user is verified."""

    def __init__(self, verified: bool) -> None:
        """Initialize filter."""
        self.verified = verified

    async def __call__(self, event: TelegramObject, container: Container) -> bool:
        """Handle call of Telegram event."""
        user_id = event.from_user.id

        user = await container.user_service.get_by_telegram_id(telegram_id=user_id)

        user_verified = False
        if user is not None and user.is_verified == True:
            user_verified = True

        return user_verified is self.verified
