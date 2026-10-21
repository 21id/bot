from motor.motor_asyncio import AsyncIOMotorDatabase


async def _find_duplicates(
    db: AsyncIOMotorDatabase, collection: str, field: str, match: dict
) -> list[dict]:
    """Return groups of documents sharing the same field value."""
    pipeline = [
        {"$match": match},
        {
            "$group": {
                "_id": f"${field}",
                "ids": {"$push": "$_id"},
                "count": {"$sum": 1},
            }
        },
        {"$match": {"count": {"$gt": 1}}},
    ]
    return await db[collection].aggregate(pipeline).to_list(None)


async def migrate(db: AsyncIOMotorDatabase) -> None:
    """Create unique indexes, refusing to run if duplicates exist."""
    duplicates = {
        "user.nickname": await _find_duplicates(
            db, "user", "nickname", {"nickname": {"$exists": True}}
        ),
        "user.telegram_id": await _find_duplicates(
            db, "user", "telegram_id", {"telegram_id": {"$type": "number"}}
        ),
        "chat.chat_id": await _find_duplicates(
            db, "chat", "chat_id", {"chat_id": {"$exists": True}}
        ),
    }
    duplicates = {key: value for key, value in duplicates.items() if value}
    if duplicates:
        # Not deleting automatically - data has to be fixed manually
        raise Exception(f"Duplicates found, resolve them manually: {duplicates}")

    await db["user"].create_index("nickname", unique=True)
    await db["user"].create_index(
        "telegram_id",
        unique=True,
        partialFilterExpression={"telegram_id": {"$type": "number"}},
    )
    await db["user"].create_index("invite_otp", unique=True, sparse=True)
    await db["chat"].create_index("chat_id", unique=True)
