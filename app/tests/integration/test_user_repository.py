from datetime import datetime, timedelta, UTC

from app.domain.user.errors import DuplicateUserError
from app.domain.user.user import User
from app.domain.verification.method import VerificationMethod
from app.domain.verification.record import VerificationRecord

import pytest


def _user(campus, nickname="jdoe", **kwargs) -> User:
    kwargs.setdefault("is_verified", False)
    return User(nickname=nickname, campus=campus, **kwargs)


async def test_insert_and_get(user_service, campus):
    await user_service.upsert(_user(campus, telegram_id=1, is_verified=True))
    by_nick = await user_service.get_by_nickname("jdoe")
    by_tg = await user_service.get_by_telegram_id(1)
    assert by_nick.id == by_tg.id and by_nick.campus.short_name == "TAS"
    assert await user_service.get_by_telegram_id(2) is None


async def test_upsert_updates_by_id(user_service, campus):
    await user_service.upsert(_user(campus))
    stored = await user_service.get_by_nickname("jdoe")
    created_at = stored.created_at

    stored.name = "John"
    await user_service.upsert(stored)
    updated = await user_service.get_by_nickname("jdoe")
    assert updated.name == "John" and updated.id == stored.id
    assert abs(updated.created_at - created_at) < timedelta(milliseconds=1)


async def test_duplicate_nickname_raises(user_service, campus):
    await user_service.upsert(_user(campus))
    with pytest.raises(DuplicateUserError):
        await user_service.upsert(_user(campus))


async def test_verify_links_telegram_and_records(user_service, campus):
    await user_service.upsert(_user(campus, invite_otp="otp1"))
    stored = await user_service.get_by_nickname("jdoe")
    record = VerificationRecord(method=VerificationMethod.INVITE, telegram_id=7)
    await user_service.verify(stored, record)

    user = await user_service.get_by_telegram_id(7)
    assert user.is_verified and user.invite_otp is None
    assert user.verifications[0].method == VerificationMethod.INVITE


async def test_verify_duplicate_telegram_id_raises(user_service, campus):
    await user_service.upsert(_user(campus, "taken", telegram_id=7, is_verified=True))
    await user_service.upsert(_user(campus, "other"))
    other = await user_service.get_by_nickname("other")
    with pytest.raises(DuplicateUserError):
        await user_service.verify(
            other,
            VerificationRecord(method=VerificationMethod.EMAIL_OTP, telegram_id=7),
        )


async def test_telegram_id_taken(user_service, campus):
    await user_service.upsert(_user(campus, telegram_id=7, is_verified=True))
    owner = await user_service.get_by_nickname("jdoe")
    assert await user_service.telegram_id_taken(7)
    assert not await user_service.telegram_id_taken(7, exclude_user_id=owner.id)
    assert not await user_service.telegram_id_taken(8)


async def test_invite_expiry(user_service, campus):
    now = datetime.now(UTC)
    await user_service.upsert(
        _user(
            campus, "fresh", invite_otp="ok", invite_expires_at=now + timedelta(days=1)
        )
    )
    await user_service.upsert(
        _user(
            campus,
            "stale",
            invite_otp="old",
            invite_expires_at=now - timedelta(seconds=1),
        )
    )
    fresh = await user_service.get_by_invite_otp("ok")
    assert fresh.nickname == "fresh" and fresh.is_invited
    assert await user_service.get_by_invite_otp("old") is None
    assert await user_service.get_by_invite_otp("missing") is None


async def test_is_invited(user_service, campus):
    await user_service.upsert(_user(campus, "inv", invite_otp="x"))
    await user_service.upsert(_user(campus, "plain"))
    assert (await user_service.get_by_nickname("inv")).is_invited
    assert not (await user_service.get_by_nickname("plain")).is_invited


async def test_search_by_nickname_escapes_regex(user_service, campus):
    for nick in ("alpha", "alphonse", "beta"):
        await user_service.upsert(_user(campus, nick))
    found = [u.nickname async for u in user_service.search_by_nickname("ALPH")]
    assert sorted(found) == ["alpha", "alphonse"]
    assert [u async for u in user_service.search_by_nickname(".*")] == []


async def test_set_language_and_migrate(user_service, campus):
    await user_service.upsert(_user(campus, telegram_id=1, is_verified=True))
    user = await user_service.get_by_nickname("jdoe")
    await user_service.set_language(user.id, "ru")
    await user_service.migrate_telegram_id(user.id, 2)
    moved = await user_service.get_by_telegram_id(2)
    assert moved.language == "ru" and moved.id == user.id
