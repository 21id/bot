from app.bot.routers.user.registration.router import router
from app.bot.routers.user.registration.callback import RegistrationMenu
from app.bot.routers.user.registration.keyboards import welcome as welcome_kb
from app.bot.routers.user.registration.states import RegistrationStates
from app.bot.utilities import reply_edit
from app.i18n.core import I18nContext

from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext


@router.message(StateFilter(None), CommandStart(), F.chat.type == "private")
@router.callback_query(StateFilter(None), RegistrationMenu.filter())
@router.callback_query(StateFilter(RegistrationStates.verification,
                                   RegistrationStates.nickname),
                       RegistrationMenu.filter())
async def welcome(
    request: Message | CallbackQuery, state: FSMContext, i18n: I18nContext
) -> None:
    """Welcome message."""
    if await state.get_state() in [RegistrationStates.verification,
                                   RegistrationStates.nickname]:
        # Preserve language across state clear
        lang = await state.get_value("language")
        await state.clear()
        if lang:
            await state.update_data(language=lang)

    text = i18n.get("welcome-text")
    keyboard = welcome_kb.get(i18n)

    await reply_edit.answer(request, text=text, reply_markup=keyboard)


@router.message(StateFilter(None), CommandStart())
async def welcome_in_group(message: Message, i18n: I18nContext) -> None:
    await message.answer(i18n.get("welcome-in-group-text"))
