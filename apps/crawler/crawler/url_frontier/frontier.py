import asyncio
import re
from collections import deque
from dataclasses import dataclass, field
from xml.etree import ElementTree as ET
from urllib.parse import urlparse

import aiohttp
from common import set_logger

from crawler.utils.url_utils import normalize_url

logger = set_logger()

_NOISE_PATTERNS = re.compile(
    r"(/page/\d+|/p/\d+|\?page=|\?p=|/tag/|/category/|/author/|"
    r"/login|/signin|/signup|/register|/cart|/checkout|"
    r"\.(css|js|png|jpg|jpeg|gif|svg|ico|woff|woff2|ttf|pdf|zip)$)",
    re.IGNORECASE,
)


@dataclass
class FrontierURL:
    url: str
    depth: int = 0
    metadata: dict = field(default_factory=dict)


class URLFrontier:
    def __init__(self, max_depth: int = 5, filter_noise: bool = True):
        self.max_depth = max_depth
        self.filter_noise = filter_noise
        self._queue: deque[FrontierURL] = deque()
        self._seen: set[str] = set()
        self._lock = asyncio.Lock()

    async def push(self, url: str, depth: int, metadata: dict) -> bool:
        """Enqueue url, returns False if rejected"""
        url = normalize_url(url)
        if not url:
            return False
        if depth > self.max_depth:
            return False
        if url in self._seen:
            return False

        if self.filter_noise and _NOISE_PATTERNS.search(url):
            return False

        async with self._lock:
            self._seen.add(url)
            self._queue.append(
                FrontierURL(url=url, depth=depth, metadata=metadata or {})
            )

        return True

    async def pop(self) -> FrontierURL | None:
        async with self._lock:
            if self._queue:
                return self._queue.popleft()
            return None

    def __len__(self) -> int:
        return len(self._queue)


def sitemap_candidates(base_url: str) -> list[str]:
    parsed = urlparse(normalize_url(base_url))
    root = f"{parsed.scheme}://{parsed.netloc}"
    return [
        f"{root}/sitemap.xml",
        f"{root}/sitemap_index.xml",
        f"{root}/sitemap-index.xml",
        f"{root}/sitemap/sitemap.xml",
    ]


async def sitemap_urls_from_robots(
    base_url: str,
    session: aiohttp.ClientSession,
) -> list[str]:
    parsed = urlparse(normalize_url(base_url))
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    try:
        async with session.get(
            robots_url, timeout=aiohttp.ClientTimeout(total=10)
        ) as resp:
            if resp.status >= 400:
                return []
            text = await resp.text()
    except Exception as exc:
        logger.info("robots.txt sitemap discovery failed for %s: %s", robots_url, exc)
        return []

    sitemap_urls: list[str] = []
    for line in text.splitlines():
        if line.lower().startswith("sitemap:"):
            sitemap_url = line.split(":", 1)[1].strip()
            if sitemap_url:
                sitemap_urls.append(normalize_url(sitemap_url))
    return sitemap_urls


async def urls_from_sitemap(
    sitemap_url: str,
    session: aiohttp.ClientSession,
) -> list[str]:
    """
    Recursively fetch and parse sitemap XML.
    Handles both <urlset> (standard) and <sitemapindex> (nested).

    RAG benefit: gives you the complete URL set upfront with zero
    crawl-time discovery cost — no scoring trade-offs needed.
    """
    try:
        async with session.get(
            sitemap_url, timeout=aiohttp.ClientTimeout(total=15)
        ) as resp:
            resp.raise_for_status()
            text = await resp.text()
    except Exception as exc:
        logger.warning("Sitemap fetch failed %s: %s", sitemap_url, exc)
        return []

    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        logger.error("Sitemap XML parse error at %s: %s", sitemap_url, exc)
        return []

    ns_match = re.match(r"\{(.*?)\}", root.tag)
    ns = f"{{{ns_match.group(1)}}}" if ns_match else ""

    # Sitemap index — recurse into child sitemaps
    if root.tag.endswith("sitemapindex"):
        child_locs = [el.text for el in root.findall(f"{ns}sitemap/{ns}loc") if el.text]
        results: list[str] = []
        for child_url in child_locs:
            results.extend(await urls_from_sitemap(child_url, session))
        return results

    # Standard urlset
    return [el.text for el in root.findall(f"{ns}url/{ns}loc") if el.text]


async def seed_from_sitemap(
    frontier: URLFrontier,
    sitemap_url: str,
    session: aiohttp.ClientSession,
) -> int:
    """Fetch sitemap and push all URLs into the frontier at depth=0."""
    urls = await urls_from_sitemap(sitemap_url, session)
    accepted = sum([await frontier.push(u, depth=0, metadata={}) for u in urls])
    logger.info(
        "Sitemap seeding: %d/%d URLs accepted from %s", accepted, len(urls), sitemap_url
    )
    return accepted


async def seed_from_site_sitemap(
    frontier: URLFrontier,
    base_url: str,
    user_agent: str,
) -> tuple[int, list[str]]:
    headers = {"User-Agent": user_agent}
    discovered_sitemaps: list[str] = []

    async with aiohttp.ClientSession(headers=headers) as session:
        candidates = await sitemap_urls_from_robots(base_url, session)
        candidates.extend(sitemap_candidates(base_url))

        accepted = 0
        seen_sitemaps: set[str] = set()
        for sitemap_url in candidates:
            normalized = normalize_url(sitemap_url)
            if normalized in seen_sitemaps:
                continue
            seen_sitemaps.add(normalized)

            seeded = await seed_from_sitemap(frontier, normalized, session)
            if seeded <= 0:
                continue

            discovered_sitemaps.append(normalized)
            accepted += seeded

        return accepted, discovered_sitemaps
