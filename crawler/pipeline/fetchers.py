from crawler.pipeline.config import CrawlConfig
from abc import ABC, abstractmethod
from urllib.parse import urlparse

import httpx

from crawler.pipeline.js_detector import JSRenderDetector

from loguru import logger


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
            response = await self._client.get(url, timeout=timeout)
            response.raise_for_status()

            # Only process HTML response
            ct = response.headers.get("content-type", "")

            if "text/html" not in ct:
                return None

            return response.text
        except httpx.HTTPError as e:
            logger.error(f"HttpFetcher Error: {e}")
            return None

    async def close(self):
        await self._client.aclose()


class PlaywrightFetcher(BaseFetcher):
    def __init__(self, user_agent: str):
        self._user_agent = user_agent
        self._playwright = None
        self._browser = None
        self._context = None

    async def _ensure_context(self):
        if self._context is not None:
            return self._context

        try:
            from playwright.async_api import async_playwright
        except ImportError as exc:
            logger.error(f"Playwright Error: {exc}")
            raise RuntimeError(
                "Playwright is not installed. Add the 'playwright' package and run "
                "'playwright install chromium' before enabling js_render."
            ) from exc

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=False)
        self._context = await self._browser.new_context(user_agent=self._user_agent)
        return self._context

    async def fetch(self, url: str, timeout: int) -> str | None:
        context = await self._ensure_context()
        page = await context.new_page()

        try:
            from playwright.async_api import TimeoutError as PlaywrightTimeoutError

            response = await page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=timeout * 1000,
            )

            # "networkidle" is unreliable for pages with long-polling/beacons.
            # If it times out, fall back to current DOM instead of failing fetch.
            try:
                await page.wait_for_load_state("networkidle", timeout=timeout * 1000)
            except PlaywrightTimeoutError:
                logger.warning(
                    "PlaywrightFetcher: networkidle timeout for {}; returning current DOM",
                    url,
                )

            await page.wait_for_selector("main, article")

            if response is not None:
                content_type = response.headers.get("content-type", "")

                if "text/html" not in content_type:
                    return None

            html = await page.locator("main").inner_html()

            if not html:
                # try for article tag
                html = await page.locator("article").inner_html()

            return html
        except Exception as e:
            logger.error(f"PlaywrightFetcher Error: {e}")
            return None
        finally:
            await page.close()

    async def close(self):
        if self._context is not None:
            await self._context.close()
            self._context = None

        if self._browser is not None:
            await self._browser.close()
            self._browser = None

        if self._playwright is not None:
            await self._playwright.stop()
            self._playwright = None


class AutoFetcher(BaseFetcher):
    """
    Tries http first. If JSRenderDetector says content is
    insufficient, retries with Playwright automatically.
    Caches the js_render decision per domain so subsequent
    pages from the same site skip the detection step.
    """

    def __init__(self, user_agent: str):
        self._http = HttpFetcher(user_agent=user_agent)
        self._playwright: PlaywrightFetcher = PlaywrightFetcher(user_agent=user_agent)
        self._user_agent = user_agent
        self._detector = JSRenderDetector()
        # domain -> bool cache so we only detect once per domain
        self._domain_needs_js: dict[str, bool] = {}

    async def fetch(self, url: str, timeout: int) -> str | None:
        domain = urlparse(url).netloc

        if domain in self._domain_needs_js:
            if self._domain_needs_js[domain]:
                return await self._playwright.fetch(url, timeout)
            else:
                return await self._http.fetch(url, timeout)

        # First visit to this domain to run detection
        html = await self._http.fetch(url, timeout)

        if html is None:
            # http fetcher has failed completely
            logger.info(f"AutoFetcher Error: Unable to fetch HTML content from {url}")
            # TODO: Handle this or use platwright to get the content
            raise ValueError(f"No HTML content found for url: {url}")

        result = self._detector.analyze(html)
        logger.info(f"Auto JS Detection Result: {result}")

        if result.needs_js:
            logger.info("AutoFetcher: URL Fetching Needs JS Renderer.")
            # Retry with playwright and cache the decision
            self._domain_needs_js[domain] = True
            return await self._playwright.fetch(url, timeout)

        else:
            self._domain_needs_js[domain] = False
            return html

    async def close(self):
        await self._http.close()
        if self._playwright:
            await self._playwright.close()


class FetcherFactory:
    @staticmethod
    def create(config: CrawlConfig) -> BaseFetcher:
        if config.js_render is True:
            logger.info("FetcherFactory: Using PlaywrightFetcher")
            return PlaywrightFetcher(user_agent=config.user_agent)
        elif config.js_render is False:
            logger.info("FetcherFactory: Using HTTP Fetcher")
            return HttpFetcher(user_agent=config.user_agent)
        else:
            logger.info("FetcherFactory: Auto Detecting...")
            # js_render=None means "auto-detect"
            return AutoFetcher(user_agent=config.user_agent)
