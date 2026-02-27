from aiogram.filters.callback_data import CallbackData


class InviteStudent(CallbackData, prefix="invite_student"):
    """CallbackData object for inviting new student to 21ID via mail."""
    invited_login: str
