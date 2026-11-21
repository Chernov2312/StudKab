import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from app.db.models import Exam, Offering, User
from app.schemas.notifications import MarkRead, Notifications
from app.seed import demo_id
from app.services.notification_service import create_exam_reminders
from tests.conftest import API, assert_contract, assert_error, csrf, sign_in

pytestmark = pytest.mark.integration
NOW = datetime(2026, 11, 19, 7, tzinfo=UTC)


async def test_exam_reminders_are_scoped_and_idempotent(
    database, student_client, client_factory, settings, secrets
):
    async with database.begin() as db:
        completed = await db.get_one(Exam, demo_id("alina-exam-1"))
        started = await db.get_one(Exam, demo_id("mark-exam-0"))
        later = await db.get_one(Exam, demo_id("mark-exam-1"))
        completed.scheduled_at = NOW + timedelta(hours=1)
        started.scheduled_at = NOW
        later.scheduled_at = NOW + timedelta(hours=24, seconds=1)

    async def run_reminders() -> int:
        async with database() as db:
            return await create_exam_reminders(db, NOW)

    path = API + "/notifications"
    before = assert_contract(await student_client.get(path), 200, Notifications)
    assert sorted(await asyncio.gather(run_reminders(), run_reminders())) == [0, 1]

    after = assert_contract(await student_client.get(path), 200, Notifications)
    assert after["unread_count"] == before["unread_count"] + 1
    assert after["pagination"]["total"] == before["pagination"]["total"] + 1
    reminder = after["items"][0]
    assert reminder["target"] == {"type": "exam", "id": str(demo_id("alina-exam-0"))}
    assert reminder["kind"] == "deadline"
    assert reminder["title"] == "Напоминание об экзамене"
    assert reminder["body"].endswith("20.11.2026 в 10:00 (МСК).")
    read_path = path + f"/{reminder['id']}/read"

    async with client_factory(settings) as other:
        await sign_in(other, "demo.mark", secrets["demo.mark"])
        other_feed = assert_contract(await other.get(path), 200, Notifications)
        assert other_feed["unread_count"] == 2
        assert_error(await other.post(read_path, headers=await csrf(other)), 404, "NOT_FOUND")

    read = assert_contract(
        await student_client.post(read_path, headers=await csrf(student_client)), 200, MarkRead
    )
    assert await run_reminders() == 0
    final = assert_contract(await student_client.get(path), 200, Notifications)
    assert final["unread_count"] == before["unread_count"]
    assert final["items"][0]["read_at"] == read["read_at"]


async def test_reminder_requires_an_active_student_in_the_current_term(database):
    async with database.begin() as db:
        user = await db.get_one(User, demo_id("alina"))
        user.active = False
    async with database() as db:
        assert await create_exam_reminders(db, NOW) == 1
    async with database.begin() as db:
        user = await db.get_one(User, demo_id("alina"))
        user.active = True
        exam = await db.get_one(Exam, demo_id("alina-exam-0"))
        offering = await db.get_one(Offering, exam.offering_id)
        offering.term = "previous"
    async with database() as db:
        assert await create_exam_reminders(db, NOW) == 0
