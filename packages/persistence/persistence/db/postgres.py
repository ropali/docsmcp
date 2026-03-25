from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from common.settings import settings

import logging

logger = logging.getLogger(__name__)


def create_engine_pg() -> AsyncEngine:
    return create_async_engine(
        settings.POSTGRES_DATABASE_URL,
        pool_size=settings.PG_POOL_SIZE,
        max_overflow=settings.PG_POOL_OVERFLOW,
    )


def create_session_factory(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


@asynccontextmanager
async def get_db_session() -> AsyncIterator[AsyncSession]:
    # Keep engine/session lifecycle scoped to this context to avoid
    # cross-loop Future binding errors in asyncio-run task execution.
    engine = create_engine_pg()
    session_factory = create_session_factory(engine)

    async with session_factory() as session:
        try:
            yield session
        except Exception as exc:
            logger.error(f"Database Exception: {exc}")
            await session.rollback()
            raise
        finally:
            await session.close()
            await engine.dispose()
