from sqlalchemy import Boolean, CheckConstraint, String, true
from sqlalchemy.orm import Mapped, mapped_column

from app.core.domain import Role
from app.db.models.base import Base, CreatedAt, Id, Timestamp, choice


class User(Base):
    __tablename__ = "users"

    id: Mapped[Id]
    username: Mapped[str] = mapped_column(String(64), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(choice(Role, "role"))
    active: Mapped[bool] = mapped_column(Boolean, server_default=true())
    created_at: Mapped[CreatedAt]


class LoginAttempt(Base):
    __tablename__ = "login_attempts"
    __table_args__ = (CheckConstraint("count > 0", name="positive_count"),)

    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    window: Mapped[Timestamp] = mapped_column(primary_key=True, index=True)
    count: Mapped[int]
