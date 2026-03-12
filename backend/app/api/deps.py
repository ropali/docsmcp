from app.respositories import PageRepository, SourceRepository
from collections.abc import AsyncGenerator
from typing import Annotated

# import redis.asyncio as redis
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession


# def get_redis_connection(request: Request) -> redis.Redis:
#     return redis.Redis.from_pool(request.app.state.redis_pool)
#


async def get_pg_connection(request: Request) -> AsyncGenerator[AsyncSession]:
    try:
        async with request.app.state.session_factory() as session:
            yield session
    except Exception as e:
        await session.rollback()
        raise e


# RedisConnectionDep = Annotated[redis.Redis, Depends(get_redis_connection)]
DBSessionDep = Annotated[AsyncSession, Depends(get_pg_connection)]


def get_source_repo(session: DBSessionDep) -> SourceRepository:
    return SourceRepository(session)


SourceRepoDep = Annotated[SourceRepository, Depends(get_source_repo)]


def get_page_repo(session: DBSessionDep) -> PageRepository:
    return PageRepository(session)


PageRepoDep = Annotated[PageRepository, Depends(get_page_repo)]
