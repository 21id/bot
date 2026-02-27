from app.bootstrap import Container

from aiogram.types import ChatMemberOwner, ChatMemberAdministrator
from aiogram.filters import Filter
from aiogram.types import TelegramObject


class IsAdmin(Filter):
    """Filter to check if user is amin."""

    def __init__(self, is_admin: bool) -> None:
        """Initialize filter."""
        self.is_admin = is_admin

    async def __call__(self, event: TelegramObject, container: Container) -> bool:
        """Handle call of Telegram event."""
        member = await event.bot.get_chat_member(event.chat.id, event.from_user.id)

        is_admin = False
        # Check if they are an admin or the creator (owner)
        if isinstance(member, (ChatMemberAdministrator, ChatMemberOwner)):
            is_admin = True

        return is_admin is self.is_admin