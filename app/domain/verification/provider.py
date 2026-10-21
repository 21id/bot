from typing import Protocol

from app.domain.verification.method import VerificationMethod


class VerificationProvider(Protocol):
    """Issues and checks challenges of one verification method.

    Challenge state (returned by start) is persisted by VerificationService, so
    providers stay stateless. E.g. email OTP keeps {"code": ...}, Face ID could
    keep {"session_id": ...} and check the liveness result in check().
    """

    method: VerificationMethod
    # Wrong responses allowed and challenge lifetime in seconds
    max_attempts: int
    ttl: int

    async def start(self, nickname: str, context: dict) -> dict | None:
        """Issue and deliver a challenge.

        Args:
            nickname: School 21 nickname being verified.
            context: Method specific data (e.g. template variables).

        Returns:
            Challenge state to persist, or None if it couldn't be delivered.
        """
        ...

    async def check(self, challenge: dict, response: str) -> bool:
        """Check user response against persisted challenge state."""
        ...
