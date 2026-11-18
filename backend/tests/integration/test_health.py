import pytest

from app.schemas.health import Live, Ready
from tests.conftest import API, assert_contract

pytestmark = pytest.mark.integration


async def test_health_endpoints_match_contract(client):
    assert_contract(await client.get(API + "/health/live"), 200, Live)
    assert_contract(await client.get(API + "/health/ready"), 200, Ready)
