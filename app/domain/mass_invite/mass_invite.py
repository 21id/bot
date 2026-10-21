import re
from datetime import datetime, timedelta, UTC

from app.domain.utils.omit import BaseModel_

from pydantic import ConfigDict, Field

NICKNAME_RE = re.compile(r"^[a-z]{1,8}\Z")
LIFETIME = timedelta(days=30)


class MassInvite(BaseModel_):
    """Link verifying listed students without OTP (temporary feature)."""

    model_config = ConfigDict(populate_by_name=True)

    # Token used in t.me/<bot>?start=mi_<token>
    id: str = Field(alias="_id")
    nicknames: list[str]
    created_by: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime = Field(default_factory=lambda: datetime.now(UTC) + LIFETIME)
    # nickname -> Telegram id which redeemed it
    used_by: dict[str, int] = Field(default_factory=dict)
    # Owner's message (Telegram HTML) sent to students after verification
    welcome_message: str | None = None


def parse_nicknames(text: str) -> tuple[list[str], list[str]]:
    """Split text by commas/whitespace into (valid, invalid) nicknames, deduped."""
    valid: list[str] = []
    invalid: list[str] = []
    for raw in re.split(r"[,\s]+", text or ""):
        nickname = raw.strip().lower()
        if not nickname:
            continue
        target = valid if NICKNAME_RE.match(nickname) else invalid
        if nickname not in target:
            target.append(nickname)
    return valid, invalid
