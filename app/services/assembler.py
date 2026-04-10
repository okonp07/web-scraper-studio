"""Document assembly and cross-page cleanup."""

from __future__ import annotations

from collections import Counter

from app.models.schemas import BlockType, BoilerplateMode, ContentBlock, PageContent
from app.utils.text import normalize_for_similarity, normalize_whitespace, word_count


class DocumentAssembler:
    """Remove repeated boilerplate across pages and preserve readable flow."""

    def refine_pages(self, pages: list[PageContent], mode: BoilerplateMode) -> list[PageContent]:
        if len(pages) < 2:
            return pages

        threshold = 0.6 if mode == BoilerplateMode.CONSERVATIVE else 0.4
        repeated = self._repeated_paragraphs(pages, threshold=threshold)
        for page in pages:
            cleaned_blocks: list[ContentBlock] = []
            for block in page.blocks:
                if self._should_drop(block, repeated):
                    continue
                cleaned_blocks.append(block)
            page.blocks = cleaned_blocks
            page.text_content = self._blocks_to_text(cleaned_blocks)
            page.word_count = word_count(page.text_content)
        return pages

    def _repeated_paragraphs(self, pages: list[PageContent], threshold: float) -> set[str]:
        counter: Counter[str] = Counter()
        minimum_occurrences = max(2, int(len(pages) * threshold))

        for page in pages:
            seen_on_page: set[str] = set()
            for block in page.blocks:
                if block.kind not in {BlockType.PARAGRAPH, BlockType.QUOTE}:
                    continue
                text = normalize_for_similarity(block.text or "")
                if 20 <= len(text) <= 220:
                    seen_on_page.add(text)
            counter.update(seen_on_page)

        return {text for text, count in counter.items() if count >= minimum_occurrences}

    def _should_drop(self, block: ContentBlock, repeated: set[str]) -> bool:
        if block.kind not in {BlockType.PARAGRAPH, BlockType.QUOTE}:
            return False
        return normalize_for_similarity(block.text or "") in repeated

    def _blocks_to_text(self, blocks: list[ContentBlock]) -> str:
        parts: list[str] = []
        for block in blocks:
            text_kinds = {BlockType.HEADING, BlockType.PARAGRAPH, BlockType.QUOTE}
            if block.kind in text_kinds and block.text:
                parts.append(block.text)
            elif block.kind in {BlockType.BULLET_LIST, BlockType.ORDERED_LIST} and block.items:
                parts.append("\n".join(block.items))
            elif block.kind == BlockType.TABLE and block.rows:
                parts.append("\n".join(" | ".join(row) for row in block.rows))
        return normalize_whitespace("\n\n".join(parts))

