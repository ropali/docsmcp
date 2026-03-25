from persistence.repositories import (
    CrawlJobRepository,
    PageRepository,
    SourceRepository,
)
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession


async def get_pg_connection(request: Request) -> AsyncGenerator[AsyncSession]:
    try:
        async with request.app.state.session_factory() as session:
            yield session
    except Exception as e:
        await session.rollback()
        raise e


DBSessionDep = Annotated[AsyncSession, Depends(get_pg_connection)]


def get_source_repo(session: DBSessionDep) -> SourceRepository:
    return SourceRepository(session)


SourceRepoDep = Annotated[SourceRepository, Depends(get_source_repo)]


def get_page_repo(session: DBSessionDep) -> PageRepository:
    return PageRepository(session)


PageRepoDep = Annotated[PageRepository, Depends(get_page_repo)]


def get_crawl_job_repo(session: DBSessionDep) -> CrawlJobRepository:
    return CrawlJobRepository(session)


CrawlJobRepoDep = Annotated[CrawlJobRepository, Depends(get_crawl_job_repo)]
