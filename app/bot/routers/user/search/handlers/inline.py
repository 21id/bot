import uuid

from app.bootstrap import Container
from app.infrastructure.s21.v1.models.responses.student import ParticipantV1DTO
from app.bot.routers.user.invite.callback import InviteStudent
from app.bot.routers.user.search.router import router
from app.bot.routers.user.registration.keyboards import (student_deeplink as
                                                         student_deeplink_kb)
from app.i18n.core import I18nContext

from aiogram import Bot, F
from aiogram.types import InlineQuery, InlineQueryResultArticle, \
    InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton


@router.inline_query(F.query.len() >= 4)
async def inline_query(
    query: InlineQuery, container: Container, bot: Bot, i18n: I18nContext
) -> None:
    """Searching user by his Platform's nickname."""
    invoke_user = await container.user_service.get_by_telegram_id(query.from_user.id)

    partial_nickname = query.query
    if not partial_nickname:
        return

    users = container.user_service.search_by_nickname(partial_nickname)

    results = []
    async for user in users:
        title = i18n.get("inline-title", nickname=user.nickname)
        short_description = i18n.get(
            "inline-short-desc", campus=user.campus.short_name, wave=user.wave_name
        )
        full_description = i18n.get(
            "inline-full-desc", nickname=user.nickname,
            campus=user.campus.short_name, wave=user.wave_name
        )

        if invoke_user:
            workplace = await container.s21api_client.get_student_workplace_by_nickname(
                user.nickname)
            if workplace:
                full_description += i18n.get(
                    "inline-awp-in", nickname=user.nickname,
                    cluster=workplace.clusterName,
                    row=workplace.row, number=workplace.number,
                )
            else:
                full_description += i18n.get("inline-awp-out", nickname=user.nickname)

            if user.is_verified:
                full_description += i18n.get("inline-verified")
            else:
                full_description += i18n.get("inline-not-verified")

            if user.telegram_id and user.is_verified:
                chat_info = await bot.get_chat(user.telegram_id)
                if not chat_info.has_private_forwards:
                    keyboard = student_deeplink_kb.get(chat_id=user.telegram_id,
                                                       nickname=user.nickname)
                else:
                    keyboard = student_deeplink_kb.get(nickname=user.nickname)
            else:
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[[
                        InlineKeyboardButton(
                            text=i18n.get("btn-cant-find-telegram"),
                            callback_data="none",
                        )
                    ]]
                )
        else:
            full_description += i18n.get("inline-unregistered-hint")

            bot_url = f"https://t.me/{(await query.bot.get_me()).username}"
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[[
                    InlineKeyboardButton(
                        text=i18n.get("btn-register-free"),
                        url=bot_url,
                    )
                ]]
            )

        results.append(InlineQueryResultArticle(
            id=uuid.uuid4().hex,
            title=title,
            description=short_description,
            input_message_content=InputTextMessageContent(
                message_text=full_description
            ),
            reply_markup=keyboard
        ))

    if len(results) == 0:
        student = await container.s21api_client.get_student_by_nickname(partial_nickname)

        if not isinstance(student, ParticipantV1DTO):
            results = [
                InlineQueryResultArticle(
                    id="none",
                    title=i18n.get("inline-not-found-title"),
                    description=i18n.get("inline-not-found-short", nickname=partial_nickname),
                    input_message_content=InputTextMessageContent(
                        message_text=i18n.get("inline-not-found-full", nickname=partial_nickname)
                    )
                )
            ]
        else:
            title = i18n.get("inline-student-title", nickname=student.login)
            short_description = i18n.get(
                "inline-student-short",
                campus=student.campus.short_name, wave=student.className
            )
            full_description = i18n.get(
                "inline-student-full", nickname=student.login,
                campus=student.campus.short_name, wave=student.className
            )

            if invoke_user:
                workplace = await container.s21api_client.get_student_workplace_by_nickname(
                    student.login)
                if workplace:
                    full_description += i18n.get(
                        "inline-student-awp-in", nickname=student.login,
                        cluster=workplace.clusterName,
                        row=workplace.row, number=workplace.number,
                    )
                else:
                    full_description += i18n.get(
                        "inline-student-awp-out", nickname=student.login
                    )

                full_description += i18n.get("inline-student-can-invite")

                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[[
                        InlineKeyboardButton(
                            text=i18n.get("btn-invite", nickname=student.login),
                            callback_data=InviteStudent(
                                invited_login=student.login,
                            ).pack(),
                        )
                    ]]
                )
            else:
                full_description += i18n.get("inline-student-unregistered")

                bot_url = f"https://t.me/{(await query.bot.get_me()).username}"
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[[
                        InlineKeyboardButton(
                            text=i18n.get("btn-register-free"),
                            url=bot_url,
                        )
                    ]]
                )

            results = [
                InlineQueryResultArticle(
                    id=student.login,
                    title=title,
                    description=short_description,
                    input_message_content=InputTextMessageContent(
                        message_text=full_description
                    ),
                    reply_markup=keyboard
                )
            ]

    await query.answer(results, is_personal=True, cache_time=0)
