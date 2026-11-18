from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response

from app.core.dependencies import CurrentStudent, require_csrf, require_json
from app.db.database import DB
from app.schemas.common import ErrorResponse
from app.schemas.requests import RequestDetails, RequestInput, RequestQuery, Requests, RequestTypes
from app.services import application_service

router = APIRouter(tags=["requests"])


@router.get("/request-types", response_model=RequestTypes)
async def request_types(student: CurrentStudent, db: DB) -> RequestTypes:
    return await application_service.list_request_types(db)


@router.get("/requests", response_model=Requests)
async def list_requests(
    student: CurrentStudent,
    db: DB,
    query: Annotated[RequestQuery, Query()],
) -> Requests:
    return await application_service.list_requests(db, student.user_id, query)


@router.post(
    "/requests",
    status_code=201,
    response_model=RequestDetails,
    dependencies=[Depends(require_csrf), Depends(require_json)],
)
async def create_request(
    body: RequestInput,
    response: Response,
    student: CurrentStudent,
    db: DB,
) -> RequestDetails:
    result = await application_service.create_request(db, student.user_id, body)
    response.headers["Location"] = f"/api/v1/requests/{result.id}"
    return result


@router.get(
    "/requests/{request_id}",
    response_model=RequestDetails,
    responses={404: {"model": ErrorResponse}},
)
async def request_details(request_id: UUID, student: CurrentStudent, db: DB) -> RequestDetails:
    return await application_service.get_request(db, student.user_id, request_id)
