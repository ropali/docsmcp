from __future__ import annotations

import mimetypes
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path, PurePosixPath
from typing import Iterator
from urllib.parse import urlparse

import boto3
from botocore.client import Config

from common.settings import settings


def _normalize_object_key(object_key: str) -> str:
    key = PurePosixPath(object_key)
    if key.is_absolute() or ".." in key.parts:
        raise ValueError(f"Invalid object key: {object_key}")
    return key.as_posix()


class StorageService(ABC):
    @abstractmethod
    def upload_bytes(
        self,
        *,
        object_key: str,
        body: bytes,
        content_type: str | None = None,
    ) -> str: ...

    @abstractmethod
    def download_file(self, *, storage_path: str) -> "StorageDownload": ...


@dataclass
class StorageDownload:
    stream: Iterator[bytes]
    content_type: str | None = None
    content_length: int | None = None
    filename: str | None = None


class S3StorageService(StorageService):
    def __init__(
        self,
        *,
        bucket_name: str,
        region: str,
        endpoint_url: str | None,
        access_key_id: str,
        secret_access_key: str,
        use_path_style: bool,
    ):
        self._bucket_name = bucket_name
        self._client = boto3.client(
            "s3",
            region_name=region,
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            config=Config(
                s3={"addressing_style": "path" if use_path_style else "auto"}
            ),
        )

    def upload_bytes(
        self,
        *,
        object_key: str,
        body: bytes,
        content_type: str | None = None,
    ) -> str:
        key = _normalize_object_key(object_key)
        kwargs: dict[str, str] = {}
        if content_type:
            kwargs["ContentType"] = content_type
        self._client.put_object(Bucket=self._bucket_name, Key=key, Body=body, **kwargs)
        return f"s3://{self._bucket_name}/{key}"

    def _extract_key(self, storage_path: str) -> str:
        if storage_path.startswith("s3://"):
            parsed = urlparse(storage_path)
            if parsed.netloc and parsed.netloc != self._bucket_name:
                raise ValueError(
                    f"Storage path bucket '{parsed.netloc}' does not match configured bucket."
                )
            return _normalize_object_key(parsed.path.lstrip("/"))
        return _normalize_object_key(storage_path)

    def download_file(self, *, storage_path: str) -> StorageDownload:
        key = self._extract_key(storage_path)
        response = self._client.get_object(Bucket=self._bucket_name, Key=key)
        body = response["Body"]

        def stream() -> Iterator[bytes]:
            try:
                yield from body.iter_chunks(chunk_size=settings.UPLOAD_CHUNK_SIZE)
            finally:
                body.close()

        return StorageDownload(
            stream=stream(),
            content_type=response.get("ContentType"),
            content_length=response.get("ContentLength"),
            filename=PurePosixPath(key).name,
        )


class LocalStorageService(StorageService):
    def __init__(self, *, root_dir: str):
        self._root = Path(root_dir)

    def upload_bytes(
        self,
        *,
        object_key: str,
        body: bytes,
        content_type: str | None = None,
    ) -> str:
        del content_type
        key = _normalize_object_key(object_key)
        destination = self._root / key
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(body)
        return str(destination)

    def _resolve_path(self, storage_path: str) -> Path:
        candidate = Path(storage_path)
        if not candidate.is_absolute():
            candidate = self._root / _normalize_object_key(storage_path)

        root_resolved = self._root.resolve()
        candidate_resolved = candidate.resolve()
        if (
            root_resolved != candidate_resolved
            and root_resolved not in candidate_resolved.parents
        ):
            raise ValueError("Storage path is outside configured local storage root.")
        return candidate_resolved

    def download_file(self, *, storage_path: str) -> StorageDownload:
        path = self._resolve_path(storage_path)
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"File not found: {storage_path}")

        def stream() -> Iterator[bytes]:
            with path.open("rb") as handle:
                while chunk := handle.read(settings.UPLOAD_CHUNK_SIZE):
                    yield chunk

        guessed_content_type, _ = mimetypes.guess_type(path.name)
        return StorageDownload(
            stream=stream(),
            content_type=guessed_content_type,
            content_length=path.stat().st_size,
            filename=path.name,
        )


@lru_cache
def get_storage_service() -> StorageService:
    backend = settings.STORAGE_BACKEND.strip().lower()
    if backend == "s3":
        return S3StorageService(
            bucket_name=settings.S3_BUCKET_NAME,
            region=settings.S3_REGION,
            endpoint_url=settings.S3_ENDPOINT_URL,
            access_key_id=settings.AWS_ACCESS_KEY_ID,
            secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            use_path_style=settings.S3_USE_PATH_STYLE,
        )
    if backend == "local":
        return LocalStorageService(root_dir=settings.FILE_UPLOAD_DIR)
    raise ValueError(f"Unsupported STORAGE_BACKEND: {settings.STORAGE_BACKEND}")
