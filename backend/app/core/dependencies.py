from secrets import compare_digest
from typing import Annotated

from fastapi import Depends, Request

from app.core.config import Settings
from app.core.domain import Role
from app.core.exceptions import ApiError, validation
from app.db.database import DB
from app.services.auth_service import AuthContext, authenticate
from app.services.student_service import StudentScope, get_profile


def settings_for(request: Request) -> Settings:
    return request.app.state.settings


AppSettings = Annotated[Settings, Depends(settings_for)]


def require_origin(request: Request, settings: AppSettings) -> None:
    if request.headers.getlist("origin") != [settings.app_origin]:
        raise ApiError("ORIGIN_FORBIDDEN")


def require_json(request: Request) -> None:
    media_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if media_type != "application/json":
        raise validation("body", "Укажите Content-Type: application/json")


async def require_empty_body(request: Request) -> None:
    if await request.body():
        raise validation("body", "Ожидается пустое тело запроса")


async def get_current_user(request: Request, settings: AppSettings, db: DB) -> AuthContext:
    return await authenticate(db, request.cookies.get(settings.cookie_name))


CurrentUser = Annotated[AuthContext, Depends(get_current_user)]


async def get_current_student(auth: CurrentUser, db: DB) -> StudentScope:
    if auth.user.role != Role.STUDENT:
        raise ApiError("FORBIDDEN")
    return await get_profile(db, auth.user.id)


CurrentStudent = Annotated[StudentScope, Depends(get_current_student)]


def require_csrf(request: Request, auth: CurrentUser, settings: AppSettings) -> None:
    require_origin(request, settings)
    values = request.headers.getlist("x-csrf-token")
    if len(values) != 1 or not compare_digest(
        values[0].encode("utf-8"),
        auth.session.csrf_token.encode("ascii"),
    ):
        raise ApiError("CSRF_INVALID")
