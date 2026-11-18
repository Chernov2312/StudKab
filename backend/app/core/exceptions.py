from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.schemas.common import (
    ErrorBody,
    ErrorDetail,
    ErrorResponse,
    ValidationErrorBody,
    ValidationErrorResponse,
)

ERRORS = {
    "BAD_REQUEST": (400, "Некорректный запрос"),
    "UNAUTHORIZED": (401, "Войдите в кабинет"),
    "INVALID_CREDENTIALS": (401, "Неверный логин или пароль"),
    "FORBIDDEN": (403, "Доступ запрещён"),
    "CSRF_INVALID": (403, "Подтверждение запроса недействительно"),
    "ORIGIN_FORBIDDEN": (403, "Источник запроса запрещён"),
    "NOT_FOUND": (404, "Запись не найдена"),
    "METHOD_NOT_ALLOWED": (405, "Метод не поддерживается"),
    "PAYLOAD_TOO_LARGE": (413, "Запрос слишком большой"),
    "VALIDATION_ERROR": (422, "Проверьте введённые данные"),
    "RATE_LIMITED": (429, "Слишком много попыток, попробуйте позже"),
    "INTERNAL_ERROR": (500, "Не удалось выполнить запрос"),
    "SERVICE_UNAVAILABLE": (503, "Сервис временно недоступен"),
}


class ApiError(Exception):
    def __init__(
        self,
        code: str,
        details: list[ErrorDetail] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(code)
        self.code = code
        self.details = details
        self.headers = headers


def validation(field: str, message: str) -> ApiError:
    return ApiError("VALIDATION_ERROR", [ErrorDetail(field=field, message=message)])


def error_response(error: ApiError, request_id: str) -> JSONResponse:
    status, message = ERRORS[error.code]
    body = ErrorBody(code=error.code, message=message, request_id=request_id)
    if status == 422:
        payload = ValidationErrorResponse(
            error=ValidationErrorBody(
                **body.model_dump(),
                details=error.details or [],
            )
        ).model_dump()
    else:
        payload = ErrorResponse(error=body).model_dump()
    return JSONResponse(payload, status_code=status, headers=error.headers)


def install_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def handle_api(request: Request, exc: ApiError) -> JSONResponse:
        return error_response(exc, request.state.request_id)

    @app.exception_handler(RequestValidationError)
    async def handle_validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        details = [
            ErrorDetail(
                field=".".join(str(part) for part in item["loc"][1:]) or str(item["loc"][0]),
                message="Недопустимое значение",
            )
            for item in exc.errors()
        ]
        return error_response(ApiError("VALIDATION_ERROR", details), request.state.request_id)

    @app.exception_handler(HTTPException)
    async def handle_http(request: Request, exc: HTTPException) -> JSONResponse:
        code = {404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED"}.get(exc.status_code, "BAD_REQUEST")
        return error_response(
            ApiError(code, headers=dict(exc.headers) if exc.headers else None),
            request.state.request_id,
        )
