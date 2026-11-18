from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.core.domain import Assessment, ExamStatus
from app.schemas.common import DTO, CalendarDate


class ExamQuery(DTO):
    date_from: CalendarDate | None = Field(default=None, alias="from")
    date_to: CalendarDate | None = Field(default=None, alias="to")


class ExamItem(DTO):
    id: UUID
    offering_id: UUID
    course_title: str
    type: Assessment
    scheduled_at: datetime
    room: str
    status: ExamStatus
    grade: str | None


class Exams(DTO):
    items: list[ExamItem]
