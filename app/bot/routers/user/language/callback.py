from aiogram.filters.callback_data import CallbackData


class ChooseLanguage(CallbackData, prefix="lang_choose"):
    """Open the language picker. back_to controls where to return after selection."""
    back_to: str = "welcome"

class SetLanguage(CallbackData, prefix="lang_set"):
    """Persist locale selection and navigate back."""
    locale: str
    back_to: str = "welcome"
