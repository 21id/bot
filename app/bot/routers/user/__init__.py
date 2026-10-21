from aiogram import Router

router = Router()


def register_sub_routers() -> Router:
    """Importing all needed sub-routers to add them into users router."""
    from app.bot.routers.user import (
        registration,
        approve_join,
        search,
        invite,
        menu,
        migration,
        language,
        mass_invite,
    )

    routers = [
        # Temporary: before registration, so mi_ deeplinks and states win
        mass_invite.register_filters(),
        approve_join.router,
        registration.router.register_filters(),
        menu.router.register_filters(),
        migration.router.register_filters(),
        language.register_filters(),
        search.router,
        invite.router,
    ]

    router.include_routers(*routers)

    return router


def register_filters() -> Router:
    """Importing all needed middlewares to add them into users router."""
    pass
