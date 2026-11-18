import pytest

from app.schemas.profile import Profile
from tests.conftest import API, COOKIE, assert_contract, assert_error, csrf

pytestmark = pytest.mark.integration


async def test_profile_requires_session(client):
    assert_error(await client.get(API + "/profile"), 401, "UNAUTHORIZED")


async def test_profile_matches_contract_and_rejects_revoked_session(student_client):
    client = student_client
    response = assert_contract(await client.get(API + "/profile"), 200, Profile)
    assert response["full_name"] == "Алина Тестова"
    token = client.cookies.get(COOKIE)
    logout = await client.post(API + "/auth/logout", headers=await csrf(client))
    assert logout.status_code == 204
    assert_error(
        await client.get(API + "/profile", headers={"Cookie": f"{COOKIE}={token}"}),
        401,
        "UNAUTHORIZED",
    )
