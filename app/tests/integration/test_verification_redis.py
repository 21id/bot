import asyncio

from app.domain.user.user import User
from app.domain.verification.method import VerificationMethod

EMAIL = VerificationMethod.EMAIL_OTP


async def test_challenge_lifecycle(verification_service, redis):
    code = (await verification_service.start(EMAIL, "42", "jdoe"))["code"]
    assert 3590 < await redis.ttl("verif:email_otp:42") <= 3600

    result = await verification_service.check(EMAIL, "42", "x" + code)
    assert not result.passed and result.remaining == 9
    assert await redis.ttl("verif:email_otp:42") > 3500

    result = await verification_service.check(EMAIL, "42", code)
    assert result.passed
    assert await redis.exists("verif:email_otp:42") == 0


async def test_attempts_exhausted(verification_service):
    await verification_service.start(VerificationMethod.MIGRATION_OTP, "s", "jdoe")
    results = [
        await verification_service.check(VerificationMethod.MIGRATION_OTP, "s", "bad")
        for _ in range(5)
    ]
    assert [r.remaining if r else None for r in results] == [2, 1, 0, -1, None]


async def test_expired_challenge(verification_service, redis):
    await verification_service.start(EMAIL, "42", "jdoe")
    await redis.pexpire("verif:email_otp:42", 50)
    await asyncio.sleep(0.2)
    assert await verification_service.check(EMAIL, "42", "000000") is None


async def test_complete_creates_verified_user(
    verification_service, user_service, campus
):
    user = User(nickname="jdoe", campus=campus, is_verified=False)
    await verification_service.complete(user, EMAIL, telegram_id=11)
    stored = await user_service.get_by_telegram_id(11)
    assert stored.is_verified and stored.verifications[0].method == EMAIL
