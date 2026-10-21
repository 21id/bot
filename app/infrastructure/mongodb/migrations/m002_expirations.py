from datetime import datetime, timedelta, UTC

from motor.motor_asyncio import AsyncIOMotorDatabase


async def migrate(db: AsyncIOMotorDatabase) -> None:
    """Drop ISO-string migration attempts and set invite expiration."""
    # Migration attempts live 15 minutes, so dropping them is safe
    await db["user"].update_many(
        {"migration_attempts": {"$exists": True}},
        {"$unset": {"migration_attempts": ""}},
    )
    await db["user"].update_many(
        {"invite_otp": {"$type": "string"}, "invite_expires_at": {"$exists": False}},
        {"$set": {"invite_expires_at": datetime.now(UTC) + timedelta(days=7)}},
    )
