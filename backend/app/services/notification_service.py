from datetime import datetime, timedelta
from uuid import UUID, uuid5

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain import MOSCOW, Assessment, NotificationKind, TargetType, utcnow
from app.core.exceptions import ApiError
from app.db.dao.exam_dao import ExamDAO
from app.db.dao.notification_dao import NotificationDAO
from app.schemas.common import Pagination, Target
from app.schemas.notifications import MarkRead, NotificationItem, NotificationQuery, Notifications
from app.services.student_service import StudentScope


async def create_exam_reminders(db: AsyncSession, now: datetime) -> int:
    async with db.begin():
        due = await ExamDAO(db).upcoming_for_reminders(now, now + timedelta(hours=24))
        rows: list[dict[str, object]] = []
        for student_id, exam_id, course, scheduled_at, kind in due:
            title = "Напоминание об экзамене" if kind == Assessment.EXAM else "Напоминание о зачёте"
            when = scheduled_at.astimezone(MOSCOW).strftime("%d.%m.%Y в %H:%M")
            rows.append(
                {
                    "id": uuid5(student_id, f"exam-reminder-24h:{exam_id}"),
                    "student_id": student_id,
                    "kind": NotificationKind.DEADLINE,
                    "title": title,
                    "body": f"{course} — {when} (МСК).",
                    "target_type": TargetType.EXAM,
                    "target_id": exam_id,
                    "created_at": now,
                }
            )
        return await NotificationDAO(db).insert_reminders(rows)


async def list_notifications(
    db: AsyncSession,
    student: StudentScope,
    query: NotificationQuery,
) -> Notifications:
    dao = NotificationDAO(db)
    unread = await dao.count_unread_for_student(student.user_id)
    unread_only = query.unread_only == "true"
    total = unread if unread_only else await dao.count_for_student(student.user_id, False)
    rows = (
        await dao.list_for_student(
            student.user_id,
            student.group_id,
            unread_only,
            query.offset,
            query.page_size,
        )
        if query.offset < total
        else []
    )
    return Notifications(
        items=[
            NotificationItem(
                id=notice.id,
                kind=notice.kind,
                title=notice.title,
                body=notice.body,
                created_at=notice.created_at,
                read_at=notice.read_at,
                target=Target(type=notice.target_type, id=notice.target_id)
                if valid_target and notice.target_type and notice.target_id
                else None,
            )
            for notice, valid_target in rows
        ],
        unread_count=unread,
        pagination=Pagination.of(query, total),
    )


async def mark_read(db: AsyncSession, student_id: UUID, notification_id: UUID) -> MarkRead:
    try:
        timestamp = await NotificationDAO(db).mark_read_for_student(
            notification_id,
            student_id,
            utcnow(),
        )
        if timestamp is None:
            raise ApiError("NOT_FOUND")
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    return MarkRead(id=notification_id, read_at=timestamp)
