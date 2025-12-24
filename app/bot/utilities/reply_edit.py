from aiogram.types import CallbackQuery, Message


async def answer(request: Message | CallbackQuery, **arguments):
    if isinstance(request, Message):
        await request.answer(**arguments)
    elif isinstance(request, CallbackQuery):
        await request.message.edit_text(**arguments)
