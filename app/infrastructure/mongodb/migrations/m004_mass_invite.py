from motor.motor_asyncio import AsyncIOMotorDatabase


async def migrate(db: AsyncIOMotorDatabase) -> None:
    """Drop mass-invite links once they expire."""
    await db["mass_invite"].create_index("expires_at", expireAfterSeconds=0)
