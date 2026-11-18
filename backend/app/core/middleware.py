import json
import logging
from time import perf_counter
from uuid import uuid4

from sqlalchemy.exc import DBAPIError
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.exceptions import ApiError, error_response

log = logging.getLogger("uvicorn.error")
MAX_BODY_BYTES = 16 * 1024


class RequestMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request_id = f"req-{uuid4().hex}"
        scope.setdefault("state", {})["request_id"] = request_id
        started = perf_counter()
        status: int | None = None

        async def send_tracked(message: Message) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
                headers = MutableHeaders(scope=message)
                headers["X-Request-ID"] = request_id
                headers["Cache-Control"] = "no-store"
                headers["X-Content-Type-Options"] = "nosniff"
            await send(message)

        try:
            if scope["method"] in {"POST", "PATCH", "PUT", "DELETE"}:
                body = bytearray()
                while True:
                    message = await receive()
                    if message["type"] == "http.disconnect":
                        return
                    body.extend(message.get("body", b""))
                    if len(body) > MAX_BODY_BYTES:
                        raise ApiError("PAYLOAD_TOO_LARGE")
                    if not message.get("more_body", False):
                        break

                pending = True

                async def replay() -> Message:
                    nonlocal pending
                    if pending:
                        pending = False
                        return {"type": "http.request", "body": bytes(body), "more_body": False}
                    return await receive()

                await self.app(scope, replay, send_tracked)
            else:
                await self.app(scope, receive, send_tracked)
        except Exception as exc:
            if status is not None:
                raise
            if isinstance(exc, ApiError):
                error = exc
            elif isinstance(exc, OSError) or (
                isinstance(exc, DBAPIError) and exc.connection_invalidated
            ):
                error = ApiError("SERVICE_UNAVAILABLE")
            else:
                error = ApiError("INTERNAL_ERROR")
            if error.code in {"INTERNAL_ERROR", "SERVICE_UNAVAILABLE"}:
                log.error(
                    json.dumps({"request_id": request_id, "exception_type": type(exc).__name__})
                )
            await error_response(error, request_id)(scope, receive, send_tracked)
        finally:
            route = scope.get("route")
            log.info(
                json.dumps(
                    {
                        "request_id": request_id,
                        "route": getattr(route, "path", None),
                        "method": scope["method"],
                        "status": status,
                        "duration_ms": round((perf_counter() - started) * 1000, 2),
                    }
                )
            )
