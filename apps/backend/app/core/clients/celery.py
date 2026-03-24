from celery import Celery

from app.core.settings import settings

celery_client = Celery(
    "docsmcp_backend",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)
