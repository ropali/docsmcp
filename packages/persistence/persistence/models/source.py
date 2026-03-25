from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from common.settings import settings
from persistence.models.base import Base


class SourceType(str, enum.Enum):
    URL = "URL"
    FILE = "FILE"
    COLLECTION = "COLLECTION"


class SourceStatus(str, enum.Enum):
    PENDING = "PENDING"
    CRAWLING = "CRAWLING"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"
    REFRESHING = "REFRESHING"


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[SourceType] = mapped_column(
        ENUM(
            SourceType,
            name="source_type_enum",
            schema=settings.POSTGRES_SCHEMA,
            create_type=False,
        ),
        nullable=False,
    )
    base_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[SourceStatus] = mapped_column(
        ENUM(
            SourceStatus,
            name="source_status_enum",
            schema=settings.POSTGRES_SCHEMA,
            create_type=False,
        ),
        nullable=False,
        default=SourceStatus.PENDING,
        server_default=SourceStatus.PENDING.value,
    )
    config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    page_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    indexed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    error_msg: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
