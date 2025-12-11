# Scrapy settings for anime_scraper project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = "anime_scraper"

SPIDER_MODULES = ["anime_scraper.spiders"]
NEWSPIDER_MODULE = "anime_scraper.spiders"

# =============================================================================
# PLAYWRIGHT CONFIGURATION
# =============================================================================
# Enable Playwright for browser automation (handles JS rendering & Cloudflare)
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}

# Required for async Playwright support
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

# Playwright browser settings
PLAYWRIGHT_BROWSER_TYPE = "chromium"
PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": True,
    "timeout": 30000,
}

# Default Playwright context options
PLAYWRIGHT_CONTEXTS = {
    "default": {
        "viewport": {"width": 1920, "height": 1080},
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
}

# =============================================================================
# POLITENESS & RATE LIMITING (CRITICAL FOR HTML SCRAPING)
# =============================================================================
# Crawl responsibly by identifying yourself on the user-agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests performed by Scrapy
# HTML scraping is heavy - keep this low to be polite
CONCURRENT_REQUESTS = 1

# Configure a delay for requests for the same website
# This is crucial - too fast will get you banned
DOWNLOAD_DELAY = 3.0

# The download delay setting will honor only one of:
CONCURRENT_REQUESTS_PER_DOMAIN = 1
CONCURRENT_REQUESTS_PER_IP = 1

# Disable cookies (enabled by default)
COOKIES_ENABLED = True

# Disable Telnet Console (enabled by default)
TELNETCONSOLE_ENABLED = False

# =============================================================================
# RETRY & TIMEOUT SETTINGS
# =============================================================================
# Retry failed requests
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# Download timeout
DOWNLOAD_TIMEOUT = 60

# =============================================================================
# DEFAULT REQUEST HEADERS
# =============================================================================
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}

# =============================================================================
# SPIDER MIDDLEWARES
# =============================================================================
SPIDER_MIDDLEWARES = {
    "anime_scraper.middlewares.AnimeScraperSpiderMiddleware": 543,
}

# =============================================================================
# DOWNLOADER MIDDLEWARES
# =============================================================================
DOWNLOADER_MIDDLEWARES = {
    "anime_scraper.middlewares.AnimeScraperDownloaderMiddleware": 543,
}

# =============================================================================
# ITEM PIPELINES
# =============================================================================
ITEM_PIPELINES = {
    "anime_scraper.pipelines.ValidationPipeline": 100,
    "anime_scraper.pipelines.ImageDownloadPipeline": 200,
    "anime_scraper.pipelines.DeduplicationPipeline": 300,
    "anime_scraper.pipelines.JsonExportPipeline": 400,
}

# =============================================================================
# IMAGE SETTINGS
# =============================================================================
# Enable and configure the Images Pipeline
IMAGES_STORE = "downloaded_images"

# Image expiration (in days)
IMAGES_EXPIRES = 90

# Minimum image dimensions to filter thumbnails
IMAGES_MIN_HEIGHT = 200
IMAGES_MIN_WIDTH = 200

# =============================================================================
# OUTPUT SETTINGS
# =============================================================================
# Feed exports
FEEDS = {
    "output/images_%(time)s.json": {
        "format": "json",
        "encoding": "utf8",
        "indent": 2,
    },
}

# =============================================================================
# LOGGING
# =============================================================================
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
LOG_DATEFORMAT = "%Y-%m-%d %H:%M:%S"

# =============================================================================
# AUTOTHROTTLE (ADAPTIVE RATE LIMITING)
# =============================================================================
# Enable AutoThrottle for intelligent rate limiting
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 3.0
AUTOTHROTTLE_MAX_DELAY = 60.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
AUTOTHROTTLE_DEBUG = False

# =============================================================================
# CACHING (Optional - for development)
# =============================================================================
# Uncomment to enable HTTP caching during development
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 3600
# HTTPCACHE_DIR = "httpcache"
# HTTPCACHE_IGNORE_HTTP_CODES = []
# HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# =============================================================================
# CUSTOM SETTINGS
# =============================================================================
# Pagination settings
IMAGES_PER_PAGE = 20

# Hash database for deduplication
HASH_DATABASE_PATH = "data/image_hashes.json"

# Request fingerprinting
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
