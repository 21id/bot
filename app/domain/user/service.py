from datetime import datetime
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
