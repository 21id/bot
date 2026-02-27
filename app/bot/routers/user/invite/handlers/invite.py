import uuid

from app.bootstrap import Container
from app.domain.user.user import User
from app.bot.routers.user.invite.router import router
from app.bot.routers.user.invite.callback import InviteStudent

from aiogram.types import CallbackQuery


@router.callback_query(InviteStudent.filter())
async def invite_student(callback: CallbackQuery, callback_data: InviteStudent,
                         container: Container):
    student = await container.s21api_client.get_student_by_nickname(
        callback_data.invited_login)

    user = await container.user_service.get_by_nickname(callback_data.invited_login)

    # If student is present in School 21 API but not already registered
    if student and not user:
        # Getting invitee user
        invitee_user = await container.user_service.get_by_telegram_id(
            callback.from_user.id)
        if invitee_user:
            invitee_nickname = invitee_user.nickname
        else:
            fullname = f"{callback.from_user.last_name} {callback.from_user.first_name}"
            username = callback.from_user.username
            invitee_nickname = username or fullname

        invite_otp: str = uuid.uuid4().hex

        student_email = f"{student.login}@student.21-school.ru"
        subject = "21ID Invitation"
        context = {
            "username": student.login, "verification_code": invite_otp,
            "invitee_nickname": invitee_nickname
        }

        try:
            message_status = await container.mail_client.send_from_template(
                to=student_email, subject=subject, template_name="invite.html",
                context=context
            )
        except Exception as e:
            # TODO: add error logging
            text = (
                f"❗️ Error has occurred on Mail send\n\n"
                f"Message: {e}\n\n"
                "✍️ Please, notify @megaplov about this problem from your perspective"
            )

            await callback.answer(text)
            return

        if message_status:
            text = f"Successfully sent invite message to {student.login}."
            await callback.answer(text, show_alert=True)
        else:
            text = f"Sending invite to {student.login} failed, please try again later."
            await callback.answer(text, show_alert=True)
            return

        # Trying to upsert user
        try:
            user = User(**student.model_dump(), is_verified=False, telegram_id=None,
                        invite_otp=invite_otp)

            # Update or create user
            await container.user_service.upsert(user)
        except Exception:
            # If user adding fails - change message
            text = (
                f"Sending invite to {student.login} failed, please try again later."
            )
            await callback.answer(text, show_alert=True)
            return

    # Do not allow user to send multiple invitations
    elif user:
        text = "This user was already invited or exists."
        await callback.answer(text, show_alert=True)


    await callback.answer()