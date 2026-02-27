from app.bot.routers.default.router import router

from aiogram import Bot
from aiogram.filters import StateFilter, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.methods import DeclineChatJoinRequest


@router.message(StateFilter(None), Command(commands=["cancel"]))
async def cancel_nothing(message: Message) -> None:
    """Handle requests, that should cancel state info, but there is none."""

    text = "Nothing to cancel, but.. okay?\n\nCanceled successfully!"

    await message.reply(text)

@router.message(StateFilter("*"), Command(commands=["cancel"]))
async def cancel(message: Message, state: FSMContext, bot: Bot) -> None:
    """Handle requests, that should cancel state info."""

    text = "Canceled successfully!"

    # Checking if user has been joining a chat, when canceling his state
    if await state.get_value("is_joining_chat"):
        chat_id = await state.get_value("chat_id")
        user_id = message.from_user.id
        try:
            await bot(DeclineChatJoinRequest(chat_id=chat_id, user_id=user_id))
        except:
            pass

        text += (
            "\n\nBut because you were joining a chat - I should cancel your join "
            "request. But you can try to join again, or verify yourself with /start"
        )

    # Clearing FSM data
    await state.clear()

    await message.reply(text)
