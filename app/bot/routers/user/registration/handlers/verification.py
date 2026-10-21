import sentry_sdk

from app.bootstrap import Container
from app.domain.user.user import User
from app.domain.verification.method import VerificationMethod
from app.infrastructure.s21.v1.models.responses.student import ParticipantV1DTO
from app.bot.routers.user.registration.router import router
from app.bot.routers.user.registration.states import RegistrationStates
from app.bot.routers.user.registration.keyboards import (
    nickname_back as nickname_back_kb,
)
from app.bot.routers.user.menu.keyboard import menu as menu_kb
from app.bot.i18n.core import I18nContext

from aiogram import F, Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.methods import ApproveChatJoinRequest, DeclineChatJoinRequest


@router.message(
    StateFilter(RegistrationStates.verification), ~F.text.regexp(r"^\d{6}\Z")
)
async def invalid_code(message: Message, i18n: I18nContext) -> None:
    """Notify that sent OTP code is invalid format."""
    await message.reply(i18n.get("verification-invalid-format"))


@router.message(StateFilter(RegistrationStates.verification))
async def code_verification(  # noqa: C901
    message: Message,
    state: FSMContext,
    container: Container,
    bot: Bot,
    i18n: I18nContext,
) -> None:
    """Validation of OTP code stored in State context."""
    student_serialized: dict = await state.get_value("student")
    student = ParticipantV1DTO(**student_serialized)

    response_otp_code: str = message.text

    try:
        user_from_db_serialized: dict = await state.get_value("user")
        if user_from_db_serialized:
            user_from_db = User(**user_from_db_serialized)
        else:
            user_from_db = None
    except Exception as e:
        sentry_sdk.capture_exception(e)
        user_from_db = await container.user_service.get_by_telegram_id(
            message.from_user.id
        )

    user_tg_id = message.from_user.id
    keyboard = None

    result = await container.verification_service.check(
        VerificationMethod.EMAIL_OTP, str(user_tg_id), response_otp_code
    )

    if not result or not result.passed:
        # Missing challenge (expired) is treated as exhausted
        if not result or result.remaining < 0:
            text = i18n.get("verification-exhausted", nickname=student.login)

            is_joining_chat = await state.get_value("is_joining_chat")
            if is_joining_chat:
                text += i18n.get("verification-exhausted-join-extra")
                chat_id: int = int(await state.get_value("chat_id"))

            await state.set_state(RegistrationStates.nickname)
            await state.set_data({})

            keyboard = nickname_back_kb.get(i18n, set_change_bt_flag=True)

            await message.reply(text, reply_markup=keyboard)

            if is_joining_chat:
                try:
                    await bot(
                        DeclineChatJoinRequest(chat_id=chat_id, user_id=user_tg_id)
                    )
                except TelegramAPIError as e:
                    sentry_sdk.capture_exception(e)

            return
        else:
            text = i18n.get(
                "verification-wrong-code",
                code=response_otp_code,
                remaining=result.remaining,
            )
    else:
        if await container.user_service.telegram_id_taken(
            user_tg_id,
            exclude_user_id=str(user_from_db.id) if user_from_db else None,
        ):
            await state.clear()
            await message.reply(i18n.get("join-invite-already-registered"))
            return

        verified_owner = await container.user_service.get_by_nickname(student.login)
        if (
            verified_owner
            and verified_owner.is_verified
            and verified_owner.telegram_id != user_tg_id
        ):
            await state.clear()
            await message.reply(
                i18n.get("verification-nickname-taken", nickname=student.login)
            )
            return

        is_joining_chat: bool = await state.get_value("is_joining_chat")
        if is_joining_chat:
            chat_id: int = int(await state.get_value("chat_id"))
            try:
                await bot(ApproveChatJoinRequest(chat_id=chat_id, user_id=user_tg_id))
            except TelegramAPIError as e:
                sentry_sdk.capture_exception(e)
                local_text = i18n.get("verification-join-error")
                await message.answer(local_text)

        if user_from_db:
            user = user_from_db
        else:
            user = User(
                **student.model_dump(), is_verified=True, telegram_id=user_tg_id
            )

        # DuplicateUserError propagates to ErrorMiddleware (shows client_message)
        await container.verification_service.complete(
            user, VerificationMethod.EMAIL_OTP, user_tg_id
        )

        try:
            campus = user.campus.short_name if user.campus else "-"
            local_text = f"NEW {user.nickname} ({user.wave_name}, {campus})"
            if is_joining_chat:
                chat_title: str = await state.get_value("chat_title")
                local_text += f" && joins {chat_title}"
            await bot.send_message(container.admin_id, local_text)
        except TelegramAPIError as e:
            sentry_sdk.capture_exception(e)

        text = i18n.get("verification-success", nickname=student.login)
        keyboard = menu_kb.get(i18n)
        await state.clear()

    await message.reply(text, reply_markup=keyboard)
