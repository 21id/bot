import asyncio
from email.message import EmailMessage

from app.infrastructure.mailer.renderer import TemplateRenderer

import aiosmtplib
import sentry_sdk
from aiosmtplib import SMTPResponse


class MailerClient:
    """Email sender client."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        login: str,
        password: str,
        sender: str,
        template_renderer: TemplateRenderer,
        smtp_client: aiosmtplib.SMTP,
    ) -> None:
        """Initialization of mailer client."""
        # Params validation
        if not all([smtp_host, login, password, sender]):
            raise Exception(
                "smtp_host, login / password, sender email and template renderer"
                "are required"
            )

        # Assigning params
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.login = login
        self.password = password
        self.sender = sender
        self.template_renderer = template_renderer
        self.smtp_client = smtp_client
        # Shared SMTP connection can't be used concurrently
        self._lock = asyncio.Lock()

        # Checking if SMTP client is connected to server
        if not smtp_client.is_connected:
            raise Exception("Could not connect to SMTP server")

    @classmethod
    async def initialize(
        cls,
        smtp_host: str,
        smtp_port: int,
        login: str,
        password: str,
        sender: str,
        template_renderer: TemplateRenderer,
    ) -> "MailerClient":
        """Initialization of mailer client from SMTP server, logging in.

        Port 465 uses implicit TLS, any other port (e.g. Brevo's 587) - STARTTLS.
        """
        # Creating SMTP connection and logging in
        smtp = aiosmtplib.SMTP(
            hostname=smtp_host,
            port=smtp_port,
            use_tls=smtp_port == 465,
            start_tls=smtp_port != 465,
            timeout=10,
        )

        await smtp.connect()
        await smtp.login(login, password)

        return cls(
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            login=login,
            password=password,
            sender=sender,
            template_renderer=template_renderer,
            smtp_client=smtp,
        )

    async def _reconnect(self) -> None:
        """Drop current SMTP connection (ignoring errors) and log in again."""
        try:
            await self.smtp_client.quit()
        except aiosmtplib.SMTPException:
            self.smtp_client.close()

        await self.smtp_client.connect()
        await self.smtp_client.login(self.login, self.password)

    async def close(self) -> None:
        """Close SMTP connection, ignoring errors."""
        try:
            await self.smtp_client.quit()
        except aiosmtplib.SMTPException:
            self.smtp_client.close()

    async def send_mail_html(
        self, to: str, subject: str, message_html: str, message_text: str | None = None
    ) -> tuple[dict[str, SMTPResponse], str]:
        """Send email with HTML data."""
        # Header injection protection
        if "\r" in to or "\n" in to:
            raise ValueError("Recipient address must not contain line breaks")

        # If user's client doesn't support HTML - user
        if not message_text:
            message_text = "Please use an HTML-compatible email client."

        msg = EmailMessage()
        msg["From"] = self.sender
        msg["To"] = to
        msg["Subject"] = subject

        msg.set_content(message_text)
        msg.add_alternative(message_html, subtype="html")

        async with self._lock:
            try:
                if not self.smtp_client.is_connected:
                    await self.smtp_client.connect()
                    await self.smtp_client.login(self.login, self.password)

                return await self.smtp_client.send_message(msg)

            except aiosmtplib.SMTPException as e:
                sentry_sdk.add_breadcrumb(
                    category="smtp",
                    level="warning",
                    message=f"SMTP send failed, reconnecting: {type(e).__name__}",
                )
                # Force reconnecting and resending once
                await self._reconnect()
                return await self.smtp_client.send_message(msg)

    async def send_from_template(
        self,
        to: str,
        subject: str,
        template_name: str,
        context: dict,
        default: str | None = None,
    ) -> bool:
        """Send email to user with template.

        :return: Boolean status if message has been sent or not.
        """
        rendered_template = self.template_renderer.render(
            template_name=template_name, context=context
        )

        # Sending a message if template has been rendered
        if rendered_template:
            rejected, _ = await self.send_mail_html(
                to=to,
                subject=subject,
                message_html=rendered_template,
                message_text=default,
            )

            # Sent if server accepted all recipients
            return not rejected

        return False
