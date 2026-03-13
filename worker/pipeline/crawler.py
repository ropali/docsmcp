import asyncio
from billiard.connection import wait
import time
from urllib.parse import urlparse
from turtle import ht
from collections import deque
from utils.url_utils import fetch_robots_txt, normalize_url, extract_links, is_same_domain, is_html_link, matches_patterns
from pipeline.fetchers import BaseFetcher, FetcherFactory, HttpFetcher
from pipeline.config import CrawlConfig
from dataclasses import field
from pydantic.dataclasses import dataclass


@dataclass
class CrawlPage:
    url: str
    html: str
    depth: int


@dataclass
class CrawlResult:
    pages: list[CrawlPage] = field(default_factory=list)
    failed_urls: list[str] = field(default_factory=list)
    skipped_urls: list[str] = field(default_factory=list)


class Crawler:
    """
    A breadth first crawler
    """

    def __init__(self, config: CrawlConfig):
        self.config = config
        self._fetcher: BaseFetcher = FetcherFactory.create(config)
        self._visited: set[str] = set()
        self._domain_last_fetch: dict[str, float] = {}

    async def discover_urls(self) -> list[str]:

        robots = await fetch_robots_txt(self.config.base_url, self.config.user_agent)

        discovered = []

        queue: deque[tuple[str, int]] = deque()

        start = normalize_url(self.config.base_url)

        queue.append((start, 0))
        visited: set[str] = {start}

        # use http fetcher for discovry only
        fetcher = HttpFetcher(user_agent=self.config.user_agent)

        try:
            while queue and len(discovered) < self.config.max_pages:
                url, depth = queue.popleft()

                if not robots.can_fetch(self.config.user_agent, url):
                    continue

                await self._rate_limit(url)
                html = await fetcher.fetch(url, self.config.request_timeout)

                if html is None:
                    continue

                discovered.append(url)

                if depth < self.config.max_depth:
                    for child_url in self._filter_urls(extract_links(html, url))
                        if child_url not in visited:
                            visited.add(child_url)
                            queue.append((child_url, depth + 1))

        finally:
            await fetcher.close()

        return discovered

    def _filter_urls(self, urls: list[str]) -> list[str]:
        """
        Apply all filtering rules
        1. Must be same domain
        2. Must look like and html page
        3. Must match whitelist (if configured)
        4. Must not match blacklist
        """

        filtered = []

        for url in urls:
            if not is_same_domain(url, self.config.base_url):
                continue

            if not is_html_link(url):
                continue

            if self.config.url_patterns:
                if not matches_patterns(url, self.config.url_patterns):
                    continue

            if matches_patterns(url, self.config.exclude_patterns):
                continue

            filtered.append(url)

        return filtered

    
    async def _rate_limit(self, url: str) -> None:
        domain = urlparse(url).netloc

        last = self._domain_last_fetch.get(domain, 0.0)
        elapsed = time.monotonic() - last

        wait = self.config.rate_limit_delay - elapsed

        if wait > 0:
            await asyncio.sleep(wait)

        self._domain_last_fetch[domain] = time.monotonic()
