"""Remove quest submissions using HEIC or HEIF images."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app import create_app
from app.models import db, QuestSubmission
from app.utils.file_uploads import delete_media_file


def _remove_submission(submission: QuestSubmission) -> None:
    """Delete submission and associated media."""
    delete_media_file(submission.image_url)
    db.session.delete(submission)


def remove_heic_content() -> None:
    """Purge all HEIC or HEIF images from the database."""
    app = create_app()
    with app.app_context():
        submissions = (
            QuestSubmission.query.filter(
                QuestSubmission.image_url.ilike("%.heic")
            ).all()
            + QuestSubmission.query.filter(
                QuestSubmission.image_url.ilike("%.heif")
            ).all()
        )
        for sub in submissions:
            _remove_submission(sub)

        db.session.commit()
        print(f"Removed {len(submissions)} submissions")


if __name__ == "__main__":
    remove_heic_content()
