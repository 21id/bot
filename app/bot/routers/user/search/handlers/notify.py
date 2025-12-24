from app.bootstrap import Container
from app.bot.routers.user.search.callback import SendNotification
from app.bot.routers.user.search.router import router
from app.bot.routers.user.registration.keyboards import (student_deeplink as
                                                         student_deeplink_kb)

from aiogram import Bot
from aiogram.types import CallbackQuery


@router.callback_query(SendNotification.filter())
async def notify_user(callback: CallbackQuery, callback_data: SendNotification,
                      container: Container, bot: Bot) -> None:
    user = await container.user_service.get_by_nickname(callback_data.nickname)
    sender = await container.user_service.get_by_telegram_id(callback.from_user.id)

    # If sender isn't registered
    if not sender:
        text = (
            "For privacy and security of our users, 21ID allows notification only for "
            "registered users\n\n🪪 So you should register in 21ID first, "
            "it takes less than 3 minutes"
        )

        await callback.answer(text, show_alert=True)
        return

    chat_info = await bot.get_chat(callback.from_user.id)
    if not chat_info.has_private_forwards:
        keyboard = student_deeplink_kb.get(chat_id=callback.from_user.id)
        is_private = False
    else:
        keyboard = None
        is_private = True

    try:
        text = (
            f"🚨 IMPORTANT 🚨\n\nHey, {user.nickname}!\n⚠️ {sender.nickname} "
            f"({sender.wave_name}, {sender.campus.short_name}) is looking forward to "
            "contacting with you (may be because of Peer Review). \n\n⚠️ Please, "
            "contact ASAP him via Rocket.Chat, Telegram or check School 21 Platform ("
            "AKA Edu) for incoming Peer reviews"
        )

        await bot.send_message(user.telegram_id, text, reply_markup=keyboard)

        text = f"Successfully sent a notification to {user.nickname}!"

        # Notifying user of privacy restrictions
        if is_private:
            text += (
                "\n\nBut because of your privacy restrictions (disabling forwarding), "
                "I couldn't add a button to your profile - so peer may take more time "
                "to find you"
            )
    except:
        text = (
            f"{user.nickname} has blocked 21ID bot or deleted his account, "
            f"can't reach him!"
        )

    await callback.answer(text, show_alert=True)