from collections.abc import Collection
from uuid import UUID

from jsonschema import Draft202012Validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain import ApplicationStatus, utcnow
from app.core.exceptions import ApiError, validation
from app.db.dao.application_dao import ApplicationDAO
from app.db.models import Application, ApplicationEvent
from app.schemas.common import ErrorDetail, Pagination
from app.schemas.requests import (
    Event,
    RequestDetails,
    RequestInput,
    RequestItem,
    RequestQuery,
    Requests,
    RequestTypeItem,
    RequestTypes,
)

ACTIVE = (ApplicationStatus.NEW, ApplicationStatus.IN_PROGRESS)


def request_item(record: Application) -> RequestItem:
    return RequestItem(
        id=record.id,
        type_code=record.request_type.code,
        type_title=record.request_type.title,
        status=record.status,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def details(record: Application, history: list[ApplicationEvent]) -> RequestDetails:
    return RequestDetails(
        **request_item(record).model_dump(),
        fields=record.fields,
        comment=record.comment,
        history=[Event.model_validate(event) for event in history],
    )


async def list_request_types(db: AsyncSession) -> RequestTypes:
    return RequestTypes(
        items=[
            RequestTypeItem.model_validate(record)
            for record in await ApplicationDAO(db).list_types()
        ]
    )


async def list_requests(
    db: AsyncSession,
    student_id: UUID,
    query: RequestQuery,
) -> Requests:
    dao = ApplicationDAO(db)
    statuses: Collection[ApplicationStatus] = (query.status,) if query.status else ()
    total = await dao.count_for_student(student_id, statuses)
    rows = (
        await dao.list_for_student(student_id, statuses, query.offset, query.page_size)
        if query.offset < total
        else []
    )
    return Requests(
        items=[request_item(record) for record in rows],
        pagination=Pagination.of(query, total),
    )


async def get_request(db: AsyncSession, student_id: UUID, request_id: UUID) -> RequestDetails:
    dao = ApplicationDAO(db)
    record = await dao.get_for_student(request_id, student_id)
    if record is None:
        raise ApiError("NOT_FOUND")
    return details(record, await dao.history_for_student(request_id, student_id))


async def create_request(
    db: AsyncSession,
    student_id: UUID,
    body: RequestInput,
) -> RequestDetails:
    dao = ApplicationDAO(db)
    try:
        kind = await dao.get_type(body.type_code)
        if kind is None:
            raise validation("type_code", "Выберите тип заявки из справочника")
        invalid_fields = [
            ErrorDetail(
                field=".".join(["fields", *map(str, error.absolute_path)]),
                message="Проверьте обязательные поля и допустимые значения",
            )
            for error in Draft202012Validator(kind.fields_schema).iter_errors(body.fields)
        ]
        if invalid_fields:
            raise ApiError("VALIDATION_ERROR", invalid_fields)
        comment = body.comment.strip() if body.comment is not None else None
        if kind.comment_required and not comment:
            raise validation("comment", "Добавьте комментарий")
        if body.comment is not None and len(body.comment) > kind.comment_max_length:
            raise validation("comment", f"Максимум {kind.comment_max_length} символов")
        now = utcnow()
        record = await dao.create(
            Application(
                student_id=student_id,
                request_type=kind,
                status=ApplicationStatus.NEW,
                fields=body.fields,
                comment=comment,
                created_at=now,
                updated_at=now,
            )
        )
        event = await dao.add_event(
            ApplicationEvent(
                application_id=record.id,
                to_status=ApplicationStatus.NEW,
                note="Заявка создана",
                actor_user_id=student_id,
                created_at=now,
            )
        )
        result = details(record, [event])
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    return result
