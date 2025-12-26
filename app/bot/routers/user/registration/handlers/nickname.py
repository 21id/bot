from app.bot.filters.user_exists import UserExists
from app.domain.user.status import StudentStatus
from app.utilities import random
from app.bootstrap import Container
from app.infrastructure.s21.v1.models.responses.error import ErrorResponseDTO
from app.infrastructure.s21.v1.models.responses.student import ParticipantV1DTO
from app.bot.utilities import reply_edit
from app.bot.filters.user_verified import UserVerified
from app.bot.routers.user.registration.router import router
from app.bot.routers.user.registration.states import RegistrationStates
from app.bot.routers.user.registration.callback import StartRegistration
from app.bot.routers.user.registration.keyboards import (nickname_back as
                                                         nickname_back_kb)

from aiogram import F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.methods import DeclineChatJoinRequest


@router.message(~F.text.isalpha() or F.text.len() > 8,
                StateFilter(RegistrationStates.nickname))
async def invalid_nickname(message: Message) -> None:
    """Notify that sent nickname is invalid."""

    text = (
        "Nickname above is invalid, please try to send it again (in shortened "
        "format): only latin symbols, length of 8 or less\n\n"
        "⚠️ For example: daemonpr, kristana, lilliank"
    )

    await message.reply(text)

# Opportunity to register for unverified student in database
@router.callback_query(StateFilter(None), StartRegistration.filter(),
                       UserExists(exists=True) and UserVerified(verified=False))
@router.message(F.text.isalpha(), StateFilter(RegistrationStates.nickname))
async def nickname(request: Message | CallbackQuery, state: FSMContext,
                   container: Container, bot: Bot) -> None:
    """Verification of nickname via email."""

    # Setting Default keyboard, which can be changed if needed
    keyboard = nickname_back_kb.get()

    # Getting current user Telegram ID
    user_tg_id = request.from_user.id

    # If current request is message - we get nickname from it
    if isinstance(request, Message):
        nickname_ = request.text
        user = await container.user_service.get_by_nickname(nickname_)
    # Otherwise - see if user is in the database
    else:
        user = await container.user_service.get_by_telegram_id(user_tg_id)
        nickname_ = user.nickname

    # If user is present in database
    if user:
        # Check if current user is registered under this, and updating state data
        if user.telegram_id == user_tg_id or user.telegram_id is None:
            await state.update_data(user=user.model_dump(mode="json"))
        # But if user has other Telegram ID - deny entry
        else:
            text = (
                f"⚠️ Dear user, {user.nickname} is registered under other "
                f"Telegram account.\n\nIf you please to move it to your current account"
                " - please, contact @megaplov\n\nℹ️ If that's not you, "
                "please - send your School 21 student nickname again"
            )

            await reply_edit.answer(request, text=text, reply_markup=keyboard)
            return

    # Getting / updating student info from School 21 API
    student = await container.s21api_client.get_student_by_nickname(nickname_)

    # Handling BLOCKED student error
    if student.status == StudentStatus.BLOCKED:
        raise Exception(
            "21ID can't work with BLOCKED students on School 21 Platform. If you "
            "believe this is a mistake (which could happen) - please contact @megaplov"
        )

    # If error has occurred on request to database, and student isn't none or found
    if (isinstance(student, ErrorResponseDTO) or
            (not isinstance(student, ParticipantV1DTO) and not student is None)):
        raise Exception(f"Couldn't retrieve student data, response: {student}")

    # If student has been found in API
    if student:
        user_id = request.from_user.id

        # If user is joining a chat - check if he can be accepted there
        if await state.get_value("is_joining_chat"):
            chat_id = await state.get_value("chat_id")
            chat_title = await state.get_value("chat_title")
            chat = await container.chat_service.get_by_telegram_id(chat_id)

            # If user can't be accepted due to chat settings - deny his join request,
            # but anyway move further
            # Important: using student object, because user may be undefined
            acceptance_requirements = (
                    (student.parallelName != "Core program" and chat.core_allowed) or
                    (student.parallelName == "Core program" and chat.intensive_allowed)
            )

            if not acceptance_requirements:
                try:
                    await bot(DeclineChatJoinRequest(chat_id=chat_id, user_id=user_id))
                except:
                    pass

                text = (
                    f"⚠️ Dear {user.nickname}!\n\nYou're denied from joining"
                    f" '{chat.chat_title}' based on chat join policy:\n"
                    f"Intensive allowed: {"✅" if chat.intensive_allowed else '❌'}\n"
                    f"Core allowed: {"✅" if chat.core_allowed else '❌'}\n\nIf you "
                    "think that it's wrong denial - please, contact @megaplov\n\n"
                    "- - - - - \n\n🪪 But you are more than welcome to join 21ID "
                    f" - just without joining {chat_title}. For that, follow "
                    "the instructions below"
                )

                await state.update_data(is_joining_chat=False, chat_id=None,
                                        chat_title=None)

                await reply_edit.answer(request, text=text)

        # But anyway moving user to OTP step
        student_email = f"{nickname_}@student.21-school.ru"

        # Setting student data
        student_data = student.model_dump(mode="json")
        if student_data:
            await state.update_data(
                student=student.model_dump(mode="json")
            )
        else:
            raise Exception("Can't serialize student data")

        text = (
            f"Thanks!\n📩 Now you need to verify that you are indeed {nickname_}\n"
            "\nFor that, I've sent you a one-time 6 digits code to your mail (to "
            f"{student_email}, which will be forwarded to your Personal Email), "
            "which you need to send me in a message, or use a link inside message\n\n"
            "⚠️ Please, check your spam folder, as email can land there.\n\nIf "
            "you want to change nickname - use button below"
        )

        # Generating OTP and sending an email to student's School 21 provided email
        otp_code: str = random.generate_secure_otp()

        email_subject = f"[{otp_code}] 21ID OTP Code"
        email_context = {"username": nickname_, "code": otp_code}

        # Try to send an email, and if it fails - notify user to retry

        try:
            is_email_sent = await container.mail_client.send_from_template(
                to=student_email, subject=email_subject, template_name="otp.html",
                context=email_context
            )
        except Exception as e:
            # TODO: add error logging
            text = (
                f"❗️ Error has occurred on Mail send\n\n"
                f"Message: {e}\n\n"
                "✍️ Please, notify @megaplov about this problem from your perspective"
            )

            await reply_edit.answer(request, text=text)
            return

        if not is_email_sent:
            text = (
                f"⚠️ Dear {user.nickname}, there was a problem with your "
                "OTP code - it can't reach your mailbox. We are very sorry for "
                "the inconvenience.\n\nℹ️ Try again by sending your nickname, and "
                "if you still can't get it - contact @megaplov"
            )

            await reply_edit.answer(request, text=text, reply_markup=keyboard)
            return
        else:
            # Updating states and saving student data for later
            await state.set_state(RegistrationStates.verification)
            await state.update_data(otp_code=otp_code, attempts_count=0,
                                    max_attempts=10)

        # Getting keyboard with "Change nickname" button
        keyboard = nickname_back_kb.get(set_change_bt_flag=True)

    # If not - prompting to resend nickname (in case user sent his nickname by hand)
    elif isinstance(request, Message):
        text = (
            f"I couldn't find you, {nickname_}!\n\n⚠️ Please, check that sent nickname "
            "is correct\n\nExamples:\ndaemonpr, kristana, lilliank"
        )

    # Otherwise - this means that there is a typo in database
    else:
        await state.set_state(RegistrationStates.nickname)

        text = (
            f"⚠️ I've detected you as {nickname_} from my database scan, but I can't "
            "find you on Platform.\n\nPlease, provide your School 21 nickname in "
            "shortened format (only 8 symbols or less, not full Name and Surname "
            "of login)"
        )

    await reply_edit.answer(request, text=text, reply_markup=keyboard)
