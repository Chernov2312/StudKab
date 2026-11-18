from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.domain import NotificationKind, TargetType
from app.db.models.base import Base, CreatedAt, Id, Timestamp, choice


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        CheckConstraint("(target_type IS NULL) = (target_id IS NULL)", name="target_pair"),
        Index("ix_notifications_student_time", "student_id", "created_at", "id"),
    )

    id: Mapped[Id]
    student_id: Mapped[UUID] = mapped_column(ForeignKey("students.user_id"))
    kind: Mapped[NotificationKind] = mapped_column(choice(NotificationKind, "kind"))
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    target_type: Mapped[TargetType | None] = mapped_column(choice(TargetType, "target_type"))
    target_id: Mapped[UUID | None]
    created_at: Mapped[CreatedAt]
    read_at: Mapped[Timestamp | None]
