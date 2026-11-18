from fastapi import APIRouter

from app.core.dependencies import CurrentStudent
from app.db.database import DB
from app.schemas.study import Study
from app.services import study_service

router = APIRouter(tags=["study"])


@router.get("/study", response_model=Study)
async def study(student: CurrentStudent, db: DB) -> Study:
    return await study_service.get_study(db, student.user_id)
