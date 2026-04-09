"""Tests for URL normalization and scope logic."""

from app.models.schemas import CrawlScope, ScrapeMode, ScrapeRequest
from app.utils.url import canonicalize_url, in_scope, is_skippable_url, normalize_user_url


def test_normalize_user_url_adds_scheme() -> None:
    assert normalize_user_url("example.com/path") == "https://example.com/path"


def test_canonicalize_url_strips_tracking_params() -> None:
    url = canonicalize_url(
        "https://example.com/path/?utm_source=test&b=2&a=1",
        include_query_params=True,
    )
    assert url == "https://example.com/path/?a=1&b=2"


def test_scope_rules_distinguish_subdomain_and_root_domain() -> None:
    start = "https://docs.example.com/guide"
    assert in_scope("https://docs.example.com/page", start, CrawlScope.SAME_SUBDOMAIN)
    assert not in_scope("https://blog.example.com/post", start, CrawlScope.SAME_SUBDOMAIN)
    assert in_scope("https://blog.example.com/post", start, CrawlScope.ROOT_DOMAIN)


def test_skippable_url_catches_non_content_paths() -> None:
    assert is_skippable_url("https://shop.example.com/checkout")
    assert is_skippable_url("https://example.com/tag/python")
    assert not is_skippable_url("https://example.com/articles/story")


def test_page_only_request_forces_single_page_limits() -> None:
    request = ScrapeRequest(
        start_url="example.com",
        mode=ScrapeMode.PAGE_ONLY,
        max_pages=25,
        max_depth=3,
        output_formats=["txt"],
    )
    assert request.max_pages == 1
    assert request.max_depth == 0

