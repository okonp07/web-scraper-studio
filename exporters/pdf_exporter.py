"""PDF export generation with optional images and table of contents."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    ListFlowable,
    ListItem,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

from app.models.schemas import BlockType, PageContent


class _ScrapePdfTemplate(BaseDocTemplate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="main")
        self.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=self._decorate_page)])
        self._bookmark_index = 0

    def afterFlowable(self, flowable):
        level = getattr(flowable, "toc_level", None)
        if level is None:
            return
        text = flowable.getPlainText()
        key = f"toc-{self._bookmark_index}"
        self.canv.bookmarkPage(key)
        self.notify("TOCEntry", (level, text, self.page, key))
        self._bookmark_index += 1

    def _decorate_page(self, canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#667085"))
        canvas.drawString(doc.leftMargin, 12 * mm, "Web Scraper Studio")
        canvas.drawRightString(A4[0] - doc.rightMargin, 12 * mm, f"Page {doc.page}")
        canvas.restoreState()


class PdfExporter:
    """Build a polished PDF document from structured page content."""

    def export(
        self,
        document_title: str,
        pages: list[PageContent],
        include_metadata: bool,
        include_images: bool,
    ) -> bytes:
        buffer = BytesIO()
        doc = _ScrapePdfTemplate(
            buffer,
            pagesize=A4,
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            topMargin=20 * mm,
            bottomMargin=18 * mm,
        )
        styles = self._styles()
        story = self._build_story(document_title, pages, include_metadata, include_images, styles)
        doc.multiBuild(story, maxPasses=15)
        return buffer.getvalue()

    def _styles(self):
        base = getSampleStyleSheet()
        return {
            "cover_title": ParagraphStyle(
                "cover_title",
                parent=base["Title"],
                fontName="Helvetica-Bold",
                fontSize=26,
                leading=30,
                textColor=colors.HexColor("#0f172a"),
                alignment=1,
                spaceAfter=12,
            ),
            "cover_subtitle": ParagraphStyle(
                "cover_subtitle",
                parent=base["Normal"],
                fontName="Helvetica",
                fontSize=11,
                leading=15,
                textColor=colors.HexColor("#475467"),
                alignment=1,
            ),
            "title": ParagraphStyle(
                "title",
                parent=base["Heading1"],
                fontName="Helvetica-Bold",
                fontSize=18,
                leading=22,
                textColor=colors.HexColor("#0f172a"),
                spaceBefore=10,
                spaceAfter=8,
            ),
            "h2": ParagraphStyle(
                "h2",
                parent=base["Heading2"],
                fontName="Helvetica-Bold",
                fontSize=14,
                leading=18,
                textColor=colors.HexColor("#102a43"),
                spaceBefore=8,
                spaceAfter=4,
            ),
            "h3": ParagraphStyle(
                "h3",
                parent=base["Heading3"],
                fontName="Helvetica-Bold",
                fontSize=12,
                leading=15,
                textColor=colors.HexColor("#1d2939"),
                spaceBefore=6,
                spaceAfter=3,
            ),
            "body": ParagraphStyle(
                "body",
                parent=base["BodyText"],
                fontName="Helvetica",
                fontSize=10,
                leading=14,
                textColor=colors.HexColor("#1f2937"),
                spaceAfter=6,
            ),
            "meta": ParagraphStyle(
                "meta",
                parent=base["BodyText"],
                fontName="Helvetica",
                fontSize=8.5,
                leading=11,
                textColor=colors.HexColor("#667085"),
                spaceAfter=4,
            ),
            "quote": ParagraphStyle(
                "quote",
                parent=base["BodyText"],
                fontName="Helvetica-Oblique",
                fontSize=10,
                leading=14,
                leftIndent=8 * mm,
                textColor=colors.HexColor("#344054"),
                borderPadding=2,
                spaceAfter=6,
            ),
            "caption": ParagraphStyle(
                "caption",
                parent=base["BodyText"],
                fontName="Helvetica-Oblique",
                fontSize=8.5,
                leading=10,
                textColor=colors.HexColor("#475467"),
                alignment=1,
                spaceAfter=8,
            ),
            "toc": ParagraphStyle(
                "toc",
                parent=base["Heading2"],
                fontName="Helvetica-Bold",
                fontSize=16,
                leading=20,
                textColor=colors.HexColor("#0f172a"),
                spaceAfter=8,
            ),
        }

    def _build_story(self, title, pages, include_metadata, include_images, styles):
        story = [
            Spacer(1, 30 * mm),
            Paragraph(escape(title), styles["cover_title"]),
            Paragraph("Readable website export with structured sections and source attribution.", styles["cover_subtitle"]),
            Spacer(1, 12 * mm),
            Paragraph(f"Pages included: {len(pages)}", styles["cover_subtitle"]),
            Paragraph(f"Total words: {sum(page.word_count for page in pages):,}", styles["cover_subtitle"]),
            PageBreak(),
        ]

        story.append(Paragraph("Contents", styles["toc"]))
        toc = TableOfContents()
        toc.levelStyles = [
            ParagraphStyle(name="toc-level-1", fontName="Helvetica", fontSize=10, leftIndent=8, firstLineIndent=-8, spaceBefore=4),
            ParagraphStyle(name="toc-level-2", fontName="Helvetica", fontSize=9, leftIndent=18, firstLineIndent=-8, textColor=colors.HexColor("#475467")),
            ParagraphStyle(name="toc-level-3", fontName="Helvetica", fontSize=8.5, leftIndent=28, firstLineIndent=-8, textColor=colors.HexColor("#667085")),
        ]
        story.extend([toc, PageBreak()])

        for index, page in enumerate(pages, start=1):
            title_para = Paragraph(escape(page.title), styles["title"])
            title_para.toc_level = 0
            story.append(title_para)
            story.append(Paragraph(f"Source URL: {escape(page.final_url)}", styles["meta"]))

            if include_metadata and (page.publication_date or page.meta_description):
                meta_parts = []
                if page.publication_date:
                    meta_parts.append(f"Published: {escape(page.publication_date)}")
                if page.meta_description:
                    meta_parts.append(f"Summary: {escape(page.meta_description)}")
                story.append(Paragraph(" | ".join(meta_parts), styles["meta"]))

            image_lookup = {image.source_url: image for image in page.images}
            for block in page.blocks:
                story.extend(self._render_block(block, image_lookup, styles, include_images))

            if index < len(pages):
                story.append(PageBreak())

        return story

    def _render_block(self, block, image_lookup, styles, include_images):
        flowables = []
        if block.kind == BlockType.HEADING and block.text:
            style = styles["h2"] if (block.level or 2) <= 2 else styles["h3"]
            paragraph = Paragraph(escape(block.text), style)
            paragraph.toc_level = 1 if (block.level or 2) <= 2 else 2
            flowables.append(paragraph)
        elif block.kind == BlockType.PARAGRAPH and block.text:
            flowables.append(Paragraph(escape(block.text), styles["body"]))
        elif block.kind == BlockType.QUOTE and block.text:
            flowables.append(Paragraph(escape(block.text), styles["quote"]))
        elif block.kind == BlockType.BULLET_LIST:
            items = [ListItem(Paragraph(escape(item), styles["body"])) for item in block.items]
            flowables.append(ListFlowable(items, bulletType="bullet", leftIndent=12))
            flowables.append(Spacer(1, 4))
        elif block.kind == BlockType.ORDERED_LIST:
            items = [ListItem(Paragraph(escape(item), styles["body"])) for item in block.items]
            flowables.append(ListFlowable(items, bulletType="1", leftIndent=12))
            flowables.append(Spacer(1, 4))
        elif block.kind == BlockType.TABLE and block.rows:
            max_cols = max(len(row) for row in block.rows)
            normalized_rows = [row + [""] * (max_cols - len(row)) for row in block.rows]
            safe_rows = [
                [Paragraph(escape(cell), styles["body"]) for cell in row]
                for row in normalized_rows
            ]
            available_width = 174 * mm
            col_widths = [available_width / max_cols] * max_cols
            table = Table(safe_rows, repeatRows=1, colWidths=col_widths)
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                        ("LEADING", (0, 0), (-1, -1), 10),
                    ]
                )
            )
            flowables.append(table)
            flowables.append(Spacer(1, 6))
        elif block.kind == BlockType.IMAGE and include_images and block.text:
            image = image_lookup.get(block.text)
            if image and image.local_path and Path(image.local_path).exists():
                max_width = 160 * mm
                width = float(image.width or 800)
                height = float(image.height or 500)
                scale = min(max_width / width, 1.0)
                flowables.append(Image(str(image.local_path), width=width * scale, height=height * scale))
                if block.caption:
                    flowables.append(Paragraph(escape(block.caption), styles["caption"]))
                else:
                    flowables.append(Spacer(1, 4))
        return flowables

