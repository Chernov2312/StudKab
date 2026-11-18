from datetime import datetime
from uuid import UUID

from app.core.domain import Assessment, GradeKind, Result
from app.schemas.common import DTO


class Summary(DTO):
    passed: int
    total: int
    pending: int


class GradeItem(DTO):
    id: UUID
    kind: GradeKind
    value: str
    graded_at: datetime


class CourseResult(DTO):
    offering_id: UUID
    title: str
    assessment_type: Assessment
    result: Result
    final_grade: str | None
    grades: list[GradeItem]


class Study(DTO):
    summary: Summary
    courses: list[CourseResult]
