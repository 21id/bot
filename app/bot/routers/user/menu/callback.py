from aiogram.filters.callback_data import CallbackData


class GetCommunities(CallbackData, prefix="menu_communities"):
    """CallbackData object for getting communities from menu."""
    pass

class Menu(CallbackData, prefix="menu_get"):
    """CallbackData object for getting back to menu."""
    pass

class AccountMigration(CallbackData, prefix="menu_migration"):
    """CallbackData object for starting account migration from menu."""
    pass

class Settings(CallbackData, prefix="menu_settings"):
    """CallbackData object for opening settings from menu."""
    pass
