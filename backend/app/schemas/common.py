from datetime import date
from re import fullmatch
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from app.core.domain import TargetType


class DTO(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class ErrorDetail(DTO):
    field: str
    message: str


class ErrorBody(DTO):
    code: str
    message: str
    request_id: str


class ValidationErrorBody(ErrorBody):
    details: list[ErrorDetail]


class ErrorResponse(DTO):
    error: ErrorBody


class ValidationErrorResponse(DTO):
    error: ValidationErrorBody


class PageQuery(DTO):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class Pagination(DTO):
    page: int
    page_size: int
    total: int
    has_next: bool

    @classmethod
    def of(cls, query: PageQuery, total: int) -> "Pagination":
        return cls(
            page=query.page,
            page_size=query.page_size,
            total=total,
            has_next=query.offset + query.page_size < total,
        )


class Target(DTO):
    type: TargetType
    id: UUID


def parse_date(value: object) -> date:
    if isinstance(value, date):
        return value
    if not isinstance(value, str) or not fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        raise ValueError("Укажите дату в формате ГГГГ-ММ-ДД")
    return date.fromisoformat(value)


CalendarDate = Annotated[date, BeforeValidator(parse_date)]
