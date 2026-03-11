from app.schemas.generic import JSONResponse
import uuid
from app.api.deps import SourceRepoDep
from app.schemas.source import SourceResponse, SourceCreate, SourceCreateResponse
from fastapi import APIRouter, status


source_router = APIRouter(prefix="/sources")


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


@source_router.delete("/{id}", response_model=JSONResponse)
async def delete_source_by_id(id: uuid.UUID, repo: SourceRepoDep) -> JSONResponse:
    await repo.delete(source_id=id)

    return JSONResponse(status=status.HTTP_200_OK, message="Record deleted.")
