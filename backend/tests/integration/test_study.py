import pytest

from app.schemas.study import Study
from tests.conftest import API, assert_contract, assert_error, sign_in

pytestmark = pytest.mark.integration


async def test_grades_scoped_to_enrollment(client, client_factory, settings, secrets):
    await sign_in(client, "demo.alina", secrets["demo.alina"])
    async with client_factory(settings) as other:
        await sign_in(other, "demo.mark", secrets["demo.mark"])
        first = assert_contract(await client.get(API + "/study"), 200, Study)
        second = assert_contract(await other.get(API + "/study"), 200, Study)
        assert first["summary"] == {"passed": 1, "pending": 1, "total": 2}
        assert second["summary"] == {"passed": 0, "pending": 2, "total": 2}
        assert {x["offering_id"] for x in first["courses"]}.isdisjoint(
            x["offering_id"] for x in second["courses"]
        )
        assert any(x["grades"] == [] and x["final_grade"] is None for x in second["courses"])


async def test_study_requires_session(client):
    assert_error(await client.get(API + "/study"), 401, "UNAUTHORIZED")
