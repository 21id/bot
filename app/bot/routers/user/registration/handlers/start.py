from app.bot.filters.user_exists import UserExists
from app.bot.routers.user.registration.router import router
from app.bot.routers.user.registration.keyboards import (nickname_back as
                                                         nickname_back_kb)
from app.bot.routers.user.registration.callback import StartRegistration, ChangeNickname
from app.bot.routers.user.registration.states import RegistrationStates
from app.bot.filters.user_verified import UserVerified
from app.i18n.core import I18nContext

from aiogram.types import CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext


@router.callback_query(StateFilter(None), UserExists(exists=False),
                       StartRegistration.filter())
@router.callback_query(StateFilter(RegistrationStates.verification,
                                   RegistrationStates.nickname),
                       UserVerified(verified=False), ChangeNickname.filter())
async def start(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: I18nContext,
    callback_data: StartRegistration | None = None,
) -> None:
    """Registration start."""
    if (await state.get_state()) == RegistrationStates.verification:
        await state.update_data(
            student=None, otp_code=None, attempts_count=None, max_attempts=None
        )

    await state.set_state(RegistrationStates.nickname)

    if isinstance(callback_data, StartRegistration) and callback_data.approve_join:
        chat_id = callback_data.join_chat_id
        chat_title = callback_data.join_chat_title
        await state.update_data(is_joining_chat=True, chat_id=chat_id,
                                chat_title=chat_title)
        keyboard = None
    else:
        keyboard = nickname_back_kb.get(i18n)

    text = i18n.get("start-nickname-prompt")

    await callback.message.edit_text(text, reply_markup=keyboard)
