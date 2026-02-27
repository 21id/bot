from os import getenv

from app.bootstrap import Container
from app.domain.user.user import User
from app.infrastructure.s21.v1.models.responses.student import ParticipantV1DTO
from app.bot.routers.user.registration.router import router
from app.bot.routers.user.registration.states import RegistrationStates
from app.bot.routers.user.registration.keyboards import (nickname_back as
                                                         nickname_back_kb)
from app.bot.routers.user.menu.keyboard import menu as menu_kb

from aiogram import F, Bot
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.methods import ApproveChatJoinRequest, DeclineChatJoinRequest


# Handling invalid OTP codes
@router.message(StateFilter(RegistrationStates.verification), ~F.text.isdigit() or
                F.text.len() != 6)
async def invalid_code(message: Message) -> None:
    """Notify that sent OTP code is invalid.

    It doesn't check if it's correct or not, only that it's 6 digits.
    """

    text = (
        "OTP Code above is invalid, please try to send it again: check that it's "
        "exactly 6 digits and nothing else (whitespaces and others).\n\n"
        "⚠️ For example: daemonpr, kristana, lilliank"
    )

    await message.reply(text)


@router.message(StateFilter(RegistrationStates.verification))
async def code_verification(message: Message, state: FSMContext,
                            container: Container, bot: Bot) -> None:
    """Validation of OTP code, stored in State context"""

    student_serialized: dict = await state.get_value("student")
    # Can raise and fail
    student = ParticipantV1DTO(**student_serialized)

    otp_code: str = await state.get_value("otp_code")
    attempts_count: int = int(await state.get_value("attempts_count"))
    max_attempts: int = int(await state.get_value("max_attempts"))
    response_otp_code: str = message.text

    # Trying to deserialize user object, and otherwise get it from database
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

    # Checking if code isn't correct
    if otp_code != response_otp_code:
        # Checking if current attempt is 10th or more
        # Otherwise, give opportunity to try again
        if attempts_count + 1 > max_attempts:
            text = (
                f"Dear {student.login}, you've used all your attempts to enter OTP "
                "code.\n\n🔄 You are required to restart your registration process "
                "and enter nickname again with /start"
            )

            is_joining_chat = await state.get_value("is_joining_chat")

            if is_joining_chat:
                text += (
                    "\n\n❌ Because you were joining a chat, your join request "
                    "will be canceled, and you will need to send it again"
                )

            await state.set_state(RegistrationStates.nickname)
            await state.set_data({})

            keyboard = nickname_back_kb.get(set_change_bt_flag=True)

            # Sending message, in case join request declining will raise an error
            await message.reply(text, reply_markup=keyboard)

            # Declining join request
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

            # Exiting, to exclude message duplication
            return
        else:
            text = (
                f"❌ Sent OTP code ({response_otp_code}) is invalid, please try again "
                f"(you have {max_attempts - attempts_count} attempts left to enter the "
                "right OTP code)"
            )

            # Update attempts count
            await state.update_data(attempts_count=(attempts_count + 1))
    else:
        # Checking if user has been joining a chat, when user is validating
        is_joining_chat: bool = await state.get_value("is_joining_chat")
        if is_joining_chat:
            # Getting chat information
            chat_id: int = int(await state.get_value("chat_id"))

            # Trying to accept and send message, otherwise - stop
            try:
                await bot(ApproveChatJoinRequest(chat_id=chat_id, user_id=user_tg_id))
            except Exception as e:
                local_text = (
                    f"⚠️ Got an error, while trying to accept your join request: {e}\n"
                    f"\nPlease, notify @megaplov if you haven't been accepted, "
                    f"and if you are - just ignore this message"
                )

                await message.answer(local_text)

            # Message to topic ID is sent on user join
            # from chat router (chat/join/join.py)

        # Trying to upsert, and if errors happen - notify user
        try:
            # If user exist - using user data, otherwise - dumping student data
            # from state
            if user_from_db:
                # Using existing student model
                user = user_from_db
                user.is_verified=True
                user.telegram_id=user_tg_id
            else:
                # Dumping student model
                user = User(
                    **student.model_dump(), is_verified=True, telegram_id=user_tg_id
                )

            if user:
                # Update or create user
                await container.user_service.upsert(user)
            else:
                # TODO: add error logging
                raise Exception("Error with retrieving and setting user data")

            try:
                # Notifying admin of new user
                local_text = (
                    f"NEW {user.nickname} ({user.wave_name}, {user.campus.short_name})"
                )
                # Adding notion that user is joining a chat when registering
                if is_joining_chat:
                    chat_title: str = await state.get_value("chat_title")
                    local_text += f" && joins {chat_title}"
                await bot.send_message(getenv("ADMIN_ID"), local_text)
            except:
                pass
        except Exception as e:
            # TODO: add error logging
            text = (
                f"❗️ Error has occurred on Database update\n\n"
                f"Message: {e}\n\n"
                "✍️ Please, notify @megaplov about this problem from your perspective"
            )
        else:
            text = (
                f"👋 Welcome to 21ID, {student.login}!\n\n🔽 Basic functionality that "
                "you may need is right below, which you can access in main menu with "
                "/start command\n\n🪪 To find other peers, please use inline mode. "
                "Guide on how to use 21ID Bot inline search is here: t.me/ident21/9"
            )

            keyboard = menu_kb.get()

            # Clearing state data if user has successfully join
            await state.clear()

    await message.reply(text, reply_markup=keyboard)