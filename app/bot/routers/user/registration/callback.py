from aiogram.filters.callback_data import CallbackData


class GetDetails(CallbackData, prefix="welcome_details"):
    """CallbackData object for getting welcome details from menu."""
    pass

class RegistrationMenu(CallbackData, prefix="welcome_main"):
    """CallbackData object for returning back to registration menu."""
    pass

class StartRegistration(CallbackData, prefix="welcome_reg_start"):
    """CallbackData object for starting registration."""
    # Params for join request
    approve_join: bool = False
    join_chat_id: int = 0
    join_chat_title: str = ""

class ChangeNickname(CallbackData, prefix="welcome_reg_change_nickname"):
    """CallbackData object for changing nickname."""
    pass
