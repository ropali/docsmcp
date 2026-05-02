import asyncio
import time
from dataclasses import field
from urllib.parse import urlparse

from pydantic.dataclasses import dataclass

from crawler.pipeline.config import CrawlConfig
from crawler.pipeline.fetchers import BaseFetcher, FetcherFactory, HttpFetcher
from crawler.url_frontier.frontier import URLFrontier, seed_from_site_sitemap
from crawler.utils.url_utils import (
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
        self._domain_last_fetch: dict[str, float] = {}
        self._frontier = URLFrontier(max_depth=config.max_depth)

    async def discover_urls(self) -> list[str]:
        logger.info(f"URL discovery started from URL: {self.config.base_url}")
        robots = await fetch_robots_txt(self.config.base_url, self.config.user_agent)

        discovered = []
        seeded_from_sitemap = await self._seed_discovery_frontier()

        # use http fetcher for discovry only
        fetcher = HttpFetcher(user_agent=self.config.user_agent)

        try:
            while len(self._frontier) and len(discovered) < self.config.max_pages:
                item = await self._frontier.pop()
                if item is None:
                    break

                url, depth = item.url, item.depth

                logger.info(f"Visiting URL: {url}")

                if not robots.can_fetch(self.config.user_agent, url):
                    continue

                await self._rate_limit(url)
                html = await fetcher.fetch(url, self.config.request_timeout)

                if html is None:
                    logger.info(f"HTML content not found for URL: {url}")
                    continue

                discovered.append(url)

                if not seeded_from_sitemap and depth < self.config.max_depth:
                    for child_url in self._filter_urls(extract_links(html, url)):
                        await self._frontier.push(
                            child_url, depth=depth + 1, metadata={}
                        )

        finally:
            await fetcher.close()
        logger.info(f"Discovered {len(discovered)} URLS.")
        return discovered

    async def crawl(self) -> CrawlResult:
        """Full Crawl"""
        robots = await fetch_robots_txt(self.config.base_url, self.config.user_agent)

        result = CrawlResult()
        seeded_from_sitemap = await self._seed_discovery_frontier()

        try:
            while len(self._frontier) and len(result.pages) < self.config.max_pages:
                item = await self._frontier.pop()
                if item is None:
                    break

                url, depth = item.url, item.depth

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

                # When sitemap discovery succeeds, the sitemap already defines the crawl set.
                if not seeded_from_sitemap and depth < self.config.max_depth:
                    child_urls = self._filter_urls(extract_links(html, url))

                    for child_url in child_urls:
                        await self._frontier.push(
                            child_url, depth=depth + 1, metadata={}
                        )
        except Exception as e:
            logger.error(f"Crawler Error: {e}")
            raise e

        finally:
            await self._fetcher.close()

        return result

    async def _seed_discovery_frontier(self) -> bool:
        self._frontier = URLFrontier(max_depth=self.config.max_depth)

        accepted, sitemap_urls = await seed_from_site_sitemap(
            self._frontier,
            self.config.base_url,
            self.config.user_agent,
        )

        if accepted > 0:
            logger.info(
                "Seeded frontier with %d URLs from sitemap(s): %s",
                accepted,
                ", ".join(sitemap_urls),
            )
            return True

        logger.info(
            "No sitemap URLs discovered for %s. Falling back to manual crawl discovery.",
            self.config.base_url,
        )
        await self._frontier.push(
            normalize_url(self.config.base_url), depth=0, metadata={}
        )
        return False

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
