from app.infrastructure.mongodb import migrations

import pytest


async def test_run_is_idempotent_and_creates_indexes(mongo):
    await migrations.run(mongo.db)
    await migrations.run(mongo.db)

    applied = [d["_id"] async for d in mongo.db["migrations"].find()]
    assert sorted(applied) == [v for v, _ in migrations.MIGRATIONS]

    user_idx = await mongo.users().index_information()
    by_key = {tuple(k for k, _ in v["key"]): v for v in user_idx.values()}
    assert by_key[("nickname",)]["unique"]
    assert by_key[("telegram_id",)]["unique"]
    assert by_key[("telegram_id",)]["partialFilterExpression"] == {
        "telegram_id": {"$type": "number"}
    }
    assert by_key[("invite_otp",)]["unique"] and by_key[("invite_otp",)]["sparse"]

    chat_idx = await mongo.chat().index_information()
    assert any(
        v["key"] == [("chat_id", 1)] and v.get("unique") for v in chat_idx.values()
    )


async def test_001_refuses_duplicate_nicknames(mongo):
    await mongo.users().insert_many([{"nickname": "jdoe"}, {"nickname": "jdoe"}])
    with pytest.raises(Exception, match="Duplicates found"):
        await migrations.run(mongo.db)
    assert await mongo.db["migrations"].count_documents({}) == 0


async def test_001_refuses_duplicate_telegram_ids(mongo):
    await mongo.users().insert_many(
        [{"nickname": "a", "telegram_id": 1}, {"nickname": "b", "telegram_id": 1}]
    )
    with pytest.raises(Exception, match="telegram_id"):
        await migrations.run(mongo.db)


async def test_001_allows_many_null_telegram_ids(mongo):
    await mongo.users().insert_many(
        [{"nickname": "a", "telegram_id": None}, {"nickname": "b", "telegram_id": None}]
    )
    await migrations.run(mongo.db)


async def test_002_and_003_backfill(mongo):
    await mongo.users().insert_many(
        [
            {
                "nickname": "inv",
                "invite_otp": "x",
                "is_verified": False,
                "migration_attempts": {"a": 1},
            },
            {"nickname": "ver", "is_verified": True, "telegram_id": 5},
        ]
    )
    await migrations.run(mongo.db)

    inv = await mongo.users().find_one({"nickname": "inv"})
    assert "invite_expires_at" in inv and "migration_attempts" not in inv

    ver = await mongo.users().find_one({"nickname": "ver"})
    assert ver["verifications"][0]["method"] == "email_otp"
    assert ver["verifications"][0]["telegram_id"] == 5
