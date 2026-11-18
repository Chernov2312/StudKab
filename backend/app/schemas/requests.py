from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.core.domain import ApplicationStatus
from app.schemas.common import DTO, PageQuery, Pagination


class RequestTypeItem(DTO):
    code: str
    title: str
    description: str
    fields_schema: dict[str, object]
    comment_required: bool
    comment_max_length: int


class RequestTypes(DTO):
    items: list[RequestTypeItem]


class RequestQuery(PageQuery):
    status: ApplicationStatus | None = None


class RequestInput(DTO):
    type_code: str = Field(min_length=1, max_length=64)
    fields: dict[str, object]
    comment: str | None = Field(default=None, max_length=1000)


class RequestItem(DTO):
    id: UUID
    type_code: str
    type_title: str
    status: ApplicationStatus
    created_at: datetime
    updated_at: datetime


class Event(DTO):
    id: UUID
    from_status: ApplicationStatus | None
    to_status: ApplicationStatus
    note: str
    created_at: datetime


class RequestDetails(RequestItem):
    fields: dict[str, object]
    comment: str | None
    history: list[Event]


class Requests(DTO):
    items: list[RequestItem]
    pagination: Pagination
