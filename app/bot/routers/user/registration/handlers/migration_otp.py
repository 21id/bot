import sentry_sdk

from app.bootstrap import Container
from app.domain.verification.method import VerificationMethod
from app.bot.utilities import reply_edit
from app.bot.routers.user.registration.router import router
from app.bot.routers.user.registration.states import RegistrationStates
from app.bot.routers.user.registration.callback import (
    ChangeNickname,
    SendMigrationOtpEmail,
)
from app.bot.routers.user.registration.keyboards import migration_otp_kb
from app.bot.i18n.core import I18nContext

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext


@router.message(StateFilter(RegistrationStates.migration_otp))
async def migration_otp(
    message: Message,
    state: FSMContext,
    container: Container,
    bot: Bot,
    i18n: I18nContext,
) -> None:
    """Verifying migration OTP entered by user trying to claim another account."""
    entered_otp = message.text
    original_nickname = await state.get_value("migration_original_nickname")
    original_user_id = await state.get_value("migration_original_user_id")
    new_tg_id = message.from_user.id

    subject = f"{original_user_id}:{new_tg_id}"
    result = await container.verification_service.check(
        VerificationMethod.MIGRATION_OTP, subject, entered_otp or ""
    )

    if not result:
        await state.set_state(RegistrationStates.nickname)
        await reply_edit.answer(message, text=i18n.get("migration-otp-expired"))
        return

    if not result.passed:
        remaining = result.remaining

        if remaining <= 0:
            await container.verification_service.cancel(
                VerificationMethod.MIGRATION_OTP, subject
            )
            await state.clear()
            await reply_edit.answer(message, text=i18n.get("migration-otp-exhausted"))
            return

        text = i18n.get("migration-otp-wrong", remaining=remaining)
        await reply_edit.answer(
            message, text=text, reply_markup=migration_otp_kb.get(i18n)
        )
        return

    if await container.user_service.telegram_id_taken(
        new_tg_id, exclude_user_id=original_user_id
    ):
        await state.clear()
        await reply_edit.answer(message, text=i18n.get("account-migration-taken"))
        return

    original_user = await container.user_service.get_by_nickname(original_nickname)
    old_tg_id = original_user.telegram_id if original_user else None

    await container.verification_service.complete(
        original_user, VerificationMethod.MIGRATION_OTP, new_tg_id
    )
    await state.clear()

    await reply_edit.answer(message, text=i18n.get("migration-otp-success"))

    if old_tg_id and old_tg_id != new_tg_id:
        try:
            await bot.send_message(
                old_tg_id,
                i18n.get("migration-old-account-notice", nickname=original_nickname),
            )
        except TelegramAPIError as e:
            sentry_sdk.capture_exception(e)


@router.callback_query(
    SendMigrationOtpEmail.filter(), StateFilter(RegistrationStates.migration_otp)
)
async def send_via_email(
    callback: CallbackQuery,
    state: FSMContext,
    container: Container,
    i18n: I18nContext,
) -> None:
    """Send migration OTP to the original account's school email."""
    original_nickname = await state.get_value("migration_original_nickname")
    original_user_id = await state.get_value("migration_original_user_id")
    new_tg_id = callback.from_user.id

    attempt = await container.verification_service.get(
        VerificationMethod.MIGRATION_OTP, f"{original_user_id}:{new_tg_id}"
    )

    if not attempt:
        await state.set_state(RegistrationStates.nickname)
        await callback.message.edit_text(i18n.get("migration-otp-expired"))
        await callback.answer()
        return

    rl_key = f"rl:migr-email:{new_tg_id}"
    if not await container.redis.set(rl_key, 1, nx=True, ex=60):
        seconds = await container.redis.ttl(rl_key)
        await callback.answer(
            i18n.get("rate-limited", seconds=seconds), show_alert=True
        )
        return

    email = f"{original_nickname}@student.21-school.ru"
    otp_code = attempt["code"]
    email_subject = f"[{otp_code}] 21ID Migration OTP Code"
    email_context = {"username": original_nickname, "code": otp_code}

    try:
        is_email_sent = await container.mail_client.send_from_template(
            to=email,
            subject=email_subject,
            template_name="otp.html",
            context=email_context,
        )
    except Exception as e:
        sentry_sdk.capture_exception(e)
        is_email_sent = False

    if not is_email_sent:
        await callback.answer(i18n.get("migration-otp-email-error"), show_alert=True)
        return

    await callback.answer(
        i18n.get("migration-otp-email-sent", email=email), show_alert=True
    )


@router.callback_query(
    ChangeNickname.filter(), StateFilter(RegistrationStates.migration_otp)
)
async def cancel_migration_otp(
    callback: CallbackQuery, state: FSMContext, i18n: I18nContext
) -> None:
    """Go back to nickname input, cancelling migration OTP flow."""
    await state.set_state(RegistrationStates.nickname)
    await callback.message.edit_text(i18n.get("migration-otp-cancel"))
    await callback.answer()
