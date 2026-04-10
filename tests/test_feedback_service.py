from pathlib import Path

from app.models import FeedbackCategory, FeedbackSubmission
from app.services.feedback_service import FeedbackService


def test_feedback_service_writes_jsonl(tmp_path: Path) -> None:
    service = FeedbackService(tmp_path)
    submission = FeedbackSubmission(
        name="Test User",
        email="test@example.com",
        category=FeedbackCategory.FEATURE,
        rating=5,
        message="Please add richer table extraction for research-heavy websites.",
        allow_follow_up=True,
    )

    output_path = service.save(submission)

    assert output_path.exists()
    content = output_path.read_text(encoding="utf-8")
    assert "Test User" in content
    assert "feature_request" in content
