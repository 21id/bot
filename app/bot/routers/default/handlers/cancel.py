from app.bot.routers.default.router import router
from app.bot.i18n.core import I18nContext

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import StateFilter, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.methods import DeclineChatJoinRequest


@router.message(StateFilter(None), Command(commands=["cancel"]))
async def cancel_nothing(message: Message, i18n: I18nContext) -> None:
    """Handle requests, that should cancel state info, but there is none."""
    text = i18n.get("cancel-nothing")

    await message.reply(text)


@router.message(StateFilter("*"), Command(commands=["cancel"]))
async def cancel(
    message: Message, state: FSMContext, bot: Bot, i18n: I18nContext
) -> None:
    """Handle requests, that should cancel state info."""
    text = i18n.get("cancel-success")

    # Checking if user has been joining a chat, when canceling his state
    if await state.get_value("is_joining_chat"):
        chat_id = await state.get_value("chat_id")
        user_id = message.from_user.id
        try:
            await bot(DeclineChatJoinRequest(chat_id=chat_id, user_id=user_id))
        except TelegramAPIError:
            # Join request may be already processed or expired
            pass

        text += i18n.get("cancel-join-extra")

    # Clearing FSM data
    await state.clear()

    await message.reply(text)
