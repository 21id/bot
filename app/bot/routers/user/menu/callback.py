from aiogram.filters.callback_data import CallbackData


class GetCommunities(CallbackData, prefix="menu_communities"):
    """CallbackData object for getting communities from menu."""
    pass

class Menu(CallbackData, prefix="menu_get"):
    """CallbackData object for getting back to menu."""
    pass
