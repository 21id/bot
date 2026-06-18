from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.i18n.core import I18nCore, I18nContext


class I18nMiddleware(BaseMiddleware):
    """Resolves user locale and injects I18nContext as ``i18n`` into handler data."""

    def __init__(self, i18n_core: I18nCore):
        self._core = i18n_core

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        locale = await self._resolve_locale(event, data)
        data["i18n"] = self._core.get_context(locale)
        return await handler(event, data)

    async def _resolve_locale(
        self, event: TelegramObject, data: dict[str, Any]
    ) -> str:
        # 1. FSM state — language chosen but not yet persisted to DB
        state = data.get("state")
        if state:
            lang = await state.get_value("language")
            if lang:
                return lang

        # 2. User profile in DB
        container = data.get("container")
        from_user = getattr(event, "from_user", None)
        if container and from_user:
            user = await container.user_service.get_by_telegram_id(from_user.id)
            if user and getattr(user, "language", None):
                return user.language

        return self._core.default_locale
