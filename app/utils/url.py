"""URL normalization and crawl boundary helpers."""

from __future__ import annotations

import posixpath
import re
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

import tldextract

from app.models.schemas import CrawlScope

TRACKING_PARAMS = {
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "ref",
    "source",
    "utm_campaign",
    "utm_content",
    "utm_medium",
    "utm_source",
    "utm_term",
}
SKIP_PATTERNS = (
    "/login",
    "/signin",
    "/sign-in",
    "/sign_up",
    "/signup",
    "/cart",
    "/checkout",
    "/account",
    "/admin",
    "/wp-admin",
    "/tag/",
    "/tags/",
    "/print",
    "/feed",
)
ASSET_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".svg",
    ".webp",
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
    ".mp3",
    ".mp4",
    ".avi",
    ".mov",
    ".css",
    ".js",
    ".json",
    ".xml",
    ".ico",
    ".woff",
    ".woff2",
}
SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*://")
EXTRACT = tldextract.TLDExtract(suffix_list_urls=())


def normalize_user_url(url: str) -> str:
    """Normalize user input and auto-add https when the scheme is missing."""

    url = (url or "").strip()
    if not url:
        raise ValueError("A URL is required.")
    if not SCHEME_RE.match(url):
        url = f"https://{url}"
    return canonicalize_url(url, include_query_params=True)


def canonicalize_url(url: str, include_query_params: bool = False) -> str:
    """Normalize a URL for visited-set and duplicate handling."""

    parsed = urlparse(url)
    scheme = (parsed.scheme or "https").lower()
    netloc = parsed.netloc.lower()

    if ":" in netloc:
        host, port = netloc.rsplit(":", maxsplit=1)
        if (scheme == "http" and port == "80") or (scheme == "https" and port == "443"):
            netloc = host

    normalized_path = posixpath.normpath(parsed.path or "/")
    if parsed.path.endswith("/") and normalized_path != "/":
        normalized_path = f"{normalized_path}/"
    if not normalized_path.startswith("/"):
        normalized_path = f"/{normalized_path}"

    query = ""
    if include_query_params:
        query_pairs = [
            (key, value)
            for key, value in parse_qsl(parsed.query, keep_blank_values=True)
            if key.lower() not in TRACKING_PARAMS
        ]
        query = urlencode(sorted(query_pairs))

    return urlunparse((scheme, netloc, normalized_path, "", query, ""))


def absolutize_url(base_url: str, href: str) -> str:
    """Resolve relative links against a base URL."""

    return canonicalize_url(urljoin(base_url, href), include_query_params=True)


def is_supported_url(url: str) -> bool:
    """Return True when the URL is a crawlable HTTP target."""

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    if not parsed.netloc:
        return False
    if parsed.fragment:
        url = url.split("#", maxsplit=1)[0]
    lowered = url.lower()
    return not any(lowered.endswith(ext) for ext in ASSET_EXTENSIONS)


def is_skippable_url(url: str) -> bool:
    """Heuristic skip rules for obviously non-content paths."""

    lowered = url.lower()
    return any(pattern in lowered for pattern in SKIP_PATTERNS)


def root_domain(url: str) -> str:
    """Return the registrable root domain for a URL."""

    extracted = EXTRACT(urlparse(url).hostname or "")
    suffix = f".{extracted.suffix}" if extracted.suffix else ""
    return f"{extracted.domain}{suffix}".strip(".")


def hostname(url: str) -> str:
    """Return the normalized hostname for a URL."""

    return (urlparse(url).hostname or "").lower()


def in_scope(candidate_url: str, start_url: str, scope: CrawlScope) -> bool:
    """Check whether a candidate stays within the requested crawl scope."""

    if scope == CrawlScope.SAME_SUBDOMAIN:
        return hostname(candidate_url) == hostname(start_url)
    return root_domain(candidate_url) == root_domain(start_url)


def candidate_sitemap_urls(start_url: str) -> list[str]:
    """Produce likely sitemap.xml locations for a site."""

    parsed = urlparse(start_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    return [
        f"{origin}/sitemap.xml",
        f"{origin}/sitemap_index.xml",
        f"{origin}/sitemap-index.xml",
    ]

