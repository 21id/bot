from app.bot.filters.user_exists import UserExists
from app.bot.routers.user.registration.router import router
from app.bot.routers.user.registration.keyboards import (nickname_back as
                                                         nickname_back_kb)
from app.bot.routers.user.registration.callback import StartRegistration, ChangeNickname
from app.bot.routers.user.registration.states import RegistrationStates
from app.bot.filters.user_verified import UserVerified

from aiogram.types import CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext


# Prompting for nickname if user doesn't exist. If he is and isn't verified - move
# him to Email verification step
@router.callback_query(StateFilter(None), UserExists(exists=False),
                       StartRegistration.filter())
# If user wants to change nickname
@router.callback_query(StateFilter(RegistrationStates.verification,
                                   RegistrationStates.nickname),
                       UserVerified(verified=False), ChangeNickname.filter())
async def start(callback: CallbackQuery, state: FSMContext, callback_data:
    StartRegistration | None = None) -> None:
    """Registration start."""

    # Clearing state data if user came back from nickname verification
    if (await state.get_state()) == RegistrationStates.verification:
        # But not all data, data which is only used by verification - to not stop
        # join accept process
        await state.update_data(
            student=None, otp_code=None, attempts_count=None, max_attempts=None
        )

    # Setting state for nickname
    await state.set_state(RegistrationStates.nickname)

    # If callback data is provided and approve join flag is present - setting needed
    # parameters, to use in the end
    if isinstance(callback_data, StartRegistration) and callback_data.approve_join:
        chat_id = callback_data.join_chat_id
        chat_title = callback_data.join_chat_title
        await state.update_data(is_joining_chat=True, chat_id=chat_id,
                                chat_title=chat_title)
    # And if he isn't joining a chat - allow keyboard

    # If user is joining a chat via join request - do not give keyboard to get back
    if await state.get_value("is_joining_chat"):
        keyboard = None
    else:
        keyboard = nickname_back_kb.get()

    text = (
        "Firstly, send your School 21 nickname in shortened format (only 8 "
        "symbols or less, not full Name and Surname of login)\n"
        "ℹ️ For example:\ndaemonpr, kristana, lilliank\n\n"
        "⚠️ We apologize for any delays due to ping with School 21 API and Email "
        "server - you may need to wait around 10 seconds to get an answer."
    )

    await callback.message.edit_text(text, reply_markup=keyboard)
