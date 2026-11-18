from datetime import date, datetime
from typing import Literal
from uuid import UUID

from app.core.domain import LessonStatus, NotificationKind
from app.schemas.common import DTO, Target
from app.schemas.study import Summary


class NextLesson(DTO):
    id: UUID
    title: str
    starts_at: datetime
    room: str
    status: LessonStatus


class NextExam(DTO):
    id: UUID
    course_title: str
    scheduled_at: datetime


class Focus(DTO):
    kind: NotificationKind
    title: str
    description: str
    target: Target
    priority: Literal["high", "normal"]


class Dashboard(DTO):
    date: date
    timezone: Literal["Europe/Moscow"] = "Europe/Moscow"
    greeting_name: str
    next_lesson: NextLesson | None
    study: Summary
    active_requests_count: int
    unread_notifications_count: int
    next_exam: NextExam | None
    focus: list[Focus]
