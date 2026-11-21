from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.orm import contains_eager, selectinload

from app.core.domain import DEMO_TERM, Assessment, GradeKind, Role
from app.db.dao.basedao import BaseDAO
from app.db.models import Course, Enrollment, Exam, Grade, Offering, User


class ExamDAO(BaseDAO):
    async def upcoming_for_reminders(
        self, now: datetime, until: datetime
    ) -> list[tuple[UUID, UUID, str, datetime, Assessment]]:
        has_final_grade = (
            select(Grade.id)
            .where(Grade.enrollment_id == Enrollment.id, Grade.kind == GradeKind.FINAL)
            .exists()
        )
        statement = (
            select(Enrollment.student_id, Exam.id, Course.title, Exam.scheduled_at, Exam.exam_type)
            .join_from(Exam, Enrollment, Enrollment.offering_id == Exam.offering_id)
            .join(User, User.id == Enrollment.student_id)
            .join(Offering, Offering.id == Exam.offering_id)
            .join(Course)
            .where(
                User.active.is_(True),
                User.role == Role.STUDENT,
                Offering.term == DEMO_TERM,
                Exam.scheduled_at > now,
                Exam.scheduled_at <= until,
                ~has_final_grade,
            )
        )
        return list((await self.session.execute(statement)).tuples())

    async def list_for_student(
        self,
        student_id: UUID,
        date_from: datetime | None,
        date_to: datetime | None,
    ) -> list[tuple[Exam, Enrollment]]:
        statement = (
            select(Exam, Enrollment)
            .join(
                Enrollment,
                and_(
                    Enrollment.offering_id == Exam.offering_id, Enrollment.student_id == student_id
                ),
            )
            .join(Offering, Offering.id == Exam.offering_id)
            .join(Course)
            .options(
                contains_eager(Enrollment.offering).contains_eager(Offering.course),
                selectinload(Enrollment.grades),
            )
            .order_by(Exam.scheduled_at, Exam.id)
        )
        if date_from is None and date_to is None:
            statement = statement.where(Offering.term == DEMO_TERM)
        if date_from is not None:
            statement = statement.where(Exam.scheduled_at >= date_from)
        if date_to is not None:
            statement = statement.where(Exam.scheduled_at < date_to)
        return list((await self.session.execute(statement)).tuples())
