from aiogram.fsm.state import StatesGroup, State


class RegistrationStates(StatesGroup):
    """User registration and verification states."""
    nickname = State()
    verification = State()
    welcome = State()
