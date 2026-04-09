"""Tests for cross-page cleanup."""

from app.models.schemas import BlockType, BoilerplateMode, ContentBlock, PageContent
from app.services.assembler import DocumentAssembler


def make_page(order: int, title: str, body: str) -> PageContent:
    return PageContent(
        order=order,
        requested_url=f"https://example.com/{order}",
        final_url=f"https://example.com/{order}",
        canonical_url=f"https://example.com/{order}",
        title=title,
        blocks=[
            ContentBlock(kind=BlockType.PARAGRAPH, text="Subscribe to our newsletter for updates."),
            ContentBlock(kind=BlockType.PARAGRAPH, text=body),
        ],
        text_content=f"Subscribe to our newsletter for updates.\n\n{body}",
        word_count=20,
    )


def test_document_assembler_removes_repeated_boilerplate() -> None:
    pages = [
        make_page(1, "One", "Body copy one."),
        make_page(2, "Two", "Body copy two."),
        make_page(3, "Three", "Body copy three."),
    ]

    refined = DocumentAssembler().refine_pages(pages, BoilerplateMode.AGGRESSIVE)

    assert all("Subscribe to our newsletter" not in page.text_content for page in refined)
    assert refined[0].blocks[0].text == "Body copy one."

