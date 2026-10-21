from typing import Any

from aiogram.types import CallbackQuery, Message


async def answer(
    request: Message | CallbackQuery,
    answer_: bool = False,
    **arguments: Any,  # noqa: ANN401
) -> None:
    """Answer a message or edit the callback message (optionally also answer)."""
    if answer_ and isinstance(request, CallbackQuery):
        await request.message.answer(**arguments)

    if isinstance(request, Message):
        await request.answer(**arguments)
    elif isinstance(request, CallbackQuery):
        await request.message.edit_text(**arguments)
