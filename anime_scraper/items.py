# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy import Field
from itemloaders.processors import TakeFirst, MapCompose, Join
from datetime import datetime


def clean_string(value):
    """Remove extra whitespace from strings."""
    if value:
        return value.strip()
    return value


def parse_tags(value):
    """Parse tags string into a list."""
    if value:
        return [tag.strip() for tag in value.split() if tag.strip()]
    return []


def ensure_https(url):
    """Ensure URL uses HTTPS."""
    if url and url.startswith("http://"):
        return url.replace("http://", "https://", 1)
    return url


class AnimeImageItem(scrapy.Item):
    """
    Item representing a scraped anime image with metadata.

    This item captures all relevant information from booru-style
    image boards including the image URL, tags, and metadata.
    """

    # Primary identifiers
    post_id = Field(
        input_processor=MapCompose(clean_string),
        output_processor=TakeFirst()
    )

    # Image URLs
    image_url = Field(
        input_processor=MapCompose(clean_string, ensure_https),
        output_processor=TakeFirst()
    )

    thumbnail_url = Field(
        input_processor=MapCompose(clean_string, ensure_https),
        output_processor=TakeFirst()
    )

    # Large/preview image URL (between thumbnail and full)
    preview_url = Field(
        input_processor=MapCompose(clean_string, ensure_https),
        output_processor=TakeFirst()
    )

    # Tags and metadata
    tags = Field(
        input_processor=MapCompose(clean_string),
        output_processor=TakeFirst()
    )

    tags_list = Field()  # Parsed list of tags

    # Character and series information
    character = Field(
        input_processor=MapCompose(clean_string),
        output_processor=TakeFirst()
    )

    series = Field(
        input_processor=MapCompose(clean_string),
        output_processor=TakeFirst()
    )

    artist = Field(
        input_processor=MapCompose(clean_string),
        output_processor=TakeFirst()
    )

    # Image properties
    width = Field(output_processor=TakeFirst())
    height = Field(output_processor=TakeFirst())
    file_size = Field(output_processor=TakeFirst())
    file_ext = Field(
        input_processor=MapCompose(clean_string),
        output_processor=TakeFirst()
    )

    # Rating (safe, questionable, explicit)
    rating = Field(
        input_processor=MapCompose(clean_string),
        output_processor=TakeFirst()
    )

    # Source information
    source_url = Field(
        input_processor=MapCompose(clean_string, ensure_https),
        output_processor=TakeFirst()
    )

    source_site = Field(
        input_processor=MapCompose(clean_string),
        output_processor=TakeFirst()
    )

    page_url = Field(
        input_processor=MapCompose(clean_string, ensure_https),
        output_processor=TakeFirst()
    )

    # Timestamps
    created_at = Field(output_processor=TakeFirst())
    scraped_at = Field(output_processor=TakeFirst())

    # Score/popularity
    score = Field(output_processor=TakeFirst())
    favorites = Field(output_processor=TakeFirst())

    # Local storage info (populated by pipeline)
    local_path = Field(output_processor=TakeFirst())
    image_hash = Field(output_processor=TakeFirst())
    is_duplicate = Field(output_processor=TakeFirst())

    # Pagination info
    page_number = Field(output_processor=TakeFirst())
    position_on_page = Field(output_processor=TakeFirst())


class PageItem(scrapy.Item):
    """
    Item representing a scraped page of results.
    Used for tracking pagination and display purposes.
    """

    page_number = Field(output_processor=TakeFirst())
    total_images = Field(output_processor=TakeFirst())
    images = Field()  # List of AnimeImageItem
    next_page_url = Field(output_processor=TakeFirst())
    previous_page_url = Field(output_processor=TakeFirst())
    scraped_at = Field(output_processor=TakeFirst())
    search_tags = Field(output_processor=TakeFirst())
