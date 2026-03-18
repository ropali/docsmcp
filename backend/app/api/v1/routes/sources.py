from app.core.settings import settings
from app.core.clients.celery import celery_client
import hashlib
import uuid
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.models import SourceStatus, SourceType
from app.schemas.generic import JSONResponse
from app.api.deps import PageRepoDep, SourceRepoDep, CrawlJobRepoDep
from app.schemas.source import SourceResponse, SourceCreate, SourceCreateResponse
from app.services.storage import StorageService, get_storage_service


source_router = APIRouter(prefix="/sources", tags=["sources"])


async def _upload_file_to_storage(
    file: UploadFile, object_key: str, storage: StorageService
) -> tuple[int, str, str]:
    hasher = hashlib.sha256()
    size = 0
    payload = bytearray()
    content_type = file.content_type

    while chunk := await file.read(settings.UPLOAD_CHUNK_SIZE):
        payload.extend(chunk)
        hasher.update(chunk)
        size += len(chunk)

    await file.close()
    storage_uri = storage.upload_bytes(
        object_key=object_key,
        body=bytes(payload),
        content_type=content_type,
    )
    return size, hasher.hexdigest(), storage_uri


@source_router.get("/", response_model=list[SourceResponse])
async def get_all_sources(repo: SourceRepoDep) -> list[SourceResponse]:
    rows = await repo.list()
    return [SourceResponse.model_validate(r, from_attributes=True) for r in rows]


@source_router.get("/{id:uuid}", response_model=SourceResponse)
async def get_source_by_id(id: uuid.UUID, repo: SourceRepoDep) -> SourceResponse:
    source = await repo.get_by_id(source_id=id)

    return SourceResponse.model_validate(source, from_attributes=True)


@source_router.post("", response_model=SourceCreateResponse)
async def create_new_source(
    source: SourceCreate, repo: SourceRepoDep, crawl_job_repo: CrawlJobRepoDep
):

    response = await repo.create(
        **source.model_dump(exclude_none=True), status=SourceStatus.CRAWLING
    )

    if response:
        job = await crawl_job_repo.create(source_id=response.id)
        celery_client.send_task(
            "worker.tasks.crawl.crawl_source_task",
            args=[str(job.id)],
            queue="crawl",
        )

    return SourceCreateResponse(
        status=status.HTTP_201_CREATED,
        message="source created.",
        data=SourceResponse.model_construct(response),
    )


@source_router.delete("/{id:uuid}", response_model=JSONResponse)
async def delete_source_by_id(id: uuid.UUID, repo: SourceRepoDep) -> JSONResponse:
    await repo.delete(source_id=id)

    return JSONResponse(status=status.HTTP_200_OK, message="Record deleted.")


@source_router.post("/{id:uuid}/refresh")
async def refresh_source_by_id(id: uuid.UUID, repo: CrawlJobRepoDep):
    sources = await repo.list_by_source_id(source_id=id)

    if not sources:
        return JSONResponse(
            status=status.HTTP_404_NOT_FOUND,
            message="Source Does not Exist",
        )

    task = celery_client.send_task(
        "worker.tasks.crawl.crawl_source_task",
        args=[str(sources[0].id)],
        queue="crawl",
    )

    # TODO: Update job id of the job

    return JSONResponse(
        status=status.HTTP_200_OK, message="Re-trigger source crawling/processing"
    )


@source_router.post(
    "/upload",
    response_model=JSONResponse,
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "required": ["source_id", "files"],
                        "properties": {
                            "source_id": {
                                "type": "string",
                                "format": "uuid",
                                "description": "Existing source ID to attach files to",
                            },
                            "files": {
                                "type": "array",
                                "items": {"type": "string", "format": "binary"},
                                "description": "One or more files to upload",
                            },
                        },
                    }
                }
            },
        }
    },
)
async def upload_source_files(
    source_id: Annotated[uuid.UUID, Form(...)],
    files: Annotated[
        list[UploadFile],
        File(
            ...,
            description="One or more files to upload",
            media_type="multipart/form-data",
        ),
    ],
    repo: SourceRepoDep,
    page_repo: PageRepoDep,
    crawl_job_repo: CrawlJobRepoDep,
) -> JSONResponse:
    source = await repo.get_by_id(source_id=source_id)
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Source not found."
        )
    if source.source_type != SourceType.FILE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploads are only supported for FILE-type sources.",
        )

    valid_files = [f for f in files if f.filename]
    if not valid_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No files were provided."
        )

    storage = get_storage_service()
    uploaded_files: list[dict] = []

    for file in valid_files:
        original_name = (
            (file.filename or "upload.bin").rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
        )
        stored_name = f"{uuid.uuid4()}_{original_name}"
        object_key = f"sources/{source.id}/{stored_name}"
        size, content_hash, file_uri = await _upload_file_to_storage(
            file, object_key, storage
        )

        page = await page_repo.create(
            source_id=source.id,
            title=original_name,
            file_path=file_uri,
            content_hash=content_hash,
        )
        uploaded_files.append(
            {
                "file_id": page.id,
                "filename": original_name,
                "file_path": file_uri,
                "size": size,
            }
        )

    await repo.update_progress(
        source,
        page_count=source.page_count + len(uploaded_files),
        status=SourceStatus.PROCESSING,
    )

    await crawl_job_repo.create(source_id=source.id)
    # TODO: Send this job to celery queue

    return JSONResponse(
        status=status.HTTP_201_CREATED,
        message="Files uploaded and linked to source.",
        data={"source_id": source.id, "files": uploaded_files},
    )


@source_router.get("/{id:uuid}/files")
async def list_all_files_by_source(id: uuid.UUID):
    """List files attached to a FILE-type source"""
    # TODO: Implement this API
