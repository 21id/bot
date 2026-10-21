import asyncio
import uuid

import sentry_sdk

from app.bootstrap import Container
from app.domain.user.user import User
from app.infrastructure.s21.v1.models.responses.student import ParticipantV1DTO
from app.bot.routers.user.invite.callback import InviteStudent
from app.bot.routers.user.search.router import router
from app.bot.routers.user.registration.keyboards import (
    student_deeplink as student_deeplink_kb,
)
from app.bot.i18n.core import I18nContext

from aiogram import Bot, F
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)


@router.inline_query(F.query.len() >= 4)
async def inline_query(  # noqa: C901
    query: InlineQuery, container: Container, bot: Bot, i18n: I18nContext
) -> None:
    """Searching user by his Platform's nickname."""
    invoke_user = await container.user_service.get_by_telegram_id(query.from_user.id)

    partial_nickname = query.query.lower()
    if not partial_nickname:
        return

    bot_url = f"https://t.me/{(await bot.get_me()).username}"
    register_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=i18n.get("btn-register-free"), url=bot_url)]
        ]
    )

    async def build_result(user: User) -> InlineQueryResultArticle:
        """Build inline result for single 21ID user."""
        campus = user.campus.short_name if user.campus else "-"
        title = i18n.get("inline-title", nickname=user.nickname)
        short_description = i18n.get(
            "inline-short-desc", campus=campus, wave=user.wave_name
        )
        full_description = i18n.get(
            "inline-full-desc",
            nickname=user.nickname,
            campus=campus,
            wave=user.wave_name,
        )

        if invoke_user:
            try:
                workplace = (
                    await (
                        container.s21api_client.get_student_workplace_by_nickname(
                            user.nickname
                        )
                    )
                )
            except Exception as e:
                sentry_sdk.capture_exception(e)
                workplace = None
            if workplace:
                full_description += i18n.get(
                    "inline-awp-in",
                    nickname=user.nickname,
                    cluster=workplace.clusterName,
                    row=workplace.row,
                    number=workplace.number,
                )
            else:
                full_description += i18n.get("inline-awp-out", nickname=user.nickname)

            if user.is_verified:
                full_description += i18n.get("inline-verified")
            else:
                full_description += i18n.get("inline-not-verified")

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=i18n.get("btn-cant-find-telegram"),
                            callback_data="none",
                        )
                    ]
                ]
            )
            if user.telegram_id and user.is_verified:
                try:
                    chat_info = await bot.get_chat(user.telegram_id)
                    if not chat_info.has_private_forwards:
                        keyboard = student_deeplink_kb.get(
                            chat_id=user.telegram_id, nickname=user.nickname
                        )
                    else:
                        keyboard = student_deeplink_kb.get(nickname=user.nickname)
                except Exception as e:
                    sentry_sdk.capture_exception(e)
                    keyboard = student_deeplink_kb.get(nickname=user.nickname)
        else:
            full_description += i18n.get("inline-unregistered-hint")
            keyboard = register_keyboard

        return InlineQueryResultArticle(
            id=uuid.uuid4().hex,
            title=title,
            description=short_description,
            input_message_content=InputTextMessageContent(
                message_text=full_description
            ),
            reply_markup=keyboard,
        )

    # Invited-but-unregistered users are treated as non-existent
    users = [
        user
        async for user in container.user_service.search_by_nickname(
            partial_nickname, limit=20
        )
        if not user.is_invited
    ]
    results = list(await asyncio.gather(*(build_result(user) for user in users)))

    if len(results) == 0:
        student = await container.s21api_client.get_student_by_nickname(
            partial_nickname
        )

        if not isinstance(student, ParticipantV1DTO):
            results = [
                InlineQueryResultArticle(
                    id="none",
                    title=i18n.get("inline-not-found-title"),
                    description=i18n.get(
                        "inline-not-found-short", nickname=partial_nickname
                    ),
                    input_message_content=InputTextMessageContent(
                        message_text=i18n.get(
                            "inline-not-found-full", nickname=partial_nickname
                        )
                    ),
                )
            ]
        else:
            campus = student.campus.short_name if student.campus else "-"
            title = i18n.get("inline-student-title", nickname=student.login)
            short_description = i18n.get(
                "inline-student-short", campus=campus, wave=student.className
            )
            full_description = i18n.get(
                "inline-student-full",
                nickname=student.login,
                campus=campus,
                wave=student.className,
            )

            if invoke_user:
                try:
                    workplace = (
                        await (
                            container.s21api_client.get_student_workplace_by_nickname(
                                student.login
                            )
                        )
                    )
                except Exception as e:
                    sentry_sdk.capture_exception(e)
                    workplace = None
                if workplace:
                    full_description += i18n.get(
                        "inline-student-awp-in",
                        nickname=student.login,
                        cluster=workplace.clusterName,
                        row=workplace.row,
                        number=workplace.number,
                    )
                else:
                    full_description += i18n.get(
                        "inline-student-awp-out", nickname=student.login
                    )

                invited_user = await container.user_service.get_by_nickname(
                    student.login
                )
                if invited_user and invited_user.is_invited:
                    full_description += i18n.get("inline-student-already-invited")
                    keyboard = None
                else:
                    full_description += i18n.get("inline-student-can-invite")

                    keyboard = InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text=i18n.get("btn-invite", nickname=student.login),
                                    callback_data=InviteStudent(
                                        invited_login=student.login,
                                    ).pack(),
                                )
                            ]
                        ]
                    )
            else:
                full_description += i18n.get("inline-student-unregistered")
                keyboard = register_keyboard

            results = [
                InlineQueryResultArticle(
                    id=student.login,
                    title=title,
                    description=short_description,
                    input_message_content=InputTextMessageContent(
                        message_text=full_description
                    ),
                    reply_markup=keyboard,
                )
            ]

    await query.answer(results, is_personal=True, cache_time=30)
