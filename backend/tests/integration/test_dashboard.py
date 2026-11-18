import pytest

from app.schemas.dashboard import Dashboard
from tests.conftest import API, assert_contract, assert_error, csrf

pytestmark = pytest.mark.integration


async def test_dashboard_requires_session(client):
    assert_error(await client.get(API + "/dashboard"), 401, "UNAUTHORIZED")


async def test_dashboard_matches_contract(student_client):
    dashboard = assert_contract(await student_client.get(API + "/dashboard"), 200, Dashboard)
    assert dashboard["greeting_name"] == "Алина"
    assert dashboard["next_lesson"]["status"] == "moved"
    assert dashboard["active_requests_count"] == 1
    assert 1 <= len(dashboard["focus"]) <= 3
    assert {item["target"]["type"] for item in dashboard["focus"]} >= {"schedule", "exam"}


async def test_dashboard_updates_unread_notification_count(student_client):
    client = student_client
    path = API + "/dashboard"
    initial = assert_contract(await client.get(path), 200, Dashboard)
    notifications = await client.get(API + "/notifications?unread_only=true&page_size=1")
    assert notifications.status_code == 200
    listing = notifications.json()
    assert listing["unread_count"] == initial["unread_notifications_count"]
    notice_id = listing["items"][0]["id"]
    read = await client.post(API + f"/notifications/{notice_id}/read", headers=await csrf(client))
    assert read.status_code == 200
    refreshed = assert_contract(await client.get(path), 200, Dashboard)
    assert refreshed["unread_notifications_count"] == listing["unread_count"] - 1
