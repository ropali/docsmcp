from enum import Enum
from typing import Any
from app.models import SourceType, SourceStatus
import uuid
from pydantic import BaseModel, AnyUrl, field_validator


class Source(BaseModel):
    id: uuid.UUID | None
    name: str
    source_type: SourceType
    base_url: str
    status: SourceStatus


class SourceResponse(Source):
    pass


class SourceCreate(BaseModel):
    name: str
    source_type: SourceType
    base_url: str

    @field_validator("base_url", mode="before")
    @classmethod
    def validate_url(cls, val):
        return str(AnyUrl(val))


class SourceCreateResponse(BaseModel):
    status: int
    data: Any
    message: str
