from app.bootstrap import Container
from app.bot.routers.user.language.router import router
from app.bot.routers.user.language.callback import ChooseLanguage, SetLanguage
from app.bot.routers.user.language.keyboards import language as language_kb
from app.bot.utilities import reply_edit
from app.i18n.core import I18nContext

from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext


@router.callback_query(ChooseLanguage.filter())
async def choose_language(
    callback: CallbackQuery,
    callback_data: ChooseLanguage,
    container: Container,
    i18n: I18nContext,
) -> None:
    """Show the language picker."""
    locales = [
        (lc, container.i18n_core.get_context(lc).get("locale-name"))
        for lc in container.i18n_core.available_locales
    ]
    keyboard = language_kb.get(locales, back_to=callback_data.back_to, i18n=i18n)
    await reply_edit.answer(
        callback, text=i18n.get("language-select-text"), reply_markup=keyboard
    )


@router.callback_query(SetLanguage.filter())
async def set_language(
    callback: CallbackQuery,
    callback_data: SetLanguage,
    state: FSMContext,
    container: Container,
) -> None:
    """Persist chosen locale to FSM state and DB, then navigate back."""
    new_locale = callback_data.locale

    await state.update_data(language=new_locale)

    user = await container.user_service.get_by_telegram_id(callback.from_user.id)
    if user and user.id:
        await container.user_service.set_language(str(user.id), new_locale)

    new_i18n = container.i18n_core.get_context(new_locale)

    await callback.answer(new_i18n.get("language-set-ok"), show_alert=True)

    if callback_data.back_to == "settings":
        from app.bot.routers.user.menu.keyboard import settings as settings_kb
        text = new_i18n.get("settings-text")
        keyboard = settings_kb.get(new_i18n)
    else:
        from app.bot.routers.user.registration.keyboards import welcome as welcome_kb
        text = new_i18n.get("welcome-text")
        keyboard = welcome_kb.get(new_i18n)

    await reply_edit.answer(callback, text=text, reply_markup=keyboard)
