from pipeline.config import CrawlConfig
from pipeline.crawler import Crawler
from datetime import datetime
from db.session import get_db_session
from app.models import JobStatus, SourceStatus
from celery_app import celery
import asyncio
import uuid
from app.respositories.source_repo import SourceRepository
from app.respositories.crawl_job_repo import CrawlJobRepository


@celery.task(
    bind=True,
    queue="crawl",
    max_retries=3,
    default_retry_delay=60,
    name="worker.tasks.crawl.crawl_source_task",
)
def crawl_source_task(self, source_id: str, job_id: str):
    """
    Top level task, Discovers all URLS and then fan-out
    """
    asyncio.run(_crawl_source(self, source_id, job_id))


async def _crawl_source(task, source_id: str, job_id: str):

    async with get_db_session() as session:
        job_repo = CrawlJobRepository(session)
        source_repo = SourceRepository(session)

    crawl_job = await job_repo.get_by_id(job_id=job_id)

    source = await source_repo.get_by_id(source_id=source_id)

    # TODO:  Mark job as RUNNING
    try:
        config = CrawlConfig(**source.config)

        crawler = Crawler(config=source.config)

        # Discover all URLs first (breadth-first)
        urls = await crawler.discover_urls(source.base_url)
        print(urls)
    except Exception as exc:
        raise task.retry(exc=exc)
