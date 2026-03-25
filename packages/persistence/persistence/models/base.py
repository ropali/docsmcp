from sqlalchemy import MetaData
from sqlalchemy.orm import declarative_base

from common.settings import settings

Base = declarative_base(metadata=MetaData(schema=settings.POSTGRES_SCHEMA))
