from uuid import UUID

from sqlalchemy import select

from app.db.dao.basedao import BaseDAO
from app.db.models import Group, Student


class StudentDAO(BaseDAO):
    async def get_profile_by_user_id(self, user_id: UUID) -> tuple[Student, Group] | None:
        row = (
            (
                await self.session.execute(
                    select(Student, Group).join(Group).where(Student.user_id == user_id)
                )
            )
            .tuples()
            .one_or_none()
        )
        return row
