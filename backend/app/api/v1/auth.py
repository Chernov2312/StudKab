from fastapi import APIRouter, Depends, Request, Response

from app.core.dependencies import (
    AppSettings,
    CurrentUser,
    require_csrf,
    require_empty_body,
    require_json,
    require_origin,
)
from app.core.domain import Role
from app.db.database import DB
from app.schemas.auth import CSRF, LoginInput, LoginOutput, Me, UserInfo
from app.schemas.common import ErrorResponse
from app.services import auth_service, student_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=LoginOutput,
    dependencies=[Depends(require_origin), Depends(require_json)],
    responses={429: {"model": ErrorResponse}},
)
async def login(
    body: LoginInput,
    request: Request,
    response: Response,
    settings: AppSettings,
    db: DB,
) -> LoginOutput:
    result, token = await auth_service.login(
        db,
        settings,
        body,
        request.client.host if request.client else "unknown",
        request.cookies.get(settings.cookie_name),
    )
    response.set_cookie(
        settings.cookie_name,
        token,
        max_age=settings.session_ttl_seconds,
        path="/",
        secure=settings.secure_cookie,
        httponly=True,
        samesite="lax",
    )
    return result


@router.get("/me", response_model=Me)
async def me(auth: CurrentUser, db: DB) -> Me:
    profile = (
        (await student_service.get_profile(db, auth.user.id)).profile
        if auth.user.role == Role.STUDENT
        else None
    )
    return Me(user=UserInfo.model_validate(auth.user), student=profile)


@router.get("/csrf", response_model=CSRF)
async def csrf(auth: CurrentUser) -> CSRF:
    return CSRF(csrf_token=auth.session.csrf_token)


@router.post(
    "/logout",
    status_code=204,
    response_model=None,
    dependencies=[Depends(require_csrf), Depends(require_empty_body)],
)
async def logout(
    auth: CurrentUser,
    settings: AppSettings,
    db: DB,
) -> Response:
    await auth_service.logout(db, auth)
    response = Response(status_code=204)
    response.delete_cookie(
        settings.cookie_name,
        path="/",
        secure=settings.secure_cookie,
        httponly=True,
        samesite="lax",
    )
    return response
