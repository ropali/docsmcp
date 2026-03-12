from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.source import Source, SourceStatus, SourceType


class SourceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        name: str,
        source_type: SourceType,
        base_url: str | None = None,
        config: dict[str, Any] | None = None,
        status: SourceStatus = SourceStatus.PENDING,
    ) -> Source:
        source = Source(
            name=name,
            source_type=source_type,
            base_url=base_url,
            status=status,
            config=config or {},
        )
        self._session.add(source)
        await self._session.commit()
        await self._session.refresh(source)
        return source

    async def get_by_id(self, source_id: uuid.UUID) -> Source | None:
        return await self._session.get(Source, source_id)

    async def list(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        status: SourceStatus | None = None,
        source_type: SourceType | None = None,
    ) -> list[Source]:
        stmt = (
            select(Source)
            .order_by(Source.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if status is not None:
            stmt = stmt.where(Source.status == status)
        if source_type is not None:
            stmt = stmt.where(Source.source_type == source_type)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(
        self,
        source: Source,
        *,
        name: str | None = None,
        base_url: str | None = None,
        config: dict[str, Any] | None = None,
        status: SourceStatus | None = None,
        error_msg: str | None = None,
    ) -> Source:
        if name is not None:
            source.name = name
        if base_url is not None:
            source.base_url = base_url
        if config is not None:
            source.config = config
        if status is not None:
            source.status = status
        source.error_msg = error_msg

        await self._session.commit()
        await self._session.refresh(source)
        return source

    async def update_progress(
        self,
        source: Source,
        *,
        page_count: int | None = None,
        indexed_count: int | None = None,
        status: SourceStatus | None = None,
        error_msg: str | None = None,
    ) -> Source:
        if page_count is not None:
            source.page_count = page_count
        if indexed_count is not None:
            source.indexed_count = indexed_count
        if status is not None:
            source.status = status
        if error_msg is not None or source.status == SourceStatus.FAILED:
            source.error_msg = error_msg

        await self._session.commit()
        await self._session.refresh(source)
        return source

    async def delete(self, source_id: uuid.UUID) -> None:
        await self._session.execute(delete(Source).where(Source.id == source_id))
        await self._session.commit()
