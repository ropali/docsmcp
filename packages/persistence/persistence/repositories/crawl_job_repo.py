from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from persistence.models.job import CrawlJob, JobStatus


class CrawlJobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        source_id: uuid.UUID,
        celery_task_id: str | None = None,
        triggered_by: str | None = None,
        status: JobStatus = JobStatus.QUEUED,
    ) -> CrawlJob:
        job = CrawlJob(
            source_id=source_id,
            celery_task_id=celery_task_id,
            triggered_by=triggered_by,
            status=status,
        )
        self._session.add(job)
        await self._session.commit()
        await self._session.refresh(job)
        return job

    async def get_by_id(self, job_id: uuid.UUID) -> CrawlJob | None:
        return await self._session.get(CrawlJob, job_id)

    async def get_by_task_id(self, celery_task_id: str) -> CrawlJob | None:
        result = await self._session.execute(
            select(CrawlJob).where(CrawlJob.celery_task_id == celery_task_id)
        )
        return result.scalars().first()

    async def list_by_source_id(self, source_id: uuid.UUID) -> list[CrawlJob]:
        result = await self._session.execute(
            select(CrawlJob).where(CrawlJob.source_id == source_id)
        )
        return list(result.scalars().all())

    async def update(
        self,
        job: CrawlJob,
        *,
        status: JobStatus | None = None,
        pages_found: int | None = None,
        pages_done: int | None = None,
        started_at: datetime | None = None,
        finished_at: datetime | None = None,
    ) -> CrawlJob:
        if status is not None:
            job.status = status
        if pages_found is not None:
            job.pages_found = pages_found
        if pages_done is not None:
            job.pages_done = pages_done
        if started_at is not None:
            job.started_at = started_at
        if finished_at is not None:
            job.finished_at = finished_at

        await self._session.commit()
        await self._session.refresh(job)
        return job
