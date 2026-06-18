from aiogram import Router

router = Router(name="language")


def register_filters() -> Router:
    from .handlers import language
    return router
