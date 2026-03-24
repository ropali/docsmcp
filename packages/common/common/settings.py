from functools import lru_cache

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Shared application settings."""

    STAGE: str = Field(default="dev", alias="STAGE")

    POSTGRES_DATABASE_URL: str = Field(
        default="postgresql+asyncpg://myuser:mypassword@localhost:5432/postgres",
        alias="DATABASE_URL",
        description="Database connection string",
    )
    PG_POOL_SIZE: int = Field(default=5, alias="PG_POOL_SIZE")
    PG_POOL_OVERFLOW: int = Field(default=10, alias="PG_POOL_OVERFLOW")
    POSTGRES_SCHEMA: str = Field(default="docs_mcp", alias="POSTGRES_SCHEMA")

    REDIS_URL: str | None = Field(
        default="redis://localhost:6379/0",
        alias="REDIS_URL",
        description="Redis connection string",
    )

    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "DocsMCP"
    VERSION: str = "1.0.0"

    LOG_LEVEL: str = Field(default="INFO", alias="LOG_LEVEL")
    LOG_JSON: bool = Field(default=False, alias="LOG_JSON")
    LOG_FILE_ENABLED: bool = Field(default=False, alias="LOG_FILE_ENABLED")
    LOG_FILE_PATH: str = Field(default="logs/docsmcp.log", alias="LOG_FILE_PATH")
    LOG_FILE_ROTATION: str = Field(default="50 MB", alias="LOG_FILE_ROTATION")
    LOG_FILE_RETENTION: str = Field(default="14 days", alias="LOG_FILE_RETENTION")
    LOG_FILE_COMPRESSION: str = Field(default="gz", alias="LOG_FILE_COMPRESSION")

    FILE_UPLOAD_DIR: str = Field(
        default="/tmp/docsmcp_uploads",
        alias="FILE_UPLOAD_DIR",
    )
    UPLOAD_CHUNK_SIZE: int = 1024 * 1024

    STORAGE_BACKEND: str = Field(default="s3", alias="STORAGE_BACKEND")
    S3_BUCKET_NAME: str = Field(default="docsmcp-dev", alias="S3_BUCKET_NAME")
    S3_REGION: str = Field(default="us-east-1", alias="S3_REGION")
    S3_ENDPOINT_URL: str | None = Field(
        default="http://localhost:4566",
        alias="S3_ENDPOINT_URL",
    )
    S3_USE_PATH_STYLE: bool = Field(default=True, alias="S3_USE_PATH_STYLE")
    AWS_ACCESS_KEY_ID: str = Field(default="test", alias="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: str = Field(default="test", alias="AWS_SECRET_ACCESS_KEY")

    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000"],
        alias="CORS_ORIGINS",
    )
    CORS_METHODS: list[str] = Field(default=["*"], alias="CORS_METHODS")
    CORS_HEADERS: list[str] = Field(default=["*"], alias="CORS_HEADERS")

    model_config = SettingsConfigDict(
        env_file=("apps/backend/.env", ".env"),
        case_sensitive=True,
    )


    @property
    def debug(self) -> bool:
        return self.STAGE == "dev"

    @computed_field
    @property
    def VECTOR_COLLECTION_NAME(self) -> str:
        return f"docsmcp-vectors-{self.STAGE}"


@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
