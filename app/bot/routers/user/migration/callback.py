from aiogram.filters.callback_data import CallbackData


class MigrateConfirm(CallbackData, prefix="migrate_confirm"):
    """CallbackData object for migration confirmation buttons."""
    confirmed: bool
