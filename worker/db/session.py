from contextlib import asynccontextmanager
from collections.abc import AsyncIterable, AsyncIterator
from anyio.functools import lru_cache
from app.db.postgres_pool import create_engine_pg, create_session_factory
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, AsyncSession


@lru_cache(maxsize=1)
def get_engine() -> AsyncEngine:
    return create_engine_pg()


@lru_cache(maxsize=1)
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return create_session_factory(get_engine())


@asynccontextmanager
async def get_db_session() -> AsyncIterator:
    session_factory = get_session_factory()

    async with session_factory() as session:
        try:
            yield session
        except Exception as e:
            print("Database Exception:", e)
            await session.rollback()


async def auto_close_db() -> None:
    engine = get_engine()
    await engine.dispose()
