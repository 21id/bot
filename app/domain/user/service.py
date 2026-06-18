from datetime import datetime, timedelta
from typing import AsyncGenerator

from app.domain.user.user import User
from app.infrastructure.mongodb.repositories.user import UserRepository


class UserService:
    """Users service."""

    def __init__(self, repo: UserRepository | None):
        """Initialize User Service."""

        # Params check
        if not all([repo]):
            raise ValueError("User Repository is required")

        self.repo = repo

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        """Get user by his Telegram id."""
        document = await self.repo.get_by_telegram_id(telegram_id)

        user = None
        if document:
            user = User(**document)

        return user

    async def get_by_nickname(self, nickname: str) -> User | None:
        """Get user by his Platform's nickname."""
        document = await self.repo.get_by_nickname(nickname)

        user = None
        if document:
            user = User(**document)

        return user

    async def get_by_invite_otp(self, invite_otp: str) -> User | None:
        """Get user by invitation OTP."""
        document = await self.repo.get_by_invite_otp(invite_otp)

        user = None
        if document:
            user = User(**document)

        return user

    async def search_by_nickname(
            self, partial_nickname: str
    ) -> AsyncGenerator[User | None, None]:
        """Searching user by his Platform's nickname."""
        cursor = self.repo.search_by_nickname(partial_nickname)

        async for document in cursor:
            if document:
                user = User(**document)
                yield user

    async def upsert(self, user: User, user_uuid: str | None = None) -> None:
        """Upsert user."""

        user_data = user.model_dump()

        # If ID is present - removing it
        if user_uuid or user_data.get("id") or user_data.get("_id"):
            if not user_uuid:
                user_uuid = user_data.get("id") or user_data.get("_id")
            # TODO: user_data = user.model_dump(exclude={"created_at", "id"}) doesn't
            #  exclude, WTF?
            # Manually excluding some values
            user_data.pop("id", None)
            user_data.pop("_id", None)
            user_data.pop("created_at", None)

            result = await self.repo.upsert_by_uuid(user_data, user_uuid)
        else:
            result = await self.repo.upsert_by_uuid(user_data, user_uuid)

        # Return upsert status
        if not result.acknowledged:
            raise Exception("Could not upsert user in database")

    async def verify(self, user: User) -> None:
        """Verifying user."""

        # Set user to verified and unset invite_otp
        result = await self.repo.update(
            user.id, {"$unset": {"invite_otp": ""},
                      "$set": {"is_verified": True, "verified_at": datetime.now(),
                               "telegram_id": user.telegram_id}}
        )

        # Return update status
        if not result.acknowledged:
            raise Exception("Could not verify user in database")

    async def set_migration_attempt(
            self, user_id: str, new_telegram_id: int, otp: str
    ) -> None:
        """Save migration OTP attempt for new_telegram_id trying to claim this account."""
        expires_at = (datetime.now() + timedelta(minutes=15)).isoformat()
        await self.repo.update(
            user_id,
            {"$set": {f"migration_attempts.{new_telegram_id}": {
                "otp": otp,
                "attempts_count": 3,
                "expires_at": expires_at,
            }}}
        )

    async def get_migration_attempt(
            self, nickname: str, new_telegram_id: int
    ) -> dict | None:
        """Get migration attempt data for a given new Telegram ID, or None if expired."""
        document = await self.repo.get_by_nickname(nickname)
        if not document:
            return None
        migration_attempts = document.get("migration_attempts") or {}
        attempt = migration_attempts.get(str(new_telegram_id))
        if not attempt:
            return None
        expires_at = attempt.get("expires_at")
        if expires_at and datetime.fromisoformat(expires_at) < datetime.now():
            return None
        return attempt

    async def decrement_migration_attempt(
            self, user_id: str, new_telegram_id: int
    ) -> None:
        """Decrement the attempts counter for a migration attempt."""
        await self.repo.update(
            user_id,
            {"$inc": {f"migration_attempts.{new_telegram_id}.attempts_count": -1}}
        )

    async def clear_migration_attempt(
            self, user_id: str, new_telegram_id: int
    ) -> None:
        """Remove a migration attempt entry."""
        await self.repo.update(
            user_id,
            {"$unset": {f"migration_attempts.{new_telegram_id}": ""}}
        )

    async def set_language(self, user_id: str, language: str) -> None:
        """Persist the user's chosen locale to the database."""
        await self.repo.update(user_id, {"$set": {"language": language}})

    async def migrate_telegram_id(
            self, user_id: str, new_telegram_id: int
    ) -> None:
        """Migrate 21ID account to a new Telegram ID and clear migration data."""
        await self.repo.update(
            user_id,
            {
                "$set": {"telegram_id": new_telegram_id, "is_verified": True},
                "$unset": {f"migration_attempts.{new_telegram_id}": ""}
            }
        )
