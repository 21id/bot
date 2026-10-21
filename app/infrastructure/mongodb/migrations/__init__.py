from datetime import datetime, UTC
from typing import Awaitable, Callable

from app.infrastructure.mongodb.migrations import (
    m001_indexes,
    m002_expirations,
    m003_verifications,
    m004_mass_invite,
)

from motor.motor_asyncio import AsyncIOMotorDatabase

# Ordered list of (version, migration); never reorder or remove applied ones
MIGRATIONS: list[tuple[str, Callable[[AsyncIOMotorDatabase], Awaitable[None]]]] = [
    ("001_indexes", m001_indexes.migrate),
    ("002_expirations", m002_expirations.migrate),
    ("003_verifications", m003_verifications.migrate),
    ("004_mass_invite", m004_mass_invite.migrate),
]


async def run(db: AsyncIOMotorDatabase) -> None:
    """Apply not yet applied migrations in order."""
    applied = {doc["_id"] async for doc in db["migrations"].find({}, {"_id": 1})}

    for version, migrate in MIGRATIONS:
        if version in applied:
            continue
        await migrate(db)
        await db["migrations"].insert_one(
            {"_id": version, "applied_at": datetime.now(UTC)}
        )
