import re
from unittest.mock import AsyncMock, MagicMock

from app.bot.routers.user.mass_invite.handlers.create import collect
from app.domain.mass_invite.mass_invite import MassInvite, parse_nicknames
from app.domain.mass_invite.service import MassInviteService


def test_parse_nicknames_splits_lowercases_dedupes():
    valid, invalid = parse_nicknames(" JDoe, kristana\nlilliank  jdoe,,daemonpr ")
    assert valid == ["jdoe", "kristana", "lilliank", "daemonpr"]
    assert invalid == []


def test_parse_nicknames_invalid():
    valid, invalid = parse_nicknames("ok, @bad, toolongnick, a1, ok@x.ru, @bad")
    assert valid == ["ok"]
    assert invalid == ["@bad", "toolongnick", "a1", "ok@x.ru"]


def test_parse_nicknames_empty():
    assert parse_nicknames(" , \n") == ([], [])


async def test_collect_accumulates(i18n):
    data: dict = {}
    state = MagicMock()
    state.get_value = AsyncMock(side_effect=lambda key: data.get(key))
    state.update_data = AsyncMock(side_effect=lambda **kw: data.update(kw))

    for text in ("jdoe, kristana", "Kristana, newbie, b@d"):
        message = MagicMock(text=text)
        message.reply = AsyncMock()
        await collect(message=message, state=state, i18n=i18n)

    assert data["mi_nicknames"] == ["jdoe", "kristana", "newbie"]
    assert message.reply.await_args.args[0] == i18n.get(
        "mass-invite-collected", added=1, total=3, invalid="b@d"
    )


async def test_create_link_payload_fits_deeplink():
    repo = MagicMock()
    repo.insert = AsyncMock()
    link = await MassInviteService(repo=repo).create(["jdoe"], created_by=1)

    payload = f"mi_{link.id}"
    assert len(payload) <= 64 and re.fullmatch(r"[A-Za-z0-9_-]+", payload)
    stored = repo.insert.await_args.args[0]
    assert stored["_id"] == link.id and "id" not in stored
    assert stored["used_by"] == {} and stored["nicknames"] == ["jdoe"]
    assert (link.expires_at - link.created_at).days == 30
    assert MassInvite(**stored) == link
