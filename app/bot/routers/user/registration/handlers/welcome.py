from app.bot.routers.user.registration.router import router
from app.bot.routers.user.registration.callback import RegistrationMenu
from app.bot.routers.user.registration.keyboards import welcome as welcome_kb
from app.bot.routers.user.registration.states import RegistrationStates
from app.bot.utilities import reply_edit

from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext


@router.message(StateFilter(None), CommandStart(), F.chat.type == "private")
@router.callback_query(StateFilter(None), RegistrationMenu.filter())
# If user wants to get back
@router.callback_query(StateFilter(RegistrationStates.verification,
                                   RegistrationStates.nickname),
                       RegistrationMenu.filter())
async def welcome(request: Message | CallbackQuery, state: FSMContext) -> None:
    """Welcome message."""

    # Clearing state if user came back from nickname verification or prompt
    if await state.get_state() in [RegistrationStates.verification,
                                   RegistrationStates.nickname]:
        await state.clear()

    text = (
        f"👋 Welcome to 21ID! \n\nThis bot will help you issue your 21ID Card, "
        "join communities, and a lot more."
        "\n\nTo do that you will need:"
        "\n- your School 21 Platform nickname (login)"
        "\n- access to your email, which you have used in Applicant"
        "\n\nWhole process takes less than 3 minutes and is fully free - so use "
        "button below to start"
    )

    keyboard = welcome_kb.get()

    await reply_edit.answer(request, text=text, reply_markup=keyboard)


@router.message(StateFilter(None), CommandStart())
async def welcome_in_group(message: Message) -> None:
    text = (
        f"👋 Welcome to 21ID! \n\nThis bot will help you issue your 21ID Card, "
        "join communities, and a lot more."
        "\n\nWhole process takes less than 3 minutes and is fully free."
        "\n\n🔒 But to keep your information private - please, continue in private "
        "messages -> @id_21bot "
    )

    await message.answer(text)