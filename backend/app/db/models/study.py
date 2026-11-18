from uuid import UUID

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.domain import Assessment, GradeKind
from app.db.models.base import Base, Id, Timestamp, choice
from app.db.models.schedule import Offering


class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (UniqueConstraint("student_id", "offering_id"),)

    id: Mapped[Id]
    student_id: Mapped[UUID] = mapped_column(ForeignKey("students.user_id"))
    offering_id: Mapped[UUID] = mapped_column(ForeignKey("course_offerings.id"))
    offering: Mapped[Offering] = relationship(lazy="raise")
    grades: Mapped[list["Grade"]] = relationship(
        lazy="raise", order_by=lambda: (Grade.graded_at, Grade.id)
    )


class Grade(Base):
    __tablename__ = "grades"

    id: Mapped[Id]
    enrollment_id: Mapped[UUID] = mapped_column(ForeignKey("enrollments.id"), index=True)
    kind: Mapped[GradeKind] = mapped_column(choice(GradeKind, "kind"))
    value: Mapped[str] = mapped_column(String(32))
    graded_at: Mapped[Timestamp]


class Exam(Base):
    __tablename__ = "exams"
    __table_args__ = (Index("ix_exams_offering_time", "offering_id", "scheduled_at"),)

    id: Mapped[Id]
    offering_id: Mapped[UUID] = mapped_column(ForeignKey("course_offerings.id"))
    scheduled_at: Mapped[Timestamp]
    room: Mapped[str] = mapped_column(String(80))
    exam_type: Mapped[Assessment] = mapped_column(choice(Assessment, "exam_type"))
