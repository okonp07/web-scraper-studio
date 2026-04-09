"""Near-duplicate page detection."""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher

from app.utils.text import normalize_for_similarity, text_hash


@dataclass(slots=True)
class DuplicateMatch:
    source_url: str
    similarity: float


class DuplicateDetector:
    """Track page text fingerprints and reject obvious duplicate pages."""

    def __init__(self, similarity_threshold: float) -> None:
        self.similarity_threshold = similarity_threshold
        self._hashes: dict[str, str] = {}
        self._samples: list[tuple[str, str]] = []

    def find_duplicate(self, url: str, text: str) -> DuplicateMatch | None:
        normalized = normalize_for_similarity(text)
        if len(normalized) < 120:
            return None

        digest = text_hash(normalized)
        if digest in self._hashes:
            return DuplicateMatch(source_url=self._hashes[digest], similarity=1.0)

        candidate = normalized[:5000]
        for existing_url, existing_text in self._samples:
            ratio = SequenceMatcher(None, candidate, existing_text[:5000]).ratio()
            if ratio >= self.similarity_threshold:
                return DuplicateMatch(source_url=existing_url, similarity=ratio)
        return None

    def remember(self, url: str, text: str) -> None:
        normalized = normalize_for_similarity(text)
        if len(normalized) < 120:
            return
        digest = text_hash(normalized)
        self._hashes[digest] = url
        self._samples.append((url, normalized))

