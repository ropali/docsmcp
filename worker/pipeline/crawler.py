import asyncio
import time
from collections import deque
from dataclasses import field
from urllib.parse import urlparse

from pydantic.dataclasses import dataclass

from pipeline.config import CrawlConfig
from pipeline.fetchers import BaseFetcher, FetcherFactory, HttpFetcher
from utils.url_utils import (
    extract_links,
    fetch_robots_txt,
    is_html_link,
    is_same_domain,
    matches_patterns,
    normalize_url,
)

from loguru import logger


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
        logger.info(f"URL discovery started from URL: {self.config.base_url}")
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

                logger.info("Visiting URL: {url}")

                if not robots.can_fetch(self.config.user_agent, url):
                    continue

                await self._rate_limit(url)
                html = await fetcher.fetch(url, self.config.request_timeout)

                if html is None:
                    logger.info("HTML content not found for URL: {url}")
                    continue

                discovered.append(url)

                if depth < self.config.max_depth:
                    for child_url in self._filter_urls(extract_links(html, url)):
                        if child_url not in visited:
                            visited.add(child_url)
                            queue.append((child_url, depth + 1))

        finally:
            await fetcher.close()
        logger.info(f"Discovered {len(discovered)} URLS.")
        return discovered

    async def crawl(self) -> CrawlResult:
        """Full Crawl"""
        robots = await fetch_robots_txt(self.config.base_url, self.config.user_agent)

        result = CrawlResult()

        queue: deque[tuple[str, int]] = deque()

        normalized_url = normalize_url(self.config.base_url)

        queue.append((normalized_url, 0))

        self._visited.add(normalized_url)

        try:
            while queue and len(result.pages) < self.config.max_pages:
                url, depth = queue.popleft()

                logger.info(f"Crawling URL: {url}")

                if not robots.can_fetch(self.config.user_agent, url):
                    result.skipped_urls.append(url)
                    continue

                # Fetch with rate limiting
                await self._rate_limit(url)

                html = await self._fetcher.fetch(url, self.config.request_timeout)

                if html is None:
                    logger.info(f"HTML content found for URL: {url}")
                    result.failed_urls.append(url)
                    continue

                result.pages.append(CrawlPage(url, html, depth))

                # Discover child links only if we haven't hit max depth
                if depth < self.config.max_depth:
                    child_urls = self._filter_urls(extract_links(html, url))

                    for child_url in child_urls:
                        self._visited.add(child_url)
                        queue.append((child_url, depth + 1))
        except Exception as e:
            logger.error(f"Crawler Error: {e}")
            raise e

        finally:
            await self._fetcher.close()

        return result

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
                logger.info(f"Skipping URL - Not same domain: {url}")
                continue

            if not is_html_link(url):
                logger.info(f"Skipping URL - No HTML Content: {url}")
                continue

            if self.config.url_patterns:
                if not matches_patterns(url, self.config.url_patterns):
                    logger.info(f"Skipping URL - Pattern Not Matched: {url}")
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
