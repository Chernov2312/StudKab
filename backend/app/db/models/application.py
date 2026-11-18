from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.domain import ApplicationStatus
from app.db.models.base import Base, CreatedAt, Id, choice


class RequestType(Base):
    __tablename__ = "request_types"
    __table_args__ = (
        CheckConstraint("comment_max_length BETWEEN 1 AND 1000", name="comment_max_length"),
    )

    id: Mapped[Id]
    code: Mapped[str] = mapped_column(String(64), unique=True)
    title: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text)
    fields_schema: Mapped[dict[str, object]] = mapped_column(JSONB)
    comment_required: Mapped[bool]
    comment_max_length: Mapped[int]


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (Index("ix_applications_student_time", "student_id", "created_at", "id"),)

    id: Mapped[Id]
    student_id: Mapped[UUID] = mapped_column(ForeignKey("students.user_id"))
    type_id: Mapped[UUID] = mapped_column(ForeignKey("request_types.id"))
    status: Mapped[ApplicationStatus] = mapped_column(choice(ApplicationStatus, "status"))
    fields: Mapped[dict[str, object]] = mapped_column(JSONB)
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[CreatedAt]
    updated_at: Mapped[CreatedAt]
    request_type: Mapped[RequestType] = relationship(lazy="raise")


class ApplicationEvent(Base):
    __tablename__ = "application_events"
    __table_args__ = (
        Index("ix_application_events_application_time", "application_id", "created_at", "id"),
    )

    id: Mapped[Id]
    application_id: Mapped[UUID] = mapped_column(ForeignKey("applications.id"))
    from_status: Mapped[ApplicationStatus | None] = mapped_column(
        choice(ApplicationStatus, "from_status")
    )
    to_status: Mapped[ApplicationStatus] = mapped_column(choice(ApplicationStatus, "to_status"))
    note: Mapped[str] = mapped_column(Text)
    actor_user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[CreatedAt]
