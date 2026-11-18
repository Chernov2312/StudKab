from datetime import date, datetime, time, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain import MOSCOW, ChangeKind, LessonStatus, utcnow
from app.core.exceptions import ApiError, validation
from app.db.dao.schedule_dao import ScheduleDAO
from app.db.models import Lesson, LessonChange
from app.schemas.schedule import (
    Change,
    CourseInfo,
    DateRange,
    InstructorInfo,
    LessonItem,
    LessonSlot,
    Schedule,
    ScheduleQuery,
    ScheduleView,
)


def bounds(day: date, view: ScheduleView) -> tuple[DateRange, datetime, datetime]:
    first = day - timedelta(days=day.weekday()) if view == "week" else day
    try:
        end = first + timedelta(days=7 if view == "week" else 1)
    except OverflowError:
        raise validation("date", "Дата вне допустимого диапазона") from None
    return (
        DateRange(start_date=first, end_date=end - timedelta(days=1)),
        datetime.combine(first, time.min, MOSCOW),
        datetime.combine(end, time.min, MOSCOW),
    )


def lesson_item(lesson: Lesson, change: LessonChange | None) -> LessonItem:
    history = None
    status = LessonStatus.SCHEDULED
    if change is not None:
        status = LessonStatus(change.kind)
        history = Change(
            kind=change.kind,
            changed_at=change.changed_at,
            before=LessonSlot.model_validate(change.old_values),
            after=LessonSlot.model_validate(change.new_values)
            if change.kind == ChangeKind.MOVED
            else None,
        )
    return LessonItem(
        id=lesson.id,
        course=CourseInfo.model_validate(lesson.offering.course),
        instructor=InstructorInfo.model_validate(lesson.offering.instructor),
        starts_at=lesson.starts_at,
        ends_at=lesson.ends_at,
        room=lesson.room,
        lesson_type=lesson.lesson_type,
        status=status,
        change=history,
    )


async def get_schedule(db: AsyncSession, group_id: UUID, query: ScheduleQuery) -> Schedule:
    dao = ScheduleDAO(db)
    day = query.date or utcnow().astimezone(MOSCOW).date()
    if query.lesson_id is not None:
        if query.date is not None:
            raise validation("date", "Для ссылки на занятие дата определяется сервером")
        record = await dao.get_for_group(query.lesson_id, group_id)
        if record is None:
            raise ApiError("NOT_FOUND")
        day = record[0].starts_at.astimezone(MOSCOW).date()
    period, start, end = bounds(day, query.view)
    return Schedule(
        view=query.view,
        range=period,
        items=[lesson_item(*row) for row in await dao.list_for_group(group_id, start, end)],
    )
