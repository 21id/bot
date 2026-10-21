from datetime import datetime, UTC

from app.domain.verification.method import VerificationMethod

from pydantic import BaseModel, Field


class VerificationRecord(BaseModel):
    """Single successful verification of a user.

    telegram_id is the account linked by this verification, if any - the user's
    identity is the 21ID user id, Telegram is just one linked account.
    """

    method: VerificationMethod
    verified_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    telegram_id: int | None = None
    details: dict | None = None
