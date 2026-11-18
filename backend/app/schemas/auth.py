from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.core.domain import Role
from app.schemas.common import DTO
from app.schemas.profile import Profile


class LoginInput(DTO):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=1, max_length=256)


class UserInfo(DTO):
    id: UUID
    username: str
    role: Role


class SessionInfo(DTO):
    expires_at: datetime


class LoginOutput(DTO):
    user: UserInfo
    session: SessionInfo


class Me(DTO):
    user: UserInfo
    student: Profile | None


class CSRF(DTO):
    csrf_token: str
