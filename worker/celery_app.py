# worker/celery_app.py
from celery import Celery
from app.core.settings import settings

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
