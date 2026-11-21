from unittest.mock import AsyncMock

from sqlalchemy.exc import OperationalError

from app import celery_app


def test_beat_schedules_the_reminder_task():
    entry = celery_app.app.conf.beat_schedule["exam-reminders"]
    assert entry["task"] == celery_app.exam_reminders.name
    assert entry["schedule"] == entry["options"]["expires"] == 60


def test_task_retries_a_temporary_database_error(monkeypatch):
    transient = OperationalError(None, None, OSError("database unavailable"))
    run = AsyncMock(side_effect=[transient, 2])
    monkeypatch.setattr(celery_app, "run_exam_reminders", run)

    result = celery_app.exam_reminders.apply(throw=False)

    assert result.get() == 2
    assert run.await_count == 2
