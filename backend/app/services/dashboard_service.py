from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain import (
    MOSCOW,
    ApplicationStatus,
    ExamStatus,
    LessonStatus,
    NotificationKind,
    TargetType,
    utcnow,
)
from app.db.dao.application_dao import ApplicationDAO
from app.db.dao.notification_dao import NotificationDAO
from app.schemas.common import Target
from app.schemas.dashboard import Dashboard, Focus, NextExam, NextLesson
from app.schemas.exams import ExamQuery
from app.schemas.schedule import ScheduleQuery
from app.services import exam_service, schedule_service, study_service
from app.services.application_service import ACTIVE
from app.services.student_service import StudentScope


async def get_dashboard(db: AsyncSession, student: StudentScope) -> Dashboard:
    now = utcnow()
    day = now.astimezone(MOSCOW).date()
    student_id = student.user_id
    schedule = await schedule_service.get_schedule(db, student.group_id, ScheduleQuery(date=day))
    study = await study_service.get_study(db, student_id)
    exams = await exam_service.get_exams(db, student_id, ExamQuery())
    application_dao = ApplicationDAO(db)
    active = await application_dao.count_for_student(student_id, ACTIVE)
    ready = await application_dao.list_for_student(student_id, (ApplicationStatus.READY,), 0, 1)
    unread = await NotificationDAO(db).count_unread_for_student(student_id)
    lesson = next(
        (
            item
            for item in schedule.items
            if item.status != LessonStatus.CANCELLED and item.starts_at >= now
        ),
        None,
    )
    exam = next(
        (
            item
            for item in exams.items
            if item.status == ExamStatus.PLANNED and item.scheduled_at >= now
        ),
        None,
    )

    focus = [
        Focus(
            kind=NotificationKind.SCHEDULE_CHANGE,
            title="Занятие отменено"
            if item.status == LessonStatus.CANCELLED
            else "Занятие перенесено",
            description=item.course.title,
            target=Target(type=TargetType.SCHEDULE, id=item.id),
            priority="high",
        )
        for item in schedule.items
        if item.change is not None
    ]
    if exam and exam.scheduled_at.astimezone(MOSCOW).date() <= day + timedelta(days=3):
        focus.append(
            Focus(
                kind=NotificationKind.DEADLINE,
                title="Скоро аттестация",
                description=exam.course_title,
                target=Target(type=TargetType.EXAM, id=exam.id),
                priority="high",
            )
        )
    if ready:
        focus.append(
            Focus(
                kind=NotificationKind.APPLICATION_STATUS,
                title="Заявка готова",
                description=ready[0].request_type.title,
                target=Target(type=TargetType.REQUEST, id=ready[0].id),
                priority="normal",
            )
        )
    return Dashboard(
        date=day,
        greeting_name=student.profile.full_name.split(maxsplit=1)[0],
        next_lesson=NextLesson(
            id=lesson.id,
            title=lesson.course.title,
            starts_at=lesson.starts_at,
            room=lesson.room,
            status=lesson.status,
        )
        if lesson
        else None,
        study=study.summary,
        active_requests_count=active,
        unread_notifications_count=unread,
        next_exam=NextExam(
            id=exam.id,
            course_title=exam.course_title,
            scheduled_at=exam.scheduled_at,
        )
        if exam
        else None,
        focus=focus[:3],
    )
