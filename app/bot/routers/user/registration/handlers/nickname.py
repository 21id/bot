import sentry_sdk

from app.bot.filters.user_exists import UserExists
from app.domain.user.status import StudentStatus
from app.bootstrap import Container
from app.domain.verification.method import VerificationMethod
from app.infrastructure.s21.v1.models.responses.error import ErrorResponseDTO
from app.infrastructure.s21.v1.models.responses.student import ParticipantV1DTO
from app.bot.utilities import reply_edit
from app.bot.filters.user_verified import UserVerified
from app.bot.routers.user.registration.router import router
from app.bot.routers.user.registration.states import RegistrationStates
from app.bot.routers.user.registration.callback import StartRegistration
from app.bot.routers.user.registration.keyboards import (
    nickname_back as nickname_back_kb,
    migration_otp_kb,
)
from app.bot.i18n.core import I18nContext

from aiogram import F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter, and_f
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.context import FSMContext
from aiogram.methods import DeclineChatJoinRequest
from aiogram.enums import ParseMode


@router.message(
    ~F.text.regexp(r"^[A-Za-z]{1,8}\Z"), StateFilter(RegistrationStates.nickname)
)
async def invalid_nickname(message: Message, i18n: I18nContext) -> None:
    """Notify that sent nickname is invalid."""
    await message.reply(i18n.get("nickname-invalid"))


@router.callback_query(
    StateFilter(None),
    StartRegistration.filter(),
    and_f(UserExists(exists=True), UserVerified(verified=False)),
)
@router.message(
    F.text.regexp(r"^[A-Za-z]{1,8}\Z"), StateFilter(RegistrationStates.nickname)
)
async def nickname(  # noqa: C901
    request: Message | CallbackQuery,
    state: FSMContext,
    container: Container,
    bot: Bot,
    i18n: I18nContext,
    callback_data: StartRegistration | None = None,
) -> None:
    """Verification of nickname via email."""
    keyboard = nickname_back_kb.get(i18n)

    if callback_data and callback_data.approve_join:
        chat_id = callback_data.join_chat_id
        chat_title = callback_data.join_chat_title
        await state.update_data(
            is_joining_chat=True, chat_id=chat_id, chat_title=chat_title
        )

    user_tg_id = request.from_user.id

    if isinstance(request, Message):
        nickname_ = request.text.lower()
        user = await container.user_service.get_by_nickname(nickname_)
    else:
        user = await container.user_service.get_by_telegram_id(user_tg_id)
        if not user or not user.nickname:
            raise Exception("User for your account exists, but doesn't have a nickname")
        nickname_ = user.nickname

    if user:
        if user.telegram_id == user_tg_id or user.telegram_id is None:
            await state.update_data(user=user.model_dump(mode="json"))
        else:
            migration_subject = f"{user.id}:{user_tg_id}"
            existing_attempt = await container.verification_service.get(
                VerificationMethod.MIGRATION_OTP, migration_subject
            )
            if existing_attempt:
                await state.update_data(
                    migration_original_nickname=nickname_,
                    migration_original_user_id=str(user.id),
                )
                await state.set_state(RegistrationStates.migration_otp)
                text = i18n.get("nickname-resume-migration", nickname=nickname_)
                await reply_edit.answer(
                    request, text=text, reply_markup=migration_otp_kb.get(i18n)
                )
                return

            rl_key = f"rl:migr:{user.id}"
            if not await container.redis.set(rl_key, 1, nx=True, ex=900):
                seconds = await container.redis.ttl(rl_key)
                text = i18n.get("rate-limited", seconds=seconds)
                await reply_edit.answer(request, text=text, reply_markup=keyboard)
                return

            challenge = await container.verification_service.start(
                VerificationMethod.MIGRATION_OTP, migration_subject, nickname_
            )
            otp = challenge["code"]
            original_email = f"{nickname_}@student.21-school.ru"

            tg_sent = False
            try:
                otp_message = i18n.get(
                    "nickname-migration-otp-spoiler-msg", nickname=nickname_, otp=otp
                )
                await bot.send_message(
                    user.telegram_id, otp_message, parse_mode=ParseMode.HTML
                )
                tg_sent = True
            except TelegramAPIError:
                pass

            if tg_sent:
                text = i18n.get("nickname-otp-prompt", nickname=nickname_)
            else:
                # Telegram unreachable — fall back to email automatically
                email_subject = f"[{otp}] 21ID Migration OTP Code"
                email_context = {"username": nickname_, "code": otp}
                try:
                    is_email_sent = await container.mail_client.send_from_template(
                        to=original_email,
                        subject=email_subject,
                        template_name="otp.html",
                        context=email_context,
                    )
                except Exception as e:
                    sentry_sdk.capture_exception(e)
                    is_email_sent = False
                if not is_email_sent:
                    await container.verification_service.cancel(
                        VerificationMethod.MIGRATION_OTP, migration_subject
                    )
                    text = i18n.get(
                        "nickname-other-account-blocked", nickname=nickname_
                    )
                    await reply_edit.answer(request, text=text, reply_markup=keyboard)
                    return
                text = i18n.get(
                    "nickname-migration-otp-via-email-fallback",
                    nickname=nickname_,
                    email=original_email,
                )

            await state.update_data(
                migration_original_nickname=nickname_,
                migration_original_user_id=str(user.id),
            )
            await state.set_state(RegistrationStates.migration_otp)

            await reply_edit.answer(
                request, text=text, reply_markup=migration_otp_kb.get(i18n)
            )
            return

    student = await container.s21api_client.get_student_by_nickname(nickname_)

    if isinstance(student, ErrorResponseDTO) or (
        not isinstance(student, ParticipantV1DTO) and student is not None
    ):
        raise Exception(f"Couldn't retrieve student data, response: {student}")

    if student:
        if student.status == StudentStatus.BLOCKED:
            raise Exception(
                "21ID can't work with BLOCKED students on School 21 Platform. If you "
                "believe this is a mistake (which could happen) - please contact "
                "@megaplov"
            )

        user_id = request.from_user.id

        if await state.get_value("is_joining_chat"):
            chat_id = await state.get_value("chat_id")
            chat_title = await state.get_value("chat_title")
            chat = await container.chat_service.get_by_telegram_id(chat_id)

            if chat is None:
                try:
                    await bot(DeclineChatJoinRequest(chat_id=chat_id, user_id=user_id))
                except TelegramAPIError as e:
                    sentry_sdk.capture_exception(e)

                text = i18n.get("chat-not-configured", chat_title=chat_title)
                await state.update_data(
                    is_joining_chat=False, chat_id=None, chat_title=None
                )
                await reply_edit.answer(request, text=text, answer_=True)
                acceptance_requirements = True
            else:
                acceptance_requirements = (
                    student.parallelName == "Core program" and chat.core_allowed
                ) or (student.parallelName != "Core program" and chat.intensive_allowed)

            if not acceptance_requirements:
                try:
                    await bot(DeclineChatJoinRequest(chat_id=chat_id, user_id=user_id))
                except TelegramAPIError as e:
                    sentry_sdk.capture_exception(e)

                intensive = "✅" if chat.intensive_allowed else "❌"
                core = "✅" if chat.core_allowed else "❌"
                text = i18n.get(
                    "nickname-chat-denied",
                    nickname=nickname_,
                    chat_title=chat_title,
                    intensive=intensive,
                    core=core,
                )

                await state.update_data(
                    is_joining_chat=False, chat_id=None, chat_title=None
                )
                await reply_edit.answer(request, text=text, answer_=True)

        student_email = f"{nickname_}@student.21-school.ru"

        student_data = student.model_dump(mode="json")
        if student_data:
            await state.update_data(student=student.model_dump(mode="json"))
        else:
            raise Exception("Can't serialize student data")

        text = i18n.get("nickname-otp-sent", nickname=nickname_, email=student_email)

        rl_key = f"rl:otp:{user_id}"
        if not await container.redis.set(rl_key, 1, nx=True, ex=60):
            seconds = await container.redis.ttl(rl_key)
            text = i18n.get("rate-limited", seconds=seconds)
            await reply_edit.answer(request, text=text, reply_markup=keyboard)
            return

        rl_nick_key = f"rl:otp-nick:{nickname_}"
        nick_count = await container.redis.incr(rl_nick_key)
        if nick_count == 1:
            await container.redis.expire(rl_nick_key, 3600)
        if nick_count > 5:
            seconds = await container.redis.ttl(rl_nick_key)
            text = i18n.get("rate-limited", seconds=seconds)
            await reply_edit.answer(request, text=text, reply_markup=keyboard)
            return

        try:
            is_email_sent = (
                await container.verification_service.start(
                    VerificationMethod.EMAIL_OTP, str(user_id), nickname_
                )
                is not None
            )
        except Exception as e:
            sentry_sdk.capture_exception(e)
            text = i18n.get("nickname-email-error")
            await reply_edit.answer(request, text=text)
            return

        if not is_email_sent:
            text = i18n.get("nickname-email-unreachable", nickname=nickname_)
            await reply_edit.answer(request, text=text, reply_markup=keyboard)
            return
        else:
            await state.set_state(RegistrationStates.verification)

        keyboard = nickname_back_kb.get(i18n, set_change_bt_flag=True)

    elif isinstance(request, Message):
        text = i18n.get("nickname-not-found", nickname=nickname_)

    else:
        await state.set_state(RegistrationStates.nickname)
        text = i18n.get("nickname-db-typo", nickname=nickname_)

    await reply_edit.answer(request, text=text, reply_markup=keyboard)
