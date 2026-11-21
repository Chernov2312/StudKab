from datetime import datetime
from uuid import UUID

from sqlalchemy import Select, and_, func, or_, select, update
from sqlalchemy.dialects.postgresql import insert

from app.core.domain import DEMO_TERM, TargetType
from app.db.dao.basedao import BaseDAO
from app.db.models import Application, Enrollment, Exam, Lesson, Notification, Offering


class NotificationDAO(BaseDAO):
    async def insert_reminders(self, rows: list[dict[str, object]]) -> int:
        if not rows:
            return 0
        statement = (
            insert(Notification)
            .on_conflict_do_nothing(index_elements=[Notification.id])
            .returning(Notification.id)
        )
        return len((await self.session.scalars(statement, rows)).all())

    @staticmethod
    def _owned(student_id: UUID, unread_only: bool) -> Select[tuple[Notification]]:
        statement = select(Notification).where(Notification.student_id == student_id)
        if unread_only:
            statement = statement.where(Notification.read_at.is_(None))
        return statement

    async def list_for_student(
        self,
        student_id: UUID,
        group_id: UUID,
        unread_only: bool,
        offset: int,
        limit: int,
    ) -> list[tuple[Notification, bool]]:
        request_ok = (
            select(Application.id)
            .where(
                Application.id == Notification.target_id,
                Application.student_id == student_id,
            )
            .exists()
        )
        schedule_ok = (
            select(Lesson.id)
            .join(Offering)
            .where(
                Lesson.id == Notification.target_id,
                Offering.group_id == group_id,
            )
            .exists()
        )
        exam_ok = (
            select(Exam.id)
            .join(Offering, Offering.id == Exam.offering_id)
            .join(
                Enrollment,
                Enrollment.offering_id == Exam.offering_id,
            )
            .where(
                Exam.id == Notification.target_id,
                Enrollment.student_id == student_id,
                Offering.term == DEMO_TERM,
            )
            .exists()
        )
        valid_target = or_(
            and_(Notification.target_type == TargetType.REQUEST, request_ok),
            and_(Notification.target_type == TargetType.SCHEDULE, schedule_ok),
            and_(Notification.target_type == TargetType.EXAM, exam_ok),
        )
        statement = (
            self._owned(student_id, unread_only)
            .add_columns(valid_target)
            .order_by(
                Notification.created_at.desc(),
                Notification.id.desc(),
            )
            .offset(offset)
            .limit(limit)
        )
        return list((await self.session.execute(statement)).tuples())

    async def count_for_student(self, student_id: UUID, unread_only: bool) -> int:
        return (
            await self.session.scalar(
                select(func.count()).select_from(self._owned(student_id, unread_only).subquery())
            )
        ) or 0

    async def count_unread_for_student(self, student_id: UUID) -> int:
        return await self.count_for_student(student_id, True)

    async def mark_read_for_student(
        self,
        notification_id: UUID,
        student_id: UUID,
        now: datetime,
    ) -> datetime | None:
        return await self.session.scalar(
            update(Notification)
            .where(
                Notification.id == notification_id,
                Notification.student_id == student_id,
            )
            .values(read_at=func.coalesce(Notification.read_at, now))
            .returning(Notification.read_at)
        )
