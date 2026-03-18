from fastapi import APIRouter
from app.api.v1.routes.sources import source_router
from app.api.v1.routes.pages import pages_router

v1_router = APIRouter(prefix="/v1")

v1_router.include_router(source_router)
v1_router.include_router(pages_router)
