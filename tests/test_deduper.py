"""Tests for duplicate detection."""

from scraper.deduper import DuplicateDetector


def test_duplicate_detector_flags_identical_text() -> None:
    detector = DuplicateDetector(similarity_threshold=0.94)
    url = "https://example.com/a"
    text = "This is a long article body. " * 20

    detector.remember(url, text)
    duplicate = detector.find_duplicate("https://example.com/b", text)

    assert duplicate is not None
    assert duplicate.source_url == url
    assert duplicate.similarity == 1.0


def test_duplicate_detector_ignores_distinct_text() -> None:
    detector = DuplicateDetector(similarity_threshold=0.94)
    detector.remember("https://example.com/a", "Apples and pears " * 30)

    duplicate = detector.find_duplicate("https://example.com/b", "Oranges and mangoes " * 30)

    assert duplicate is None

