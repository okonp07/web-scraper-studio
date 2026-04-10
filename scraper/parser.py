"""HTML parsing and metadata extraction."""

from __future__ import annotations

from dataclasses import dataclass

from bs4 import BeautifulSoup, Tag

from app.utils.text import normalize_whitespace
from app.utils.url import absolutize_url


@dataclass(slots=True)
class LinkCandidate:
    url: str
    text: str
    source: str


@dataclass(slots=True)
class ParsedPage:
    title: str
    canonical_url: str
    meta_description: str | None
    publication_date: str | None
    headings: list[str]
    links: list[LinkCandidate]
    soup: BeautifulSoup


def parse_page(html: str, base_url: str, final_url: str) -> ParsedPage:
    """Parse a page and return metadata plus discovered links."""

    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript", "template"]):
        tag.decompose()

    title = _first_meta_content(soup, ("meta[property='og:title']",)) or (
        soup.title.get_text(strip=True) if soup.title else ""
    )
    title = title or final_url

    canonical_tag = soup.select_one("link[rel='canonical']")
    canonical_url = (
        absolutize_url(final_url, canonical_tag.get("href", ""))
        if canonical_tag and canonical_tag.get("href")
        else final_url
    )

    meta_description = _first_meta_content(
        soup,
        (
            "meta[name='description']",
            "meta[property='og:description']",
            "meta[name='twitter:description']",
        ),
    )

    publication_date = _extract_publication_date(soup)
    headings = [
        normalize_whitespace(node.get_text(" ", strip=True))
        for node in soup.find_all(["h1", "h2", "h3"])
        if normalize_whitespace(node.get_text(" ", strip=True))
    ][:15]
    links = _extract_links(soup, final_url)

    return ParsedPage(
        title=title.strip(),
        canonical_url=canonical_url,
        meta_description=meta_description,
        publication_date=publication_date,
        headings=headings,
        links=links,
        soup=soup,
    )


def _first_meta_content(soup: BeautifulSoup, selectors: tuple[str, ...]) -> str | None:
    for selector in selectors:
        tag = soup.select_one(selector)
        if tag and tag.get("content"):
            return normalize_whitespace(tag["content"])
    return None


def _extract_publication_date(soup: BeautifulSoup) -> str | None:
    for selector in (
        "meta[property='article:published_time']",
        "meta[name='pubdate']",
        "meta[name='publish-date']",
        "meta[itemprop='datePublished']",
        "time[datetime]",
    ):
        tag = soup.select_one(selector)
        if not tag:
            continue
        value = tag.get("content") or tag.get("datetime") or tag.get_text(" ", strip=True)
        if value:
            return normalize_whitespace(value)
    return None


def _extract_links(soup: BeautifulSoup, base_url: str) -> list[LinkCandidate]:
    links: list[LinkCandidate] = []
    seen: set[str] = set()

    for anchor in soup.find_all("a", href=True):
        href = anchor.get("href", "").strip()
        if not href or href.startswith("#"):
            continue
        lowered = href.lower()
        if lowered.startswith(("mailto:", "tel:", "javascript:", "data:")):
            continue

        absolute = absolutize_url(base_url, href)
        if absolute in seen:
            continue

        source = _link_source(anchor)
        links.append(
            LinkCandidate(
                url=absolute,
                text=normalize_whitespace(anchor.get_text(" ", strip=True)),
                source=source,
            )
        )
        seen.add(absolute)

    return links


def _link_source(anchor: Tag) -> str:
    if anchor.find_parent(["nav", "header", "footer"]):
        return "navigation"
    if anchor.find_parent(["main", "article"]):
        return "content"
    return "page"

