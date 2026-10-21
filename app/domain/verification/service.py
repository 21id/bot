import json
from dataclasses import dataclass

from app.domain.user.service import UserService
from app.domain.user.user import User
from app.domain.verification.method import VerificationMethod
from app.domain.verification.provider import VerificationProvider
from app.domain.verification.record import VerificationRecord

from redis.asyncio import Redis


@dataclass
class CheckResult:
    """Outcome of a challenge check.

    remaining = max_attempts - wrong responses; challenge is dropped once passed
    or remaining goes below zero.
    """

    passed: bool
    remaining: int


class VerificationService:
    """Runs verification challenges and records completed verifications."""

    def __init__(
        self,
        providers: list[VerificationProvider],
        redis: Redis,
        user_service: UserService,
    ) -> None:
        """Initialize Verification Service."""
        self.providers = {provider.method: provider for provider in providers}
        self.redis = redis
        self.user_service = user_service

    @staticmethod
    def _key(method: VerificationMethod, subject: str) -> str:
        """Redis key of a challenge.

        subject identifies who answers the challenge (e.g. Telegram id), it's
        not the 21ID identity.
        """
        return f"verif:{method}:{subject}"

    async def start(
        self,
        method: VerificationMethod,
        subject: str,
        nickname: str,
        context: dict | None = None,
    ) -> dict | None:
        """Start a challenge, replacing the previous one of the subject.

        Returns:
            Challenge state, or None if provider couldn't deliver it.
        """
        provider = self.providers[method]
        challenge = await provider.start(nickname, context or {})
        if challenge is None:
            return None

        state = {"challenge": challenge, "remaining": provider.max_attempts}
        await self.redis.set(
            self._key(method, subject), json.dumps(state), ex=provider.ttl
        )
        return challenge

    async def get(self, method: VerificationMethod, subject: str) -> dict | None:
        """Get active challenge state, or None if absent/expired."""
        raw = await self.redis.get(self._key(method, subject))
        return json.loads(raw)["challenge"] if raw else None

    async def check(
        self, method: VerificationMethod, subject: str, response: str
    ) -> CheckResult | None:
        """Check response, counting wrong ones.

        Returns:
            Check result, or None if there is no active challenge.
        """
        key = self._key(method, subject)
        raw = await self.redis.get(key)
        if not raw:
            return None
        state = json.loads(raw)

        passed = await self.providers[method].check(state["challenge"], response)
        if not passed:
            state["remaining"] -= 1

        if passed or state["remaining"] < 0:
            await self.redis.delete(key)
        else:
            await self.redis.set(key, json.dumps(state), keepttl=True)

        return CheckResult(passed=passed, remaining=state["remaining"])

    async def cancel(self, method: VerificationMethod, subject: str) -> None:
        """Drop active challenge."""
        await self.redis.delete(self._key(method, subject))

    async def complete(
        self,
        user: User,
        method: VerificationMethod,
        telegram_id: int | None,
        details: dict | None = None,
    ) -> None:
        """Mark user verified, link telegram_id and store verification record.

        Creates the user if he isn't stored yet.
        """
        record = VerificationRecord(
            method=method, telegram_id=telegram_id, details=details
        )
        user.telegram_id = telegram_id
        user.is_verified = True
        user.verified_at = record.verified_at

        if user.id:
            await self.user_service.verify(user, record)
        else:
            user.verifications.append(record)
            await self.user_service.upsert(user)
