from aiogram.fsm.state import StatesGroup, State


class MassInviteStates(StatesGroup):
    """Mass-invite link creation (owner) and redemption (student) states."""

    collecting = State()
    welcome_message = State()
    nickname = State()
