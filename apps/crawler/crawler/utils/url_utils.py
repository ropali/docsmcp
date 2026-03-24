from urllib.parse import urlparse, urljoin, urldefrag
from urllib.robotparser import RobotFileParser
import fnmatch
import httpx


def normalize_url(url: str) -> str:
    """Remove fragment, trailing slash, and lowercase scheme+host."""
    url, _ = urldefrag(url)  # strip #section
    parsed = urlparse(url)
    # Lowercase scheme and host; keep path as-is
    normalized = parsed._replace(
        scheme=parsed.scheme.lower(),
        netloc=parsed.netloc.lower(),
    )
    return normalized.geturl().rstrip("/")


def is_same_domain(url: str, base_url: str) -> bool:
    return urlparse(url).netloc == urlparse(base_url).netloc


def is_html_link(url: str) -> bool:
    """Exclude binary/media/asset URLs."""
    skip_exts = {
        ".pdf",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".svg",
        ".ico",
        ".css",
        ".js",
        ".woff",
        ".woff2",
        ".ttf",
        ".zip",
        ".tar",
        ".gz",
        ".xml",
        ".json",
    }
    path = urlparse(url).path.lower()
    return not any(path.endswith(ext) for ext in skip_exts)


def matches_patterns(url: str, patterns: list[str]) -> bool:
    """Check if a URL path matches any glob pattern in the list."""
    if not patterns:
        return False
    path = urlparse(url).path
    return any(fnmatch.fnmatch(path, pat) for pat in patterns)


def extract_links(html: str, base_url: str) -> list[str]:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    links = []
    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()
        if not href or href.startswith(("mailto:", "tel:", "javascript:")):
            continue
        absolute = urljoin(base_url, href)
        links.append(normalize_url(absolute))
    return links


async def fetch_robots_txt(base_url: str, user_agent: str) -> RobotFileParser:
    rp = RobotFileParser()
    robots_url = f"{urlparse(base_url).scheme}://{urlparse(base_url).netloc}/robots.txt"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(robots_url, timeout=10)
            rp.parse(resp.text.splitlines())
    except Exception:
        pass  # if robots.txt is unreachable, allow everything
    return rp
