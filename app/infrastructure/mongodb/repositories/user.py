from typing import Any
from bson import ObjectId

from app.domain.user.user import User
from app.infrastructure.mongodb.client import MongoClient

from pymongo.results import UpdateResult, InsertOneResult
from motor.motor_asyncio import AsyncIOMotorCursor


class UserRepository:
    """Users database repository."""

    def __init__(self, client: MongoClient | None):
        """Initialize User Repository."""

        # Params check
        if not all([client]):
            raise ValueError("MongoDB client is required")

        self.collection = client.users()

    async def get_by_telegram_id(self, telegram_id: int) -> dict | None:
        """Get user by his Telegram id."""
        return await self.collection.find_one({"telegram_id": telegram_id})

    async def get_by_nickname(self, nickname: str) -> dict | None:
        """Get user by his Platform's nickname."""
        return await self.collection.find_one({"nickname": nickname})

    async def get_by_invite_otp(self, invite_otp: str) -> dict | None:
        """Get user by invitation OTP."""
        return await self.collection.find_one({"invite_otp": invite_otp})

    def search_by_nickname(self, partial_nickname: str) -> AsyncIOMotorCursor[User]:
        """Searching user by his Platform's nickname."""
        return self.collection.find(
            {"nickname": {"$regex": partial_nickname, "$options": "i"}}
        )

    async def upsert_by_uuid(
            self, user_data: dict, user_uuid: str | None = None
    ) -> UpdateResult | InsertOneResult:
        """Upsert (create or update) user from User model."""

        # If ID is present, we exclude it from data and update object by it
        if user_uuid:
            return await self.collection.update_one(
                {"_id": ObjectId(user_uuid)}, {"$set": user_data}
            )
        # Otherwise - just inserting
        else:
            return await self.collection.insert_one(user_data)

    async def upsert_by_nickname(
            self, user_data: dict, nickname: str | None = None
    ) -> UpdateResult | InsertOneResult:
        """Upsert (create or update) user from User model."""

        # If ID is present, we exclude it from data and update object by it
        if nickname:
            return await self.collection.update_one(
                {"nickname": ObjectId(nickname)}, {"$set": user_data}
            )
        # Otherwise - just inserting
        else:
            return await self.collection.insert_one(user_data)

    async def update(self, user_id: str, update: dict[str, Any]) -> UpdateResult:
        """Updating user."""

        return await self.collection.update_one({"_id": ObjectId(user_id)}, update)
