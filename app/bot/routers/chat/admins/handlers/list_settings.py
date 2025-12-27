from app.bootstrap import Container
from app.bot.routers.chat_admins.router import router

from aiogram.types import Message
from aiogram.filters import Command


@router.message(Command(commands=["list_settings"]))
async def list_settings(message: Message, container: Container) -> None:
    """Listing all chat settings."""

    chat = await container.chat_service.get_by_telegram_id(message.chat.id)

    if chat:
        text = (
            f"⚙️ Chat: {message.chat.title}\n"
            f"Join rules:\n- Intensive: {"✅ Yes" if chat.intensive_allowed else "❌ No"}"
            f"\n- Core: {"✅ Yes" if chat.core_allowed else "❌ No"}\n"
            f"ID Topic set: {"✅ Yes" if chat.id_topic_id else "❌ No"}\n"
            f"Message on join: {chat.desc_on_join}"
        )
    else:
        text = "Chat isn't created!"

    await message.reply(text)
