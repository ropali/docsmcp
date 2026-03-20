from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from app.db.postgres_pool import create_engine_pg, create_session_factory
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, AsyncSession
from loguru import logger


def get_engine() -> AsyncEngine:
    return create_engine_pg()


def get_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return create_session_factory(engine)


@asynccontextmanager
async def get_db_session() -> AsyncIterator[AsyncSession]:
    # Each asyncio.run() task gets a fresh loop. Keep engine/session lifecycle
    # scoped to the current context to avoid cross-loop Future binding errors.
    engine = get_engine()
    session_factory = get_session_factory(engine)

    async with session_factory() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database Exception: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()
            await engine.dispose()
