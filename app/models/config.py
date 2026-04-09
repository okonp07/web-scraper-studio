"""Runtime and developer settings."""

from __future__ import annotations

import os
import tomllib
from pathlib import Path

from pydantic import BaseModel, Field


class DeveloperSettings(BaseModel):
    """Developer-only crawler overrides that are not exposed in the UI."""

    respect_robots: bool = True
    debug: bool = False
    max_sitemap_urls: int = 250
    duplicate_similarity_threshold: float = 0.94
    max_images_per_page: int = 4
    minimum_text_length: int = 180


class RuntimeSettings(BaseModel):
    """Environment-driven runtime settings."""

    log_level: str = Field(default="INFO")
    default_timeout_seconds: float = Field(default=20.0)
    max_concurrency: int = Field(default=2)
    user_agent: str = Field(
        default="WebScraperStudio/0.1 (+https://github.com/your-org/web-scraper-studio)"
    )
    developer: DeveloperSettings = Field(default_factory=DeveloperSettings)

    @classmethod
    def load(cls, project_root: Path) -> "RuntimeSettings":
        """Load runtime settings from env vars plus developer TOML when present."""

        config_path = os.getenv("SCRAPER_DEV_CONFIG", str(project_root / "config" / "developer.toml"))
        developer_payload: dict[str, object] = {}
        config_file = Path(config_path)
        if config_file.exists():
            with config_file.open("rb") as handle:
                loaded = tomllib.load(handle)
            developer_payload = loaded.get("developer", {})

        return cls(
            log_level=os.getenv("SCRAPER_LOG_LEVEL", "INFO"),
            default_timeout_seconds=float(os.getenv("SCRAPER_DEFAULT_TIMEOUT", "20")),
            max_concurrency=int(os.getenv("SCRAPER_MAX_CONCURRENCY", "2")),
            user_agent=os.getenv(
                "SCRAPER_USER_AGENT",
                "WebScraperStudio/0.1 (+https://github.com/your-org/web-scraper-studio)",
            ),
            developer=DeveloperSettings.model_validate(developer_payload),
        )

