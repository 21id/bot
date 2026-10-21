import uuid
from datetime import UTC, datetime, timedelta

import sentry_sdk

from app.bootstrap import Container
from app.domain.user.user import User
from app.bot.routers.user.invite.router import router
from app.bot.routers.user.invite.callback import InviteStudent
from app.bot.i18n.core import I18nContext

from aiogram.types import CallbackQuery


@router.callback_query(InviteStudent.filter())
async def invite_student(  # noqa: C901
    callback: CallbackQuery,
    callback_data: InviteStudent,
    container: Container,
    i18n: I18nContext,
) -> None:
    """Send 21ID invitation email to School 21 student."""
    # Only verified users can invite
    invitee_user = await container.user_service.get_by_telegram_id(
        callback.from_user.id
    )
    if not invitee_user or not invitee_user.is_verified:
        await callback.answer(i18n.get("invite-not-verified"), show_alert=True)
        return

    login = callback_data.invited_login.lower()

    user = await container.user_service.get_by_nickname(login)
    invite_expired = bool(
        user
        and user.is_invited
        and user.invite_expires_at
        and user.invite_expires_at < datetime.now(UTC)
    )

    # Do not allow user to send multiple invitations
    if user and not invite_expired:
        await callback.answer(i18n.get("invite-already-exists"), show_alert=True)
        return

    rl_key = f"rl:invite:{callback.from_user.id}"
    if not await container.redis.set(rl_key, 1, nx=True, ex=60):
        seconds = await container.redis.ttl(rl_key)
        await callback.answer(
            i18n.get("rate-limited", seconds=seconds), show_alert=True
        )
        return

    rl_login_key = f"rl:invite-login:{login}"
    if not await container.redis.set(rl_login_key, 1, nx=True, ex=86400):
        seconds = await container.redis.ttl(rl_login_key)
        await callback.answer(
            i18n.get("rate-limited", seconds=seconds), show_alert=True
        )
        return

    student = await container.s21api_client.get_student_by_nickname(login)

    # If student is present in School 21 API but not already registered
    if not student:
        await callback.answer(
            i18n.get("invite-failed", nickname=login), show_alert=True
        )
        return

    invite_otp: str = uuid.uuid4().hex

    student_email = f"{student.login}@student.21-school.ru"
    subject = "21ID Invitation"
    context = {
        "username": student.login,
        "verification_code": invite_otp,
        "invitee_nickname": invitee_user.nickname,
    }

    try:
        message_status = await container.mail_client.send_from_template(
            to=student_email,
            subject=subject,
            template_name="invite.html",
            context=context,
        )
    except Exception as e:
        sentry_sdk.capture_exception(e)
        message_status = False

    if not message_status:
        await callback.answer(
            i18n.get("invite-failed", nickname=student.login), show_alert=True
        )
        return

    # Trying to upsert user
    try:
        if user:
            # Re-invite after previous invite expired
            user.invite_otp = invite_otp
        else:
            user = User(
                **student.model_dump(),
                is_verified=False,
                telegram_id=None,
                invite_otp=invite_otp,
            )
        user.invite_expires_at = datetime.now(UTC) + timedelta(days=7)

        # Update or create user
        await container.user_service.upsert(user)
    except Exception as e:
        # If user adding fails - change message
        sentry_sdk.capture_exception(e)
        await callback.answer(
            i18n.get("invite-failed", nickname=student.login), show_alert=True
        )
        return

    await callback.answer(
        i18n.get("invite-sent", nickname=student.login), show_alert=True
    )
