from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import contains_eager, selectinload

from app.db.dao.basedao import BaseDAO
from app.db.models import Course, Enrollment, Offering


class StudyDAO(BaseDAO):
    async def list_enrollments_with_grades(self, student_id: UUID) -> list[Enrollment]:
        statement = (
            select(Enrollment)
            .join(Offering)
            .join(Course)
            .where(
                Enrollment.student_id == student_id,
            )
            .options(
                contains_eager(Enrollment.offering).contains_eager(Offering.course),
                selectinload(Enrollment.grades),
            )
            .order_by(Course.title, Offering.id)
        )
        return list(await self.session.scalars(statement))
