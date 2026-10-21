import html

import sentry_sdk

from app.bootstrap import Container
from app.bot.routers.chat.join.router import router
from app.bot.routers.user.registration.keyboards import (
    student_deeplink as student_deeplink_kb,
)
from app.bot.i18n.core import I18nContext

from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError
from aiogram.types import ChatMemberUpdated
from aiogram.filters import ChatMemberUpdatedFilter, JOIN_TRANSITION


@router.chat_member(ChatMemberUpdatedFilter(member_status_changed=JOIN_TRANSITION))
async def handle_join(  # noqa: C901
    event: ChatMemberUpdated, container: Container, i18n: I18nContext
) -> None:
    """Handling chat joins."""
    # Checking if chat is registered
    chat = await container.chat_service.get_by_telegram_id(chat_id=event.chat.id)
    if not chat:
        return

    # If chat title isn't set in DB - using from event
    chat_title = chat.title
    if not chat_title:
        chat_title = event.chat.title

    # Checking if user is valid 21ID user
    user_tg_id = event.new_chat_member.user.id
    user = await container.user_service.get_by_telegram_id(telegram_id=user_tg_id)
    if not user:
        return

    # If there is ID topic set - try to send message there
    if chat.id_topic_id:
        # Try to send message to ID topic
        try:
            campus = user.campus.short_name if user.campus else "-"
            local_text = (
                f'<a href="tg://user?id={user.telegram_id}">'
                f"{html.escape(user.nickname)}</a> "
                f"({html.escape(str(user.wave_name))}, {html.escape(campus)})"
            )

            chat_info = await event.bot.get_chat(user_tg_id)
            if not chat_info.has_private_forwards:
                keyboard = student_deeplink_kb.get(
                    chat_id=user_tg_id, nickname=user.nickname
                )
            else:
                keyboard = student_deeplink_kb.get(nickname=user.nickname)

            await event.bot.send_message(
                chat_id=chat.chat_id,
                message_thread_id=chat.id_topic_id,
                text=local_text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
            )
        except TelegramAPIError as e:
            sentry_sdk.capture_exception(e)

    # Try to send welcome message to user
    try:
        text = i18n.get(
            "chat-join-welcome", nickname=user.nickname, chat_title=chat_title
        )

        # Adding chat description
        if chat.desc_on_join:
            text += i18n.get("chat-join-message", text=chat.desc_on_join)

        await event.bot.send_message(
            chat_id=user.telegram_id,
            text=text,
        )
    except TelegramAPIError:
        # User hasn't started the bot or blocked it - nothing to do
        pass
