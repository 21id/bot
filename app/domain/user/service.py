from datetime import datetime, UTC
from typing import AsyncGenerator

from app.domain.user.errors import DuplicateUserError
from app.domain.user.user import User
from app.domain.verification.record import VerificationRecord
from app.infrastructure.mongodb.repositories.user import UserRepository

from pymongo.errors import DuplicateKeyError


class UserService:
    """Users service."""

    def __init__(self, repo: UserRepository | None) -> None:
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
            # Expired invites are treated as non-existent
            expires_at = user.invite_expires_at
            if expires_at and expires_at < datetime.now(UTC):
                user = None

        return user

    async def telegram_id_taken(
        self, telegram_id: int, exclude_user_id: str | None = None
    ) -> bool:
        """Check if Telegram ID is linked to another user."""
        document = await self.repo.get_by_telegram_id(telegram_id)
        if not document:
            return False
        return str(document["_id"]) != str(exclude_user_id)

    async def search_by_nickname(
        self, partial_nickname: str, limit: int = 20
    ) -> AsyncGenerator[User | None, None]:
        """Searching user by his Platform's nickname."""
        cursor = self.repo.search_by_nickname(partial_nickname, limit=limit)

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

        try:
            result = await self.repo.upsert_by_uuid(user_data, user_uuid)
        except DuplicateKeyError as e:
            raise DuplicateUserError(support_details=str(e.details)) from e

        # Return upsert status
        if not result.acknowledged:
            raise Exception("Could not upsert user in database")

    async def verify(self, user: User, record: VerificationRecord) -> None:
        """Mark stored user verified, linking record's Telegram ID.

        Args:
            user: Stored user.
            record: Completed verification, appended to user's verifications.
        """
        try:
            result = await self.repo.update(
                user.id,
                {
                    "$unset": {"invite_otp": "", "migration_attempts": ""},
                    "$set": {
                        "is_verified": True,
                        "verified_at": record.verified_at,
                        "telegram_id": record.telegram_id,
                    },
                    "$push": {"verifications": record.model_dump()},
                },
            )
        except DuplicateKeyError as e:
            raise DuplicateUserError(support_details=str(e.details)) from e

        # Return update status
        if not result.acknowledged:
            raise Exception("Could not verify user in database")

    async def set_language(self, user_id: str, language: str) -> None:
        """Persist the user's chosen locale to the database."""
        await self.repo.update(user_id, {"$set": {"language": language}})

    async def migrate_telegram_id(self, user_id: str, new_tg_id: int) -> None:
        """Link 21ID account to a new Telegram ID (owner-initiated, no challenge)."""
        await self.repo.update(
            user_id,
            {
                "$set": {"telegram_id": new_tg_id, "is_verified": True},
                "$unset": {"migration_attempts": ""},
            },
        )
