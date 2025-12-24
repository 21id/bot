from app.bootstrap import Container
from app.infrastructure.s21.v1.models.responses.student import ParticipantV1DTO
from app.bot.routers.user.invite.callback import InviteStudent
from app.bot.routers.user.search.router import router
from app.bot.routers.user.registration.keyboards import (student_deeplink as
                                                         student_deeplink_kb)

from aiogram import Bot
from aiogram.types import InlineQuery, InlineQueryResultArticle, \
    InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton


@router.inline_query()
async def inline_query(query: InlineQuery, container: Container, bot: Bot) -> None:
    """Searching user by his Platform's nickname."""

    # Getting every student that contains nickname
    partial_nickname = query.query
    if not partial_nickname:
        return

    users = container.user_service.search_by_nickname(partial_nickname)

    results = []
    async for user in users:
        title = f"👤 {user.nickname}: 21ID 🪪"

        short_description = (
            f"Student at {user.campus.short_name}, wave {user.wave_name}"
        )

        full_description = (
            f"👤 {user.nickname} is a student at {user.campus.short_name}, "
            f"wave {user.wave_name}"
        )

        # Notifying that user is logged in the AWP
        workplace = await container.s21api_client.get_student_workplace_by_nickname(
            user.nickname)
        if workplace:
            full_description += (
                f"\n🖥 {user.nickname} is currently logged in cluster"
                f" {workplace.clusterName} on {workplace.row}.{workplace.number}"
            )

        # If user is verified, means he contacted the bot and bot can send links to him
        if user.is_verified:
            full_description += (
                "\n\nBecause he's registered in 21ID, you can try sending a "
                "notification to him, using button below"
            )

        # Checking if there is Telegram userid associated with user
        if user.telegram_id:
            # If it is - create contact keyboard
            chat_info = await bot.get_chat(user.telegram_id)
            if not chat_info.has_private_forwards:
                keyboard = student_deeplink_kb.get(chat_id=user.telegram_id)
            else:
                keyboard = student_deeplink_kb.get(nickname=user.nickname)
        else:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[[
                    InlineKeyboardButton(
                        text="❌ Isn't registered in 21ID",
                        callback_data="none",
                    )
                ]]
            )

        results.append(InlineQueryResultArticle(
            id=user.nickname,
            title=title,
            description=short_description,
            input_message_content=InputTextMessageContent(
                message_text=full_description
            ),
            reply_markup=keyboard
        ))

    if len(results) == 0:
        student = await container.s21api_client.get_student_by_nickname(
            partial_nickname)

        # If this nickname really belongs to a student - offer user to invite
        # him to 21ID
        if not isinstance(student, ParticipantV1DTO):
            short_description = f"Can't find student by nickname '{partial_nickname}'"

            full_description = (
                f"Nickname '{partial_nickname}' (even if it's partial) doesn't belong to "
                f"any student or 21ID user"
            )

            results = [
                InlineQueryResultArticle(
                    id="none",
                    title="Not found!",
                    description=short_description,
                    input_message_content=InputTextMessageContent(
                        message_text=full_description
                    )
                )
            ]

        else:
            title = f"🎓 {student.login}"

            short_description = (
                f"Student at {student.campus.short_name}, wave {student.className}"
            )

            full_description = (
                f"🎓 {student.login} is a student at {student.campus.short_name}, "
                f"wave {student.className}"
            )

            # Notifying that user is logged in the AWP
            workplace = await container.s21api_client.get_student_workplace_by_nickname(
                student.login)
            if workplace:
                full_description += (
                    f"\n🖥 {student.login} is currently logged in "
                    f"cluster {workplace.clusterName} on {workplace.row}"
                    f".{workplace.number}"
                )

            full_description += (
                "\n\n❌ Because he isn't registered in 21ID, you can't contact him "
                "right away.\n\n🪪 But you are more than welcome to invite him to 21ID "
                "by using the button below - we would send him a notification that "
                "you're looking for him"
            )

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[[
                    InlineKeyboardButton(
                        text=f"🪪 Invite {student.login} to 21ID",
                        callback_data=InviteStudent(
                            invited_login=student.login,
                        ).pack(),
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

    # Setting is_personal and cache_time so Telegram servers do not cache results
    await query.answer(results, is_personal=True, cache_time=0)
