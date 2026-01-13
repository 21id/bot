from aiogram.types import CallbackQuery, Message


async def answer(request: Message | CallbackQuery, answer_: bool = False, **arguments):
    if answer_ and isinstance(request, CallbackQuery):
        await request.message.answer(**arguments)

    if isinstance(request, Message):
        await request.answer(**arguments)
    elif isinstance(request, CallbackQuery):
        await request.message.edit_text(**arguments)
