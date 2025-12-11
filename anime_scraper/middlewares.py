# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
from scrapy.http import HtmlResponse
import logging

logger = logging.getLogger(__name__)


class AnimeScraperSpiderMiddleware:
    """
    Spider middleware for the anime scraper.
    Handles response processing and error handling.
    """

    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        """Process incoming responses before they reach the spider."""
        return None

    def process_spider_output(self, response, result, spider):
        """Process items and requests yielded by the spider."""
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        """Handle exceptions raised during spider processing."""
        logger.error(f"Spider exception on {response.url}: {exception}")
        pass

    def process_start_requests(self, start_requests, spider):
        """Process start requests before they are sent."""
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        logger.info(f"Spider opened: {spider.name}")


class AnimeScraperDownloaderMiddleware:
    """
    Downloader middleware for handling anti-bot measures
    and improving request success rate.
    """

    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        """
        Process each request before it's sent.
        Add extra headers or modify requests as needed.
        """
        # Add referer for subsequent requests
        if "referer" not in request.headers:
            request.headers["Referer"] = request.url

        return None

    def process_response(self, request, response, spider):
        """
        Process each response.
        Handle common anti-bot responses.
        """
        # Check for Cloudflare challenge
        if self._is_cloudflare_challenge(response):
            logger.warning(f"Cloudflare challenge detected on {request.url}")
            # The Playwright handler should handle this automatically
            # If we still get a challenge, log it for debugging

        # Check for rate limiting
        if response.status == 429:
            logger.warning(f"Rate limited on {request.url}")

        # Check for blocked response
        if response.status == 403:
            logger.warning(f"Access forbidden on {request.url}")

        return response

    def process_exception(self, request, exception, spider):
        """Handle download exceptions."""
        logger.error(f"Download exception on {request.url}: {exception}")
        pass

    def spider_opened(self, spider):
        logger.info(f"Spider opened: {spider.name}")

    def _is_cloudflare_challenge(self, response):
        """Check if response is a Cloudflare challenge page."""
        if response.status == 503:
            body = response.text.lower()
            return "cloudflare" in body or "checking your browser" in body
        return False


class PlaywrightRetryMiddleware:
    """
    Middleware to retry failed Playwright requests.
    Useful for handling transient browser errors.
    """

    def __init__(self, max_retries=3):
        self.max_retries = max_retries

    @classmethod
    def from_crawler(cls, crawler):
        max_retries = crawler.settings.getint("PLAYWRIGHT_MAX_RETRIES", 3)
        return cls(max_retries)

    def process_exception(self, request, exception, spider):
        """Retry Playwright requests on specific exceptions."""
        retries = request.meta.get("playwright_retries", 0)

        if retries < self.max_retries:
            logger.info(f"Retrying Playwright request ({retries + 1}/{self.max_retries}): {request.url}")
            new_request = request.copy()
            new_request.meta["playwright_retries"] = retries + 1
            new_request.dont_filter = True
            return new_request

        logger.error(f"Max Playwright retries reached for {request.url}")
        return None
