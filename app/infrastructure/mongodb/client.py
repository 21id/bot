from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection


class MongoClient:
    """MongoDB client."""

    def __init__(self, uri: str, db_name: str) -> None:
        """Initialize MongoDB client."""
        # Params check
        if not all([uri, db_name]):
            raise ValueError("uri and db_name are required")

        self.client = AsyncIOMotorClient(uri, tz_aware=True)
        self.db = self.client[db_name]

    def users(self) -> AsyncIOMotorCollection:
        """Return users collection from database."""
        return self.db["user"]

    def campus(self) -> AsyncIOMotorCollection:
        """Return campus collection from database."""
        return self.db["campus"]

    def chat(self) -> AsyncIOMotorCollection:
        """Return chats collection from database."""
        return self.db["chat"]
