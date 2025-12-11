"""
Anime Scraper Pipelines

This module contains item processing pipelines for:
- Validation: Ensure required fields are present
- Image Download: Download images to local storage
- Deduplication: Use perceptual hashing to detect duplicates
- Export: Save metadata to JSON
"""

import os
import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

import scrapy
from scrapy.exceptions import DropItem
from scrapy.pipelines.images import ImagesPipeline
from itemadapter import ItemAdapter

logger = logging.getLogger(__name__)


class ValidationPipeline:
    """
    Validate items have required fields before processing.
    Drops items that are missing essential data.
    """

    REQUIRED_FIELDS = ["image_url"]

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        for field in self.REQUIRED_FIELDS:
            if not adapter.get(field):
                raise DropItem(f"Missing required field: {field}")

        # Validate image URL format
        image_url = adapter.get("image_url")
        if image_url:
            parsed = urlparse(image_url)
            if not parsed.scheme or not parsed.netloc:
                raise DropItem(f"Invalid image URL: {image_url}")

        return item


class ImageDownloadPipeline(ImagesPipeline):
    """
    Download images to local storage.

    Extends Scrapy's ImagesPipeline with custom naming
    and filtering logic.
    """

    def get_media_requests(self, item, info):
        """Generate download requests for item images."""
        adapter = ItemAdapter(item)
        image_url = adapter.get("image_url")

        if image_url:
            yield scrapy.Request(
                image_url,
                meta={
                    "item": item,
                    "post_id": adapter.get("post_id"),
                    "source_site": adapter.get("source_site"),
                }
            )

    def file_path(self, request, response=None, info=None, *, item=None):
        """Generate custom file path for downloaded images."""
        # Get metadata from request
        post_id = request.meta.get("post_id", "unknown")
        source_site = request.meta.get("source_site", "unknown")

        # Extract extension from URL
        url_path = urlparse(request.url).path
        ext = os.path.splitext(url_path)[1] or ".jpg"

        # Create organized folder structure: site/id.ext
        return f"{source_site}/{post_id}{ext}"

    def item_completed(self, results, item, info):
        """Process item after image download completes."""
        adapter = ItemAdapter(item)

        # Check download results
        downloaded_paths = []
        for ok, result in results:
            if ok:
                downloaded_paths.append(result["path"])
                logger.debug(f"Downloaded: {result['path']}")
            else:
                logger.warning(f"Failed to download image for post {adapter.get('post_id')}")

        if downloaded_paths:
            adapter["local_path"] = downloaded_paths[0]

        return item


class DeduplicationPipeline:
    """
    Detect and handle duplicate images using perceptual hashing (pHash).

    Uses the imagededup library to compute perceptual hashes and compare
    against previously seen images. This catches:
    - Exact duplicates
    - Near-duplicates (resized, slightly modified)
    - Re-uploads of the same image
    """

    def __init__(self, hash_db_path, images_store, hamming_threshold=10):
        """
        Initialize the deduplication pipeline.

        Args:
            hash_db_path: Path to the hash database JSON file
            images_store: Path to downloaded images directory
            hamming_threshold: Max Hamming distance for duplicate detection
                              (lower = stricter, 10 is good default)
        """
        self.hash_db_path = Path(hash_db_path)
        self.images_store = Path(images_store)
        self.hamming_threshold = hamming_threshold
        self.existing_hashes = {}
        self.phasher = None
        self.stats = {
            "processed": 0,
            "duplicates_found": 0,
            "unique_images": 0,
        }

    @classmethod
    def from_crawler(cls, crawler):
        """Create pipeline from crawler settings."""
        return cls(
            hash_db_path=crawler.settings.get("HASH_DATABASE_PATH", "data/image_hashes.json"),
            images_store=crawler.settings.get("IMAGES_STORE", "downloaded_images"),
            hamming_threshold=crawler.settings.getint("DEDUP_HAMMING_THRESHOLD", 10),
        )

    def open_spider(self, spider):
        """Initialize hash database when spider opens."""
        # Lazy import to avoid issues if imagededup not installed
        try:
            from imagededup.methods import PHash
            self.phasher = PHash()
        except ImportError:
            logger.warning("imagededup not installed. Deduplication disabled.")
            self.phasher = None
            return

        # Ensure directories exist
        self.hash_db_path.parent.mkdir(parents=True, exist_ok=True)
        self.images_store.mkdir(parents=True, exist_ok=True)

        # Load existing hashes
        if self.hash_db_path.exists():
            try:
                with open(self.hash_db_path, "r") as f:
                    self.existing_hashes = json.load(f)
                logger.info(f"Loaded {len(self.existing_hashes)} existing hashes")
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load hash database: {e}")
                self.existing_hashes = {}
        else:
            logger.info("No existing hash database found, starting fresh")

    def close_spider(self, spider):
        """Save hash database when spider closes."""
        if self.phasher is None:
            return

        # Save updated hashes
        try:
            self.hash_db_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.hash_db_path, "w") as f:
                json.dump(self.existing_hashes, f, indent=2)
            logger.info(f"Saved {len(self.existing_hashes)} hashes to database")
        except IOError as e:
            logger.error(f"Failed to save hash database: {e}")

        # Log statistics
        logger.info(f"Deduplication stats: {self.stats}")

    def process_item(self, item, spider):
        """Process item and check for duplicates."""
        if self.phasher is None:
            return item

        adapter = ItemAdapter(item)
        self.stats["processed"] += 1

        # Get the local path of downloaded image
        local_path = adapter.get("local_path")
        if not local_path:
            logger.debug("No local_path, skipping deduplication")
            return item

        # Build full path
        full_path = self.images_store / local_path
        if not full_path.exists():
            logger.warning(f"Image file not found: {full_path}")
            return item

        # Compute perceptual hash
        try:
            image_hash = self._compute_hash(str(full_path))
            if not image_hash:
                logger.warning(f"Failed to compute hash for {full_path}")
                return item

            adapter["image_hash"] = image_hash

            # Check for duplicates
            duplicate_id = self._find_duplicate(image_hash)
            if duplicate_id:
                self.stats["duplicates_found"] += 1
                adapter["is_duplicate"] = True
                logger.info(
                    f"Duplicate found: {adapter.get('post_id')} matches {duplicate_id}"
                )
                # Optionally drop duplicates
                # raise DropItem(f"Duplicate of {duplicate_id}")
            else:
                self.stats["unique_images"] += 1
                adapter["is_duplicate"] = False
                # Store hash for future comparisons
                post_id = adapter.get("post_id", str(full_path))
                self.existing_hashes[post_id] = {
                    "hash": image_hash,
                    "path": str(local_path),
                    "source_site": adapter.get("source_site"),
                    "added_at": datetime.utcnow().isoformat(),
                }

        except Exception as e:
            logger.error(f"Error during deduplication: {e}")

        return item

    def _compute_hash(self, image_path):
        """Compute perceptual hash for an image."""
        try:
            # imagededup expects a directory, but we can use encode_image for single files
            encodings = self.phasher.encode_image(image_file=image_path)
            return encodings
        except Exception as e:
            logger.error(f"Hash computation failed for {image_path}: {e}")
            return None

    def _find_duplicate(self, new_hash):
        """
        Find if the new hash matches any existing hash.

        Uses Hamming distance to compare perceptual hashes.
        Returns the post_id of the duplicate if found, None otherwise.
        """
        if not new_hash:
            return None

        for post_id, data in self.existing_hashes.items():
            existing_hash = data.get("hash")
            if existing_hash:
                distance = self._hamming_distance(new_hash, existing_hash)
                if distance <= self.hamming_threshold:
                    return post_id

        return None

    def _hamming_distance(self, hash1, hash2):
        """Calculate Hamming distance between two hex hash strings."""
        if not hash1 or not hash2:
            return float("inf")

        try:
            # Convert hex strings to integers
            int1 = int(hash1, 16)
            int2 = int(hash2, 16)

            # XOR and count bits
            xor = int1 ^ int2
            return bin(xor).count("1")
        except (ValueError, TypeError):
            return float("inf")


class JsonExportPipeline:
    """
    Export scraped items to JSON files organized by date and search tags.
    """

    def __init__(self):
        self.items = []
        self.output_dir = Path("output")

    def open_spider(self, spider):
        """Prepare output directory."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.spider_name = spider.name
        self.search_tags = getattr(spider, "search_tags", "unknown")

    def process_item(self, item, spider):
        """Collect items for batch export."""
        adapter = ItemAdapter(item)
        self.items.append(dict(adapter))
        return item

    def close_spider(self, spider):
        """Export all collected items to JSON."""
        if not self.items:
            logger.info("No items to export")
            return

        # Create filename with timestamp and search tags
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_tags = self.search_tags.replace(" ", "_").replace(":", "-")[:50]
        filename = f"images_{safe_tags}_{timestamp}.json"
        filepath = self.output_dir / filename

        # Export data
        export_data = {
            "metadata": {
                "spider": self.spider_name,
                "search_tags": self.search_tags,
                "total_items": len(self.items),
                "exported_at": datetime.utcnow().isoformat(),
            },
            "images": self.items,
        }

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Exported {len(self.items)} items to {filepath}")
        except IOError as e:
            logger.error(f"Failed to export items: {e}")


class PaginationDisplayPipeline:
    """
    Group items by page for display purposes.
    Shows 20 images per page as required.
    """

    def __init__(self):
        self.pages = {}
        self.images_per_page = 20

    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        pipeline.images_per_page = crawler.settings.getint("IMAGES_PER_PAGE", 20)
        return pipeline

    def process_item(self, item, spider):
        """Group items by page number."""
        adapter = ItemAdapter(item)
        page_num = adapter.get("page_number", 1)

        if page_num not in self.pages:
            self.pages[page_num] = []

        self.pages[page_num].append(dict(adapter))
        return item

    def close_spider(self, spider):
        """Log pagination summary."""
        total_pages = len(self.pages)
        total_images = sum(len(images) for images in self.pages.values())

        logger.info(f"Pagination Summary:")
        logger.info(f"  Total pages: {total_pages}")
        logger.info(f"  Total images: {total_images}")
        logger.info(f"  Images per page: {self.images_per_page}")

        for page_num in sorted(self.pages.keys()):
            count = len(self.pages[page_num])
            logger.info(f"  Page {page_num}: {count} images")
