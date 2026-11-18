from uuid import uuid4

import pytest

from app.db.models import Notification
from app.schemas.notifications import MarkRead, Notifications
from app.seed import demo_id
from tests.conftest import API, COOKIE, assert_contract, assert_error, csrf, sign_in

pytestmark = pytest.mark.integration


async def test_notifications_require_session(client):
    assert_error(await client.get(API + "/notifications"), 401, "UNAUTHORIZED")
    assert_error(await client.post(API + f"/notifications/{uuid4()}/read"), 401, "UNAUTHORIZED")


async def test_notifications_match_contract(student_client):
    assert_contract(await student_client.get(API + "/notifications"), 200, Notifications)


async def test_notification_read_is_idempotent(client, client_factory, settings, secrets):
    await sign_in(client, "demo.alina", secrets["demo.alina"])
    headers = await csrf(client)
    initial = assert_contract(
        await client.get(API + "/notifications?unread_only=true&page_size=1"), 200, Notifications
    )
    item = initial["items"][0]
    assert item["read_at"] is None and initial["unread_count"] > 1
    path = API + f"/notifications/{item['id']}/read"
    body = assert_contract(await client.post(path, headers=headers), 200, MarkRead)
    assert body["is_read"]
    assert (await client.post(path, headers=headers)).json() == body
    assert_error(
        await client.post(API + "/notifications/invalid/read", headers=headers),
        422,
        "VALIDATION_ERROR",
    )
    assert_error(
        await client.get(API + "/notifications?unread_only=other"), 422, "VALIDATION_ERROR"
    )
    async with client_factory(settings) as reopened:
        await sign_in(reopened, "demo.alina", secrets["demo.alina"])
        refreshed = (await reopened.get(API + "/notifications")).json()
        assert refreshed["unread_count"] == initial["unread_count"] - 1
        assert (
            next(x["read_at"] for x in refreshed["items"] if x["id"] == item["id"])
            == body["read_at"]
        )


async def test_missing_and_foreign_notifications_are_equal(client, secrets):
    await sign_in(client, "demo.alina", secrets["demo.alina"])
    headers = await csrf(client)
    paths = [
        f"{API}/notifications/{identifier}/read"
        for identifier in (demo_id("mark-exam-notice"), uuid4())
    ]
    errors = [
        assert_error(await client.post(path, headers=headers), 404, "NOT_FOUND") for path in paths
    ]
    assert errors[0]["message"] == errors[1]["message"]
    assert client.cookies.get(COOKIE)


async def test_student_cannot_mark_foreign_notification_read(client, secrets, database):
    await sign_in(client, "demo.alina", secrets["demo.alina"])
    notice_id = demo_id("mark-exam-notice")
    path = f"{API}/notifications/{notice_id}/read"
    assert_error(await client.post(path, headers=await csrf(client)), 404, "NOT_FOUND")
    async with database.begin() as db:
        record = await db.get(Notification, notice_id)
        assert record is not None and record.read_at is None
        own = await db.get(Notification, demo_id("alina-exam-notice"))
        assert own is not None
        own.target_type = "request"
        own.target_id = demo_id("mark-request-0")
    items = (await client.get(API + "/notifications")).json()["items"]
    assert (
        next(item["target"] for item in items if item["id"] == str(demo_id("alina-exam-notice")))
        is None
    )
