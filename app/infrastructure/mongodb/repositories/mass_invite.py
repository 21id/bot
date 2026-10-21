from app.infrastructure.mongodb.client import MongoClient


class MassInviteRepository:
    """Mass-invite links database repository (temporary feature)."""

    def __init__(self, client: MongoClient | None) -> None:
        """Initialize Mass-invite Repository."""
        # Params check
        if not all([client]):
            raise ValueError("MongoDB client is required")

        self.collection = client.mass_invite()

    async def insert(self, data: dict) -> None:
        """Insert link."""
        await self.collection.insert_one(data)

    async def get(self, token: str) -> dict | None:
        """Get link by its token."""
        return await self.collection.find_one({"_id": token})

    async def mark_used(self, token: str, nickname: str, telegram_id: int) -> bool:
        """Atomically bind nickname to Telegram id, False if already used."""
        result = await self.collection.update_one(
            {"_id": token, f"used_by.{nickname}": {"$exists": False}},
            {"$set": {f"used_by.{nickname}": telegram_id}},
        )
        return result.modified_count == 1

    async def unmark_used(self, token: str, nickname: str) -> None:
        """Release nickname of the link, so it can be redeemed again."""
        await self.collection.update_one(
            {"_id": token}, {"$unset": {f"used_by.{nickname}": ""}}
        )
