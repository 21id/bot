from app.bootstrap import Container
from app.bot.routers.user.migration.router import router
from app.bot.routers.user.migration.states import MigrationStates
from app.bot.routers.user.migration.callback import MigrateConfirm
from app.bot.routers.user.menu.callback import AccountMigration
from app.bot.routers.user.migration.keyboards import migration as migration_kb
from app.i18n.core import I18nContext

from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext


@router.callback_query(AccountMigration.filter())
async def start_migration(
    callback: CallbackQuery, state: FSMContext, i18n: I18nContext
) -> None:
    """Starting account migration flow."""
    text = i18n.get("account-migration-start")
    await state.set_state(MigrationStates.selecting_user)
    await callback.message.answer(
        text=text,
        reply_markup=migration_kb.get_select_user(i18n),
    )
    await callback.answer()


@router.message(F.users_shared, StateFilter(MigrationStates.selecting_user))
async def user_selected(
    message: Message, state: FSMContext, container: Container, i18n: I18nContext
) -> None:
    """Handling shared user selection for migration target."""
    new_tg_id = message.users_shared.users[0].user_id

    if new_tg_id == message.from_user.id:
        text = i18n.get("account-migration-self-error")
        await message.answer(text=text, reply_markup=migration_kb.get_select_user(i18n))
        return

    existing_user = await container.user_service.get_by_telegram_id(new_tg_id)
    if existing_user:
        text = i18n.get("account-migration-taken")
        await message.answer(text=text)
        await state.clear()
        return

    await state.update_data(new_tg_id=new_tg_id)
    await state.set_state(MigrationStates.confirm_1)

    await message.answer(
        text=i18n.get("account-migration-confirm-1"),
        reply_markup=migration_kb.get_confirm(),
    )


@router.callback_query(MigrateConfirm.filter(), StateFilter(MigrationStates.confirm_1))
async def confirm_round_1(
    callback: CallbackQuery, callback_data: MigrateConfirm,
    state: FSMContext, i18n: I18nContext,
) -> None:
    """First confirmation round."""
    if not callback_data.confirmed:
        await state.clear()
        await callback.message.edit_text(i18n.get("account-migration-cancelled"))
        await callback.answer()
        return

    await state.set_state(MigrationStates.confirm_2)
    await callback.message.edit_text(
        text=i18n.get("account-migration-confirm-2"),
        reply_markup=migration_kb.get_confirm(),
    )
    await callback.answer()


@router.callback_query(MigrateConfirm.filter(), StateFilter(MigrationStates.confirm_2))
async def confirm_round_2(
    callback: CallbackQuery, callback_data: MigrateConfirm,
    state: FSMContext, i18n: I18nContext,
) -> None:
    """Second confirmation round."""
    if not callback_data.confirmed:
        await state.clear()
        await callback.message.edit_text(i18n.get("account-migration-cancelled"))
        await callback.answer()
        return

    await state.set_state(MigrationStates.confirm_3)
    await callback.message.edit_text(
        text=i18n.get("account-migration-confirm-3"),
        reply_markup=migration_kb.get_confirm(),
    )
    await callback.answer()


@router.callback_query(MigrateConfirm.filter(), StateFilter(MigrationStates.confirm_3))
async def confirm_round_3(
    callback: CallbackQuery, callback_data: MigrateConfirm,
    state: FSMContext, container: Container, i18n: I18nContext,
) -> None:
    """Third and final confirmation round."""
    if not callback_data.confirmed:
        await state.clear()
        await callback.message.edit_text(i18n.get("account-migration-cancelled"))
        await callback.answer()
        return

    current_user = await container.user_service.get_by_telegram_id(callback.from_user.id)
    if not current_user:
        await state.clear()
        await callback.message.edit_text(i18n.get("account-migration-error"))
        await callback.answer()
        return

    new_tg_id = int(await state.get_value("new_tg_id"))
    await container.user_service.migrate_telegram_id(str(current_user.id), new_tg_id)
    await state.clear()

    await callback.message.edit_text(i18n.get("account-migration-success"))
    await callback.answer()
