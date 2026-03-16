from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from loguru import logger

from app.api.exceptions import validation_exception_handler
from app.api.main import api_router
from app.core.settings import settings
from app.core.events import shutdown_db_clients, startup_db_clients
from app.core.logging import set_logger

# try:
#     from app.metrics import setup_metrics
# except ImportError:
#     setup_metrics = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    logger.info("Starting application")
    await startup_db_clients(app)
    yield
    logger.info("Stopping application")
    await shutdown_db_clients(app)


def get_application() -> FastAPI:
    """Returns a FastAPI application instance."""
    set_logger(
        log_level=settings.LOG_LEVEL,
        json_logs=settings.LOG_JSON,
        log_file_enabled=settings.LOG_FILE_ENABLED,
        log_file_path=settings.LOG_FILE_PATH,
        file_rotation=settings.LOG_FILE_ROTATION,
        file_retention=settings.LOG_FILE_RETENTION,
        file_compression=settings.LOG_FILE_COMPRESSION,
    )
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_version="3.0.3",
        lifespan=lifespan,
        debug=settings.DEBUG,
        docs_url="/docs",
        default_response_class=ORJSONResponse,
    )

    app.include_router(api_router)

    # if setup_metrics is not None:
    #     setup_metrics(app, metrics_endpoint=False, metrics_port=8001)
    #
    if settings.CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ORIGINS,
            allow_methods=settings.CORS_METHODS,
            allow_headers=settings.CORS_HEADERS,
            allow_credentials=True,
        )

    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    return app


app = get_application()
