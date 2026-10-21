import secrets

from app.domain.verification.method import VerificationMethod
from app.infrastructure.mailer.client import MailerClient
from app.utilities import random


class EmailOtpProvider:
    """Numeric OTP sent to student's School 21 email."""

    method = VerificationMethod.EMAIL_OTP
    max_attempts = 10
    ttl = 3600

    def __init__(self, mail_client: MailerClient) -> None:
        """Initialize Email OTP provider."""
        self.mail_client = mail_client

    async def start(self, nickname: str, context: dict) -> dict | None:
        """Send OTP to {nickname}@student.21-school.ru, raises on SMTP errors."""
        code = random.generate_secure_otp()
        is_sent = await self.mail_client.send_from_template(
            to=f"{nickname}@student.21-school.ru",
            subject=f"[{code}] 21ID OTP Code",
            template_name="otp.html",
            context={"username": nickname, "code": code, **context},
        )
        return {"code": code} if is_sent else None

    async def check(self, challenge: dict, response: str) -> bool:
        """Compare OTP in constant time."""
        return secrets.compare_digest(challenge["code"].encode(), response.encode())


class MigrationOtpProvider:
    """Alphanumeric OTP for claiming an account from another Telegram account.

    Only issues the code - delivery (Telegram / email fallback) is done by the
    caller, as it depends on the bot.
    """

    method = VerificationMethod.MIGRATION_OTP
    max_attempts = 3
    ttl = 900

    async def start(self, nickname: str, context: dict) -> dict | None:
        """Generate migration OTP."""
        return {"code": random.generate_migration_otp()}

    async def check(self, challenge: dict, response: str) -> bool:
        """Compare OTP in constant time."""
        return secrets.compare_digest(challenge["code"].encode(), response.encode())
