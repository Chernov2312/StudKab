from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base, Id


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[Id]
    name: Mapped[str] = mapped_column(String(64), unique=True)


class Student(Base):
    __tablename__ = "students"
    __table_args__ = (CheckConstraint("course_year BETWEEN 1 AND 6", name="course_year"),)

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    full_name: Mapped[str] = mapped_column(String(160))
    faculty: Mapped[str] = mapped_column(String(160))
    program: Mapped[str] = mapped_column(String(160))
    course_year: Mapped[int]
    group_id: Mapped[UUID] = mapped_column(ForeignKey("groups.id"), index=True)
