from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ApiError
from app.db.dao.health_dao import HealthDAO


async def ready(db: AsyncSession) -> None:
    try:
        await HealthDAO(db).ping()
    except (SQLAlchemyError, OSError):
        raise ApiError("SERVICE_UNAVAILABLE") from None
