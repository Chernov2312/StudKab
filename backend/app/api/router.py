from fastapi import APIRouter

from app.api.v1 import (
    auth,
    dashboard,
    exams,
    health,
    notifications,
    profile,
    requests,
    schedule,
    study,
)
from app.schemas.common import ErrorResponse, ValidationErrorResponse

router = APIRouter(
    prefix="/api/v1",
    responses={
        413: {"model": ErrorResponse, "description": "Превышен размер тела запроса"},
        422: {"model": ValidationErrorResponse, "description": "Ошибка валидации"},
        500: {"model": ErrorResponse, "description": "Внутренняя ошибка"},
        503: {"model": ErrorResponse, "description": "Сервис недоступен"},
    },
)

for module in (auth, profile, dashboard, schedule, study, exams, requests, notifications):
    router.include_router(
        module.router,
        responses={
            401: {"model": ErrorResponse, "description": "Требуется действующая сессия или пароль"},
            403: {"model": ErrorResponse, "description": "Доступ запрещён"},
        },
    )
router.include_router(health.router)
