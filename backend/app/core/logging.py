import logging
import os
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TextIO

from loguru import logger

DEFAULT_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level:<8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)

DEFAULT_JSON_FORMAT = "{time} {level} {name}:{function}:{line} {message}"

_configured = False

SinkType = str | Path | TextIO | logging.Handler | Callable[[str], None]


@dataclass(slots=True)
class SinkConfig:
    sink: SinkType
    level: str = "INFO"
    format: str | None = None
    kwargs: dict[str, Any] = field(default_factory=dict)


class InterceptHandler(logging.Handler):
    def emit(self, record):
        logger_opt = logger.opt(depth=6, exception=record.exc_info)
        logger_opt.log(record.levelname, record.getMessage())


def configure_logging(
    *,
    log_level: str | None = None,
    json_logs: bool | None = None,
    log_file_path: str | None = None,
    log_file_enabled: bool | None = None,
    file_rotation: str | None = None,
    file_retention: str | None = None,
    file_compression: str | None = None,
    extra_sinks: Sequence[SinkConfig] | None = None,
) -> None:
    global _configured
    if _configured:
        return

    resolved_level = (log_level or os.getenv("LOG_LEVEL", "INFO")).upper()
    resolved_json_logs = (
        json_logs
        if json_logs is not None
        else os.getenv("LOG_JSON", "false").lower() in ("1", "true", "yes")
    )
    resolved_log_file_enabled = (
        log_file_enabled
        if log_file_enabled is not None
        else os.getenv("LOG_FILE_ENABLED", "false").lower() in ("1", "true", "yes")
    )
    resolved_log_file_path = (
        log_file_path or os.getenv("LOG_FILE_PATH", "logs/docsmcp.log")
    )
    resolved_rotation = file_rotation or os.getenv("LOG_FILE_ROTATION", "50 MB")
    resolved_retention = file_retention or os.getenv("LOG_FILE_RETENTION", "14 days")
    resolved_compression = file_compression or os.getenv("LOG_FILE_COMPRESSION", "gz")
    resolved_format = DEFAULT_JSON_FORMAT if resolved_json_logs else DEFAULT_FORMAT

    logger.remove()
    logger.add(
        sys.stdout,
        level=resolved_level,
        format=resolved_format,
        serialize=resolved_json_logs,
        backtrace=True,
        diagnose=False,
        enqueue=True,
    )

    if resolved_log_file_enabled:
        file_path = Path(resolved_log_file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            str(file_path),
            level=resolved_level,
            format=resolved_format,
            serialize=resolved_json_logs,
            enqueue=True,
            rotation=resolved_rotation,
            retention=resolved_retention,
            compression=resolved_compression,
            backtrace=True,
            diagnose=False,
        )

    for sink_config in extra_sinks or ():
        sink_format = sink_config.format or resolved_format
        logger.add(
            sink_config.sink,
            level=sink_config.level,
            format=sink_format,
            serialize=resolved_json_logs,
            enqueue=True,
            backtrace=True,
            diagnose=False,
            **sink_config.kwargs,
        )

    logging.basicConfig(
        handlers=[InterceptHandler()],
        level=resolved_level,
        force=True,
    )

    loggers = [
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error",
        "gunicorn",
        "gunicorn.access",
        "gunicorn.error",
    ]

    for logger_name in loggers:
        ext_logger = logging.getLogger(logger_name)
        ext_logger.handlers = [InterceptHandler()]
        ext_logger.propagate = False

    _configured = True


def set_logger(**kwargs: Any) -> None:
    """
    Backward-compatible wrapper for existing imports.
    """
    configure_logging(**kwargs)
