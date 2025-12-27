from app.bootstrap import Container
from app.bot.routers.chat.join.router import router
from app.bot.routers.user.registration.keyboards import (student_deeplink as
                                                         student_deeplink_kb)

from aiogram.enums import ParseMode
from aiogram.types import ChatMemberUpdated
from aiogram.filters import ChatMemberUpdatedFilter, JOIN_TRANSITION


@router.chat_member(ChatMemberUpdatedFilter(member_status_changed=JOIN_TRANSITION))
async def handle_join(event: ChatMemberUpdated, container: Container) -> None:
    """Handling chat joins."""

    # Checking if chat is registered
    chat = await container.chat_service.get_by_telegram_id(chat_id=event.chat.id)
    if not chat:
        return

    # Checking if user is valid 21ID user
    user_tg_id = event.new_chat_member.user.id
    user = await container.user_service.get_by_telegram_id(
        telegram_id=user_tg_id)
    if not user:
        return

    # If there is ID topic set - try to send message there
    if chat.id_topic_id:
        # Try to send message to ID topic
        try:
            local_text = (
                f'<a href="tg://user?id={user.telegram_id}">{user.nickname}</a> '
                f'({user.wave_name}, {user.campus.short_name})'
            )

            chat_info = await event.bot.get_chat(user_tg_id)
            if not chat_info.has_private_forwards:
                keyboard = student_deeplink_kb.get(chat_id=user_tg_id)
            else:
                keyboard = student_deeplink_kb.get(nickname=user.nickname)

            await event.bot.send_message(
                chat_id=chat.chat_id,
                message_thread_id=chat.id_topic_id,
                text=local_text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            pass

    # Try to send welcome message to user
    try:
        text = f"👋 Dear {user.nickname}, welcome to '{chat.title}'!"

        # Adding chat description
        if chat.desc_on_join:
            text += f"\n\nJoin message:\n{chat.desc_on_join}"

        await event.bot.send_message(
            chat_id=user.telegram_id,
            text=text,
        )
    except Exception as e:
        pass