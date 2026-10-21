from aiogram import Router

router = Router(name="language")


def register_filters() -> Router:
    """Import handlers to register them and return router."""
    from .handlers import language  # noqa: F401

    return router
