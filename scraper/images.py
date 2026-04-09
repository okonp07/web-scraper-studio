"""Relevant content image downloading and preparation."""

from __future__ import annotations

import io
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from app.models.schemas import ImageAsset, PageContent
from app.utils.files import ensure_directory
from scraper.fetcher import FetchError, PageFetcher


class ContentImageManager:
    """Download body images for PDF export while skipping decorative assets."""

    def __init__(self, fetcher: PageFetcher, temp_dir: Path, max_images_per_page: int) -> None:
        self.fetcher = fetcher
        self.temp_dir = ensure_directory(temp_dir)
        self.max_images_per_page = max_images_per_page

    def enrich_pages(self, pages: list[PageContent]) -> int:
        """Download accessible images and attach local file paths to page image assets."""

        total = 0
        for page in pages:
            selected: list[ImageAsset] = []
            for image in page.images[: self.max_images_per_page]:
                prepared = self._prepare_image(image)
                if prepared:
                    selected.append(prepared)
                    total += 1
            page.images = selected
        return total

    def _prepare_image(self, image: ImageAsset) -> ImageAsset | None:
        try:
            fetched = self.fetcher.fetch_binary(image.source_url, max_bytes=8_000_000)
        except FetchError:
            return None

        try:
            with Image.open(io.BytesIO(fetched.content_bytes)) as raw:
                width, height = raw.size
                if width < 240 or height < 140:
                    return None
                if max(width, height) > 1600:
                    raw.thumbnail((1600, 1600))
                prepared = raw.convert("RGB")
                filename = f"{abs(hash(image.source_url))}.jpg"
                local_path = self.temp_dir / filename
                prepared.save(local_path, format="JPEG", quality=85, optimize=True)
        except (UnidentifiedImageError, OSError, ValueError):
            return None

        image.local_path = local_path
        image.width = width
        image.height = height
        return image

