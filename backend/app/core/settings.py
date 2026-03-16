from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings/configuration class"""

    # Database Settings
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

    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "DocsMCP"
    DEBUG: bool = False

    VERSION: str = "1.0.0"

    # Logging Settings
    LOG_LEVEL: str = Field(default="INFO", alias="LOG_LEVEL")
    LOG_JSON: bool = Field(default=False, alias="LOG_JSON")
    LOG_FILE_ENABLED: bool = Field(default=False, alias="LOG_FILE_ENABLED")
    LOG_FILE_PATH: str = Field(default="logs/docsmcp.log", alias="LOG_FILE_PATH")
    LOG_FILE_ROTATION: str = Field(default="50 MB", alias="LOG_FILE_ROTATION")
    LOG_FILE_RETENTION: str = Field(default="14 days", alias="LOG_FILE_RETENTION")
    LOG_FILE_COMPRESSION: str = Field(default="gz", alias="LOG_FILE_COMPRESSION")

    # File Upload Settings
    FILE_UPLOAD_DIR: str = Field(
        default="/tmp/docsmcp_uploads",
        alias="FILE_UPLOAD_DIR",
    )

    # CORS Settings
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000"],
        alias="CORS_ORIGINS",
    )
    CORS_METHODS: list[str] = Field(default=["*"], alias="CORS_METHODS")
    CORS_HEADERS: list[str] = Field(default=["*"], alias="CORS_HEADERS")

    model_config = SettingsConfigDict(
        env_file=("backend/.env", ".env"),
        case_sensitive=True,
    )


@lru_cache
def get_settings() -> Settings:
    """
    Creates and returns a cached instance of the settings.
    Use this function to get settings throughout the application.
    """
    return Settings()


settings = Settings()
