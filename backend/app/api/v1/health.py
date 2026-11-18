from fastapi import APIRouter

from app.db.database import DB
from app.schemas.health import Live, Ready
from app.services import health_service

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live", response_model=Live)
async def live() -> Live:
    return Live()


@router.get("/ready", response_model=Ready)
async def ready(db: DB) -> Ready:
    await health_service.ready(db)
    return Ready()
