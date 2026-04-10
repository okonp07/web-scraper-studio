"""Pydantic data models shared across the app."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Self
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator, model_validator


class ScrapeMode(StrEnum):
    PAGE_ONLY = "page_only"
    FULL_SCRAPE = "full_scrape"


class CrawlScope(StrEnum):
    SAME_SUBDOMAIN = "same_subdomain"
    ROOT_DOMAIN = "root_domain"


class OutputFormat(StrEnum):
    TXT = "txt"
    DOCX = "docx"
    PDF = "pdf"
    IMAGES = "images"


class BoilerplateMode(StrEnum):
    CONSERVATIVE = "conservative"
    AGGRESSIVE = "aggressive"


class BlockType(StrEnum):
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    BULLET_LIST = "bullet_list"
    ORDERED_LIST = "ordered_list"
    QUOTE = "quote"
    TABLE = "table"
    IMAGE = "image"


class ContentBlock(BaseModel):
    kind: BlockType
    text: str | None = None
    level: int | None = None
    items: list[str] = Field(default_factory=list)
    rows: list[list[str]] = Field(default_factory=list)
    caption: str | None = None


class ImageAsset(BaseModel):
    source_url: str
    alt_text: str | None = None
    caption: str | None = None
    local_path: Path | None = None
    width: int | None = None
    height: int | None = None


class PageContent(BaseModel):
    order: int
    requested_url: str
    final_url: str
    canonical_url: str
    title: str
    meta_description: str | None = None
    publication_date: str | None = None
    headings: list[str] = Field(default_factory=list)
    blocks: list[ContentBlock] = Field(default_factory=list)
    text_content: str
    word_count: int = 0
    images: list[ImageAsset] = Field(default_factory=list)
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ScrapeArtifact(BaseModel):
    format: OutputFormat
    filename: str
    mime_type: str
    bytes_data: bytes


class ScrapeIssue(BaseModel):
    url: str
    reason: str
    detail: str | None = None


class ScrapeSummary(BaseModel):
    start_url: str
    mode: ScrapeMode
    pages_scraped: int
    pages_skipped: int
    total_words: int
    total_images: int
    runtime_seconds: float
    discovered_pages: int
    error_count: int


class ScrapeResult(BaseModel):
    summary: ScrapeSummary
    pages: list[PageContent]
    artifacts: list[ScrapeArtifact]
    skipped_pages: list[ScrapeIssue] = Field(default_factory=list)
    errors: list[ScrapeIssue] = Field(default_factory=list)
    logs: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ScrapeRequest(BaseModel):
    start_url: str
    mode: ScrapeMode
    max_pages: int = 25
    max_depth: int = 2
    delay_seconds: float = 0.8
    timeout_seconds: float = 20.0
    max_file_size_mb: float = 6.0
    concurrency: int = 1
    include_query_params: bool = False
    scope: CrawlScope = CrawlScope.SAME_SUBDOMAIN
    include_sitemap: bool = True
    use_browser_fallback: bool = True
    include_images_in_pdf: bool = True
    include_metadata: bool = True
    boilerplate_mode: BoilerplateMode = BoilerplateMode.CONSERVATIVE
    output_formats: list[OutputFormat] = Field(default_factory=lambda: [OutputFormat.TXT])

    @field_validator("start_url", mode="before")
    @classmethod
    def _normalize_url(cls, value: str) -> str:
        value = (value or "").strip()
        if not value:
            raise ValueError("A URL is required.")
        if "://" not in value:
            value = f"https://{value}"
        parsed = urlparse(value)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("Enter a valid website URL.")
        return value

    @model_validator(mode="after")
    def _validate_limits(self) -> Self:
        if self.mode == ScrapeMode.PAGE_ONLY:
            self.max_pages = 1
            self.max_depth = 0
        self.max_pages = max(1, min(self.max_pages, 500))
        self.max_depth = max(0, min(self.max_depth, 8))
        self.delay_seconds = max(0.0, min(self.delay_seconds, 30.0))
        self.timeout_seconds = max(5.0, min(self.timeout_seconds, 120.0))
        self.max_file_size_mb = max(0.5, min(self.max_file_size_mb, 50.0))
        self.concurrency = max(1, min(self.concurrency, 8))
        if not self.output_formats:
            raise ValueError("Select at least one output format.")
        return self

