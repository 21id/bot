from aiogram.enums import ParseMode

from app.bootstrap import Container
from app.bot.routers.user.approve_join.router import router
from app.bot.routers.user.approve_join.keyboard import join_request as join_request_kb
from app.bot.routers.user.registration.keyboards import (student_deeplink as
                                                         student_deeplink_kb)

from aiogram import Bot
from aiogram.types import ChatJoinRequest
from aiogram.methods import ApproveChatJoinRequest, DeclineChatJoinRequest


@router.chat_join_request()
async def join_request(
        chat_join_request: ChatJoinRequest, bot: Bot, container: Container
):
    """Handle join request in chat, where it's needed to join."""

    user_id = chat_join_request.from_user.id
    chat_id = chat_join_request.chat.id
    chat_title = chat_join_request.chat.title

    user = await container.user_service.get_by_telegram_id(user_id)

    if user:
        chat = await container.chat_service.get_by_telegram_id(chat_id)

        # If user can't be accepted due to chat settings - deny his request
        acceptance_requirements = (
                (user.parallel != "Core program" and chat.intensive_allowed) or
                (user.parallel == "Core program" and chat.core_allowed)
        )

        if not acceptance_requirements:
            try:
                await bot(DeclineChatJoinRequest(chat_id=chat_id, user_id=user_id))
            except:
                pass

            text = (
                f"⚠️ Dear {user.nickname}!\n\nYou're denied from joining"
                f" '{chat_title}' based on chat join policy:\n"
                f"Intensive allowed: {"✅" if chat.intensive_allowed else '❌'}\n"
                f"Core allowed: {"✅" if chat.core_allowed else '❌'}\n\nIf you "
                "think that it's wrong denial - please, contact @megaplov"
            )

            await bot.send_message(user_id, text=text)
            return

        # Trying to accept
        try:
            await bot(ApproveChatJoinRequest(chat_id=chat_id, user_id=user_id))
        except Exception as e:
            # Notify user on error
            text = (
                f"⚠️ Got error while trying to accept your request: {e}\n\n"
                f"Try to send another request, or contact @megaplov"
            )
            await bot.send_message(user_id, text=text)
            return

        text = f"👋 Dear {user.nickname}, welcome to '{chat_title}'!"

        # Adding chat description
        if chat.desc_on_join:
            text += f"\n\nJoin message:\n{chat.desc_on_join}"

        # If there is ID topic set - try to send message there
        if chat.id_topic_id:
            try:
                local_text = (
                    f'<a href="tg://user?id={user.telegram_id}">{user.nickname}</a> '
                    f'({user.wave_name}, {user.campus.short_name})'
                )

                chat_info = await bot.get_chat(user_id)
                if not chat_info.has_private_forwards:
                    keyboard = student_deeplink_kb.get(chat_id=user_id)
                else:
                    keyboard = student_deeplink_kb.get(nickname=user.nickname)

                await bot.send_message(
                    chat_id=chat.chat_id,
                    message_thread_id=chat.id_topic_id,
                    text=local_text,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.HTML,
                )
            except Exception as e:
                print("NICKNAME_SEND_ERROR", user.nickname, e)
                local_text = (
                    f"Can't send your nickname and deeplink to '{chat_title}' ID "
                    f"topic because of an error ({e})\n\n🔗 Students can find you "
                    "anyway, and this would be a bit easier for them, so please - "
                    "send your nickname to ID topic"
                )

                await bot.send_message(user_id, text=local_text)

        # Send welcome message
        await bot.send_message(user_id, text=text)
    else:
        text = (
            f"🔗 To join chat '{chat_title}' - you need to first verify your "
            "School 21 student status\n\nTo do that - press button below to start "
            "verification process"
        )

        # Sending a message with "Start verification" button with special feature flag
        keyboard = join_request_kb.get(chat_id=chat_id, chat_title=chat_title)
        await bot.send_message(user_id, text, reply_markup=keyboard)
