"""intial migration

Revision ID: ad58c2219fa5
Revises:
Create Date: 2026-03-11 12:16:31.216537
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from app.core.settings import settings

# revision identifiers, used by Alembic.
revision: str = "ad58c2219fa5"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    schema = settings.POSTGRES_SCHEMA
    op.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')

    source_type_enum = postgresql.ENUM(
        "URL",
        "FILE",
        "COLLECTION",
        name="source_type_enum",
        schema=schema,
        create_type=False,
    )
    source_status_enum = postgresql.ENUM(
        "PENDING",
        "CRAWLING",
        "PROCESSING",
        "READY",
        "FAILED",
        "REFRESHING",
        name="source_status_enum",
        schema=schema,
        create_type=False,
    )
    job_status_enum = postgresql.ENUM(
        "QUEUED",
        "RUNNING",
        "DONE",
        "FAILED",
        name="job_status_enum",
        schema=schema,
        create_type=False,
    )
    page_status_enum = postgresql.ENUM(
        "PENDING",
        "INDEXED",
        "FAILED",
        name="page_status_enum",
        schema=schema,
        create_type=False,
    )

    source_type_enum.create(op.get_bind(), checkfirst=True)
    source_status_enum.create(op.get_bind(), checkfirst=True)
    job_status_enum.create(op.get_bind(), checkfirst=True)
    page_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "sources",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("source_type", source_type_enum, nullable=False),
        sa.Column("base_url", sa.Text(), nullable=True),
        sa.Column("status", source_status_enum, server_default="PENDING", nullable=False),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("page_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("indexed_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error_msg", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema=schema,
    )

    op.create_table(
        "crawl_jobs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("source_id", sa.UUID(), nullable=False),
        sa.Column("celery_task_id", sa.String(length=255), nullable=False),
        sa.Column("status", job_status_enum, server_default="QUEUED", nullable=False),
        sa.Column("pages_found", sa.Integer(), server_default="0", nullable=False),
        sa.Column("pages_done", sa.Integer(), server_default="0", nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("triggered_by", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], [f"{schema}.sources.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema=schema,
    )
    op.create_index("ix_crawl_jobs_celery_task_id", "crawl_jobs", ["celery_task_id"], unique=False, schema=schema)
    op.create_index("ix_crawl_jobs_source_id", "crawl_jobs", ["source_id"], unique=False, schema=schema)

    op.create_table(
        "pages",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("source_id", sa.UUID(), nullable=False),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("file_path", sa.Text(), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("status", page_status_enum, server_default="PENDING", nullable=False),
        sa.Column("chunk_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("crawled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("indexed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_msg", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["source_id"], [f"{schema}.sources.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema=schema,
    )
    op.create_index("ix_pages_content_hash", "pages", ["content_hash"], unique=False, schema=schema)
    op.create_index("ix_pages_source_id", "pages", ["source_id"], unique=False, schema=schema)


def downgrade() -> None:
    """Downgrade schema."""
    schema = settings.POSTGRES_SCHEMA

    op.drop_index("ix_pages_source_id", table_name="pages", schema=schema)
    op.drop_index("ix_pages_content_hash", table_name="pages", schema=schema)
    op.drop_table("pages", schema=schema)

    op.drop_index("ix_crawl_jobs_source_id", table_name="crawl_jobs", schema=schema)
    op.drop_index("ix_crawl_jobs_celery_task_id", table_name="crawl_jobs", schema=schema)
    op.drop_table("crawl_jobs", schema=schema)

    op.drop_table("sources", schema=schema)

    postgresql.ENUM(name="page_status_enum", schema=schema).drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="job_status_enum", schema=schema).drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="source_status_enum", schema=schema).drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="source_type_enum", schema=schema).drop(op.get_bind(), checkfirst=True)
