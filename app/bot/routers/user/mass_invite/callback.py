from aiogram.filters.callback_data import CallbackData


class MassInviteFinish(CallbackData, prefix="mass_invite_finish"):
    """CallbackData object for finishing (done) or cancelling link creation."""

    done: bool
