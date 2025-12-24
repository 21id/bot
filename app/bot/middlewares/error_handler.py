import os
import traceback
import logging
from typing import Any

from aiogram import BaseMiddleware, Bot
from aiogram.types import TelegramObject, Update

logger = logging.getLogger(__name__)


class ErrorMiddleware(BaseMiddleware):
    def __init__(self):
        self.admin_id = int(os.getenv("ADMIN_ID", "0"))

    async def __call__(
        self,
        handler,
        event: TelegramObject,
        data: dict[str, Any],
    ):
        try:
            return await handler(event, data)

        except Exception as e:
            # TODO: Add Admin notification
            # TODO: Check it out, because it may not work (or some other logging
            #  problem, IDK)
            print(e, event, data)

            return None