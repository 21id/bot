from app.bot.routers.user.mass_invite.callback import MassInviteFinish
from app.bot.i18n.core import I18nContext

from aiogram.utils.keyboard import (
    InlineKeyboardBuilder,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


def get(
    i18n: I18nContext, done_key: str = "mass-invite-btn-done"
) -> InlineKeyboardMarkup:
    """Creating inline keyboard to finish nicknames collection (or skip a step)."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=i18n.get(done_key),
            callback_data=MassInviteFinish(done=True).pack(),
        ),
        InlineKeyboardButton(
            text=i18n.get("mass-invite-btn-cancel"),
            callback_data=MassInviteFinish(done=False).pack(),
        ),
    )

    return builder.as_markup()
