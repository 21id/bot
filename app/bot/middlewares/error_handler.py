import uuid
import os
from typing import Any

from app.bot.utilities.data_formatting import message_split
from app.domain.base_error import BaseError

from aiogram import BaseMiddleware, Bot
from aiogram.types import TelegramObject


class ErrorMiddleware(BaseMiddleware):
    def __init__(self):
        self.admin_id = int(os.getenv("ADMIN_ID"))

    async def __call__(
        self,
        handler,
        event: TelegramObject,
        data: dict[str, Any],
    ):
        try:
            return await handler(event, data)

        except Exception as e:

            basic_errors = [
                # Handling old requests
                ("Telegram server says - Bad Request: query is too old and "
                 "response timeout expired or query ID is invalid")
            ]
            # Trying to see if this is an 'possible mistake'
            if str(e) in basic_errors:
                return None

            error_uuid = str(uuid.uuid4())

            bot: Bot = data["bot"]

            client_message = str(e)
            support_data = str(e)
            # If it's BaseError (local error type) - remap messages
            if isinstance(e, BaseError):
                client_message = e.message
                support_data = e.support_details

            try:
                # Sending raised error
                for msg in message_split(text=support_data, type_="error",
                                         uuid_=error_uuid):
                    await bot.send_message(self.admin_id, msg)

                # Sending event itself
                for msg in message_split(text=str(event), type_="event",
                                         uuid_=error_uuid):
                    await bot.send_message(self.admin_id, msg)

                # Sending handler data
                for msg in message_split(text=str(handler), type_="handler",
                                         uuid_=error_uuid):
                    await bot.send_message(self.admin_id, msg)

                # Sending event data
                for msg in message_split(text=str(data), type_="data",
                                         uuid_=error_uuid):
                    await bot.send_message(self.admin_id, msg)
            except Exception as e2:
                print(error_uuid, e2)
                print(error_uuid, e, event, handler, data, end="\n")

            text = (
                "⚠️ Dear user, I got an error while trying to handle your "
                f"request:\n{client_message}\n\n✍️ Please, if you have any questions "
                f"- contact @megaplov (21ID developer).\n\n"
                f"ERROR UUID: {error_uuid}"
            )

            # Notify the user of an error
            user = data.get("event_from_user")
            if user:
                # Try sending to user personally
                try:
                    await bot.send_message(user.id, text)
                    return None
                except Exception as e2:
                    print(error_uuid, "Send to PM failed:", e2)

            # Try sending to chat, where this action was invoked, if can't do that to
            # user's PM
            chat = data.get("event_chat")
            if chat:
                try:
                    await bot.send_message(user.id, text)
                    return None
                except Exception as e2:
                    print(error_uuid, "Send to PM failed:", e2)

            print(error_uuid, "Have no way to send user his error message")
            return None
