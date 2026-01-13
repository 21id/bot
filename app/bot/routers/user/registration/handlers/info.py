from app.bot.routers.user.registration.router import router
from app.bot.routers.user.registration.callback import GetDetails
from app.bot.routers.user.registration.keyboards import info as info_kb

from aiogram.types import CallbackQuery
from aiogram.filters import StateFilter


@router.callback_query(StateFilter(None), GetDetails.filter())
async def info(callback: CallbackQuery) -> None:
    """Information page."""

    text = (
        "🪪 21ID is an identification system for School 21 students, which helps to...\n"
        "\n- Find peers' from yours and other campuses, and notify them via Telegram "
        "and email"
        "\n- Using your School 21 account to sign in to external services)"
        "\n\n❓ If you want to contribute or ask questions about "
        "development - please visit https://github.com/21id/bot\n\nMade with ❤️ from "
        "SKD & TAS by daemonpr (@megaplov)"
    )

    keyboard = info_kb.get()

    await callback.message.edit_text(text, reply_markup=keyboard)
