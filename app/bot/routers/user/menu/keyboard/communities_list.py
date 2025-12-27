from typing import AsyncGenerator

from app.domain.chat.chat import Chat
from app.bot.routers.user.menu.callback import Menu

from aiogram.utils.keyboard import (InlineKeyboardBuilder, InlineKeyboardButton,
                                    InlineKeyboardMarkup)


async def get(chats: list[Chat] | AsyncGenerator[Chat]) -> InlineKeyboardMarkup:
    """Creating inline keyboard for listing all communities."""

    builder = InlineKeyboardBuilder()

    async for chat in chats:
        # If there is a join link present - mark button with emoji
        text = ""
        if chat.join_link:
            text = "🔗 "

        if chat.description:
            text += f"{chat.title} - {chat.description}"
        else:
            text += f"{chat.title}"

        builder.row(InlineKeyboardButton(
            text=text, url=chat.join_link
        ))

    builder.row(InlineKeyboardButton(
        text="⬅️ Back", callback_data=Menu().pack()
    ))

    return builder.as_markup()
