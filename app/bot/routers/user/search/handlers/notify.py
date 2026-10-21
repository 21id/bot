from app.bootstrap import Container
from app.bot.routers.user.search.callback import SendNotification
from app.bot.routers.user.search.router import router
from app.bot.routers.user.registration.keyboards import (
    student_deeplink as student_deeplink_kb,
)
from app.bot.i18n.core import I18nContext

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import CallbackQuery


@router.callback_query(SendNotification.filter())
async def notify_user(  # noqa: C901
    callback: CallbackQuery,
    callback_data: SendNotification,
    container: Container,
    bot: Bot,
    i18n: I18nContext,
) -> None:
    """Send notification to 21ID user from another registered user."""
    user = await container.user_service.get_by_nickname(callback_data.nickname)
    sender = await container.user_service.get_by_telegram_id(callback.from_user.id)

    if user and sender and user.telegram_id == sender.telegram_id:
        await callback.answer(
            i18n.get("notify-self", nickname=user.nickname), show_alert=True
        )
        return

    if not sender:
        await callback.answer(i18n.get("notify-not-registered"), show_alert=True)
        return

    # Invited-but-unregistered users are treated as non-existent
    if not user or user.is_invited:
        await callback.answer(i18n.get("notify-target-not-found"), show_alert=True)
        return

    if not user.telegram_id:
        await callback.answer(i18n.get("notify-no-telegram"), show_alert=True)
        return

    rl_key = f"rl:notify:{callback.from_user.id}:{user.id}"
    if not await container.redis.set(rl_key, 1, nx=True, ex=300):
        seconds = await container.redis.ttl(rl_key)
        await callback.answer(
            i18n.get("rate-limited", seconds=seconds), show_alert=True
        )
        return

    chat_info = await bot.get_chat(callback.from_user.id)
    if not chat_info.has_private_forwards:
        keyboard = student_deeplink_kb.get(chat_id=callback.from_user.id)
    else:
        keyboard = student_deeplink_kb.get(
            chat_id=callback.from_user.id, nickname=user.nickname
        )

    try:
        notify_text = i18n.get(
            "notify-message",
            nickname=user.nickname,
            sender=sender.nickname,
            wave=sender.wave_name,
            campus=sender.campus.short_name if sender.campus else "-",
        )
        await bot.send_message(user.telegram_id, notify_text, reply_markup=keyboard)
        text = i18n.get("notify-success", nickname=user.nickname)
    except TelegramAPIError:
        text = i18n.get("notify-blocked", nickname=user.nickname)

    await callback.answer(text, show_alert=True)
