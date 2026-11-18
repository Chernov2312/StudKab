from datetime import UTC, datetime, timedelta

import pytest

from app.db.models import Lesson, LessonChange
from app.schemas.schedule import Schedule
from app.seed import demo_id
from tests.conftest import API, assert_contract, assert_error, sign_in

pytestmark = pytest.mark.integration


async def test_week_boundaries_and_lesson_changes(client, secrets, database):
    await sign_in(client, "demo.alina", secrets["demo.alina"])
    week = assert_contract(
        await client.get(API + "/schedule?view=week&date=2026-11-22"), 200, Schedule
    )
    assert week["range"] == {"start_date": "2026-11-16", "end_date": "2026-11-22"}
    moved, cancelled = week["items"][:2]
    assert moved["status"] == "moved" and moved["change"]["before"]["room"] == "А-101"
    assert moved["change"]["after"]["room"] == "Б-204"
    assert datetime.fromisoformat(moved["starts_at"]).hour == 7
    assert cancelled["status"] == "cancelled" and cancelled["change"]["after"] is None
    next_week = (await client.get(API + "/schedule?view=week&date=2026-11-23")).json()
    assert next_week["range"]["start_date"] == "2026-11-23" and next_week["items"] == []
    target = (await client.get(API + f"/schedule?lesson_id={moved['id']}")).json()
    assert target["range"]["start_date"] == "2026-11-18"
    assert any(item["id"] == moved["id"] for item in target["items"])

    lesson_id = demo_id("alina-lesson-0-0")
    async with database.begin() as db:
        lesson = await db.get(Lesson, lesson_id)
        assert lesson is not None
        lesson.starts_at += timedelta(days=6)
        lesson.ends_at += timedelta(days=6)
        db.add(
            LessonChange(
                lesson_id=lesson_id,
                kind="moved",
                old_values=moved["change"]["after"],
                new_values={
                    "starts_at": lesson.starts_at.isoformat(),
                    "ends_at": lesson.ends_at.isoformat(),
                    "room": lesson.room,
                },
                changed_at=datetime(2026, 11, 19, 7, tzinfo=UTC),
            )
        )
    link = await client.get(API + f"/schedule?view=week&lesson_id={lesson_id}")
    assert link.status_code == 200
    assert link.json()["range"]["start_date"] == "2026-11-23"
    assert link.json()["items"][0]["id"] == str(lesson_id)
    for query in ("view=month", "date=november", f"date=2026-11-18&lesson_id={moved['id']}"):
        assert_error(await client.get(API + "/schedule?" + query), 422, "VALIDATION_ERROR")


async def test_schedule_scoped_to_group(client, client_factory, settings, secrets):
    await sign_in(client, "demo.alina", secrets["demo.alina"])
    foreign = demo_id("mark-lesson-0-0")
    assert_error(await client.get(API + f"/schedule?lesson_id={foreign}"), 404, "NOT_FOUND")
    assert_error(
        await client.get(API + f"/schedule?group_id={demo_id('ПМИ-31')}"), 422, "VALIDATION_ERROR"
    )
    async with client_factory(settings) as other:
        await sign_in(other, "demo.mark", secrets["demo.mark"])
        first = (await client.get(API + "/schedule")).json()["items"]
        second = (await other.get(API + "/schedule")).json()["items"]
        assert first and second
        assert {item["course"]["id"] for item in first}.isdisjoint(
            item["course"]["id"] for item in second
        )


async def test_schedule_requires_session(client):
    assert_error(await client.get(API + "/schedule"), 401, "UNAUTHORIZED")


async def test_schedule_validation_error_matches_openapi(client):
    response = await client.get("/api/openapi.json")
    assert response.status_code == 200
    spec = response.json()
    assert spec["paths"][API + "/schedule"]["get"]["responses"]["422"]["content"][
        "application/json"
    ]["schema"]["$ref"].endswith("/ValidationErrorResponse")
