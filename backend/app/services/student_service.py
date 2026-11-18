from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ApiError
from app.db.dao.student_dao import StudentDAO
from app.schemas.profile import GroupInfo, Profile


@dataclass(frozen=True)
class StudentScope:
    user_id: UUID
    group_id: UUID
    profile: Profile


async def get_profile(db: AsyncSession, user_id: UUID) -> StudentScope:
    record = await StudentDAO(db).get_profile_by_user_id(user_id)
    if record is None:
        raise ApiError("FORBIDDEN")
    student, group = record
    return StudentScope(
        user_id=student.user_id,
        group_id=group.id,
        profile=Profile(
            full_name=student.full_name,
            faculty=student.faculty,
            program=student.program,
            course_year=student.course_year,
            group=GroupInfo.model_validate(group),
        ),
    )
