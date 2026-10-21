from app.bootstrap import Container
from app.domain.mass_invite.mass_invite import parse_nicknames
from app.bot.routers.user.mass_invite.router import router, is_owner
from app.bot.routers.user.mass_invite.states import MassInviteStates
from app.bot.routers.user.mass_invite.callback import MassInviteFinish
from app.bot.routers.user.mass_invite.keyboards import collect as collect_kb
from app.bot.i18n.core import I18nContext

from aiogram import F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext


@router.message(Command(commands=["mass_invite"]), F.chat.type == "private", is_owner)
async def mass_invite(message: Message, state: FSMContext, i18n: I18nContext) -> None:
    """Start collecting nicknames for a mass-invite link."""
    await state.clear()
    await state.set_state(MassInviteStates.collecting)
    await state.update_data(mi_nicknames=[])

    await message.reply(
        i18n.get("mass-invite-start"), reply_markup=collect_kb.get(i18n)
    )


@router.message(StateFilter(MassInviteStates.collecting), F.text, is_owner)
async def collect(message: Message, state: FSMContext, i18n: I18nContext) -> None:
    """Accumulate nicknames sent by the owner."""
    valid, invalid = parse_nicknames(message.text)
    nicknames: list[str] = await state.get_value("mi_nicknames") or []

    added = [nickname_ for nickname_ in valid if nickname_ not in nicknames]
    nicknames += added
    await state.update_data(mi_nicknames=nicknames)

    text = i18n.get(
        "mass-invite-collected",
        added=len(added),
        total=len(nicknames),
        invalid=", ".join(invalid) or "-",
    )
    await message.reply(text, reply_markup=collect_kb.get(i18n))


@router.callback_query(
    StateFilter(MassInviteStates.collecting), MassInviteFinish.filter(), is_owner
)
async def finish(
    callback: CallbackQuery,
    callback_data: MassInviteFinish,
    state: FSMContext,
    container: Container,
    bot: Bot,
    i18n: I18nContext,
) -> None:
    """Ask for welcome message (done) or drop collected nicknames (cancel)."""
    if not callback_data.done:
        await state.clear()
        await callback.message.edit_text(i18n.get("cancel-success"))
        return

    nicknames: list[str] = await state.get_value("mi_nicknames") or []
    if not nicknames:
        await callback.answer(i18n.get("mass-invite-empty"), show_alert=True)
        return

    await state.set_state(MassInviteStates.welcome_message)
    await callback.message.edit_text(
        i18n.get("mass-invite-welcome-prompt", count=len(nicknames)),
        reply_markup=collect_kb.get(i18n, done_key="mass-invite-btn-skip"),
    )


@router.message(StateFilter(MassInviteStates.welcome_message), F.text, is_owner)
async def welcome_message(
    message: Message,
    state: FSMContext,
    container: Container,
    bot: Bot,
    i18n: I18nContext,
) -> None:
    """Create the link with owner's welcome message (formatting is kept)."""
    welcome_message_ = message.html_text
    if len(welcome_message_) > 3500:
        await message.reply(i18n.get("mass-invite-welcome-too-long"))
        return

    nicknames: list[str] = await state.get_value("mi_nicknames") or []
    link = await container.mass_invite_service.create(
        nicknames, message.from_user.id, welcome_message=welcome_message_
    )
    me = await bot.me()
    url = f"https://t.me/{me.username}?start=mi_{link.id}"
    await state.clear()

    text = i18n.get("mass-invite-created", url=url, count=len(nicknames))
    await message.reply(text)


@router.callback_query(
    StateFilter(MassInviteStates.welcome_message),
    MassInviteFinish.filter(),
    is_owner,
)
async def skip_welcome_message(
    callback: CallbackQuery,
    callback_data: MassInviteFinish,
    state: FSMContext,
    container: Container,
    bot: Bot,
    i18n: I18nContext,
) -> None:
    """Create the link without welcome message (skip) or cancel creation."""
    if not callback_data.done:
        await state.clear()
        await callback.message.edit_text(i18n.get("cancel-success"))
        return

    nicknames: list[str] = await state.get_value("mi_nicknames") or []
    link = await container.mass_invite_service.create(nicknames, callback.from_user.id)
    me = await bot.me()
    url = f"https://t.me/{me.username}?start=mi_{link.id}"
    await state.clear()

    text = i18n.get("mass-invite-created", url=url, count=len(nicknames))
    await callback.message.edit_text(text)
