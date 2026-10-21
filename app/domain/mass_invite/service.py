import secrets
from datetime import datetime, UTC

from app.domain.mass_invite.mass_invite import MassInvite
from app.infrastructure.mongodb.repositories.mass_invite import MassInviteRepository


class MassInviteService:
    """Mass-invite links service (temporary feature)."""

    def __init__(self, repo: MassInviteRepository | None) -> None:
        """Initialize Mass-invite Service."""
        # Params check
        if not all([repo]):
            raise ValueError("Mass-invite Repository is required")

        self.repo = repo

    async def create(self, nicknames: list[str], created_by: int) -> MassInvite:
        """Create link for nicknames."""
        link = MassInvite(
            id=secrets.token_urlsafe(16), nicknames=nicknames, created_by=created_by
        )
        data = link.model_dump()
        data["_id"] = data.pop("id")
        await self.repo.insert(data)
        return link

    async def get(self, token: str) -> MassInvite | None:
        """Get active link, expired links are treated as non-existent."""
        document = await self.repo.get(token)
        if not document:
            return None

        link = MassInvite(**document)
        if link.expires_at < datetime.now(UTC):
            return None
        return link

    async def mark_used(self, token: str, nickname: str, telegram_id: int) -> bool:
        """Bind nickname of the link to Telegram id, False if already used."""
        return await self.repo.mark_used(token, nickname, telegram_id)

    async def unmark_used(self, token: str, nickname: str) -> None:
        """Release nickname of the link after a failed verification."""
        await self.repo.unmark_used(token, nickname)
