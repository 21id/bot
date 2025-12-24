from .router import router
from .handlers import (set_id_topic, base_create, list_settings, set_join_rules,
                       set_description)

from aiogram import Router, F


def register_filters() -> Router:
    """Importing all needed middlewares to add them into chat admins router."""
    from app.bot.filters.is_admin import IsAdmin

    # Applying filters to check if user is admin in a chat (group / supergroup)
    admin_in_community = (IsAdmin(is_admin=True) and
                          F.chat.type in ["group", "supergroup"])

    router.message.filter(admin_in_community)
    router.callback_query.filter(admin_in_community)

    return router
