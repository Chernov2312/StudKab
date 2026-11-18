from datetime import UTC, datetime
from enum import StrEnum
from zoneinfo import ZoneInfo

MOSCOW = ZoneInfo("Europe/Moscow")
DEMO_TERM = "demo"


def utcnow() -> datetime:
    return datetime.now(UTC)


class Role(StrEnum):
    STUDENT = "student"
    STAFF = "staff"


class Assessment(StrEnum):
    EXAM = "exam"
    PASS_FAIL = "pass_fail"


class Result(StrEnum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"


class ExamStatus(StrEnum):
    PLANNED = "planned"
    PASSED = "passed"
    FAILED = "failed"


class LessonType(StrEnum):
    LECTURE = "lecture"
    PRACTICE = "practice"
    LAB = "lab"
    SEMINAR = "seminar"


class LessonStatus(StrEnum):
    SCHEDULED = "scheduled"
    MOVED = "moved"
    CANCELLED = "cancelled"


class ChangeKind(StrEnum):
    MOVED = "moved"
    CANCELLED = "cancelled"


class GradeKind(StrEnum):
    CURRENT = "current"
    FINAL = "final"


class ApplicationStatus(StrEnum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    READY = "ready"
    REJECTED = "rejected"


class NotificationKind(StrEnum):
    SCHEDULE_CHANGE = "schedule_change"
    APPLICATION_STATUS = "application_status"
    DEADLINE = "deadline"
    ANNOUNCEMENT = "announcement"


class TargetType(StrEnum):
    SCHEDULE = "schedule"
    EXAM = "exam"
    REQUEST = "request"
