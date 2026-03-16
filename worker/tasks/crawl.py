import uuid
from app.respositories import PageRepository
from pathlib import Path
from utils.files import file_sha256
import datetime
from app.models import JobStatus, Page, PageStatus
import argparse
import asyncio

from pipeline.config import CrawlConfig
from pipeline.crawler import Crawler
from db.session import get_db_session
from app.respositories.source_repo import SourceRepository
from app.respositories.crawl_job_repo import CrawlJobRepository
from loguru import logger


try:
    from celery_app import celery
except Exception:
    celery = None


async def _crawl_source(task, job_id: str):

    async with get_db_session() as session:
        job_repo = CrawlJobRepository(session)
        source_repo = SourceRepository(session)

        page_repo = PageRepository(session)

        crawl_job = await job_repo.get_by_id(job_id=job_id)

        source = await source_repo.get_by_id(source_id=crawl_job.source_id)

        logger.info(f"CrawlTask: Started for job ID {job_id}")

        # Mark job as running
        await job_repo.update(crawl_job, status=JobStatus.RUNNING)

        try:
            config = CrawlConfig.from_source(source)

            crawler = Crawler(config)

            result = await crawler.crawl()

            for page in result.pages:
                # TODO: Remove hardcoded path
                file_path = Path("/home/ropalim/Workspace/docsmcp/uploads/") / str(
                    uuid.uuid4()
                )

                with open(file_path, "w") as file:
                    file.write(page.html)

                file_hash = file_sha256(file_path.absolute())

                # TODO: Peform bulk operation
                await page_repo.create(
                    source_id=source.id,
                    url=page.url,
                    content_hash=file_hash,
                    file_path=str(file_path),
                )

                # TODO: Handle failed URLS

        except Exception as exc:
            logger.info(f"CrawlTask Error: {exc}")
            if task is not None:
                logger.info(f"CrawlTask Retry: {task}")
                raise task.retry(exc=exc)
            raise


def run_crawl_job(job_id: str):
    """
    Run a crawl job directly without requiring Celery worker orchestration.
    """
    asyncio.run(_crawl_source(None, job_id))


if celery is not None:

    @celery.task(
        bind=True,
        queue="crawl",
        max_retries=3,
        default_retry_delay=60,
        name="worker.tasks.crawl.crawl_source_task",
    )
    def crawl_source_task(self, job_id: str):
        """
        Top level task, Discovers all URLS and then fan-out
        """
        asyncio.run(_crawl_source(self, job_id))
else:

    def crawl_source_task(job_id: str):
        """
        Local fallback for non-Celery runs.
        """
        run_crawl_job(job_id)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run crawler for an existing crawl job id"
    )
    parser.add_argument("job_id", help="Crawl job UUID to run")
    args = parser.parse_args()
    run_crawl_job(args.job_id)
