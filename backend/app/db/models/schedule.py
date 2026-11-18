from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.domain import Assessment, ChangeKind, LessonType
from app.db.models.base import Base, CreatedAt, Id, Timestamp, choice


class Instructor(Base):
    __tablename__ = "instructors"

    id: Mapped[Id]
    display_name: Mapped[str] = mapped_column(String(160))


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[Id]
    title: Mapped[str] = mapped_column(String(160))
    assessment_type: Mapped[Assessment] = mapped_column(choice(Assessment, "assessment_type"))


class Offering(Base):
    __tablename__ = "course_offerings"

    id: Mapped[Id]
    course_id: Mapped[UUID] = mapped_column(ForeignKey("courses.id"))
    group_id: Mapped[UUID] = mapped_column(ForeignKey("groups.id"), index=True)
    instructor_id: Mapped[UUID] = mapped_column(ForeignKey("instructors.id"))
    term: Mapped[str] = mapped_column(String(32))
    course: Mapped[Course] = relationship(lazy="raise")
    instructor: Mapped[Instructor] = relationship(lazy="raise")


class Lesson(Base):
    __tablename__ = "lessons"
    __table_args__ = (
        CheckConstraint("ends_at > starts_at", name="time_range"),
        Index("ix_lessons_offering_start", "offering_id", "starts_at"),
    )

    id: Mapped[Id]
    offering_id: Mapped[UUID] = mapped_column(ForeignKey("course_offerings.id"))
    starts_at: Mapped[Timestamp]
    ends_at: Mapped[Timestamp]
    room: Mapped[str] = mapped_column(String(80))
    lesson_type: Mapped[LessonType] = mapped_column(choice(LessonType, "lesson_type"))
    offering: Mapped[Offering] = relationship(lazy="raise")


class LessonChange(Base):
    __tablename__ = "lesson_changes"
    __table_args__ = (Index("ix_lesson_changes_lesson_time", "lesson_id", "changed_at"),)

    id: Mapped[Id]
    lesson_id: Mapped[UUID] = mapped_column(ForeignKey("lessons.id"))
    kind: Mapped[ChangeKind] = mapped_column(choice(ChangeKind, "kind"))
    old_values: Mapped[dict[str, str]] = mapped_column(JSONB)
    new_values: Mapped[dict[str, str] | None] = mapped_column(JSONB(none_as_null=True))
    changed_at: Mapped[CreatedAt]
