from aiogram.fsm.state import StatesGroup, State


class MigrationStates(StatesGroup):
    """Account migration states."""
    selecting_user = State()
    confirm_1 = State()
    confirm_2 = State()
    confirm_3 = State()
