from datetime import datetime
from typing import Literal
from uuid import UUID

from app.core.domain import NotificationKind
from app.schemas.common import DTO, PageQuery, Pagination, Target


class NotificationQuery(PageQuery):
    unread_only: Literal["true", "false"] = "false"


class NotificationItem(DTO):
    id: UUID
    kind: NotificationKind
    title: str
    body: str
    created_at: datetime
    read_at: datetime | None
    target: Target | None


class Notifications(DTO):
    items: list[NotificationItem]
    unread_count: int
    pagination: Pagination


class MarkRead(DTO):
    id: UUID
    read_at: datetime
    is_read: Literal[True] = True
