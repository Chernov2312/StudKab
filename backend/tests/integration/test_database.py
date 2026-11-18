import pytest
from sqlalchemy import func, select

from alembic import command
from alembic.config import Config
from app.core.config import get_settings
from app.db.models import Application, Notification, User
from app.seed import demo_id, seed_demo
from tests.conftest import DEMO_DAY

pytestmark = pytest.mark.integration


async def test_seed_is_idempotent(database, secrets):
    models = (User, Application, Notification)
    async with database() as db:
        counts = [await db.scalar(select(func.count()).select_from(model)) for model in models]
    async with database() as db:
        await seed_demo(db, secrets["demo.alina"], secrets["demo.mark"], DEMO_DAY)
    async with database() as db:
        assert counts == [
            await db.scalar(select(func.count()).select_from(model)) for model in models
        ]
        user = await db.get(User, demo_id("alina"))
        assert user is not None and user.password_hash.startswith("$argon2id$")
        assert secrets["demo.alina"] != user.password_hash


def test_migrations_apply_to_fresh_database(db_url):
    get_settings.cache_clear()
    assert get_settings().database_url == db_url
    command.check(Config("alembic.ini"))
    get_settings.cache_clear()
