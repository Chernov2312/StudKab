from datetime import date, datetime
from typing import Literal
from uuid import UUID

from app.core.domain import ChangeKind, LessonStatus, LessonType
from app.schemas.common import DTO, CalendarDate

ScheduleView = Literal["today", "week"]


class ScheduleQuery(DTO):
    view: ScheduleView = "today"
    date: CalendarDate | None = None
    lesson_id: UUID | None = None


class DateRange(DTO):
    start_date: date
    end_date: date


class CourseInfo(DTO):
    id: UUID
    title: str


class InstructorInfo(DTO):
    display_name: str


class LessonSlot(DTO):
    starts_at: datetime
    ends_at: datetime
    room: str


class Change(DTO):
    kind: ChangeKind
    changed_at: datetime
    before: LessonSlot
    after: LessonSlot | None


class LessonItem(LessonSlot):
    id: UUID
    course: CourseInfo
    lesson_type: LessonType
    instructor: InstructorInfo
    status: LessonStatus
    change: Change | None


class Schedule(DTO):
    view: ScheduleView
    timezone: Literal["Europe/Moscow"] = "Europe/Moscow"
    range: DateRange
    items: list[LessonItem]
