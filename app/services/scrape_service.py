"""Orchestrates crawling, cleanup, and artifact generation."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Callable

from app.models import OutputFormat, RuntimeSettings, ScrapeArtifact, ScrapeIssue, ScrapeRequest, ScrapeResult, ScrapeSummary
from app.utils.logging import setup_logging
from app.utils.text import safe_filename_from_url
from exporters.docx_exporter import DocxExporter
from exporters.pdf_exporter import PdfExporter
from exporters.txt_exporter import TxtExporter
from scraper.crawler import BreadthFirstCrawler
from scraper.fetcher import PageFetcher
from scraper.images import ContentImageManager

from .assembler import DocumentAssembler


class ScrapeService:
    """High-level scrape pipeline used by the Streamlit UI."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.settings = RuntimeSettings.load(project_root)
        self.logger = setup_logging(self.settings.log_level, project_root / "logs")
        self.assembler = DocumentAssembler()
        self.crawler = BreadthFirstCrawler(self.settings, self.logger)
        self.txt_exporter = TxtExporter()
        self.docx_exporter = DocxExporter()
        self.pdf_exporter = PdfExporter()

    def run(
        self,
        request: ScrapeRequest,
        emit: Callable[[dict[str, object]], None] | None = None,
    ) -> ScrapeResult:
        """Run the complete scrape pipeline and return artifacts plus summary metadata."""

        started = time.perf_counter()
        pages, skipped_pages, errors, logs, crawl_metrics = self.crawler.crawl(request, emit=emit)
        pages = self.assembler.refine_pages(pages, request.boilerplate_mode)

        artifacts: list[ScrapeArtifact] = []
        total_images = 0
        document_title = self._document_title(request.start_url, pages)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        export_stem = f"{safe_filename_from_url(request.start_url)}-{timestamp}"

        with TemporaryDirectory(prefix="web-scraper-studio-") as temp_dir:
            if OutputFormat.PDF in request.output_formats and request.include_images_in_pdf and pages:
                image_fetcher = PageFetcher(
                    user_agent=self.settings.user_agent,
                    timeout_seconds=request.timeout_seconds,
                    delay_seconds=max(0.1, request.delay_seconds / 2),
                )
                try:
                    image_manager = ContentImageManager(
                        fetcher=image_fetcher,
                        temp_dir=Path(temp_dir) / "images",
                        max_images_per_page=self.settings.developer.max_images_per_page,
                    )
                    total_images = image_manager.enrich_pages(pages)
                finally:
                    image_fetcher.close()

            artifacts.extend(
                self._build_artifacts(
                    request=request,
                    pages=pages,
                    document_title=document_title,
                    export_stem=export_stem,
                    emit=emit,
                    errors=errors,
                )
            )

        runtime_seconds = time.perf_counter() - started
        summary = ScrapeSummary(
            start_url=request.start_url,
            mode=request.mode,
            pages_scraped=len(pages),
            pages_skipped=len(skipped_pages),
            total_words=sum(page.word_count for page in pages),
            total_images=total_images,
            runtime_seconds=runtime_seconds,
            discovered_pages=crawl_metrics.get("discovered", len(pages) + len(skipped_pages) + len(errors)),
            error_count=len(errors),
        )

        return ScrapeResult(
            summary=summary,
            pages=pages,
            artifacts=artifacts,
            skipped_pages=skipped_pages,
            errors=errors,
            logs=logs,
        )

    def _build_artifacts(
        self,
        request: ScrapeRequest,
        pages,
        document_title: str,
        export_stem: str,
        emit: Callable[[dict[str, object]], None] | None,
        errors: list[ScrapeIssue],
    ) -> list[ScrapeArtifact]:
        artifacts: list[ScrapeArtifact] = []

        for output_format in request.output_formats:
            self._emit(emit, f"Generating {output_format.value.upper()} export...")
            try:
                if output_format == OutputFormat.TXT:
                    bytes_data = self.txt_exporter.export(document_title, pages)
                    artifacts.append(
                        ScrapeArtifact(
                            format=output_format,
                            filename=f"{export_stem}.txt",
                            mime_type="text/plain",
                            bytes_data=bytes_data,
                        )
                    )
                elif output_format == OutputFormat.DOCX:
                    bytes_data = self.docx_exporter.export(
                        document_title=document_title,
                        pages=pages,
                        include_metadata=request.include_metadata,
                    )
                    artifacts.append(
                        ScrapeArtifact(
                            format=output_format,
                            filename=f"{export_stem}.docx",
                            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            bytes_data=bytes_data,
                        )
                    )
                elif output_format == OutputFormat.PDF:
                    bytes_data = self.pdf_exporter.export(
                        document_title=document_title,
                        pages=pages,
                        include_metadata=request.include_metadata,
                        include_images=request.include_images_in_pdf,
                    )
                    artifacts.append(
                        ScrapeArtifact(
                            format=output_format,
                            filename=f"{export_stem}.pdf",
                            mime_type="application/pdf",
                            bytes_data=bytes_data,
                        )
                    )
            except Exception as exc:  # pragma: no cover - exporter failures are environment-specific
                errors.append(
                    ScrapeIssue(
                        url=request.start_url,
                        reason=f"Error generating {output_format.value.upper()} export",
                        detail=str(exc),
                    )
                )

        return artifacts

    def _document_title(self, start_url: str, pages) -> str:
        if pages:
            return pages[0].title or pages[0].final_url
        return f"Website scrape for {start_url}"

    def _emit(
        self,
        emit: Callable[[dict[str, object]], None] | None,
        message: str,
    ) -> None:
        self.logger.info(message)
        if emit is None:
            return
        emit({"message": message})
