from app.services import StorageService
from app.api.deps import PageRepoDep
import uuid
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse

from app.services.storage import get_storage_service


pages_router = APIRouter(prefix="/pages", tags=["pages"])


@pages_router.get("/{source_id:uuid}/")
async def list_all_pages_by_source_id(source_id: uuid.UUID, page_repo: PageRepoDep):
    pages = await page_repo.list(source_id=source_id)

    return pages


@pages_router.get("/{page_id:uuid}/file/content/")
async def get_page_file_content(
    page_id: uuid.UUID,
    repo: PageRepoDep,
    storage: StorageService = Depends(get_storage_service),
):
    """Get page file content"""
    page = await repo.get_by_id(page_id)

    if not page:
        raise HTTPException(status_code=404, detail="Page not found.")
    if not page.file_path:
        raise HTTPException(status_code=404, detail="Page file is not available.")

    try:
        download = storage.download_file(storage_path=page.file_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Page file not found in storage.")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    headers: dict[str, str] = {}
    if download.content_length is not None:
        headers["Content-Length"] = str(download.content_length)
    if download.filename:
        headers["Content-Disposition"] = f'inline; filename="{download.filename}"'

    return StreamingResponse(
        download.stream,
        media_type=download.content_type or "application/octet-stream",
        headers=headers,
    )
