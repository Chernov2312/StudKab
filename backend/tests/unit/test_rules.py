from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.core.domain import Assessment, Result
from app.core.exceptions import ApiError
from app.services.health_service import ready
from app.services.schedule_service import bounds
from app.services.study_service import assessment_result


@pytest.mark.parametrize(
    ("kind", "grade", "expected"),
    [
        (Assessment.EXAM, None, Result.PENDING),
        (Assessment.EXAM, "2", Result.FAILED),
        (Assessment.EXAM, "3", Result.PASSED),
        (Assessment.PASS_FAIL, " ЗАЧЁТ ", Result.PASSED),
        (Assessment.PASS_FAIL, "незачёт", Result.FAILED),
    ],
)
def test_assessment_rules(kind, grade, expected):
    assert assessment_result(kind, grade) == expected


def test_calendar_week_is_moscow_monday_to_sunday():
    period, start, end = bounds(date(2026, 11, 22), "week")
    assert period.start_date == date(2026, 11, 16)
    assert period.end_date == date(2026, 11, 22)
    assert start.isoformat() == "2026-11-16T00:00:00+03:00"
    assert end.isoformat() == "2026-11-23T00:00:00+03:00"


def test_production_requires_https():
    with pytest.raises(ValueError, match="requires HTTPS"):
        Settings(app_env="production", app_origin="http://puls.test")


async def test_ready_translates_db_failure(monkeypatch):
    async def offline(self, *args):
        raise OSError("internal connection detail")

    monkeypatch.setattr(AsyncSession, "execute", offline)
    async with async_sessionmaker()() as db:
        with pytest.raises(ApiError) as error:
            await ready(db)
    assert error.value.code == "SERVICE_UNAVAILABLE"
