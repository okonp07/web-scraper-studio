"""Readable content extraction and block structuring."""

from __future__ import annotations

from dataclasses import dataclass

import trafilatura
from bs4 import BeautifulSoup, Tag
from readability import Document

from app.models.schemas import BlockType, BoilerplateMode, ContentBlock, ImageAsset
from app.utils.text import normalize_whitespace, word_count
from app.utils.url import absolutize_url


NOISY_TOKENS = (
    "cookie",
    "consent",
    "newsletter",
    "subscribe",
    "breadcrumb",
    "share",
    "social",
    "related",
    "promo",
    "banner",
    "advert",
    "sidebar",
    "footer",
    "header",
    "menu",
    "nav",
)
BOILERPLATE_PHRASES = (
    "accept cookies",
    "all rights reserved",
    "sign up for our newsletter",
    "subscribe to our newsletter",
    "privacy preference center",
    "skip to content",
)
MEANINGFUL_TAGS = {"h1", "h2", "h3", "p", "ul", "ol", "blockquote", "table", "figure", "img"}


@dataclass(slots=True)
class ExtractionResult:
    blocks: list[ContentBlock]
    text_content: str
    images: list[ImageAsset]


class ContentExtractor:
    """Convert messy HTML into readable semantic blocks."""

    def __init__(self, minimum_text_length: int) -> None:
        self.minimum_text_length = minimum_text_length

    def extract(self, html: str, base_url: str, mode: BoilerplateMode) -> ExtractionResult:
        """Extract main content with readability first and trafilatura fallback."""

        working = BeautifulSoup(html, "lxml")
        self._strip_noise(working, aggressive=mode == BoilerplateMode.AGGRESSIVE)
        readable_html = self._readability_html(str(working))
        if not readable_html:
            readable_html = str(working)
        article = BeautifulSoup(readable_html, "lxml")
        blocks, images = self._build_blocks(article, base_url)
        text_content = self._blocks_to_text(blocks)

        if word_count(text_content) < self.minimum_text_length:
            fallback_text = trafilatura.extract(
                html,
                include_comments=False,
                include_links=False,
                include_tables=True,
                deduplicate=True,
                favor_precision=True,
                output_format="txt",
            )
            fallback_text = normalize_whitespace(fallback_text or "")
            if word_count(fallback_text) > word_count(text_content):
                blocks = [
                    ContentBlock(kind=BlockType.PARAGRAPH, text=paragraph)
                    for paragraph in fallback_text.split("\n\n")
                    if paragraph.strip()
                ]
                text_content = fallback_text
                images = []

        return ExtractionResult(blocks=blocks, text_content=text_content, images=images)

    def _strip_noise(self, soup: BeautifulSoup, aggressive: bool) -> None:
        for tag in soup(["script", "style", "noscript", "template", "svg", "canvas"]):
            tag.decompose()

        structural_tags = ["nav", "footer", "aside"]
        if aggressive:
            structural_tags.extend(["header", "form", "button"])
        for tag_name in structural_tags:
            for tag in soup.find_all(tag_name):
                tag.decompose()

        for tag in list(soup.find_all(True)):
            if tag.decomposed if hasattr(tag, "decomposed") else not tag.parent:
                continue
            try:
                classes = tag.get("class", []) or []
                tag_id = tag.get("id", "") or ""
                signature = " ".join(list(classes) + [tag_id]).lower()
                if any(token in signature for token in NOISY_TOKENS):
                    tag.decompose()
            except Exception:
                continue

    def _readability_html(self, html: str) -> str:
        try:
            return Document(html).summary(html_partial=True)
        except Exception:
            return html

    def _build_blocks(self, soup: BeautifulSoup, base_url: str) -> tuple[list[ContentBlock], list[ImageAsset]]:
        container = soup.body or soup
        blocks: list[ContentBlock] = []
        images: list[ImageAsset] = []
        seen_texts: set[str] = set()
        seen_images: set[str] = set()

        for element in container.find_all(MEANINGFUL_TAGS):
            if element.find_parent(MEANINGFUL_TAGS):
                continue

            if element.name in {"h1", "h2", "h3"}:
                text = normalize_whitespace(element.get_text(" ", strip=True))
                if text and text not in seen_texts:
                    blocks.append(
                        ContentBlock(kind=BlockType.HEADING, text=text, level=int(element.name[1]))
                    )
                    seen_texts.add(text)
                continue

            if element.name == "p":
                text = normalize_whitespace(element.get_text(" ", strip=True))
                if self._keep_text_block(text, seen_texts):
                    blocks.append(ContentBlock(kind=BlockType.PARAGRAPH, text=text))
                    seen_texts.add(text)
                continue

            if element.name in {"ul", "ol"}:
                items = [
                    normalize_whitespace(item.get_text(" ", strip=True))
                    for item in element.find_all("li", recursive=False)
                    if normalize_whitespace(item.get_text(" ", strip=True))
                ]
                items = [item for item in items if item not in seen_texts]
                if items:
                    blocks.append(
                        ContentBlock(
                            kind=BlockType.BULLET_LIST if element.name == "ul" else BlockType.ORDERED_LIST,
                            items=items,
                        )
                    )
                    seen_texts.update(items)
                continue

            if element.name == "blockquote":
                text = normalize_whitespace(element.get_text(" ", strip=True))
                if self._keep_text_block(text, seen_texts):
                    blocks.append(ContentBlock(kind=BlockType.QUOTE, text=text))
                    seen_texts.add(text)
                continue

            if element.name == "table":
                rows = []
                for row in element.find_all("tr"):
                    cells = [
                        normalize_whitespace(cell.get_text(" ", strip=True))
                        for cell in row.find_all(["th", "td"])
                        if normalize_whitespace(cell.get_text(" ", strip=True))
                    ]
                    if cells:
                        rows.append(cells[:8])
                if rows:
                    blocks.append(ContentBlock(kind=BlockType.TABLE, rows=rows[:20]))
                continue

            image_asset = self._image_from_element(element, base_url)
            if image_asset and image_asset.source_url not in seen_images:
                blocks.append(
                    ContentBlock(
                        kind=BlockType.IMAGE,
                        text=image_asset.source_url,
                        caption=image_asset.caption or image_asset.alt_text,
                    )
                )
                images.append(image_asset)
                seen_images.add(image_asset.source_url)

        return blocks, images

    def _image_from_element(self, element: Tag, base_url: str) -> ImageAsset | None:
        node = element if element.name == "img" else element.find("img")
        if not node:
            return None
        src = node.get("src") or node.get("data-src") or node.get("data-original")
        if not src:
            return None
        alt_text = normalize_whitespace(node.get("alt", ""))
        caption = ""
        if element.name == "figure":
            caption = normalize_whitespace(element.get_text(" ", strip=True))
        if self._looks_decorative_image(src, alt_text):
            return None
        return ImageAsset(
            source_url=absolutize_url(base_url, src),
            alt_text=alt_text or None,
            caption=caption or alt_text or None,
        )

    def _keep_text_block(self, text: str, seen_texts: set[str]) -> bool:
        if not text or text in seen_texts:
            return False
        if text.lower() in BOILERPLATE_PHRASES:
            return False
        if any(phrase in text.lower() for phrase in BOILERPLATE_PHRASES):
            return False
        return len(text) >= 20 or text.endswith(".")

    def _looks_decorative_image(self, src: str, alt_text: str) -> bool:
        signature = f"{src} {alt_text}".lower()
        return any(token in signature for token in ("logo", "icon", "avatar", "share", "social", "sprite"))

    def _blocks_to_text(self, blocks: list[ContentBlock]) -> str:
        parts: list[str] = []
        for block in blocks:
            if block.kind == BlockType.HEADING and block.text:
                parts.append(block.text)
            elif block.kind in {BlockType.PARAGRAPH, BlockType.QUOTE} and block.text:
                parts.append(block.text)
            elif block.kind in {BlockType.BULLET_LIST, BlockType.ORDERED_LIST} and block.items:
                parts.append("\n".join(block.items))
            elif block.kind == BlockType.TABLE and block.rows:
                parts.append("\n".join(" | ".join(row) for row in block.rows))
        return normalize_whitespace("\n\n".join(parts))

