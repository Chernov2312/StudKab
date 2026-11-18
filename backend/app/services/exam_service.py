from datetime import date, datetime, time, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain import MOSCOW, ExamStatus, Result
from app.core.exceptions import validation
from app.db.dao.exam_dao import ExamDAO
from app.schemas.exams import ExamItem, ExamQuery, Exams
from app.services.study_service import assessment_result, final_grade


async def get_exams(db: AsyncSession, student_id: UUID, query: ExamQuery) -> Exams:
    if query.date_from and query.date_to and query.date_from > query.date_to:
        raise validation("to", "Конец периода раньше начала")
    start = datetime.combine(query.date_from, time.min, MOSCOW) if query.date_from else None
    end = (
        datetime.combine(query.date_to + timedelta(days=1), time.min, MOSCOW)
        if query.date_to and query.date_to != date.max
        else None
    )
    if query.date_to == date.max and start is None:
        start = datetime.combine(date.min + timedelta(days=1), time.min, MOSCOW)
    rows = await ExamDAO(db).list_for_student(student_id, start, end)
    items = []
    for exam, enrollment in rows:
        grade = final_grade(enrollment.grades)
        result = assessment_result(exam.exam_type, grade)
        items.append(
            ExamItem(
                id=exam.id,
                offering_id=exam.offering_id,
                course_title=enrollment.offering.course.title,
                type=exam.exam_type,
                scheduled_at=exam.scheduled_at,
                room=exam.room,
                status=ExamStatus.PLANNED if result == Result.PENDING else ExamStatus(result),
                grade=grade,
            )
        )
    return Exams(items=items)
