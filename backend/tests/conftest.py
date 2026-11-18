from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, closing
from datetime import UTC, date, datetime
from secrets import token_urlsafe
from uuid import uuid4

import httpx
import psycopg2
import pytest
from psycopg2 import sql
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from testcontainers.postgres import PostgresContainer

from alembic import command
from alembic.config import Config
from app.core.config import Settings, get_settings
from app.db.database import make_database
from app.main import create_app
from app.seed import seed_demo
from app.services import dashboard_service, schedule_service

API = "/api/v1"
ORIGIN = "https://puls.test"
COOKIE = "__Host-session"
DEMO_DAY = date(2026, 11, 18)
CERTIFICATE = {
    "type_code": "STUDY_CERTIFICATE",
    "fields": {"purpose": "work", "delivery_method": "digital"},
}


@pytest.fixture(scope="session")
def postgres() -> Iterator[PostgresContainer]:
    with PostgresContainer("postgres:16-alpine", password=token_urlsafe(24)) as container:
        yield container


@pytest.fixture
def db_url(postgres: PostgresContainer, monkeypatch: pytest.MonkeyPatch) -> str:
    name = f"test_{uuid4().hex}"
    host, port = postgres.get_container_host_ip(), postgres.get_exposed_port(5432)
    with (
        closing(
            psycopg2.connect(
                host=host,
                port=port,
                user=postgres.username,
                password=postgres.password,
                dbname=postgres.dbname,
            )
        ) as connection,
        connection.cursor() as cursor,
    ):
        connection.autocommit = True
        cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    url = f"postgresql+asyncpg://{postgres.username}:{postgres.password}@{host}:{port}/{name}"
    monkeypatch.setenv("DATABASE_URL", url)
    get_settings.cache_clear()
    command.upgrade(Config("alembic.ini"), "head")
    get_settings.cache_clear()
    return url


@pytest.fixture
def secrets() -> dict[str, str]:
    return {account: token_urlsafe(20) for account in ("demo.alina", "demo.mark")}


@pytest.fixture
async def database(
    db_url: str, secrets: dict[str, str]
) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    factory = make_database(db_url)
    try:
        async with factory() as db:
            await seed_demo(db, secrets["demo.alina"], secrets["demo.mark"], DEMO_DAY)
        yield factory
    finally:
        await factory.kw["bind"].dispose()


@pytest.fixture
def settings(db_url: str) -> Settings:
    return Settings(database_url=db_url, app_env="production", app_origin=ORIGIN)


@pytest.fixture
def client_factory(database: async_sessionmaker[AsyncSession], monkeypatch: pytest.MonkeyPatch):
    def frozen_now() -> datetime:
        return datetime(2026, 11, 18, 6, tzinfo=UTC)

    monkeypatch.setattr(dashboard_service, "utcnow", frozen_now)
    monkeypatch.setattr(schedule_service, "utcnow", frozen_now)

    @asynccontextmanager
    async def open_client(config: Settings) -> AsyncIterator[httpx.AsyncClient]:
        app = create_app(config)
        async with (
            app.router.lifespan_context(app),
            httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url=ORIGIN) as client,
        ):
            yield client

    return open_client


@pytest.fixture
async def client(client_factory, settings: Settings) -> AsyncIterator[httpx.AsyncClient]:
    async with client_factory(settings) as primary:
        yield primary


@pytest.fixture
async def student_client(client: httpx.AsyncClient, secrets: dict[str, str]) -> httpx.AsyncClient:
    await sign_in(client, "demo.alina", secrets["demo.alina"])
    return client


def assert_contract(response: httpx.Response, status: int, schema: type[BaseModel]) -> dict:
    assert response.status_code == status, response.text
    payload = response.json()
    schema.model_validate(payload)
    assert response.headers["cache-control"] == "no-store"
    return payload


async def sign_in(client: httpx.AsyncClient, username: str, password: str) -> httpx.Response:
    response = await client.post(
        f"{API}/auth/login",
        headers={"Origin": ORIGIN},
        json={
            "username": username,
            "password": password,
        },
    )
    assert response.status_code == 200, response.json()
    return response


async def csrf(client: httpx.AsyncClient) -> dict[str, str]:
    response = await client.get(f"{API}/auth/csrf")
    assert response.status_code == 200
    return {"Origin": ORIGIN, "X-CSRF-Token": response.json()["csrf_token"]}


def assert_error(response: httpx.Response, status: int, code: str) -> dict:
    assert response.status_code == status, response.text
    payload = response.json()
    assert set(payload) == {"error"}
    error = payload["error"]
    assert error["code"] == code
    assert error["request_id"] == response.headers["x-request-id"]
    assert set(error) == (
        {"code", "message", "request_id", "details"}
        if status == 422
        else {"code", "message", "request_id"}
    )
    return error
