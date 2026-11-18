from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select, update

from app.core.security import digest
from app.db.models import Session
from app.schemas.auth import CSRF, LoginOutput, Me
from tests.conftest import API, COOKIE, ORIGIN, assert_contract, assert_error, csrf, sign_in

pytestmark = pytest.mark.integration


async def test_login_and_me_for_two_students(client, client_factory, settings, secrets, database):
    response = await sign_in(client, "demo.alina", secrets["demo.alina"])
    login = assert_contract(response, 200, LoginOutput)
    assert set(login["user"]) == {"id", "username", "role"}
    assert set(login["session"]) == {"expires_at"}
    assert datetime.fromisoformat(login["session"]["expires_at"]).tzinfo is not None
    cookie = response.headers["set-cookie"]
    for flag in ("__Host-session=", "HttpOnly", "Secure", "SameSite=lax", "Path=/", "Max-Age="):
        assert flag in cookie
    token = client.cookies.get(COOKIE)
    assert token not in response.text
    async with database() as db:
        row = await db.scalar(select(Session).where(Session.token_hash == digest(token)))
        assert row is not None and row.token_hash != token
    async with client_factory(settings) as other:
        await sign_in(other, "demo.mark", secrets["demo.mark"])
        alina = assert_contract(await client.get(API + "/auth/me"), 200, Me)
        mark = assert_contract(await other.get(API + "/auth/me"), 200, Me)
        assert alina["student"]["full_name"] == "Алина Тестова"
        assert mark["student"]["full_name"] == "Марк Примеров"
        assert alina["student"]["group"] != mark["student"]["group"]


async def test_login_wrong_password_and_rate_limit(client_factory, settings, secrets):
    config = settings.model_copy(update={"login_username_limit": 3})
    async with client_factory(config) as first, client_factory(config) as second:
        for active in (first, second):
            result = await active.post(
                API + "/auth/login",
                headers={"Origin": ORIGIN},
                json={
                    "username": "demo.alina",
                    "password": secrets["demo.mark"],
                },
            )
            assert_error(result, 401, "INVALID_CREDENTIALS")
        nonexistent = await second.post(
            API + "/auth/login",
            headers={"Origin": ORIGIN},
            json={
                "username": "nonexistent",
                "password": secrets["demo.mark"],
            },
        )
        assert_error(nonexistent, 401, "INVALID_CREDENTIALS")
        await sign_in(first, "demo.alina", secrets["demo.alina"])
        last = await second.post(
            API + "/auth/login",
            headers={"Origin": ORIGIN},
            json={
                "username": "demo.alina",
                "password": secrets["demo.alina"],
            },
        )
        assert_error(last, 429, "RATE_LIMITED")
        assert int(last.headers["Retry-After"]) > 0


async def test_login_validates_origin_and_body(client, secrets):
    credentials = {"username": "demo.alina", "password": secrets["demo.alina"]}
    assert_error(await client.post(API + "/auth/login", json=credentials), 403, "ORIGIN_FORBIDDEN")
    wrong_media = await client.post(
        API + "/auth/login", data=credentials, headers={"Origin": ORIGIN}
    )
    assert_error(wrong_media, 422, "VALIDATION_ERROR")
    valid_media = {"Origin": ORIGIN, "Content-Type": "application/json"}
    invalid_json = await client.post(API + "/auth/login", content="{", headers=valid_media)
    assert_error(invalid_json, 422, "VALIDATION_ERROR")
    oversized = await client.post(API + "/auth/login", content="x" * 17000, headers=valid_media)
    assert_error(oversized, 413, "PAYLOAD_TOO_LARGE")


async def test_logout_revokes_session(client, secrets, database):
    await sign_in(client, "demo.alina", secrets["demo.alina"])
    old = client.cookies.get(COOKIE)
    await sign_in(client, "demo.alina", secrets["demo.alina"])
    previous = await client.get(API + "/auth/me", headers={"Cookie": f"{COOKIE}={old}"})
    assert_error(previous, 401, "UNAUTHORIZED")
    token = client.cookies.get(COOKIE)
    logout = await client.post(API + "/auth/logout", headers=await csrf(client))
    assert logout.status_code == 204 and logout.content == b""
    assert client.cookies.get(COOKIE) is None
    assert_error(
        await client.get(API + "/auth/me", headers={"Cookie": f"{COOKIE}={token}"}),
        401,
        "UNAUTHORIZED",
    )
    await sign_in(client, "demo.mark", secrets["demo.mark"])
    async with database.begin() as db:
        await db.execute(
            update(Session)
            .where(Session.token_hash == digest(client.cookies.get(COOKIE)))
            .values(
                expires_at=datetime.now(UTC) - timedelta(seconds=1),
            )
        )
    assert_error(await client.get(API + "/auth/me"), 401, "UNAUTHORIZED")


async def test_auth_requires_session(client):
    for path in ("/auth/me", "/auth/csrf"):
        assert_error(await client.get(API + path), 401, "UNAUTHORIZED")
    assert_error(await client.post(API + "/auth/logout"), 401, "UNAUTHORIZED")


async def test_csrf_response_matches_contract(student_client):
    assert_contract(await student_client.get(API + "/auth/csrf"), 200, CSRF)


async def test_logout_requires_trusted_origin_and_empty_body(student_client):
    headers = await csrf(student_client)
    assert_error(
        await student_client.post(API + "/auth/logout", headers=headers, json={}),
        422,
        "VALIDATION_ERROR",
    )
    headers["Origin"] = "https://another.example"
    assert_error(
        await student_client.post(API + "/auth/logout", headers=headers), 403, "ORIGIN_FORBIDDEN"
    )
