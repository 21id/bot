import uuid

from app.bot.utilities.data_formatting import message_split

import pytest

TELEGRAM_LIMIT = 4096


@pytest.mark.parametrize("size", [0, 1, 3000, 3963, 3964, 10_000, 50_000])
def test_parts_fit_telegram_limit_and_roundtrip(size):
    uuid_ = str(uuid.uuid4())
    text = "".join(chr(ord("a") + i % 26) for i in range(size))
    parts = message_split(text=text, type_="error", uuid_=uuid_)

    assert all(len(p) <= TELEGRAM_LIMIT for p in parts)
    assert all(p.startswith(f"{uuid_} error ") for p in parts)
    prefix = len(f"{uuid_} error ")
    assert "".join(p[prefix:] for p in parts) == text


def test_respects_custom_max_size():
    parts = message_split(text="x" * 100, type_="t", uuid_="u", max_size=20)
    assert all(len(p) <= 20 for p in parts)
    assert len(parts) == 7
