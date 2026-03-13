from app.models.base import Base
from pipeline.config import CrawlConfig
from traceback import print_tb
import time
import httpx
from abc import ABC, abstractmethod


class BaseFetcher(ABC):
    @abstractmethod
    async def fetch(self, url: str, timeout: int) -> str | None:
        """Returns raw HTML string or None on failure"""

    async def close(self):
        pass


class HttpFetcher(BaseFetcher):
    def __init__(self, user_agent: str):
        self._client = httpx.AsyncClient(
            headers={"User-Agent": user_agent}, follow_redirects=True
        )

    async def fetch(self, url: str, timeout: int) -> str | None:
        try:
            response = await self._client(url, timeout=timeout)
            response.raise_for_status()

            # Only process HTML response
            ct = response.headers.get("content-type", "")

            if "text/html" not in ct:
                return None

            return response.text
        except httpx.HTTPError as e:
            print("Worker Error: ", e)
            return None

    async def close(self):
        await self._client.aclose()


class PlaywrightFetcher(BaseFetcher):
    # TODO: Implement playwright base fetcher to handle SPAs
    async def fetch(self, url: str, timeout: int) -> str | None:
        raise NotImplementedError()


class FetcherFactory:
    @staticmethod
    def create(config: CrawlConfig) -> BaseFetcher:
        if config.js_render:
            return PlaywrightFetcher()

        return HttpFetcher(user_agent=config.user_agent)
