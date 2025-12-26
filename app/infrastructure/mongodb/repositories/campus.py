from app.infrastructure.mongodb.client import MongoClient
from app.infrastructure.s21.v1.client import S21APIClient
from app.infrastructure.s21.v1.models.responses.campus import Campus

class CampusRepository:
    """Campus database repository."""

    def __init__(self, client: MongoClient | None, s21_api_client: S21APIClient | None):
        """Initialize campus Repository."""

        # Params check
        if not all([client, s21_api_client]):
            raise ValueError("MongoDB and S21API clients are required")

        self.collection = client.campus()

    async def get_by_id(self, id_: int) -> Campus | None:
        """Get campus by its id."""
        return await self.collection.find_one({"id": id_})

    async def get_by_uuid(self, uuid: int) -> Campus | None:
        """Get campus by its UUID from API."""
        return await self.collection.find_one({"uuid": uuid})
