from aiogram.filters.callback_data import CallbackData


class SendNotification(CallbackData, prefix="send_notification"):
    """CallbackData object for notifying the student."""
    nickname: str
