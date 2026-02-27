from email.message import EmailMessage
from smtplib import SMTPServerDisconnected

from app.infrastructure.mailer.renderer import TemplateRenderer

import aiosmtplib
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
    ):
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
            use_tls: bool = False,
    ) -> "MailerClient":
        """Initialization of mailer client from SMTP server, logging in."""

        # Creating SMTP connection and logging in
        smtp = aiosmtplib.SMTP(
            hostname=smtp_host,
            port=smtp_port,
            use_tls=use_tls,
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
            smtp_client=smtp
        )

    async def send_mail_html(self, to: str, subject: str, message_html: str,
                             message_text: str | None = None) -> (dict, str):
        """Send email with HTML data."""

        # If user's client doesn't support HTML - user
        if not message_text:
            message_text = "Please use an HTML-compatible email client."

        msg = EmailMessage()
        msg["From"] = self.sender
        msg["To"] = to
        msg["Subject"] = subject

        msg.set_content(message_text)
        msg.add_alternative(message_html, subtype="html")

        try:
            if not self.smtp_client.is_connected:
                await self.smtp_client.connect()
                await self.smtp_client.login(self.login, self.password)

            response = await self.smtp_client.send_message(msg)

        except aiosmtplib.SMTPException as e:
            print(e)
            # Force reconnecting and checking state
            await self.smtp_client.quit()
            await self.smtp_client.connect()
            await self.smtp_client.login(self.login, self.password)
            if not self.smtp_client.is_connected:
                raise Exception("Could not connect to SMTP server")

            response = await self.smtp_client.send_message(msg)

        print(to, subject, response)

        return response

    async def send_from_template(
            self, to: str, subject: str, template_name: str, context: dict,
            default: str | None = None
    ) -> bool:
        """Send email to user with template.

        :return: Boolean status if message has been sent or not.
        """

        rendered_template = self.template_renderer.render(
            template_name=template_name, context=context
        )

        # Sending a message if template has been rendered
        if rendered_template:
            response = await self.send_mail_html(
                to=to, subject=subject, message_html=rendered_template,
                message_text=default
            )

            # Returning status of sent email msg - has it been sent to end-user or not
            response_status_text: str = response[1]
            return self.check_if_sent(response_status_text)

        return False

    @staticmethod
    def check_if_sent(response: str) -> bool:
        """Simple function to check if message has been sent

        By the server to the recipient, that's why 3xy and 4xy errors aren't included.
        """

        code = response.split(" ")[0].replace(".", "")

        if code.startswith("2"):
            return True
        return False
