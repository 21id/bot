import uuid
import os
from typing import Any

from aiogram import BaseMiddleware, Bot
from aiogram.types import TelegramObject

from app.bot.utilities.data_formatting import message_split


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
            error_uuid = str(uuid.uuid4())

            bot: Bot = data["bot"]

            try:
                # Sending raised error
                for msg in message_split(text=str(e), type_="error", uuid_=error_uuid):
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
                f"request:\n{e}\n\n✍️ Please, tell us about your side of "
                "occurred problem to @megaplov (bot administrator).\n\n"
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
