import re
from unittest.mock import AsyncMock, patch

from app.infrastructure.s21.v1.client import S21APIClient
from app.infrastructure.s21.v1.models.auth.credentials import Credentials
from app.infrastructure.s21.v1.models.auth.session import Session
from app.infrastructure.s21.v1.models.errors.client_error import S21ClientError

import pytest
from aioresponses import aioresponses

BASE = "https://api.test/services/21-school/api"
AUTH = "https://auth.test"
REALM = "School21"
TOKEN_URL = f"{AUTH}/auth/realms/{REALM}/protocol/openid-connect/token"
STUDENT_URL = f"{BASE}/v1/participants/jdoe"
STUDENT = {
    "login": "jdoe",
    "className": "24_03_TAS",
    "parallelName": "Core program",
    "expValue": 100,
    "level": 1,
    "expToNextLevel": 300,
    "status": "ACTIVE",
    "campus": {"id": "c-uuid", "shortName": "TAS"},
}


@pytest.fixture
async def client():
    """Client with an existing session and password credentials."""
    c = S21APIClient(
        base_url=BASE,
        auth_url=AUTH,
        auth_realm=REALM,
        credentials=Credentials(login="bot", password="pw"),
        session=Session(access_token="old", refresh_token="refresh"),
    )
    yield c
    await c.close()


@pytest.fixture(autouse=True)
def no_sleep():
    """Skip retry back-off."""
    with patch("app.infrastructure.s21.v1.client.asyncio.sleep", AsyncMock()):
        yield


def test_requires_https():
    with pytest.raises(ValueError):
        S21APIClient(
            base_url="http://x", auth_url=AUTH, auth_realm=REALM, credentials=None
        )


async def test_get_student_ok_lowercases_nickname(client):
    with aioresponses() as m:
        m.get(STUDENT_URL, payload=STUDENT)
        student = await client.get_student_by_nickname("JDoe")
    assert student.login == "jdoe"
    assert student.campus.short_name == "TAS"


async def test_get_student_not_found(client):
    with aioresponses() as m:
        m.get(STUDENT_URL, status=404)
        assert await client.get_student_by_nickname("jdoe") is None


async def test_401_relogins_with_refresh_token(client):
    with aioresponses() as m:
        m.get(STUDENT_URL, status=401)
        m.post(TOKEN_URL, payload={"access_token": "new", "refresh_token": "r2"})
        m.get(STUDENT_URL, payload=STUDENT)
        student = await client.get_student_by_nickname("jdoe")

        token_calls = [k for k in m.requests if str(k[1]) == TOKEN_URL]
        body = m.requests[token_calls[0]][0].kwargs["data"]
    assert student.login == "jdoe"
    assert client.session.access_token == "new"
    assert body["grant_type"] == "refresh_token"


async def test_401_falls_back_to_password_login(client):
    with aioresponses() as m:
        m.get(STUDENT_URL, status=401)
        m.post(TOKEN_URL, status=400, body="invalid_grant")
        m.post(TOKEN_URL, payload={"access_token": "pw-new", "refresh_token": "r"})
        m.get(STUDENT_URL, payload=STUDENT)
        await client.get_student_by_nickname("jdoe")
    assert client.session.access_token == "pw-new"


async def test_401_twice_raises(client):
    with aioresponses() as m:
        m.get(STUDENT_URL, status=401)
        m.post(TOKEN_URL, payload={"access_token": "new", "refresh_token": "r2"})
        m.get(STUDENT_URL, status=401)
        with pytest.raises(S21ClientError):
            await client.get_student_by_nickname("jdoe")


async def test_relogin_skipped_when_token_already_refreshed(client):
    client.session = Session(access_token="fresh", refresh_token="r")
    with aioresponses():
        # No token endpoint registered: any login attempt would fail
        await client.relogin(expired_token="old")
    assert client.session.access_token == "fresh"


async def test_500_retried_once(client):
    with aioresponses() as m:
        m.get(STUDENT_URL, status=500)
        m.get(STUDENT_URL, payload=STUDENT)
        student = await client.get_student_by_nickname("jdoe")
    assert student.login == "jdoe"


async def test_500_twice_raises_api_side_error(client):
    with aioresponses() as m:
        m.get(STUDENT_URL, status=500)
        m.get(STUDENT_URL, status=502)
        with pytest.raises(S21ClientError) as exc:
            await client.get_student_by_nickname("jdoe")
    assert "School 21 API side" in exc.value.client_message
    assert exc.value.support_details["status"] == 502
    # Retry hits the same URL, base URL isn't nested
    assert exc.value.support_details["url"] == STUDENT_URL


async def test_429_raises_rate_limit_error(client):
    with aioresponses() as m:
        m.get(STUDENT_URL, status=429, payload={"message": "slow down"})
        with pytest.raises(S21ClientError) as exc:
            await client.get_student_by_nickname("jdoe")
    assert "429" in exc.value.client_message


async def test_403_raises(client):
    with aioresponses() as m:
        m.get(STUDENT_URL, status=403, body="forbidden")
        with pytest.raises(S21ClientError):
            await client.get_student_by_nickname("jdoe")


async def test_workstation_empty_body_is_none(client):
    with aioresponses() as m:
        m.get(f"{STUDENT_URL}/workstation", status=200, body="")
        assert await client.get_student_workplace_by_nickname("jdoe") is None


async def test_workstation_ok(client):
    with aioresponses() as m:
        m.get(
            f"{STUDENT_URL}/workstation",
            payload={"clusterId": 1, "clusterName": "oasis", "row": "a", "number": 3},
        )
        ws = await client.get_student_workplace_by_nickname("jdoe")
    assert ws.clusterName == "oasis"


async def test_login_invalid_credentials(client):
    with aioresponses() as m:
        m.post(TOKEN_URL, status=401)
        with pytest.raises(S21ClientError) as exc:
            await client.login(login="a", password="b")
    assert exc.value.notify_user is False


async def test_login_missing_tokens(client):
    with aioresponses() as m:
        m.post(TOKEN_URL, payload={"access_token": "only"})
        with pytest.raises(S21ClientError):
            await client.login(login="a", password="b")


async def test_from_credentials_logs_in():
    with aioresponses() as m:
        m.post(
            re.compile(re.escape(TOKEN_URL)),
            payload={"access_token": "a", "refresh_token": "r"},
        )
        c = await S21APIClient.from_credentials(
            BASE, AUTH, REALM, Credentials(login="bot", password="pw")
        )
    assert c.session.access_token == "a"
    await c.close()
