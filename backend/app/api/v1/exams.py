from typing import Annotated

from fastapi import APIRouter, Query

from app.core.dependencies import CurrentStudent
from app.db.database import DB
from app.schemas.exams import ExamQuery, Exams
from app.services import exam_service

router = APIRouter(tags=["exams"])


@router.get("/exams", response_model=Exams)
async def exams(student: CurrentStudent, db: DB, query: Annotated[ExamQuery, Query()]) -> Exams:
    return await exam_service.get_exams(db, student.user_id, query)
