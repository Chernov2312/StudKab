from uuid import uuid4

import pytest

from app.schemas.requests import RequestDetails, Requests, RequestTypes
from app.seed import demo_id
from tests.conftest import API, CERTIFICATE, ORIGIN, assert_contract, assert_error, csrf, sign_in

pytestmark = pytest.mark.integration


async def test_requests_require_session(client):
    for path in ("/request-types", "/requests", f"/requests/{uuid4()}"):
        assert_error(await client.get(API + path), 401, "UNAUTHORIZED")
    assert_error(await client.post(API + "/requests", json=CERTIFICATE), 401, "UNAUTHORIZED")


async def test_request_types_and_list_match_contract(student_client):
    assert_contract(await student_client.get(API + "/request-types"), 200, RequestTypes)
    assert_contract(await student_client.get(API + "/requests"), 200, Requests)


async def test_application_persists_and_has_history(client, client_factory, settings, secrets):
    await sign_in(client, "demo.alina", secrets["demo.alina"])
    headers = await csrf(client)
    for body in [
        {**CERTIFICATE, "fields": {"purpose": "invalid", "delivery_method": "digital"}},
        {**CERTIFICATE, "fields": {"purpose": "work"}},
        {**CERTIFICATE, "fields": {"purpose": "work", "delivery_method": "digital", "extra": 1}},
        {**CERTIFICATE, "type_code": "UNKNOWN"},
        {**CERTIFICATE, "comment": "x" * 501},
        {"type_code": "DEAN_OFFICE_STATEMENT", "fields": {"topic": "study"}, "comment": "   "},
    ]:
        assert_error(
            await client.post(API + "/requests", headers=headers, json=body),
            422,
            "VALIDATION_ERROR",
        )
    created = await client.post(API + "/requests", headers=headers, json=CERTIFICATE)
    data = assert_contract(created, 201, RequestDetails)
    assert data["status"] == "new"
    assert (
        assert_contract(await client.get(created.headers["location"]), 200, RequestDetails) == data
    )
    assert data["history"][0]["from_status"] is None
    assert data["history"][0]["to_status"] == "new"
    async with client_factory(settings) as reopened:
        await sign_in(reopened, "demo.alina", secrets["demo.alina"])
        assert (await reopened.get(created.headers["location"])).json() == data
        page = (await reopened.get(API + "/requests?status=new&page=1&page_size=1")).json()
        assert page["pagination"]["total"] == 2 and page["pagination"]["has_next"]
        assert page["items"][0]["id"] == data["id"]
        assert_error(await reopened.get(API + "/requests?page_size=101"), 422, "VALIDATION_ERROR")
        assert_error(await reopened.get(API + "/requests?status=invalid"), 422, "VALIDATION_ERROR")
        assert_error(await reopened.get(API + "/requests/not-an-id"), 422, "VALIDATION_ERROR")


async def test_student_cannot_read_other_application(client, secrets):
    await sign_in(client, "demo.alina", secrets["demo.alina"])
    target = API + f"/requests/{demo_id('mark-request-0')}"
    foreign = assert_error(await client.get(target), 404, "NOT_FOUND")
    absent = assert_error(await client.get(API + f"/requests/{uuid4()}"), 404, "NOT_FOUND")
    assert foreign["message"] == absent["message"]
    assert_error(
        await client.patch(target, headers=await csrf(client), json={"status": "ready"}),
        405,
        "METHOD_NOT_ALLOWED",
    )
    assert_error(
        await client.get(API + "/requests?student_id=" + str(demo_id("mark"))),
        422,
        "VALIDATION_ERROR",
    )


async def test_student_cannot_set_request_owner_in_payload(client, secrets):
    await sign_in(client, "demo.alina", secrets["demo.alina"])
    headers = await csrf(client)
    for key in ("student_id", "owner_id", "status"):
        assert_error(
            await client.post(
                API + "/requests", headers=headers, json={**CERTIFICATE, key: str(demo_id("mark"))}
            ),
            422,
            "VALIDATION_ERROR",
        )


async def test_mutation_rejects_missing_or_bad_csrf(student_client):
    for headers in ({"Origin": ORIGIN}, {"Origin": ORIGIN, "X-CSRF-Token": "wrong"}):
        assert_error(
            await student_client.post(API + "/requests", json=CERTIFICATE, headers=headers),
            403,
            "CSRF_INVALID",
        )


async def test_request_creation_response_matches_openapi(client):
    response = await client.get("/api/openapi.json")
    assert response.status_code == 200
    spec = response.json()
    assert spec["paths"][API + "/requests"]["post"]["responses"]["201"]["content"][
        "application/json"
    ]["schema"]["$ref"].endswith("/RequestDetails")
