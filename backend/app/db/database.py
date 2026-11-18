from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


def make_database(url: str) -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine(url, pool_pre_ping=True, hide_parameters=True)
    return async_sessionmaker(engine, expire_on_commit=False)


async def get_db(request: Request) -> AsyncIterator[AsyncSession]:
    factory: async_sessionmaker[AsyncSession] = request.app.state.database
    async with factory() as session:
        yield session


DB = Annotated[AsyncSession, Depends(get_db)]
