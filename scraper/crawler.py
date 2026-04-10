"""Breadth-first website crawler."""

from __future__ import annotations

import logging
from collections import deque
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from bs4 import BeautifulSoup

from app.models.config import RuntimeSettings
from app.models.schemas import PageContent, ScrapeIssue, ScrapeRequest
from app.utils.text import word_count
from app.utils.url import (
    candidate_sitemap_urls,
    canonicalize_url,
    in_scope,
    is_skippable_url,
    is_supported_url,
    normalize_user_url,
)
from scraper.deduper import DuplicateDetector
from scraper.extractor import ContentExtractor
from scraper.fetcher import ContentTooLargeError, FetchError, FetchResult, PageFetcher
from scraper.parser import parse_page
from scraper.robots import RobotsPolicy


@dataclass(slots=True)
class CrawlTarget:
    url: str
    depth: int
    source: str


@dataclass(slots=True)
class ProcessedPage:
    page: PageContent
    links: list[str]


class BreadthFirstCrawler:
    """Crawl page-only or whole-site requests with conservative defaults."""

    def __init__(self, settings: RuntimeSettings, logger: logging.Logger) -> None:
        self.settings = settings
        self.logger = logger

    def crawl(
        self,
        request: ScrapeRequest,
        emit: Callable[[dict[str, object]], None] | None = None,
    ) -> tuple[
        list[PageContent], list[ScrapeIssue],
        list[ScrapeIssue], list[str], dict[str, int],
    ]:
        """Run a crawl and return pages, skipped pages, errors, and live logs."""

        start_url = canonicalize_url(
            normalize_user_url(request.start_url),
            include_query_params=request.include_query_params,
        )
        max_bytes = int(request.max_file_size_mb * 1024 * 1024)

        fetcher = PageFetcher(
            user_agent=self.settings.user_agent,
            timeout_seconds=request.timeout_seconds,
            delay_seconds=request.delay_seconds,
        )
        robots = RobotsPolicy(
            fetcher=fetcher,
            user_agent=self.settings.user_agent,
            respect_robots=self.settings.developer.respect_robots,
        )
        extractor = ContentExtractor(
            minimum_text_length=self.settings.developer.minimum_text_length,
        )
        deduper = DuplicateDetector(
            self.settings.developer.duplicate_similarity_threshold,
        )

        logs: list[str] = []
        skipped_pages: list[ScrapeIssue] = []
        errors: list[ScrapeIssue] = []
        pages: list[PageContent] = []

        queue: deque[CrawlTarget] = deque([
            CrawlTarget(url=start_url, depth=0, source="seed"),
        ])
        discovered_urls: set[str] = {start_url}
        visited_urls: set[str] = set()

        self._emit(
            emit,
            logs,
            f"Starting scrape from {start_url}",
            current_url=start_url,
            discovered=len(discovered_urls),
            scraped=0,
            skipped=0,
            errors=0,
        )

        if request.mode.value == "full_scrape" and request.include_sitemap:
            sitemap_links = self._discover_sitemap_links(
                start_url, request, fetcher, robots, max_bytes,
            )
            added = 0
            for link in sitemap_links:
                if len(discovered_urls) >= request.max_pages * 8:
                    break
                if link not in discovered_urls:
                    queue.append(CrawlTarget(url=link, depth=1, source="sitemap"))
                    discovered_urls.add(link)
                    added += 1
            if added:
                self._emit(
                    emit,
                    logs,
                    f"Seeded {added} in-scope URLs from sitemap discovery.",
                    current_url=start_url,
                    discovered=len(discovered_urls),
                    scraped=0,
                    skipped=0,
                    errors=0,
                )

        try:
            while queue and len(pages) < request.max_pages:
                batch = self._next_batch(queue, request.concurrency)
                eligible_targets: list[CrawlTarget] = []
                for target in batch:
                    if target.url in visited_urls:
                        continue
                    if target.depth > request.max_depth:
                        skipped_pages.append(
                            ScrapeIssue(url=target.url, reason="Depth limit exceeded"),
                        )
                        continue
                    if not in_scope(target.url, start_url, request.scope):
                        skipped_pages.append(
                            ScrapeIssue(url=target.url, reason="Out of crawl scope"),
                        )
                        continue
                    if is_skippable_url(target.url):
                        skipped_pages.append(ScrapeIssue(
                            url=target.url,
                            reason="Skipped likely non-content page",
                        ))
                        continue
                    if not robots.can_fetch(target.url):
                        skipped_pages.append(ScrapeIssue(
                            url=target.url,
                            reason="Blocked by robots.txt",
                        ))
                        self._emit(
                            emit,
                            logs,
                            f"Skipped by robots.txt: {target.url}",
                            current_url=target.url,
                            discovered=len(discovered_urls),
                            scraped=len(pages),
                            skipped=len(skipped_pages),
                            errors=len(errors),
                        )
                        continue
                    visited_urls.add(target.url)
                    eligible_targets.append(target)

                if not eligible_targets:
                    continue

                fetched_batch = self._fetch_batch(
                    eligible_targets,
                    fetcher,
                    max_bytes,
                    request.concurrency,
                )

                for target, fetched in fetched_batch:
                    page_result = self._process_target(
                        target=target,
                        fetched=fetched,
                        request=request,
                        fetcher=fetcher,
                        extractor=extractor,
                        deduper=deduper,
                        max_bytes=max_bytes,
                    )

                    if isinstance(page_result, ScrapeIssue):
                        if page_result.reason.startswith("Error"):
                            errors.append(page_result)
                        else:
                            skipped_pages.append(page_result)
                        self._emit(
                            emit,
                            logs,
                            f"{page_result.reason}: {target.url}",
                            current_url=target.url,
                            discovered=len(discovered_urls),
                            scraped=len(pages),
                            skipped=len(skipped_pages),
                            errors=len(errors),
                        )
                        continue

                    page_result.page.order = len(pages) + 1
                    pages.append(page_result.page)
                    deduper.remember(
                        page_result.page.canonical_url,
                        page_result.page.text_content,
                    )
                    visited_urls.add(page_result.page.canonical_url)

                    self._emit(
                        emit,
                        logs,
                        f"Scraped page {len(pages)}: {page_result.page.title}",
                        current_url=page_result.page.final_url,
                        discovered=len(discovered_urls),
                        scraped=len(pages),
                        skipped=len(skipped_pages),
                        errors=len(errors),
                    )

                    if request.mode.value == "full_scrape" and target.depth < request.max_depth:
                        for link in page_result.links:
                            normalized = canonicalize_url(
                                link,
                                include_query_params=request.include_query_params,
                            )
                            if not is_supported_url(normalized):
                                continue
                            if not in_scope(normalized, start_url, request.scope):
                                continue
                            if is_skippable_url(normalized):
                                continue
                            if normalized in discovered_urls or normalized in visited_urls:
                                continue
                            queue.append(CrawlTarget(
                                url=normalized,
                                depth=target.depth + 1,
                                source=target.source,
                            ))
                            discovered_urls.add(normalized)

            return (
                pages, skipped_pages, errors, logs,
                {"discovered": len(discovered_urls)},
            )
        finally:
            fetcher.close()

    def _process_target(
        self,
        target: CrawlTarget,
        fetched: FetchResult | Exception,
        request: ScrapeRequest,
        fetcher: PageFetcher,
        extractor: ContentExtractor,
        deduper: DuplicateDetector,
        max_bytes: int,
    ) -> ProcessedPage | ScrapeIssue:
        if isinstance(fetched, Exception):
            if request.use_browser_fallback:
                try:
                    fetched = fetcher.render(target.url, max_bytes=max_bytes)
                except FetchError as exc:
                    return ScrapeIssue(
                        url=target.url,
                        reason="Error fetching page",
                        detail=str(exc),
                    )
            else:
                return ScrapeIssue(
                    url=target.url,
                    reason="Error fetching page",
                    detail=str(fetched),
                )

        if not self._is_html_like(fetched.content_type):
            return ScrapeIssue(
                url=target.url,
                reason="Skipped non-HTML response",
                detail=fetched.content_type,
            )

        try:
            parsed = parse_page(fetched.text, target.url, fetched.final_url)
        except Exception as exc:
            return ScrapeIssue(
                url=target.url,
                reason="Error parsing page",
                detail=str(exc),
            )

        canonical_url = canonicalize_url(
            parsed.canonical_url,
            include_query_params=request.include_query_params,
        )
        if is_skippable_url(canonical_url):
            return ScrapeIssue(
                url=target.url,
                reason="Skipped canonical non-content page",
            )

        try:
            extracted = extractor.extract(
                fetched.text, fetched.final_url,
                request.boilerplate_mode,
            )
        except Exception as exc:
            return ScrapeIssue(
                url=target.url,
                reason="Error extracting content",
                detail=str(exc),
            )

        if request.use_browser_fallback and word_count(extracted.text_content) < max(
            100, self.settings.developer.minimum_text_length // 2
        ):
            try:
                rendered = fetcher.render(target.url, max_bytes=max_bytes)
                rendered_parsed = parse_page(
                    rendered.text, target.url, rendered.final_url,
                )
                rendered_extracted = extractor.extract(
                    rendered.text,
                    rendered.final_url,
                    request.boilerplate_mode,
                )
                if word_count(rendered_extracted.text_content) > word_count(
                    extracted.text_content
                ):
                    fetched = rendered
                    parsed = rendered_parsed
                    extracted = rendered_extracted
                    canonical_url = canonicalize_url(
                        parsed.canonical_url,
                        include_query_params=request.include_query_params,
                    )
            except FetchError:
                pass

        if word_count(extracted.text_content) < 40:
            return ScrapeIssue(
                url=target.url,
                reason="Skipped page with too little readable content",
            )

        duplicate = deduper.find_duplicate(canonical_url, extracted.text_content)
        if duplicate:
            return ScrapeIssue(
                url=target.url,
                reason=f"Skipped near-duplicate of {duplicate.source_url}",
                detail=f"Similarity {duplicate.similarity:.2f}",
            )

        page = PageContent(
            order=0,
            requested_url=target.url,
            final_url=fetched.final_url,
            canonical_url=canonical_url,
            title=parsed.title,
            meta_description=parsed.meta_description,
            publication_date=parsed.publication_date,
            headings=parsed.headings,
            blocks=extracted.blocks,
            text_content=extracted.text_content,
            word_count=word_count(extracted.text_content),
            images=extracted.images,
        )
        links = [link.url for link in parsed.links]
        return ProcessedPage(page=page, links=links)

    def _discover_sitemap_links(
        self,
        start_url: str,
        request: ScrapeRequest,
        fetcher: PageFetcher,
        robots: RobotsPolicy,
        max_bytes: int,
    ) -> list[str]:
        sitemap_queue = deque(
            robots.known_sitemaps(start_url)
            + candidate_sitemap_urls(start_url)
        )
        seen_sitemaps: set[str] = set()
        discovered_links: list[str] = []

        max_urls = self.settings.developer.max_sitemap_urls
        while sitemap_queue and len(discovered_links) < max_urls:
            sitemap_url = sitemap_queue.popleft()
            if sitemap_url in seen_sitemaps:
                continue
            seen_sitemaps.add(sitemap_url)
            try:
                result = fetcher.fetch(
                    sitemap_url, max_bytes=max_bytes,
                    accept="application/xml,text/xml,*/*;q=0.5",
                )
            except FetchError:
                continue

            soup = BeautifulSoup(result.text, "xml")
            if soup.find("sitemapindex"):
                for loc in soup.find_all("loc"):
                    child = loc.get_text(strip=True)
                    if child and child not in seen_sitemaps:
                        sitemap_queue.append(child)
                continue

            for loc in soup.find_all("loc"):
                raw = loc.get_text(strip=True)
                if not raw:
                    continue
                normalized = canonicalize_url(
                    raw,
                    include_query_params=request.include_query_params,
                )
                if not is_supported_url(normalized):
                    continue
                if not in_scope(normalized, start_url, request.scope):
                    continue
                if is_skippable_url(normalized):
                    continue
                discovered_links.append(normalized)
                if len(discovered_links) >= max_urls:
                    break

        return discovered_links

    def _next_batch(self, queue: deque[CrawlTarget], batch_size: int) -> list[CrawlTarget]:
        items: list[CrawlTarget] = []
        while queue and len(items) < max(1, batch_size):
            items.append(queue.popleft())
        return items

    def _fetch_batch(
        self,
        targets: list[CrawlTarget],
        fetcher: PageFetcher,
        max_bytes: int,
        concurrency: int,
    ) -> list[tuple[CrawlTarget, FetchResult | Exception]]:
        if concurrency <= 1 or len(targets) <= 1:
            return [
                (target, self._safe_fetch(fetcher, target.url, max_bytes))
                for target in targets
            ]

        results: dict[str, FetchResult | Exception] = {}
        max_workers = min(concurrency, len(targets))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    self._safe_fetch, fetcher, target.url, max_bytes,
                ): target
                for target in targets
            }
            for future, target in futures.items():
                results[target.url] = future.result()
        return [(target, results[target.url]) for target in targets]

    def _safe_fetch(
        self, fetcher: PageFetcher, url: str, max_bytes: int,
    ) -> FetchResult | Exception:
        try:
            return fetcher.fetch(url, max_bytes=max_bytes)
        except (FetchError, ContentTooLargeError) as exc:
            return exc

    def _is_html_like(self, content_type: str) -> bool:
        lowered = (content_type or "").lower()
        return (
            not lowered
            or "html" in lowered
            or "xml" in lowered
            or "text/" in lowered
        )

    def _emit(
        self,
        emit: Callable[[dict[str, object]], None] | None,
        logs: list[str],
        message: str,
        *,
        current_url: str,
        discovered: int,
        scraped: int,
        skipped: int,
        errors: int,
    ) -> None:
        logs.append(message)
        self.logger.info(message)
        if emit is None:
            return
        emit(
            {
                "message": message,
                "current_url": current_url,
                "discovered": discovered,
                "scraped": scraped,
                "skipped": skipped,
                "errors": errors,
            }
        )
