from datetime import datetime
from uuid import UUID

from sqlalchemy import Select, select, true
from sqlalchemy.orm import aliased, joinedload

from app.db.dao.basedao import BaseDAO
from app.db.models import Lesson, LessonChange, Offering


class ScheduleDAO(BaseDAO):
    @staticmethod
    def _query(group_id: UUID) -> Select[tuple[Lesson, LessonChange]]:
        latest = (
            select(LessonChange)
            .where(
                LessonChange.lesson_id == Lesson.id,
            )
            .order_by(
                LessonChange.changed_at.desc(),
                LessonChange.id.desc(),
            )
            .limit(1)
            .correlate(Lesson)
            .lateral()
        )
        change = aliased(LessonChange, latest)
        return (
            select(Lesson, change)
            .join(Offering)
            .outerjoin(change, true())
            .where(
                Offering.group_id == group_id,
            )
            .options(
                joinedload(Lesson.offering).joinedload(Offering.course),
                joinedload(Lesson.offering).joinedload(Offering.instructor),
            )
        )

    async def list_for_group(
        self,
        group_id: UUID,
        start: datetime,
        end: datetime,
    ) -> list[tuple[Lesson, LessonChange | None]]:
        statement = (
            self._query(group_id)
            .where(
                Lesson.starts_at >= start,
                Lesson.starts_at < end,
            )
            .order_by(Lesson.starts_at, Lesson.id)
        )
        return list((await self.session.execute(statement)).tuples())

    async def get_for_group(
        self,
        lesson_id: UUID,
        group_id: UUID,
    ) -> tuple[Lesson, LessonChange | None] | None:
        return (
            (await self.session.execute(self._query(group_id).where(Lesson.id == lesson_id)))
            .tuples()
            .one_or_none()
        )
