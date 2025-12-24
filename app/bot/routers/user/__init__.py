from aiogram import Router

router = Router()


def register_sub_routers() -> Router:
    """Importing all needed sub-routers to add them into users router."""
    from app.bot.routers.user import registration, approve_join, search, invite, menu

    routers = [
        approve_join.router,
        registration.router.register_filters(),
        menu.router.register_filters(),
        search.router,
        invite.router,
    ]

    router.include_routers(*routers)

    return router

def register_filters() -> Router:
    """Importing all needed middlewares to add them into users router."""
    pass
