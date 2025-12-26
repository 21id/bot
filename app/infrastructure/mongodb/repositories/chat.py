from typing import Any

from app.infrastructure.mongodb.client import MongoClient

from pymongo.results import UpdateResult


class ChatRepository:
    """Chats database repository."""

    def __init__(self, client: MongoClient | None):
        """Initialize Chat Repository."""

        # Params check
        if not all([client]):
            raise ValueError("MongoDB client is required")

        self.collection = client.chat()

    async def get_by_telegram_id(self, telegram_id: int) -> dict | None:
        """Get user by his Telegram id."""
        return await self.collection.find_one({"chat_id": telegram_id})

    async def upsert(self, chat_data: dict, chat_id: int) -> dict | None:
        """Update or insert chat by chat_id."""

        return await self.collection.update_one(
            {"chat_id": chat_id}, {"$set": chat_data}, upsert=True
        )

    async def update(self, chat_id: int, update: dict[str, Any]) -> UpdateResult:
        """Updating chat."""
        return await self.collection.update_one({"chat_id": chat_id}, update)
