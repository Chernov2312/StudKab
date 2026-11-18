import asyncio
import os
from datetime import date, datetime, time, timedelta
from typing import cast
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlalchemy import Table
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.domain import MOSCOW, utcnow
from app.core.security import passwords
from app.db.database import make_database
from app.db.models import (
    Application,
    ApplicationEvent,
    Course,
    Enrollment,
    Exam,
    Grade,
    Group,
    Instructor,
    Lesson,
    LessonChange,
    Notification,
    Offering,
    RequestType,
    Student,
    User,
)
from app.db.models.base import Base


def demo_id(key: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"urn:puls:demo:{key}")


def at(day: date, hour: int, minute: int = 0) -> datetime:
    return datetime.combine(day, time(hour, minute), MOSCOW)


def select_schema(*fields: tuple[str, str, list[str]]) -> dict[str, object]:
    return {
        "type": "object",
        "properties": {
            name: {"type": "string", "title": title, "enum": choices}
            for name, title, choices in fields
        },
        "required": [name for name, _, _ in fields],
        "additionalProperties": False,
    }


async def add(db: AsyncSession, model: type[Base], **values: object) -> None:
    table = cast(Table, model.__table__)
    statement = insert(table).values(values)
    await db.execute(statement.on_conflict_do_nothing(index_elements=list(table.primary_key)))


async def seed_demo(db: AsyncSession, alina_password: str, mark_password: str, day: date) -> None:
    if not all(1 <= len(value) <= 256 for value in (alina_password, mark_password)):
        raise ValueError("Укажите оба демонстрационных пароля длиной 1–256 символов")
    julia, roman = demo_id("teacher-julia"), demo_id("teacher-roman")
    certificate, statement = demo_id("certificate"), demo_id("statement")
    async with db.begin():
        await add(db, Instructor, id=julia, display_name="Юлия Вымышленная")
        await add(db, Instructor, id=roman, display_name="Роман Образцов")
        await add(
            db,
            RequestType,
            id=certificate,
            code="STUDY_CERTIFICATE",
            title="Справка об обучении",
            description="Демонстрационный запрос справки",
            fields_schema=select_schema(
                ("purpose", "Для чего нужна справка", ["work", "bank", "other"]),
                ("delivery_method", "Способ получения", ["digital", "pickup"]),
            ),
            comment_required=False,
            comment_max_length=500,
        )
        await add(
            db,
            RequestType,
            id=statement,
            code="DEAN_OFFICE_STATEMENT",
            title="Заявление в деканат",
            description="Обращение по учебному вопросу",
            fields_schema=select_schema(
                ("topic", "Тема обращения", ["study", "documents", "other"])
            ),
            comment_required=True,
            comment_max_length=1000,
        )
        for key, name, group, program, year, secret, teacher, subjects in [
            (
                "alina",
                "Алина Тестова",
                "ИВТ-21",
                "Информатика и вычислительная техника",
                2,
                alina_password,
                julia,
                ("Алгоритмы и структуры данных", "Базы данных"),
            ),
            (
                "mark",
                "Марк Примеров",
                "ПМИ-31",
                "Прикладная математика и информатика",
                3,
                mark_password,
                roman,
                ("Математическое моделирование", "Теория вероятностей"),
            ),
        ]:
            user_id, group_id = demo_id(key), demo_id(group)
            await add(db, Group, id=group_id, name=group)
            await add(
                db,
                User,
                id=user_id,
                username=f"demo.{key}",
                role="student",
                password_hash=passwords.hash(secret),
            )
            await add(
                db,
                Student,
                user_id=user_id,
                group_id=group_id,
                full_name=name,
                faculty="Факультет цифровых технологий",
                program=program,
                course_year=year,
            )
            for index, title in enumerate(subjects):
                course_id = demo_id(title)
                offering_id, enrollment_id = (
                    demo_id(f"{key}-offering-{index}"),
                    demo_id(f"{key}-enroll-{index}"),
                )
                assessment = "exam" if index == 0 else "pass_fail"
                await add(db, Course, id=course_id, title=title, assessment_type=assessment)
                await add(
                    db,
                    Offering,
                    id=offering_id,
                    group_id=group_id,
                    instructor_id=teacher,
                    course_id=course_id,
                    term="demo",
                )
                await add(
                    db, Enrollment, id=enrollment_id, student_id=user_id, offering_id=offering_id
                )
                if index == 0 or key == "alina":
                    await add(
                        db,
                        Grade,
                        id=demo_id(f"{key}-grade-{index}"),
                        enrollment_id=enrollment_id,
                        kind="current" if index == 0 else "final",
                        value="5" if index == 0 else "зачёт",
                        graded_at=at(day - timedelta(days=3), 12),
                    )
                exam_id = demo_id(f"{key}-exam-{index}")
                await add(
                    db,
                    Exam,
                    id=exam_id,
                    offering_id=offering_id,
                    exam_type=assessment,
                    scheduled_at=at(day + timedelta(days=2 + index), 10),
                    room=f"Д-{202 + index}",
                )
                if index == 0:
                    await add(
                        db,
                        Notification,
                        id=demo_id(f"{key}-exam-notice"),
                        student_id=user_id,
                        kind="deadline",
                        title="Скоро экзамен",
                        body=title,
                        target_type="exam",
                        target_id=exam_id,
                        created_at=at(day, 8),
                    )
                for offset in (0, 1, 3):
                    lesson_id = demo_id(f"{key}-lesson-{index}-{offset}")
                    hour = 10 + index * 3 + (1 if key == "mark" else 0)
                    minute = 45 if key == "alina" and index == 0 and offset == 0 else 0
                    lesson_date = day + timedelta(days=offset)
                    begins = at(lesson_date, hour, minute)
                    ends = begins + timedelta(minutes=90)
                    room = f"{'Б' if key == 'alina' else 'В'}-{204 + index}"
                    await add(
                        db,
                        Lesson,
                        id=lesson_id,
                        offering_id=offering_id,
                        starts_at=begins,
                        ends_at=ends,
                        room=room,
                        lesson_type="practice" if index == 0 else "lecture",
                    )
                    if offset != 0 or key != "alina":
                        continue
                    moved = index == 0
                    original = at(day, 9) if moved else begins
                    await add(
                        db,
                        LessonChange,
                        id=demo_id(f"{lesson_id}-change"),
                        lesson_id=lesson_id,
                        kind="moved" if moved else "cancelled",
                        changed_at=at(day, 8, 30),
                        old_values={
                            "starts_at": original.isoformat(),
                            "ends_at": (original + timedelta(minutes=90)).isoformat(),
                            "room": "А-101" if moved else room,
                        },
                        new_values={
                            "starts_at": begins.isoformat(),
                            "ends_at": ends.isoformat(),
                            "room": room,
                        }
                        if moved
                        else None,
                    )
                    await add(
                        db,
                        Notification,
                        id=demo_id(f"{lesson_id}-notice"),
                        student_id=user_id,
                        kind="schedule_change",
                        title="Пара перенесена" if moved else "Пара отменена",
                        body=f"{title} — новое время 10:45, {room}" if moved else title,
                        target_type="schedule",
                        target_id=lesson_id,
                        created_at=at(day, 8, 30),
                    )
            await seed_requests(db, key, user_id, certificate, statement, day)


async def seed_requests(
    db: AsyncSession,
    key: str,
    user_id: UUID,
    certificate: UUID,
    statement: UUID,
    day: date,
) -> None:
    statuses = ["ready", "new"] if key == "alina" else ["in_progress"]
    for index, status in enumerate(statuses):
        identity = f"{key}-request-{index}"
        app_id = demo_id(identity)
        created = at(day - timedelta(days=4 - index), 10)
        steps = [
            ("new", "Заявка создана"),
            ("in_progress", "Заявка принята в работу"),
            ("ready", "Демонстрационная справка готова"),
        ]
        history = steps[: ["new", "in_progress", "ready"].index(status) + 1]
        await add(
            db,
            Application,
            id=app_id,
            student_id=user_id,
            type_id=certificate if key == "alina" else statement,
            status=status,
            fields={"purpose": "work", "delivery_method": "digital"}
            if key == "alina"
            else {"topic": "study"},
            comment=None if key == "alina" else "Прошу уточнить расписание консультаций.",
            created_at=created,
            updated_at=created + timedelta(days=len(history) - 1),
        )
        previous = None
        for step, (current, note) in enumerate(history):
            await add(
                db,
                ApplicationEvent,
                id=demo_id(f"{identity}-step-{step}"),
                application_id=app_id,
                from_status=previous,
                to_status=current,
                note=note,
                actor_user_id=user_id if step == 0 else None,
                created_at=created + timedelta(days=step),
            )
            previous = current
        if status != "new":
            await add(
                db,
                Notification,
                id=demo_id(f"{identity}-notice"),
                student_id=user_id,
                kind="application_status",
                title=history[-1][1],
                body="Статус обновлён в истории заявки.",
                target_type="request",
                target_id=app_id,
                created_at=created + timedelta(days=len(history) - 1),
            )


async def main() -> None:
    database = make_database(get_settings().database_url)
    try:
        async with database() as db:
            await seed_demo(
                db,
                os.environ.get("DEMO_ALINA_PASSWORD", ""),
                os.environ.get("DEMO_MARK_PASSWORD", ""),
                utcnow().astimezone(MOSCOW).date(),
            )
    finally:
        await database.kw["bind"].dispose()


if __name__ == "__main__":
    asyncio.run(main())
