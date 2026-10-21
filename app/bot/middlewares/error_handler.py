import uuid
from typing import Any, Awaitable, Callable

from app.bot.utilities.data_formatting import message_split
from app.domain.base_error import BaseError

import sentry_sdk
from aiogram import BaseMiddleware, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import TelegramObject

GENERIC_ERROR_TEXT = (
    "⚠️ Dear user, I got an error while trying to handle your request.\n\n"
    "✍️ Please, if you have any questions - contact @megaplov (21ID developer).\n\n"
    "ERROR UUID: {uuid}"
)
DETAILED_ERROR_TEXT = (
    "⚠️ Dear user, I got an error while trying to handle your request:\n{details}"
    "\n\n✍️ Please, if you have any questions - contact @megaplov (21ID developer)."
    "\n\nERROR UUID: {uuid}"
)


class ErrorMiddleware(BaseMiddleware):
    """Catches handler errors, reports them to Sentry, admin and user."""

    def __init__(self, admin_id: int) -> None:
        """Initialize middleware."""
        self.admin_id = admin_id

    async def __call__(  # noqa: C901
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:  # noqa: ANN401
        """Run handler, handling any raised error."""
        try:
            return await handler(event, data)

        except Exception as e:
            # Expired callback queries are raised even if nothing really failed
            if isinstance(e, TelegramBadRequest) and "query is too old" in e.message:
                return None

            error_uuid = str(uuid.uuid4())
            bot: Bot = data["bot"]
            user = data.get("event_from_user")
            chat = data.get("event_chat")

            with sentry_sdk.new_scope() as scope:
                scope.set_tag("error_uuid", error_uuid)
                if user:
                    scope.set_user({"id": user.id})
                sentry_sdk.capture_exception(e)

            # Only BaseError messages are safe to show to the user
            if isinstance(e, BaseError):
                client_message = e.client_message
                support_data = e.support_details
                notify_user = e.notify_user
            else:
                client_message = None
                support_data = str(e)
                notify_user = True

            state = data.get("state")
            fsm_state = await state.get_state() if state else None
            handler_obj = data.get("handler")
            handler_name = getattr(handler_obj, "callback", handler)
            report = (
                f"{type(e).__name__}: {support_data}\n"
                f"handler: {getattr(handler_name, '__qualname__', handler_name)}\n"
                f"user: {user.id if user else None}\n"
                f"state: {fsm_state}"
            )

            try:
                for msg in message_split(text=report, type_="error", uuid_=error_uuid):
                    await bot.send_message(self.admin_id, msg)
            except Exception as e2:
                sentry_sdk.capture_exception(e2)

            if not notify_user:
                return None

            i18n = data.get("i18n")
            if client_message:
                text = (
                    i18n.get(
                        "error-with-details", details=client_message, uuid=error_uuid
                    )
                    if i18n
                    else DETAILED_ERROR_TEXT.format(
                        details=client_message, uuid=error_uuid
                    )
                )
            else:
                text = (
                    i18n.get("error-generic", uuid=error_uuid)
                    if i18n
                    else GENERIC_ERROR_TEXT.format(uuid=error_uuid)
                )

            # Try sending to user personally, then to the chat of the event
            for target in (user, chat):
                if target is None:
                    continue
                try:
                    await bot.send_message(target.id, text)
                    return None
                except Exception as e2:
                    sentry_sdk.capture_exception(e2)

            sentry_sdk.capture_message(
                f"Have no way to send user error message {error_uuid}"
            )
            return None
