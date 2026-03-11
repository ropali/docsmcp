from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.settings import settings
from app.models.base import Base


class JobStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"


class CrawlJob(Base):
    __tablename__ = "crawl_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{settings.POSTGRES_SCHEMA}.sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    celery_task_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status_enum"),
        nullable=False,
        default=JobStatus.QUEUED,
        server_default=JobStatus.QUEUED.value,
    )
    pages_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    pages_done: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    triggered_by: Mapped[str] = mapped_column(String(32), nullable=False)
