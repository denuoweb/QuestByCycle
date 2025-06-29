"""Remove quest submissions using HEIC or HEIF images."""

from __future__ import annotations

from app import create_app
from app.models import db, QuestSubmission, Quest
from app.utils.file_uploads import delete_media_file


def _remove_submission(submission: QuestSubmission) -> None:
    """Delete submission and associated media."""
    delete_media_file(submission.image_url)
    db.session.delete(submission)


def _clear_quest_image(quest: Quest) -> None:
    """Remove HEIC/HEIF evidence images from quests."""
    delete_media_file(quest.evidence_url)
    quest.evidence_url = None


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

        quests = (
            Quest.query.filter(Quest.evidence_url.ilike("%.heic")).all()
            + Quest.query.filter(Quest.evidence_url.ilike("%.heif")).all()
        )
        for quest in quests:
            _clear_quest_image(quest)

        db.session.commit()
        print(f"Removed {len(submissions)} submissions and {len(quests)} quests")


if __name__ == "__main__":
    remove_heic_content()
