from motor.motor_asyncio import AsyncIOMotorClient


class MongoClient:
    """MongoDB client."""

    def __init__(self, uri: str, db_name: str):
        """Initialize MongoDB client."""
        # Params check
        if not all([uri, db_name]):
            raise ValueError("uri and db_name are required")

        self.client = AsyncIOMotorClient(uri)
        self.db = self.client[db_name]

    def users(self):
        """Return users collection from database."""
        return self.db["user"]

    def campus(self):
        """Return campus collection from database."""
        return self.db["campus"]

    def chat(self):
        """Return chats collection from database."""
        return self.db["chat"]