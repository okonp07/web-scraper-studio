"""Plain-text export generation."""

from __future__ import annotations

from app.models.schemas import BlockType, PageContent


class TxtExporter:
    """Export scraped pages as an ordered text file."""

    def export(self, document_title: str, pages: list[PageContent]) -> bytes:
        parts = [document_title.strip(), "=" * max(18, len(document_title.strip())), ""]

        for page in pages:
            parts.extend(
                [
                    f"PAGE {page.order}: {page.title}",
                    f"URL: {page.final_url}",
                    f"SCRAPED_AT: {page.scraped_at.isoformat()}",
                    "-" * 72,
                ]
            )
            for block in page.blocks:
                if block.kind == BlockType.HEADING and block.text:
                    parts.append(block.text.upper())
                elif block.kind in {BlockType.PARAGRAPH, BlockType.QUOTE} and block.text:
                    parts.append(block.text)
                elif block.kind == BlockType.BULLET_LIST:
                    parts.extend(f"- {item}" for item in block.items)
                elif block.kind == BlockType.ORDERED_LIST:
                    parts.extend(f"{index}. {item}" for index, item in enumerate(block.items, start=1))
                elif block.kind == BlockType.TABLE:
                    parts.extend(" | ".join(row) for row in block.rows)
                elif block.kind == BlockType.IMAGE and block.caption:
                    parts.append(f"[Image] {block.caption}")
            parts.extend(["", "=" * 72, ""])

        return "\n".join(parts).encode("utf-8")

