from uuid import UUID

from app.schemas.common import DTO


class GroupInfo(DTO):
    id: UUID
    name: str


class Profile(DTO):
    full_name: str
    faculty: str
    program: str
    course_year: int
    group: GroupInfo
