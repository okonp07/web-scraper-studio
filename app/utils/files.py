"""Filesystem helpers."""

from __future__ import annotations

import base64
import mimetypes
from functools import lru_cache
from pathlib import Path


def ensure_directory(path: Path) -> Path:
    """Create a directory if it does not exist."""

    path.mkdir(parents=True, exist_ok=True)
    return path


def human_size(num_bytes: int) -> str:
    """Render byte counts in a compact human-readable format."""

    value = float(num_bytes)
    units = ["B", "KB", "MB", "GB"]
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{num_bytes} B"


@lru_cache(maxsize=16)
def image_data_uri(path: Path) -> str:
    """Convert a local image into a cacheable data URI for Streamlit HTML blocks."""

    mime_type, _ = mimetypes.guess_type(path.name)
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type or 'application/octet-stream'};base64,{encoded}"
