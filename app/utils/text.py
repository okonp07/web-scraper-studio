"""Text helpers used across crawling and export layers."""

from __future__ import annotations

import hashlib
import re
from urllib.parse import urlparse

WHITESPACE_RE = re.compile(r"\s+")
MULTI_BLANK_RE = re.compile(r"\n{3,}")
NON_FILENAME_RE = re.compile(r"[^a-zA-Z0-9._-]+")


def normalize_whitespace(text: str) -> str:
    """Collapse noisy whitespace while preserving paragraph boundaries."""

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return MULTI_BLANK_RE.sub("\n\n", text).strip()


def normalize_for_similarity(text: str) -> str:
    """Normalize text aggressively for duplicate detection."""

    return WHITESPACE_RE.sub(" ", text).strip().lower()


def text_hash(text: str) -> str:
    """Create a stable SHA-256 hash for cleaned text."""

    return hashlib.sha256(normalize_for_similarity(text).encode("utf-8")).hexdigest()


def truncate(text: str, limit: int = 240) -> str:
    """Trim long text snippets for UI previews."""

    cleaned = normalize_whitespace(text)
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "..."


def safe_filename_from_url(url: str) -> str:
    """Generate a filesystem-safe stem from a URL."""

    parsed = urlparse(url)
    path = parsed.path.strip("/") or "home"
    candidate = f"{parsed.netloc}-{path}".replace("/", "-")
    candidate = NON_FILENAME_RE.sub("-", candidate).strip("-")
    return candidate[:100] or "scrape"


def word_count(text: str) -> int:
    """Count words in a reasonably human-oriented way."""

    return len([token for token in WHITESPACE_RE.split(text.strip()) if token])

