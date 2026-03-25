from persistence.db.postgres import get_db_session
import asyncio
import uuid

from common.settings import settings
from common.storage import get_storage_service
from persistence.repositories import PageRepository
from functools import lru_cache
from rag.splitters.text_splitter import RecursiveCharacterSplitter
from rag.loaders import HTMLLoader
from rag.store.chroma_store import ChromaVectorStore
from rag.embedding.embedders import LocalEmbedder
from rag.pipeline.ingestion import IngestionPipeline
from rag.celery_app import celery

from rag.pipeline.ingestion import Page as IngestPage

from loguru import logger


@lru_cache(maxsize=1)
def get_pipeline() -> IngestionPipeline:

    collection = settings.VECTOR_COLLECTION_NAME
    logger.info(f"COLLECTION NAME {collection}")
    embedder = LocalEmbedder()
    store = ChromaVectorStore(collection_name=collection)

    return IngestionPipeline(
        loader=HTMLLoader(),
        splitter=RecursiveCharacterSplitter(chunk_size=512, overlap=64),
        embedder=embedder,
        store=store,
    )


async def _ingest_page(page_id: uuid.UUID) -> None:
    logger.info(f"Ingesting Page with ID {page_id}")

    pipeline = get_pipeline()

    file_storage = get_storage_service()

    async with get_db_session() as session:
        page_repo = PageRepository(session)

        page = await page_repo.get_by_id(page_id=page_id)

        if not page:
            logger.info(f"Page not found with ID {page_id}")
            return

        file = file_storage.download_file(storage_path=page.file_path)

        logger.info(f"File downloaded for ingestion {page.file_path}")

        parts = []

        for chunk in file.stream:
            parts.append(chunk)

        raw = b"".join(parts)

        html = raw.decode("utf-8", errors="replace")

        pipeline.run([IngestPage(html=html, url=page.url, title=page.title)])

        logger.info(f"Ingested page with ID {page.id}")


if celery is not None:

    @celery.task(
        bind=True,
        queue="embed",
        max_retries=3,
        default_retry_delay=60,
        name="crawler.tasks.embed.ingest_page",
    )
    def ingest_page(task, page_id: str):
        try:
            parsed_page_id = uuid.UUID(str(page_id))
            asyncio.run(_ingest_page(parsed_page_id))
        except Exception as exc:
            logger.exception(f"Ingest task failed for page_id={page_id}: {exc}")
            raise task.retry(exc=exc)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Run crawler for an existing crawl job id"
    )
    parser.add_argument("job_id", help="Crawl job UUID to run")
    args = parser.parse_args()
    asyncio.run(_ingest_page(uuid.UUID(args.job_id)))
