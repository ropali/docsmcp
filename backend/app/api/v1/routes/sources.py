import hashlib
from pathlib import Path
import uuid
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.core.settings import settings
from app.models import SourceStatus, SourceType
from app.schemas.generic import JSONResponse
from app.api.deps import PageRepoDep, SourceRepoDep
from app.schemas.source import SourceResponse, SourceCreate, SourceCreateResponse


source_router = APIRouter(prefix="/sources")
UPLOAD_CHUNK_SIZE = 1024 * 1024


async def _write_upload_to_disk(file: UploadFile, destination: Path) -> tuple[int, str]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    hasher = hashlib.sha256()
    size = 0

    with destination.open("wb") as output:
        while chunk := await file.read(UPLOAD_CHUNK_SIZE):
            output.write(chunk)
            hasher.update(chunk)
            size += len(chunk)

    await file.close()
    return size, hasher.hexdigest()


@source_router.get("/", response_model=list[SourceResponse])
async def get_all_sources(repo: SourceRepoDep) -> list[SourceResponse]:
    rows = await repo.list()
    return [SourceResponse.model_validate(r, from_attributes=True) for r in rows]


@source_router.get("/{id}", response_model=SourceResponse)
async def get_source_by_id(id: uuid.UUID, repo: SourceRepoDep) -> SourceResponse:
    source = await repo.get_by_id(source_id=id)

    return SourceResponse.model_validate(source, from_attributes=True)


@source_router.post("", response_model=SourceCreateResponse)
async def create_new_source(source: SourceCreate, repo: SourceRepoDep):
    response = await repo.create(**source.model_dump(exclude_none=True))

    return SourceCreateResponse(
        status=status.HTTP_201_CREATED,
        message="source created.",
        data=SourceResponse.model_construct(response),
    )


@source_router.post("/{id}", response_model=JSONResponse)
async def refresh_source_by_id(id: uuid.UUID, repo: SourceRepoDep) -> JSONResponse:
    source = await repo.get_by_id(source_id=id)

    if source:
        await repo.update_progress(source, status=SourceStatus.PROCESSING)

        return JSONResponse(
            status=status.HTTP_200_OK,
            message=f"Resource with ID {source.id} is added in the queue for processing.",
        )

    return JSONResponse(status=status.HTTP_404_NOT_FOUND, message="Resource not found.")


@source_router.delete("/{id}", response_model=JSONResponse)
async def delete_source_by_id(id: uuid.UUID, repo: SourceRepoDep) -> JSONResponse:
    await repo.delete(source_id=id)

    return JSONResponse(status=status.HTTP_200_OK, message="Record deleted.")


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

    upload_dir = Path(settings.FILE_UPLOAD_DIR) / str(source.id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    uploaded_files: list[dict] = []

    for file in valid_files:
        original_name = Path(file.filename or "upload.bin").name
        stored_name = f"{uuid.uuid4()}_{original_name}"
        saved_path = upload_dir / stored_name
        size, content_hash = await _write_upload_to_disk(file, saved_path)

        page = await page_repo.create(
            source_id=source.id,
            title=original_name,
            file_path=str(saved_path),
            content_hash=content_hash,
        )
        uploaded_files.append(
            {
                "file_id": page.id,
                "filename": original_name,
                "file_path": str(saved_path),
                "size": size,
            }
        )

    await repo.update_progress(
        source,
        page_count=source.page_count + len(uploaded_files),
        status=SourceStatus.PENDING,
    )

    return JSONResponse(
        status=status.HTTP_201_CREATED,
        message="Files uploaded and linked to source.",
        data={"source_id": source.id, "files": uploaded_files},
    )


@source_router.get("/sources/{id}/pages")
async def list_all_pages_by_source_id(id: uuid.UUID, page_repo: PageRepoDep):
    pages = await page_repo.list(source_id=id)

    return pages
