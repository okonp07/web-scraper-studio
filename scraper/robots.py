"""robots.txt handling."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

from scraper.fetcher import FetchError, PageFetcher


@dataclass(slots=True)
class _RobotsCacheEntry:
    parser: RobotFileParser
    sitemaps: list[str]


class RobotsPolicy:
    """Origin-scoped robots.txt cache."""

    def __init__(self, fetcher: PageFetcher, user_agent: str, respect_robots: bool) -> None:
        self.fetcher = fetcher
        self.user_agent = user_agent
        self.respect_robots = respect_robots
        self._cache: dict[str, _RobotsCacheEntry] = {}

    def _origin(self, url: str) -> str:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def _load(self, url: str) -> _RobotsCacheEntry | None:
        origin = self._origin(url)
        if origin in self._cache:
            return self._cache[origin]

        robots_url = f"{origin}/robots.txt"
        parser = RobotFileParser()
        parser.set_url(robots_url)
        try:
            result = self.fetcher.fetch(
                robots_url, max_bytes=512_000,
                accept="text/plain,*/*;q=0.5",
            )
        except FetchError:
            return None

        parser.parse(result.text.splitlines())
        entry = _RobotsCacheEntry(parser=parser, sitemaps=parser.site_maps() or [])
        self._cache[origin] = entry
        return entry

    def can_fetch(self, url: str) -> bool:
        """Return whether the configured agent may fetch a URL."""

        if not self.respect_robots:
            return True
        entry = self._load(url)
        if entry is None:
            return True
        return entry.parser.can_fetch(self.user_agent, url)

    def known_sitemaps(self, url: str) -> list[str]:
        """Return sitemaps advertised in robots.txt when present."""

        entry = self._load(url)
        return entry.sitemaps if entry else []

