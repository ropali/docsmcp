import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import select

from persistence.models.page import Page


class PageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        source_id: uuid.UUID,
        content_hash: str,
        title: str | None = None,
        file_path: str | None = None,
        url: str | None = None,
    ) -> Page:
        page = Page(
            source_id=source_id,
            content_hash=content_hash,
            title=title,
            file_path=file_path,
            url=url,
        )
        self._session.add(page)
        await self._session.commit()
        await self._session.refresh(page)
        return page

    async def bulk_create(self, pages: list[dict[str, Any]]) -> list[Page]:
        if not pages:
            return []

        records = [Page(**page_data) for page_data in pages]
        self._session.add_all(records)
        await self._session.commit()
        return records

    async def get_by_id(self, page_id: uuid.UUID) -> Page | None:
        result = await self._session.execute(select(Page).where(Page.id == page_id))

        return result.scalar_one_or_none()

    async def list(self, *, source_id: uuid.UUID) -> list[Page]:
        result = await self._session.execute(
            select(Page).where(Page.source_id == source_id)
        )

        return list(result.scalars().all())
