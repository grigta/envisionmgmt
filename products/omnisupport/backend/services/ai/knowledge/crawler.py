"""Website crawler for knowledge base."""

import asyncio
import logging
import re
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class CrawledPage:
    """Crawled page data."""

    url: str
    title: str
    content: str
    links: list[str]
    depth: int
    metadata: dict | None = None


class WebCrawler:
    """Async website crawler for knowledge base indexing."""

    def __init__(
        self,
        max_pages: int = 100,
        max_depth: int = 3,
        timeout: float = 30.0,
        delay: float = 1.0,
        user_agent: str = "OmniSupport-Crawler/1.0",
    ):
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.timeout = timeout
        self.delay = delay
        self.user_agent = user_agent
        self._visited: set[str] = set()
        self._queue: asyncio.Queue = asyncio.Queue()

    def _normalize_url(self, url: str) -> str:
        """Normalize URL for deduplication."""
        parsed = urlparse(url)
        # Remove fragment and trailing slash
        path = parsed.path.rstrip("/") or "/"
        return f"{parsed.scheme}://{parsed.netloc}{path}"

    def _is_same_domain(self, url1: str, url2: str) -> bool:
        """Check if two URLs belong to the same domain."""
        return urlparse(url1).netloc == urlparse(url2).netloc

    def _extract_text(self, soup: BeautifulSoup) -> str:
        """Extract main content text from page."""
        # Remove unwanted elements
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            tag.decompose()

        # Try to find main content
        main_content = (
            soup.find("main")
            or soup.find("article")
            or soup.find(id=re.compile(r"content|main", re.I))
            or soup.find(class_=re.compile(r"content|main|article", re.I))
            or soup.body
        )

        if main_content:
            text = main_content.get_text(separator="\n", strip=True)
        else:
            text = soup.get_text(separator="\n", strip=True)

        # Clean up text
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        return "\n\n".join(lines)

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> list[str]:
        """Extract valid links from page."""
        links = []

        for a in soup.find_all("a", href=True):
            href = a["href"]

            # Skip anchors, javascript, mailto
            if href.startswith(("#", "javascript:", "mailto:", "tel:")):
                continue

            # Make absolute URL
            absolute_url = urljoin(base_url, href)

            # Only include same-domain links
            if self._is_same_domain(base_url, absolute_url):
                normalized = self._normalize_url(absolute_url)
                if normalized not in self._visited:
                    links.append(normalized)

        return list(set(links))

    async def _fetch_page(
        self,
        client: httpx.AsyncClient,
        url: str,
    ) -> tuple[str, str] | None:
        """Fetch page content."""
        try:
            response = await client.get(
                url,
                follow_redirects=True,
                timeout=self.timeout,
            )

            if response.status_code != 200:
                logger.debug(f"Failed to fetch {url}: {response.status_code}")
                return None

            content_type = response.headers.get("content-type", "")
            if "text/html" not in content_type:
                logger.debug(f"Skipping non-HTML: {url}")
                return None

            return response.text, str(response.url)

        except Exception as e:
            logger.debug(f"Error fetching {url}: {e}")
            return None

    async def _process_page(
        self,
        client: httpx.AsyncClient,
        url: str,
        depth: int,
    ) -> CrawledPage | None:
        """Fetch and process a single page."""
        result = await self._fetch_page(client, url)
        if not result:
            return None

        html, final_url = result
        soup = BeautifulSoup(html, "lxml")

        # Extract title
        title = ""
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True)

        h1 = soup.find("h1")
        if h1 and not title:
            title = h1.get_text(strip=True)

        # Extract content
        content = self._extract_text(soup)

        # Skip pages with little content
        if len(content) < 100:
            logger.debug(f"Skipping low-content page: {url}")
            return None

        # Extract links for further crawling
        links = []
        if depth < self.max_depth:
            links = self._extract_links(soup, final_url)

        return CrawledPage(
            url=final_url,
            title=title,
            content=content,
            links=links,
            depth=depth,
            metadata={
                "original_url": url,
                "content_length": len(content),
            },
        )

    async def crawl(
        self,
        start_url: str,
        include_patterns: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
    ) -> list[CrawledPage]:
        """
        Crawl website starting from URL.

        Args:
            start_url: Starting URL
            include_patterns: Regex patterns to include (optional)
            exclude_patterns: Regex patterns to exclude (optional)

        Returns:
            List of crawled pages
        """
        self._visited = set()
        pages: list[CrawledPage] = []

        # Compile patterns
        include_regex = [re.compile(p) for p in (include_patterns or [])]
        exclude_regex = [re.compile(p) for p in (exclude_patterns or [])]

        def should_crawl(url: str) -> bool:
            """Check if URL should be crawled based on patterns."""
            if include_regex:
                if not any(r.search(url) for r in include_regex):
                    return False
            if exclude_regex:
                if any(r.search(url) for r in exclude_regex):
                    return False
            return True

        # Start with initial URL
        normalized_start = self._normalize_url(start_url)
        await self._queue.put((normalized_start, 0))

        headers = {"User-Agent": self.user_agent}

        async with httpx.AsyncClient(headers=headers) as client:
            while not self._queue.empty() and len(pages) < self.max_pages:
                url, depth = await self._queue.get()

                # Skip if already visited
                if url in self._visited:
                    continue

                # Skip if doesn't match patterns
                if not should_crawl(url):
                    continue

                self._visited.add(url)
                logger.info(f"Crawling ({len(pages) + 1}/{self.max_pages}): {url}")

                # Process page
                page = await self._process_page(client, url, depth)

                if page:
                    pages.append(page)

                    # Add links to queue
                    for link in page.links:
                        if link not in self._visited and should_crawl(link):
                            await self._queue.put((link, depth + 1))

                # Respect delay
                await asyncio.sleep(self.delay)

        logger.info(f"Crawl complete. Found {len(pages)} pages.")
        return pages

    async def crawl_sitemap(self, sitemap_url: str) -> list[str]:
        """Extract URLs from sitemap.xml."""
        urls = []

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(sitemap_url, timeout=30.0)
                if response.status_code != 200:
                    return urls

                soup = BeautifulSoup(response.text, "xml")

                # Handle sitemap index
                for sitemap in soup.find_all("sitemap"):
                    loc = sitemap.find("loc")
                    if loc:
                        child_urls = await self.crawl_sitemap(loc.get_text())
                        urls.extend(child_urls)

                # Handle regular sitemap
                for url in soup.find_all("url"):
                    loc = url.find("loc")
                    if loc:
                        urls.append(loc.get_text())

            except Exception as e:
                logger.error(f"Error parsing sitemap: {e}")

        return urls


async def crawl_website(
    url: str,
    max_pages: int = 50,
    max_depth: int = 2,
    include_patterns: list[str] | None = None,
    exclude_patterns: list[str] | None = None,
) -> list[CrawledPage]:
    """Convenience function to crawl a website."""
    crawler = WebCrawler(max_pages=max_pages, max_depth=max_depth)
    return await crawler.crawl(url, include_patterns, exclude_patterns)
