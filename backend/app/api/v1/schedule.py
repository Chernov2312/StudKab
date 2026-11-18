from typing import Annotated

from fastapi import APIRouter, Query

from app.core.dependencies import CurrentStudent
from app.db.database import DB
from app.schemas.common import ErrorResponse
from app.schemas.schedule import Schedule, ScheduleQuery
from app.services import schedule_service

router = APIRouter(tags=["schedule"])


@router.get("/schedule", response_model=Schedule, responses={404: {"model": ErrorResponse}})
async def schedule(
    student: CurrentStudent,
    db: DB,
    query: Annotated[ScheduleQuery, Query()],
) -> Schedule:
    return await schedule_service.get_schedule(db, student.group_id, query)
