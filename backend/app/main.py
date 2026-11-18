from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine

from app.api.router import router
from app.core.config import Settings, get_settings
from app.core.exceptions import install_handlers
from app.core.middleware import RequestMiddleware
from app.db.database import make_database


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or get_settings()
    database = make_database(config.database_url)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            engine = database.kw["bind"]
            if isinstance(engine, AsyncEngine):
                await engine.dispose()

    app = FastAPI(
        title="Пульс API",
        version="1.0",
        lifespan=lifespan,
        redirect_slashes=False,
        openapi_url="/api/openapi.json",
        docs_url=None,
        redoc_url=None,
        swagger_ui_oauth2_redirect_url=None,
    )
    app.state.settings = config
    app.state.database = database
    app.add_middleware(RequestMiddleware)
    install_handlers(app)
    app.include_router(router)
    return app


app = create_app()
