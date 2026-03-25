from persistence.models import Source
from pydantic import BaseModel, field_validator


class CrawlConfig(BaseModel):
    base_url: str
    max_depth: int = 5
    max_pages: int = 5
    url_patterns: list[str] = []
    exclude_patterns: list[str] = []

    chunk_size: int = 512
    chunk_overlap: int = 64
    refersh_interval: int | None = 5
    js_render: bool | None = None
    rate_limit_delay: int = 2
    request_timeout: int = 10
    user_agent: str = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"

    @field_validator("base_url")
    @classmethod
    def normalize_base_url(cls, v: str) -> str:
        return v.rstrip("/")

    @classmethod
    def from_source(cls, source: Source) -> CrawlConfig:
        return CrawlConfig(base_url=source.base_url, **source.config)
