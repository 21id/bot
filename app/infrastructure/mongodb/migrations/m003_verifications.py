from motor.motor_asyncio import AsyncIOMotorDatabase


async def migrate(db: AsyncIOMotorDatabase) -> None:
    """Backfill verification records, drop Mongo migration attempts.

    Migration OTP challenges moved to Redis and live 15 minutes, so dropping
    them is safe.
    """
    await db["user"].update_many(
        {"is_verified": True, "verifications": {"$exists": False}},
        [
            {
                "$set": {
                    "verifications": [
                        {
                            "method": "email_otp",
                            "verified_at": {"$ifNull": ["$verified_at", "$created_at"]},
                            "telegram_id": "$telegram_id",
                            "details": None,
                        }
                    ]
                }
            }
        ],
    )
    await db["user"].update_many(
        {"migration_attempts": {"$exists": True}},
        {"$unset": {"migration_attempts": ""}},
    )
