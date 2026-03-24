from sqlalchemy import MetaData
from sqlalchemy.orm import declarative_base

from app.core.settings import settings

Base = declarative_base(metadata=MetaData(schema=settings.POSTGRES_SCHEMA))
