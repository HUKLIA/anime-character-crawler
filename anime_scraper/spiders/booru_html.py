"""
Booru HTML Spider

A Scrapy spider for scraping anime images from booru-style imageboards
using HTML parsing with Playwright for JavaScript rendering.

Key features:
- Playwright integration for JS-rendered pages and Cloudflare bypass
- Handles infinite scroll via automated scrolling
- Extracts full-resolution image URLs (avoids thumbnail trap)
- Supports multiple booru sites with site-specific selectors
- Pagination support with 20 images per page display
"""

import scrapy
from scrapy import Request
from scrapy.loader import ItemLoader
from anime_scraper.items import AnimeImageItem
from datetime import datetime
from urllib.parse import urljoin, urlparse, parse_qs
import logging
import re

logger = logging.getLogger(__name__)


class BooruHtmlSpider(scrapy.Spider):
    """
    Spider for scraping anime images from booru-style imageboards.

    Usage:
        scrapy crawl booru_html -a tags="rating:general" -a site="danbooru"
        scrapy crawl booru_html -a tags="1girl blue_hair" -a max_pages=10
    """

    name = "booru_html"
    allowed_domains = ["danbooru.donmai.us", "safebooru.org", "gelbooru.com"]

    # Site-specific configurations
    SITE_CONFIG = {
        "danbooru": {
            "base_url": "https://danbooru.donmai.us",
            "search_path": "/posts",
            "post_selector": "article.post-preview",
            "image_url_attr": "data-file-url",
            "large_image_attr": "data-large-file-url",
            "preview_attr": "data-preview-file-url",
            "tags_attr": "data-tags",
            "post_id_attr": "data-id",
            "score_attr": "data-score",
            "rating_attr": "data-rating",
            "width_attr": "data-width",
            "height_attr": "data-height",
            "next_page_selector": "a.paginator-next",
            "uses_infinite_scroll": False,
        },
        "safebooru": {
            "base_url": "https://safebooru.org",
            "search_path": "/index.php",
            "post_selector": "span.thumb",
            "thumbnail_selector": "img",
            "link_selector": "a",
            "next_page_selector": 'a[alt="next"]',
            "uses_infinite_scroll": False,
        },
        "gelbooru": {
            "base_url": "https://gelbooru.com",
            "search_path": "/index.php",
            "post_selector": "article.thumbnail-preview",
            "thumbnail_selector": "img",
            "link_selector": "a",
            "tags_attr": "data-tags",
            "post_id_attr": "data-id",
            "next_page_selector": 'a[alt="next"]',
            "uses_infinite_scroll": False,
        },
    }

    # Custom settings for this spider
    custom_settings = {
        "DOWNLOAD_DELAY": 3.0,
        "CONCURRENT_REQUESTS": 1,
        "IMAGES_PER_PAGE": 20,
    }

    def __init__(
        self,
        tags="rating:general",
        site="danbooru",
        max_pages=None,
        start_page=1,
        *args,
        **kwargs
    ):
        """
        Initialize the spider with search parameters.

        Args:
            tags: Search tags (space-separated)
            site: Target site (danbooru, safebooru, gelbooru)
            max_pages: Maximum number of pages to scrape (None = unlimited)
            start_page: Page number to start from
        """
        super().__init__(*args, **kwargs)
        self.search_tags = tags
        self.site = site
        self.max_pages = int(max_pages) if max_pages else None
        self.start_page = int(start_page)
        self.current_page = self.start_page
        self.images_scraped = 0
        self.config = self.SITE_CONFIG.get(site, self.SITE_CONFIG["danbooru"])

        logger.info(f"Initialized spider for {site} with tags: {tags}")

    def start_requests(self):
        """Generate initial requests to start the crawl."""
        url = self._build_search_url(self.current_page)
        logger.info(f"Starting crawl at: {url}")

        yield Request(
            url,
            callback=self.parse,
            meta={
                "playwright": True,
                "playwright_include_page": True,
                "playwright_page_methods": [
                    # Wait for content to load
                    {"method": "wait_for_load_state", "args": ["networkidle"]},
                ],
                "page_number": self.current_page,
            },
            errback=self.handle_error,
        )

    def _build_search_url(self, page=1):
        """Build the search URL for the target site."""
        base_url = self.config["base_url"]
        search_path = self.config["search_path"]

        if self.site == "danbooru":
            return f"{base_url}{search_path}?tags={self.search_tags}&page={page}"
        elif self.site == "safebooru":
            return f"{base_url}{search_path}?page=dapi&s=post&q=index&tags={self.search_tags}&pid={page - 1}"
        elif self.site == "gelbooru":
            return f"{base_url}{search_path}?page=post&s=list&tags={self.search_tags}&pid={(page - 1) * 42}"

        return f"{base_url}{search_path}?tags={self.search_tags}&page={page}"

    async def parse(self, response):
        """
        Parse the gallery page and extract image items.

        This method handles:
        1. Extracting post containers
        2. Parsing image URLs and metadata from HTML attributes
        3. Handling pagination
        """
        page_number = response.meta.get("page_number", 1)
        page = response.meta.get("playwright_page")

        logger.info(f"Parsing page {page_number}: {response.url}")

        # Handle infinite scroll if needed
        if self.config.get("uses_infinite_scroll") and page:
            await self._handle_infinite_scroll(page)

        # Close the Playwright page to free resources
        if page:
            await page.close()

        # Select all post containers
        posts = response.css(self.config["post_selector"])
        logger.info(f"Found {len(posts)} posts on page {page_number}")

        if not posts:
            logger.warning(f"No posts found on page {page_number}. Layout may have changed.")
            return

        # Process each post (limit to 20 per page for display)
        images_per_page = self.settings.getint("IMAGES_PER_PAGE", 20)
        posts_to_process = posts[:images_per_page]

        for position, post in enumerate(posts_to_process, start=1):
            item = self._extract_item(post, response, page_number, position)
            if item:
                self.images_scraped += 1
                yield item

        # Handle pagination
        if self._should_continue_pagination(page_number, len(posts)):
            next_page_url = self._get_next_page_url(response, page_number)
            if next_page_url:
                self.current_page += 1
                yield Request(
                    next_page_url,
                    callback=self.parse,
                    meta={
                        "playwright": True,
                        "playwright_include_page": True,
                        "playwright_page_methods": [
                            {"method": "wait_for_load_state", "args": ["networkidle"]},
                        ],
                        "page_number": self.current_page,
                    },
                    errback=self.handle_error,
                )

    def _extract_item(self, post, response, page_number, position):
        """
        Extract an AnimeImageItem from a post element.

        Handles the "Thumbnail Trap" by looking for full-size image URLs
        in data attributes rather than the img src.
        """
        loader = ItemLoader(item=AnimeImageItem(), selector=post)

        # Extract based on site configuration
        if self.site == "danbooru":
            return self._extract_danbooru_item(post, response, page_number, position)
        elif self.site == "safebooru":
            return self._extract_safebooru_item(post, response, page_number, position)
        elif self.site == "gelbooru":
            return self._extract_gelbooru_item(post, response, page_number, position)

        return None

    def _extract_danbooru_item(self, post, response, page_number, position):
        """Extract item from Danbooru HTML structure."""
        item = AnimeImageItem()

        # IMPORTANT: Get FULL image URL, not thumbnail
        # The thumbnail trap: <img src="thumbnail.jpg"> vs data-file-url="full.jpg"
        image_url = post.css(f"::attr({self.config['image_url_attr']})").get()
        large_url = post.css(f"::attr({self.config.get('large_image_attr', '')})").get()
        preview_url = post.css(f"::attr({self.config.get('preview_attr', '')})").get()

        # Prefer full image, fall back to large, then preview
        item["image_url"] = image_url or large_url or preview_url
        item["preview_url"] = large_url or preview_url
        item["thumbnail_url"] = preview_url

        if not item["image_url"]:
            logger.warning(f"No image URL found for post on page {page_number}")
            return None

        # Make URLs absolute
        if item["image_url"]:
            item["image_url"] = urljoin(response.url, item["image_url"])
        if item.get("preview_url"):
            item["preview_url"] = urljoin(response.url, item["preview_url"])
        if item.get("thumbnail_url"):
            item["thumbnail_url"] = urljoin(response.url, item["thumbnail_url"])

        # Extract metadata from data attributes
        item["post_id"] = post.css(f"::attr({self.config['post_id_attr']})").get()
        item["tags"] = post.css(f"::attr({self.config['tags_attr']})").get()
        item["score"] = self._safe_int(post.css(f"::attr({self.config.get('score_attr', '')})").get())
        item["rating"] = post.css(f"::attr({self.config.get('rating_attr', '')})").get()
        item["width"] = self._safe_int(post.css(f"::attr({self.config.get('width_attr', '')})").get())
        item["height"] = self._safe_int(post.css(f"::attr({self.config.get('height_attr', '')})").get())

        # Parse tags into list
        if item["tags"]:
            item["tags_list"] = [tag.strip() for tag in item["tags"].split() if tag.strip()]

        # Extract file extension from URL
        if item["image_url"]:
            item["file_ext"] = self._extract_extension(item["image_url"])

        # Set page URL for reference
        post_link = post.css("a::attr(href)").get()
        if post_link:
            item["page_url"] = urljoin(response.url, post_link)

        # Metadata
        item["source_site"] = "danbooru"
        item["scraped_at"] = datetime.utcnow().isoformat()
        item["page_number"] = page_number
        item["position_on_page"] = position

        return item

    def _extract_safebooru_item(self, post, response, page_number, position):
        """Extract item from Safebooru HTML structure."""
        item = AnimeImageItem()

        # Get the link to the full post page
        link = post.css("a::attr(href)").get()
        if link:
            item["page_url"] = urljoin(response.url, link)

        # Get thumbnail (we'll need to visit the post page for full image)
        thumbnail = post.css("img::attr(src)").get()
        if thumbnail:
            item["thumbnail_url"] = urljoin(response.url, thumbnail)
            # Try to construct full image URL from thumbnail
            # Safebooru pattern: thumbnails/xxx.jpg -> images/xxx.jpg
            full_url = thumbnail.replace("/thumbnails/", "/images/").replace(
                "/thumbnail_", "/"
            )
            item["image_url"] = urljoin(response.url, full_url)

        # Extract post ID from link
        if link:
            match = re.search(r"id=(\d+)", link)
            if match:
                item["post_id"] = match.group(1)

        # Extract tags from title attribute
        title = post.css("img::attr(title)").get() or post.css("img::attr(alt)").get()
        if title:
            item["tags"] = title
            item["tags_list"] = [tag.strip() for tag in title.split() if tag.strip()]

        # Metadata
        item["source_site"] = "safebooru"
        item["scraped_at"] = datetime.utcnow().isoformat()
        item["page_number"] = page_number
        item["position_on_page"] = position

        if item.get("image_url"):
            item["file_ext"] = self._extract_extension(item["image_url"])

        return item if item.get("image_url") else None

    def _extract_gelbooru_item(self, post, response, page_number, position):
        """Extract item from Gelbooru HTML structure."""
        item = AnimeImageItem()

        # Get the link to the full post page
        link = post.css("a::attr(href)").get()
        if link:
            item["page_url"] = urljoin(response.url, link)

        # Get thumbnail
        thumbnail = post.css("img::attr(src)").get()
        if thumbnail:
            item["thumbnail_url"] = urljoin(response.url, thumbnail)
            # Try to construct full image URL
            full_url = thumbnail.replace("/thumbnails/", "/images/").replace(
                "/thumbnail_", "/"
            )
            item["image_url"] = urljoin(response.url, full_url)

        # Extract data attributes if available
        item["post_id"] = post.css(f"::attr({self.config.get('post_id_attr', 'data-id')})").get()
        item["tags"] = post.css(f"::attr({self.config.get('tags_attr', 'data-tags')})").get()

        if item["tags"]:
            item["tags_list"] = [tag.strip() for tag in item["tags"].split() if tag.strip()]

        # Metadata
        item["source_site"] = "gelbooru"
        item["scraped_at"] = datetime.utcnow().isoformat()
        item["page_number"] = page_number
        item["position_on_page"] = position

        if item.get("image_url"):
            item["file_ext"] = self._extract_extension(item["image_url"])

        return item if item.get("image_url") else None

    async def _handle_infinite_scroll(self, page):
        """
        Handle infinite scroll pages by scrolling to load more content.

        Some modern booru sites use infinite scroll instead of pagination.
        This method scrolls the page to trigger lazy loading.
        """
        logger.info("Handling infinite scroll...")

        previous_height = 0
        max_scrolls = 10  # Safety limit
        scroll_count = 0

        while scroll_count < max_scrolls:
            # Scroll to bottom
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

            # Wait for new content to load
            await page.wait_for_timeout(2000)

            # Check if we've reached the bottom
            current_height = await page.evaluate("document.body.scrollHeight")
            if current_height == previous_height:
                logger.info("Reached end of infinite scroll")
                break

            previous_height = current_height
            scroll_count += 1

        logger.info(f"Completed {scroll_count} scroll iterations")

    def _get_next_page_url(self, response, current_page):
        """Extract or construct the next page URL."""
        # Try to find next page link
        next_selector = self.config.get("next_page_selector")
        if next_selector:
            next_link = response.css(f"{next_selector}::attr(href)").get()
            if next_link:
                return urljoin(response.url, next_link)

        # Construct next page URL
        return self._build_search_url(current_page + 1)

    def _should_continue_pagination(self, current_page, posts_found):
        """Determine if we should continue to the next page."""
        if posts_found == 0:
            logger.info("No more posts found, stopping pagination")
            return False

        if self.max_pages and current_page >= self.max_pages:
            logger.info(f"Reached max pages limit ({self.max_pages})")
            return False

        return True

    def _safe_int(self, value):
        """Safely convert a value to int."""
        if value:
            try:
                return int(value)
            except (ValueError, TypeError):
                pass
        return None

    def _extract_extension(self, url):
        """Extract file extension from URL."""
        if url:
            path = urlparse(url).path
            match = re.search(r"\.(\w+)(?:\?|$)", path)
            if match:
                return match.group(1).lower()
        return None

    def handle_error(self, failure):
        """Handle request failures."""
        logger.error(f"Request failed: {failure.request.url}")
        logger.error(f"Error: {failure.value}")

    def closed(self, reason):
        """Called when spider closes."""
        logger.info(f"Spider closed: {reason}")
        logger.info(f"Total images scraped: {self.images_scraped}")
        logger.info(f"Total pages processed: {self.current_page}")
