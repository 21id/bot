from app.bootstrap import Container
from app.bot.utilities import reply_edit
from app.bot.routers.user.registration.router import router
from app.bot.routers.user.registration.states import RegistrationStates
from app.bot.routers.user.registration.callback import (ChangeNickname,
                                                         SendMigrationOtpEmail)
from app.bot.routers.user.registration.keyboards import migration_otp_kb
from app.i18n.core import I18nContext

from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext


@router.message(StateFilter(RegistrationStates.migration_otp))
async def migration_otp(
    message: Message, state: FSMContext, container: Container, i18n: I18nContext
) -> None:
    """Verifying migration OTP entered by user trying to claim another account."""
    entered_otp = message.text
    original_nickname = await state.get_value("migration_original_nickname")
    original_user_id = await state.get_value("migration_original_user_id")
    new_tg_id = message.from_user.id

    attempt = await container.user_service.get_migration_attempt(
        original_nickname, new_tg_id
    )

    if not attempt:
        await state.set_state(RegistrationStates.nickname)
        await reply_edit.answer(message, text=i18n.get("migration-otp-expired"))
        return

    if entered_otp != attempt["otp"]:
        remaining = attempt["attempts_count"] - 1

        if remaining <= 0:
            await container.user_service.clear_migration_attempt(
                original_user_id, new_tg_id
            )
            await state.clear()
            await reply_edit.answer(message, text=i18n.get("migration-otp-exhausted"))
            return

        await container.user_service.decrement_migration_attempt(
            original_user_id, new_tg_id
        )

        text = i18n.get("migration-otp-wrong", remaining=remaining)
        await reply_edit.answer(
            message, text=text, reply_markup=migration_otp_kb.get(i18n)
        )
        return

    await container.user_service.migrate_telegram_id(original_user_id, new_tg_id)
    await state.clear()

    await reply_edit.answer(message, text=i18n.get("migration-otp-success"))


@router.callback_query(SendMigrationOtpEmail.filter(),
                       StateFilter(RegistrationStates.migration_otp))
async def send_via_email(
    callback: CallbackQuery, state: FSMContext, container: Container, i18n: I18nContext
) -> None:
    """Send migration OTP to the original account's school email."""
    original_nickname = await state.get_value("migration_original_nickname")
    new_tg_id = callback.from_user.id

    attempt = await container.user_service.get_migration_attempt(
        original_nickname, new_tg_id
    )

    if not attempt:
        await state.set_state(RegistrationStates.nickname)
        await callback.message.edit_text(i18n.get("migration-otp-expired"))
        await callback.answer()
        return

    email = f"{original_nickname}@student.21-school.ru"
    otp_code = attempt["otp"]
    email_subject = f"[{otp_code}] 21ID Migration OTP Code"
    email_context = {"username": original_nickname, "code": otp_code}

    try:
        await container.mail_client.send_from_template(
            to=email, subject=email_subject, template_name="otp.html",
            context=email_context
        )
    except Exception:
        await callback.answer(i18n.get("migration-otp-email-error"), show_alert=True)
        return

    await callback.answer(i18n.get("migration-otp-email-sent", email=email), show_alert=True)


@router.callback_query(ChangeNickname.filter(),
                       StateFilter(RegistrationStates.migration_otp))
async def cancel_migration_otp(
    callback: CallbackQuery, state: FSMContext, i18n: I18nContext
) -> None:
    """Go back to nickname input, cancelling migration OTP flow."""
    await state.set_state(RegistrationStates.nickname)
    await callback.message.edit_text(i18n.get("migration-otp-cancel"))
    await callback.answer()
