from fastapi import APIRouter

from app.core.dependencies import CurrentStudent
from app.db.database import DB
from app.schemas.dashboard import Dashboard
from app.services import dashboard_service

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_model=Dashboard)
async def dashboard(student: CurrentStudent, db: DB) -> Dashboard:
    return await dashboard_service.get_dashboard(db, student)
