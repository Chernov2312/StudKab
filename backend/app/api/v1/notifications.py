from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import CurrentStudent, require_csrf, require_empty_body
from app.db.database import DB
from app.schemas.common import ErrorResponse
from app.schemas.notifications import MarkRead, NotificationQuery, Notifications
from app.services import notification_service

router = APIRouter(tags=["notifications"])


@router.get("/notifications", response_model=Notifications)
async def notifications(
    student: CurrentStudent,
    db: DB,
    query: Annotated[NotificationQuery, Query()],
) -> Notifications:
    return await notification_service.list_notifications(db, student, query)


@router.post(
    "/notifications/{id}/read",
    response_model=MarkRead,
    dependencies=[Depends(require_csrf), Depends(require_empty_body)],
    responses={404: {"model": ErrorResponse}},
)
async def mark_read(id: UUID, student: CurrentStudent, db: DB) -> MarkRead:
    return await notification_service.mark_read(db, student.user_id, id)
