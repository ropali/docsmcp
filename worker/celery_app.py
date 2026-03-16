import asyncio

from celery.signals import worker_process_shutdown
from celery import Celery
from app.core.settings import settings
from app.core.logging import set_logger
from worker.db.session import auto_close_db

set_logger(
    log_level=settings.LOG_LEVEL,
    json_logs=settings.LOG_JSON,
    log_file_enabled=settings.LOG_FILE_ENABLED,
    log_file_path=settings.LOG_FILE_PATH,
    file_rotation=settings.LOG_FILE_ROTATION,
    file_retention=settings.LOG_FILE_RETENTION,
    file_compression=settings.LOG_FILE_COMPRESSION,
)

celery = Celery(
    "docsmcp_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery.conf.update(
    task_serializer="json",
    result_expires=3600,
    task_acks_late=True,  # only ack after task succeeds
    worker_prefetch_multiplier=1,  # one task at a time per worker
    task_routes={
        "worker.tasks.crawl.*": {"queue": "crawl"},
        "worker.tasks.embed.*": {"queue": "embed"},
    },
)

celery.autodiscover_tasks(["worker"], related_name="tasks", force=True)


@worker_process_shutdown.connect
def worker_shutdown_event(*args, **kwargs):
    asyncio.run(auto_close_db())
