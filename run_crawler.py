#!/usr/bin/env python3
"""
Anime Image Crawler - Main Entry Point

A command-line tool to crawl anime images from booru-style imageboards.
Displays 20 images per page with support for pagination.

Usage:
    python run_crawler.py --tags "rating:general" --site danbooru --max-pages 5
    python run_crawler.py --tags "1girl blue_hair" --site safebooru
    python run_crawler.py --help
"""

import argparse
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


def setup_directories():
    """Create necessary directories for output."""
    dirs = [
        "downloaded_images",
        "output",
        "data",
        "logs",
    ]
    for d in dirs:
        Path(d).mkdir(exist_ok=True)


def run_spider(args):
    """Run the Scrapy spider with provided arguments."""
    from scrapy.crawler import CrawlerProcess
    from scrapy.utils.project import get_project_settings
    from anime_scraper.spiders.booru_html import BooruHtmlSpider

    # Setup directories
    setup_directories()

    # Get project settings
    settings = get_project_settings()

    # Override settings from command line
    if args.delay:
        settings.set("DOWNLOAD_DELAY", args.delay)
    if args.images_per_page:
        settings.set("IMAGES_PER_PAGE", args.images_per_page)
    if args.output_dir:
        settings.set("IMAGES_STORE", args.output_dir)
    if args.log_level:
        settings.set("LOG_LEVEL", args.log_level.upper())

    # Create crawler process
    process = CrawlerProcess(settings)

    # Add spider with arguments
    process.crawl(
        BooruHtmlSpider,
        tags=args.tags,
        site=args.site,
        max_pages=args.max_pages,
        start_page=args.start_page,
    )

    # Start crawling
    print(f"\n{'='*60}")
    print(f"Anime Image Crawler")
    print(f"{'='*60}")
    print(f"Site: {args.site}")
    print(f"Tags: {args.tags}")
    print(f"Max Pages: {args.max_pages or 'unlimited'}")
    print(f"Start Page: {args.start_page}")
    print(f"Download Delay: {settings.get('DOWNLOAD_DELAY')}s")
    print(f"Images Per Page: {settings.get('IMAGES_PER_PAGE', 20)}")
    print(f"{'='*60}\n")

    process.start()


def main():
    """Parse arguments and run the crawler."""
    parser = argparse.ArgumentParser(
        description="Anime Image Crawler - Scrape anime images from booru imageboards",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape safe images from Danbooru
  python run_crawler.py --tags "rating:general" --site danbooru

  # Scrape specific character with limit
  python run_crawler.py --tags "hatsune_miku" --max-pages 3

  # Scrape from Safebooru with custom delay
  python run_crawler.py --tags "1girl" --site safebooru --delay 5

  # Resume from page 10
  python run_crawler.py --tags "blue_hair" --start-page 10 --max-pages 5

Supported Sites:
  - danbooru (default)
  - safebooru
  - gelbooru

Note: Always respect the site's terms of service and rate limits.
        """
    )

    parser.add_argument(
        "--tags", "-t",
        type=str,
        default="rating:general",
        help="Search tags (space-separated, use quotes). Default: 'rating:general'"
    )

    parser.add_argument(
        "--site", "-s",
        type=str,
        choices=["danbooru", "safebooru", "gelbooru"],
        default="danbooru",
        help="Target site to scrape. Default: danbooru"
    )

    parser.add_argument(
        "--max-pages", "-m",
        type=int,
        default=None,
        help="Maximum number of pages to scrape. Default: unlimited"
    )

    parser.add_argument(
        "--start-page", "-p",
        type=int,
        default=1,
        help="Page number to start from. Default: 1"
    )

    parser.add_argument(
        "--delay", "-d",
        type=float,
        default=None,
        help="Delay between requests in seconds. Default: 3.0"
    )

    parser.add_argument(
        "--images-per-page", "-i",
        type=int,
        default=20,
        help="Number of images to display per page. Default: 20"
    )

    parser.add_argument(
        "--output-dir", "-o",
        type=str,
        default=None,
        help="Directory to save downloaded images. Default: downloaded_images"
    )

    parser.add_argument(
        "--log-level", "-l",
        type=str,
        choices=["debug", "info", "warning", "error"],
        default="info",
        help="Logging level. Default: info"
    )

    args = parser.parse_args()
    run_spider(args)


if __name__ == "__main__":
    main()
