"""Feedback persistence for the Streamlit app."""

from __future__ import annotations

from pathlib import Path

from app.models import FeedbackSubmission
from app.utils.files import ensure_directory


class FeedbackService:
    """Save feedback form submissions to a local JSONL file."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.storage_dir = ensure_directory(project_root / "data" / "feedback")
        self.storage_path = self.storage_dir / "feedback_submissions.jsonl"

    def save(self, submission: FeedbackSubmission) -> Path:
        """Append a feedback submission to the local store."""

        with self.storage_path.open("a", encoding="utf-8") as handle:
            handle.write(submission.model_dump_json())
            handle.write("\n")
        return self.storage_path
