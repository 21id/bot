from os import getenv

from app.bootstrap import Container
from app.domain.user.user import User
from app.infrastructure.s21.v1.models.responses.student import ParticipantV1DTO
from app.bot.routers.user.registration.router import router
from app.bot.routers.user.registration.states import RegistrationStates
from app.bot.routers.user.registration.keyboards import (nickname_back as
                                                         nickname_back_kb)
from app.bot.routers.user.menu.keyboard import menu as menu_kb
from app.i18n.core import I18nContext

from aiogram import F, Bot
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.methods import ApproveChatJoinRequest, DeclineChatJoinRequest


@router.message(StateFilter(RegistrationStates.verification), ~F.text.isdigit() or
                F.text.len() != 6)
async def invalid_code(message: Message, i18n: I18nContext) -> None:
    """Notify that sent OTP code is invalid format."""
    await message.reply(i18n.get("verification-invalid-format"))


@router.message(StateFilter(RegistrationStates.verification))
async def code_verification(
    message: Message, state: FSMContext, container: Container, bot: Bot,
    i18n: I18nContext,
) -> None:
    """Validation of OTP code stored in State context."""
    student_serialized: dict = await state.get_value("student")
    student = ParticipantV1DTO(**student_serialized)

    otp_code: str = await state.get_value("otp_code")
    attempts_count: int = int(await state.get_value("attempts_count"))
    max_attempts: int = int(await state.get_value("max_attempts"))
    response_otp_code: str = message.text

    try:
        user_from_db_serialized: dict = await state.get_value("user")
        if user_from_db_serialized:
            user_from_db = User(**user_from_db_serialized)
        else:
            user_from_db = None
    except:
        user_from_db = await container.user_service.get_by_telegram_id(
            message.from_user.id)

    user_tg_id = message.from_user.id
    keyboard = None

    if otp_code != response_otp_code:
        if attempts_count + 1 > max_attempts:
            text = i18n.get("verification-exhausted", nickname=student.login)

            is_joining_chat = await state.get_value("is_joining_chat")
            if is_joining_chat:
                text += i18n.get("verification-exhausted-join-extra")

            await state.set_state(RegistrationStates.nickname)
            await state.set_data({})

            keyboard = nickname_back_kb.get(i18n, set_change_bt_flag=True)

            await message.reply(text, reply_markup=keyboard)

            if is_joining_chat:
                chat_id: int = int(await state.get_value("chat_id"))
                try:
                    await bot(
                        DeclineChatJoinRequest(chat_id=chat_id, user_id=user_tg_id)
                    )
                except Exception as e:
                    raise Exception(
                        f"Got an error while trying to decline join request: {e}"
                    )

            return
        else:
            text = i18n.get(
                "verification-wrong-code",
                code=response_otp_code,
                remaining=max_attempts - attempts_count,
            )
            await state.update_data(attempts_count=(attempts_count + 1))
    else:
        is_joining_chat: bool = await state.get_value("is_joining_chat")
        if is_joining_chat:
            chat_id: int = int(await state.get_value("chat_id"))
            try:
                await bot(ApproveChatJoinRequest(chat_id=chat_id, user_id=user_tg_id))
            except Exception as e:
                local_text = i18n.get("verification-join-error", error=e)
                await message.answer(local_text)

        try:
            if user_from_db:
                user = user_from_db
                user.is_verified = True
                user.telegram_id = user_tg_id
            else:
                user = User(
                    **student.model_dump(), is_verified=True, telegram_id=user_tg_id
                )

            if user:
                await container.user_service.upsert(user)
            else:
                raise Exception("Error with retrieving and setting user data")

            try:
                local_text = (
                    f"NEW {user.nickname} ({user.wave_name}, {user.campus.short_name})"
                )
                if is_joining_chat:
                    chat_title: str = await state.get_value("chat_title")
                    local_text += f" && joins {chat_title}"
                await bot.send_message(getenv("ADMIN_ID"), local_text)
            except:
                pass
        except Exception as e:
            text = i18n.get("verification-db-error", error=e)
        else:
            text = i18n.get("verification-success", nickname=student.login)
            keyboard = menu_kb.get(i18n)
            await state.clear()

    await message.reply(text, reply_markup=keyboard)
