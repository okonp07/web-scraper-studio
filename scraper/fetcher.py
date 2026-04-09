"""HTTP and browser-backed fetch helpers."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential


class FetchError(RuntimeError):
    """Base fetch error."""


class RetryableFetchError(FetchError):
    """Transient fetch failure that should be retried."""


class ContentTooLargeError(FetchError):
    """Raised when the response exceeds the configured cap."""


@dataclass(slots=True)
class FetchResult:
    requested_url: str
    final_url: str
    status_code: int
    headers: dict[str, str]
    content_type: str
    content_bytes: bytes
    text: str
    elapsed_seconds: float


class _RateLimiter:
    """Simple global minimum-delay limiter shared across fetches."""

    def __init__(self, delay_seconds: float) -> None:
        self.delay_seconds = max(0.0, delay_seconds)
        self._next_allowed_at = 0.0
        self._lock = threading.Lock()

    def wait(self) -> None:
        if self.delay_seconds <= 0:
            return
        with self._lock:
            now = time.monotonic()
            sleep_for = self._next_allowed_at - now
            if sleep_for > 0:
                time.sleep(sleep_for)
                now = time.monotonic()
            self._next_allowed_at = now + self.delay_seconds


class PageFetcher:
    """Conservative HTTP fetcher with retries, size limits, and browser fallback."""

    RETRYABLE_STATUS_CODES = {408, 425, 429, 500, 502, 503, 504}

    def __init__(self, user_agent: str, timeout_seconds: float, delay_seconds: float) -> None:
        self.user_agent = user_agent
        self.timeout_seconds = timeout_seconds
        self.rate_limiter = _RateLimiter(delay_seconds)
        self.client = httpx.Client(
            follow_redirects=True,
            headers={
                "User-Agent": user_agent,
                "Accept-Language": "en-US,en;q=0.9",
            },
            timeout=httpx.Timeout(timeout_seconds),
        )

    def close(self) -> None:
        self.client.close()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type((httpx.HTTPError, RetryableFetchError)),
        reraise=True,
    )
    def fetch(
        self,
        url: str,
        max_bytes: int,
        accept: str = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    ) -> FetchResult:
        """Fetch a URL over HTTP with retries for transient failures."""

        self.rate_limiter.wait()
        started = time.perf_counter()
        try:
            with self.client.stream("GET", url, headers={"Accept": accept}) as response:
                status_code = response.status_code
                if status_code in self.RETRYABLE_STATUS_CODES:
                    raise RetryableFetchError(f"Retryable HTTP status {status_code} for {url}")
                if status_code >= 400:
                    raise FetchError(f"HTTP {status_code} while fetching {url}")

                content_length = int(response.headers.get("content-length", "0") or 0)
                if max_bytes and content_length and content_length > max_bytes:
                    raise ContentTooLargeError(f"Response too large for {url}")

                payload_chunks: list[bytes] = []
                total = 0
                for chunk in response.iter_bytes():
                    total += len(chunk)
                    if max_bytes and total > max_bytes:
                        raise ContentTooLargeError(f"Response exceeded size limit for {url}")
                    payload_chunks.append(chunk)

                payload = b"".join(payload_chunks)
                encoding = response.encoding or response.charset_encoding or "utf-8"
                elapsed = time.perf_counter() - started
                return FetchResult(
                    requested_url=url,
                    final_url=str(response.url),
                    status_code=status_code,
                    headers=dict(response.headers),
                    content_type=response.headers.get("content-type", ""),
                    content_bytes=payload,
                    text=payload.decode(encoding, errors="ignore"),
                    elapsed_seconds=elapsed,
                )
        except httpx.HTTPError as exc:
            raise FetchError(str(exc)) from exc

    def fetch_binary(self, url: str, max_bytes: int) -> FetchResult:
        """Fetch binary content such as images."""

        return self.fetch(url, max_bytes=max_bytes, accept="image/*,*/*;q=0.8")

    def render(self, url: str, max_bytes: int) -> FetchResult:
        """Render a page with Playwright when a site is JS-heavy."""

        try:
            from playwright.sync_api import Error as PlaywrightError
            from playwright.sync_api import sync_playwright
        except Exception as exc:  # pragma: no cover - optional dependency at runtime
            raise FetchError("Playwright is not available in this environment.") from exc

        self.rate_limiter.wait()
        started = time.perf_counter()
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                page = browser.new_page(user_agent=self.user_agent)
                response = page.goto(url, wait_until="networkidle", timeout=int(self.timeout_seconds * 1000))
                html = page.content()
                final_url = page.url
                browser.close()

            payload = html.encode("utf-8", errors="ignore")
            if max_bytes and len(payload) > max_bytes:
                raise ContentTooLargeError(f"Rendered page exceeded size limit for {url}")

            elapsed = time.perf_counter() - started
            return FetchResult(
                requested_url=url,
                final_url=final_url,
                status_code=response.status if response else 200,
                headers={"content-type": "text/html; charset=utf-8"},
                content_type="text/html; charset=utf-8",
                content_bytes=payload,
                text=html,
                elapsed_seconds=elapsed,
            )
        except PlaywrightError as exc:  # pragma: no cover - browser runtime specific
            raise FetchError(f"Browser rendering failed for {url}: {exc}") from exc

