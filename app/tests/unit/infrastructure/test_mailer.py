from unittest.mock import AsyncMock, MagicMock

from app.infrastructure.mailer.client import MailerClient

import aiosmtplib
import pytest
from aiosmtplib import SMTPResponse


def make_mailer(rendered: str = "<p>hi</p>", connected: bool = True):
    """Mailer with mocked SMTP client and renderer."""
    smtp = MagicMock()
    smtp.is_connected = connected
    smtp.send_message = AsyncMock(return_value=({}, "OK"))
    smtp.connect = AsyncMock()
    smtp.login = AsyncMock()
    smtp.quit = AsyncMock()
    renderer = MagicMock()
    renderer.render.return_value = rendered
    mailer = MailerClient(
        smtp_host="smtp.test",
        smtp_port=587,
        login="l",
        password="p",
        sender="21id@test",
        template_renderer=renderer,
        smtp_client=smtp,
    )
    return mailer, smtp


async def test_send_from_template_ok():
    mailer, smtp = make_mailer()
    assert (
        await mailer.send_from_template(
            to="jdoe@student.21-school.ru",
            subject="s",
            template_name="otp.html",
            context={"code": "1"},
        )
        is True
    )
    msg = smtp.send_message.await_args.args[0]
    assert msg["To"] == "jdoe@student.21-school.ru"
    assert msg["From"] == "21id@test"


async def test_rejected_recipient_returns_false():
    mailer, smtp = make_mailer()
    smtp.send_message.return_value = (
        {"jdoe@student.21-school.ru": SMTPResponse(550, "no such user")},
        "OK",
    )
    assert (
        await mailer.send_from_template(
            to="jdoe@student.21-school.ru",
            subject="s",
            template_name="t",
            context={},
        )
        is False
    )


async def test_empty_render_returns_false():
    mailer, smtp = make_mailer(rendered="")
    assert (
        await mailer.send_from_template(
            to="a@b.c", subject="s", template_name="t", context={}
        )
        is False
    )
    smtp.send_message.assert_not_awaited()


@pytest.mark.parametrize("to", ["a@b.c\r\nBcc: x@y.z", "a@b.c\nBcc: x@y.z", "a@b.c\r"])
async def test_crlf_in_recipient_rejected(to):
    mailer, smtp = make_mailer()
    with pytest.raises(ValueError):
        await mailer.send_mail_html(to=to, subject="s", message_html="<p/>")
    smtp.send_message.assert_not_awaited()


async def test_reconnects_and_resends_once_on_smtp_error():
    mailer, smtp = make_mailer()
    smtp.send_message.side_effect = [
        aiosmtplib.SMTPServerDisconnected("gone"),
        ({}, "OK"),
    ]
    await mailer.send_mail_html(to="a@b.c", subject="s", message_html="<p/>")
    assert smtp.send_message.await_count == 2
    smtp.connect.assert_awaited_once()
    smtp.login.assert_awaited_once_with("l", "p")


async def test_connects_when_disconnected():
    mailer, smtp = make_mailer()
    smtp.is_connected = False
    await mailer.send_mail_html(to="a@b.c", subject="s", message_html="<p/>")
    smtp.connect.assert_awaited_once()


def test_init_requires_connected_client():
    with pytest.raises(Exception, match="connect"):
        make_mailer(connected=False)
