import sentry_sdk

from app.bootstrap import Container
from app.bot.routers.user.approve_join.router import router
from app.bot.routers.user.approve_join.keyboard import join_request as join_request_kb
from app.bot.i18n.core import I18nContext

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import ChatJoinRequest
from aiogram.methods import ApproveChatJoinRequest, DeclineChatJoinRequest


@router.chat_join_request()
async def join_request(  # noqa: C901
    chat_join_request: ChatJoinRequest,
    bot: Bot,
    container: Container,
    i18n: I18nContext,
) -> None:
    """Handle join request in chat, where it's needed to join."""
    user_id = chat_join_request.from_user.id
    chat_id = chat_join_request.chat.id
    chat_title = chat_join_request.chat.title

    chat = await container.chat_service.get_by_telegram_id(chat_id)

    # Chat isn't registered in 21ID - decline request and notify user
    if chat is None:
        try:
            await bot(DeclineChatJoinRequest(chat_id=chat_id, user_id=user_id))
            await bot.send_message(
                user_id, text=i18n.get("chat-not-configured", chat_title=chat_title)
            )
        except TelegramAPIError as e:
            sentry_sdk.capture_exception(e)
        return

    user = await container.user_service.get_by_telegram_id(user_id)

    if user and user.is_verified:
        # If user can't be accepted due to chat settings - deny his request
        acceptance_requirements = (
            user.parallel != "Core program" and chat.intensive_allowed
        ) or (user.parallel == "Core program" and chat.core_allowed)

        if not acceptance_requirements:
            try:
                await bot(DeclineChatJoinRequest(chat_id=chat_id, user_id=user_id))
            except TelegramAPIError as e:
                sentry_sdk.capture_exception(e)

            text = i18n.get(
                "nickname-chat-denied",
                nickname=user.nickname,
                chat_title=chat_title,
                intensive="✅" if chat.intensive_allowed else "❌",
                core="✅" if chat.core_allowed else "❌",
            )

            await bot.send_message(user_id, text=text)
            return

        # Trying to accept
        try:
            await bot(ApproveChatJoinRequest(chat_id=chat_id, user_id=user_id))
        except TelegramAPIError as e:
            # Notify user on error
            sentry_sdk.capture_exception(e)
            await bot.send_message(user_id, text=i18n.get("join-request-error"))
            return

        text = i18n.get(
            "chat-join-welcome", nickname=user.nickname, chat_title=chat_title
        )

        # Adding chat description
        if chat.desc_on_join:
            text += i18n.get("chat-join-message", text=chat.desc_on_join)

        # Send welcome message
        await bot.send_message(user_id, text=text)
    else:
        text = i18n.get("join-request-verify", chat_title=chat_title)

        # Sending a message with "Start verification" button with special feature flag
        keyboard = join_request_kb.get(chat_id=chat_id, chat_title=chat_title)
        await bot.send_message(user_id, text, reply_markup=keyboard)
