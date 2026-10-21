import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.domain.user.user import User
from app.domain.verification.method import VerificationMethod
from app.domain.verification.service import VerificationService
from app.infrastructure.verification.email_otp import (
    EmailOtpProvider,
    MigrationOtpProvider,
)

import pytest
from fakeredis import FakeAsyncRedis

EMAIL = VerificationMethod.EMAIL_OTP
MIGRATION = VerificationMethod.MIGRATION_OTP


@pytest.fixture
async def redis():
    r = FakeAsyncRedis(decode_responses=True)
    yield r
    await r.aclose()


@pytest.fixture
def mailer():
    m = MagicMock()
    m.send_from_template = AsyncMock(return_value=True)
    return m


@pytest.fixture
def user_service():
    s = MagicMock()
    s.verify = AsyncMock()
    s.upsert = AsyncMock()
    return s


@pytest.fixture
def service(redis, mailer, user_service):
    return VerificationService(
        providers=[EmailOtpProvider(mail_client=mailer), MigrationOtpProvider()],
        redis=redis,
        user_service=user_service,
    )


async def test_start_sends_email_and_stores_challenge(service, mailer, redis):
    challenge = await service.start(EMAIL, "42", "jdoe", {"extra": 1})
    code = challenge["code"]
    assert len(code) == 6 and code.isdigit()

    kwargs = mailer.send_from_template.await_args.kwargs
    assert kwargs["to"] == "jdoe@student.21-school.ru"
    assert kwargs["context"] == {"username": "jdoe", "code": code, "extra": 1}
    assert await service.get(EMAIL, "42") == {"code": code}
    assert 3590 < await redis.ttl("verif:email_otp:42") <= 3600


async def test_start_not_delivered_stores_nothing(service, mailer, redis):
    mailer.send_from_template.return_value = False
    assert await service.start(EMAIL, "42", "jdoe") is None
    assert await redis.get("verif:email_otp:42") is None


async def test_correct_code_passes_and_drops_challenge(service):
    code = (await service.start(EMAIL, "42", "jdoe"))["code"]
    result = await service.check(EMAIL, "42", code)
    assert result.passed and result.remaining == 10
    assert await service.check(EMAIL, "42", code) is None


async def test_wrong_codes_counted_until_exhausted(service, redis):
    code = (await service.start(EMAIL, "42", "jdoe"))["code"]
    wrong = "000000" if code != "000000" else "111111"
    for expected in range(9, -1, -1):
        result = await service.check(EMAIL, "42", wrong)
        assert not result.passed and result.remaining == expected
    # TTL preserved between wrong attempts
    assert await redis.ttl("verif:email_otp:42") > 0

    result = await service.check(EMAIL, "42", wrong)
    assert result.remaining == -1
    assert await service.get(EMAIL, "42") is None
    # Even the right code is useless now
    assert await service.check(EMAIL, "42", code) is None


async def test_migration_otp_has_three_attempts(service):
    await service.start(MIGRATION, "u:1", "jdoe")
    remaining = [
        (await service.check(MIGRATION, "u:1", "nope")).remaining for _ in range(4)
    ]
    assert remaining == [2, 1, 0, -1]
    assert await service.get(MIGRATION, "u:1") is None


async def test_challenge_expires(redis, user_service):
    provider = MigrationOtpProvider()
    provider.ttl = 1
    service = VerificationService([provider], redis, user_service)
    code = (await service.start(MIGRATION, "s", "jdoe"))["code"]
    await asyncio.sleep(1.1)
    assert await service.check(MIGRATION, "s", code) is None


async def test_start_replaces_previous_challenge(service):
    first = (await service.start(EMAIL, "42", "jdoe"))["code"]
    second = (await service.start(EMAIL, "42", "jdoe"))["code"]
    assert await service.get(EMAIL, "42") == {"code": second}
    if first != second:
        assert not (await service.check(EMAIL, "42", first)).passed


async def test_cancel(service):
    await service.start(EMAIL, "42", "jdoe")
    await service.cancel(EMAIL, "42")
    assert await service.get(EMAIL, "42") is None


@pytest.mark.parametrize(
    "provider", [EmailOtpProvider(MagicMock()), MigrationOtpProvider()]
)
async def test_check_uses_constant_time_compare(provider):
    with patch(
        "app.infrastructure.verification.email_otp.secrets.compare_digest",
        return_value=True,
    ) as compare:
        assert await provider.check({"code": "ABC"}, "ABC")
    compare.assert_called_once_with(b"ABC", b"ABC")


async def test_complete_new_user_upserts_with_record(service, user_service, campus):
    user = User(nickname="jdoe", campus=campus, is_verified=False)
    await service.complete(user, EMAIL, telegram_id=7)
    user_service.upsert.assert_awaited_once_with(user)
    assert user.is_verified and user.telegram_id == 7
    assert user.verifications[0].method == EMAIL
    assert user.verifications[0].telegram_id == 7


async def test_complete_stored_user_verifies(service, user_service, campus):
    user = User(
        id="65f000000000000000000000", nickname="jdoe", campus=campus, is_verified=False
    )
    await service.complete(user, VerificationMethod.INVITE, telegram_id=7)
    user_service.verify.assert_awaited_once()
    record = user_service.verify.await_args.args[1]
    assert record.method == VerificationMethod.INVITE and record.telegram_id == 7
    user_service.upsert.assert_not_awaited()
