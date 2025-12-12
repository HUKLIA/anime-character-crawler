"""
Background crawler thread for the GUI application.
Runs the Scrapy spider in a separate thread to keep the UI responsive.
"""

import os
import sys
import json
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

from PyQt6.QtCore import QThread, pyqtSignal, QMutex


@dataclass
class ImageResult:
    """Data class representing a scraped image."""
    post_id: str
    image_url: str
    thumbnail_url: str = ""
    preview_url: str = ""
    tags: str = ""
    tags_list: List[str] = field(default_factory=list)
    character: str = ""
    series: str = ""
    artist: str = ""
    rating: str = "g"
    score: int = 0
    width: int = 0
    height: int = 0
    source_site: str = ""
    page_url: str = ""
    local_path: str = ""
    is_duplicate: bool = False


class CrawlerThread(QThread):
    """
    Background thread for running the image crawler.

    Signals:
        progress: Emits (current, total, message) for progress updates
        image_found: Emits ImageResult when an image is found
        finished_crawling: Emits when crawling is complete
        error: Emits error message string
    """

    progress = pyqtSignal(int, int, str)
    image_found = pyqtSignal(object)  # ImageResult
    page_complete = pyqtSignal(int, int)  # page_num, images_on_page
    finished_crawling = pyqtSignal(int)  # total images
    error = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.mutex = QMutex()
        self._is_cancelled = False

        # Crawl parameters
        self.search_tags = ""
        self.site = "danbooru"
        self.max_pages = 5
        self.rating_filter = "general"
        self.download_images = True
        self.output_dir = Path("downloaded_images")

    def configure(
        self,
        search_tags: str,
        site: str = "danbooru",
        max_pages: int = 5,
        rating_filter: str = "general",
        download_images: bool = True,
        output_dir: str = "downloaded_images"
    ):
        """Configure the crawler parameters."""
        self.search_tags = search_tags
        self.site = site
        self.max_pages = max_pages
        self.rating_filter = rating_filter
        self.download_images = download_images
        self.output_dir = Path(output_dir)

    def cancel(self):
        """Request cancellation of the crawl."""
        self.mutex.lock()
        self._is_cancelled = True
        self.mutex.unlock()

    def is_cancelled(self) -> bool:
        """Check if cancellation was requested."""
        self.mutex.lock()
        result = self._is_cancelled
        self.mutex.unlock()
        return result

    def run(self):
        """Main thread execution - performs the crawl."""
        self._is_cancelled = False
        total_images = 0

        try:
            # Ensure output directory exists
            self.output_dir.mkdir(parents=True, exist_ok=True)

            # Use the appropriate crawler based on site
            if self.site == "danbooru":
                total_images = self._crawl_danbooru()
            elif self.site == "safebooru":
                total_images = self._crawl_safebooru()
            elif self.site == "gelbooru":
                total_images = self._crawl_gelbooru()
            elif self.site == "konachan":
                total_images = self._crawl_konachan()
            elif self.site == "yande.re":
                total_images = self._crawl_yandere()
            elif self.site == "zerochan":
                total_images = self._crawl_zerochan()
            elif self.site == "anime-pictures":
                total_images = self._crawl_anime_pictures()
            else:
                total_images = self._crawl_danbooru()

            self.finished_crawling.emit(total_images)

        except Exception as e:
            self.error.emit(str(e))

    def _crawl_danbooru(self) -> int:
        """Crawl images from Danbooru using their API."""
        base_url = "https://danbooru.donmai.us"
        total_images = 0

        # Build search tags with rating filter
        tags = self.search_tags
        if self.rating_filter and self.rating_filter != "all":
            rating_map = {
                "general": "rating:general",
                "sensitive": "rating:sensitive",
                "safe": "rating:general"
            }
            if self.rating_filter in rating_map:
                tags = f"{tags} {rating_map[self.rating_filter]}"

        for page in range(1, self.max_pages + 1):
            if self.is_cancelled():
                break

            self.progress.emit(page, self.max_pages, f"Fetching page {page}...")

            try:
                # Use Danbooru's JSON API for easier parsing
                api_url = f"{base_url}/posts.json"
                params = {
                    "tags": tags,
                    "page": page,
                    "limit": 20
                }

                headers = {
                    "User-Agent": "AnimeCharacterCrawler/1.0 (Educational Project)"
                }

                response = requests.get(api_url, params=params, headers=headers, timeout=30)
                response.raise_for_status()

                posts = response.json()

                if not posts:
                    self.progress.emit(page, self.max_pages, "No more results")
                    break

                page_images = 0
                for post in posts:
                    if self.is_cancelled():
                        break

                    # Skip if no file URL
                    file_url = post.get("file_url") or post.get("large_file_url")
                    if not file_url:
                        continue

                    # Create ImageResult
                    result = ImageResult(
                        post_id=str(post.get("id", "")),
                        image_url=file_url,
                        thumbnail_url=post.get("preview_file_url", ""),
                        preview_url=post.get("large_file_url", file_url),
                        tags=post.get("tag_string", ""),
                        tags_list=post.get("tag_string", "").split(),
                        character=post.get("tag_string_character", ""),
                        series=post.get("tag_string_copyright", ""),
                        artist=post.get("tag_string_artist", ""),
                        rating=post.get("rating", "g"),
                        score=post.get("score", 0),
                        width=post.get("image_width", 0),
                        height=post.get("image_height", 0),
                        source_site="danbooru",
                        page_url=f"{base_url}/posts/{post.get('id')}"
                    )

                    # Download image if requested
                    if self.download_images:
                        local_path = self._download_image(result)
                        if local_path:
                            result.local_path = local_path

                    self.image_found.emit(result)
                    total_images += 1
                    page_images += 1

                self.page_complete.emit(page, page_images)

                # Be polite - wait between requests
                if page < self.max_pages:
                    self.msleep(1000)  # 1 second delay

            except requests.exceptions.RequestException as e:
                self.error.emit(f"Network error on page {page}: {str(e)}")
                continue
            except json.JSONDecodeError as e:
                self.error.emit(f"Failed to parse response on page {page}")
                continue

        return total_images

    def _crawl_safebooru(self) -> int:
        """Crawl images from Safebooru."""
        base_url = "https://safebooru.org"
        total_images = 0

        for page in range(self.max_pages):
            if self.is_cancelled():
                break

            self.progress.emit(page + 1, self.max_pages, f"Fetching page {page + 1}...")

            try:
                # Safebooru API
                api_url = f"{base_url}/index.php"
                params = {
                    "page": "dapi",
                    "s": "post",
                    "q": "index",
                    "tags": self.search_tags,
                    "pid": page,
                    "limit": 20,
                    "json": 1
                }

                headers = {
                    "User-Agent": "AnimeCharacterCrawler/1.0 (Educational Project)"
                }

                response = requests.get(api_url, params=params, headers=headers, timeout=30)
                response.raise_for_status()

                posts = response.json()

                if not posts:
                    break

                page_images = 0
                for post in posts:
                    if self.is_cancelled():
                        break

                    # Build image URL
                    directory = post.get("directory", "")
                    image = post.get("image", "")
                    if not image:
                        continue

                    file_url = f"https://safebooru.org/images/{directory}/{image}"
                    preview_url = f"https://safebooru.org/thumbnails/{directory}/thumbnail_{image}"

                    result = ImageResult(
                        post_id=str(post.get("id", "")),
                        image_url=file_url,
                        thumbnail_url=preview_url,
                        preview_url=file_url,
                        tags=post.get("tags", ""),
                        tags_list=post.get("tags", "").split(),
                        rating=post.get("rating", "safe"),
                        score=post.get("score", 0),
                        width=post.get("width", 0),
                        height=post.get("height", 0),
                        source_site="safebooru",
                        page_url=f"{base_url}/index.php?page=post&s=view&id={post.get('id')}"
                    )

                    if self.download_images:
                        local_path = self._download_image(result)
                        if local_path:
                            result.local_path = local_path

                    self.image_found.emit(result)
                    total_images += 1
                    page_images += 1

                self.page_complete.emit(page + 1, page_images)

                if page < self.max_pages - 1:
                    self.msleep(1000)

            except Exception as e:
                self.error.emit(f"Error on page {page + 1}: {str(e)}")
                continue

        return total_images

    def _crawl_gelbooru(self) -> int:
        """Crawl images from Gelbooru."""
        base_url = "https://gelbooru.com"
        total_images = 0

        # Build tags with rating filter
        tags = self.search_tags
        if self.rating_filter == "general":
            tags = f"{tags} rating:general"
        elif self.rating_filter == "safe":
            tags = f"{tags} rating:safe"

        for page in range(self.max_pages):
            if self.is_cancelled():
                break

            self.progress.emit(page + 1, self.max_pages, f"Fetching page {page + 1}...")

            try:
                api_url = f"{base_url}/index.php"
                params = {
                    "page": "dapi",
                    "s": "post",
                    "q": "index",
                    "tags": tags,
                    "pid": page,
                    "limit": 20,
                    "json": 1
                }

                headers = {
                    "User-Agent": "AnimeCharacterCrawler/1.0 (Educational Project)"
                }

                response = requests.get(api_url, params=params, headers=headers, timeout=30)
                response.raise_for_status()

                data = response.json()
                posts = data.get("post", []) if isinstance(data, dict) else data

                if not posts:
                    break

                page_images = 0
                for post in posts:
                    if self.is_cancelled():
                        break

                    file_url = post.get("file_url", "")
                    if not file_url:
                        continue

                    result = ImageResult(
                        post_id=str(post.get("id", "")),
                        image_url=file_url,
                        thumbnail_url=post.get("preview_url", ""),
                        preview_url=post.get("sample_url", file_url),
                        tags=post.get("tags", ""),
                        tags_list=post.get("tags", "").split(),
                        rating=post.get("rating", "general"),
                        score=post.get("score", 0),
                        width=post.get("width", 0),
                        height=post.get("height", 0),
                        source_site="gelbooru",
                        page_url=f"{base_url}/index.php?page=post&s=view&id={post.get('id')}"
                    )

                    if self.download_images:
                        local_path = self._download_image(result)
                        if local_path:
                            result.local_path = local_path

                    self.image_found.emit(result)
                    total_images += 1
                    page_images += 1

                self.page_complete.emit(page + 1, page_images)

                if page < self.max_pages - 1:
                    self.msleep(1000)

            except Exception as e:
                self.error.emit(f"Error on page {page + 1}: {str(e)}")
                continue

        return total_images

    def _crawl_konachan(self) -> int:
        """Crawl images from Konachan."""
        base_url = "https://konachan.com"
        total_images = 0

        tags = self.search_tags
        if self.rating_filter == "general":
            tags = f"{tags} rating:safe"

        for page in range(1, self.max_pages + 1):
            if self.is_cancelled():
                break

            self.progress.emit(page, self.max_pages, f"Fetching page {page}...")

            try:
                api_url = f"{base_url}/post.json"
                params = {
                    "tags": tags,
                    "page": page,
                    "limit": 20
                }

                headers = {
                    "User-Agent": "AnimeCharacterCrawler/1.0 (Educational Project)"
                }

                response = requests.get(api_url, params=params, headers=headers, timeout=30)
                response.raise_for_status()

                posts = response.json()

                if not posts:
                    break

                page_images = 0
                for post in posts:
                    if self.is_cancelled():
                        break

                    file_url = post.get("file_url") or post.get("jpeg_url") or post.get("sample_url")
                    if not file_url:
                        continue

                    result = ImageResult(
                        post_id=str(post.get("id", "")),
                        image_url=file_url,
                        thumbnail_url=post.get("preview_url", ""),
                        preview_url=post.get("sample_url", file_url),
                        tags=post.get("tags", ""),
                        tags_list=post.get("tags", "").split(),
                        rating=post.get("rating", "s"),
                        score=post.get("score", 0),
                        width=post.get("width", 0),
                        height=post.get("height", 0),
                        source_site="konachan",
                        page_url=f"{base_url}/post/show/{post.get('id')}"
                    )

                    if self.download_images:
                        local_path = self._download_image(result)
                        if local_path:
                            result.local_path = local_path

                    self.image_found.emit(result)
                    total_images += 1
                    page_images += 1

                self.page_complete.emit(page, page_images)

                if page < self.max_pages:
                    self.msleep(1000)

            except Exception as e:
                self.error.emit(f"Error on page {page}: {str(e)}")
                continue

        return total_images

    def _crawl_yandere(self) -> int:
        """Crawl images from Yande.re."""
        base_url = "https://yande.re"
        total_images = 0

        tags = self.search_tags
        if self.rating_filter == "general":
            tags = f"{tags} rating:safe"

        for page in range(1, self.max_pages + 1):
            if self.is_cancelled():
                break

            self.progress.emit(page, self.max_pages, f"Fetching page {page}...")

            try:
                api_url = f"{base_url}/post.json"
                params = {
                    "tags": tags,
                    "page": page,
                    "limit": 20
                }

                headers = {
                    "User-Agent": "AnimeCharacterCrawler/1.0 (Educational Project)"
                }

                response = requests.get(api_url, params=params, headers=headers, timeout=30)
                response.raise_for_status()

                posts = response.json()

                if not posts:
                    break

                page_images = 0
                for post in posts:
                    if self.is_cancelled():
                        break

                    file_url = post.get("file_url") or post.get("jpeg_url") or post.get("sample_url")
                    if not file_url:
                        continue

                    result = ImageResult(
                        post_id=str(post.get("id", "")),
                        image_url=file_url,
                        thumbnail_url=post.get("preview_url", ""),
                        preview_url=post.get("sample_url", file_url),
                        tags=post.get("tags", ""),
                        tags_list=post.get("tags", "").split(),
                        rating=post.get("rating", "s"),
                        score=post.get("score", 0),
                        width=post.get("width", 0),
                        height=post.get("height", 0),
                        source_site="yandere",
                        page_url=f"{base_url}/post/show/{post.get('id')}"
                    )

                    if self.download_images:
                        local_path = self._download_image(result)
                        if local_path:
                            result.local_path = local_path

                    self.image_found.emit(result)
                    total_images += 1
                    page_images += 1

                self.page_complete.emit(page, page_images)

                if page < self.max_pages:
                    self.msleep(1000)

            except Exception as e:
                self.error.emit(f"Error on page {page}: {str(e)}")
                continue

        return total_images

    def _crawl_zerochan(self) -> int:
        """Crawl images from Zerochan."""
        base_url = "https://www.zerochan.net"
        total_images = 0

        # Zerochan uses different URL structure
        search_term = self.search_tags.replace(" ", "+").replace("_", "+")

        for page in range(1, self.max_pages + 1):
            if self.is_cancelled():
                break

            self.progress.emit(page, self.max_pages, f"Fetching page {page}...")

            try:
                # Zerochan has a JSON API
                api_url = f"{base_url}/{search_term}?json&p={page}&l=20"

                headers = {
                    "User-Agent": "AnimeCharacterCrawler/1.0 (Educational Project)"
                }

                response = requests.get(api_url, headers=headers, timeout=30)
                response.raise_for_status()

                data = response.json()
                posts = data.get("items", [])

                if not posts:
                    break

                page_images = 0
                for post in posts:
                    if self.is_cancelled():
                        break

                    # Zerochan image URL pattern
                    post_id = post.get("id", "")
                    thumbnail = post.get("thumbnail", "")

                    # Construct full image URL from thumbnail
                    if thumbnail:
                        # Replace thumbnail path with full image path
                        file_url = thumbnail.replace("/240/", "/full/").replace(".240.", ".full.")
                    else:
                        continue

                    result = ImageResult(
                        post_id=str(post_id),
                        image_url=file_url,
                        thumbnail_url=thumbnail,
                        preview_url=file_url,
                        tags=post.get("tag", ""),
                        tags_list=post.get("tag", "").split() if post.get("tag") else [],
                        rating="safe",
                        width=post.get("width", 0),
                        height=post.get("height", 0),
                        source_site="zerochan",
                        page_url=f"{base_url}/{post_id}"
                    )

                    if self.download_images:
                        local_path = self._download_image(result)
                        if local_path:
                            result.local_path = local_path

                    self.image_found.emit(result)
                    total_images += 1
                    page_images += 1

                self.page_complete.emit(page, page_images)

                if page < self.max_pages:
                    self.msleep(1500)  # Zerochan needs more delay

            except Exception as e:
                self.error.emit(f"Error on page {page}: {str(e)}")
                continue

        return total_images

    def _crawl_anime_pictures(self) -> int:
        """Crawl images from Anime-Pictures.net."""
        base_url = "https://anime-pictures.net"
        total_images = 0

        search_term = self.search_tags.replace(" ", "+")

        for page in range(self.max_pages):
            if self.is_cancelled():
                break

            self.progress.emit(page + 1, self.max_pages, f"Fetching page {page + 1}...")

            try:
                # Anime-Pictures API
                api_url = f"{base_url}/api/v3/posts"
                params = {
                    "page": page,
                    "search_tag": search_term,
                    "posts_per_page": 20,
                    "lang": "en"
                }

                headers = {
                    "User-Agent": "AnimeCharacterCrawler/1.0 (Educational Project)"
                }

                response = requests.get(api_url, params=params, headers=headers, timeout=30)
                response.raise_for_status()

                data = response.json()
                posts = data.get("posts", [])

                if not posts:
                    break

                page_images = 0
                for post in posts:
                    if self.is_cancelled():
                        break

                    post_id = post.get("id", "")
                    # Build image URLs
                    file_url = f"{base_url}/images/{post.get('file_path', '')}"
                    preview_url = f"{base_url}/previews/{post.get('preview_path', '')}"

                    if not post.get("file_path"):
                        continue

                    result = ImageResult(
                        post_id=str(post_id),
                        image_url=file_url,
                        thumbnail_url=preview_url,
                        preview_url=preview_url,
                        tags=" ".join(post.get("tags", [])) if isinstance(post.get("tags"), list) else post.get("tags", ""),
                        tags_list=post.get("tags", []) if isinstance(post.get("tags"), list) else [],
                        rating="safe" if post.get("ero", 0) == 0 else "explicit",
                        score=post.get("star_count", 0),
                        width=post.get("width", 0),
                        height=post.get("height", 0),
                        source_site="anime-pictures",
                        page_url=f"{base_url}/posts/{post_id}"
                    )

                    if self.download_images:
                        local_path = self._download_image(result)
                        if local_path:
                            result.local_path = local_path

                    self.image_found.emit(result)
                    total_images += 1
                    page_images += 1

                self.page_complete.emit(page + 1, page_images)

                if page < self.max_pages - 1:
                    self.msleep(1000)

            except Exception as e:
                self.error.emit(f"Error on page {page + 1}: {str(e)}")
                continue

        return total_images

    def _download_image(self, result: ImageResult) -> Optional[str]:
        """Download an image and return the local path."""
        try:
            # Create site-specific subdirectory
            site_dir = self.output_dir / result.source_site
            site_dir.mkdir(parents=True, exist_ok=True)

            # Get file extension from URL
            url_path = result.image_url.split("?")[0]
            ext = os.path.splitext(url_path)[1] or ".jpg"

            # Create filename
            filename = f"{result.post_id}{ext}"
            filepath = site_dir / filename

            # Skip if already exists
            if filepath.exists():
                return str(filepath)

            # Download
            headers = {
                "User-Agent": "AnimeCharacterCrawler/1.0 (Educational Project)"
            }

            response = requests.get(result.image_url, headers=headers, timeout=60, stream=True)
            response.raise_for_status()

            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            return str(filepath)

        except Exception as e:
            return None


class TagSuggestionThread(QThread):
    """
    Thread for fetching tag suggestions/autocomplete from booru sites.
    """

    suggestions_ready = pyqtSignal(list)  # List of tag suggestions
    error = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.query = ""
        self.site = "danbooru"

    def configure(self, query: str, site: str = "danbooru"):
        """Set the query to search for."""
        self.query = query
        self.site = site

    def run(self):
        """Fetch tag suggestions."""
        if not self.query or len(self.query) < 2:
            self.suggestions_ready.emit([])
            return

        try:
            suggestions = []

            if self.site == "danbooru":
                suggestions = self._get_danbooru_suggestions()
            elif self.site == "safebooru":
                suggestions = self._get_safebooru_suggestions()
            elif self.site == "gelbooru":
                suggestions = self._get_gelbooru_suggestions()

            self.suggestions_ready.emit(suggestions)

        except Exception as e:
            self.error.emit(str(e))
            self.suggestions_ready.emit([])

    def _get_danbooru_suggestions(self) -> List[Dict[str, Any]]:
        """Get tag suggestions from Danbooru."""
        url = "https://danbooru.donmai.us/autocomplete.json"
        params = {
            "search[query]": self.query,
            "search[type]": "tag_query",
            "limit": 10
        }
        headers = {"User-Agent": "AnimeCharacterCrawler/1.0"}

        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()
        suggestions = []

        for item in data:
            suggestions.append({
                "name": item.get("value", ""),
                "count": item.get("post_count", 0),
                "category": item.get("category", "general"),
                "label": item.get("label", item.get("value", ""))
            })

        return suggestions

    def _get_safebooru_suggestions(self) -> List[Dict[str, Any]]:
        """Get tag suggestions from Safebooru."""
        # Safebooru doesn't have a great autocomplete API
        # Return empty for now
        return []

    def _get_gelbooru_suggestions(self) -> List[Dict[str, Any]]:
        """Get tag suggestions from Gelbooru."""
        url = "https://gelbooru.com/index.php"
        params = {
            "page": "autocomplete2",
            "term": self.query,
            "type": "tag_query",
            "limit": 10
        }
        headers = {"User-Agent": "AnimeCharacterCrawler/1.0"}

        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            suggestions = []

            for item in data:
                suggestions.append({
                    "name": item.get("value", ""),
                    "count": item.get("post_count", 0),
                    "category": item.get("category", "general"),
                    "label": item.get("label", item.get("value", ""))
                })

            return suggestions
        except:
            return []
