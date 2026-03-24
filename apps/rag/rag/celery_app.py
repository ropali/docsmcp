from celery import Celery
from common.settings import settings
from common.logging import set_logger

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
    "docsmcp_rag_ingestion",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery.conf.update(
    task_serializer="json",
    result_expires=3600,
    task_acks_late=True,  # only ack after task succeeds
    worker_prefetch_multiplier=1,  # one task at a time per crawler process
    task_routes={
        "crawler.tasks.embed.*": {"queue": "embed"},
    },
)

celery.autodiscover_tasks(["rag"], related_name="tasks", force=True)
