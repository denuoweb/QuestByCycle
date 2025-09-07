from datetime import datetime, timedelta, timezone

import pytest
from flask_login import login_user

from app import create_app, db
from app.models import Game, Quest, QuestSubmission, SubmissionLike, User
from app.quests import submission_like


@pytest.fixture
def app():
    app = create_app(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "MAIL_SERVER": None,
        }
    )
    ctx = app.app_context()
    ctx.push()
    db.create_all()
    yield app
    db.session.remove()
    db.drop_all()
    ctx.pop()


@pytest.fixture
def users(app):
    owner = User(
        username="owner",
        email="owner@example.com",
        license_agreed=True,
        email_verified=True,
    )
    owner.set_password("pw")
    owner.created_at = datetime.now(timezone.utc)

    liker = User(
        username="liker",
        email="liker@example.com",
        license_agreed=True,
        email_verified=True,
    )
    liker.set_password("pw")
    liker.created_at = datetime.now(timezone.utc)

    db.session.add_all([owner, liker])
    db.session.commit()
    return owner, liker


def test_submission_like_handles_unique_violation(app, users, monkeypatch):
    owner, liker = users
    game = Game(
        title="G",
        start_date=datetime.now(timezone.utc) - timedelta(days=1),
        end_date=datetime.now(timezone.utc) + timedelta(days=1),
        admin_id=owner.id,
        timezone="UTC",
    )
    quest = Quest(title="Q", game=game)
    db.session.add_all([game, quest])
    db.session.commit()

    submission = QuestSubmission(quest_id=quest.id, user_id=owner.id)
    db.session.add(submission)
    db.session.commit()

    like = SubmissionLike(submission_id=submission.id, user_id=liker.id)
    db.session.add(like)
    db.session.commit()

    def fake_filter_by(**kwargs):
        class Dummy:
            def first(self):
                return None

        return Dummy()

    monkeypatch.setattr(SubmissionLike.query, "filter_by", fake_filter_by)

    with app.test_request_context(method="POST"):
        login_user(liker)
        response = submission_like(submission.id)

    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["liked"] is True
    assert SubmissionLike.query.count() == 1

