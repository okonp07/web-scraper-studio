"""Logging setup."""

from __future__ import annotations

import logging
from pathlib import Path

from .files import ensure_directory


def setup_logging(log_level: str = "INFO", log_dir: Path | None = None) -> logging.Logger:
    """Configure application logging once and return the shared logger."""

    logger = logging.getLogger("web_scraper_studio")
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    if log_dir is not None:
        ensure_directory(log_dir)
        file_handler = logging.FileHandler(log_dir / "scraper.log", encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logger.propagate = False
    return logger

