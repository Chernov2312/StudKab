import pytest

from app.schemas.exams import Exams
from tests.conftest import API, assert_contract, assert_error, sign_in

pytestmark = pytest.mark.integration


async def test_exams_scoped_to_enrollment(student_client, client_factory, settings, secrets):
    client = student_client
    exam_a = assert_contract(
        await client.get(API + "/exams?from=2026-11-20&to=2026-11-20"), 200, Exams
    )["items"]
    async with client_factory(settings) as other:
        await sign_in(other, "demo.mark", secrets["demo.mark"])
        exam_b = assert_contract(await other.get(API + "/exams"), 200, Exams)["items"]
    assert len(exam_a) == 1 and {x["offering_id"] for x in exam_a}.isdisjoint(
        x["offering_id"] for x in exam_b
    )
    assert_error(
        await client.get(API + "/exams?from=2026-11-21&to=2026-11-20"), 422, "VALIDATION_ERROR"
    )


async def test_exams_requires_session(client):
    assert_error(await client.get(API + "/exams"), 401, "UNAUTHORIZED")
